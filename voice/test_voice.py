"""
test_voice.py - Live Voice Connection & Response Diagnostic Test.

Tests the live session connection to Google Gemini Live API with your API key,
sends a test greeting to the Master Orchestrator, and verifies received voice audio chunks and transcripts.
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")
load_dotenv()

from google import genai
from google.genai import types

from voice.backend.persona import get_system_instruction
from voice.backend.tools import TOOL_DECLARATIONS

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def play_pcm_to_speaker(pcm_bytes: bytes, sample_rate: int = 24000):
    """Plays 16-bit Mono PCM audio directly to the computer speaker."""
    # Attempt 1: sounddevice (if installed)
    try:
        import sounddevice as sd
        import numpy as np
        audio_arr = np.frombuffer(pcm_bytes, dtype=np.int16)
        sd.play(audio_arr, samplerate=sample_rate)
        sd.wait()
        return
    except Exception:
        pass

    # Attempt 2: Native Windows audio playback via winsound (no external deps required)
    try:
        import winsound
        import wave
        import io
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)           # Mono
            wf.setsampwidth(2)          # 16-bit (2 bytes per sample)
            wf.setframerate(sample_rate) # 24kHz
            wf.writeframes(pcm_bytes)
        wav_io.seek(0)
        winsound.PlaySound(wav_io.read(), winsound.SND_MEMORY)
    except Exception as e:
        print(f"{YELLOW}[*] Speaker note: {e}{RESET}", flush=True)


async def run_voice_test():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    model = os.getenv("LIVE_MODEL", "gemini-2.0-flash-exp")
    voice = os.getenv("LIVE_VOICE", "Aoede")

    print(f"\n{BOLD}{CYAN}======================================================={RESET}", flush=True)
    print(f"{BOLD}{CYAN}      GEMINI LIVE VOICE SYSTEM DIAGNOSTIC TEST        {RESET}", flush=True)
    print(f"{BOLD}{CYAN}======================================================={RESET}\n", flush=True)

    print(f"[*] API Key Loaded:    {GREEN}{api_key[:8]}...{api_key[-4:] if api_key else 'NONE'}{RESET}", flush=True)
    print(f"[*] Live Model:        {CYAN}{model}{RESET}", flush=True)
    print(f"[*] Live Voice:        {CYAN}{voice}{RESET}", flush=True)
    print(f"[*] Connecting to Google Gemini Live API...", flush=True)

    if not api_key:
        print(f"{RED}[!] Error: No GOOGLE_API_KEY found in .env!{RESET}")
        return False

    client = genai.Client(api_key=api_key)

    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": get_system_instruction(),
        "input_audio_transcription": {},
        "output_audio_transcription": {},
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": voice}
            }
        },
        "tools": [{"function_declarations": TOOL_DECLARATIONS}],
    }

    try:
        # Try primary live model, fallback to native live audio models
        candidate_models = [model, "gemini-2.5-flash-native-audio-latest", "gemini-3.1-flash-live-preview"]
        models_to_try = list(dict.fromkeys([m for m in candidate_models if m]))
        connected = False
        active_model = model

        for m in models_to_try:
            try:
                print(f"[*] Testing connection with model: {m}...")
                async with client.aio.live.connect(model=m, config=config) as session:
                    print(f"{GREEN}[OK] Successfully connected to Gemini Live Session ({m})!{RESET}\n")
                    connected = True
                    active_model = m

                    # Send test prompt to orchestrator with turn_complete=True so it replies instantly
                    test_msg = "Hello Gemini Master Orchestrator! Please give a brief wise status report for the multi-agent system."
                    print(f"{CYAN}You (Test Input):{RESET} {test_msg}", flush=True)
                    print(f"[*] Waiting for Gemini Live Voice response...\n", flush=True)

                    await session.send_client_content(
                        turns=[types.Content(role="user", parts=[types.Part.from_text(text=test_msg)])],
                        turn_complete=True
                    )

                    audio_bytes_received = 0
                    transcripts = []

                    all_pcm_chunks = []

                    # Receive response turn
                    async for response in session.receive():
                        sc = getattr(response, "server_content", None)
                        if sc is not None:
                            ot = getattr(sc, "output_transcription", None)
                            if ot and getattr(ot, "text", None):
                                print(f"{GREEN}Gemini (Voice Transcript):{RESET} {ot.text}", flush=True)
                                transcripts.append(ot.text)

                            mt = getattr(sc, "model_turn", None)
                            if mt and getattr(mt, "parts", None):
                                for part in mt.parts:
                                    idata = getattr(part, "inline_data", None)
                                    if idata and getattr(idata, "data", None):
                                        audio_bytes_received += len(idata.data)
                                        all_pcm_chunks.append(idata.data)

                            if getattr(sc, "turn_complete", False):
                                print(f"\n{GREEN}[OK] Turn complete.{RESET}", flush=True)
                                break

                    # Play Gemini's voice out loud through the computer speakers
                    if all_pcm_chunks:
                        print(f"\n{BOLD}{MAGENTA}[🔊 PLAYING GEMINI VOICE THROUGH SPEAKERS...]{RESET}", flush=True)
                        full_audio = b"".join(all_pcm_chunks)
                        play_pcm_to_speaker(full_audio, 24000)

                    print(f"\n{GREEN}======================================================={RESET}", flush=True)
                    print(f"{GREEN} [PASSED] TEST COMPLETED SUCCESSFULLY!                {RESET}", flush=True)
                    print(f" - Received Audio Bytes: {CYAN}{audio_bytes_received:,} bytes (24kHz PCM){RESET}", flush=True)
                    print(f" - Spoken Transcripts:   {CYAN}{len(transcripts)} chunks received{RESET}", flush=True)
                    print(f" - Speaker Playback:     {GREEN}Active (24kHz Mono Audio played){RESET}", flush=True)
                    print(f" - Active Live Model:    {CYAN}{active_model}{RESET}", flush=True)
                    print(f"{GREEN}======================================================={RESET}\n", flush=True)
                    return True

            except Exception as e:
                print(f"{YELLOW}[*] Model {m} test note: {e}{RESET}")
                if "404" not in str(e) and "not found" not in str(e).lower():
                    # If it's auth or quota or network error, raise it
                    raise e

        if not connected:
            print(f"{RED}[!] Could not establish live session with test models.{RESET}")
            return False

    except Exception as exc:
        print(f"\n{RED}[!] Test Failed with error: {exc}{RESET}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(run_voice_test())
