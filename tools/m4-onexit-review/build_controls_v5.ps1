param([Parameter(Mandatory=$true)][string]$Build,[Parameter(Mandatory=$true)][string]$ExpectedSha,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$onexitReviewVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $onexitReviewVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $onexitReviewVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$(Join-Path $onexitReviewVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja');$env:PATH"
& C:/Python314/python.exe (Join-Path $PSScriptRoot 'build_controls_v5.py') $Build $ExpectedSha $Output
exit $LASTEXITCODE
