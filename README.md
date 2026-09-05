# ⚡ Agentic Web: Autonomous Multi-Agent Desktop Operations Platform

> **Organization**: [MaxMasAI](https://github.com/MaxMasAI)  
> **Owner & Creator**: [Sahil Kumar Dhala](https://github.com/Sahilkumardhala)  
> **License**: [MIT License](LICENSE)  

An enterprise-grade autonomous multi-agent operating system and native **PySide6 Desktop Application** designed for synchronized AI model orchestration, dynamic Model Context Protocol (MCP) tool execution, senior engineering skill integration, and real-time live voice control.

---

## 🌟 Key Architecture & Capabilities

### 👑 1. Multi-Agent Command Hierarchy (10 Active Models)
- **👑 Master Leader & Orchestrator:**
  - **Google Gemini**: Decomposes user missions into atomic subtasks, assigns work equally across available specialist models, and conducts final editorial approval.
- **🔬 Research & Technical Computing Cluster:**
  - **DeepSeek**: Creative ideation, algorithmic design, and test-driven code implementation.
  - **Perplexity AI**: Real-time factual citations and live web knowledge verification.
  - **Nvidia NIM AI**: High-performance GPU compute advisor and web performance profiling.
- **✍️ Content, Copy & Editorial Cluster:**
  - **OpenAI ChatGPT (GPT-4o)**: Campaign synthesis, client copywriting, and document packaging.
  - **Anthropic Claude**: Editorial review, security boundary auditing, and accessibility audits.
  - **Mistral Le Chat**: European multilingual translation and logic verification.
- **🎨 Creative, Media & Operations Cluster:**
  - **Meta AI**: Viral trend analysis and platform engagement optimization.
  - **OpenAI DALL-E 3**: Graphic asset design, composition, and visual prompt engineering.
  - **Microsoft Copilot**: Enterprise workflow coordination and office document integration.

---

## 🔌 2. Model Context Protocol (MCP) Subsystem
- **Addy Osmani Agent Skills (`https://github.com/addyosmani/agent-skills.git`)**:
  - Live remote integration connecting 24 senior engineering skills (Spec-Driven Development, TDD, Architectural Review, Code Simplification, Security & A11y Audits).
  - Dynamically injected into each agent's execution prompt according to their task role.
- **CitroLabs Ego-Lite Parallel Browser (`https://github.com/citrolabs/ego-lite.git`)**:
  - Isolated Chromium spaces, authenticated Chrome session reuse, and high-speed CDP DOM extraction.
- **Standardized 9-Field Schema**:
  - All MCP configurations in `json/mcp_config.json` conform strictly to the 9-field schema (`name`, `repository`, `api_endpoint`, `raw_base_url`, `version`, `skills_count`, `status`, `type`, `description`).

---

## 🖥️ 3. Futuristic PySide6 Desktop Console
- **🛰️ Mission Control (Home):** Interactive telemetry cards (`Tasks Completed`, `Memory Items`, `Squad Roster`, `Agent Skills`, `Assets Saved`, `Active Missions`), Gemini Direct Task Dispatcher, and real-time Multi-Agent Hierarchy Monitor.
- **🌳 Agent Command Hierarchy Tree:** Switchable tree & grid view with Gemini Leader at the root branching into the specialist clusters with live `🟢 FREE` vs `🟡 BUSY` indicators and agent activity inspector.
- **🚀 Task Dispatch Console:** Custom agent loop selector, latency & communication speed tuner, real-time streaming log terminal, and process manager.
- **🎮 Playground Studio:** Live HTML/CSS/JS sandbox with real-time deliverable preview, isolated Python execution sandbox, and task code extractor.
- **🤖 Agent Squads:** Autonomous AI Squad generator based on project scope, 1-click fast presets, and repeated pattern auto-learner.
- **📋 Mission Archive:** Searchable mission history with 5 deep inspection tabs (Gemini Plan, Worker Outputs, Final Approved Result, Live Sandbox, Downloaded Assets) and full-resolution screenshot lightboxes.
- **📁 Folder Explorer:** Direct inline code inspector and preview for `json/`, `tasks/`, `logs/`, `downloads/`, `visuals/`, and `tests/` with safe file deletion protection.
- **🔌 MCP Service Hub:** Live tool tester with dynamic parameter forms, server registry, parameter schema explorer, and custom server registration.
- **🧠 Neural Memory Vault:** Cross-mission factual memory search, semantic categorization, importance rating, pin priority, deduplication, and `RULES.md` exporter.

---

## 📁 Directory Structure

| Directory | Purpose |
|---|---|
| **`gui/`** | PySide6 Desktop UI architecture (Theme, Widgets, Pages). |
| **`json/`** | Centralized storage for MCP configs, agent status, squads, memories, and PID queues. |
| **`tasks/`** | Historical task archives, subtask breakdowns, debate logs, and deliverables. |
| **`logs/`** | Real-time console logs, telemetry streams, and system diagnostics. |
| **`downloads/`** | Generated images, code bundles, and client assets auto-downloaded from agents. |
| **`visuals/`** | Browser verification screenshots captured at each execution milestone. |
| **`tests/`** | Automated unit tests for MCP services, agent status, and skills router. |

---

## 🚀 Quick Start & Installation via GitHub

### 1. Clone the Repository
```bash
git clone https://github.com/MaxMasAI/agentic-web.git
cd agentic-web
```

### 2. Create & Activate Python Virtual Environment (`.venv`)
> [!TIP]
> Always create an isolated virtual environment to prevent dependency conflicts with system packages.

#### On Windows (PowerShell / Command Prompt):
```powershell
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate

# Upgrade pip and install all dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### On macOS & Linux (Bash / Zsh):
```bash
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip and install all dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

*(Alternatively, Windows users can simply run `install.bat` and Unix users can run `./install.sh` to automate this entire process).*

---

### 3. Launch the Application

#### Launch Full Suite (Voice Server Daemon + PySide6 Desktop GUI):
```cmd
run.bat
```

#### Launch Desktop GUI Directly:
```bash
python app.py
```

### 4. Run Test Suites
```bash
python -m unittest discover tests
```

## 🐳 5. Run with Docker Compose
If you prefer containerized execution, you can run the app seamlessly using the provided `docker-compose.yml`.

```bash
docker compose up --build
```
*(Note: Since this is a GUI application, it automatically passes your host's X11 server socket. This is primarily supported on Linux/WSL).*

---

## 📦 6. Build Standalone Executable
You can easily compile Agentic Web into a standalone, portable Windows executable (`.exe`) that doesn't require Python or virtual environments!

1. Open your terminal in the project root.
2. Run the executable builder:
```bash
python STD_EXE.py
```
3. Your portable app will be generated in `dist/agentic-web/`. You can simply double-click `agentic-web.exe` to start the dashboard!

---

## 👥 Organization & Ownership

- **Organization**: [MaxMasAI](https://github.com/MaxMasAI)
- **Founder & Owner**: [Sahil Kumar Dhala](https://github.com/Sahilkumardhala)
- **License**: Released under the open-source [MIT License](LICENSE).

*© 2026 MaxMasAI. All rights reserved.*


