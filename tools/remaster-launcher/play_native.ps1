param([string]$Profile,[int]$Frames=0,[int]$Dump=0,[string]$Script='')
$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $taskRoot
$active=Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('entry_commandline.exe','Mech3.exe')}
if($active){throw "A game session is already running (PID $($active.ProcessId -join ', '))."}
$config=Get-Content -LiteralPath $Profile -Raw | ConvertFrom-Json
if($config.native.runtime_environment){
 foreach($binding in $config.native.runtime_environment.PSObject.Properties){
  if($binding.Name -notlike 'MW34_*'){throw 'Invalid native runtime environment binding'}
  [Environment]::SetEnvironmentVariable($binding.Name,[string]$binding.Value,'Process')
 }
}
$distance=if($config.graphics.PSObject.Properties.Name -contains 'draw_distance'){[int]$config.graphics.draw_distance}else{800}
if($distance -notin @(800,1600,2400,3200)){throw 'Unsupported scenery draw distance'}
$env:MW34_REMASTER_DRAW_DISTANCE=[string]$distance
$exe=Join-Path $taskRoot $config.native.executable
if(!(Test-Path -LiteralPath $exe)){throw 'Registered native executable is missing'}
$run=Join-Path $taskRoot ('local/remaster/runs/'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $run | Out-Null
$env:MW34_FRAME_BUDGET="$Frames";$env:MW34_FRAME_DUMP="$Dump";$env:MW34_FRAME_TIMES="$run/frame-times.txt"
$env:MW34_MODELS_LOG="$run/mesh-runtime.jsonl"
if($env:MW34_GPU_WORLD -eq '1'){
 $env:MW34_WORLD_LOG="$run/world.jsonl"
 $env:MW34_GEOMETRY_PROFILE="$run/geometry.csv"
}
if($env:MW34_MUSIC_PACK){$env:MW34_MUSIC_LOG="$run/music.log"}
if($env:MW34_BUSHWACKER_TEST){$env:MW34_BUSHWACKER_TEST_LOG=$env:MW34_MODELS_LOG}
if($Script){$env:MW34_INPUT_SCRIPT=$Script;$env:MW34_VIRTUAL_CLOCK='50'}
else{Remove-Item Env:MW34_INPUT_SCRIPT,Env:MW34_VIRTUAL_CLOCK -ErrorAction SilentlyContinue}
$arguments=@('MW3/Mech3.exe','reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj','local/mw3-staged/Shared_DLLs/MSVCRT.DLL','reports/m4-crt-fdiv/native-derived-r1/pack.bin','reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin',"$run/game")
$process=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput "$run/stdout.txt" -RedirectStandardError "$run/stderr.txt"
$null=$process.Handle
Write-Output "Native Remaster PID $($process.Id). Enter Training and press X for third-person. Logs: $run"
$process.WaitForExit()
$digestAlgorithm=[System.Security.Cryptography.SHA256]::Create()
$digestStream=[System.IO.File]::OpenRead($exe)
try{$digest=[BitConverter]::ToString($digestAlgorithm.ComputeHash($digestStream)).Replace('-','')}
finally{$digestStream.Dispose();$digestAlgorithm.Dispose()}
@{exit_code=$process.ExitCode;pid=$process.Id;graphics=$config.graphics;executable=$exe;executable_sha256=$digest;runtime_environment=$config.native.runtime_environment} | ConvertTo-Json -Depth 6 | Set-Content "$run/run.json"
Write-Output "Native Remaster exit: $($process.ExitCode)"
exit $process.ExitCode
