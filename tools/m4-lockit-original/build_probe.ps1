param([Parameter(Mandatory=$true)][string]$Preparation,[Parameter(Mandatory=$true)][string]$PreparationSha256,[Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$taskBase=Join-Path $taskRoot 'reports/m4-lockit-original';$taskPrep=[IO.Path]::GetFullPath($Preparation);$taskOut=Join-Path $taskBase $Name
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
if([IO.Path]::GetDirectoryName($taskPrep)-ne$taskBase-or$Name-notmatch'^[a-z][a-z0-9-]{0,63}$'-or(Test-Path -LiteralPath $taskOut)){throw 'Fresh assigned probe build required'}
if((Hash (Join-Path $taskPrep 'report.json'))-ne$PreparationSha256){throw 'Exact fixed preparation required'}
$taskPins=Get-Content -Raw (Join-Path $taskPrep 'pins.json')|ConvertFrom-Json -AsHashtable;foreach($pair in $taskPins.files.GetEnumerator()){if((Hash $pair.Key)-ne$pair.Value){throw 'Preparation input changed'}}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$taskFiles=[ordered]@{};foreach($pair in $taskPins.files.GetEnumerator()){$taskFiles[$pair.Key]=$pair.Value};$taskFiles[$PSCommandPath]=Hash $PSCommandPath
$taskCommands=[Collections.Generic.List[object]]::new();$taskPassed=$false;$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
try{
 Import-Module (Join-Path $taskVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
 $taskArgs=@('/nologo','/c',('/Fo'+(Join-Path $taskOut 'observer.obj')),(Join-Path $taskPrep 'observer_x86.asm')); &ml.exe @taskArgs 2>&1|Tee-Object -FilePath (Join-Path $taskOut 'assembler.log');$taskCode=$LASTEXITCODE;$taskCommands.Add([ordered]@{program=(Get-Command ml.exe).Source;arguments=$taskArgs;exit_code=$taskCode});if($taskCode-ne0){throw 'Actual observer assembly failed'}
 $taskArgs=@('/nologo','/std:c++17','/O2','/MT','/EHsc','/W4',(Join-Path $taskPrep 'reference.cpp'),(Join-Path $taskOut 'observer.obj'),('/Fo'+(Join-Path $taskOut 'reference.obj')),('/Fe'+(Join-Path $taskOut 'probe.exe')),'/link','/DYNAMICBASE:NO','/FIXED'); &cl.exe @taskArgs 2>&1|Tee-Object -FilePath (Join-Path $taskOut 'compile.log');$taskCode=$LASTEXITCODE;$taskCommands.Add([ordered]@{program=(Get-Command cl.exe).Source;arguments=$taskArgs;exit_code=$taskCode});if($taskCode-ne0){throw 'Actual x86 probe compiler failed'}
 foreach($pair in $taskFiles.GetEnumerator()){if((Hash $pair.Key)-ne$pair.Value){throw 'Frozen source changed during compile'}};$taskPassed=$true
}finally{
 foreach($p in Get-ChildItem -LiteralPath $taskOut -Recurse -File){$taskFiles[$p.FullName]=Hash $p.FullName};foreach($n in @('cl.exe','ml.exe','link.exe')){if(Get-Command $n -ErrorAction SilentlyContinue){$p=(Get-Command $n).Source;$taskFiles[$p]=Hash $p}}
 [ordered]@{passed=$taskPassed;scope='Authentic balanced original32 scratch Lockit probe build only';preparation=$taskPrep;preparation_sha256=$PreparationSha256;worker=(Join-Path $taskOut 'probe.exe');worker_sha256=if($taskPassed){Hash (Join-Path $taskOut 'probe.exe')}else{$null};commands=$taskCommands;files=$taskFiles;original_executed=$false;state_seeded=$false}|ConvertTo-Json -Depth 12|Set-Content (Join-Path $taskOut 'build.json')
}
