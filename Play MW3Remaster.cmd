@echo off
setlocal
title Play MW3Remaster
cd /d "%~dp0"
set "PYTHON_EXE="
rem Prefer the existing bundled runtime; validate dependencies in this environment.
call :try_python "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PYTHON_EXE call :try_python "C:\Python314\python.exe"
if not defined PYTHON_EXE call :try_python "python"
if not defined PYTHON_EXE call :try_python "py"
if not defined PYTHON_EXE (
  echo ERROR: No Python 3.11+ runtime with Pillow could be loaded.
  echo Restore the bundled Codex runtime or install Pillow for your Python.
  pause
  exit /b 1
)
"%PYTHON_EXE%" "%~dp0tools\remaster-launcher\play_remaster.py" %*
if errorlevel 1 (
  echo.
  echo Remaster launch did not complete. Review the message above.
  pause
  exit /b 1
)
exit /b 0

:try_python
"%~1" -c "import sys; assert sys.version_info >= (3,11); from PIL import Image; Image.new('RGB',(1,1)).tobytes()" >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=%~1"
exit /b 0
