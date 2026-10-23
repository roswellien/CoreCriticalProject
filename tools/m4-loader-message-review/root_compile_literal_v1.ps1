param([Parameter(Mandatory=$true)][string]$Admission,[Parameter(Mandatory=$true)][string]$AdmissionSha,[Parameter(Mandatory=$true)][string]$BuildName)
$ErrorActionPreference='Stop'
$messageVsRoot='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$messageVsRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $messageVsRoot -DevCmdArguments '-arch=amd64 -host_arch=amd64' -SkipAutomaticLocation | Out-Null
& 'C:/Python314/python.exe' -B "$PSScriptRoot/root_compile_literal_v1.py" $Admission $AdmissionSha $BuildName
exit $LASTEXITCODE
