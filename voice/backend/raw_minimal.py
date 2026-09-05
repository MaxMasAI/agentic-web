"""
raw_minimal.py - Gemini Live Voice Primitive in ~40 lines.

The raw primitive extracted directly from the official Google GenAI Live demo:
open session -> send 16k PCM mic up -> receive 24k PCM voice down -> play.

Run:
    uvicorn voice.backend.raw_minimal:app --port 8000
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()

from fastapi import FastAPI, WebSocket
from google import genai
from google.genai import types

MODEL = os.getenv("LIVE_MODEL", "gemini-3.1-flash-live-preview")
CONFIG = {
    "response_modalities": ["AUDIO"],
    "speech_config": {
        "voice_config": {
            "prebuilt_voice_config": {"voice_name": os.getenv("LIVE_VOICE", "Aoede")}
        }
    },
}

app = FastAPI(title="Gemini Live Voice Minimal")


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    client = genai.Client()
    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:   # 1. OPEN

        async def send_mic():                          # 2. SEND — Mic 16 kHz PCM → Gemini
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    return
                if chunk := msg.get("bytes"):          # 16 kHz PCM
                    await session.send_realtime_input(
                        audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                    )

        async def play_voice():                        # 3. RECEIVE — Gemini → 24 kHz PCM
            while True:                                # The Gotcha: receive() is per-turn
                async for response in session.receive():
                    turn = getattr(response.server_content, "model_turn", None)
                    for part in (turn.parts if turn else []):
                        if part.inline_data and part.inline_data.data:
                            await websocket.send_bytes(part.inline_data.data)

        up, down = asyncio.create_task(send_mic()), asyncio.create_task(play_voice())
        _, pending = await asyncio.wait({up, down}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
