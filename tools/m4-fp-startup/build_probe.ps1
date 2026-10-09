param(
    [Parameter(Mandatory=$true)][string]$ExtractionDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$VSRoot='C:/Program Files/Microsoft Visual Studio/18/Community'
)
$ErrorActionPreference='Stop'
$mwFPWorkspace=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwFPExtraction=(Resolve-Path -LiteralPath $ExtractionDirectory).Path
$mwFPOutput=[System.IO.Path]::GetFullPath($OutputDirectory)
$mwFPAllowed=[System.IO.Path]::GetFullPath((Join-Path $mwFPWorkspace 'reports/m4-fp-startup'))+[System.IO.Path]::DirectorySeparatorChar
if (-not $mwFPOutput.StartsWith($mwFPAllowed,[System.StringComparison]::OrdinalIgnoreCase)) { throw 'Private probe report path required' }
$mwFPName=Split-Path $mwFPOutput -Leaf
if ($mwFPName -notmatch '^[a-z0-9-]+$') { throw 'Simple fresh probe name required' }
$mwFPBuild=Join-Path $mwFPWorkspace "build/m4-fp-startup-$mwFPName"
if ((Test-Path -LiteralPath $mwFPOutput) -or (Test-Path -LiteralPath $mwFPBuild)) { throw 'Fresh report and build paths required' }
function Get-MWFPHash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
$mwFPSources=@(Get-ChildItem -LiteralPath $PSScriptRoot -File)+@(Get-Item -LiteralPath (Join-Path $mwFPExtraction 'probe_spec.hpp'))
$mwFPIdentity=[ordered]@{}
foreach ($mwFPSource in $mwFPSources) {$mwFPIdentity[$mwFPSource.FullName]=Get-MWFPHash $mwFPSource.FullName}
New-Item -ItemType Directory -Path $mwFPOutput | Out-Null
$mwFPSnapshot=Join-Path $mwFPOutput 'sources';New-Item -ItemType Directory -Path $mwFPSnapshot | Out-Null
foreach ($mwFPSource in $mwFPSources) {Copy-Item -LiteralPath $mwFPSource.FullName -Destination (Join-Path $mwFPSnapshot $mwFPSource.Name)}
$mwFPCommands=[System.Collections.Generic.List[object]]::new()
function Invoke-MWFP([string]$Program,[string[]]$Arguments,[string]$Log) {
    $mwFPSaved=$ErrorActionPreference;$ErrorActionPreference='Continue'
    try {& $Program @Arguments 2>&1 | Tee-Object -FilePath $Log;$mwFPExit=$LASTEXITCODE}
    finally {$ErrorActionPreference=$mwFPSaved}
    $mwFPCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwFPExit;log_path=$Log;log_sha256=(Get-MWFPHash $Log)})
    if ($mwFPExit -ne 0) {throw "Probe tool failed: $Program exit=$mwFPExit"}
}
$mwFPPassed=$false
try {
    Import-Module (Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64' | Out-Null
    $mwFPCMake=Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
    Invoke-MWFP $mwFPCMake @('-S',$PSScriptRoot,'-B',$mwFPBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_PROBE_INCLUDE=$mwFPExtraction") (Join-Path $mwFPOutput 'configure.log')
    Invoke-MWFP $mwFPCMake @('--build',$mwFPBuild,'--config','Release','--verbose') (Join-Path $mwFPOutput 'build.log')
    $mwFPWorker=Join-Path $mwFPBuild 'Release/mw34_m4_fp_reference.exe'
    Invoke-MWFP $mwFPWorker @('--check-hash') (Join-Path $mwFPOutput 'hash-controls.log')
    foreach ($mwFPSource in $mwFPSources) {if ((Get-MWFPHash $mwFPSource.FullName) -ne $mwFPIdentity[$mwFPSource.FullName]) {throw 'Probe sources changed during build'}}
    $mwFPPassed=$true
} catch {$_ | Out-String | Set-Content -LiteralPath (Join-Path $mwFPOutput 'failure.txt');throw}
finally {
    $mwFPBindings=[ordered]@{}
    foreach($mwFPSource in $mwFPSources) {$mwFPBindings[$mwFPSource.FullName]=$mwFPIdentity[$mwFPSource.FullName]}
    foreach($mwFPFile in Get-ChildItem -LiteralPath $mwFPOutput -Recurse -File) {$mwFPBindings[$mwFPFile.FullName]=Get-MWFPHash $mwFPFile.FullName}
    foreach($mwFPFile in Get-ChildItem -LiteralPath $mwFPExtraction -Recurse -File) {$mwFPBindings[$mwFPFile.FullName]=Get-MWFPHash $mwFPFile.FullName}
    if(Test-Path -LiteralPath $mwFPBuild) {foreach($mwFPFile in Get-ChildItem -LiteralPath $mwFPBuild -Recurse -File) {if($mwFPFile.Extension -in @('.exe','.obj','.lib','.txt','.cmake','.vcxproj','.props')) {$mwFPBindings[$mwFPFile.FullName]=Get-MWFPHash $mwFPFile.FullName}}}
    foreach($mwFPTool in @($mwFPCMake,(Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Command cl.exe -ErrorAction SilentlyContinue).Source,(Get-Command ml.exe -ErrorAction SilentlyContinue).Source,(Get-Command link.exe -ErrorAction SilentlyContinue).Source,(Join-Path $VSRoot 'MSBuild/Current/Bin/MSBuild.exe'))) {if($mwFPTool) {$mwFPBindings[$mwFPTool]=Get-MWFPHash $mwFPTool}}
    [ordered]@{scope='Original hardware research only; no native equivalence or full-startup acceptance';passed=$mwFPPassed;sources=$mwFPIdentity;commands=$mwFPCommands;bindings=$mwFPBindings;worker=$mwFPWorker} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $mwFPOutput 'build.json')
}
