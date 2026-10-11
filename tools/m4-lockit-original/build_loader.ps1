param([Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'reports/m4-lockit-original'
if($Name -notmatch '^[a-z][a-z0-9-]{0,63}$'){throw 'Fresh simple report name required'}
$taskOut=Join-Path $taskBase $Name
if(Test-Path -LiteralPath $taskOut){throw 'Fresh loader build required'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$taskPassed=$false;$taskSources=[ordered]@{};$taskCommands=[Collections.Generic.List[object]]::new()
foreach($p in @($PSCommandPath,(Join-Path $PSScriptRoot 'loader_probe.cpp'))){$taskSources[$p]=Hash $p;Copy-Item -LiteralPath $p -Destination (Join-Path $taskOut ([IO.Path]::GetFileName($p)))}
$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
try{
 Import-Module (Join-Path $taskVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
 $taskArgs=@('/nologo','/std:c++17','/O2','/MT','/EHsc','/W4',(Join-Path $taskOut 'loader_probe.cpp'),('/Fo'+(Join-Path $taskOut 'probe.obj')),('/Fe'+(Join-Path $taskOut 'probe.exe')),'/link','/DYNAMICBASE:NO','/FIXED')
 &cl.exe @taskArgs 2>&1|Tee-Object -FilePath (Join-Path $taskOut 'compile.log');$taskCode=$LASTEXITCODE;$taskCommands.Add([ordered]@{program=(Get-Command cl.exe).Source;arguments=$taskArgs;exit_code=$taskCode});if($taskCode-ne0){throw 'Actual x86 compiler failed'}
 foreach($p in $taskSources.Keys){if((Hash $p)-ne$taskSources[$p]){throw 'Frozen source changed during compile'}}
 $taskPassed=$true
}finally{
 $taskFiles=[ordered]@{};foreach($p in $taskSources.Keys){$taskFiles[$p]=$taskSources[$p]};foreach($p in Get-ChildItem -LiteralPath $taskOut -Recurse -File){$taskFiles[$p.FullName]=Hash $p.FullName}
 foreach($n in @('cl.exe','link.exe')){if(Get-Command $n -ErrorAction SilentlyContinue){$p=(Get-Command $n).Source;$taskFiles[$p]=Hash $p}}
 [ordered]@{passed=$taskPassed;scope='Authentic x86 post-DllMain loader probe build only';worker=(Join-Path $taskOut 'probe.exe');worker_sha256=if($taskPassed){Hash (Join-Path $taskOut 'probe.exe')}else{$null};commands=$taskCommands;files=$taskFiles;original_executed=$false;state_seeded=$false}|ConvertTo-Json -Depth 12|Set-Content (Join-Path $taskOut 'build.json')
}
