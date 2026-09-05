@echo off
color 0B
title Multi-Agent AI Orchestrator ^& Live Voice Control (PySide6 Desktop)

:: Ensure logs and tasks directory exist
if not exist "logs" mkdir logs
if not exist "tasks" mkdir tasks
if not exist "downloads" mkdir downloads
if not exist "visuals" mkdir visuals
if not exist "json" mkdir json

echo.
echo  ============================================================
echo    LEADER-WORKER MULTI-AI COLLABORATIVE SYSTEM ^& LIVE VOICE
echo    Desktop App:  PySide6 Native Desktop Application
echo    Voice Socket: ws://localhost:8000/ws
echo  ============================================================
echo.
echo  [*] Starting Gemini Live Voice Backend in background...
start /b python -m uvicorn voice.backend.server:app --host 127.0.0.1 --port 8000 > nul 2>&1

echo  [*] Launching Multi-Agent Desktop Control Center (PySide6)...
echo.

:: Launch PySide6 Desktop Application
python app.py

:: Auto-cleanup on close/exit
echo.
echo [*] Terminating active agent browser process trees ^& background servers...
python -c "from utils import pid_tracker; pid_tracker.kill_all_tracked_pids()"
echo [OK] All agent and voice processes closed.

pause
