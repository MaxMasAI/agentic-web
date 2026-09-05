@echo off
setlocal enabledelayedexpansion
color 0B
title Agentic Web - Build All (Executable + Installer)

echo.
echo  ============================================================
echo    BUILD ALL: BINARIES, ASSETS, AND INSTALLER PACKAGES
echo  ============================================================
echo.

cd /d "%~dp0"

echo [1/4] Minifying codebase assets...
call python minify.py

echo.
echo [2/4] Compiling Qt resources...
call python resources.py

echo.
echo [3/4] Building standalone executable...
call build.bat

echo.
echo [4/4] Generating installer package...
call build_installer.bat

echo.
echo  ============================================================
echo    ALL BUILDS COMPLETED SUCCESSFULLY!
echo  ============================================================
echo.
pause
