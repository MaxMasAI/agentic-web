"""
services/file_io_service.py - Comprehensive Files I/O Plugin & Local Filesystem Service
Enables reading, writing, appending, auto-timestamp prefixing on collision, downloading,
copying, moving, indexing with LlamaIndex/RAG, searching, and Python code execution.
"""

import os
import sys
import shutil
import time
import re
import subprocess
import urllib.request
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from services.rag_engine import query_indexed_documents, extract_text_from_file

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class FileIOService:
    """
    Local Filesystem I/O Engine.
    Handles safe file manipulations, auto-prefixed versioning on overwrite collisions,
    searching, indexing, and Python code execution.
    """
    def __init__(self, base_dir: str = DATA_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        self.indexed_files: List[str] = []

    def _resolve_path(self, path: str) -> str:
        """Resolves path relative to base_dir if not absolute."""
        if os.path.isabs(path):
            return os.path.abspath(path)
        return os.path.abspath(os.path.join(self.base_dir, path))

    # 1. Read File
    def read_file(self, path: str, limit: Optional[int] = None) -> Dict[str, Any]:
        target = self._resolve_path(path)
        if not os.path.exists(target):
            return {"success": False, "error": f"File '{path}' does not exist."}
        if os.path.isdir(target):
            return {"success": False, "error": f"'{path}' is a directory, not a file."}

        try:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(limit) if limit else f.read()
            return {"success": True, "path": target, "content": content, "size_bytes": os.path.getsize(target)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 2. Write File (With timestamp prefix on collision if overwrite=False)
    def write_file(self, path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        target = self._resolve_path(path)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        final_path = target
        if os.path.exists(target) and not overwrite:
            # Add date and time prefix to avoid overwriting existing file
            timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S")
            parent = os.path.dirname(target)
            fname = os.path.basename(target)
            final_path = os.path.join(parent, f"{timestamp_str}_{fname}")

        try:
            with open(final_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "path": final_path,
                "renamed_with_prefix": final_path != target,
                "size_bytes": len(content.encode("utf-8"))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 3. Append to File
    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        target = self._resolve_path(path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        try:
            with open(target, "a", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": target, "size_bytes": os.path.getsize(target)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 4. Delete File or Directory
    def delete_file(self, path: str) -> Dict[str, Any]:
        target = self._resolve_path(path)
        if not os.path.exists(target):
            return {"success": False, "error": f"File '{path}' does not exist."}
        try:
            os.remove(target)
            return {"success": True, "message": f"Deleted file '{path}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_dir(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        target = self._resolve_path(path)
        if not os.path.exists(target):
            return {"success": False, "error": f"Directory '{path}' does not exist."}
        try:
            if recursive:
                shutil.rmtree(target)
            else:
                os.rmdir(target)
            return {"success": True, "message": f"Deleted directory '{path}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 5. List Files and Directories
    def list_dir(self, path: str = "", recursive: bool = False) -> Dict[str, Any]:
        target = self._resolve_path(path) if path else self.base_dir
        if not os.path.exists(target):
            return {"success": False, "error": f"Directory '{target}' not found."}

        entries = []
        try:
            if recursive:
                for root, dirs, files in os.walk(target):
                    rel = os.path.relpath(root, target)
                    for d in dirs:
                        entries.append({"name": d, "type": "directory", "path": os.path.join(rel, d)})
                    for f in files:
                        entries.append({"name": f, "type": "file", "path": os.path.join(rel, f)})
            else:
                for item in os.listdir(target):
                    full = os.path.join(target, item)
                    is_dir = os.path.isdir(full)
                    entries.append({
                        "name": item,
                        "type": "directory" if is_dir else "file",
                        "size_bytes": 0 if is_dir else os.path.getsize(full)
                    })
            return {"success": True, "directory": target, "entries": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 6. Create Directory
    def create_dir(self, path: str) -> Dict[str, Any]:
        target = self._resolve_path(path)
        try:
            os.makedirs(target, exist_ok=True)
            return {"success": True, "path": target}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 7. Download File
    def download_file(self, url: str, target_path: Optional[str] = None) -> Dict[str, Any]:
        if not target_path:
            fname = os.path.basename(url.split("?")[0]) or f"download_{int(time.time())}.bin"
            target_path = os.path.join(self.base_dir, fname)
        else:
            target_path = self._resolve_path(target_path)

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AgenticWeb/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp, open(target_path, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
            return {"success": True, "path": target_path, "size_bytes": os.path.getsize(target_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 8. Copy and Move Files / Directories
    def copy_file(self, src: str, dst: str) -> Dict[str, Any]:
        s = self._resolve_path(src)
        d = self._resolve_path(dst)
        if not os.path.exists(s):
            return {"success": False, "error": f"Source '{src}' not found."}
        try:
            os.makedirs(os.path.dirname(d), exist_ok=True)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
            return {"success": True, "src": s, "dst": d}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        s = self._resolve_path(src)
        d = self._resolve_path(dst)
        if not os.path.exists(s):
            return {"success": False, "error": f"Source '{src}' not found."}
        try:
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.move(s, d)
            return {"success": True, "src": s, "dst": d}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 9. Get File Info
    def get_file_info(self, path: str) -> Dict[str, Any]:
        target = self._resolve_path(path)
        if not os.path.exists(target):
            return {"success": False, "error": f"Path '{path}' does not exist."}
        try:
            st = os.stat(target)
            is_dir = os.path.isdir(target)
            line_count = 0
            if not is_dir:
                try:
                    with open(target, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                except Exception:
                    pass

            return {
                "success": True,
                "name": os.path.basename(target),
                "path": target,
                "is_dir": is_dir,
                "size_bytes": st.st_size,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_ctime)),
                "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
                "extension": os.path.splitext(target)[1],
                "line_count": line_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 10. Search Files and Directories
    def search_files(self, query: str, directory: str = "", regex: bool = False) -> Dict[str, Any]:
        target = self._resolve_path(directory) if directory else self.base_dir
        matches = []
        try:
            for root, dirs, files in os.walk(target):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, target)
                    matched = False
                    
                    # Match by filename
                    if regex:
                        if re.search(query, fname, re.IGNORECASE):
                            matched = True
                    else:
                        if query.lower() in fname.lower():
                            matched = True
                            
                    # Match by content
                    if not matched and fname.endswith((".txt", ".py", ".md", ".json", ".csv", ".html")):
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                body = f.read()
                                if regex and re.search(query, body, re.IGNORECASE):
                                    matched = True
                                elif not regex and query.lower() in body.lower():
                                    matched = True
                        except Exception:
                            pass

                    if matched:
                        matches.append({"name": fname, "rel_path": rel_path, "full_path": full_path})
            return {"success": True, "query": query, "total_matches": len(matches), "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 11. Index & Query using LlamaIndex / RAG Engine
    def index_files(self, path: str = "") -> Dict[str, Any]:
        target = self._resolve_path(path) if path else self.base_dir
        indexed = []
        if os.path.isfile(target):
            indexed.append(target)
        elif os.path.isdir(target):
            for root, _, files in os.walk(target):
                for f in files:
                    if f.endswith((".pdf", ".txt", ".md", ".csv", ".json", ".html", ".py")):
                        indexed.append(os.path.join(root, f))
        self.indexed_files = indexed
        return {"success": True, "indexed_count": len(indexed), "files": indexed}

    def query_indexed_files(self, query: str, top_k: int = 4) -> Dict[str, Any]:
        if not self.indexed_files:
            self.index_files()
        results = query_indexed_documents(query, self.indexed_files, top_k=top_k)
        return {"success": True, "query": query, "results": results}

    # 12. Execute Python Code Files
    def execute_python_code(self, code_or_file: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Executes a Python code file or inline Python code safely in subprocess.
        """
        temp_file = None
        if os.path.exists(self._resolve_path(code_or_file)) and os.path.isfile(self._resolve_path(code_or_file)):
            target_script = self._resolve_path(code_or_file)
        else:
            # Inline code: save to temporary execution file
            temp_file = os.path.join(self.base_dir, f"temp_exec_{int(time.time())}.py")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code_or_file)
            target_script = temp_file

        try:
            proc = subprocess.run(
                [sys.executable, target_script],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.base_dir
            )
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Execution timed out after {timeout} seconds."}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass


# Singleton Helper
_file_io_service: Optional[FileIOService] = None

def get_file_io_service() -> FileIOService:
    global _file_io_service
    if _file_io_service is None:
        _file_io_service = FileIOService()
    return _file_io_service
