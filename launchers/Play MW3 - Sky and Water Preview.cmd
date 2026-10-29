@echo off
call "%~dp0Play MW3Remaster.cmd" --profile "%~dp0..\local\sky-water-detail-r1\launcher-sky-water.json" --registry "%~dp0..\local\normal-mapping-integration-r1\normal-registry.json" %*
exit /b %errorlevel%
