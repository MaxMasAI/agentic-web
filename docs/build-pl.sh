#!/usr/bin/env bash
# ==============================================================================
# Build Polish Documentation (Sphinx HTML)
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[*] Building Polish Sphinx HTML documentation..."
sphinx-build -b html -D language='pl' source build/html/pl

echo "[OK] Polish docs built at: docs/build/html/pl/index.html"
