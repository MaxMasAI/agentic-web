#!/usr/bin/env bash
# ==============================================================================
# Convert reStructuredText (.rst) to Markdown (.md) via Pandoc
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/source"

echo "[*] Converting .rst documentation files to .md..."

if command -v pandoc &> /dev/null; then
    for f in *.rst; do
        if [ -f "$f" ]; then
            base="${f%.rst}"
            pandoc "$f" -f rst -t markdown_strict -o "$base.md"
            echo "  -> Converted: $f -> $base.md"
        fi
    done
    echo "[OK] All RST files converted to Markdown."
else
    echo "[!] Pandoc not found in PATH. Please install pandoc (e.g. brew install pandoc / apt install pandoc)."
fi
