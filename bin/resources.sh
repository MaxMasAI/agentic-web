#!/usr/bin/env bash
# ==============================================================================
# Qt Resource Compilation Shell Wrapper
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

echo "[*] Compiling Qt resource bundle..."
python3 bin/resources.py

echo "[OK] Resource compilation complete."
