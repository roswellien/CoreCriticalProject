param([Parameter(Mandatory=$true)][string]$OutputDirectory,[string]$PreparationDirectory='D:/Projects/MW34Recomp/reports/m4-crt-entry-matherr/preparation-r1')
$ErrorActionPreference='Stop'
$reviewRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$reviewOut=[IO.Path]::GetFullPath($OutputDirectory);$reviewPrep=[IO.Path]::GetFullPath($PreparationDirectory)
$reviewBase=Join-Path $reviewRoot 'reports/m4-crt-entry-matherr'
if([IO.Path]::GetDirectoryName($reviewOut)-ne$reviewBase-or(Test-Path -LiteralPath $reviewOut)-or(Split-Path $reviewOut -Leaf)-notlike'independent-*'){throw 'Fresh immediate independent report required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$reviewPins=Get-Content -Raw -LiteralPath (Join-Path $reviewPrep 'pins.json')|ConvertFrom-Json
foreach($binding in $reviewPins.files.PSObject.Properties){if((Hash $binding.Name)-ne$binding.Value){throw 'Prepared candidate changed'}}
$reviewSources=[ordered]@{};foreach($rel in @('tools/m4-crt-entry-matherr-review/controls.cpp','tools/m4-crt-entry-matherr-review/build_controls.ps1','tools/m4-crt/crt_services.cpp','tools/m4-crt/crt_services.hpp','tools/m4-crt-entry-matherr/capture.s','tools/m4-runtime/runtime.cpp','tools/m4-runtime/runtime.hpp')){$p=Join-Path $reviewRoot $rel;$reviewSources[$p]=Hash $p}
foreach($file in Get-ChildItem -LiteralPath $reviewPrep -File){$reviewSources[$file.FullName]=Hash $file.FullName}
New-Item -ItemType Directory -Path $reviewOut|Out-Null
foreach($p in $reviewSources.Keys){$q=Join-Path $reviewOut ('sources/'+[IO.Path]::GetRelativePath($reviewRoot,$p));New-Item -ItemType Directory -Force -Path (Split-Path $q)|Out-Null;Copy-Item -LiteralPath $p -Destination $q}
$reviewVS='C:/Program Files/Microsoft Visual Studio/18/Community';$reviewLLVM=Join-Path $reviewRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$reviewCommands=[Collections.Generic.List[object]]::new();$reviewPassed=$false
Import-Module (Join-Path $reviewVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $reviewVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
function Run([string]$p,[string[]]$a,[string]$log){[IO.File]::WriteAllBytes($log,[byte[]]::new(0));&$p @a 2>&1|Tee-Object -FilePath $log|Out-Null;$exitCode=$LASTEXITCODE;$reviewCommands.Add([ordered]@{program=$p;arguments=$a;exit_code=$exitCode;log_path=$log;log_sha256=(Hash $log)});if($exitCode-ne0){throw ('Independent tool failed '+$p)}}
try{
 foreach($level in @('O0','O2')){
  $dir=Join-Path $reviewOut $level;New-Item -ItemType Directory -Path $dir|Out-Null
  $entry=Join-Path $reviewRoot "reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-$level.obj";$matherr=Join-Path $reviewRoot "reports/m4-crt-matherr/paired-native-build-r7/native-$level.obj";$library=Join-Path $reviewRoot "build/m4-fdiv-native-build-r3-$level/fdiv_registry.lib"
  $capture=Join-Path $dir 'capture.obj';Run (Join-Path $reviewLLVM 'clang.exe') @('--target=x86_64-pc-windows-msvc','-c',(Join-Path $reviewRoot 'tools/m4-crt-entry-matherr/capture.s'),'-o',$capture) (Join-Path $dir 'capture.log')
  $opt=if($level-eq'O0'){'/Od'}else{'/O2'};$exe=Join-Path $dir 'controls.exe'
  $a=@('/nologo','/std:c++20','/EHs','/MD','/showIncludes',$opt,'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',('/DMW34_ENTRY_OBJECT_SHA="'+(Hash $entry)+'"'),'/DMW34_REPLAY_INPUT_SHA="4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a"',('/I'+$reviewPrep))
  foreach($rel in @('tools/m4-crt-entry-matherr','tools/m4-crt','tools/m4-crt-fdiv','tools/m4-runtime','tools/m4-startup','tools/m4-guest-cw','runtime','local/tools/remill-v6.0.1/remill-6.0.1/include')){$a+=('/I'+(Join-Path $reviewRoot $rel))}
  $a+=@(('/Fo'+$dir+'/'),('/Fe'+$exe),(Join-Path $PSScriptRoot 'controls.cpp'),(Join-Path $reviewRoot 'tools/m4-crt/crt_services.cpp'),$entry,$matherr,$capture,$library,'/link','bcrypt.lib')
  Run (Join-Path $reviewLLVM 'clang-cl.exe') $a (Join-Path $dir 'compile.log')
  $inputs=@((Join-Path $reviewRoot 'MW3/Mech3.exe'),$entry,(Join-Path $reviewRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $reviewRoot 'reports/m4-crt-fdiv/native-derived-r1/pack.bin'),(Join-Path $reviewRoot 'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin'),(Join-Path $dir 'actual'))
  Run $exe $inputs (Join-Path $dir 'controls.log')
 }
 foreach($p in $reviewSources.Keys){if((Hash $p)-ne$reviewSources[$p]){throw 'Independent source changed during actual build'}}
 $reviewPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $reviewOut 'failure.txt');throw}finally{
 $artifacts=[ordered]@{};foreach($f in Get-ChildItem -LiteralPath $reviewOut -Recurse -File){$artifacts[$f.FullName]=Hash $f.FullName}
 $tools=[ordered]@{};foreach($p in @((Join-Path $reviewLLVM 'clang.exe'),(Join-Path $reviewLLVM 'clang-cl.exe'),(Get-Command link.exe).Source,(Get-Process -Id $PID).Path)){$tools[$p]=Hash $p}
 [ordered]@{passed=$reviewPassed;scope='Independent authored fixtures on exact production composition, persistent original-BEFORE FDIV writer, frozen entry and matherr objects; no original process/game';sources=$reviewSources;tools=$tools;commands=@($reviewCommands);artifacts=$artifacts;ordinary_game_launched=$false;original_executed=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $reviewOut 'build.json')
}
