# 📁 JSON Configuration & State Directory (`json/`)

This directory serves as the centralized, persistent data store for the Agentic Web Operations platform. All runtime state, neural memories, process queues, and MCP server registries are persisted here.

---

## 🗄️ File Catalog & Descriptions

| File | Purpose | Description |
|---|---|---|
| `mcp_config.json` | **MCP Server Registry** | Stores configurations for all registered Model Context Protocol (MCP) servers using the standard 9-field schema. |
| `agent_status.json` | **Agent State Pool** | Tracks the live status (`FREE`, `BUSY`, `LEADER`), active task assignments, and roles of all 10 AI models. |
| `subagents.json` | **Squad Rosters** | Contains saved multi-agent preset squads, specialist pairings, and custom pipelines. |
| `memory.json` | **Neural Memory Vault** | Stores cross-mission memory nodes, architectural decisions, and key factual summaries for continuity. |
| `tracked_pids.json` | **Process Tree Queue** | Disk-persisted queue of active browser and automation PIDs for guaranteed clean process termination. |

---

## 📐 Standard 9-Field MCP Server Schema

All entries in `mcp_config.json` strictly conform to the following schema:

```json
{
  "mcpServers": {
    "server_id": {
      "name": "Human-readable Display Name",
      "repository": "https://github.com/org/repo.git",
      "api_endpoint": "https://api.github.com/repos/org/repo/contents",
      "raw_base_url": "https://raw.githubusercontent.com/org/repo/main",
      "version": "1.0.0",
      "skills_count": 24,
      "status": "active",
      "type": "remote-git-provider",
      "description": "Detailed explanation of server capabilities and tools."
    }
  }
}
```

---

## 🔒 State Transition Rules (`agent_status.json`)

1. **`LEADER`**: Assigned permanently to Google Gemini during pipeline orchestration.
2. **`BUSY`**: Assigned to specialist workers during task execution and debate rounds.
3. **`FREE`**: Assigned to idle agents ready for immediate task dispatch.
