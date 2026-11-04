@echo off
title MechWarrior 3 - Visual 3D Mod Studio
cd /d "%~dp0"

echo ====================================================================
echo   MECHWARRIOR 3 - VISUAL 3D MOD STUDIO
echo ====================================================================

:: 1. Check for bundled embedded Python runtime
if exist "dist\MW3-Mod-Studio-v1.0.0-Standalone\python\python.exe" (
    echo [Mod Studio] Starting with bundled portable Python runtime...
    start "" "dist\MW3-Mod-Studio-v1.0.0-Standalone\python\python.exe" games\mw3\mod-tools\run_studio.py
    exit /b 0
)

:: 2. Check for system Python launcher (py -3)
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [Mod Studio] Starting with system Python launcher (py -3)...
    start "" py -3 games\mw3\mod-tools\run_studio.py
    exit /b 0
)

:: 3. Check for python on PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [Mod Studio] Starting with system Python...
    start "" python games\mw3\mod-tools\run_studio.py
    exit /b 0
)

echo.
echo ====================================================================
echo ERROR: Python 3 was not detected on this computer.
echo.
echo To run MechWarrior 3 Mod Studio:
echo   1. Install Python 3.9+ from https://www.python.org/downloads/
echo   2. Ensure "Add Python to PATH" is checked during installation.
echo   3. Run this script again.
echo ====================================================================
echo.
pause
exit /b 1
