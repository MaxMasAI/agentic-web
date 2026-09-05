"""
tests/test_app_config.py - Unit tests for ConfigManager
"""

import os
import tempfile
import pytest
from services.app_config import ConfigManager, DEFAULT_CONFIG


def test_config_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = os.path.join(tmpdir, "test_config.json")
        mgr = ConfigManager(cfg_path)
        
        # Test Layout defaults
        assert mgr.get("layout.style.chat") == "chatgpt"
        assert mgr.get("layout.chat_zoom") == 1.0
        assert mgr.get("layout.font_size.chat") == 12
        assert mgr.get("layout.dpi_scaling") is True
        assert mgr.get("layout.auto_collapse_user_msg_px") == 1500

        # Test Syntax defaults
        assert mgr.get("syntax.theme") == "github-dark"
        assert mgr.get("syntax.disabled") is False
        assert mgr.get("syntax.stream_highlight_every_n_lines") == 50

        # Test Files & Attachments defaults
        assert mgr.get("attachments.store_in_workdir_upload") is True
        assert mgr.get("attachments.model_summary") == "gpt-4o-mini"
        assert mgr.get("rag.history_limit") == 5

        # Test Context defaults
        assert mgr.get("context.per_load") == 1000
        assert mgr.get("context.use_context") is True
        assert mgr.get("browser.open_urls_in_builtin") is True


def test_config_set_and_persist():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = os.path.join(tmpdir, "test_config.json")
        mgr = ConfigManager(cfg_path)
        
        mgr.set("layout.chat_zoom", 1.25)
        mgr.set("syntax.theme", "monokai")
        mgr.set("context.per_load", 500)

        # Reload in new instance
        mgr2 = ConfigManager(cfg_path)
        assert mgr2.get("layout.chat_zoom") == 1.25
        assert mgr2.get("syntax.theme") == "monokai"
        assert mgr2.get("context.per_load") == 500
