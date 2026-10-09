param([Parameter(Mandatory=$true)][string]$OutputDirectory,[Parameter(Mandatory=$true)][string]$PreparationDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use pwsh.exe'}
$fdRefRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$fdRefAllowed=Join-Path $fdRefRoot 'reports/m4-crt-fdiv-reference'
$fdRefOut=[IO.Path]::GetFullPath($OutputDirectory)
$fdRefPreparation=(Resolve-Path -LiteralPath $PreparationDirectory).Path
if([IO.Path]::GetDirectoryName($fdRefOut)-ne$fdRefAllowed-or[IO.Path]::GetDirectoryName($fdRefPreparation)-ne$fdRefAllowed){throw 'Immediate private FDIV reference evidence required'}
$fdRefName=Split-Path $fdRefOut -Leaf
if($fdRefName-notmatch'^[a-z][a-z0-9-]{0,63}$'-or$fdRefName-match'^(con|prn|aux|nul|com[0-9]|lpt[0-9])$'){throw 'Fresh simple experiment name required'}
$fdRefBuild=Join-Path $fdRefRoot "build/m4-crt-fdiv-reference-$fdRefName"
if((Test-Path -LiteralPath $fdRefOut)-or(Test-Path -LiteralPath $fdRefBuild)){throw 'Fresh report/build directories required before any capture'}
function Hash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$fdRefPreparationMap=Get-Content -Raw -LiteralPath (Join-Path $fdRefPreparation 'pins.json')|ConvertFrom-Json
foreach($fdRefPair in $fdRefPreparationMap.files.PSObject.Properties){if((Hash $fdRefPair.Name)-ne$fdRefPair.Value){throw 'Exact source preparation changed'}}
$fdRefSources=[ordered]@{}
foreach($fdRefFile in @(Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File|Where-Object {$_.FullName -notmatch '__pycache__'};Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../m4-runtime') -File|Where-Object {$_.Extension-eq'.hpp'};Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../m4-startup') -File|Where-Object {$_.Extension-eq'.hpp'};Get-ChildItem -LiteralPath (Join-Path $fdRefRoot 'runtime/memory') -File|Where-Object {$_.Extension-eq'.hpp'};Get-Item -LiteralPath (Join-Path $fdRefRoot 'runtime/core/guest_address.hpp'),(Join-Path $PSScriptRoot '../m4-crt/probe_common.hpp'),(Join-Path $PSScriptRoot '../m4-crt/probe_io.hpp'),(Join-Path $PSScriptRoot '../m4-crt-fdiv/provider.hpp'),(Join-Path $PSScriptRoot '../m4-crt-fdiv/host_services.hpp'),(Join-Path $fdRefPreparation 'spec.hpp'))|Sort-Object FullName){$fdRefSources[$fdRefFile.FullName]=Hash $fdRefFile.FullName}
New-Item -ItemType Directory -Path $fdRefOut|Out-Null
$fdRefCopies=[Collections.Generic.List[object]]::new()
foreach($fdRefPair in $fdRefSources.GetEnumerator()){$fdRefCopy=Join-Path $fdRefOut ('sources/'+[IO.Path]::GetRelativePath($fdRefRoot,$fdRefPair.Key));New-Item -ItemType Directory -Force -Path (Split-Path $fdRefCopy -Parent)|Out-Null;Copy-Item -LiteralPath $fdRefPair.Key -Destination $fdRefCopy;if((Hash $fdRefCopy)-ne$fdRefPair.Value){throw 'Literal source preservation failed'};$fdRefCopies.Add([ordered]@{original_path=$fdRefPair.Key;preserved_path=$fdRefCopy;sha256=$fdRefPair.Value})}
$fdRefCommands=[Collections.Generic.List[object]]::new();$fdRefTools=[ordered]@{};$fdRefPassed=$false;$fdRefFailure=$null
function Run([string]$Program,[string[]]$Arguments,[string]$Log){$fdRefTools[$Program]=Hash $Program;$fdRefLog=Join-Path $fdRefOut $Log;[IO.File]::WriteAllBytes($fdRefLog,[byte[]]::new(0));$fdRefSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{&$Program @Arguments 2>&1|Tee-Object -FilePath $fdRefLog|Out-Null;$fdRefExit=$LASTEXITCODE}finally{$ErrorActionPreference=$fdRefSaved};$fdRefCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$fdRefExit;log_path=$fdRefLog;log_sha256=(Hash $fdRefLog)});if($fdRefExit-ne0){throw "Reference build tool failed exit=$fdRefExit"}}
$fdRefVS='C:/Program Files/Microsoft Visual Studio/18/Community'
try{
 $fdRefShell=Join-Path $fdRefVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll';$fdRefTools[$fdRefShell]=Hash $fdRefShell
 Import-Module $fdRefShell;Enter-VsDevShell -VsInstallPath $fdRefVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
 $fdRefCMake=Join-Path $fdRefVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
 foreach($fdRefTool in @((Get-Process -Id $PID).Path,(Join-Path $fdRefVS 'MSBuild/Current/Bin/amd64/MSBuild.exe'))+@('cl.exe','link.exe','ml.exe','rc.exe','mt.exe'|ForEach-Object {(Get-Command $_ -ErrorAction SilentlyContinue).Source})){if($fdRefTool-and(Test-Path -LiteralPath $fdRefTool)){$fdRefTools[$fdRefTool]=Hash $fdRefTool}}
 Run $fdRefCMake @('-S',(Join-Path $PSScriptRoot 'original'),'-B',$fdRefBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_FDIV_REFERENCE_INCLUDE=$fdRefPreparation") 'configure.log'
 Run $fdRefCMake @('--build',$fdRefBuild,'--config','Release','--verbose') 'build.log'
 $fdRefWorker=Join-Path $fdRefBuild 'Release/fdiv_reference.exe'
 if(-not(Test-Path -LiteralPath $fdRefWorker)){throw 'Compiled reference worker missing'}
 foreach($fdRefPair in $fdRefSources.GetEnumerator()){if((Hash $fdRefPair.Key)-ne$fdRefPair.Value){throw 'Source changed during reference compilation'}}
 foreach($fdRefPair in $fdRefTools.GetEnumerator()){if((Hash $fdRefPair.Key)-ne$fdRefPair.Value){throw 'Admitted provider changed during reference compilation'}}
 $fdRefPassed=$true
}catch{$fdRefFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $fdRefOut 'failure.txt');throw}
finally{
 $fdRefHeaders=[ordered]@{}
 if(Test-Path -LiteralPath (Join-Path $fdRefOut 'build.log')){foreach($fdRefLine in Get-Content -LiteralPath (Join-Path $fdRefOut 'build.log')){if($fdRefLine-match'Note: including file:\s*(.+?)\s*$'){$fdRefHeader=$Matches[1].Trim();if(Test-Path -LiteralPath $fdRefHeader){$fdRefHeaders[[IO.Path]::GetFullPath($fdRefHeader)]=Hash $fdRefHeader}}}}
 $fdRefArtifacts=[ordered]@{};foreach($fdRefDirectory in @($fdRefOut,$fdRefBuild,$fdRefPreparation)){if(Test-Path -LiteralPath $fdRefDirectory){foreach($fdRefFile in Get-ChildItem -LiteralPath $fdRefDirectory -Recurse -File){$fdRefArtifacts[$fdRefFile.FullName]=Hash $fdRefFile.FullName}}}
 [ordered]@{passed=$fdRefPassed;failure=$fdRefFailure;scope='Build/static scaffold only; complete original FDIV writer not executed';original_executed=$false;native_executed=$false;worker=$fdRefWorker;worker_expected_image_base=0x34000000;source_files=$fdRefSources;literal_source_copies=@($fdRefCopies);tool_files=$fdRefTools;tool_hash_semantics='Listed direct and indirect provider current hashes admitted before build and rechecked after. Recorded commands/logs establish invocation; merely listing RC/MT does not assert child execution.';compiler_read_headers=$fdRefHeaders;commands=@($fdRefCommands);artifacts=$fdRefArtifacts;preparation=(Join-Path $fdRefPreparation 'report.json');preparation_sha256=(Hash (Join-Path $fdRefPreparation 'report.json'));whole_M4_complete=$false}|ConvertTo-Json -Depth 16|Set-Content -Encoding utf8 -LiteralPath (Join-Path $fdRefOut 'build.json')
}
