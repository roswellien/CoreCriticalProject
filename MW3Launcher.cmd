@echo off
if exist "%~dp0tools\mw3-remaster-launcher\bin\Release\net8.0-windows\Core Critical Launcher.exe" (
    start "" "%~dp0tools\mw3-remaster-launcher\bin\Release\net8.0-windows\Core Critical Launcher.exe" %*
) else if exist "%~dp0tools\mw3-remaster-launcher\bin\Debug\net8.0-windows\Core Critical Launcher.exe" (
    start "" "%~dp0tools\mw3-remaster-launcher\bin\Debug\net8.0-windows\Core Critical Launcher.exe" %*
) else (
    echo Core Critical Launcher has not been built. Build the launcher project first.
    exit /b 1
)
