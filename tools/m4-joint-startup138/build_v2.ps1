param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$widgetJoint138V2Vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $widgetJoint138V2Vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $widgetJoint138V2Vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build_v2.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
