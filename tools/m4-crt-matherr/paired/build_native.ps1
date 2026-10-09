param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use bundled pwsh.exe'}
$mwPairRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$mwPairOut=[IO.Path]::GetFullPath($OutputDirectory)
$mwPairAllowed=Join-Path $mwPairRoot 'reports/m4-crt-matherr'
$mwPairName=Split-Path $mwPairOut -Leaf
if(-not $mwPairOut.StartsWith($mwPairAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $mwPairName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or (Test-Path -LiteralPath $mwPairOut)){throw 'Entirely fresh private native report directory required'}
$mwPairTrees=@('O0','O2'|ForEach-Object {Join-Path $mwPairRoot "build/m4-crt-matherr-paired-$mwPairName-$_"})
foreach($mwPairTree in $mwPairTrees){if(Test-Path -LiteralPath $mwPairTree){throw 'All derived native build directories must be fresh before mutation'}}
function Get-MWPairHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwPairLLVM=Join-Path $mwPairRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwPairVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwPairIR=Join-Path $mwPairAllowed 'abi-r1/host.ll'
if((Get-MWPairHash $mwPairIR) -ne '6afb5776644c82629221ad44799e2ea7c0ce821258fc0413eb04e2819ca60a4c' -or (Get-MWPairHash (Join-Path $mwPairRoot 'tools/m4-runtime/runtime.hpp')) -ne '41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536' -or (Get-MWPairHash (Join-Path $mwPairRoot 'tools/m4-runtime/runtime.cpp')) -ne '48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7'){throw 'Frozen ABI/runtime identity mismatch'}
$mwPairSources=[ordered]@{}
foreach($mwPairFile in @((Get-ChildItem -LiteralPath $PSScriptRoot -File);(Get-Item -LiteralPath (Join-Path $PSScriptRoot 'native/CMakeLists.txt'));(Get-Item -LiteralPath $mwPairIR);(Get-ChildItem -LiteralPath (Join-Path $mwPairRoot 'tools/m4-runtime') -File|Where-Object {$_.Extension -in '.cpp','.hpp'});(Get-ChildItem -LiteralPath (Join-Path $mwPairRoot 'tools/m4-startup') -File|Where-Object {$_.Extension -in '.cpp','.hpp'});(Get-ChildItem -LiteralPath (Join-Path $mwPairRoot 'runtime/memory') -File);(Get-Item -LiteralPath (Join-Path $mwPairRoot 'runtime/core/guest_address.hpp'));(Get-Item -LiteralPath (Join-Path $mwPairRoot 'tools/m4-crt/probe_common.hpp'));(Get-Item -LiteralPath (Join-Path $mwPairRoot 'tools/m4-crt/probe_io.hpp')))){$mwPairSources[$mwPairFile.FullName]=Get-MWPairHash $mwPairFile.FullName}
New-Item -ItemType Directory $mwPairOut|Out-Null
$mwPairCopies=[Collections.Generic.List[object]]::new()
foreach($mwPairPath in $mwPairSources.Keys){$mwPairCopy=Join-Path (Join-Path $mwPairOut 'sources') ([IO.Path]::GetRelativePath($mwPairRoot,$mwPairPath));New-Item -ItemType Directory -Force -Path (Split-Path $mwPairCopy)|Out-Null;Copy-Item -LiteralPath $mwPairPath -Destination $mwPairCopy;$mwPairCopies.Add([ordered]@{original_path=$mwPairPath;preserved_path=$mwPairCopy;sha256=$mwPairSources[$mwPairPath]})}
$mwPairCommands=[Collections.Generic.List[object]]::new()
function Invoke-MWPair([string]$Program,[string[]]$Arguments,[string]$Log){$mwPairSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{& $Program @Arguments 2>&1|Tee-Object -FilePath $Log|Out-Null;$mwPairExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwPairSaved};$mwPairCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwPairExit;log_path=$Log;log_sha256=(Get-MWPairHash $Log)});if($mwPairExit -ne 0){throw "Native paired tool failed $Program exit=$mwPairExit"}}
$mwPairPassed=$false;$mwPairFailure=$null;$mwPairBuilds=[Collections.Generic.List[object]]::new()
try{
 Import-Module (Join-Path $mwPairVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $mwPairVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $mwPairCMake=Join-Path $mwPairVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
 $mwPairNinja=Join-Path $mwPairVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
 $env:PATH="$mwPairLLVM;$(Split-Path $mwPairNinja);$env:PATH"
 $mwPairTemp=Join-Path $mwPairOut 'compiler-temp';New-Item -ItemType Directory $mwPairTemp|Out-Null
 $env:TEMP=$mwPairTemp;$env:TMP=$mwPairTemp;$env:TMPDIR=$mwPairTemp
 foreach($mwPairLevel in @('O0','O2')){
  $mwPairObject=Join-Path $mwPairOut "native-$mwPairLevel.obj"
  Invoke-MWPair (Join-Path $mwPairLLVM 'clang.exe') @('-target','x86_64-pc-windows-msvc',"-$mwPairLevel",'-c',$mwPairIR,'-o',$mwPairObject) (Join-Path $mwPairOut "IR-$mwPairLevel.log")
  $mwPairBuild=Join-Path $mwPairRoot "build/m4-crt-matherr-paired-$mwPairName-$mwPairLevel"
  $mwPairOpt=if($mwPairLevel -eq 'O0'){'/Od'}else{'/O2'}
  Invoke-MWPair $mwPairCMake @('-G','Ninja','-S',(Join-Path $PSScriptRoot 'native'),'-B',$mwPairBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$mwPairLLVM/clang-cl.exe","-DCMAKE_CXX_FLAGS_RELEASE=$mwPairOpt /DNDEBUG /showIncludes","-DMW34_MATHERR_OBJECT=$mwPairObject") (Join-Path $mwPairOut "configure-$mwPairLevel.log")
  Invoke-MWPair $mwPairCMake @('--build',$mwPairBuild,'--verbose','--parallel','6') (Join-Path $mwPairOut "build-$mwPairLevel.log")
  $mwPairExe=Join-Path $mwPairBuild 'mw34_matherr_paired_native.exe'
  $mwPairInputs=@((Join-Path $mwPairRoot 'MW3/Mech3.exe'),(Join-Path $mwPairRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $mwPairAllowed 'preparation-r1/source.bin'))
  Invoke-MWPair $mwPairExe (@('--unit')+$mwPairInputs+@((Join-Path $mwPairOut "unit-$mwPairLevel.json"))) (Join-Path $mwPairOut "unit-$mwPairLevel.log")
  Invoke-MWPair $mwPairExe (@('--replay')+$mwPairInputs+@((Join-Path $mwPairAllowed 'paired-original-r1-normal-windows/original.bin'),(Join-Path $mwPairOut "native-$mwPairLevel.bin"))) (Join-Path $mwPairOut "replay-$mwPairLevel.log")
  Invoke-MWPair (Join-Path $mwPairLLVM 'llvm-objdump.exe') @('--disassemble','--reloc','--x86-asm-syntax=intel',$mwPairObject) (Join-Path $mwPairOut "decode-$mwPairLevel.txt")
  Invoke-MWPair (Join-Path $mwPairLLVM 'llvm-readobj.exe') @('--unwind',$mwPairObject) (Join-Path $mwPairOut "unwind-$mwPairLevel.txt")
  $mwPairBuilds.Add([ordered]@{level=$mwPairLevel;directory=$mwPairBuild;object=$mwPairObject;worker=$mwPairExe;unit=(Join-Path $mwPairOut "unit-$mwPairLevel.json");observations=(Join-Path $mwPairOut "native-$mwPairLevel.bin")})
 }
 foreach($mwPairPath in $mwPairSources.Keys){if((Get-MWPairHash $mwPairPath) -ne $mwPairSources[$mwPairPath]){throw 'Source changed during native-only build'}}
 $mwPairPassed=$true
}catch{$mwPairFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $mwPairOut 'failure.txt');throw}finally{
 $mwPairArtifacts=[ordered]@{}
 foreach($mwPairFile in @(Get-ChildItem -LiteralPath $mwPairOut -Recurse -File;foreach($mwPairTree in $mwPairTrees){if(Test-Path -LiteralPath $mwPairTree){Get-ChildItem -LiteralPath $mwPairTree -Recurse -File|Where-Object {$_.Extension -in '.exe','.obj','.lib','.txt','.cmake','.json' -or $_.Name -in 'build.ninja','rules.ninja','.ninja_log'}}})|Where-Object {$_.FullName -notmatch 'compiler-temp'}|Sort-Object FullName){$mwPairArtifacts[$mwPairFile.FullName]=Get-MWPairHash $mwPairFile.FullName}
 $mwPairTools=[ordered]@{}
 foreach($mwPairTool in @($mwPairCMake,$mwPairNinja,(Get-Process -Id $PID).Path,(Join-Path $mwPairVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'))+@('clang.exe','clang-cl.exe','lld-link.exe','llvm-objdump.exe','llvm-readobj.exe'|ForEach-Object {Join-Path $mwPairLLVM $_})){if($mwPairTool -and (Test-Path -LiteralPath $mwPairTool)){$mwPairTools[$mwPairTool]=Get-MWPairHash $mwPairTool}}
 [ordered]@{passed=$mwPairPassed;failure=$mwPairFailure;scope='Native-only coherent State tests and offline ORIGINAL BEFORE replay; no original worker run';source_files=$mwPairSources;literal_sources=@($mwPairCopies);tool_files=$mwPairTools;artifacts=$mwPairArtifacts;commands=@($mwPairCommands);builds=@($mwPairBuilds);original_executed=$false;independent_acceptance=$false;callback_invoked=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 12|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwPairOut 'build.json')
}
