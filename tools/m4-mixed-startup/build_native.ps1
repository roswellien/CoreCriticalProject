param([Parameter(Mandatory=$true)][string]$Derived,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$mwVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$mwVS/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $mwVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="$mwRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$mwVS/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
& 'C:/Python314/python.exe' "$PSScriptRoot/build_native.py" --derived $Derived --output $OutputDirectory
exit $LASTEXITCODE
