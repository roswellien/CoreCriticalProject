@echo off
setlocal
cd /d "%~dp0"
echo ======================================================================
echo   MECHWARRIOR 3 - TERRAIN MATERIAL ^& HEIGHT MAP INSPECTOR
echo   Interactive 3D WebGL preview and quality audit
echo ======================================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0tools\remaster-launcher\launch_terrain_inspector.py" %*
) else (
    python "%~dp0tools\remaster-launcher\launch_terrain_inspector.py" %*
)

if errorlevel 1 (
    echo.
    echo Inspector exited with error code %errorlevel%.
    pause
)
