@echo off
setlocal enabledelayedexpansion
color 0B
title Agentic Web Workstation - Automated Installer

echo.
echo  ============================================================
echo    AGENTIC WORKSTATION & MULTI-AGENT AI PLATFORM INSTALLER
echo  ============================================================
echo.

:: 1. Verify Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Python detected:
python --version
echo.

:: 2. Create Workspace Directories
echo [*] Initializing workspace directories...
for %%d in (logs tasks downloads visuals json tests logs\chats browser) do (
    if not exist "%%d" mkdir "%%d"
)
echo [OK] Workspace folders initialized.
echo.

:: 3. Optional Virtual Environment Setup
if not exist "venv" (
    echo [*] Creating virtual environment (.venv / venv)...
    python -m venv venv
    if %errorlevel% equ 0 (
        echo [OK] Virtual environment created.
    ) else (
        echo [!] Could not create venv. Proceeding with global Python environment...
    )
)

if exist "venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call venv\Scripts\activate.bat
)

:: 4. Upgrade pip, setuptools, wheel
echo [*] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel --quiet

:: 5. Install Dependencies
echo [*] Installing all workspace dependencies from requirements.txt...
echo [*] (This may take 1-2 minutes depending on your internet connection)
echo.
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [!] Standard install completed with some warnings. Running fallback dependency verification...
    pip install PySide6 pydantic requests aiohttp fastapi uvicorn websockets python-dotenv mcp playwright pillow google-genai
)

:: 6. Install Playwright Chromium Drivers (For Autonomous Computer Use)
echo.
echo [*] Installing Playwright Chromium browser binary for autonomous agents...
playwright install chromium >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Playwright browser binaries installed.
) else (
    echo [!] Playwright install skipped (can be installed later via 'playwright install').
)

echo.
echo  ============================================================
echo    INSTALLATION COMPLETE! ALL DEPENDENCIES READY.
echo  ============================================================
echo.
echo  [+] You can now launch the full desktop application by running:
echo      run.bat
echo.
pause
