param([Parameter(Mandatory=$true)][string]$Output,[switch]$Diagnostic)
$ErrorActionPreference='Stop'
$jointBoundaryVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $jointBoundaryVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $jointBoundaryVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin;$(Join-Path $jointBoundaryVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja');$env:PATH"
$jointBoundaryArgs=@($Output)
if($Diagnostic){$jointBoundaryArgs+='--diagnostic'}
& C:/Python314/python.exe (Join-Path $PSScriptRoot 'build.py') @jointBoundaryArgs
exit $LASTEXITCODE
