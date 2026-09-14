"""
gui/workers/async_worker.py - Non-Blocking Background Thread Workers for PySide6.

Enforces a strict multi-threaded architecture to execute multi-agent workflows,
continuous LLM token streaming, browser automation, and audio synthesis without
freezing or degrading the PySide6 desktop UI rendering thread.
"""

import sys
import asyncio
import traceback
from typing import Callable, Any, Dict, Optional, List
from dataclasses import dataclass, field

from PySide6.QtCore import QThread, Signal, QObject, QThreadPool, QRunnable


@dataclass
class TaskProgressPayload:
    task_id: str
    agent_id: str
    status: str
    percentage: int = 0
    message: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


class AgenticTaskWorker(QThread):
    """
    Dedicated QThread worker for running long-running multi-agent pipelines
    completely decoupled from the main UI thread.
    """
    task_started = Signal(str)                                  # task_id
    agent_status_changed = Signal(str, str, str)               # agent_id, state, message
    token_streamed = Signal(str, str)                          # agent_id, token_chunk
    progress_updated = Signal(object)                          # TaskProgressPayload
    task_completed = Signal(dict)                              # result dictionary
    task_failed = Signal(str)                                  # error message

    def __init__(self, target_coro_or_func: Callable, *args, **kwargs):
        super().__init__()
        self.target = target_coro_or_func
        self.args = args
        self.kwargs = kwargs
        self.is_cancelled = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def cancel(self):
        """Requests graceful cancellation of the worker."""
        self.is_cancelled = True
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(self._loop):
                task.cancel()

    def run(self):
        """Executes the target in an isolated thread and local event loop."""
        try:
            if asyncio.iscoroutinefunction(self.target) or asyncio.iscoroutine(self.target):
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                if asyncio.iscoroutine(self.target):
                    result = self._loop.run_until_complete(self.target)
                else:
                    result = self._loop.run_until_complete(self.target(*self.args, **self.kwargs))
                self._loop.close()
            else:
                result = self.target(*self.args, **self.kwargs)

            if not self.is_cancelled:
                self.task_completed.emit(result if isinstance(result, dict) else {"result": result})
        except asyncio.CancelledError:
            self.task_failed.emit("Task execution was cancelled by user.")
        except Exception as e:
            err_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.task_failed.emit(err_msg)


class StreamExecutionWorker(QThread):
    """
    Specialized QThread worker for asynchronous multi-provider LLM token streaming.
    """
    token_received = Signal(str)      # token
    stream_finished = Signal(str)     # full_text
    stream_error = Signal(str)        # error_message

    def __init__(self, stream_generator_func: Callable, *args, **kwargs):
        super().__init__()
        self.stream_func = stream_generator_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        full_text = []
        try:
            gen = self.stream_func(*self.args, **self.kwargs)
            for token in gen:
                if token:
                    full_text.append(token)
                    self.token_received.emit(token)
            self.stream_finished.emit("".join(full_text))
        except Exception as e:
            self.stream_error.emit(f"Stream error: {str(e)}")


class GenericAsyncWorker(QThread):
    """
    Lightweight background worker for one-shot asynchronous tasks
    (e.g., FancyZones snapping, system app launch, database checkpointing).
    """
    finished_with_result = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            if asyncio.iscoroutinefunction(self.fn):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                res = loop.run_until_complete(self.fn(*self.args, **self.kwargs))
                loop.close()
            else:
                res = self.fn(*self.args, **self.kwargs)
            self.finished_with_result.emit(res)
        except Exception as e:
            self.failed.emit(str(e))
