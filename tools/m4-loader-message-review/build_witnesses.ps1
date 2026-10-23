$ErrorActionPreference='Stop'
$vsRoot='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vsRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vsRoot -DevCmdArguments '-arch=amd64 -host_arch=amd64' -SkipAutomaticLocation | Out-Null
& 'C:/Python314/python.exe' -B "$PSScriptRoot/build_witnesses.py"
exit $LASTEXITCODE
