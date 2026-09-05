"""
bin/resources.py - Qt Resource Compiler (rcc wrapper) for PySide6
Compiles visuals, icons, and themes into Python bytecode resources.
"""

import os
import subprocess
import sys

def compile_qt_resources(root_dir: str):
    qrc_file = os.path.join(root_dir, "resources.qrc")
    out_file = os.path.join(root_dir, "gui", "resources_rc.py")

    # Generate .qrc if missing
    if not os.path.exists(qrc_file):
        with open(qrc_file, "w", encoding="utf-8") as f:
            f.write('<!DOCTYPE RCC><RCC version="1.0">\n<qresource prefix="/">\n')
            for v_file in os.listdir(os.path.join(root_dir, "visuals")):
                f.write(f'    <file>visuals/{v_file}</file>\n')
            f.write('</qresource>\n</RCC>\n')
        print(f"[RCC] Generated: {qrc_file}")

    # Compile via pyside6-rcc
    try:
        cmd = ["pyside6-rcc", qrc_file, "-o", out_file]
        subprocess.run(cmd, check=True)
        print(f"[RCC] Compiled resources to: {out_file}")
    except Exception as e:
        print(f"[RCC] pyside6-rcc not available or skipped: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    compile_qt_resources(base_dir)
