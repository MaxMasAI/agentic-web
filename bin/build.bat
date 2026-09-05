@echo off
setlocal enabledelayedexpansion
color 0B
title Agentic Web - Build Executable (Windows)

echo.
echo  ============================================================
echo    BUILDING STANDALONE WINDOWS BINARY (PyInstaller)
echo  ============================================================
echo.

cd /d "%~dp0\.."

:: 1. Compile Resources
if exist "bin\resources.py" (
    echo [*] Compiling Qt resources...
    python bin\resources.py
)

:: 2. Clean Previous Builds
if exist "build" rmdir /s /q build
if exist "dist\AgenticWeb" rmdir /s /q "dist\AgenticWeb"

:: 3. Run PyInstaller
echo [*] Executing PyInstaller build...
pyinstaller --noconfirm --onedir --windowed ^
    --name "AgenticWeb" ^
    --add-data "json;json" ^
    --add-data "visuals;visuals" ^
    --add-data "core;core" ^
    --add-data "services;services" ^
    --add-data "gui;gui" ^
    --hidden-import "PySide6" ^
    --hidden-import "pydantic" ^
    --hidden-import "mcp" ^
    --hidden-import "requests" ^
    --hidden-import "aiohttp" ^
    --hidden-import "websockets" ^
    --hidden-import "fastapi" ^
    --hidden-import "uvicorn" ^
    --hidden-import "telethon" ^
    --hidden-import "wikipedia" ^
    app.py

if %errorlevel% equ 0 (
    echo.
    echo [OK] Standalone build succeeded: dist\AgenticWeb\AgenticWeb.exe
) else (
    echo.
    echo [ERROR] Build failed! Check PyInstaller logs above.
    exit /b 1
)
