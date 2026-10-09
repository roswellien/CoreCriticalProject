param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwRepairRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$mwRepairOut=[IO.Path]::GetFullPath($OutputDirectory);$mwRepairName=Split-Path $mwRepairOut -Leaf
if(-not $mwRepairOut.StartsWith((Join-Path $mwRepairRoot 'reports/m4-fp-store-repair')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $mwRepairName -notmatch '^[a-z0-9-]+$' -or (Test-Path -LiteralPath $mwRepairOut)){throw 'Fresh private repair path required'}
$mwRepairVS='C:/Program Files/Microsoft Visual Studio/18/Community';$mwRepairLLVM=Join-Path $mwRepairRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwRepairRemill=Join-Path $mwRepairRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include';$mwRepairProbe=Join-Path $mwRepairRoot 'reports/m4-fp-startup/research-r1'
$mwRepairCMake=Join-Path $mwRepairVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$mwRepairNinja=Join-Path $mwRepairVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
function Hash-MWRepair([string]$path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
$ancestors=[ordered]@{}
foreach($relative in @('reports/m4-fp-native/first-native-r2/build.json','reports/m4-fp-directed/baseline-r3/build.json')){
    $path=Join-Path $mwRepairRoot $relative;$meta=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json;if(-not $meta.passed){throw 'Complete ancestor build required'}
    foreach($b in $meta.bindings.PSObject.Properties){$ancestors[$b.Name]=$b.Value};$ancestors[$path]=Hash-MWRepair $path
}
foreach($relative in @('reports/m4-fp-native/lift-r1/pins.json','reports/m4-fp-startup/run-r1/closure/pins.json')){
    $path=Join-Path $mwRepairRoot $relative;$meta=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
    foreach($b in $meta.files.PSObject.Properties){$ancestors[$b.Name]=$b.Value};$ancestors[$path]=Hash-MWRepair $path
}
foreach($b in $ancestors.GetEnumerator()){if((Hash-MWRepair $b.Key) -ne $b.Value){throw "Ancestor identity changed: $($b.Key)"}}
$sources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-ChildItem -LiteralPath (Join-Path $mwRepairRoot 'tools/m4-fp-directed') -File)+@(Get-ChildItem -LiteralPath (Join-Path $mwRepairRoot 'tools/m4-fp-native') -File)+@(Get-Item -LiteralPath (Join-Path $mwRepairRoot 'tools/lifting/host_adapter.py'))+@(Get-Item -LiteralPath (Join-Path $mwRepairProbe 'probe_spec.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwRepairRoot 'runtime/memory/guest_memory.cpp'))+@(Get-Item -LiteralPath (Join-Path $mwRepairRoot 'runtime/memory/guest_memory.hpp'))+@(Get-Item -LiteralPath (Join-Path $mwRepairRoot 'runtime/core/guest_address.hpp'))+@(Get-ChildItem -LiteralPath (Join-Path $mwRepairRemill 'remill/Arch/Runtime') -Filter '*.h')+@(Get-ChildItem -LiteralPath (Join-Path $mwRepairRemill 'remill/Arch/X86/Runtime') -Filter '*.h')
$identities=[ordered]@{};New-Item -ItemType Directory -Path $mwRepairOut|Out-Null
foreach($s in $sources){$identities[$s.FullName]=Hash-MWRepair $s.FullName;$target=Join-Path $mwRepairOut ('sources/'+[IO.Path]::GetRelativePath($mwRepairRoot,$s.FullName));New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force|Out-Null;Copy-Item -LiteralPath $s.FullName -Destination $target}
$commands=[Collections.Generic.List[object]]::new();$builds=[Collections.Generic.List[string]]::new();$passed=$false
function Run-MWRepair([string]$program,[string[]]$Arguments,[string]$log){
    [IO.File]::WriteAllText($log,'');$saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try{& $program @Arguments 2>&1|Tee-Object -FilePath $log;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$saved}
    $commands.Add([ordered]@{program=$program;arguments=$Arguments;exit_code=$code;log=$log;log_sha256=(Hash-MWRepair $log)})
    if($code -ne 0){throw "Repair command failed: $program exit=$code"}
}
try{
    Import-Module (Join-Path $mwRepairVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $mwRepairVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    Run-MWRepair 'C:/Python314/python.exe' @((Join-Path $PSScriptRoot 'repair_accumulated.py'),(Join-Path $mwRepairRoot 'reports/m4-fp-native/first-host-r1/host.ll'),(Join-Path $mwRepairOut 'repaired.ll'),(Join-Path $mwRepairOut 'repair.json')) (Join-Path $mwRepairOut 'repair.log')
    Run-MWRepair (Join-Path $mwRepairLLVM 'opt.exe') @('-passes=verify','-S',(Join-Path $mwRepairOut 'repaired.ll'),'-o',(Join-Path $mwRepairOut 'verified.ll')) (Join-Path $mwRepairOut 'verify.log')
    Run-MWRepair (Join-Path $mwRepairLLVM 'opt.exe') @('-passes=default<O2>,verify','-S',(Join-Path $mwRepairOut 'verified.ll'),'-o',(Join-Path $mwRepairOut 'optimized.ll')) (Join-Path $mwRepairOut 'optimize.log')
    foreach($level in @('O0','O2')){
        $ir=if($level -eq 'O0'){Join-Path $mwRepairOut 'verified.ll'}else{Join-Path $mwRepairOut 'optimized.ll'};$object=Join-Path $mwRepairOut "first-$level.obj"
        Run-MWRepair (Join-Path $mwRepairLLVM 'llc.exe') @('-filetype=obj',"-$level",$ir,'-o',$object) (Join-Path $mwRepairOut "llc-$level.log")
        $build=Join-Path $mwRepairRoot "build/m4-fp-store-repair-$mwRepairName-$level";if(Test-Path -LiteralPath $build){throw 'Fresh repaired build required'};$builds.Add($build)
        Run-MWRepair $mwRepairCMake @('-S',$PSScriptRoot,'-B',$build,'-G','Ninja',"-DCMAKE_MAKE_PROGRAM=$mwRepairNinja",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$(Join-Path $mwRepairLLVM 'clang-cl.exe')","-DMW34_HOST_OBJECT=$object","-DMW34_PROBE_INCLUDE=$mwRepairProbe","-DMW34_REMILL_INCLUDE=$mwRepairRemill") (Join-Path $mwRepairOut "configure-$level.log")
        Run-MWRepair $mwRepairCMake @('--build',$build,'--verbose') (Join-Path $mwRepairOut "build-$level.log")
        Run-MWRepair (Join-Path $build 'mw34_m4_fp_store_repair.exe') @((Join-Path $mwRepairProbe 'pages.bin'),(Join-Path $mwRepairRoot 'MW3/Mech3.exe'),(Join-Path $mwRepairOut "native-$level.bin")) (Join-Path $mwRepairOut "execute-$level.log")
    }
    foreach($s in $sources){if((Hash-MWRepair $s.FullName) -ne $identities[$s.FullName]){throw 'Repair sources changed'}};$passed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwRepairOut 'failure.txt');throw}
finally{
    $bindings=[ordered]@{};foreach($b in $ancestors.GetEnumerator()){$bindings[$b.Key]=$b.Value};foreach($s in $sources){$bindings[$s.FullName]=$identities[$s.FullName]}
    foreach($folder in @($mwRepairOut)+$builds){if(Test-Path -LiteralPath $folder){foreach($f in Get-ChildItem -LiteralPath $folder -Recurse -File){$bindings[$f.FullName]=Hash-MWRepair $f.FullName}}}
    foreach($t in @($mwRepairCMake,$mwRepairNinja,(Join-Path $mwRepairVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwRepairLLVM 'clang-cl.exe'),(Join-Path $mwRepairLLVM 'lld-link.exe'),(Join-Path $mwRepairLLVM 'llvm-mt.exe'),(Join-Path $mwRepairLLVM 'llc.exe'),(Join-Path $mwRepairLLVM 'opt.exe'),(Join-Path $mwRepairLLVM 'LLVM-C.dll'),'C:/Python314/python.exe',(Get-Command rc.exe).Source)){ $bindings[$t]=Hash-MWRepair $t }
    [ordered]@{passed=$passed;scope='Actual directed first FP static store-status repair observations; equivalence and admission are separate';sources=$identities;commands=$commands;bindings=$bindings}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwRepairOut 'build.json')
}
