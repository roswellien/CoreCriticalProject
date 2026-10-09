param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$startup28VS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $startup28VS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $startup28VS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$(Join-Path $startup28VS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja');$env:PATH"
& C:/Python314/python.exe -B (Join-Path $PSScriptRoot 'build.py') $Preparation $ExpectedSha $Output
exit $LASTEXITCODE
