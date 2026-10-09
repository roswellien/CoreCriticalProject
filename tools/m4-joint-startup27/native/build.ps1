param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$jointNativeVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $jointNativeVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $jointNativeVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$(Join-Path $jointNativeVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja');$env:PATH"
& C:/Python314/python.exe (Join-Path $PSScriptRoot 'build.py') $Output
exit $LASTEXITCODE
