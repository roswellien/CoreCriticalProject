@echo off
setlocal
set "MAP_DIR=%~dp0"
title MechWarrior 3 - Launching %~n0

echo ======================================================================
echo   MECHWARRIOR 3 - CUSTOM MISSION LAUNCH
echo   Map Title: Iron Ridge Outpost [iron_ridge_outpost]
echo   Operation: C1 - Biome: coastal
echo   Atmosphere: SUNSET - Time: 18.0h
echo ======================================================================
echo.
if exist "%MAP_DIR%briefing.txt" type "%MAP_DIR%briefing.txt"
echo.

set "PY_EXE=python"
if exist "%MAP_DIR%..\..\python\python.exe" set "PY_EXE=%MAP_DIR%..\..\python\python.exe"
if exist "%MAP_DIR%..\..\..\python\python.exe" set "PY_EXE=%MAP_DIR%..\..\..\python\python.exe"
if exist "C:\Python314\python.exe" set "PY_EXE=C:\Python314\python.exe"

set "RUNNER_SCRIPT="
if exist "%MAP_DIR%..\..\games\mw3\mod-tools\editor\core\play_map.py" set "RUNNER_SCRIPT=%MAP_DIR%..\..\games\mw3\mod-tools\editor\core\play_map.py"
if exist "%MAP_DIR%..\..\..\games\mw3\mod-tools\editor\core\play_map.py" set "RUNNER_SCRIPT=%MAP_DIR%..\..\..\games\mw3\mod-tools\editor\core\play_map.py"
if exist "%MAP_DIR%..\..\editor\core\play_map.py" set "RUNNER_SCRIPT=%MAP_DIR%..\..\editor\core\play_map.py"

if defined RUNNER_SCRIPT (
    "%PY_EXE%" "%RUNNER_SCRIPT%" "%MAP_DIR%" %*
) else (
    echo Error: Could not locate play_map.py runner script.
    pause
    exit /b 1
)
if errorlevel 1 (
    echo.
    echo Map launch exited with code %errorlevel%.
    pause
)
