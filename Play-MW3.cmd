@echo off
rem Launches MechWarrior 3 through the native recompiled host (tools\m4-crt-heap-carry\play.ps1).
rem Double-click to play with your keyboard and mouse. Optional arguments are passed through, e.g.
rem   Play-MW3.cmd -Dump 100      save every 100th frame as a PPM next to the log
rem   Play-MW3.cmd -Frames 3000   stop after 3000 presented frames
rem The host must be built first: tools\m4-crt-heap-carry\build.ps1 -Levels O2
cd /d "%~dp0"
if not exist "build\m4-crt-heap-carry-O2\entry_commandline.exe" (
  echo The native host is not built yet. Run: powershell -File tools\m4-crt-heap-carry\build.ps1 -Levels O2
  pause
  exit /b 1
)
echo Starting MechWarrior 3 (native host). Startup takes about 30-60 seconds; Alt+Tab releases the mouse.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\m4-crt-heap-carry\play.ps1" %*
echo.
echo The run log is the newest reports\m4-crt-attach\play-*.err (its first line says why the run ended).
pause
