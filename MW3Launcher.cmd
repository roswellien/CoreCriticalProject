@echo off
if exist "%~dp0tools\mw3-remaster-launcher\bin\Release\net8.0-windows\MW3RemasterLauncher.exe" (
    start "" "%~dp0tools\mw3-remaster-launcher\bin\Release\net8.0-windows\MW3RemasterLauncher.exe" %*
) else (
    start "" "%~dp0tools\mw3-remaster-launcher\bin\Debug\net8.0-windows\MW3RemasterLauncher.exe" %*
)
