<#
.SYNOPSIS
Start the selected private native host after Python has prepared its assets.
.DESCRIPTION
The profile supplies a previously validated host and environment bindings. This
script applies explicit session overrides, owns a fresh log directory, waits for
normal process completion and records the exit status. It does not build/admit a
host or fall back to the original executable. Capture scripts/clocks are opt-in.
#>
param(
    [string]$Profile,
    [int]$Frames = 0,
    [int]$Dump = 0,
    [string]$Script = '',
    [string]$LightingPreset = '',
    [string]$GameExe = '',
    [ValidateSet('0','1')][string]$InstantReplay = '0',
    [ValidateSet('','0','1')][string]$FixtureLights = '',
    [ValidateSet('','0','1')][string]$Weather = '',
    [string]$RuntimeRoot = ''
)

$ErrorActionPreference = 'Stop'
$taskRoot = if ($RuntimeRoot) { [IO.Path]::GetFullPath($RuntimeRoot) } else { Split-Path (Split-Path $PSScriptRoot -Parent) -Parent }
Set-Location $taskRoot
$active = Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('entry_commandline.exe','Mech3.exe')}
if ($active) {
    throw "A game session is already running (PID $($active.ProcessId -join ', '))."
}

# Profile bindings affect this coordinator and its child, never machine/user settings.
$config = Get-Content -LiteralPath $Profile -Raw | ConvertFrom-Json
if ($config.native.runtime_environment) {
    foreach ($binding in $config.native.runtime_environment.PSObject.Properties) {
        if ($binding.Name -notlike 'MW34_*') {
            throw 'Invalid native runtime environment binding'
        }
        [Environment]::SetEnvironmentVariable($binding.Name, [string]$binding.Value, 'Process')
    }
}

# Explicit launcher choice wins over old profiles and inherited capture defaults.
$env:MW34_INSTANT_REPLAY = $InstantReplay
if ($FixtureLights -ne '') {
    $env:MW34_FIXTURE_LIGHTS = $FixtureLights
}
if ($Weather -ne '') {
    $env:MW34_WEATHER = $Weather
}
$lighting = $null
if ($config.native.sun_preset -or $LightingPreset) {
    $lighting = (& (Join-Path $PSScriptRoot 'resolve_sun_preset.ps1') -Profile $Profile -Preset $LightingPreset -RuntimeRoot $taskRoot) | ConvertFrom-Json
    foreach ($binding in $lighting.environment.PSObject.Properties) {
        [Environment]::SetEnvironmentVariable($binding.Name, [string]$binding.Value, 'Process')
        $config.native.runtime_environment | Add-Member -NotePropertyName $binding.Name -NotePropertyValue ([string]$binding.Value) -Force
    }
    if ($LightingPreset) {
        [Environment]::SetEnvironmentVariable('MW34_MANUAL_LIGHTING', '1', 'Process')
    }
    Write-Output "Lighting preset: $($lighting.map) / $($lighting.preset)"
}

# These values are native renderer world-distance choices, not an arbitrary slider.
$distance = if ($config.graphics.PSObject.Properties.Name -contains 'draw_distance') {
    [int]$config.graphics.draw_distance
} else {
    800
}
if ($distance -notin @(800,1200,1600,2400,3200)) {
    throw 'Unsupported scenery draw distance'
}
$env:MW34_REMASTER_DRAW_DISTANCE = [string]$distance
$fogDistance = if ($config.graphics.PSObject.Properties.Name -contains 'fog_distance') {
    [int]$config.graphics.fog_distance
} else {
    0
}
if ($fogDistance -notin @(0,1100)) {
    throw 'Unsupported scenery fog distance'
}
$env:MW34_REMASTER_FOG_DISTANCE = [string]$fogDistance
if ($config.graphics.PSObject.Properties.Name -contains 'window_mode') {
    $env:MW34_WINDOW_MODE = [string]$config.graphics.window_mode
}

$exe = if ([IO.Path]::IsPathRooted([string]$config.native.executable)) {
    [string]$config.native.executable
} else {
    Join-Path $taskRoot $config.native.executable
}
if (!(Test-Path -LiteralPath $exe)) {
    throw 'Registered native executable is missing'
}

