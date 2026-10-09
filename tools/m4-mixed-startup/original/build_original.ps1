param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'));$mwOut=[IO.Path]::GetFullPath($OutputDirectory);$mwName=Split-Path $mwOut -Leaf
$mwPrivate=Join-Path $mwRoot 'reports/m4-mixed-startup'
if([IO.Path]::GetDirectoryName($mwOut)-ne $mwPrivate -or $mwName -notmatch '^original-[a-z0-9-]+$'){throw 'Assigned fresh original output required'}
$mwExtract=Join-Path $mwPrivate "original-extract-$mwName";$mwBuild=Join-Path $mwRoot "build/m4-mixed-startup-$mwName-x86"
foreach($mwPath in @($mwOut,$mwExtract,$mwBuild)){if(Test-Path -LiteralPath $mwPath){throw 'Existing report/extraction/build directory rejected before mutation'}}
$mwPython='C:/Python314/python.exe';$mwVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwCMake=Join-Path $mwVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
function Hash-MW([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwSources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-Item -LiteralPath (Join-Path $mwRoot 'tools/analysis/pe.py'))
$mwSourceIDs=[ordered]@{};foreach($mwSource in $mwSources){$mwSourceIDs[$mwSource.FullName]=Hash-MW $mwSource.FullName}
New-Item -ItemType Directory -Path $mwOut|Out-Null
foreach($mwSource in $mwSources){$mwTarget=Join-Path $mwOut ('sources/'+[IO.Path]::GetRelativePath($mwRoot,$mwSource.FullName));New-Item -ItemType Directory -Path (Split-Path $mwTarget -Parent) -Force|Out-Null;Copy-Item -LiteralPath $mwSource.FullName -Destination $mwTarget}
$mwCommands=[Collections.Generic.List[object]]::new();$mwToolPaths=[Collections.Generic.List[string]]::new();$mwPassed=$false
function Run-MW([string]$p,[string[]]$Arguments,[string]$Log){
    [IO.File]::WriteAllText($Log,'');$mwPreference=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try{& $p @Arguments 2>&1|Tee-Object -FilePath $Log;$mwExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwPreference}
    $mwCommands.Add([ordered]@{program=$p;arguments=$Arguments;exit_code=$mwExit;log=$Log;log_sha256=(Hash-MW $Log)})
    if($mwExit-ne 0){throw "Connected original tool failed: $p exit=$mwExit"}
}
try{
    Run-MW $mwPython @((Join-Path $PSScriptRoot 'extract.py'),$mwExtract) (Join-Path $mwOut 'extraction.log')
    $mwGenerated=Join-Path $mwExtract 'spec.hpp';$mwSourceIDs[$mwGenerated]=Hash-MW $mwGenerated
    $mwTarget=Join-Path $mwOut ('sources/'+[IO.Path]::GetRelativePath($mwRoot,$mwGenerated));New-Item -ItemType Directory -Path (Split-Path $mwTarget -Parent) -Force|Out-Null;Copy-Item -LiteralPath $mwGenerated -Destination $mwTarget
    Import-Module (Join-Path $mwVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $mwVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
    Run-MW $mwCMake @('-S',$PSScriptRoot,'-B',$mwBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_ORIGINAL_INCLUDE=$mwExtract") (Join-Path $mwOut 'configure.log')
    Run-MW $mwCMake @('--build',$mwBuild,'--config','Release','--verbose') (Join-Path $mwOut 'compile.log')
    foreach($mwTool in @('cl.exe','ml.exe','link.exe')){$mwToolPaths.Add((Get-Command $mwTool).Source)}
    $mwWorker=Join-Path $mwBuild 'Release/mw34_m4_mixed_original.exe'
    Run-MW $mwWorker @('--check-protocol') (Join-Path $mwOut 'protocol-controls.log')
    Run-MW $mwWorker @('--check-publication',(Join-Path $mwOut 'publisher-fixtures')) (Join-Path $mwOut 'publisher-controls.log')
    foreach($mwPair in $mwSourceIDs.GetEnumerator()){if((Hash-MW $mwPair.Key)-ne $mwPair.Value){throw 'Sources changed during original compilation'}}
    $mwPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $mwOut 'failure.txt');throw}
finally{
    $mwBindings=[ordered]@{};foreach($mwPair in $mwSourceIDs.GetEnumerator()){$mwBindings[$mwPair.Key]=$mwPair.Value}
    $mwInventory=Get-Content -LiteralPath (Join-Path $mwRoot 'reports/m4-initializer-inventory/r1/pins.json') -Raw|ConvertFrom-Json
    foreach($mwItem in $mwInventory.bindings){$mwBindings[$mwItem.path]=$mwItem.sha256}
    foreach($mwFolder in @($mwOut,$mwExtract,$mwBuild)){if(Test-Path -LiteralPath $mwFolder){foreach($mwFile in Get-ChildItem -LiteralPath $mwFolder -Recurse -File){$mwBindings[$mwFile.FullName]=Hash-MW $mwFile.FullName}}}
    foreach($mwTool in @($mwPython,$mwCMake,(Join-Path $mwVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path)+@($mwToolPaths)){if($mwTool){$mwBindings[$mwTool]=Hash-MW $mwTool}}
    foreach($mwDep in @('reports/m4-initializer-inventory/r1/pins.json','docs/m2-floating-point-policy.md','tools/m4-fp-startup/reference.cpp','tools/m4-fp-startup/reference_x86.asm','tools/m4-fp-startup/original_broker.hpp')){$mwPath=Join-Path $mwRoot $mwDep;$mwBindings[$mwPath]=Hash-MW $mwPath}
    [ordered]@{schema_version=1;passed=$mwPassed;scope='Original-only selected26 connected default-input hardware observation; no native or full-ledger acceptance';sources=$mwSourceIDs;commands=$mwCommands;bindings=$mwBindings;build=$mwBuild;extraction=$mwExtract;worker=(Join-Path $mwBuild 'Release/mw34_m4_mixed_original.exe');pack=(Join-Path $mwExtract 'pages.bin');image=(Join-Path $mwRoot 'MW3/Mech3.exe');sequence_count=48;phases=1248;record_size=92388;framing_esp=0x20001800;return_pc=0x410a80;records_header='MW4MXO01'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $mwOut 'build.json')
}
