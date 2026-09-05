# Gemini Orchestrator — Live Multimodal Voice Backend

Bidirectional real-time Gemini Live voice backend for the **Gemini Master Orchestrator**, powered by the raw `google-genai` Live API over WebSockets.

---

## ⚡ Architecture & Features

- **Direct Live Connection**: Connects to the Gemini Live API (`client.aio.live.connect`) with no heavy frameworks.
- **Wise Orchestration Persona**: Gemini speaks calmly, authoritatively, and strategically as the Master Orchestrator.
- **Instant Tool Calling**:
  - `dispatch_mission`: Asynchronously launches engineering tasks across the specialist agent squad (DeepSeek, ChatGPT, Claude, etc.).
  - `check_agent_status`: Reports real-time states of all agents (FREE, BUSY, LEADER).
  - `query_orchestrator_memory`: Retrieves neural memories and architectural directives.
  - `list_available_agents`: Lists active specialist agents and capabilities.
- **Real-Time Turn Gotcha Solved**: Wrapped in `while True: async for response in session.receive(): ...` so conversations flow naturally across turns without dead air.
- **Continuous Mic Stream**: Sends audio via `send_realtime_input` (16 kHz PCM) rather than discrete turn content.
- **Real-Time Feedback**: Streams 24 kHz raw audio PCM, live user/orchestrator transcriptions, and barge-in signals.

---

## 📁 Directory Structure

```
voice/
├── backend/
│   ├── __init__.py
│   ├── server.py                     # Main Gemini Orchestrator Live Voice WebSocket backend
│   ├── raw_minimal.py                # 39-line minimal Gemini Live voice primitive
│   ├── persona.py                    # Master Orchestrator system prompt & instructions
│   ├── tools.py                      # Instant non-blocking tool dispatchers
│   └── gotcha_send_client_content.py # Demonstration of realtime vs discrete stream
├── live_client.py                    # Terminal / local mic & speaker audio client
├── run_voice.py                      # CLI server & client runner
└── README.md                         # Documentation
```

---

## 🚀 How to Run

### 1. Environment Configuration

Ensure your `.env` contains your Gemini Developer API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
LIVE_MODEL=gemini-3.1-flash-live-preview
LIVE_VOICE=Aoede
```

*(Available Live voices: `Aoede`, `Puck`, `Charon`, `Kore`, `Fenrir`)*

### 2. Start the Voice Backend Server

```bash
python voice/run_voice.py --port 8000
```
- **WebSocket Endpoint**: `ws://127.0.0.1:8000/ws`
- **Health Status**: `http://127.0.0.1:8000/health`

### 3. Connect via Python Voice Client

In another terminal window:
```bash
python voice/run_voice.py --client
```
*(Or connect any WebSocket client streaming 16kHz PCM to `ws://127.0.0.1:8000/ws`)*

---

## 💡 Key Lessons & Gotchas

1. **`session.receive()` is per-turn**: Calling `async for response in session.receive()` without an outer `while True` loop stops the session after the first sentence.
2. **Audio is a stream, not a turn**: Always use `session.send_realtime_input(audio=types.Blob(...))` instead of `session.send_client_content`.
3. **Instant Tool Dispatching**: Live API function calls pause the voice generation until resolved. Tool handlers in `tools.py` return immediately with confirmation so Gemini's voice never stalls.
