#!/usr/bin/env bash
# ==============================================================================
# Localization Key Sorter - Alphabetizes translation keys in JSON dictionaries
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

python3 - << 'EOF'
import os
import json
import glob

locale_files = glob.glob("json/locales/*.json")
for path in locale_files:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
        print(f"[Sort] Alphabetized keys in: {path}")
    except Exception as e:
        print(f"[Sort] Skipped {path}: {e}")
EOF

echo "[OK] Localization sort complete."
