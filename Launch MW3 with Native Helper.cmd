@echo off
title MW34 RECOMP - Live x64 Address Helper Test
echo Preparing the live address-helper x64 test...
"C:\Python314\python.exe" "%~dp0tools\in-game-native-helper\launch.py" --hold %*
if errorlevel 1 (
    echo.
    echo Helper launch failed. Review the retained logs.
    pause
    exit /b 1
)
