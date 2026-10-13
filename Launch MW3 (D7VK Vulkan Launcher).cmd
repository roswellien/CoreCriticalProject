@echo off
title MechWarrior 3 - D7VK Vulkan Launcher
cd /d "%~dp0"

set "PYTHON_EXE="
where python >nul 2>nul && set "PYTHON_EXE=python"
if not defined PYTHON_EXE if exist "C:\Python314\python.exe" set "PYTHON_EXE=C:\Python314\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=py"

"%PYTHON_EXE%" "%~dp0mw3_launcher.py" %*
if errorlevel 1 (
    echo.
    echo Launcher exited with an error. Review the message above.
    pause
    exit /b 1
)
