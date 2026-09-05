#!/usr/bin/env bash
# ==============================================================================
# Asset Minification Pipeline Wrapper
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

echo "[*] Running Python asset minifier..."
python3 bin/minify.py

echo "[OK] Minification completed."
