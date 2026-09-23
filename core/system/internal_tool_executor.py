"""
core/system/internal_tool_executor.py - Universal Internal Tool Execution & Autonomous Agent Engine
Coordinates all internal workstation tools (System OS, Web Search, File I/O, Neural Memory,
Wikipedia, MCP Hub, MaxMasAI Harness, Token Manager) for both direct interactive slash control
and autonomous agent self-invocation.
"""

import os
import sys
import json
import re
import time
from typing import Dict, Any, List, Optional, Union

# Dynamic imports with graceful fallbacks
try:
    from services.system_os_service import SystemOSService
except Exception:
    SystemOSService = None

try:
    from services.system_app_launcher import is_system_app_task, execute_system_app_launch
except Exception:
    is_system_app_task = lambda t: False
    execute_system_app_launch = lambda t: ""

try:
    from services.file_io_service import FileIOService
except Exception:
    FileIOService = None

try:
    from services.web_search import WebSearchService
except Exception:
    WebSearchService = None

try:
    from services.wikipedia_service import WikipediaService
except Exception:
    WikipediaService = None

try:
    from services.context_storage import ContextStorage
except Exception:
    ContextStorage = None

try:
    from services.mcp_client import MCPClient
except Exception:
    MCPClient = None

try:
    from services.token_manager import TokenManager
except Exception:
    TokenManager = None

try:
    from core.harness.maxmasai_harness import MaxMasAIHarnessEngine
except Exception:
    MaxMasAIHarnessEngine = None


