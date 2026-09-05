#!/usr/bin/env bash
# ==============================================================================
# Linux / macOS PyInstaller Build Script
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

echo "[*] Compiling resources..."
python3 bin/resources.py || true

echo "[*] Cleaning old build artifacts..."
rm -rf build dist/AgenticWeb

echo "[*] Running PyInstaller..."
pyinstaller --noconfirm --onedir --windowed \
    --name "AgenticWeb" \
    --add-data "json:json" \
    --add-data "visuals:visuals" \
    --add-data "core:core" \
    --add-data "services:services" \
    --add-data "gui:gui" \
    --hidden-import "PySide6" \
    --hidden-import "pydantic" \
    --hidden-import "mcp" \
    --hidden-import "requests" \
    --hidden-import "aiohttp" \
    --hidden-import "websockets" \
    --hidden-import "fastapi" \
    --hidden-import "uvicorn" \
    --hidden-import "telethon" \
    --hidden-import "wikipedia" \
    app.py

echo "[OK] Standalone build complete: dist/AgenticWeb/AgenticWeb"
