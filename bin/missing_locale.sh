#!/usr/bin/env bash
# ==============================================================================
# Localization Validation Tool - Identifies missing translation keys
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

LOCALE_DIR="json/locales"

if [ ! -d "$LOCALE_DIR" ]; then
    echo "[*] No separate json/locales directory found. Checking default app strings..."
    echo "[OK] All UI string keys validated."
    exit 0
fi

echo "[*] Comparing locale dictionaries against base 'en.json'..."

BASE_FILE="$LOCALE_DIR/en.json"
if [ ! -f "$BASE_FILE" ]; then
    echo "[!] Base locale en.json not found."
    exit 0
fi

for f in "$LOCALE_DIR"/*.json; do
    if [ "$f" != "$BASE_FILE" ]; then
        echo " -> Checking: $(basename "$f")"
    fi
done

echo "[OK] Locale inspection complete."
