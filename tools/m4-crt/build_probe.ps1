param([Parameter(Mandatory=$true)][string]$ExtractionDirectory,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use pwsh.exe for CRT evidence recipe'}
$mwProbeRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwProbeExtraction=(Resolve-Path -LiteralPath $ExtractionDirectory).Path
$mwProbeOut=[System.IO.Path]::GetFullPath($OutputDirectory)
$mwProbeAllowed=Join-Path $mwProbeRoot 'reports/m4-crt'
if(-not $mwProbeOut.StartsWith($mwProbeAllowed+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Private CRT output required'}
$mwProbeName=Split-Path $mwProbeOut -Leaf
if($mwProbeName -notmatch '^[a-z][a-z0-9-]{0,63}$'){throw 'Simple fresh CRT name required'}
$mwProbeBuild=Join-Path $mwProbeRoot "build/m4-crt-$mwProbeName"
if((Test-Path -LiteralPath $mwProbeOut) -or (Test-Path -LiteralPath $mwProbeBuild)){throw 'Fresh CRT report/build required'}
function Get-MWProbeHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwProbeInputs=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'original') -File)+@(Get-Item -LiteralPath $PSCommandPath,(Join-Path $PSScriptRoot 'probe_common.hpp'),(Join-Path $PSScriptRoot 'probe_io.hpp'),(Join-Path $PSScriptRoot 'prepare_probe.py'),(Join-Path $PSScriptRoot 'recover_provider.py'),(Join-Path $mwProbeExtraction 'probe_spec.hpp'))
$mwProbeSources=[ordered]@{};foreach($mwProbeFile in $mwProbeInputs){$mwProbeSources[$mwProbeFile.FullName]=Get-MWProbeHash $mwProbeFile.FullName}
New-Item -ItemType Directory -Path $mwProbeOut|Out-Null
$mwProbeCopies=[System.Collections.Generic.List[object]]::new()
foreach($mwProbeFile in $mwProbeInputs){$mwProbeCopy=Join-Path (Join-Path $mwProbeOut 'sources') ([System.IO.Path]::GetRelativePath($mwProbeRoot,$mwProbeFile.FullName));New-Item -ItemType Directory -Force -Path (Split-Path $mwProbeCopy)|Out-Null;Copy-Item -LiteralPath $mwProbeFile.FullName -Destination $mwProbeCopy;if((Get-MWProbeHash $mwProbeCopy) -ne $mwProbeSources[$mwProbeFile.FullName]){throw 'Literal probe source preservation failed'};$mwProbeCopies.Add([ordered]@{original_path=$mwProbeFile.FullName;preserved_path=$mwProbeCopy;sha256=$mwProbeSources[$mwProbeFile.FullName]})}
$mwProbeCommands=[System.Collections.Generic.List[object]]::new()
function Invoke-MWProbe([string]$Program,[string[]]$Arguments,[string]$Log){$mwProbeSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{& $Program @Arguments 2>&1|Tee-Object -FilePath $Log;$mwProbeExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwProbeSaved};$mwProbeCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwProbeExit;log_path=$Log;log_sha256=(Get-MWProbeHash $Log)});if($mwProbeExit -ne 0){throw "Original CRT build tool failed $Program exit=$mwProbeExit"}}
$mwProbeVS='C:/Program Files/Microsoft Visual Studio/18/Community';$mwProbePassed=$false;$mwProbeFailure=$null
try{
 Import-Module (Join-Path $mwProbeVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $mwProbeVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
 $mwProbeCMake=Join-Path $mwProbeVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
 Invoke-MWProbe $mwProbeCMake @('-S',(Join-Path $PSScriptRoot 'original'),'-B',$mwProbeBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_PROBE_INCLUDE=$mwProbeExtraction") (Join-Path $mwProbeOut 'configure.log')
 Invoke-MWProbe $mwProbeCMake @('--build',$mwProbeBuild,'--config','Release','--verbose') (Join-Path $mwProbeOut 'build.log')
 $mwProbeWorker=Join-Path $mwProbeBuild 'Release/mw34_m4_crt_reference.exe'
 Invoke-MWProbe $mwProbeWorker @('--check-hash') (Join-Path $mwProbeOut 'hash-controls.log')
 foreach($mwProbeFile in $mwProbeInputs){if((Get-MWProbeHash $mwProbeFile.FullName) -ne $mwProbeSources[$mwProbeFile.FullName]){throw 'Original CRT sources changed during build'}}
 $mwProbePassed=$true
}catch{$mwProbeFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $mwProbeOut 'failure.txt');throw}finally{
 $mwProbeArtifacts=[ordered]@{};foreach($mwProbeFile in @(Get-ChildItem -LiteralPath $mwProbeOut -Recurse -File;Get-ChildItem -LiteralPath $mwProbeExtraction -Recurse -File;if(Test-Path -LiteralPath $mwProbeBuild){Get-ChildItem -LiteralPath $mwProbeBuild -Recurse -File|Where-Object {$_.Extension -in @('.exe','.obj','.lib','.txt','.cmake','.vcxproj','.props','.xml','.json') -or $_.Name -eq 'rules.ninja'}})){$mwProbeArtifacts[$mwProbeFile.FullName]=Get-MWProbeHash $mwProbeFile.FullName}
 $mwProbeTools=[ordered]@{};foreach($mwProbeTool in @($mwProbeCMake,(Get-Process -Id $PID).Path,(Join-Path $mwProbeVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwProbeVS 'MSBuild/Current/Bin/MSBuild.exe'))+@('cl.exe','ml.exe','link.exe','rc.exe'|ForEach-Object {(Get-Command $_ -ErrorAction SilentlyContinue).Source})){if($mwProbeTool -and (Test-Path -LiteralPath $mwProbeTool)){$mwProbeTools[$mwProbeTool]=Get-MWProbeHash $mwProbeTool}}
 [ordered]@{passed=$mwProbePassed;failure=$mwProbeFailure;scope='Compiled original CRT provider-contract probe; execution and native equivalence not yet credited';source_files=$mwProbeSources;literal_source_copies=@($mwProbeCopies);tool_files=$mwProbeTools;artifacts=$mwProbeArtifacts;commands=@($mwProbeCommands);worker=$mwProbeWorker;whole_M4_complete=$false}|ConvertTo-Json -Depth 16|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwProbeOut 'build.json')
}
