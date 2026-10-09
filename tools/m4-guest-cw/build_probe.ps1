param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use pwsh.exe for guest CW evidence build'}
$mwGCWRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$mwGCWOut=[IO.Path]::GetFullPath($OutputDirectory);$mwGCWAllowed=Join-Path $mwGCWRoot 'reports/m4-guest-cw'
if(-not $mwGCWOut.StartsWith($mwGCWAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Private guest CW output required'}
$mwGCWName=Split-Path $mwGCWOut -Leaf
if($mwGCWName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $mwGCWName -match '^(con|prn|aux|nul|com[0-9]|lpt[0-9])$'){throw 'Fresh simple guest CW name required'}
$mwGCWBuild=Join-Path $mwGCWRoot "build/m4-guest-cw-$mwGCWName"
if((Test-Path -LiteralPath $mwGCWOut) -or (Test-Path -LiteralPath $mwGCWBuild)){throw 'Fresh guest CW report/build required'}
function Get-MWGCWHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwGCWHardware=Join-Path $mwGCWRoot 'reports/m4-crt-cw/run-r1/original.bin';$mwGCWHardwareMap=Join-Path $mwGCWRoot 'reports/m4-crt-cw/closure-r1/pins.json'
if((Get-MWGCWHash $mwGCWHardware) -ne 'a31f18e7960db0caba66c63cfd949ba776e08b33564f17d7a0bd2918574801b4' -or (Get-MWGCWHash $mwGCWHardwareMap) -ne 'ebdef8baffc1d06d999b10c6ed5a30f339c61875c1fe75caf3cc9ce5ddcb3c90'){throw 'Frozen hardware evidence identity required'}
function Get-MWGCWSources{
 $mwGCWMap=[ordered]@{}
 $mwGCWFiles=@(Get-ChildItem -LiteralPath $PSScriptRoot -File;Get-ChildItem -LiteralPath (Join-Path $mwGCWRoot 'tests/m4-guest-cw') -File;Get-Item -LiteralPath (Join-Path $mwGCWRoot 'runtime/memory/guest_memory.cpp'),(Join-Path $mwGCWRoot 'runtime/memory/guest_memory.hpp'),(Join-Path $mwGCWRoot 'runtime/core/guest_address.hpp'),(Join-Path $PSScriptRoot '../m4-crt/probe_io.hpp'),(Join-Path $PSScriptRoot '../m4-crt/probe_common.hpp'),(Join-Path $mwGCWRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h');Get-ChildItem -LiteralPath (Join-Path $mwGCWRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/Runtime') -File -Recurse)
 foreach($mwGCWFile in $mwGCWFiles|Sort-Object FullName){$mwGCWMap[$mwGCWFile.FullName]=Get-MWGCWHash $mwGCWFile.FullName};return $mwGCWMap
}
$mwGCWSources=Get-MWGCWSources
New-Item -ItemType Directory -Path $mwGCWOut|Out-Null;$mwGCWCopies=[Collections.Generic.List[object]]::new()
foreach($mwGCWPath in $mwGCWSources.Keys){$mwGCWCopy=Join-Path (Join-Path $mwGCWOut 'sources') ([IO.Path]::GetRelativePath($mwGCWRoot,$mwGCWPath));New-Item -ItemType Directory -Force -Path (Split-Path $mwGCWCopy)|Out-Null;Copy-Item -LiteralPath $mwGCWPath -Destination $mwGCWCopy;if((Get-MWGCWHash $mwGCWCopy) -ne $mwGCWSources[$mwGCWPath]){throw 'Guest CW literal source preservation'};$mwGCWCopies.Add([ordered]@{original_path=$mwGCWPath;preserved_path=$mwGCWCopy;sha256=$mwGCWSources[$mwGCWPath]})}
$mwGCWCommands=[Collections.Generic.List[object]]::new()
function Invoke-MWGCW([string]$Program,[string[]]$Arguments,[string]$Log){$mwGCWSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{& $Program @Arguments 2>&1|Tee-Object -FilePath $Log;$mwGCWExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwGCWSaved};$mwGCWCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwGCWExit;log_path=$Log;log_sha256=(Get-MWGCWHash $Log)});if($mwGCWExit -ne 0){throw "Guest CW build tool failed $Program exit=$mwGCWExit"}}
$mwGCWVS='C:/Program Files/Microsoft Visual Studio/18/Community';$mwGCWLLVM=Join-Path $mwGCWRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc';$mwGCWPassed=$false;$mwGCWFailure=$null
try{
 Import-Module (Join-Path $mwGCWVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $mwGCWVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $mwGCWCMake=Join-Path $mwGCWVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$mwGCWCTest=Join-Path $mwGCWVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe';$mwGCWNinja=Join-Path $mwGCWVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
 $env:PATH="$mwGCWLLVM/bin;$(Split-Path $mwGCWNinja);$env:PATH";$mwGCWTemp=Join-Path $mwGCWOut 'compiler-temp';New-Item -ItemType Directory $mwGCWTemp|Out-Null;$env:TEMP=$mwGCWTemp;$env:TMP=$mwGCWTemp;$env:TMPDIR=$mwGCWTemp
 Invoke-MWGCW $mwGCWCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$mwGCWBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$mwGCWLLVM/bin/clang-cl.exe",'-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG') (Join-Path $mwGCWOut 'configure.log')
 Invoke-MWGCW $mwGCWCMake @('--build',$mwGCWBuild,'--parallel','8','--verbose') (Join-Path $mwGCWOut 'build.log')
 Invoke-MWGCW $mwGCWCTest @('--test-dir',$mwGCWBuild,'--verbose','--output-on-failure','--no-tests=error','--output-junit',(Join-Path $mwGCWOut 'ctest.xml')) (Join-Path $mwGCWOut 'ctest.log')
 foreach($mwGCWLevel in @('O0','O2')){Invoke-MWGCW (Join-Path $mwGCWBuild "mw34_guest_cw_replay_$mwGCWLevel.exe") @('--check-hash') (Join-Path $mwGCWOut "hash-$mwGCWLevel.log")}
 if((Get-MWGCWSources|ConvertTo-Json -Compress) -ne ($mwGCWSources|ConvertTo-Json -Compress)){throw 'Guest CW source changed during build'};$mwGCWPassed=$true
}catch{$mwGCWFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $mwGCWOut 'failure.txt');throw}finally{
 $mwGCWArtifacts=[ordered]@{};foreach($mwGCWFile in @(Get-ChildItem -LiteralPath $mwGCWOut -File -Recurse;if(Test-Path -LiteralPath $mwGCWBuild){Get-ChildItem -LiteralPath $mwGCWBuild -File -Recurse|Where-Object {$_.Extension -in @('.exe','.obj','.lib','.txt','.cmake','.json','.xml') -or $_.Name -in @('build.ninja','rules.ninja','.ninja_log')}})|Where-Object {$_.FullName -notmatch 'compiler-temp'}|Sort-Object FullName){$mwGCWArtifacts[$mwGCWFile.FullName]=Get-MWGCWHash $mwGCWFile.FullName}
 $mwGCWTools=[ordered]@{};foreach($mwGCWTool in @($mwGCWCMake,$mwGCWCTest,$mwGCWNinja,(Get-Process -Id $PID).Path,(Join-Path $mwGCWVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Command rc.exe -ErrorAction SilentlyContinue).Source)+@('clang-cl.exe','llvm-lib.exe','lld-link.exe','llvm-mt.exe'|ForEach-Object {Join-Path $mwGCWLLVM "bin/$_"})){if($mwGCWTool -and (Test-Path -LiteralPath $mwGCWTool)){$mwGCWTools[$mwGCWTool]=Get-MWGCWHash $mwGCWTool}}
 [ordered]@{passed=$mwGCWPassed;failure=$mwGCWFailure;scope='Separately compiled O0/O2 bounded typed guest CW transfer; actual native comparison pending';source_files=$mwGCWSources;literal_source_copies=@($mwGCWCopies);tool_files=$mwGCWTools;artifacts=$mwGCWArtifacts;commands=@($mwGCWCommands);build_directory=$mwGCWBuild;hardware_path=$mwGCWHardware;hardware_sha256=(Get-MWGCWHash $mwGCWHardware);hardware_pins_path=$mwGCWHardwareMap;hardware_pins_sha256=(Get-MWGCWHash $mwGCWHardwareMap);original_provider_executed=$false;numerical_host_cw_synchronization_admitted=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 16|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwGCWOut 'build.json')
}
