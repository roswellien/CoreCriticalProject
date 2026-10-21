@echo off
setlocal
title MechWarrior 3 Map and Mission Editor
cd /d "%~dp0"

set "PYTHON_EXE="
call :try_python "%~dp0.venv-mod-tools\Scripts\python.exe"
if not defined PYTHON_EXE call :try_python "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON_EXE call :try_python "C:\Python314\python.exe"
if not defined PYTHON_EXE call :try_python "python"
if not defined PYTHON_EXE call :try_python "py"

if not defined PYTHON_EXE (
  echo ERROR: No Python runtime with Tkinter and Pillow could be loaded.
  pause
  exit /b 1
)

"%PYTHON_EXE%" "%~dp0games\mw3\mod-tools\run_editor.py" %*
if errorlevel 1 (
  echo.
  echo Editor closed with an error. Review the message above.
  pause
  exit /b 1
)
exit /b 0

:try_python
"%~1" -c "import tkinter, PIL" >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=%~1"
exit /b 0
