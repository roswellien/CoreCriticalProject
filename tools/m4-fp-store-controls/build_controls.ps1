param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwCtlRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$mwCtlOut=[IO.Path]::GetFullPath($OutputDirectory);$mwCtlName=Split-Path $mwCtlOut -Leaf
if(-not $mwCtlOut.StartsWith((Join-Path $mwCtlRoot 'reports/m4-fp-store-controls')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $mwCtlName -notmatch '^[a-z0-9-]+$' -or (Test-Path -LiteralPath $mwCtlOut)){throw 'Fresh private controls path required'}
$mwCtlVS='C:/Program Files/Microsoft Visual Studio/18/Community';$mwCtlLLVM=Join-Path $mwCtlRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwCtlCMake=Join-Path $mwCtlVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$mwCtlNinja=Join-Path $mwCtlVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$mwCtlPrior=Join-Path $mwCtlRoot 'reports/m4-fp-store-repair/accumulated-r1';$mwCtlProbe=Join-Path $mwCtlRoot 'reports/m4-fp-startup/research-r1';$mwCtlRemill=Join-Path $mwCtlRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'
function Hash-MWCtl([string]$path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
$prior=Get-Content -LiteralPath (Join-Path $mwCtlPrior 'build.json') -Raw|ConvertFrom-Json;if(-not $prior.passed){throw 'Complete repaired build required'}
foreach($b in $prior.bindings.PSObject.Properties){if((Hash-MWCtl $b.Name) -ne $b.Value){throw "Repaired dependency changed: $($b.Name)"}}
$sources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File);$identities=[ordered]@{};New-Item -ItemType Directory -Path $mwCtlOut|Out-Null
foreach($s in $sources){$identities[$s.FullName]=Hash-MWCtl $s.FullName;Copy-Item -LiteralPath $s.FullName -Destination (Join-Path $mwCtlOut $s.Name)}
$commands=[Collections.Generic.List[object]]::new();$builds=[Collections.Generic.List[string]]::new();$passed=$false
function Run-MWCtl([string]$program,[string[]]$Arguments,[string]$log){
    [IO.File]::WriteAllText($log,'');$saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try{& $program @Arguments 2>&1|Tee-Object -FilePath $log;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$saved}
    $commands.Add([ordered]@{program=$program;arguments=$Arguments;exit_code=$code;log=$log;log_sha256=(Hash-MWCtl $log)})
    if($code -ne 0){throw "Control command failed: $program exit=$code"}
}
try{
    Import-Module (Join-Path $mwCtlVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $mwCtlVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    foreach($level in @('O0','O2')){
        $build=Join-Path $mwCtlRoot "build/m4-fp-store-controls-$mwCtlName-$level";if(Test-Path -LiteralPath $build){throw 'Fresh control build required'};$builds.Add($build)
        Run-MWCtl $mwCtlCMake @('-S',$PSScriptRoot,'-B',$build,'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$mwCtlNinja",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$(Join-Path $mwCtlLLVM 'clang-cl.exe')","-DMW34_HOST_OBJECT=$(Join-Path $mwCtlPrior "first-$level.obj")","-DMW34_PROBE_INCLUDE=$mwCtlProbe","-DMW34_REMILL_INCLUDE=$mwCtlRemill") (Join-Path $mwCtlOut "configure-$level.log")
        Run-MWCtl $mwCtlCMake @('--build',$build,'--verbose') (Join-Path $mwCtlOut "build-$level.log")
        Run-MWCtl (Join-Path $build 'mw34_m4_fp_store_controls.exe') @((Join-Path $mwCtlProbe 'pages.bin'),(Join-Path $mwCtlRoot 'MW3/Mech3.exe')) (Join-Path $mwCtlOut "controls-$level.log")
    }
    foreach($s in $sources){if((Hash-MWCtl $s.FullName) -ne $identities[$s.FullName]){throw 'Control source changed'}};$passed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwCtlOut 'failure.txt');throw}
finally{
    $bindings=[ordered]@{};foreach($b in $prior.bindings.PSObject.Properties){$bindings[$b.Name]=$b.Value};$bindings[(Join-Path $mwCtlPrior 'build.json')]=Hash-MWCtl (Join-Path $mwCtlPrior 'build.json')
    foreach($s in $sources){$bindings[$s.FullName]=$identities[$s.FullName]};foreach($folder in @($mwCtlOut)+$builds){if(Test-Path -LiteralPath $folder){foreach($f in Get-ChildItem -LiteralPath $folder -Recurse -File){$bindings[$f.FullName]=Hash-MWCtl $f.FullName}}}
    foreach($t in @($mwCtlCMake,$mwCtlNinja,(Join-Path $mwCtlVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwCtlLLVM 'clang-cl.exe'),(Join-Path $mwCtlLLVM 'lld-link.exe'),(Join-Path $mwCtlLLVM 'llvm-mt.exe'))){$bindings[$t]=Hash-MWCtl $t}
    [ordered]@{passed=$passed;scope='Actual repaired compiled context/permission/return controls at both optimization levels';sources=$identities;commands=$commands;bindings=$bindings}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwCtlOut 'build.json')
}
