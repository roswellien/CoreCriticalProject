@echo off
title MW34 RECOMP - Live x64 Numeric Test
echo Preparing the live numeric initializer x64 test...
"C:\Python314\python.exe" "%~dp0..\tools\in-game-native-numeric\launch.py" --hold %*
if errorlevel 1 (
    echo.
    echo Numeric launch failed. Review the retained logs.
    pause
    exit /b 1
)
