param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwDirRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwDirOut=[IO.Path]::GetFullPath($OutputDirectory);$mwDirName=Split-Path $mwDirOut -Leaf
if(-not $mwDirOut.StartsWith((Join-Path $mwDirRoot 'reports/m4-fp-directed')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $mwDirName -notmatch '^[a-z0-9-]+$' -or (Test-Path -LiteralPath $mwDirOut)){throw 'Fresh private directed report path required'}
$mwDirVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwDirLLVM=Join-Path $mwDirRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwDirRemill=Join-Path $mwDirRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'
$mwDirProbe=Join-Path $mwDirRoot 'reports/m4-fp-startup/research-r1'
$mwDirPrior=Join-Path $mwDirRoot 'reports/m4-fp-native/first-native-r2'
$mwDirCMake=Join-Path $mwDirVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$mwDirNinja=Join-Path $mwDirVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
function Hash-MWDir([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$prior=Get-Content -LiteralPath (Join-Path $mwDirPrior 'build.json') -Raw|ConvertFrom-Json
if(-not $prior.passed){throw 'Completed first actual native build required'}
foreach($binding in $prior.bindings.PSObject.Properties){if((Hash-MWDir $binding.Name) -ne $binding.Value){throw "Prior candidate binding changed: $($binding.Name)"}}
$sources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-Item -LiteralPath (Join-Path $mwDirRoot 'tools/m4-fp-native/native_first.cpp'))+@(Get-ChildItem -LiteralPath (Join-Path $mwDirRoot 'tools/m4-fp-startup') -File)+@(Get-Item -LiteralPath (Join-Path $mwDirProbe 'probe_spec.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwDirRoot 'runtime/memory/guest_memory.cpp'))+@(Get-Item -LiteralPath (Join-Path $mwDirRoot 'runtime/memory/guest_memory.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwDirRoot 'runtime/core/guest_address.hpp'))+@(Get-ChildItem -LiteralPath (Join-Path $mwDirRemill 'remill/Arch/Runtime') -Filter '*.h')+@(Get-ChildItem -LiteralPath (Join-Path $mwDirRemill 'remill/Arch/X86/Runtime') -Filter '*.h')
$identities=[ordered]@{};New-Item -ItemType Directory -Path $mwDirOut|Out-Null
foreach($s in $sources){$identities[$s.FullName]=Hash-MWDir $s.FullName;$target=Join-Path $mwDirOut ('sources/'+[IO.Path]::GetRelativePath($mwDirRoot,$s.FullName));New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force|Out-Null;Copy-Item -LiteralPath $s.FullName -Destination $target}
$commands=[Collections.Generic.List[object]]::new();$builds=[Collections.Generic.List[string]]::new();$tools=[Collections.Generic.List[string]]::new();$passed=$false
function Run-MWDir([string]$p,[string[]]$Arguments,[string]$log){
    [IO.File]::WriteAllText($log,'');$saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try{& $p @Arguments 2>&1|Tee-Object -FilePath $log;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$saved}
    $commands.Add([ordered]@{program=$p;arguments=$Arguments;exit_code=$code;log=$log;log_sha256=(Hash-MWDir $log)})
    if($code -ne 0){throw "Directed command failed: $p exit=$code"}
}
try{
    Import-Module (Join-Path $mwDirVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $mwDirVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
    $originalBuild=Join-Path $mwDirRoot "build/m4-fp-directed-$mwDirName-x86";if(Test-Path -LiteralPath $originalBuild){throw 'Fresh original build required'};$builds.Add($originalBuild)
    Run-MWDir $mwDirCMake @('-S',$PSScriptRoot,'-B',$originalBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_PROBE_INCLUDE=$mwDirProbe") (Join-Path $mwDirOut 'configure-x86.log')
    Run-MWDir $mwDirCMake @('--build',$originalBuild,'--config','Release','--verbose') (Join-Path $mwDirOut 'build-x86.log')
    foreach($t in @('cl.exe','ml.exe','link.exe')){$tools.Add((Get-Command $t).Source)}
    Enter-VsDevShell -VsInstallPath $mwDirVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    foreach($level in @('O0','O2')){
        $build=Join-Path $mwDirRoot "build/m4-fp-directed-$mwDirName-$level";if(Test-Path -LiteralPath $build){throw 'Fresh native build required'};$builds.Add($build)
        Run-MWDir $mwDirCMake @('-S',$PSScriptRoot,'-B',$build,'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$mwDirNinja",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$(Join-Path $mwDirLLVM 'clang-cl.exe')","-DMW34_HOST_OBJECT=$(Join-Path $mwDirPrior "first-$level.obj")","-DMW34_PROBE_INCLUDE=$mwDirProbe","-DMW34_REMILL_INCLUDE=$mwDirRemill") (Join-Path $mwDirOut "configure-$level.log")
        Run-MWDir $mwDirCMake @('--build',$build,'--verbose') (Join-Path $mwDirOut "build-$level.log")
        Run-MWDir (Join-Path $build 'mw34_m4_fp_directed_native.exe') @((Join-Path $mwDirProbe 'pages.bin'),(Join-Path $mwDirRoot 'MW3/Mech3.exe'),(Join-Path $mwDirOut "native-$level.bin")) (Join-Path $mwDirOut "execute-$level.log")
    }
    foreach($s in $sources){if((Hash-MWDir $s.FullName) -ne $identities[$s.FullName]){throw 'Directed sources changed'}};$passed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwDirOut 'failure.txt');throw}
finally{
    $bindings=[ordered]@{};foreach($s in $sources){$bindings[$s.FullName]=$identities[$s.FullName]}
    foreach($b in $prior.bindings.PSObject.Properties){$bindings[$b.Name]=$b.Value};$bindings[(Join-Path $mwDirPrior 'build.json')]=Hash-MWDir (Join-Path $mwDirPrior 'build.json')
    foreach($dir in @($mwDirOut)+$builds){if(Test-Path -LiteralPath $dir){foreach($f in Get-ChildItem -LiteralPath $dir -Recurse -File){$bindings[$f.FullName]=Hash-MWDir $f.FullName}}}
    foreach($t in @($mwDirCMake,$mwDirNinja,(Join-Path $mwDirVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwDirLLVM 'clang-cl.exe'),(Join-Path $mwDirLLVM 'lld-link.exe'),(Join-Path $mwDirLLVM 'llvm-mt.exe'))+$tools){$bindings[$t]=Hash-MWDir $t}
    [ordered]@{passed=$passed;scope='Directed static native observations; original worker built but not executed by this recipe';sources=$identities;commands=$commands;bindings=$bindings;original_worker=(Join-Path $originalBuild 'Release/mw34_m4_fp_directed_reference.exe')}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwDirOut 'build.json')
}