# Each session owns its trace filenames. Zero frame/dump budgets remain interactive.
$run = if ($config.native.launch_session_directory) {
    Join-Path ([string]$config.native.launch_session_directory) 'native'
} else {
    Join-Path $taskRoot ('local/remaster/runs/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
}
if (Test-Path -LiteralPath $run) { throw 'The native session directory already exists; refusing to overwrite prior logs.' }
New-Item -ItemType Directory -Path $run | Out-Null
if ($config.native.platform_visibility_trace) {
    $env:MW34_PLATFORM_TRACE = Join-Path $run 'platform-visibility.txt'
    if ($env:MW34_TURRET_AIM_REPAIR -eq '1') {
        $env:MW34_TURRET_AIM_LOG = Join-Path $run 'turret-aim.txt'
    }
}
$env:MW34_FRAME_BUDGET = "$Frames"
$env:MW34_FRAME_DUMP = "$Dump"
$env:MW34_FRAME_TIMES = "$run/frame-times.txt"
$env:MW34_MODELS_LOG = "$run/mesh-runtime.jsonl"
if ($env:MW34_GPU_WORLD -eq '1') {
    $env:MW34_WORLD_LOG = "$run/world.jsonl"
    $env:MW34_GEOMETRY_PROFILE = "$run/geometry.csv"
}
if ($env:MW34_MUSIC_PACK) {
    $env:MW34_MUSIC_LOG = "$run/music.log"
}
if ($env:MW34_BUSHWACKER_TEST) {
    $env:MW34_BUSHWACKER_TEST_LOG = $env:MW34_MODELS_LOG
}
if ($Script) {
    $env:MW34_INPUT_SCRIPT = $Script
    $env:MW34_VIRTUAL_CLOCK = '50'
}

# GameExe is original input data for the native host, not the process being started.
# The remaining inputs are private, previously prepared development artifacts.
$gameExe = if ($GameExe) {
    if (!(Test-Path -LiteralPath $GameExe)) {
        throw 'Selected game executable is missing'
    }
    $GameExe
} elseif ($env:MW34_GAME_EXE -and (Test-Path -LiteralPath $env:MW34_GAME_EXE)) {
    $env:MW34_GAME_EXE
} else {
    'MW3/Mech3.exe'
}
$env:MW34_GAME_EXE = $gameExe
if ($config.native.installation_layout -eq 1) {
    if ($env:MW34_SEED -ne 'host' -or $env:MW34_STARTUP -ne 'loader') {
        throw 'Installed runtime requires host-initialized loader startup; captured startup state is not allowed.'
    }
    $inputs = $config.native.launch_inputs
    $paths = @()
    foreach ($key in @('entry_object','crt_provider','crt_pack')) {
        $path = [string]$inputs.$key
        if (!$path) { throw "Installed runtime is missing required input $key" }
        if (![IO.Path]::IsPathRooted($path)) { $path = Join-Path $taskRoot $path }
        if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Installed runtime input is missing: $key" }
        $paths += $path
    }
    # Host-initialized startup never reads this positional slot. Do not ship or
    # silently fall back to the original-process BEFORE capture.
    $arguments = @($gameExe) + $paths + @('host-initialized', "$run/game")
} else {
    $arguments = @(
        $gameExe,
        'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj',
        'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
        'reports/m4-crt-fdiv/native-derived-r1/pack.bin',
        'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin',
        "$run/game"
    )
}
$process = Start-Process -FilePath $exe -ArgumentList ($arguments | ForEach-Object {'"' + $_ + '"'}) -WindowStyle Hidden -PassThru -RedirectStandardOutput "$run/stdout.txt" -RedirectStandardError "$run/stderr.txt"
$null = $process.Handle
Write-Output "Native Remaster PID $($process.Id). Enter Training and press X for third-person. Logs: $run"
$process.WaitForExit()

# Record the executable actually selected; dispose hashing handles even on failure.
$digestAlgorithm = [System.Security.Cryptography.SHA256]::Create()
$digestStream = [System.IO.File]::OpenRead($exe)
try {
    $digest = [BitConverter]::ToString($digestAlgorithm.ComputeHash($digestStream)).Replace('-', '')
} finally {
    $digestStream.Dispose()
    $digestAlgorithm.Dispose()
}
@{
    exit_code = $process.ExitCode
    pid = $process.Id
    graphics = $config.graphics
    executable = $exe
    executable_sha256 = $digest
    lighting = $lighting
    instant_replay = $InstantReplay
    runtime_environment = $config.native.runtime_environment
    platform_visibility_trace = $env:MW34_PLATFORM_TRACE
    turret_aim_trace = $env:MW34_TURRET_AIM_LOG
} | ConvertTo-Json -Depth 6 | Set-Content "$run/run.json"
Write-Output "Native Remaster exit: $($process.ExitCode)"
exit $process.ExitCode
