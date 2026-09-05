"""
server.py - Gemini Master Orchestrator Live Voice Backend.

Direct WebSocket connection to the Gemini Live API via google-genai SDK.
Bidirectional real-time streaming:
  - Upstream:   Mic 16kHz PCM audio -> session.send_realtime_input
  - Downstream: session.receive()   -> 24kHz audio bytes + transcripts + tool triggers

GOTCHA SOLVED: session.receive() is a per-turn async generator. It is wrapped in
an outer `while True` loop so the conversation continues seamlessly across turns.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

from voice.backend.persona import get_system_instruction
from voice.backend.tools import TOOL_DECLARATIONS, dispatch_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("gemini-voice-orchestrator")

MODEL = os.getenv("LIVE_MODEL", "gemini-3.1-flash-live-preview")
VOICE = os.getenv("LIVE_VOICE", "Aoede")  # Options: Aoede, Puck, Charon, Kore, Fenrir

def get_genai_client():
    """Lazily initializes and returns the GenAI client with authenticated session or fallback key."""
    from services.auth_service import get_auth_token
    token = get_auth_token("google")
    if token:
        try:
            return genai.Client(api_key=token)
        except Exception:
            pass

    from services.llm_provider import load_api_keys
    keys = load_api_keys()
    api_key = keys.get("gemini") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)
    return genai.Client()

def build_live_config():
    return {
        "response_modalities": ["AUDIO"],
        "system_instruction": get_system_instruction(),
        "input_audio_transcription": {},
        "output_audio_transcription": {},
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": VOICE}
            }
        },
        "tools": [{"function_declarations": TOOL_DECLARATIONS}],
    }

app = FastAPI(
    title="Gemini Orchestrator Voice Backend",
    description="Low-latency bidirectional Gemini Live voice interface for multi-agent orchestration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
async def health():
    """Health check and status endpoint."""
    return {
        "status": "online",
        "model": MODEL,
        "voice": VOICE,
        "api_key_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "roles": "Gemini Master Orchestrator"
    }


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    """
    Main Live Voice WebSocket connection.
    Accepts 16kHz PCM audio stream and returns 24kHz audio + JSON transcripts.
    """
    await websocket.accept()
    log.info("Client connected. Opening Gemini Live session (model=%s, voice=%s)...", MODEL, VOICE)

    config = build_live_config()

    try:
        genai_client = get_genai_client()
    except Exception as err:
        log.error("Failed to initialize GenAI client: %s", err)
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"GenAI Client Error: {err}. Please ensure GOOGLE_API_KEY is set in .env."
        }))
        await websocket.close()
        return

    # Models to connect in priority order
    candidate_models = [MODEL, "gemini-2.5-flash-native-audio-latest", "gemini-3.1-flash-live-preview"]
    # Deduplicate while preserving order
    models_to_try = list(dict.fromkeys([m for m in candidate_models if m]))

    session = None
    connected_model = None

    for m in models_to_try:
        try:
            log.info("Attempting live connection with model: %s", m)
            session_ctx = genai_client.aio.live.connect(model=m, config=config)
            session = await session_ctx.__aenter__()
            connected_model = m
            log.info("Gemini Live session established successfully with model: %s", m)
            break
        except Exception as conn_err:
            log.warning("Connection failed for model %s: %s", m, conn_err)

    if not session:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to connect to any Gemini Live model. Please check your API key / model permissions."
        }))
        await websocket.close()
        return

    try:
        await websocket.send_text(json.dumps({
            "type": "session_ready",
            "model": connected_model,
            "voice": VOICE,
            "message": "Gemini Orchestrator is listening..."
        }))

        async def upstream():
            """Reads 16kHz PCM chunks from WebSocket and streams to Gemini Live."""
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    log.info("Upstream: Client disconnected.")
                    return

                raw_bytes = msg.get("bytes")
                if raw_bytes:
                    # Feed raw 16kHz mono audio directly into the live session stream
                    await session.send_realtime_input(
                        audio=types.Blob(data=raw_bytes, mime_type="audio/pcm;rate=16000")
                    )
                elif msg.get("text"):
                    # Handle text instructions / control payloads
                    try:
                        data = json.loads(msg["text"])
                        if data.get("type") == "text_prompt" and data.get("text"):
                            await session.send_client_content(
                                turns=[types.Content(role="user", parts=[types.Part.from_text(text=data["text"])])],
                                turn_complete=True
                            )
                    except Exception:
                        pass

        async def handle_response(response):
            """Handles server content (audio chunks, transcriptions) and tool calls."""
            sc = getattr(response, "server_content", None)
            tc = getattr(response, "tool_call", None)

            if sc is not None:
                it = getattr(sc, "input_transcription", None)
                ot = getattr(sc, "output_transcription", None)
                mt = getattr(sc, "model_turn", None)

                if it and getattr(it, "text", None):
                    await websocket.send_text(json.dumps({
                        "type": "transcript",
                        "role": "user",
                        "text": it.text
                    }))

                if ot and getattr(ot, "text", None):
                    await websocket.send_text(json.dumps({
                        "type": "transcript",
                        "role": "gemini",
                        "text": ot.text
                    }))

                if mt and getattr(mt, "parts", None):
                    for part in mt.parts:
                        idata = getattr(part, "inline_data", None)
                        if idata and getattr(idata, "data", None):
                            # 24kHz raw PCM voice chunk from Gemini
                            await websocket.send_bytes(idata.data)

                if getattr(sc, "interrupted", None):
                    log.info("Gemini output was interrupted (barge-in triggered).")
                    await websocket.send_text(json.dumps({"type": "interrupted"}))

            if tc:
                results = []
                for fc in tc.function_calls:
                    args = dict(getattr(fc, "args", None) or {})
                    cmd, result = dispatch_tool(fc.name, args)
                    if cmd:
                        await websocket.send_text(json.dumps({
                            "type": "tool_event",
                            "tool": fc.name,
                            **cmd
                        }))
                    results.append(types.FunctionResponse(id=fc.id, name=fc.name, response=result))

                # Immediate non-blocking response back to the model
                await session.send_tool_response(function_responses=results)

        async def downstream():
            """
            Continuously reads responses across multi-turn conversations.
            Outer loop handles turn regeneration.
            """
            empty_turns = 0
            while True:
                got_items = 0
                try:
                    async for response in session.receive():
                        got_items += 1
                        await handle_response(response)
                except Exception as e:
                    log.warning("Downstream receive ended: %s", e)
                    return

                if got_items == 0:
                    empty_turns += 1
                    if empty_turns >= 2:
                        log.info("Session closed naturally.")
                        return
                else:
                    empty_turns = 0  # Turn completed; ready for next turn

        up_task = asyncio.create_task(upstream(), name="voice_upstream")
        down_task = asyncio.create_task(downstream(), name="voice_downstream")

        done, pending = await asyncio.wait(
            {up_task, down_task},
            return_when=asyncio.FIRST_COMPLETED
        )

        for t in done:
            exc = t.exception()
            if exc:
                log.error("%s failed with error: %r", t.get_name(), exc)
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"{type(exc).__name__}: {exc}"
                    }))
                except Exception:
                    pass

        for t in pending:
            t.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    except WebSocketDisconnect:
        log.info("WebSocket disconnected.")
    except Exception as e:
        log.exception("Error in Live Voice session handler: %s", e)
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"{type(e).__name__}: {e}"
            }))
        except Exception:
            pass
    finally:
        if session_ctx:
            try:
                await session_ctx.__aexit__(None, None, None)
            except Exception:
                pass
        log.info("Voice connection session terminated.")
