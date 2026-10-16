param(
    [Parameter(Mandatory=$true)][string]$Harness,
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string]$Assets,
    [Parameter(Mandatory=$true)][string]$InputScript,
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Prefix='geometry-r1',
    [int]$Frames=1600
)
$ErrorActionPreference='Stop'
if($Frames -lt 1100){throw 'At least 1100 frames required for warm scene coverage'}
$Harness=(Resolve-Path -LiteralPath $Harness).Path
$Executable=(Resolve-Path -LiteralPath $Executable).Path
$Assets=(Resolve-Path -LiteralPath $Assets).Path
$InputScript=(Resolve-Path -LiteralPath $InputScript).Path
# Independent shell per case avoids sharing Add-Type and process/static state.
# ABBA order controls warm-up/drift; capture cases are excluded from timings.
$cases=@(
    @{Name='cpu-a';Gpu=$false;Capture=$false},
    @{Name='gpu-a';Gpu=$true;Capture=$false},
    @{Name='gpu-b';Gpu=$true;Capture=$false},
    @{Name='cpu-b';Gpu=$false;Capture=$false},
    @{Name='cpu-image';Gpu=$false;Capture=$true},
    @{Name='gpu-image';Gpu=$true;Capture=$true}
)
foreach($case in $cases){
    $busy=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(entry_commandline|mech3|mw3|piratesmoon)\.exe$'})
    if($busy.Count){throw 'A game is already running; comparison stopped'}
    $arguments=@('-NoProfile','-File',$Harness,'-Scenario','IA','-Build','play',
        '-Name',"$Prefix-$($case.Name)",'-Executable',$Executable,
        '-DrawDistance','1600','-Frames',$(if($case.Capture){1050}else{$Frames}),
        '-Visible','-RemasterAssets','OriginalModels','-RemasterWidth','3440',
        '-GpuHud','-AA','fxaa','-AF','16','-FrameDump','0',
        '-CandidateEnvironment',$Assets,'-InputScript',$InputScript)
    if($case.Gpu){$arguments+='-GpuModels'}
    if($case.Capture){$arguments+=@('-HiresDumps','1000')}
    & pwsh @arguments
    if($LASTEXITCODE){throw "Harness failed: $($case.Name)"}
    # The game itself uses a deliberate frame-budget exception (exit1).
    # A successful harness alone is not evidence; inspect its record and logs.
    $run=Join-Path (Split-Path $Harness -Parent) "runs/$Prefix-$($case.Name)"
    $record=Get-Content -LiteralPath (Join-Path $run 'run.json') -Raw | ConvertFrom-Json
    $expected=if($case.Capture){1050}else{$Frames}
    $errorText=Get-Content -LiteralPath (Join-Path $run 'stderr.txt') -Raw
    if($record.exit_code -ne 1 -or $errorText -notmatch "Presentation frame budget reached: $expected frames presented"){
        throw "Case did not reach its intended budget: $run"
    }
    Write-Output "Completed $($case.Name): $run"
}
