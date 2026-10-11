param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$widgetBuildVs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $widgetBuildVs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $widgetBuildVs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$env:PATH"
$env:PYTHONUTF8='1'
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build_v3.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
