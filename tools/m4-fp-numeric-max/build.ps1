param([Parameter(Mandatory=$true)][string]$OutputDirectory,[switch]$Repair)
$ErrorActionPreference='Stop'
$mwRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$mwOut=[IO.Path]::GetFullPath($OutputDirectory);$mwName=Split-Path $mwOut -Leaf
if(-not $mwOut.StartsWith((Join-Path $mwRoot 'reports/m4-fp-numeric-max')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $mwName -notmatch '^[a-z0-9-]+$'){throw 'Fresh private simple FP path required'}
$mwBuilds=[ordered]@{x86=(Join-Path $mwOut "build-x86");O0=(Join-Path $mwOut "build-O0");O2=(Join-Path $mwOut "build-O2")}
if(Test-Path -LiteralPath $mwOut){throw 'Existing report directory rejected before mutation'}
foreach($mwPath in $mwBuilds.Values){if(Test-Path -LiteralPath $mwPath){throw 'Existing build directory rejected before mutation'}}
$mwVS='C:/Program Files/Microsoft Visual Studio/18/Community';$mwLLVM=Join-Path $mwRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$mwRemill=Join-Path $mwRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'
$mwProbe=Join-Path $mwRoot 'reports/m4-fp-numeric-max/recovery-r1';$mwCMake=Join-Path $mwVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$mwNinja=Join-Path $mwVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe';$mwPython='C:/Python314/python.exe'
function Hash-MW([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwAncestors=[ordered]@{}
foreach($mwRelative in @('reports/m4-fp-numeric-max/recovery-r1/pins.json')){
    $mwPin=Join-Path $mwRoot $mwRelative;$mwMap=Get-Content -LiteralPath $mwPin -Raw|ConvertFrom-Json
    foreach($mwPair in $mwMap.bindings){if((Hash-MW $mwPair.path)-ne $mwPair.sha256){throw "Ancestor changed: $($mwPair.path)"};$mwAncestors[$mwPair.path]=$mwPair.sha256};$mwAncestors[$mwPin]=Hash-MW $mwPin
}
$mwSources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-Item -LiteralPath (Join-Path $mwRoot 'tools/lifting/host_adapter.py'))+@(Get-Item -LiteralPath (Join-Path $mwProbe 'spec.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwRoot 'runtime/memory/guest_memory.cpp'))+@(Get-Item -LiteralPath (Join-Path $mwRoot 'runtime/memory/guest_memory.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwRoot 'runtime/core/guest_address.hpp'))+@(Get-ChildItem -LiteralPath (Join-Path $mwRemill 'remill/Arch/Runtime') -Filter '*.h')+@(Get-ChildItem -LiteralPath (Join-Path $mwRemill 'remill/Arch/X86/Runtime') -Filter '*.h')
$mwSourceIDs=[ordered]@{};New-Item -ItemType Directory -Path $mwOut|Out-Null
foreach($mwSource in $mwSources){$mwSourceIDs[$mwSource.FullName]=Hash-MW $mwSource.FullName;$mwTarget=Join-Path $mwOut ('sources/'+[IO.Path]::GetRelativePath($mwRoot,$mwSource.FullName));New-Item -ItemType Directory -Path (Split-Path $mwTarget -Parent) -Force|Out-Null;Copy-Item -LiteralPath $mwSource.FullName -Destination $mwTarget}
$mwCommands=[Collections.Generic.List[object]]::new();$mwToolPaths=[Collections.Generic.List[string]]::new();$mwPassed=$false
function Run-MW([string]$p,[string[]]$Arguments,[string]$Log){
    [IO.File]::WriteAllText($Log,'');$mwPreference=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try{& $p @Arguments 2>&1|Tee-Object -FilePath $Log;$mwExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwPreference}
    $mwCommands.Add([ordered]@{program=$p;arguments=$Arguments;exit_code=$mwExit;log=$Log;log_sha256=(Hash-MW $Log)})
    if($mwExit-ne 0){throw "Simple FP tool failed: $p exit=$mwExit"}
}
try{
    Import-Module (Join-Path $mwVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $mwVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
    Run-MW $mwCMake @('-S',$PSScriptRoot,'-B',$mwBuilds.x86,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_PROBE_INCLUDE=$mwProbe") (Join-Path $mwOut 'configure-x86.log')
    Run-MW $mwCMake @('--build',$mwBuilds.x86,'--config','Release','--verbose') (Join-Path $mwOut 'build-x86.log')
    foreach($mwTool in @('cl.exe','ml.exe','link.exe')){$mwToolPaths.Add((Get-Command $mwTool).Source)}
    Enter-VsDevShell -VsInstallPath $mwVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    foreach($mwEntry in @('4c19f0','4c1a00','780c10f0')){
        Run-MW $mwPython @((Join-Path $PSScriptRoot 'adapt.py'),(Join-Path $mwRoot "reports/m4-fp-numeric-max/recovery-r1/$mwEntry.ll"),(Join-Path $mwOut "$mwEntry-host.ll"),(Join-Path $mwOut "$mwEntry-adapter.json")) (Join-Path $mwOut "$mwEntry-adapter.log")
        if($Repair){Run-MW $mwPython @((Join-Path $PSScriptRoot 'repair.py'),(Join-Path $mwOut "$mwEntry-host.ll"),(Join-Path $mwOut "$mwEntry-repaired.ll"),(Join-Path $mwOut "$mwEntry-repair.json")) (Join-Path $mwOut "$mwEntry-repair.log")}
    }
    $mwSuffix=if($Repair){'repaired'}else{'host'}
    Run-MW (Join-Path $mwLLVM 'llvm-link.exe') @('-S',(Join-Path $mwOut "4c19f0-$mwSuffix.ll"),(Join-Path $mwOut "4c1a00-$mwSuffix.ll"),(Join-Path $mwOut "780c10f0-$mwSuffix.ll"),'-o',(Join-Path $mwOut 'linked.ll')) (Join-Path $mwOut 'link.log')
    Run-MW (Join-Path $mwLLVM 'opt.exe') @('-passes=verify','-S',(Join-Path $mwOut 'linked.ll'),'-o',(Join-Path $mwOut 'verified.ll')) (Join-Path $mwOut 'verify.log')
    Run-MW (Join-Path $mwLLVM 'opt.exe') @('-passes=default<O2>,verify','-S',(Join-Path $mwOut 'verified.ll'),'-o',(Join-Path $mwOut 'optimized.ll')) (Join-Path $mwOut 'optimize.log')
    foreach($mwLevel in @('O0','O2')){
        $mwObject=Join-Path $mwOut "native-$mwLevel.obj";$mwIR=if($mwLevel-eq 'O0'){Join-Path $mwOut 'verified.ll'}else{Join-Path $mwOut 'optimized.ll'}
        Run-MW (Join-Path $mwLLVM 'llc.exe') @('-filetype=obj',"-$mwLevel",$mwIR,'-o',$mwObject) (Join-Path $mwOut "llc-$mwLevel.log")
        Run-MW $mwCMake @('-S',$PSScriptRoot,'-B',$mwBuilds[$mwLevel],'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$mwNinja",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$(Join-Path $mwLLVM 'clang-cl.exe')","-DMW34_HOST_OBJECT=$mwObject","-DMW34_REPAIRED=$([bool]$Repair)","-DMW34_PROBE_INCLUDE=$mwProbe","-DMW34_REMILL_INCLUDE=$mwRemill") (Join-Path $mwOut "configure-$mwLevel.log")
        Run-MW $mwCMake @('--build',$mwBuilds[$mwLevel],'--verbose') (Join-Path $mwOut "build-$mwLevel.log")
        $mwWorker=Join-Path $mwBuilds[$mwLevel] 'mw34_numeric_native.exe'
        Run-MW $mwWorker @('--check-context',(Join-Path $mwProbe 'pages.bin'),(Join-Path $mwRoot 'MW3/Mech3.exe'),(Join-Path $mwRoot 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL')) (Join-Path $mwOut "controls-$mwLevel.log")
        Run-MW $mwWorker @((Join-Path $mwProbe 'pages.bin'),(Join-Path $mwRoot 'MW3/Mech3.exe'),(Join-Path $mwRoot 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),(Join-Path $mwOut "default-$mwLevel.bin")) (Join-Path $mwOut "default-$mwLevel.log")
        Run-MW $mwWorker @((Join-Path $mwProbe 'pages.bin'),(Join-Path $mwRoot 'MW3/Mech3.exe'),(Join-Path $mwRoot 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),(Join-Path $mwOut "directed-$mwLevel.bin"),'--directed') (Join-Path $mwOut "directed-$mwLevel.log")
    }
    foreach($mwSource in $mwSources){if((Hash-MW $mwSource.FullName)-ne $mwSourceIDs[$mwSource.FullName]){throw 'Sources changed during compile'}};$mwPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwOut 'failure.txt');throw}
finally{
    $mwBindings=[ordered]@{};foreach($mwPair in $mwAncestors.GetEnumerator()){$mwBindings[$mwPair.Key]=$mwPair.Value};foreach($mwPair in $mwSourceIDs.GetEnumerator()){$mwBindings[$mwPair.Key]=$mwPair.Value}
    foreach($mwFolder in @($mwOut)+@($mwBuilds.Values)){if(Test-Path -LiteralPath $mwFolder){foreach($mwFile in Get-ChildItem -LiteralPath $mwFolder -Recurse -File){$mwBindings[$mwFile.FullName]=Hash-MW $mwFile.FullName}}}
    foreach($mwTool in @($mwPython,$mwCMake,$mwNinja,(Join-Path $mwVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path,(Join-Path $mwLLVM 'clang-cl.exe'),(Join-Path $mwLLVM 'LLVM-C.dll'),(Join-Path $mwLLVM 'llc.exe'),(Join-Path $mwLLVM 'opt.exe'),(Join-Path $mwLLVM 'llvm-link.exe'))+@($mwToolPaths)){if($mwTool){$mwBindings[$mwTool]=Hash-MW $mwTool}}
    [ordered]@{passed=$mwPassed;scope='Two complete simple FP original/native observation candidates; no full FP/startup admission';repaired=[bool]$Repair;sources=$mwSourceIDs;commands=$mwCommands;bindings=$mwBindings;builds=$mwBuilds;original_worker=(Join-Path $mwBuilds.x86 'Release/mw34_numeric_reference.exe');records_directed=13824;records_default=864}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwOut 'build.json')
}
