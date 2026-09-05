"""
tests/test_settings_page.py - Unit test for multi-category SettingsPage
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


def test_settings_page_initialization(qapp):
    from gui.pages.settings_page import SettingsPage
    page = SettingsPage()
    assert page is not None
    assert page.nav_list.count() == 18
    assert page.stacked_widget.count() == 18

    # Switch across categories
    for i in range(18):
        page.nav_list.setCurrentRow(i)
        assert page.stacked_widget.currentIndex() == i
