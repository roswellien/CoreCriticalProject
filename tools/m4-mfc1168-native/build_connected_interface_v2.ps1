param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$mfcConnectedVs2='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $mfcConnectedVs2 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $mfcConnectedVs2 -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build_connected_interface_v2.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
