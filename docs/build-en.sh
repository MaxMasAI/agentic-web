#!/usr/bin/env bash
# ==============================================================================
# Build English Documentation (Sphinx HTML)
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[*] Building English Sphinx HTML documentation..."
sphinx-build -b html -D language='en' source build/html/en

echo "[OK] English docs built at: docs/build/html/en/index.html"
