param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$icRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$icOut=[IO.Path]::GetFullPath($OutputDirectory)
$icAllowed=Join-Path $icRoot 'reports/m4-crt-control-integration/independent-final-review-r1'
if(-not $icOut.StartsWith($icAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $icOut)){throw 'Entirely fresh independent controls path required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$icNative=Join-Path $icRoot 'reports/m4-crt-control-integration/native-build-r1/build.json'
if((Hash $icNative) -ne '5df2ad8c63acbc2236a1760b2fc8fe62770a304ae6eb5f1fb8ed70e9262ed524'){throw 'Exact frozen guest-object build required'}
$icMap=Get-Content -Raw -LiteralPath $icNative|ConvertFrom-Json
$icSources=[ordered]@{};foreach($rel in @('tools/m4-crt-control-integration-independent/controls.cpp','tools/m4-crt-control-integration-independent/build.ps1','tools/m4-crt-control-integration/native_context.hpp','tools/m4-crt-control-integration/common.hpp','tools/m4-crt/probe_common.hpp','tools/m4-runtime/runtime.cpp','tools/m4-runtime/runtime.hpp','tools/m4-startup/image_loader.cpp','tools/m4-startup/image_loader.hpp','tools/m4-startup/admission.hpp','tools/m4-guest-cw/guest_cw.cpp','tools/m4-guest-cw/guest_cw.hpp','runtime/memory/guest_memory.cpp','runtime/memory/guest_memory.hpp','runtime/core/guest_address.hpp','local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h')){$p=Join-Path $icRoot $rel;$icSources[$p]=Hash $p}
foreach($p in $icMap.source_files.PSObject.Properties){if((Hash $p.Name) -ne $p.Value){throw 'Frozen native source changed'}}
foreach($p in $icMap.artifacts.PSObject.Properties){if((Hash $p.Name) -ne $p.Value){throw 'Frozen native artifact changed'}}
New-Item -ItemType Directory $icOut|Out-Null
foreach($p in $icSources.Keys){$t=Join-Path $icOut ('sources/'+[IO.Path]::GetRelativePath($icRoot,$p));New-Item -ItemType Directory -Force (Split-Path $t)|Out-Null;Copy-Item -LiteralPath $p -Destination $t}
$icVS='C:/Program Files/Microsoft Visual Studio/18/Community';Import-Module (Join-Path $icVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $icVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$icClang=Join-Path $icRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe';$icCommands=[Collections.Generic.List[object]]::new();$icPassed=$false
try{
 foreach($level in @('O0','O2')){$dir=Join-Path $icOut $level;New-Item -ItemType Directory $dir|Out-Null;$exe=Join-Path $dir 'controls.exe';$opt=if($level -eq 'O0'){'/Od'}else{'/O2'};$object=Join-Path $icRoot "reports/m4-crt-control-integration/native-build-r1/native-$level.obj";$artifact=Hash $object
  $args=@('/nologo','/showIncludes','/std:c++20','/EHsc','/MD',$opt,'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',('/DMW34_CONNECTED_ARTIFACT_SHA="'+$artifact+'"'),('/I'+(Join-Path $icRoot 'tools/m4-crt-control-integration')),('/I'+(Join-Path $icRoot 'tools/m4-runtime')),('/I'+(Join-Path $icRoot 'tools/m4-startup')),('/I'+(Join-Path $icRoot 'tools/m4-guest-cw')),('/I'+(Join-Path $icRoot 'tools/m4-crt')),('/I'+(Join-Path $icRoot 'runtime')),('/I'+(Join-Path $icRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include')),('/Fo'+$dir+'/'),('/Fe'+$exe),(Join-Path $PSScriptRoot 'controls.cpp'),(Join-Path $icRoot 'tools/m4-runtime/runtime.cpp'),(Join-Path $icRoot 'tools/m4-startup/image_loader.cpp'),(Join-Path $icRoot 'tools/m4-guest-cw/guest_cw.cpp'),(Join-Path $icRoot 'runtime/memory/guest_memory.cpp'),$object,'/link','bcrypt.lib')
  & $icClang @args 2>&1|Tee-Object -FilePath (Join-Path $dir 'compile.log');$exit=$LASTEXITCODE;$icCommands.Add(@{command=@($icClang)+$args;exit_code=$exit});if($exit -ne 0){throw 'Independent controls compile failed'}
  $inputs=@((Join-Path $icRoot 'MW3/Mech3.exe'),(Join-Path $icRoot 'reports/m4-crt-control-integration/research-r1/pack.bin'))
  & $exe @inputs 2>&1|Tee-Object -FilePath (Join-Path $dir 'controls.log');$exit=$LASTEXITCODE;$icCommands.Add(@{command=@($exe)+$inputs;exit_code=$exit});if($exit -ne 0){throw 'Independent controls execution failed'}
 }
 foreach($p in $icSources.Keys){if((Hash $p) -ne $icSources[$p]){throw 'Independent source changed'}};$icPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $icOut 'failure.txt');throw}finally{
 $art=@{};foreach($f in Get-ChildItem -LiteralPath $icOut -Recurse -File){$art[$f.FullName]=Hash $f.FullName}
 @{passed=$icPassed;sources=$icSources;tools=@{$icClang=(Hash $icClang);(Get-Command link.exe).Source=(Hash (Get-Command link.exe).Source);(Get-Process -Id $PID).Path=(Hash (Get-Process -Id $PID).Path)};commands=@($icCommands);artifacts=$art;consumed_native_build=$icNative;consumed_native_sha=(Hash $icNative);scope='Independent compiled faults plus repaired-trigger poisoned-retry and boundary/unaligned/CW positives; exact frozen guest objects and r9 Runtime, no numerical following callback'}|ConvertTo-Json -Depth 14|Set-Content -Encoding utf8 -LiteralPath (Join-Path $icOut 'build.json')
}
