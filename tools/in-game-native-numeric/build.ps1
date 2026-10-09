param([switch]$PrepareOnly)
$ErrorActionPreference='Stop'
$nmxRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$nmxVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$nmxLLVM=Join-Path $nmxRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$nmxCmake=Join-Path $nmxVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$nmxNinja=Join-Path $nmxVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$nmxRun=Join-Path $nmxRoot ('reports/mw3-live-native-numeric/'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $nmxRun|Out-Null
$nmxCommands=[Collections.Generic.List[object]]::new()
$nmxSources=[ordered]@{}
function Hash-Nmx([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
foreach($nmxFile in Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File | Where-Object {$_.FullName -notmatch '__pycache__'}){
 $nmxSources[$nmxFile.FullName]=Hash-Nmx $nmxFile.FullName
 $nmxCopy=Join-Path $nmxRun ('sources/'+[IO.Path]::GetRelativePath($PSScriptRoot,$nmxFile.FullName))
 New-Item -ItemType Directory -Force -Path (Split-Path $nmxCopy)|Out-Null
 Copy-Item -LiteralPath $nmxFile.FullName -Destination $nmxCopy
}
$nmxCanonical=Get-Content -Raw -LiteralPath "$nmxRoot/reports/m4-fp-numeric-max-carry/native-canonical-r1/build.json"|ConvertFrom-Json
foreach($nmxRelative in @('tools/m4-runtime/runtime.cpp','tools/m4-runtime/runtime.hpp','tools/m4-startup/image_loader.cpp','tools/m4-startup/image_loader.hpp','tools/m4-startup/admission.hpp','runtime/memory/guest_memory.cpp','runtime/memory/guest_memory.hpp','runtime/core/guest_address.hpp')){
 $nmxDependency=[IO.Path]::GetFullPath((Join-Path $nmxRoot $nmxRelative))
 $nmxHash=Hash-Nmx $nmxDependency
 $nmxExpected=$nmxCanonical.source_files.PSObject.Properties[$nmxDependency].Value
 if(-not $nmxExpected -or $nmxHash-ne$nmxExpected){throw "Accepted runtime dependency changed: $nmxDependency"}
 $nmxSources[$nmxDependency]=$nmxHash
 $nmxCopy=Join-Path $nmxRun ('dependencies/'+$nmxRelative)
 New-Item -ItemType Directory -Force -Path (Split-Path $nmxCopy)|Out-Null
 Copy-Item -LiteralPath $nmxDependency -Destination $nmxCopy
}
$nmxDependency=[IO.Path]::GetFullPath((Join-Path $nmxRoot 'tools/in-game-hook/identity.hpp'))
$nmxSources[$nmxDependency]=Hash-Nmx $nmxDependency
Copy-Item -LiteralPath $nmxDependency -Destination "$nmxRun/identity.hpp"
foreach($nmxRelative in @('reports/mw3-live-native-numeric/session-mxcsr-r1/session.hpp','reports/mw3-live-native-numeric/session-mxcsr-r1/preparation.json','reports/m4-fp-numeric-max-carry/native-preparation-canonical-r1/session.hpp')){
 $nmxDependency=[IO.Path]::GetFullPath((Join-Path $nmxRoot $nmxRelative))
 $nmxSources[$nmxDependency]=Hash-Nmx $nmxDependency
 $nmxCopy=Join-Path $nmxRun ('dependencies/'+$nmxRelative)
 New-Item -ItemType Directory -Force -Path (Split-Path $nmxCopy)|Out-Null
 Copy-Item -LiteralPath $nmxDependency -Destination $nmxCopy
}
function Run-Nmx([string]$program,[string[]]$arguments,[string]$name){
 $nmxLog=Join-Path $nmxRun ($name+'.log')
 & $program @arguments 2>&1|Tee-Object -FilePath $nmxLog
 $nmxCode=$LASTEXITCODE
 $nmxCommands.Add([ordered]@{program=$program;arguments=$arguments;exit_code=$nmxCode;log=$nmxLog})
 if($nmxCode-ne0){throw "$name failed ($nmxCode)"}
}
$nmxX86=Join-Path $nmxRoot 'build/in-game-native-numeric-x86'
$nmxWorkers=[ordered]@{}
$nmxPassed=$false;$nmxFailure=$null
try{
 Run-Nmx $nmxCmake @('-S',"$PSScriptRoot/x86",'-B',$nmxX86,'-G','Visual Studio 18 2026','-A','Win32') 'configure-x86'
 Run-Nmx $nmxCmake @('--build',$nmxX86,'--config','Release') 'build-x86'
 Import-Module (Join-Path $nmxVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $nmxVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $env:PATH="$nmxLLVM;$(Split-Path $nmxNinja);$env:PATH"
 foreach($nmxLevel in @('O0','O2')){
  $nmxObject=Join-Path $nmxRoot "reports/m4-fp-numeric-max-carry/native-canonical-r1/native-$nmxLevel.obj"
  $nmxBuild=Join-Path $nmxRoot "build/in-game-native-numeric-$nmxLevel"
  $nmxOpt=if($nmxLevel-eq'O0'){'/Od'}else{'/O2'}
  Run-Nmx $nmxCmake @('-G','Ninja','-S',"$PSScriptRoot/worker",'-B',$nmxBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$nmxLLVM/clang-cl.exe","-DCMAKE_MAKE_PROGRAM=$nmxNinja","-DCMAKE_CXX_FLAGS_RELEASE=$nmxOpt /DNDEBUG","-DMW34_NMX_OBJECT=$nmxObject") "configure-$nmxLevel"
  Run-Nmx $nmxCmake @('--build',$nmxBuild,'--verbose','--parallel','4') "build-$nmxLevel"
  $nmxBuiltExe=Join-Path $nmxBuild 'mw34_numeric_worker.exe'
  $nmxExe=Join-Path $nmxRun "mw34_numeric_worker-$nmxLevel.exe"
  Copy-Item -LiteralPath $nmxBuiltExe -Destination $nmxExe
  $nmxWorkers[$nmxLevel]=[ordered]@{worker=$nmxExe;sha256=(Hash-Nmx $nmxExe);object=$nmxObject;object_sha256=(Hash-Nmx $nmxObject)}
 }
 Copy-Item -LiteralPath "$nmxX86/Release/mw34_numeric_launcher.exe" -Destination "$nmxRun/mw34_numeric_launcher.exe"
 Copy-Item -LiteralPath "$nmxX86/Release/mw34_numeric_hook.dll" -Destination "$nmxRun/mw34_numeric_hook.dll"
 foreach($nmxPath in $nmxSources.Keys){if((Hash-Nmx $nmxPath)-ne$nmxSources[$nmxPath]){throw 'Sources changed during build'}}
 $nmxPassed=$true
}catch{$nmxFailure=$_.Exception.Message;throw}finally{
 [ordered]@{passed=$nmxPassed;failure=$nmxFailure;scope='Live x86 initializer bridge to unchanged translated x64 numeric-max object; build only';run=$nmxRun;source_files=$nmxSources;commands=@($nmxCommands);workers=$nmxWorkers;launcher="$nmxRun/mw34_numeric_launcher.exe";hook="$nmxRun/mw34_numeric_hook.dll";game_launched=$false;full_M4_complete=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath "$nmxRun/build.json" -Encoding utf8
}
Write-Output "NUMERIC_BUILD_REPORT=$nmxRun/build.json"
