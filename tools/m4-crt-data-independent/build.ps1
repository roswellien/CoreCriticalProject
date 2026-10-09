param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$riRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$riOut=[IO.Path]::GetFullPath($OutputDirectory)
$riAllowed=Join-Path $riRoot 'reports/m4-crt-data/independent-review-r1'
if(-not $riOut.StartsWith($riAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Independent private path required'}
if(Test-Path -LiteralPath $riOut){throw 'Entirely fresh independent build directory required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$riLibraries=@{}
foreach($level in @('O0','O2')){$p=Join-Path $riRoot "build/m4-crt-data-ownership-build-r3/Release/data_reference_$level.lib";$riLibraries[$p]=Hash $p}
New-Item -ItemType Directory $riOut|Out-Null
$riSources=[ordered]@{}
foreach($rel in @('tools/m4-crt-data-independent/ownership.cpp','tools/m4-crt-data-independent/build.ps1','tools/m4-crt-data/data_imports.hpp','tools/m4-runtime/runtime.hpp','tools/m4-startup/admission.hpp','tools/m4-startup/image_loader.hpp','runtime/core/guest_address.hpp','runtime/memory/guest_memory.hpp')){$p=Join-Path $riRoot $rel;$riSources[$p]=Hash $p;$copy=Join-Path (Join-Path $riOut 'sources') $rel;New-Item -ItemType Directory -Force (Split-Path $copy)|Out-Null;Copy-Item -LiteralPath $p -Destination $copy;if((Hash $copy) -ne $riSources[$p]){throw 'Source copy identity'}}
$riVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $riVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $riVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$riCommands=[Collections.Generic.List[object]]::new()
$riPassed=$false;$riFailure=$null
try{
 foreach($level in @('O0','O2')){
  $riLib=Join-Path $riRoot "build/m4-crt-data-ownership-build-r3/Release/data_reference_$level.lib"
  $riExe=Join-Path $riOut "independent-$level.exe";$riObj=Join-Path $riOut "independent-$level.obj"
  $riOpt=if($level -eq 'O0'){'/Od'}else{'/O2'}
  $riArgs=@('/nologo','/EHsc','/std:c++20','/W4','/WX','/wd4324','/permissive-','/MD',$riOpt,"/I$(Join-Path $riRoot 'tools/m4-crt-data')","/I$(Join-Path $riRoot 'tools/m4-runtime')","/I$(Join-Path $riRoot 'tools/m4-startup')","/I$(Join-Path $riRoot 'runtime')","/Fo$riObj","/Fe$riExe",(Join-Path $PSScriptRoot 'ownership.cpp'),$riLib,'bcrypt.lib')
  & cl.exe @riArgs 2>&1|Tee-Object -FilePath (Join-Path $riOut "compile-$level.log")
  $riCode=$LASTEXITCODE;$riCommands.Add(@{program=(Get-Command cl.exe).Source;arguments=$riArgs;exit_code=$riCode});if($riCode -ne 0){throw "Independent compile $level failed"}
  $riInputs=@((Join-Path $riRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $riRoot 'MW3/Mech3.exe'),(Join-Path $riRoot 'reports/m4-crt-data/commandline-run-r1/original.bin'))
  & $riExe @riInputs 2>&1|Tee-Object -FilePath (Join-Path $riOut "run-$level.log")
  $riCode=$LASTEXITCODE;$riCommands.Add(@{program=$riExe;arguments=$riInputs;exit_code=$riCode});if($riCode -ne 0){throw "Independent ownership $level failed"}
 }
 foreach($p in $riSources.Keys){if((Hash $p) -ne $riSources[$p]){throw 'Consumed source mutated'}}
 foreach($p in $riLibraries.Keys){if((Hash $p) -ne $riLibraries[$p]){throw 'Frozen library mutated'}}
 $riPassed=$true
}catch{$riFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $riOut 'failure.txt');throw}finally{
 $riTools=[ordered]@{};foreach($p in @((Get-Process -Id $PID).Path,(Get-Command cl.exe).Source,(Get-Command link.exe).Source,(Join-Path $riVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'))){$riTools[$p]=Hash $p}
 $riArtifacts=[ordered]@{};foreach($f in Get-ChildItem -LiteralPath $riOut -Recurse -File){$riArtifacts[$f.FullName]=Hash $f.FullName}
 @{passed=$riPassed;failure=$riFailure;source_files=$riSources;frozen_libraries=$riLibraries;tool_files=$riTools;artifacts=$riArtifacts;commands=@($riCommands);scope='Independent tests of frozen reference projection; no original/native OS code executed'}|ConvertTo-Json -Depth 14|Set-Content -Encoding utf8 -LiteralPath (Join-Path $riOut 'build.json')
}
