#!/usr/bin/env bash
# ==============================================================================
# Update & Sync Documentation
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[*] Updating documentation build..."
pip install -r requirements.txt --quiet || true

echo "[*] Rebuilding documentation..."
bash build-en.sh

echo "[OK] Documentation update complete."
