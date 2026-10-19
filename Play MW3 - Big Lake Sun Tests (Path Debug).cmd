@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\remaster-launcher\play_big_lake_sun.ps1" -PathDebug %*
if errorlevel 1 pause
