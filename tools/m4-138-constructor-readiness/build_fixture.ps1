param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$constructorRestoreVs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $constructorRestoreVs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $constructorRestoreVs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PYTHONUTF8='1'
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot '../m4-constructor-native/build_fixture_v5.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
