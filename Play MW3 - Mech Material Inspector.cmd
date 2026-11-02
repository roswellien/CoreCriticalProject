@echo off
setlocal
cd /d "%~dp0"
echo ======================================================================
echo   MECHWARRIOR 3 - HERO MECH MATERIAL ^& HEIGHT MAP INSPECTOR
echo   Interactive 3D WebGL preview and quality audit (Bushwacker / MadCat)
echo ======================================================================
echo.

if "%~1"=="" (
    set MECH_ARG=--mech bushwacker
) else (
    set MECH_ARG=%*
)

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0tools\remaster-launcher\launch_mech_inspector.py" %MECH_ARG%
) else (
    python "%~dp0tools\remaster-launcher\launch_mech_inspector.py" %MECH_ARG%
)

if errorlevel 1 (
    echo.
    echo Inspector exited with error code %errorlevel%.
    pause
)
