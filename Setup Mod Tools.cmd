@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto use_py
where python >nul 2>nul
if errorlevel 1 (
    echo Install Python 3.11-3.14 for Windows x64 with Tkinter, then run setup again.
    echo See docs\setup-mod-tools.md for requirements.
    exit /b 1
)
python "%~dp0tools\release\setup_mod_tools.py" %*
exit /b %errorlevel%

:use_py
py -3 "%~dp0tools\release\setup_mod_tools.py" %*
exit /b %errorlevel%
