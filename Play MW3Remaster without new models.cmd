@echo off
rem Reuse the living Remaster profile, with every model replacement disabled.
call "%~dp0Play MW3Remaster.cmd" --original-models %*
exit /b %errorlevel%
