@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\tools\remaster-launcher\play_big_lake_sun.ps1" -TextureMarkers %*
if errorlevel 1 pause
