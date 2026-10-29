@echo off
title MW34 RECOMP - Hook and Monitoring
echo Preparing the verified helper replacement and live logging...
"C:\Python314\python.exe" "%~dp0..\tools\game-monitor\launch_hook.py" %*
if errorlevel 1 (
    echo.
    echo Launch failed. Review the message above.
    pause
    exit /b 1
)
