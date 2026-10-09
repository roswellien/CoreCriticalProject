param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwCosWorkspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwCosOutput=[IO.Path]::GetFullPath($OutputDirectory)
$mwCosAllowed=(Join-Path $mwCosWorkspace 'reports/m4-fp-transcendental')+[IO.Path]::DirectorySeparatorChar
if(-not $mwCosOutput.StartsWith($mwCosAllowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Private fresh FP report path required'}
$mwCosName=Split-Path $mwCosOutput -Leaf
if($mwCosName -notmatch '^[a-z0-9-]+$' -or (Test-Path -LiteralPath $mwCosOutput)){throw 'Fresh simple report name required'}
$mwCosVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwCosLLVM=Join-Path $mwCosWorkspace 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwCosRemill=Join-Path $mwCosWorkspace 'local/tools/remill-v6.0.1/remill-6.0.1/include'
$mwCosExtraction=Join-Path $mwCosWorkspace 'reports/m4-fp-startup/research-r1'
$mwCosCandidate=Join-Path $mwCosWorkspace 'reports/m4-fp-transcendental/cosine-host-r1'
$mwCosCMake=Join-Path $mwCosVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$mwCosNinja=Join-Path $mwCosVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
function Hash-MWCos([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwCosLiftPins=Join-Path $mwCosWorkspace 'reports/m4-fp-native/lift-r1/pins.json'
$mwCosLift=Get-Content -LiteralPath $mwCosLiftPins -Raw|ConvertFrom-Json
foreach($b in $mwCosLift.files.PSObject.Properties){if((Hash-MWCos $b.Name) -ne $b.Value){throw "Exact lift binding changed: $($b.Name)"}}
$mwCosAdapter=Get-Content -LiteralPath (Join-Path $mwCosCandidate 'adapter.json') -Raw|ConvertFrom-Json
if(-not $mwCosAdapter.passed -or $mwCosAdapter.records.Count -ne 4){throw 'Four complete host candidates required'}
foreach($b in $mwCosAdapter.bindings.PSObject.Properties){if((Hash-MWCos $b.Name) -ne $b.Value){throw "Exact adapter binding changed: $($b.Name)"}}
$mwCosSources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-Item -LiteralPath (Join-Path $mwCosWorkspace 'tools/m4-fp-native/adapt_first.py'))+@(Get-Item -LiteralPath (Join-Path $mwCosWorkspace 'tools/lifting/host_adapter.py'))+@(Get-Item -LiteralPath (Join-Path $mwCosExtraction 'probe_spec.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwCosWorkspace 'runtime/memory/guest_memory.cpp'))+@(Get-Item -LiteralPath (Join-Path $mwCosWorkspace 'runtime/memory/guest_memory.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwCosWorkspace 'runtime/core/guest_address.hpp'))+@(Get-ChildItem -LiteralPath (Join-Path $mwCosRemill 'remill/Arch/Runtime') -Filter '*.h')+@(Get-ChildItem -LiteralPath (Join-Path $mwCosRemill 'remill/Arch/X86/Runtime') -Filter '*.h')
$mwCosIdentity=[ordered]@{};foreach($source in $mwCosSources){$mwCosIdentity[$source.FullName]=Hash-MWCos $source.FullName}
New-Item -ItemType Directory -Path $mwCosOutput|Out-Null
foreach($source in $mwCosSources){$relative=[IO.Path]::GetRelativePath($mwCosWorkspace,$source.FullName);$target=Join-Path $mwCosOutput "sources/$relative";New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force|Out-Null;Copy-Item -LiteralPath $source.FullName -Destination $target}
$mwCosCommands=[Collections.Generic.List[object]]::new();$mwCosBuilds=[Collections.Generic.List[string]]::new();$mwCosPassed=$false
function Run-MWCos([string]$Program,[string[]]$Arguments,[string]$Log){
    [IO.File]::WriteAllText($Log,'')
    $saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try {& $Program @Arguments 2>&1|Tee-Object -FilePath $Log;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$saved}
    $mwCosCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$code;log=$Log;log_sha256=(Hash-MWCos $Log)})
    if($code -ne 0){throw "FP experiment command failed: $Program exit=$code"}
}
try{
    Import-Module (Join-Path $mwCosVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $mwCosVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    foreach($stem in @('4ce5a0','4ce5c0','4ce5e0','4ce600')){
        Run-MWCos (Join-Path $mwCosLLVM 'opt.exe') @('-passes=verify','-S',(Join-Path $mwCosCandidate "$stem.ll"),'-o',(Join-Path $mwCosOutput "$stem-verified.ll")) (Join-Path $mwCosOutput "$stem-verify.log")
        Run-MWCos (Join-Path $mwCosLLVM 'opt.exe') @('-passes=default<O2>,verify','-S',(Join-Path $mwCosOutput "$stem-verified.ll"),'-o',(Join-Path $mwCosOutput "$stem-optimized.ll")) (Join-Path $mwCosOutput "$stem-optimize.log")
    }
    foreach($level in @('O0','O2')){
        $mwCosObjects=[Collections.Generic.List[string]]::new()
        foreach($stem in @('4ce5a0','4ce5c0','4ce5e0','4ce600')){
            $object=Join-Path $mwCosOutput "$stem-$level.obj";$ir=if($level -eq 'O0'){Join-Path $mwCosOutput "$stem-verified.ll"}else{Join-Path $mwCosOutput "$stem-optimized.ll"}
            Run-MWCos (Join-Path $mwCosLLVM 'llc.exe') @('-filetype=obj',"-$level",$ir,'-o',$object) (Join-Path $mwCosOutput "$stem-llc-$level.log")
            $mwCosObjects.Add($object)
        }
        $build=Join-Path $mwCosWorkspace "build/m4-fp-cosine-$mwCosName-$level";if(Test-Path -LiteralPath $build){throw 'Fresh native build required'};$mwCosBuilds.Add($build)
        Run-MWCos $mwCosCMake @('-S',$PSScriptRoot,'-B',$build,'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$mwCosNinja",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$(Join-Path $mwCosLLVM 'clang-cl.exe')","-DMW34_HOST_OBJECTS=$($mwCosObjects -join ';')","-DMW34_PROBE_INCLUDE=$mwCosExtraction","-DMW34_REMILL_INCLUDE=$mwCosRemill") (Join-Path $mwCosOutput "configure-$level.log")
        Run-MWCos $mwCosCMake @('--build',$build,'--verbose') (Join-Path $mwCosOutput "build-$level.log")
        $worker=Join-Path $build 'mw34_m4_fp_cosine.exe'
        Run-MWCos $worker @('--layout') (Join-Path $mwCosOutput "layout-$level.json")
        Run-MWCos $worker @('--check-context',(Join-Path $mwCosExtraction 'pages.bin'),(Join-Path $mwCosWorkspace 'MW3/Mech3.exe')) (Join-Path $mwCosOutput "controls-$level.log")
        Run-MWCos $worker @((Join-Path $mwCosExtraction 'pages.bin'),(Join-Path $mwCosWorkspace 'MW3/Mech3.exe'),(Join-Path $mwCosOutput "native-$level.bin")) (Join-Path $mwCosOutput "execute-$level.log")
    }
    foreach($source in $mwCosSources){if((Hash-MWCos $source.FullName) -ne $mwCosIdentity[$source.FullName]){throw 'Sources changed during FP experiment'}}
    $mwCosPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwCosOutput 'failure.txt');throw}
finally{
    $bindings=[ordered]@{};foreach($source in $mwCosSources){$bindings[$source.FullName]=$mwCosIdentity[$source.FullName]}
    foreach($b in $mwCosLift.files.PSObject.Properties){$bindings[$b.Name]=$b.Value}
    $bindings[$mwCosLiftPins]=Hash-MWCos $mwCosLiftPins
    foreach($folder in @($mwCosOutput,$mwCosCandidate,$mwCosExtraction)+$mwCosBuilds){if(Test-Path -LiteralPath $folder){foreach($file in Get-ChildItem -LiteralPath $folder -Recurse -File){$bindings[$file.FullName]=Hash-MWCos $file.FullName}}}
    foreach($tool in @($mwCosCMake,$mwCosNinja,(Join-Path $mwCosVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwCosLLVM 'clang-cl.exe'),(Join-Path $mwCosLLVM 'llc.exe'),(Join-Path $mwCosLLVM 'opt.exe'),(Get-Command link.exe -ErrorAction SilentlyContinue).Source,(Get-Command rc.exe -ErrorAction SilentlyContinue).Source,(Get-Command mt.exe -ErrorAction SilentlyContinue).Source)){if($tool){$bindings[$tool]=Hash-MWCos $tool}}
    [ordered]@{passed=$mwCosPassed;scope='Actual four compiled cosine observations; no equivalence acceptance';sources=$mwCosIdentity;commands=$mwCosCommands;bindings=$bindings}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwCosOutput 'build.json')
}
