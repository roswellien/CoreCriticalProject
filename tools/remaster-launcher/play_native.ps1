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

function Read-LegacyJsonString {
    param([string]$Json, [ref]$Position, [bool]$DecodeName)
    $length = $Json.Length
    $index = [int]$Position.Value
    $quote = $Json[$index]
    $index++
    # Values need lexical boundaries only; never retain their contents.
    if (-not $DecodeName) {
        while ($index -lt $length) {
            if ($Json[$index] -ceq $quote) { $Position.Value = $index + 1; return '' }
            if ($Json[$index] -ceq '\') { $index++ }
            $index++
        }
        throw 'Invalid legacy JSON string'
    }
    $coreRuntime = $PSVersionTable.PSEdition -ne 'Desktop'
    $name = [Text.StringBuilder]::new()
    while ($index -lt $length) {
        $character = $Json[$index]
        if ($character -ceq $quote) {
            $Position.Value = $index + 1
            if ($coreRuntime) { return $name.ToString() }
            # Desktop's converter replaces unpaired units after unescaping.
            $decoded = $name.ToString()
            $legacyName = [Text.StringBuilder]::new()
            for ($unitIndex = 0; $unitIndex -lt $decoded.Length; $unitIndex++) {
                $unit = $decoded[$unitIndex]
                if ([char]::IsHighSurrogate($unit) -and $unitIndex + 1 -lt $decoded.Length -and
                    [char]::IsLowSurrogate($decoded[$unitIndex + 1])) {
                    [void]$legacyName.Append($unit)
                    $unitIndex++
                    [void]$legacyName.Append($decoded[$unitIndex])
                } elseif ([char]::IsSurrogate($unit)) {
                    [void]$legacyName.Append([char]0xFFFD)
                } else { [void]$legacyName.Append($unit) }
            }
            return $legacyName.ToString()
        }
        if ($character -cne '\') {
            [void]$name.Append($character)
            $index++
            continue
        }
        $index++
        if ($index -ge $length) { throw 'Invalid legacy JSON string' }
        $escape = $Json[$index]
        if ($escape -ceq 'u') {
            if ($index + 4 -ge $length) { throw 'Invalid legacy JSON string' }
            $unit = 0
            for ($digit = 1; $digit -le 4; $digit++) {
                $hex = [int][char]$Json[$index + $digit]
                if ($hex -ge 48 -and $hex -le 57) { $value = $hex - 48 }
                elseif ($hex -ge 65 -and $hex -le 70) { $value = $hex - 55 }
                elseif ($hex -ge 97 -and $hex -le 102) { $value = $hex - 87 }
                else { throw 'Invalid legacy JSON string' }
                $unit = $unit * 16 + $value
            }
            $index += 5
            if ($coreRuntime -and [char]::IsHighSurrogate([char]$unit)) {
                $paired = $false
                if ($index + 5 -lt $length -and $Json[$index] -ceq '\' -and $Json[$index + 1] -ceq 'u') {
                    $low = 0
                    $valid = $true
                    for ($digit = 2; $digit -le 5; $digit++) {
                        $hex = [int][char]$Json[$index + $digit]
                        if ($hex -ge 48 -and $hex -le 57) { $value = $hex - 48 }
                        elseif ($hex -ge 65 -and $hex -le 70) { $value = $hex - 55 }
                        elseif ($hex -ge 97 -and $hex -le 102) { $value = $hex - 87 }
                        else { $valid = $false; break }
                        $low = $low * 16 + $value
                    }
                    if ($valid -and [char]::IsLowSurrogate([char]$low)) {
                        [void]$name.Append([char]$unit)
                        [void]$name.Append([char]$low)
                        $index += 6
                        $paired = $true
                    }
                }
                if (-not $paired) { [void]$name.Append([char]0xFFFD) }
            } elseif ($coreRuntime -and [char]::IsLowSurrogate([char]$unit)) {
                [void]$name.Append([char]0xFFFD)
            } else { [void]$name.Append([char]$unit) }
            continue
        }
        switch -CaseSensitive ($escape) {
            '"' { [void]$name.Append('"') }
            "'" { [void]$name.Append("'") }
            '\' { [void]$name.Append('\') }
            '/' { [void]$name.Append('/') }
            'b' { [void]$name.Append([char]8) }
            'f' { [void]$name.Append([char]12) }
            'n' { [void]$name.Append([char]10) }
            'r' { [void]$name.Append([char]13) }
            't' { [void]$name.Append([char]9) }
            default { throw 'Invalid legacy JSON string' }
        }
        $index++
    }
    throw 'Invalid legacy JSON string'
}

function Assert-UniqueLegacyJson {
    param([string]$Json)
    if ([Text.Encoding]::UTF8.GetByteCount($Json) -gt 2097152) { throw 'Legacy profile JSON is too large' }
    $frames = [Collections.Generic.List[object]]::new()
    $index = 0
    while ($index -lt $Json.Length) {
        $character = $Json[$index]
        if ([char]::IsWhiteSpace($character)) { $index++; continue }
        if ($character -ceq '/' -and $index + 1 -lt $Json.Length) {
            if ($Json[$index + 1] -ceq '/') {
                $index += 2
                while ($index -lt $Json.Length -and $Json[$index] -notin @([char]10, [char]13)) { $index++ }
                continue
            }
            if ($Json[$index + 1] -ceq '*') {
                $index += 2
                while ($index + 1 -lt $Json.Length -and -not ($Json[$index] -ceq '*' -and $Json[$index + 1] -ceq '/')) { $index++ }
                if ($index + 1 -ge $Json.Length) { throw 'Invalid legacy JSON comment' }
                $index += 2
                continue
            }
        }
        $frame = if ($frames.Count) { $frames[$frames.Count - 1] } else { $null }
        if ($null -ne $frame -and $frame.Kind -ceq '{' -and $frame.Phase -ceq 'key' -and $character -cne '}') {
            if ($character -ceq '"' -or $character -ceq "'") {
                $name = Read-LegacyJsonString $Json ([ref]$index) $true
            } else {
                $start = $index
                while ($index -lt $Json.Length -and -not [char]::IsWhiteSpace($Json[$index]) -and
                    -not '{}[]():,\"''/'.Contains([string]$Json[$index])) { $index++ }
                if ($index -eq $start) { throw 'Invalid legacy JSON member' }
                $name = $Json.Substring($start, $index - $start)
            }
            if (-not $frame.Names.Add($name)) { throw 'Duplicate JSON property' }
            $frame.Phase = 'colon'
            continue
        }
        if ($null -ne $frame -and $frame.Kind -ceq '{' -and $frame.Phase -ceq 'colon') {
            if ($character -cne ':') { throw 'Invalid legacy JSON member' }
            $frame.Phase = 'value'
            $index++
            continue
        }
        if ($character -ceq '"' -or $character -ceq "'") {
            $null = Read-LegacyJsonString $Json ([ref]$index) $false
            continue
        }
        if ('{[('.Contains([string]$character)) {
            if ($frames.Count -ge 64) { throw 'Legacy profile JSON exceeds depth limit' }
            $names = $null
            if ($character -ceq '{') { $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal) }
            $frames.Add([pscustomobject]@{Kind=$character; Phase='key'; Names=$names})
        } elseif ('}])'.Contains([string]$character)) {
            $expected = switch ($character) { '}' { '{' } ']' { '[' } ')' { '(' } }
            if ($null -eq $frame -or $frame.Kind -cne $expected -or $frame.Phase -ceq 'colon') {
                throw 'Invalid legacy JSON container'
            }
            $frames.RemoveAt($frames.Count - 1)
        } elseif ($character -ceq ',' -and $null -ne $frame -and $frame.Kind -ceq '{') {
            $frame.Phase = 'key'
        }
        $index++
    }
    if ($frames.Count) { throw 'Invalid legacy JSON container' }
}

