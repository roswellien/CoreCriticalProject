param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$contextControls138Vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $contextControls138Vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $contextControls138Vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PYTHONUTF8='1'
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build_controls.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
