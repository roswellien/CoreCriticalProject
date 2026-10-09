param([string]$VSRoot='C:/Program Files/Microsoft Visual Studio/18/Community',[string]$Python='C:/Python314/python.exe',[switch]$RunComparison)
$ErrorActionPreference='Stop'
$m2Root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path.Replace('\','/')
$m2Out="$m2Root/reports/m2-boundary-extension"
$m2LLVM="$m2Root/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc"
$m2Remill="$m2Root/local/tools/remill-v6.0.1/remill-6.0.1"
$m2CMake="$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
function Invoke-M2([string]$program,[string[]]$arguments){& $program @arguments;if($LASTEXITCODE -ne 0){throw "M2 tool failed: $program"}}
Invoke-M2 $Python @("$PSScriptRoot/build.py")
Invoke-M2 $m2CMake @('-S',$PSScriptRoot,'-B',"$m2Out/build-reference",'-G','Visual Studio 18 2026','-A','Win32')
Invoke-M2 $m2CMake @('--build',"$m2Out/build-reference",'--config','Release')
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH="$m2LLVM/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
foreach($m2Level in @('O0','O2')){
 $m2Objects=(Get-ChildItem -LiteralPath $m2Out -Filter "*-$m2Level.obj" | ForEach-Object{$_.FullName.Replace('\','/')}) -join ';'
 Invoke-M2 $m2CMake @('-G','Ninja','-S',$PSScriptRoot,'-B',"$m2Out/build-$m2Level",'-DCMAKE_CXX_COMPILER=clang-cl','-DCMAKE_BUILD_TYPE=Release',"-DM2_OBJECTS=$m2Objects","-DMW34_REMILL_INCLUDE=$m2Remill/include")
 Invoke-M2 $m2CMake @('--build',"$m2Out/build-$m2Level",'--parallel','8')
}
Invoke-M2 $Python @("$PSScriptRoot/build.py",'--record')
if($RunComparison){
 Invoke-M2 $Python @("$PSScriptRoot/compare.py")
 Invoke-M2 $Python @("$PSScriptRoot/live.py")
 Invoke-M2 $Python @("$PSScriptRoot/run_controls.py")
 Invoke-M2 $Python @("$PSScriptRoot/verify.py")
}
