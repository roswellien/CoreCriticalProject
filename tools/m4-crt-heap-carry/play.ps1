# Runs the native host (build/m4-crt-heap-carry-O2, produced by build.ps1) on the local game install.
# Without -Script the player's real keyboard and mouse drive the game through the real DirectInput
# provider (keyboard background/non-exclusive, mouse exclusive while the game window is in front, exactly
# as the original requests). With -Script, an input script stands in for the player (see README).
# -Frames limits the presented frames (0 = unlimited); -Dump writes every Nth frame as PPM (0 = none).
# Output goes to a fresh git-ignored directory under reports/m4-crt-attach/.
param([string]$Script = '', [int]$Frames = 0, [int]$Dump = 0)
$root = Resolve-Path (Join-Path $PSScriptRoot '../..')
Set-Location $root
$exe = 'build/m4-crt-heap-carry-O2/entry_commandline.exe'
if (-not (Test-Path $exe)) { throw "Build the native host first: tools/m4-crt-heap-carry/build.ps1 -Levels O2" }
$out = "reports/m4-crt-attach/play-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$env:MW34_FRAME_BUDGET = "$Frames"
$env:MW34_FRAME_DUMP = "$Dump"
if ($Script) { $env:MW34_INPUT_SCRIPT = (Resolve-Path $Script).Path } else { Remove-Item Env:MW34_INPUT_SCRIPT -ErrorAction SilentlyContinue }
$p = Start-Process -FilePath $exe -ArgumentList @('MW3/Mech3.exe', 'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj',
    'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', 'reports/m4-crt-fdiv/native-derived-r1/pack.bin',
    'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin', $out) -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput "$out.out" -RedirectStandardError "$out.err"
"exit=$($p.ExitCode); log: $out.err"
Get-Content "$out.err" -TotalCount 1 | ForEach-Object { $_.Substring(0, [Math]::Min(400, $_.Length)) }
