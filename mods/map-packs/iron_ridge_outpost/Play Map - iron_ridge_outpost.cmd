@echo off
setlocal
set "MAP_DIR=%~dp0"
cd /d "%MAP_DIR%..\..\.."
echo ======================================================================
echo   MECHWARRIOR 3 - CUSTOM MISSION LAUNCH
echo   Map Title: Iron Ridge Outpost [iron_ridge_outpost]
echo   Operation: C1 | Biome: coastal
echo ======================================================================
echo.
type "%MAP_DIR%briefing.txt"
echo.
echo Initializing native Vulkan engine redirect banks...
set "MW34_REMASTER_BANKS=%MAP_DIR%map-banks.bin"
set "MW34_SUN_AZIMUTH=225.0"
set "MW34_SUN_ELEVATION=35.0"
set "MW34_SUN_STRENGTH=0.85"
set "MW34_SUN_AMBIENT=0.2"

call "Play MW3Remaster.cmd" --profile "local\effect-lighting-r1\launcher.json" --registry "local\material-authoring-r1\normal-registry.json" %*
if errorlevel 1 (
    echo.
    echo Map launch exited with code %errorlevel%.
    pause
)
