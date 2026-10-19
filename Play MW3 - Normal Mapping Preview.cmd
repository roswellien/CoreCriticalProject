@echo off
call "%~dp0Play MW3Remaster.cmd" --profile "%~dp0local\normal-mapping-integration-r1\launcher-normal-mapping.json" --registry "%~dp0local\normal-mapping-integration-r1\normal-registry.json" %*
exit /b %errorlevel%
