Function Calling & Remote Tools
================================

Agents can autonomously declare, discover, and invoke local and remote tools.

Native Provider Functions
-------------------------
* **Google Gemini Tool Declarations**: Function call dispatching with parameter validation.
* **OpenAI Function Calling**: Structured JSON schemas with auto-execution.
* **Anthropic Tool Use**: Direct tool invocations formatted for Claude 3.5 models.

Model Context Protocol (MCP)
----------------------------
Connects agents to remote MCP servers via `stdio`, `streamable_http`, or `sse` transports.
