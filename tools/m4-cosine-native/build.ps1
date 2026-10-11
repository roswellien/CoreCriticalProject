param([Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
$mwCompoundVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $mwCompoundVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $mwCompoundVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build.py') $Name
exit $LASTEXITCODE
