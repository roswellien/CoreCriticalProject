param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwFPWorkspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwFPOutput=[IO.Path]::GetFullPath($OutputDirectory)
$mwFPAllowed=(Join-Path $mwFPWorkspace 'reports/m4-fp-native')+[IO.Path]::DirectorySeparatorChar
if(-not $mwFPOutput.StartsWith($mwFPAllowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Private fresh FP report path required'}
$mwFPName=Split-Path $mwFPOutput -Leaf
if($mwFPName -notmatch '^[a-z0-9-]+$' -or (Test-Path -LiteralPath $mwFPOutput)){throw 'Fresh simple report name required'}
$mwFPVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwFPLLVM=Join-Path $mwFPWorkspace 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwFPRemill=Join-Path $mwFPWorkspace 'local/tools/remill-v6.0.1/remill-6.0.1/include'
$mwFPExtraction=Join-Path $mwFPWorkspace 'reports/m4-fp-startup/research-r1'
$mwFPCandidate=Join-Path $mwFPWorkspace 'reports/m4-fp-native/first-host-r1'
$mwFPCMake=Join-Path $mwFPVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$mwFPNinja=Join-Path $mwFPVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
function Hash-MWFP([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
if((Hash-MWFP (Join-Path $mwFPCandidate 'host.ll')) -ne '564f22610d368ce8ae6b40283cc93668f7394ac30674d9051e784a9ad1a723b5'){throw 'Exact strict first host candidate required'}
$mwFPSources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-Item -LiteralPath (Join-Path $mwFPExtraction 'probe_spec.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwFPWorkspace 'runtime/memory/guest_memory.cpp'))+@(Get-Item -LiteralPath (Join-Path $mwFPWorkspace 'runtime/memory/guest_memory.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwFPWorkspace 'runtime/core/guest_address.hpp'))+@(Get-ChildItem -LiteralPath (Join-Path $mwFPRemill 'remill/Arch/Runtime') -Filter '*.h')+@(Get-ChildItem -LiteralPath (Join-Path $mwFPRemill 'remill/Arch/X86/Runtime') -Filter '*.h')
$mwFPIdentity=[ordered]@{};foreach($source in $mwFPSources){$mwFPIdentity[$source.FullName]=Hash-MWFP $source.FullName}
New-Item -ItemType Directory -Path $mwFPOutput|Out-Null
foreach($source in $mwFPSources){$relative=[IO.Path]::GetRelativePath($mwFPWorkspace,$source.FullName);$target=Join-Path $mwFPOutput "sources/$relative";New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force|Out-Null;Copy-Item -LiteralPath $source.FullName -Destination $target}
$mwFPCommands=[Collections.Generic.List[object]]::new();$mwFPBuilds=[Collections.Generic.List[string]]::new();$mwFPPassed=$false
function Run-MWFP([string]$Program,[string[]]$Arguments,[string]$Log){
    [IO.File]::WriteAllText($Log,'')
    $saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try {& $Program @Arguments 2>&1|Tee-Object -FilePath $Log;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$saved}
    $mwFPCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$code;log=$Log;log_sha256=(Hash-MWFP $Log)})
    if($code -ne 0){throw "FP experiment command failed: $Program exit=$code"}
}
try{
    Import-Module (Join-Path $mwFPVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $mwFPVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    Run-MWFP (Join-Path $mwFPLLVM 'opt.exe') @('-passes=verify','-S',(Join-Path $mwFPCandidate 'host.ll'),'-o',(Join-Path $mwFPOutput 'verified.ll')) (Join-Path $mwFPOutput 'verify.log')
    Run-MWFP (Join-Path $mwFPLLVM 'opt.exe') @('-passes=default<O2>,verify','-S',(Join-Path $mwFPOutput 'verified.ll'),'-o',(Join-Path $mwFPOutput 'optimized.ll')) (Join-Path $mwFPOutput 'optimize.log')
    foreach($level in @('O0','O2')){
        $object=Join-Path $mwFPOutput "first-$level.obj";$ir=if($level -eq 'O0'){Join-Path $mwFPOutput 'verified.ll'}else{Join-Path $mwFPOutput 'optimized.ll'}
        Run-MWFP (Join-Path $mwFPLLVM 'llc.exe') @('-filetype=obj',"-$level",$ir,'-o',$object) (Join-Path $mwFPOutput "llc-$level.log")
        $build=Join-Path $mwFPWorkspace "build/m4-fp-native-$mwFPName-$level";if(Test-Path -LiteralPath $build){throw 'Fresh native build required'};$mwFPBuilds.Add($build)
        Run-MWFP $mwFPCMake @('-S',$PSScriptRoot,'-B',$build,'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$mwFPNinja",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$(Join-Path $mwFPLLVM 'clang-cl.exe')","-DMW34_HOST_OBJECT=$object","-DMW34_PROBE_INCLUDE=$mwFPExtraction","-DMW34_REMILL_INCLUDE=$mwFPRemill") (Join-Path $mwFPOutput "configure-$level.log")
        Run-MWFP $mwFPCMake @('--build',$build,'--verbose') (Join-Path $mwFPOutput "build-$level.log")
        $worker=Join-Path $build 'mw34_m4_fp_native_first.exe'
        Run-MWFP $worker @('--layout') (Join-Path $mwFPOutput "layout-$level.json")
        Run-MWFP $worker @('--check-context',(Join-Path $mwFPExtraction 'pages.bin'),(Join-Path $mwFPWorkspace 'MW3/Mech3.exe')) (Join-Path $mwFPOutput "controls-$level.log")
        Run-MWFP $worker @((Join-Path $mwFPExtraction 'pages.bin'),(Join-Path $mwFPWorkspace 'MW3/Mech3.exe'),(Join-Path $mwFPOutput "native-$level.bin")) (Join-Path $mwFPOutput "execute-$level.log")
    }
    foreach($source in $mwFPSources){if((Hash-MWFP $source.FullName) -ne $mwFPIdentity[$source.FullName]){throw 'Sources changed during FP experiment'}}
    $mwFPPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwFPOutput 'failure.txt');throw}
finally{
    $bindings=[ordered]@{};foreach($source in $mwFPSources){$bindings[$source.FullName]=$mwFPIdentity[$source.FullName]}
    foreach($folder in @($mwFPOutput,$mwFPCandidate,$mwFPExtraction)+$mwFPBuilds){if(Test-Path -LiteralPath $folder){foreach($file in Get-ChildItem -LiteralPath $folder -Recurse -File){$bindings[$file.FullName]=Hash-MWFP $file.FullName}}}
    foreach($tool in @($mwFPCMake,$mwFPNinja,(Join-Path $mwFPVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwFPLLVM 'clang-cl.exe'),(Join-Path $mwFPLLVM 'llc.exe'),(Join-Path $mwFPLLVM 'opt.exe'),(Get-Command link.exe -ErrorAction SilentlyContinue).Source,(Get-Command rc.exe -ErrorAction SilentlyContinue).Source,(Get-Command mt.exe -ErrorAction SilentlyContinue).Source)){if($tool){$bindings[$tool]=Hash-MWFP $tool}}
    [ordered]@{passed=$mwFPPassed;scope='Actual first compiled FP observations; no equivalence acceptance';sources=$mwFPIdentity;commands=$mwFPCommands;bindings=$bindings}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwFPOutput 'build.json')
}
