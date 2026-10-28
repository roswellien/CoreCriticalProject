@echo off
rem Launches MechWarrior 3 through the native recompiled host (tools\m4-crt-heap-carry\play.ps1).
rem Double-click to play with your keyboard and mouse. Optional arguments are passed through, e.g.
rem   Play-MW3.cmd -Dump 100      save every 100th frame as a PPM next to the log
rem   Play-MW3.cmd -Frames 3000   stop after 3000 presented frames
rem   Play-MW3.cmd -Build O2      use the unmodified build instead of the default merged-x87 build
rem   Play-MW3.cmd -Overlay       show an FPS / frame-time overlay (host-drawn, off by default)
rem The default build (build\m4-crt-heap-carry-O2-merge) is made with
rem   python tools\m4-crt-heap-carry\inline_objects.py reports\m4-crt-attach\merge-r7 --merge-x87 --no-inline --cleanup --strict-x87 --x87-noexc --flat-mem
rem   then reports\m4-crt-attach\merge-r7-entry\mfc_objects_inline.txt = the merge-r7 list plus the lifts-r63 CRT-entry
rem   objects (mfc_closure.py game 5ac3a0 7800bbbc, lift_closure.py, gen_mfc_dispatch.py), linked with
rem   powershell -Command "& tools\m4-crt-heap-carry\build.ps1 -Levels O2 -Inline reports\m4-crt-attach\merge-r7-entry -Suffix '-merge'"
cd /d "%~dp0.."
set BUILD=O2-merge
echo %* | findstr /i /c:"-Build" >nul && set BUILD=
if defined BUILD if not exist "build\m4-crt-heap-carry-%BUILD%\entry_commandline.exe" (
  echo The native host build build\m4-crt-heap-carry-%BUILD% is missing. See the comments at the top of Play-MW3.cmd.
  pause
  exit /b 1
)
echo Starting MechWarrior 3 (native host). Startup takes about 30-60 seconds; Alt+Tab releases the mouse.
if defined BUILD (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\tools\m4-crt-heap-carry\play.ps1" -Build %BUILD% %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\tools\m4-crt-heap-carry\play.ps1" %*
)
echo.
echo The run log is the newest reports\m4-crt-attach\play-*.err (its first line says why the run ended).
pause
