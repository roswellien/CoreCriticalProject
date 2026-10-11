param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$PreparationSha256,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'reports/m4-formatting-original'
$taskPrep=[IO.Path]::GetFullPath($Preparation);$taskOut=[IO.Path]::GetFullPath($Output)
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
if([IO.Path]::GetDirectoryName($taskPrep)-ne$taskBase-or[IO.Path]::GetDirectoryName($taskOut)-ne$taskBase-or(Test-Path -LiteralPath $taskOut)){throw 'Fresh assigned preparation/build required'}
if((Hash (Join-Path $taskPrep 'report.json'))-ne$PreparationSha256){throw 'Exact externally fixed preparation required'}
$taskPins=Get-Content -Raw (Join-Path $taskPrep 'pins.json')|ConvertFrom-Json -AsHashtable
foreach($pair in $taskPins.files.GetEnumerator()){if((Hash $pair.Key)-ne$pair.Value){throw "Source changed: $($pair.Key)"}}
$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$taskCMake=Join-Path $taskVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$taskSources=[ordered]@{};$taskCommands=[Collections.Generic.List[object]]::new();$taskPassed=$false
$taskBuild=Join-Path $taskOut 'build-x86'
New-Item -ItemType Directory -Path $taskOut|Out-Null
foreach($pair in $taskPins.files.GetEnumerator()){$taskSources[$pair.Key]=$pair.Value}
$taskSources[$PSCommandPath]=Hash $PSCommandPath
function Run([string[]]$a,[string]$name){&$taskCMake @a 2>&1|Tee-Object -FilePath (Join-Path $taskOut $name);$code=$LASTEXITCODE;$taskCommands.Add([ordered]@{program=$taskCMake;arguments=$a;exit_code=$code});if($code-ne0){throw 'Actual x86 compiler failed'}}
try{
 Import-Module (Join-Path $taskVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
 Run @('-S',$taskPrep,'-B',$taskBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_ORIGINAL_INCLUDE=$taskPrep",("-DMW34_WRITER_SOURCE="+(Join-Path $taskRoot 'tools/m4-capture-direct/capture_direct_v3.cpp')),("-DMW34_WRITER_INCLUDE="+(Join-Path $taskRoot 'tools/m4-capture-direct'))) 'configure.log'
 Run @('--build',$taskBuild,'--config','Release','--verbose') 'compile.log'
 foreach($pair in $taskSources.GetEnumerator()){if((Hash $pair.Key)-ne$pair.Value){throw 'Source changed during compile'}}
 $taskWorker=Join-Path $taskBuild 'Release/mw34_joint_startup124_original.exe';Copy-Item -LiteralPath $taskWorker -Destination (Join-Path $taskOut 'original-worker.exe');$taskPassed=$true
}catch{$_|Out-String|Set-Content (Join-Path $taskOut 'failure.txt');throw}
finally{
 $taskPhysical=[ordered]@{};foreach($pair in $taskSources.GetEnumerator()){$taskPhysical[$pair.Key]=$pair.Value}
 foreach($file in Get-ChildItem -LiteralPath $taskOut -Recurse -File){$taskPhysical[$file.FullName]=Hash $file.FullName}
 foreach($name in @('cl.exe','ml.exe','link.exe')){if(Get-Command $name -ErrorAction SilentlyContinue){$p=(Get-Command $name).Source;$taskPhysical[$p]=Hash $p}}
 $taskPhysical[$taskCMake]=Hash $taskCMake
 [ordered]@{passed=$taskPassed;preparation=$taskPrep;preparation_sha256=$PreparationSha256;sources=$taskSources;commands=$taskCommands;worker=(Join-Path $taskOut 'original-worker.exe');worker_sha256=if($taskPassed){Hash (Join-Path $taskOut 'original-worker.exe')}else{$null};pack=(Join-Path $taskPrep 'pages.bin');record_bytes=356992;sequences=1;phases=3;roots=3;pages=43;extra_pages=3;direct_primary=$true;initializer_credit=$false;original_executed=$false;native_executed=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 12|Set-Content (Join-Path $taskOut 'build.json')
 $taskPhysical[(Join-Path $taskOut 'build.json')]=Hash (Join-Path $taskOut 'build.json')
 [ordered]@{files=$taskPhysical}|ConvertTo-Json -Depth 6|Set-Content (Join-Path $taskOut 'pins.json')
}


