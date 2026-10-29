@echo off
setlocal
cd /d "%~dp0.."
echo ======================================================================
echo   MECHWARRIOR 3 - VISUAL 3D MAP STUDIO
echo   Modern visual editor for authoring standalone community map packs
echo ======================================================================
echo.
echo Starting Web Studio server...
if exist "%~dp0..\.venv-mod-tools\Scripts\python.exe" goto use_tools_python
python "%~dp0..\games\mw3\mod-tools\run_studio.py" %*
goto finished

:use_tools_python
"%~dp0..\.venv-mod-tools\Scripts\python.exe" "%~dp0..\games\mw3\mod-tools\run_studio.py" %*

:finished
if errorlevel 1 (
    echo.
    echo Studio server exited with code %errorlevel%.
    pause
)
