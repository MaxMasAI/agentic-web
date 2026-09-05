#!/usr/bin/env bash
# ==============================================================================
# Rebuild Multilingual Sphinx Documentation
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[*] Extracting gettext message catalogs..."
sphinx-build -b gettext source build/gettext || true

echo "[*] Updating locale po files..."
sphinx-intl update -p build/gettext -l pl || true

echo "[*] Building all localized HTML documentation targets..."
bash build-en.sh
bash build-pl.sh

echo "[OK] Multilingual documentation rebuild finished."
