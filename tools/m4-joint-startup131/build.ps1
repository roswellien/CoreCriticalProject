param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$mfcJoint131Vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $mfcJoint131Vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $mfcJoint131Vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
