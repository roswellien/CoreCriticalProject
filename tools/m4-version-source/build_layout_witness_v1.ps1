param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$versionLayoutVs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $versionLayoutVs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $versionLayoutVs -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build_layout_witness_v1.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
