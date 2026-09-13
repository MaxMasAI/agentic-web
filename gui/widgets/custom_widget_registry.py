"""
gui/widgets/custom_widget_registry.py - Custom Widget Creation, Persistence & Discovery Engine
Allows developers and users to build, persist, and reuse custom workflow widgets
without repeating code for same or similar widgets.
"""

import os
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import QWidget

WIDGETS_STORAGE_DIR = Path(__file__).parent / "custom_widgets"
REGISTRY_JSON_FILE = Path(__file__).parent.parent.parent / "json" / "custom_widgets_registry.json"


class CustomWidgetRegistry:
    """
    Manages custom reusable widgets saved in gui/widgets/custom_widgets/.
    """
    def __init__(self):
        self.storage_dir = WIDGETS_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = REGISTRY_JSON_FILE
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.saved_widgets: Dict[str, Dict[str, Any]] = {}
        self.load_registry()

    def load_registry(self):
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.saved_widgets = json.load(f)
            except Exception:
                self.saved_widgets = {}

    def save_registry(self):
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.saved_widgets, f, indent=2)
        except Exception:
            pass

    def register_custom_widget(self, widget_id: str, name: str, category: str, description: str, python_code: str) -> bool:
        """Saves a custom workflow widget into the custom_widgets folder and updates the registry."""
        safe_id = widget_id.lower().replace(" ", "_")
        target_file = self.storage_dir / f"{safe_id}.py"

        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(python_code)

            self.saved_widgets[safe_id] = {
                "id": safe_id,
                "name": name,
                "category": category,
                "description": description,
                "file_path": str(target_file),
                "created_at": os.path.getmtime(target_file)
            }
            self.save_registry()
            return True
        except Exception:
            return False

    def list_saved_widgets(self) -> List[Dict[str, Any]]:
        return list(self.saved_widgets.values())

    def instantiate_widget(self, widget_id: str, parent=None) -> Optional[QWidget]:
        """Dynamically imports and instantiates a saved custom widget."""
        meta = self.saved_widgets.get(widget_id)
        if not meta:
            return None

        file_path = Path(meta["file_path"])
        if not file_path.exists():
            return None

        try:
            mod_name = f"custom_widget_{widget_id}"
            spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if isinstance(obj, type) and issubclass(obj, QWidget) and obj != QWidget:
                        return obj(parent)
        except Exception:
            pass
        return None


# Global Singleton
_custom_widget_registry: Optional[CustomWidgetRegistry] = None

def get_custom_widget_registry() -> CustomWidgetRegistry:
    global _custom_widget_registry
    if _custom_widget_registry is None:
        _custom_widget_registry = CustomWidgetRegistry()
    return _custom_widget_registry
