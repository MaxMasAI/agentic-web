"""
bin/minify.py - JSON and Static Asset Minifier for Agentic Web Workstation
Minifies JSON configuration files, CSS themes, and JS assets for faster load time.
"""

import os
import json
import glob

def minify_json_files(root_dir: str):
    json_pattern = os.path.join(root_dir, "json", "*.json")
    for file_path in glob.glob(json_pattern):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(',', ':'))
            print(f"[Minify] Processed: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[Minify] Skipped {file_path}: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"[*] Minifying configuration assets in: {base_dir}")
    minify_json_files(base_dir)
    print("[OK] Asset minification complete.")
