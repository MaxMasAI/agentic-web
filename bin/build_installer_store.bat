@echo off
setlocal enabledelayedexpansion
color 0B
title Agentic Web - Build Microsoft Store MSIX Package

echo.
echo  ============================================================
echo    BUILDING WINDOWS STORE MSIX PACKAGE (DesktopAppConverter)
echo  ============================================================
echo.

cd /d "%~dp0\.."

:: 1. Ensure Binary Exists
if not exist "dist\AgenticWeb\AgenticWeb.exe" (
    echo [*] Executable not found. Compiling binary...
    call bin\build.bat
)

:: 2. Check for MakeAppx (Windows SDK)
where makeappx >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Windows SDK MakeAppx tool detected.
    echo [*] Packaging MSIX container...
    makeappx pack /d dist\AgenticWeb /p dist\AgenticWeb_v2.4.4.msix /nv
    echo [OK] Windows Store MSIX Package created: dist\AgenticWeb_v2.4.4.msix
) else (
    echo [!] MakeAppx tool not found in PATH.
    echo     Please install the Windows 10/11 SDK to produce store-signed .msix packages.
)

echo.
