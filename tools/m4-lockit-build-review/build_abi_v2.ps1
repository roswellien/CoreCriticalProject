param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$reviewVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $reviewVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $reviewVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'review_v2.py') abi $Output
exit $LASTEXITCODE
