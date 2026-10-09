param([Parameter(Mandatory=$true)][string]$Derived,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$jointVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $jointVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $jointVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$(Join-Path $jointVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja');$env:PATH"
& C:/Python314/python.exe (Join-Path $PSScriptRoot 'build.py') --derived $Derived --output $Output
exit $LASTEXITCODE
