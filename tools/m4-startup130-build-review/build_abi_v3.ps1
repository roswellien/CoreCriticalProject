param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$review130Vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $review130Vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $review130Vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'review_v3.py') abi $Output
exit $LASTEXITCODE
