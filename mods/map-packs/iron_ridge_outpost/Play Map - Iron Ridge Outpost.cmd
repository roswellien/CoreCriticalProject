@echo off
setlocal
set "MAP_DIR=%~dp0"
cd /d "%MAP_DIR%..\..\.."
echo ======================================================================
echo   Launching Custom Map Pack: Iron Ridge Outpost
echo ======================================================================
echo.
set "MW34_REMASTER_BANKS=%MAP_DIR%map-banks.bin"
set "MW34_SUN_AZIMUTH=235.0"
set "MW34_SUN_ELEVATION=28.0"
set "MW34_SUN_STRENGTH=0.9"
set "MW34_SUN_AMBIENT=0.22"

call "launchers\Play MW3Remaster.cmd" --profile "local\effect-lighting-r1\launcher.json" --registry "local\material-authoring-r1\normal-registry.json" %*
if errorlevel 1 (
    echo.
    echo Map launch exited with code %errorlevel%.
    pause
)
