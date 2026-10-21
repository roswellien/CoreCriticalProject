@echo off
setlocal
cd /d "%~dp0"
echo ======================================================================
echo   MECHWARRIOR 3 - VISUAL 3D MAP STUDIO
echo   Modern visual editor for authoring standalone community map packs
echo ======================================================================
echo.
echo Starting Web Studio server...
python "games\mw3\mod-tools\run_studio.py"
if errorlevel 1 (
    echo.
    echo Studio server exited with code %errorlevel%.
    pause
)