class InternalToolExecutor:
    """
    Centralized executor for all internal agent workstation tools.
    Supports both direct slash dispatch and autonomous multi-agent tool resolution.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.file_service = FileIOService() if FileIOService else None
        self.os_service = SystemOSService() if SystemOSService else None
        self.web_service = WebSearchService() if WebSearchService else None
        self.wiki_service = WikipediaService() if WikipediaService else None
        self.memory_service = ContextStorage() if ContextStorage else None
        self.mcp_client = MCPClient() if MCPClient else None

    # =========================================================================
    # 1. Direct Tool Invocations
    # =========================================================================

    def execute_os_command(self, command: str) -> Dict[str, Any]:
        """Executes system OS command or launches desktop application."""
        clean_cmd = (command or "").strip()
        if not clean_cmd:
            return {"success": False, "error": "Empty OS command provided."}

        # Check if desktop application launch
        if is_system_app_task(clean_cmd):
            res_msg = execute_system_app_launch(clean_cmd)
            return {"success": True, "tool": "system_app_launcher", "output": res_msg, "command": clean_cmd}

        if self.os_service:
            res = self.os_service.sys_exec(clean_cmd)
            stdout = res.get("stdout", "")
            stderr = res.get("stderr", "")
            output = stdout if stdout else stderr
            return {
                "success": res.get("success", False),
                "tool": "system_os",
                "output": output or "Command executed successfully.",
                "command": clean_cmd
            }

        # Fallback subprocess
        import subprocess
        try:
            p = subprocess.run(clean_cmd, shell=True, capture_output=True, text=True, timeout=15)
            out = p.stdout or p.stderr or "Executed (returncode=0)"
            return {"success": p.returncode == 0, "tool": "system_os", "output": out, "command": clean_cmd}
        except Exception as e:
            return {"success": False, "tool": "system_os", "error": str(e), "command": clean_cmd}

    def execute_web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Performs real-time web search across DuckDuckGo, Google CSE, or Bing."""
        clean_q = (query or "").strip()
        if not clean_q:
            return {"success": False, "error": "Empty search query."}

        if self.web_service:
            try:
                results = self.web_service.search(clean_q, max_results=num_results)
                formatted = []
                for idx, r in enumerate(results, 1):
                    formatted.append(f"{idx}. **{r.get('title', 'Result')}**\n   {r.get('snippet', '')}\n   URL: {r.get('link', r.get('url', ''))}")
                
                output_text = "\n\n".join(formatted) if formatted else "No web results found."
                return {
                    "success": True,
                    "tool": "web_search",
                    "query": clean_q,
                    "results": results,
                    "output": output_text
                }
            except Exception as e:
                return {"success": False, "tool": "web_search", "error": str(e), "query": clean_q}

        return {"success": False, "tool": "web_search", "error": "Web search service not available."}

    def execute_wikipedia(self, query: str) -> Dict[str, Any]:
        """Searches Wikipedia for factual summaries."""
        clean_q = (query or "").strip()
        if not clean_q:
            return {"success": False, "error": "Empty Wikipedia query."}

        if self.wiki_service:
            try:
                res = self.wiki_service.search_summary(clean_q)
                return {
                    "success": True,
                    "tool": "wikipedia",
                    "query": clean_q,
                    "title": res.get("title", clean_q),
                    "output": res.get("summary", "No Wikipedia summary found."),
                    "url": res.get("url", "")
                }
            except Exception as e:
                return {"success": False, "tool": "wikipedia", "error": str(e), "query": clean_q}

        return {"success": False, "tool": "wikipedia", "error": "Wikipedia service not available."}

    def execute_file_operation(self, operation: str, path: str, content: str = "") -> Dict[str, Any]:
        """Performs read, write, list, or search on local files."""
        if not self.file_service:
            return {"success": False, "tool": "file_io", "error": "File IO service not available."}

        op = (operation or "read").strip().lower()
        if op in ("read", "cat", "view"):
            res = self.file_service.read_file(path)
            if res.get("success"):
                return {"success": True, "tool": "file_io", "operation": op, "path": path, "output": res.get("content", "")}
            return {"success": False, "tool": "file_io", "error": res.get("error", "Read failed")}

        elif op in ("write", "create", "save"):
            res = self.file_service.write_file(path, content, overwrite=True)
            return {"success": res.get("success", False), "tool": "file_io", "operation": op, "path": path, "output": f"File written ({res.get('size_bytes', 0)} bytes)"}

        elif op in ("list", "ls", "dir"):
            target_dir = path if path else "."
            res = self.file_service.list_directory(target_dir) if hasattr(self.file_service, "list_directory") else None
            if res:
                return {"success": True, "tool": "file_io", "operation": op, "output": str(res)}
            # fallback list
            try:
                items = os.listdir(target_dir)
                return {"success": True, "tool": "file_io", "operation": op, "output": "\n".join(items[:50])}
            except Exception as e:
                return {"success": False, "tool": "file_io", "error": str(e)}

        elif op in ("search", "grep", "find"):
            res = self.file_service.search_files(path if path else content) if hasattr(self.file_service, "search_files") else None
            return {"success": True, "tool": "file_io", "operation": op, "output": str(res or "No search matches.")}

        return {"success": False, "tool": "file_io", "error": f"Unknown file operation '{op}'"}

    def execute_memory_operation(self, action: str, query_or_text: str) -> Dict[str, Any]:
        """Searches or saves neural memory items."""
        if not self.memory_service:
            return {"success": False, "tool": "memory", "error": "Memory service not available."}

        act = (action or "search").strip().lower()
        if act in ("search", "find", "query"):
            try:
                mems = self.memory_service.search_context(query_or_text) if hasattr(self.memory_service, "search_context") else []
                out_lines = []
                for m in mems[:10]:
                    txt = m.get("text", m.get("content", str(m)))
                    out_lines.append(f"• {txt}")
                output_str = "\n".join(out_lines) if out_lines else "No relevant memories found."
                return {"success": True, "tool": "memory", "action": act, "output": output_str, "count": len(mems)}
            except Exception as e:
                return {"success": False, "tool": "memory", "error": str(e)}

        elif act in ("add", "save", "record", "store"):
            try:
                if hasattr(self.memory_service, "add_memory"):
                    self.memory_service.add_memory(query_or_text)
                elif hasattr(self.memory_service, "save_context"):
                    self.memory_service.save_context("user_note", query_or_text)
                return {"success": True, "tool": "memory", "action": act, "output": f"Memory stored: '{query_or_text[:60]}...'"}
            except Exception as e:
                return {"success": False, "tool": "memory", "error": str(e)}

        return {"success": False, "tool": "memory", "error": f"Unknown memory action '{act}'"}

    def execute_mcp_tool(self, server_or_tool: str, args_json: str = "{}") -> Dict[str, Any]:
        """Executes a tool on an active MCP server or queries registered MCP tools."""
        if not self.mcp_client:
            return {"success": False, "tool": "mcp", "error": "MCP client service not available."}

        try:
            parsed_args = {}
            if args_json.strip():
                try:
                    parsed_args = json.loads(args_json)
                except Exception:
                    parsed_args = {"input": args_json}

            if hasattr(self.mcp_client, "call_tool"):
                res = self.mcp_client.call_tool(server_or_tool, parsed_args)
                return {"success": True, "tool": "mcp", "target": server_or_tool, "output": str(res)}
            elif hasattr(self.mcp_client, "list_tools"):
                tools = self.mcp_client.list_tools()
                return {"success": True, "tool": "mcp", "output": f"Available MCP Tools: {tools}"}
        except Exception as e:
            return {"success": False, "tool": "mcp", "error": str(e)}

        return {"success": False, "tool": "mcp", "error": "MCP execution not handled."}

    # =========================================================================
    # 2. Autonomous Tool Detection for Agents & Prompts
    # =========================================================================

    def detect_and_auto_execute_tools(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Evaluates a natural language user query and autonomously determines if
        an internal workstation tool should be pre-executed before LLM reasoning.
        
        Returns None if pure conversational/reasoning task, or tool result dict.
        """
        p_lower = (prompt or "").lower().strip()
        if not p_lower:
            return None

        # 1. Direct System/App Launch Intent
        if is_system_app_task(prompt):
            return self.execute_os_command(prompt)

        # 2. Real-Time Web Search Intent
        web_triggers = [
            "search the web for", "search web for", "find online", "google for",
            "look up online", "latest news on", "current weather", "what is the price of"
        ]
        for trig in web_triggers:
            if trig in p_lower:
                q = p_lower.split(trig, 1)[1].strip()
                if q:
                    return self.execute_web_search(q)

        # 3. Wikipedia Search Intent
        wiki_triggers = ["who was", "who is", "what is the history of", "wikipedia summary of", "wiki for", "define "]
        for trig in wiki_triggers:
            if p_lower.startswith(trig):
                q = p_lower[len(trig):].strip(" ?.")
                if q and len(q.split()) <= 6:
                    return self.execute_wikipedia(q)

        # 4. File Reading Intent
        file_read_triggers = ["read file", "open file", "contents of", "view file", "cat "]
        for trig in file_read_triggers:
            if trig in p_lower:
                path_part = p_lower.split(trig, 1)[1].strip().split()[0].strip("\"'`")
                if path_part:
                    return self.execute_file_operation("read", path_part)

        # 5. Memory Search Intent
        mem_triggers = ["what do we remember about", "search memory for", "recall about", "check memories for"]
        for trig in mem_triggers:
            if trig in p_lower:
                q = p_lower.split(trig, 1)[1].strip(" ?.")
                if q:
                    return self.execute_memory_operation("search", q)

        return None

    @staticmethod
    def format_tool_result_for_agent(tool_res: Dict[str, Any]) -> str:
        """Formats an internal tool result into an explicit markdown block for LLM ingestion."""
        if not tool_res:
            return ""

        tool_name = tool_res.get("tool", "internal_tool").upper()
        output = tool_res.get("output") or tool_res.get("error") or ""
        return (
            f"\n\n```[INTERNAL_TOOL_EXECUTION: {tool_name}]\n"
            f"{output}\n"
            f"```\n"
        )