function Read-LegacyProfileSnapshot {
    param([string]$Path)
    $limit = 2097152
    $buffer = New-Object byte[] ($limit + 1)
    $count = 0
    $stream = [IO.File]::OpenRead($Path)
    try {
        while ($count -lt $buffer.Length) {
            $read = $stream.Read($buffer, $count, $buffer.Length - $count)
            if ($read -le 0) { break }
            $count += $read
        }
        if ($count -gt $limit) { throw 'Legacy profile snapshot is too large.' }
    } finally { $stream.Dispose() }
    $memory = [IO.MemoryStream]::new($buffer, 0, $count, $false)
    try {
        $reader = [IO.StreamReader]::new($memory, [Text.Encoding]::UTF8, $true)
        try { $text = $reader.ReadToEnd() }
        finally { $reader.Dispose() }
    } finally { $memory.Dispose() }
    if ([Text.Encoding]::UTF8.GetByteCount($text) -gt $limit) { throw 'Legacy profile snapshot is too large.' }
    return $text
}

function ConvertFrom-LegacyLaunchProfile {
    param([string]$Json)
    Assert-UniqueLegacyJson $Json
    try { $config = ConvertFrom-Json -InputObject $Json }
    catch { throw [IO.InvalidDataException]::new('Invalid legacy profile JSON') }
    if ($config -isnot [System.Management.Automation.PSCustomObject]) {
        throw 'Legacy routing requires a JSON object'
    }
    foreach ($property in $config.PSObject.Properties) {
        if ($property.Name -ieq 'engine') { throw 'Legacy routing rejects an explicit engine' }
        if ($property.Name -ieq 'schema_version' -and
            ($property.Name -cne 'schema_version' -or
             ($property.Value -isnot [int] -and $property.Value -isnot [long]) -or $property.Value -ne 1)) {
            throw 'Unsupported legacy routing schema'
        }
        if ($property.Name -ieq 'native') {
            foreach ($binding in $property.Value.PSObject.Properties) {
                if ($binding.Name -ieq 'engine') { throw 'Legacy routing rejects native.engine' }
            }
        }
    }
    return $config
}

$taskRoot = if ($RuntimeRoot) { [IO.Path]::GetFullPath($RuntimeRoot) } else { Split-Path (Split-Path $PSScriptRoot -Parent) -Parent }
$profilePath = if ([IO.Path]::IsPathRooted($Profile)) { $Profile } else { Join-Path $taskRoot $Profile }
$config = ConvertFrom-LegacyLaunchProfile (Read-LegacyProfileSnapshot $profilePath)
Set-Location $taskRoot
$active = Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('entry_commandline.exe','Mech3.exe')}
if ($active) {
    throw "A game session is already running (PID $($active.ProcessId -join ', '))."
}

# Profile bindings affect this coordinator and its child, never machine/user settings.
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
$presentationOff = $null -ne $config.native.presentation -and $config.native.presentation.dynamic_lighting -eq $false
if ($presentationOff -and $LightingPreset) {
    throw 'Lighting presets require Dynamic Lighting to be enabled'
}
if (!$presentationOff -and ($config.native.sun_preset -or $LightingPreset)) {
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
