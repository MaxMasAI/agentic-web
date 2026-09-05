"""
gotcha_send_client_content.py - Common Gemini Live SDK Mistake vs Correct Way.

Prompting an LLM or coding agent with "send the user's mic audio to the Gemini Live session"
very often leads to `send_client_content` — which is the standard method for discrete turns.
However, live audio is a continuous realtime stream. Using `send_client_content` causes
the live turn to never trigger, resulting in complete dead air.

The fix: use `send_realtime_input`.
"""
from google.genai import types


# ❌ THE WRONG WAY — Discrete turn method (causes silence / dead air in Live API)
async def send_mic_audio_WRONG(session, pcm_16k: bytes):
    await session.send_client_content(
        turns=types.Content(
            role="user",
            parts=[types.Part(inline_data=types.Blob(data=pcm_16k, mime_type="audio/pcm;rate=16000"))],
        )
    )


# ✅ THE RIGHT WAY — Live input continuous stream
async def send_mic_audio_RIGHT(session, pcm_16k: bytes):
    await session.send_realtime_input(
        audio=types.Blob(data=pcm_16k, mime_type="audio/pcm;rate=16000")
    )
