# Runs the native host (build/m4-crt-heap-carry-O2, produced by build.ps1) on the local game install.
# Without -Script the player's real keyboard and mouse drive the game through the real DirectInput
# provider (keyboard background/non-exclusive, mouse exclusive while the game window is in front, exactly
# as the original requests). With -Script, an input script stands in for the player (see README).
# -Frames limits the presented frames (0 = unlimited); -Dump writes every Nth frame as PPM (0 = none).
# -Overlay shows a host performance overlay (FPS, mean/worst frame time) on the presented frames; off by default.
# Output goes to a fresh git-ignored directory under reports/m4-crt-attach/.
param([string]$Script = '', [int]$Frames = 0, [int]$Dump = 0, [string]$Build = 'O2-merge', [switch]$Overlay)
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '../..')
Set-Location $root
if(Get-Process -Name entry_commandline,Mech3 -ErrorAction SilentlyContinue){throw 'A game session is already running. Close it normally before launching.'}
$exe = "build/m4-crt-heap-carry-$Build/entry_commandline.exe"  # -Build O2-inline: the inlined-fast-path build
if (-not (Test-Path $exe)) { throw "Build the native host first: tools/m4-crt-heap-carry/build.ps1 -Levels O2" }
$out = "reports/m4-crt-attach/play-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
# The local soundtrack is prepared with the system media decoder, outside the guest process.
$musicConfig=Join-Path $root 'local/remaster/music.json'
Remove-Item Env:MW34_MUSIC_PACK,Env:MW34_MUSIC_LOG -ErrorAction SilentlyContinue
if((Test-Path -LiteralPath $musicConfig) -and (Get-Content -LiteralPath $musicConfig -Raw | ConvertFrom-Json).enabled){
    if($Build -ne 'O2-merge'){throw 'Configured local music requires the current O2-merge native play build.'}
    $python=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if(!(Test-Path -LiteralPath $python)){$python=(Get-Command python.exe -ErrorAction Stop).Source}
    & $python (Join-Path $root 'tools/remaster-launcher/prepare_music.py')
    if($LASTEXITCODE){throw 'Local music preparation failed'}
    $env:MW34_MUSIC_PACK=Join-Path $root 'local/remaster/prepared/music/tracklist.bin'
    $env:MW34_MUSIC_LOG="$out.music.log"
}
$env:MW34_FRAME_BUDGET = "$Frames"
$env:MW34_FRAME_DUMP = "$Dump"
if ($Overlay) { if (-not $env:MW34_PERF_OVERLAY) { $env:MW34_PERF_OVERLAY = '1' } } else { Remove-Item Env:MW34_PERF_OVERLAY -ErrorAction SilentlyContinue }
# Host-built initial state (no original-process BEFORE data); MW34_SEED=before selects the original projection.
if (-not $env:MW34_SEED) { $env:MW34_SEED = 'host' }
# True loader order: MSVCRT/MFC42/MSVCP50 attach complete, then the game's CRT entry runs whole in the generic native
# stage; MW34_STARTUP=accepted selects the accepted bounded entry chain (attach at the __getmainargs service).
if (-not $env:MW34_STARTUP) { $env:MW34_STARTUP = 'loader' }
# GPU-resident frame and GPU HUD (docs/hud-vulkan-integration-handoff.md): the 3D target stays on the GPU, the game's
# HUD primitives are drawn by Vulkan, and frames are presented directly. MW34_LAZY_RT=0 / MW34_GPU_HUD=0 restore the
# CPU path (exact frame comparisons against the recorded baselines use it).
if (-not $env:MW34_LAZY_RT) { $env:MW34_LAZY_RT = '1' }
if (-not $env:MW34_GPU_HUD) { $env:MW34_GPU_HUD = '1' }
# Window: the largest window of the game's aspect that fits the screen; 3D and HUD render at its resolution
# (MW34_WINDOW=integer keeps the 1x/2x window; MW34_RENDER_SCALE=1 renders at the game resolution).
if (-not $env:MW34_WINDOW) { $env:MW34_WINDOW = 'fit' }
if ($Script) { $env:MW34_INPUT_SCRIPT = (Resolve-Path $Script).Path } else { Remove-Item Env:MW34_INPUT_SCRIPT -ErrorAction SilentlyContinue }
$p = Start-Process -FilePath $exe -ArgumentList @('MW3/Mech3.exe', 'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj',
    'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', 'reports/m4-crt-fdiv/native-derived-r1/pack.bin',
    'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin', $out) -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput "$out.out" -RedirectStandardError "$out.err"
"exit=$($p.ExitCode); log: $out.err"
Get-Content "$out.err" -TotalCount 1 | ForEach-Object { $_.Substring(0, [Math]::Min(400, $_.Length)) }
