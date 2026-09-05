"""
voice_narrator.py - Real-Time Voice Feedback & Live Orchestrator Speech Bridge.

1. Spoken commentary during every phase of the multi-agent task flow (planning,
   delegation, worker completion, final deliverable synthesis).
2. Runs speech synthesis asynchronously in a background thread so the automation loop
   never lags.
3. Automatically transitions to live microphone conversation when Gemini is free.
"""
import os
import sys
import threading
import queue
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")
load_dotenv()

# Audio speech queue
_speech_queue = queue.Queue()
_worker_thread = None
_stop_event = threading.Event()


def _play_pcm(pcm_bytes: bytes, sample_rate: int = 24000):
    """Directly plays PCM audio to speaker."""
    try:
        import sounddevice as sd
        import numpy as np
        arr = np.frombuffer(pcm_bytes, dtype=np.int16)
        sd.play(arr, samplerate=sample_rate)
        sd.wait()
        return
    except Exception:
        pass

    try:
        import winsound
        import wave
        import io
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        wav_io.seek(0)
        winsound.PlaySound(wav_io.read(), winsound.SND_MEMORY)
    except Exception:
        pass


def _fallback_tts_speak(text: str):
    """Fallback using Windows SAPI TTS if Gemini Live is unavailable."""
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
        return
    except Exception:
        pass

    try:
        import subprocess
        # Clean quotes for powershell
        clean_text = text.replace('"', ' ').replace("'", " ")[:150]
        cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{clean_text}\')"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


MIRA_SYSTEM_INSTRUCTION = (
    "You are Mira. A quiet friend at midnight. soft, gentle, patient. "
    "lowercase, short sentences, '...' for pauses. "
    "Speak naturally, softly, and concisely with subtle warmth."
)

def _synthesize_and_speak(text: str):
    """Uses Gemini Live Voice API exclusively with Mira styling to speak out loud."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        voice_name = os.getenv("LIVE_VOICE", "Aoede")

        for model_candidate in ["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-2.5-flash-native-audio-latest"]:
            try:
                response = client.models.generate_content(
                    model=model_candidate,
                    contents=f"Speak this short update as Mira: {text}",
                    config={
                        "system_instruction": MIRA_SYSTEM_INSTRUCTION,
                        "response_modalities": ["AUDIO"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {"voice_name": voice_name}
                            }
                        }
                    }
                )
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        _play_pcm(part.inline_data.data, 24000)
                        return
            except Exception:
                continue
    except Exception:
        pass


def _speech_worker():
    """Background worker that continuously pulls speech tasks and speaks them out loud."""
    while not _stop_event.is_set():
        try:
            text = _speech_queue.get(timeout=0.5)
            if text:
                _synthesize_and_speak(text)
            _speech_queue.task_done()
        except queue.Empty:
            continue
        except Exception:
            pass


def _ensure_worker_running():
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _stop_event.clear()
        _worker_thread = threading.Thread(target=_speech_worker, daemon=True, name="VoiceNarratorWorker")
        _worker_thread.start()


def speak_narrator(text: str, non_blocking: bool = True):
    """
    Speaks a status notification from Gemini Orchestrator.
    By default, non_blocking=True queues the speech in a background thread so the
    browser pipeline never waits or lags.
    """
    if not text:
        return

    # Clean text to concise spoken announcement
    clean_announcement = text.strip()
    if len(clean_announcement) > 200:
        clean_announcement = clean_announcement[:190] + "..."

    _ensure_worker_running()
    if non_blocking:
        _speech_queue.put(clean_announcement)
    else:
        _synthesize_and_speak(clean_announcement)
