param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use pwsh.exe for CW research build'}
$mwCWRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$mwCWOut=[System.IO.Path]::GetFullPath($OutputDirectory);$mwCWAllowed=Join-Path $mwCWRoot 'reports/m4-crt-cw'
if(-not $mwCWOut.StartsWith($mwCWAllowed+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Private CW output required'}
$mwCWName=Split-Path $mwCWOut -Leaf;if($mwCWName -notmatch '^[a-z][a-z0-9-]{0,63}$'){throw 'Fresh simple CW name'};$mwCWBuild=Join-Path $mwCWRoot "build/m4-crt-cw-$mwCWName"
if((Test-Path -LiteralPath $mwCWOut) -or (Test-Path -LiteralPath $mwCWBuild)){throw 'Fresh CW report/build required'}
function Get-MWCWHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwCWSources=[ordered]@{};foreach($mwCWFile in @(Get-ChildItem -LiteralPath $PSScriptRoot -File;Get-Item -LiteralPath (Join-Path $PSScriptRoot '../m4-crt/probe_common.hpp'),(Join-Path $PSScriptRoot '../m4-crt/probe_io.hpp'))){$mwCWSources[$mwCWFile.FullName]=Get-MWCWHash $mwCWFile.FullName}
New-Item -ItemType Directory -Path $mwCWOut|Out-Null;$mwCWCopies=[System.Collections.Generic.List[object]]::new();foreach($mwCWPath in $mwCWSources.Keys){$mwCWCopy=Join-Path (Join-Path $mwCWOut 'sources') ([System.IO.Path]::GetRelativePath($mwCWRoot,$mwCWPath));New-Item -ItemType Directory -Force -Path (Split-Path $mwCWCopy)|Out-Null;Copy-Item -LiteralPath $mwCWPath -Destination $mwCWCopy;if((Get-MWCWHash $mwCWCopy) -ne $mwCWSources[$mwCWPath]){throw 'Exact CW literal source preservation'};$mwCWCopies.Add([ordered]@{original_path=$mwCWPath;preserved_path=$mwCWCopy;sha256=$mwCWSources[$mwCWPath]})}
$mwCWCommands=[System.Collections.Generic.List[object]]::new()
function Invoke-MWCW([string]$Program,[string[]]$Arguments,[string]$Log){$mwCWSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{& $Program @Arguments 2>&1|Tee-Object -FilePath $Log;$mwCWExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwCWSaved};$mwCWCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwCWExit;log_path=$Log;log_sha256=(Get-MWCWHash $Log)});if($mwCWExit -ne 0){throw "CW build tool failed $Program exit=$mwCWExit"}}
$mwCWVS='C:/Program Files/Microsoft Visual Studio/18/Community';$mwCWPassed=$false;$mwCWFailure=$null
try{
 Import-Module (Join-Path $mwCWVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $mwCWVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
 $mwCWCMake=Join-Path $mwCWVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
 Invoke-MWCW $mwCWCMake @('-S',$PSScriptRoot,'-B',$mwCWBuild,'-G','Visual Studio 18 2026','-A','Win32') (Join-Path $mwCWOut 'configure.log')
 Invoke-MWCW $mwCWCMake @('--build',$mwCWBuild,'--config','Release','--verbose') (Join-Path $mwCWOut 'build.log')
 $mwCWWorker=Join-Path $mwCWBuild 'Release/mw34_m4_cw_reference.exe';Invoke-MWCW $mwCWWorker @('--check-hash') (Join-Path $mwCWOut 'hash-controls.log')
 foreach($mwCWPath in $mwCWSources.Keys){if((Get-MWCWHash $mwCWPath) -ne $mwCWSources[$mwCWPath]){throw 'CW source changed during build'}};$mwCWPassed=$true
}catch{$mwCWFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $mwCWOut 'failure.txt');throw}finally{
 $mwCWArtifacts=[ordered]@{};foreach($mwCWFile in @(Get-ChildItem -LiteralPath $mwCWOut -File -Recurse;if(Test-Path -LiteralPath $mwCWBuild){Get-ChildItem -LiteralPath $mwCWBuild -File -Recurse|Where-Object {$_.Extension -in @('.exe','.obj','.lib','.txt','.cmake','.vcxproj','.props','.json','.tlog')}})){$mwCWArtifacts[$mwCWFile.FullName]=Get-MWCWHash $mwCWFile.FullName}
 $mwCWTools=[ordered]@{};foreach($mwCWTool in @($mwCWCMake,(Get-Process -Id $PID).Path,(Join-Path $mwCWVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $mwCWVS 'MSBuild/Current/Bin/amd64/MSBuild.exe'))+@('cl.exe','link.exe','rc.exe'|ForEach-Object {(Get-Command $_ -ErrorAction SilentlyContinue).Source})){if($mwCWTool -and (Test-Path -LiteralPath $mwCWTool)){$mwCWTools[$mwCWTool]=Get-MWCWHash $mwCWTool}}
 [ordered]@{passed=$mwCWPassed;failure=$mwCWFailure;scope='Compiled authored hardware FLDCW/FNSTCW probe only; no vendor/game/native bridge acceptance';source_files=$mwCWSources;literal_source_copies=@($mwCWCopies);tool_files=$mwCWTools;artifacts=$mwCWArtifacts;commands=@($mwCWCommands);worker=$mwCWWorker;whole_M4_complete=$false}|ConvertTo-Json -Depth 16|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwCWOut 'build.json')
}
