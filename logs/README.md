# 📜 Logs & Telemetry Directory (`logs/`)

This directory captures real-time console telemetry, multi-agent communication logs, and runtime diagnostics for monitoring and debugging.

---

## 📄 Log Files Overview

| Log Type | Filename Pattern | Content Description |
|---|---|---|
| **Mission Telemetry** | `mission_YYYYMMDD_HHMMSS.log` | Complete stream of step-by-step orchestrations, prompt inputs, and agent responses. |
| **Debate Transcripts** | `debate_YYYYMMDD_HHMMSS.log` | Turn-by-turn critiques, counter-arguments, and consensus formation during multi-agent discussions. |
| **System Diagnostics** | `error.log` / `stream.log` | Process life-cycle events, socket connections, CDP port status (9222), and cleanup hooks. |

---

## ⚡ Real-Time Streaming

- The Streamlit Web UI (`http://localhost:8501`) polls active logs in `logs/` to stream live execution progress directly into the **🚀 Task Dispatch** console.
- Log formatting utilizes ANSI color codes for terminal clarity and structured timestamps (`[YYYY-MM-DD HH:MM:SS]`).
