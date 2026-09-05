Configuration & Settings
========================

Centralized configuration is managed via `services/app_config.py` and persisted in `json/app_config.json`.

Configuration Categories
------------------------
1. **General**: Startup settings, system tray minimization, temp cache cleanup.
2. **API Keys**: OAuth 2.0 PKCE browser authentication and direct API key vault.
3. **Layout**: Rendering style, window zoom, font sizes, DPI factor, message collapse limits.
4. **Files & Attachments**: Upload directories, native provider upload toggles, RAG models.
5. **Context**: SQLite `db.sqlite` multi-turn memory, auto-titling models, pagination batching.
6. **Remote Tools**: Model Context Protocol (MCP) servers and remote function calling.
7. **Security**: Server credential sanitization, OS command safeguards (`sys_exec`).
