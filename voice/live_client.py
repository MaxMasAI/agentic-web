"""
live_client.py - Local Terminal / Mic Audio Client for Gemini Live Orchestrator.

Connects to the Gemini Voice Backend over WebSocket (ws://127.0.0.1:8000/ws).
Streams local microphone (16kHz PCM) and plays back Gemini voice (24kHz PCM).
Displays live speech transcriptions and tool events in real time.
"""
import asyncio
import json
import sys
import logging
from pathlib import Path

# Terminal ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

logging.basicConfig(level=logging.WARNING)

try:
    import websockets
except ImportError:
    print(f"{YELLOW}[!] 'websockets' package required. Run: pip install websockets{RESET}")
    websockets = None

try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


async def run_voice_client(ws_url="ws://127.0.0.1:8000/ws"):
    """Connects to the Gemini Live Voice backend and streams audio & transcripts."""
    if not websockets:
        print(f"{YELLOW}[!] websockets is required. Please install it with 'pip install websockets'{RESET}")
        return

    print(f"\n{BOLD}{GREEN}====================================================={RESET}")
    print(f"{BOLD}{GREEN}    Gemini Orchestrator - Live Voice Session         {RESET}")
    print(f"{BOLD}{GREEN}====================================================={RESET}")
    print(f"Connecting to: {CYAN}{ws_url}{RESET}")

    try:
        async with websockets.connect(ws_url) as ws:
            print(f"{GREEN}[OK] Connected to Gemini Orchestrator Live Voice!{RESET}\n")

            audio_stream_out = None
            if AUDIO_AVAILABLE:
                # 24kHz Mono 16-bit PCM playback stream
                audio_stream_out = sd.RawOutputStream(
                    samplerate=24000,
                    channels=1,
                    dtype='int16'
                )
                audio_stream_out.start()

            async def receive_loop():
                """Receives audio chunks and transcripts from Gemini."""
                try:
                    async for message in ws:
                        if isinstance(message, bytes):
                            # Binary 24kHz PCM audio from Gemini
                            if audio_stream_out:
                                audio_stream_out.write(message)
                        else:
                            try:
                                payload = json.loads(message)
                                mtype = payload.get("type")

                                if mtype == "session_ready":
                                    print(f"{YELLOW}[*] {payload.get('message', 'Ready.')}{RESET}\n")
                                elif mtype == "transcript":
                                    role = payload.get("role", "unknown")
                                    text = payload.get("text", "")
                                    if role == "user":
                                        print(f"{CYAN}You:{RESET} {text}")
                                    elif role == "gemini":
                                        print(f"{GREEN}Gemini:{RESET} {text}")
                                elif mtype == "tool_event":
                                    tool = payload.get("tool", "")
                                    action = payload.get("action", "")
                                    print(f"{MAGENTA}[TOOL DISPATCH] {tool} -> {action}{RESET}")
                                elif mtype == "interrupted":
                                    print(f"{YELLOW}[* Barge-in: User interrupted Gemini]{RESET}")
                                elif mtype == "error":
                                    print(f"\033[91m[Error] {payload.get('message')}{RESET}")
                            except Exception:
                                pass
                except Exception as e:
                    print(f"{YELLOW}[Connection closed: {e}]{RESET}")

            async def send_mic_loop():
                """Captures local microphone (16kHz PCM) and streams to WebSocket."""
                if not AUDIO_AVAILABLE:
                    print(f"{YELLOW}[!] sounddevice/numpy not found. Voice playback/mic disabled.{RESET}")
                    print(f"{YELLOW}[*] You can type messages below to talk to Gemini:{RESET}")
                    while True:
                        line = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
                        if line.strip():
                            await ws.send(json.dumps({"type": "text_prompt", "text": line.strip()}))
                    return

                loop = asyncio.get_running_loop()
                queue = asyncio.Queue()

                def callback(indata, frames, time_info, status):
                    # Convert to 16-bit PCM bytes
                    queue.put_nowait(bytes(indata))

                # 16kHz Mono 16-bit PCM recording stream
                with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16', callback=callback, blocksize=2048):
                    print(f"{GREEN}[MIC ACTIVE] Speak now into your microphone (Headphones recommended)...{RESET}\n")
                    while True:
                        pcm_chunk = await queue.get()
                        await ws.send(pcm_chunk)

            await asyncio.gather(receive_loop(), send_mic_loop())

    except Exception as e:
        print(f"\033[91m[!] Failed to connect to voice backend: {e}{RESET}")
        print(f"Make sure the voice backend is running: {CYAN}python voice/run_voice.py{RESET}")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/ws"
    try:
        asyncio.run(run_voice_client(url))
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[Session ended]{RESET}")
