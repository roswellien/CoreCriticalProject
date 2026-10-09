param([string]$OutputDirectory,[string]$Image,[string]$Python='C:/Python314/python.exe',[string]$VSRoot='C:/Program Files/Microsoft Visual Studio/18/Community')
$ErrorActionPreference='Stop'
$mwRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path.Replace('\','/')
if(-not $OutputDirectory){$OutputDirectory="$mwRoot/reports/m4-integer-integration-r9/host"}
$mwOut=[System.IO.Path]::GetFullPath($OutputDirectory).Replace('\','/')
if(-not $mwOut.StartsWith("$mwRoot/reports/m4-integer-integration-r9/",[System.StringComparison]::OrdinalIgnoreCase)){throw 'Private combined output required'}
$mwLeaf=Split-Path $mwOut -Leaf
$mwBuilds=[ordered]@{O0="$mwRoot/build/m4-integer-integration-r9-$mwLeaf-O0";O2="$mwRoot/build/m4-integer-integration-r9-$mwLeaf-O2"}
if(Test-Path -LiteralPath $mwOut){throw 'M4 report output already exists; use an entirely fresh OutputDirectory'}
foreach($mwLevel in $mwBuilds.Keys){if(Test-Path -LiteralPath $mwBuilds[$mwLevel]){throw "M4 derived build directory already exists: $mwLevel"}}
if(-not $Image){$Image="$mwRoot/MW3/Mech3.exe"}
$Image=(Resolve-Path -LiteralPath $Image).Path.Replace('\','/')
$mwLLVM="$mwRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin"
$mwCMake="$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$mwCommands=[System.Collections.Generic.List[object]]::new()
function Invoke-MW([string]$Program,[string[]]$Arguments,[string]$Log){
    $mwCommands.Add(@($Program)+$Arguments);$mwPreference=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try{& $Program @Arguments 2>&1|Tee-Object -FilePath $Log}finally{$ErrorActionPreference=$mwPreference}
    if($LASTEXITCODE -ne 0){throw "Tool failed ($LASTEXITCODE): $Program"}
}
function Get-MWHash([string]$Path){(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()}
$mwBefore=& $Python "$PSScriptRoot/source_identity.py" $mwRoot|ConvertFrom-Json
if($LASTEXITCODE){throw 'Combined source admission failed'}
$mwPrevious=[ordered]@{
    "$mwRoot/reports/m4-initializer-chain/author-review-r1/report.json"='8829d4063d99d68bb207ee01d99408fa676eb0d3c1afcbec93fd4058eb5ea69a'
    "$mwRoot/reports/m4-initializer-chain/independent-review/r6/report.json"='d1969f101977a620a69278a587f4632d71060251550481d34855ae5b25fedd37'
    "$mwRoot/reports/m4-integer-startup/author-review-r1/report.json"='b2d371ee42f7721f8822fdff52261bc374cba23a522dbee78a968aec544e55cb'
    "$mwRoot/reports/m4-runtime/context-r9/build.json"='12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5'
    "$mwRoot/reports/m4-runtime/independent-service-r9/report.json"='27a48065b1d9e046a138379d6ded99bc691e4813a0337a9b7709afe920035886'
    "$mwRoot/reports/m4-runtime/independent-service-r9/pins.json"='3e1c6fd2124e84b6af78cffd09cb5f841afaf0f3e93b6f668a952149eed3b949'
    "$mwRoot/reports/m4-integer-startup/independent-review/r3/report.json"='6804a3834186b57c9db89e94f5a3f476fb3e3945af392d0c6b0357cc4b23fc02'
}
foreach($mwPin in $mwPrevious.Keys){if((Get-MWHash $mwPin)-ne $mwPrevious[$mwPin]){throw 'Frozen combined dependency differs'}}
$mwChainBuildPath="$mwRoot/reports/m4-initializer-chain/runtime-preflight-3/build.json";$mwBatchBuildPath="$mwRoot/reports/m4-integer-startup/batch-r2/build.json"
$mwChain=Get-Content -Raw -LiteralPath $mwChainBuildPath|ConvertFrom-Json;$mwBatch=Get-Content -Raw -LiteralPath $mwBatchBuildPath|ConvertFrom-Json
if((Get-MWHash $mwChainBuildPath)-ne '16da6941b8662aef374600076114ec339821e48c250f8ca7d136611b052a4925' -or (Get-MWHash $mwBatchBuildPath)-ne '59d5473ce02d8be6c088592a8ad4fe9ba501e4b78fae952f316d389281f4fae3'){throw 'Frozen object-producing build differs'}
New-Item -ItemType Directory $mwOut|Out-Null
Invoke-MW $Python @("$PSScriptRoot/check_build_paths.py",'--powershell',(Get-Process -Id $PID).Path,'--recipe',"$PSScriptRoot/build_host.ps1",'--output',"$mwOut/build-directory-controls.json") "$mwOut/build-directory-controls.log"
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$env:PATH="$mwLLVM;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
$mwTemp="$mwOut/compiler-temp";New-Item -ItemType Directory $mwTemp|Out-Null;$env:TEMP=$mwTemp;$env:TMP=$mwTemp;$env:TMPDIR=$mwTemp
$mwWorkers=[ordered]@{};$mwObjects=[ordered]@{}
foreach($mwLevel in $mwBuilds.Keys){
    $mwChainObject="$mwRoot/reports/m4-initializer-chain/runtime-preflight-3/native-$mwLevel.obj";$mwBatchObject="$mwRoot/reports/m4-integer-startup/batch-r2/native-$mwLevel.obj"
    $mwChainHash=Get-MWHash $mwChainObject;$mwBatchHash=Get-MWHash $mwBatchObject
    if($mwChainHash-ne $mwChain.artifacts."native-$mwLevel.obj" -or $mwBatchHash-ne $mwBatch.artifacts."native-$mwLevel.obj"){throw 'Frozen compiled guest object differs'}
    $mwObjects[$mwLevel]=[ordered]@{chain_path=$mwChainObject;chain_sha256=$mwChainHash;integer_path=$mwBatchObject;integer_sha256=$mwBatchHash}
    Invoke-MW $mwCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$mwBuilds[$mwLevel],"-DMW34_CHAIN_OBJECT=$mwChainObject","-DMW34_INTEGER_OBJECT=$mwBatchObject","-DMW34_REMILL_INCLUDE=$mwRoot/local/tools/remill-v6.0.1/remill-6.0.1/include",'-DCMAKE_CXX_COMPILER=clang-cl','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG -Wno-invalid-offsetof') "$mwOut/$mwLevel-configure.log"
    Invoke-MW $mwCMake @('--build',$mwBuilds[$mwLevel],'--parallel','8') "$mwOut/$mwLevel-build.log"
    $mwWorkers[$mwLevel]="$($mwBuilds[$mwLevel])/mw34_m4_integer_host.exe"
    Invoke-MW $mwWorkers[$mwLevel] @($Image,$mwChainHash,(Get-MWHash "$mwRoot/reports/m4-initializer-chain/independent-review/r6/report.json"),$mwBatchHash,(Get-MWHash "$mwRoot/reports/m4-integer-startup/author-review-r1/report.json")) "$mwOut/$mwLevel-actual.log"
}
Invoke-MW $Python @("$PSScriptRoot/check_observations.py",'--logs',"$mwOut/O0-actual.log","$mwOut/O2-actual.log",'--output',"$mwOut/observations.json") "$mwOut/observations.log"
$mwAfter=& $Python "$PSScriptRoot/source_identity.py" $mwRoot|ConvertFrom-Json
if($LASTEXITCODE -or $mwAfter.source_digest-ne $mwBefore.source_digest){throw 'Combined sources changed during compile; preserve this run and rebuild fresh'}
$mwTools=[ordered]@{}
foreach($mwTool in @($Python,$mwCMake,"$mwLLVM/clang-cl.exe",(Get-Process -Id $PID).Path,"$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll")){$mwTools[$mwTool]=Get-MWHash $mwTool}
foreach($mwLevel in $mwBuilds.Keys){
    $mwCache="$($mwBuilds[$mwLevel])/CMakeCache.txt";Copy-Item -LiteralPath $mwCache -Destination "$mwOut/$mwLevel-CMakeCache.txt"
    foreach($mwLine in Get-Content -LiteralPath $mwCache){if($mwLine-match '^CMAKE_(CXX_COMPILER|AR|LINKER|MT|RC_COMPILER|MAKE_PROGRAM):(?:FILEPATH|STRING)=(.+)$'){$mwTool=$matches[2];if(-not [System.IO.Path]::IsPathRooted($mwTool)){throw 'Build-selected tool path not absolute'};$mwTools[$mwTool]=Get-MWHash $mwTool}}
    foreach($mwCompiler in Get-ChildItem -LiteralPath "$($mwBuilds[$mwLevel])/CMakeFiles" -Recurse -File -Filter 'CMake*Compiler.cmake'){Copy-Item -LiteralPath $mwCompiler.FullName -Destination "$mwOut/$mwLevel-$($mwCompiler.Name)"}
}
$mwArtifacts=[ordered]@{};foreach($mwFile in Get-ChildItem -LiteralPath $mwOut -File){$mwArtifacts[$mwFile.Name]=Get-MWHash $mwFile.FullName}
foreach($mwWorker in $mwWorkers.Values){$mwArtifacts[$mwWorker]=Get-MWHash $mwWorker}
$mwRecord=[ordered]@{schema_version=1;profile='m4-combined-sixteen-integer-roots';passed=$true;scope='Actual selected16-root dispatcher/image/stack/persistentState integration; full CRT/M4 remains open';source_digest=$mwAfter.source_digest;source_files=$mwAfter.absolute_source_files;source_relative_files=$mwAfter.source_files;tool_files=$mwTools;artifacts=$mwArtifacts;workers=$mwWorkers;objects=$mwObjects;previous_gate_pins=$mwPrevious;image_path=$Image;image_sha256=Get-MWHash $Image;runtime_build="$mwRoot/reports/m4-runtime/context-r9/build.json";runtime_abi='Freshly compiled C++ adapters/header-dependent code against exact r9';chain_build=$mwChainBuildPath;integer_build=$mwBatchBuildPath;commands=$mwCommands.ToArray();registered_roots=16;actual_callbacks_per_level=16;full_ledger_completed=$false;defined_flags_mask=0xcc5}
$mwRecord|ConvertTo-Json -Depth 15|Set-Content -Encoding utf8 "$mwOut/build.json"
