param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwCosDirRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwCosDirOut=[IO.Path]::GetFullPath($OutputDirectory);$mwCosDirName=Split-Path $mwCosDirOut -Leaf
if(-not $mwCosDirOut.StartsWith((Join-Path $mwCosDirRoot 'reports/m4-fp-transcendental')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $mwCosDirName -notmatch '^[a-z0-9-]+$' -or (Test-Path -LiteralPath $mwCosDirOut)){throw 'Fresh private directed report path required'}
$mwCosDirVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwCosDirLLVM=Join-Path $mwCosDirRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwCosDirRemill=Join-Path $mwCosDirRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'
$mwCosDirProbe=Join-Path $mwCosDirRoot 'reports/m4-fp-startup/research-r1'
$mwCosDirPrior=Join-Path $mwCosDirRoot 'reports/m4-fp-transcendental/cosine-baseline-r1'
$mwCosDirCMake=Join-Path $mwCosDirVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$mwCosDirNinja=Join-Path $mwCosDirVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
function Hash-MWCosDir([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$prior=Get-Content -LiteralPath (Join-Path $mwCosDirPrior 'build.json') -Raw|ConvertFrom-Json
if(-not $prior.passed){throw 'Completed first actual native build required'}
foreach($binding in $prior.bindings.PSObject.Properties){if((Hash-MWCosDir $binding.Name) -ne $binding.Value){throw "Prior candidate binding changed: $($binding.Name)"}}
$sources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File -Recurse)+@(Get-ChildItem -LiteralPath (Join-Path $mwCosDirRoot 'tools/m4-fp-startup') -File)+@(Get-Item -LiteralPath (Join-Path $mwCosDirProbe 'probe_spec.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwCosDirRoot 'runtime/memory/guest_memory.cpp'))+@(Get-Item -LiteralPath (Join-Path $mwCosDirRoot 'runtime/memory/guest_memory.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwCosDirRoot 'runtime/core/guest_address.hpp'))+@(Get-ChildItem -LiteralPath (Join-Path $mwCosDirRemill 'remill/Arch/Runtime') -Filter '*.h')+@(Get-ChildItem -LiteralPath (Join-Path $mwCosDirRemill 'remill/Arch/X86/Runtime') -Filter '*.h')
$identities=[ordered]@{};New-Item -ItemType Directory -Path $mwCosDirOut|Out-Null
foreach($s in $sources){$identities[$s.FullName]=Hash-MWCosDir $s.FullName;$target=Join-Path $mwCosDirOut ('sources/'+[IO.Path]::GetRelativePath($mwCosDirRoot,$s.FullName));New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force|Out-Null;Copy-Item -LiteralPath $s.FullName -Destination $target}
$commands=[Collections.Generic.List[object]]::new();$builds=[Collections.Generic.List[string]]::new();$tools=[Collections.Generic.List[string]]::new();$passed=$false
function Run-MWCosDir([string]$p,[string[]]$Arguments,[string]$log){
    [IO.File]::WriteAllText($log,'');$saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try{& $p @Arguments 2>&1|Tee-Object -FilePath $log;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$saved}
    $commands.Add([ordered]@{program=$p;arguments=$Arguments;exit_code=$code;log=$log;log_sha256=(Hash-MWCosDir $log)})
    if($code -ne 0){throw "Directed command failed: $p exit=$code"}
}
try{
    Import-Module (Join-Path $mwCosDirVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $mwCosDirVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
    $originalBuild=Join-Path $mwCosDirRoot "build/m4-fp-cosine-directed-$mwCosDirName-x86";if(Test-Path -LiteralPath $originalBuild){throw 'Fresh original build required'};$builds.Add($originalBuild)
    Run-MWCosDir $mwCosDirCMake @('-S',(Join-Path $PSScriptRoot 'directed'),'-B',$originalBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_PROBE_INCLUDE=$mwCosDirProbe") (Join-Path $mwCosDirOut 'configure-x86.log')
    Run-MWCosDir $mwCosDirCMake @('--build',$originalBuild,'--config','Release','--verbose') (Join-Path $mwCosDirOut 'build-x86.log')
    foreach($t in @('cl.exe','ml.exe','link.exe')){$tools.Add((Get-Command $t).Source)}
    Enter-VsDevShell -VsInstallPath $mwCosDirVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    foreach($level in @('O0','O2')){
        $build=Join-Path $mwCosDirRoot "build/m4-fp-cosine-directed-$mwCosDirName-$level";if(Test-Path -LiteralPath $build){throw 'Fresh native build required'};$builds.Add($build)
        Run-MWCosDir $mwCosDirCMake @('-S',(Join-Path $PSScriptRoot 'directed'),'-B',$build,'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$mwCosDirNinja",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$(Join-Path $mwCosDirLLVM 'clang-cl.exe')","-DMW34_HOST_OBJECTS=$((@('4ce5a0','4ce5c0','4ce5e0','4ce600')|ForEach-Object {Join-Path $mwCosDirPrior "$_-$level.obj"}) -join ';')","-DMW34_PROBE_INCLUDE=$mwCosDirProbe","-DMW34_REMILL_INCLUDE=$mwCosDirRemill") (Join-Path $mwCosDirOut "configure-$level.log")
        Run-MWCosDir $mwCosDirCMake @('--build',$build,'--verbose') (Join-Path $mwCosDirOut "build-$level.log")
        Run-MWCosDir (Join-Path $build 'mw34_m4_fp_cosine_directed.exe') @((Join-Path $mwCosDirProbe 'pages.bin'),(Join-Path $mwCosDirRoot 'MW3/Mech3.exe'),(Join-Path $mwCosDirOut "native-$level.bin")) (Join-Path $mwCosDirOut "execute-$level.log")
    }
    foreach($s in $sources){if((Hash-MWCosDir $s.FullName) -ne $identities[$s.FullName]){throw 'Directed sources changed'}};$passed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwCosDirOut 'failure.txt');throw}
finally{
    $bindings=[ordered]@{};foreach($s in $sources){$bindings[$s.FullName]=$identities[$s.FullName]}
    foreach($b in $prior.bindings.PSObject.Properties){$bindings[$b.Name]=$b.Value};$bindings[(Join-Path $mwCosDirPrior 'build.json')]=Hash-MWCosDir (Join-Path $mwCosDirPrior 'build.json')
    foreach($dir in @($mwCosDirOut)+$builds){if(Test-Path -LiteralPath $dir){foreach($f in Get-ChildItem -LiteralPath $dir -Recurse -File){$bindings[$f.FullName]=Hash-MWCosDir $f.FullName}}}
    foreach($t in @($mwCosDirCMake,$mwCosDirNinja,(Join-Path $mwCosDirVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwCosDirLLVM 'clang-cl.exe'),(Join-Path $mwCosDirLLVM 'lld-link.exe'),(Join-Path $mwCosDirLLVM 'llvm-mt.exe'))+$tools){$bindings[$t]=Hash-MWCosDir $t}
    [ordered]@{passed=$passed;scope='Directed static native observations; original worker built but not executed by this recipe';sources=$identities;commands=$commands;bindings=$bindings;original_worker=(Join-Path $originalBuild 'Release/mw34_m4_fp_cosine_reference.exe')}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwCosDirOut 'build.json')
}
