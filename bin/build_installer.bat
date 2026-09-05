@echo off
setlocal enabledelayedexpansion
color 0B
title Agentic Web - Build Windows MSI Installer (WiX / Inno)

echo.
echo  ============================================================
echo    BUILDING WINDOWS INSTALLER PACKAGE (.MSI / .EXE)
echo  ============================================================
echo.

cd /d "%~dp0\.."

:: 1. Ensure Binary is Built
if not exist "dist\AgenticWeb\AgenticWeb.exe" (
    echo [*] Executable not found. Building binary first...
    call bin\build.bat
)

:: 2. Check for WiX Toolset
where candle >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] WiX Toolset detected. Compiling MSI package...
    candle -out build\Product.wixobj bin\Product.wxs
    light -out dist\AgenticWeb_Setup_v2.4.4.msi build\Product.wixobj
    echo [OK] MSI Installer created: dist\AgenticWeb_Setup_v2.4.4.msi
    goto :done
)

:: 3. Check for Inno Setup (ISCC)
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Inno Setup detected. Building setup executable...
    iscc bin\installer.iss
    goto :done
)

echo [!] Neither WiX Toolset (candle.exe) nor Inno Setup (iscc.exe) found in PATH.
echo [!] Standalone portable directory is ready at: dist\AgenticWeb\
echo     You can zip or distribute dist\AgenticWeb directly.

:done
echo.
echo  ============================================================
echo    INSTALLER BUILD PROCESS FINISHED.
echo  ============================================================
echo.
