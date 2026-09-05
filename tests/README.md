# 🧪 Test Suite Directory (`tests/`)

This directory contains automated unit tests and integration test suites for all backend modules, MCP servers, agent pool state transitions, and skill routing engines.

---

## 📂 Test Suites Overview

| Test File | Target Module | What is Verified |
|---|---|---|
| `test_mcp_service.py` | `mcp_service.py` | Validates MCP server registration, dynamic tool schema discovery, Addy Osmani skills retrieval, and CitroLabs Ego-Lite browser tools. |
| `test_agent_status.py` | `agent_status.py` | Validates agent pool state transitions (`FREE` ➔ `BUSY` ➔ `FREE`), leader assignment, and pool resets. |
| `test_agent_skills_router.py` | `agent_skills_router.py` | Validates dynamic role-based mapping of Addy Osmani senior engineering skills across all 10 AI models. |

---

## 🏃 Running Tests

To execute all test suites simultaneously, run:

```bash
python -m unittest discover tests
```

To run an individual test suite:

```bash
python -m unittest tests/test_mcp_service.py
python -m unittest tests/test_agent_status.py
python -m unittest tests/test_agent_skills_router.py
```
