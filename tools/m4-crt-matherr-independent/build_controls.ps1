param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mathReviewRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mathReviewOut=[IO.Path]::GetFullPath($OutputDirectory)
$mathReviewAllowed=Join-Path $mathReviewRoot 'reports/m4-crt-matherr'
if(-not $mathReviewOut.StartsWith($mathReviewAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $mathReviewOut)){throw 'Fresh root independent output directory required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$mathReviewNative=Join-Path $mathReviewAllowed 'paired-native-build-r7/build.json'
$mathReviewMap=Get-Content -Raw -LiteralPath $mathReviewNative|ConvertFrom-Json
if(-not $mathReviewMap.passed){throw 'Frozen paired candidate positive build required'}
foreach($p in $mathReviewMap.source_files.PSObject.Properties){if((Hash $p.Name) -ne $p.Value){throw 'Frozen matherr candidate source changed'}}
$mathReviewSources=[ordered]@{}
foreach($rel in @('tools/m4-crt-matherr-independent/controls.cpp','tools/m4-crt-matherr-independent/build_controls.ps1','tools/m4-crt-matherr/paired/paired_context.hpp','tools/m4-runtime/runtime.cpp','tools/m4-runtime/runtime.hpp','tools/m4-startup/admission.hpp','tools/m4-startup/image_loader.cpp','tools/m4-startup/image_loader.hpp','runtime/memory/guest_memory.cpp','runtime/memory/guest_memory.hpp','runtime/core/guest_address.hpp')){$p=Join-Path $mathReviewRoot $rel;$mathReviewSources[$p]=Hash $p}
New-Item -ItemType Directory $mathReviewOut|Out-Null
foreach($p in $mathReviewSources.Keys){$q=Join-Path $mathReviewOut ('sources/'+[IO.Path]::GetRelativePath($mathReviewRoot,$p));New-Item -ItemType Directory -Force (Split-Path $q)|Out-Null;Copy-Item -LiteralPath $p -Destination $q}
$mathReviewCommands=[Collections.Generic.List[object]]::new();$mathReviewPassed=$false
$mathReviewVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $mathReviewVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $mathReviewVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$mathReviewCompiler=Join-Path $mathReviewRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'
try{
 foreach($level in @('O0','O2')){
  $dir=Join-Path $mathReviewOut $level;New-Item -ItemType Directory $dir|Out-Null
  $object=Join-Path $mathReviewAllowed "paired-native-build-r7/native-$level.obj"
  if((Hash $object) -ne $mathReviewMap.artifacts.PSObject.Properties[$object].Value){throw 'Exact candidate guest object required'}
  $opt=if($level -eq 'O0'){'/Od'}else{'/O2'};$exe=Join-Path $dir 'controls.exe'
  $args=@('/nologo','/showIncludes','/std:c++20','/EHs','/MD',$opt,'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',('/I'+(Join-Path $mathReviewRoot 'tools/m4-crt-matherr/paired')),('/I'+(Join-Path $mathReviewRoot 'tools/m4-runtime')),('/I'+(Join-Path $mathReviewRoot 'tools/m4-startup')),('/I'+(Join-Path $mathReviewRoot 'runtime')),('/I'+(Join-Path $mathReviewRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include')),('/Fo'+$dir+'/'),('/Fe'+$exe),(Join-Path $PSScriptRoot 'controls.cpp'),(Join-Path $mathReviewRoot 'tools/m4-runtime/runtime.cpp'),(Join-Path $mathReviewRoot 'tools/m4-startup/image_loader.cpp'),(Join-Path $mathReviewRoot 'runtime/memory/guest_memory.cpp'),$object,'/link','bcrypt.lib')
  & $mathReviewCompiler @args 2>&1|Tee-Object -FilePath (Join-Path $dir 'compile.log')|Out-Null;$exit=$LASTEXITCODE;$mathReviewCommands.Add(@{command=@($mathReviewCompiler)+$args;exit_code=$exit});if($exit -ne 0){throw 'Root matherr compile failed'}
  $inputs=@((Join-Path $mathReviewRoot 'MW3/Mech3.exe'),(Join-Path $mathReviewAllowed 'preparation-r1/source.bin'))
  & $exe @inputs 2>&1|Tee-Object -FilePath (Join-Path $dir 'controls.log');$exit=$LASTEXITCODE;$mathReviewCommands.Add(@{command=@($exe)+$inputs;exit_code=$exit});if($exit -ne 0){throw 'Root matherr causal test failed'}
 }
 foreach($p in $mathReviewSources.Keys){if((Hash $p) -ne $mathReviewSources[$p]){throw 'Root source changed during compile'}}
 $mathReviewPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mathReviewOut 'failure.txt');throw}finally{
 $artifacts=[ordered]@{};foreach($f in Get-ChildItem -LiteralPath $mathReviewOut -Recurse -File){$artifacts[$f.FullName]=Hash $f.FullName}
 [ordered]@{passed=$mathReviewPassed;sources=$mathReviewSources;tools=@{$mathReviewCompiler=(Hash $mathReviewCompiler);(Get-Command link.exe).Source=(Hash (Get-Command link.exe).Source);(Get-Process -Id $PID).Path=(Hash (Get-Process -Id $PID).Path)};commands=@($mathReviewCommands);artifacts=$artifacts;consumed_candidate_build=$mathReviewNative;consumed_candidate_build_sha256=(Hash $mathReviewNative);scope='Root independent own fixtures on exact guest objects/r9 and production typed matherr Context; no original worker execution'}|ConvertTo-Json -Depth 14|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mathReviewOut 'build.json')
}
