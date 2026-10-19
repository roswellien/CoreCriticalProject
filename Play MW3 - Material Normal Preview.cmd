@echo off
call "%~dp0Play MW3Remaster.cmd" --profile "%~dp0local\material-authoring-r1\launcher-material-normals.json" --registry "%~dp0local\material-authoring-r1\normal-registry.json" %*
exit /b %errorlevel%
