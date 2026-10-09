param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$taskVS/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="$taskRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$taskVS/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
& 'C:/Python314/python.exe' "$PSScriptRoot/build_peer.py" $OutputDirectory
exit $LASTEXITCODE
