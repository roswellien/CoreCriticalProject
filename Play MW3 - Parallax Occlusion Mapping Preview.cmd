@echo off
setlocal
title Play MW3 - Parallax Occlusion Mapping Preview

rem Enable opt-in Vulkan POM shader stage and required lighting prerequisites
set "MW34_POM=1"
set "MW34_SUN=1"
set "MW34_SUN_NORMALS=1"
set "MW34_POM_MAX_DISTANCE=80"

rem Optional debug mode: uncomment below to visualize POM raymarch step counts
rem set "MW34_POM_DEBUG=1"

rem Default to midday lighting preset unless explicitly provided by caller
set "PRESET_ARGS="
echo %* | findstr /i /c:"--lighting-preset" >nul
if errorlevel 1 (
    set "PRESET_ARGS=--lighting-preset midday"
)

call "%~dp0Play MW3Remaster.cmd" %PRESET_ARGS% %*
if errorlevel 1 (
    echo.
    echo Parallax Occlusion Mapping preview exited with code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)
exit /b 0
