"""
tests/test_sidebar.py - Unit test for Sidebar Auto-Hide and Pinning
"""

import sys
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_sidebar_auto_hide_and_pin(qapp):
    from gui.widgets.sidebar import Sidebar
    sidebar = Sidebar()
    assert sidebar is not None
    assert sidebar.auto_hide is True
    assert sidebar.width() == Sidebar.COLLAPSED_WIDTH

    # Test Pin Toggle
    sidebar.toggle_pin()
    assert sidebar.auto_hide is False
    assert sidebar.width() == Sidebar.EXPANDED_WIDTH

    # Toggle back to Auto-Hide
    sidebar.toggle_pin()
    assert sidebar.auto_hide is True
    assert sidebar.width() == Sidebar.COLLAPSED_WIDTH
