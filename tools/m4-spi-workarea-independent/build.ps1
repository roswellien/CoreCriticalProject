param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$siRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$siOut=[IO.Path]::GetFullPath($OutputDirectory)
$siAllowed=Join-Path $siRoot 'reports/m4-spi-workarea/independent-review-r1'
if(-not $siOut.StartsWith($siAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $siOut)){throw 'Entirely fresh independent controls path required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$siSources=[ordered]@{};foreach($rel in @('tools/m4-spi-workarea-independent/controls.cpp','tools/m4-spi-workarea-independent/build.ps1','tools/m4-spi-workarea/native.cpp','tools/m4-spi-workarea/common.hpp','reports/m4-spi-workarea/static-r1/spec.hpp','tools/m4-startup/image_loader.cpp','tools/m4-startup/image_loader.hpp','tools/m4-startup/admission.hpp','runtime/memory/guest_memory.cpp','runtime/memory/guest_memory.hpp','runtime/core/guest_address.hpp')){$p=Join-Path $siRoot $rel;$siSources[$p]=Hash $p}
New-Item -ItemType Directory $siOut|Out-Null
foreach($p in $siSources.Keys){$t=Join-Path $siOut ('sources/'+[IO.Path]::GetRelativePath($siRoot,$p));New-Item -ItemType Directory -Force (Split-Path $t)|Out-Null;Copy-Item -LiteralPath $p -Destination $t}
$siVS='C:/Program Files/Microsoft Visual Studio/18/Community';Import-Module (Join-Path $siVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $siVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$siClang=Join-Path $siRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe';$siCommands=[Collections.Generic.List[object]]::new();$siPassed=$false
try{
 foreach($level in @('O0','O2')){$dir=Join-Path $siOut $level;New-Item -ItemType Directory $dir|Out-Null;$exe=Join-Path $dir 'controls.exe';$opt=if($level -eq 'O0'){'/Od'}else{'/O2'}
  $args=@('/nologo','/std:c++20','/EHsc','/MD',$opt,'-Wno-invalid- offsetof'.Replace(' ',''),'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',('/I'+(Join-Path $siRoot 'reports/m4-spi-workarea/static-r1')),('/I'+(Join-Path $siRoot 'tools/m4-spi-workarea')),('/I'+(Join-Path $siRoot 'tools/m4-startup')),('/I'+(Join-Path $siRoot 'runtime')),('/I'+(Join-Path $siRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include')),('/Fo'+$dir+'/'),('/Fe'+$exe),(Join-Path $PSScriptRoot 'controls.cpp'),(Join-Path $siRoot 'tools/m4-startup/image_loader.cpp'),(Join-Path $siRoot 'runtime/memory/guest_memory.cpp'),'/link','bcrypt.lib','user32.lib')
  & $siClang @args 2>&1|Tee-Object -FilePath (Join-Path $dir 'compile.log');$exit=$LASTEXITCODE;$siCommands.Add(@{command=@($siClang)+$args;exit_code=$exit});if($exit -ne 0){throw 'Independent controls compile failed'}
  $inputs=@((Join-Path $siRoot 'reports/m4-spi-workarea/static-r1/pack.bin'),(Join-Path $siRoot 'MW3/Mech3.exe'),(Join-Path $dir 'sentinels'))
  & $exe @inputs 2>&1|Tee-Object -FilePath (Join-Path $dir 'controls.log');$exit=$LASTEXITCODE;$siCommands.Add(@{command=@($exe)+$inputs;exit_code=$exit});if($exit -ne 0){throw 'Independent controls execution failed'}
 }
 foreach($p in $siSources.Keys){if((Hash $p) -ne $siSources[$p]){throw 'Source changed'}};$siPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $siOut 'failure.txt');throw}finally{
 $art=@{};foreach($f in Get-ChildItem -LiteralPath $siOut -Recurse -File){$art[$f.FullName]=Hash $f.FullName}
 @{passed=$siPassed;sources=$siSources;tools=@{$siClang=(Hash $siClang);(Get-Command link.exe).Source=(Hash (Get-Command link.exe).Source);(Get-Process -Id $PID).Path=(Hash (Get-Process -Id $PID).Path)};commands=@($siCommands);artifacts=$art;scope='Independent causal fixtures; same frozen caller body, authored query token only; no actual provider execution'}|ConvertTo-Json -Depth 14|Set-Content -Encoding utf8 -LiteralPath (Join-Path $siOut 'build.json')
}
