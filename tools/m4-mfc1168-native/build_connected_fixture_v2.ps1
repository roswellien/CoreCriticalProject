param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$mfcFixtureVs2='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $mfcFixtureVs2 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $mfcFixtureVs2 -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build_connected_fixture_v2.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
