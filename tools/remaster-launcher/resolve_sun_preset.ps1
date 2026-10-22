<#
.SYNOPSIS
Resolve one registered map/preset into validated native environment strings.
.DESCRIPTION
Read-only helper shared by launch paths. An explicit Preset overrides the
profile's default. The only success output is JSON; callers parse it rather
than evaluating script text. This helper does not set environment variables,
write profiles or start the game.
#>
param(
    [Parameter(Mandatory=$true)][string]$Profile,
    [string]$Preset = '',
    [string]$RuntimeRoot = '',
    [string]$CatalogPath = '',
    [string]$MapName = ''
)

$ErrorActionPreference = 'Stop'
$root = if ($RuntimeRoot) { [IO.Path]::GetFullPath($RuntimeRoot) } else { Split-Path (Split-Path $PSScriptRoot -Parent) -Parent }
$config = Get-Content -LiteralPath $Profile -Raw | ConvertFrom-Json
$selection = $config.native.sun_preset
if ($CatalogPath) {
    if (!$MapName -or !$Preset) { throw 'Explicit lighting catalog requires a map and preset.' }
    $selection = [pscustomobject]@{source=$CatalogPath;map=$MapName;default=$Preset}
}
if (!$selection) {
    throw 'This profile has no registered sun preset source'
}
$source = if ([IO.Path]::IsPathRooted([string]$selection.source)) {
    [string]$selection.source
} else {
    Join-Path $root ([string]$selection.source)
}
$catalog = Get-Content -LiteralPath $source -Raw | ConvertFrom-Json
$map = $catalog.maps.PSObject.Properties[[string]$selection.map]
if (!$map) {
    throw "No lighting presets for $($selection.map)"
}
$name = if ($Preset) {
    $Preset
} else {
    [string]$selection.default
}
$chosen = $map.Value.presets.PSObject.Properties[$name]
if (!$chosen) {
    throw "Unknown lighting preset '$name' for $($selection.map)"
}
$p = $chosen.Value

# Decimal points and comma-separated RGB values must not depend on Windows locale.
$culture = [Globalization.CultureInfo]::InvariantCulture
$environment = @{MW34_SUN='1';MW34_SKY_AUTO='1';MW34_NIGHT_WORLD_GAIN='1'}
if ($null -ne $p.sky_auto) {
    if ($p.sky_auto -isnot [bool]) {
        throw 'Invalid lighting field sky_auto'
    }
    $environment.MW34_SKY_AUTO = if ($p.sky_auto) {'1'} else {'0'}
}

# Each field tuple is (JSON name, environment name, minimum, maximum).
# Omit absent optional bindings so the native host can retain its defaults.
foreach ($field in @(
    @('sky_brightness','MW34_SKY_BRIGHTNESS',0,4),
    @('sky_glow','MW34_SKY_GLOW',0,4),
    @('night_world_gain','MW34_NIGHT_WORLD_GAIN',0,1)
)) {
    if ($null -eq $p.($field[0])) {
        continue
    }
    $value = [double]$p.($field[0])
    if ([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt $field[2] -or $value -gt $field[3]) {
        throw "Invalid lighting field $($field[0])"
    }
    $environment[$field[1]] = $value.ToString($culture)
}

# Sun angles are degrees; strength/ambient are bounded multipliers.
foreach ($field in @(
    @('azimuth','MW34_SUN_AZIMUTH',-360,360),
    @('elevation','MW34_SUN_ELEVATION',1,89),
    @('strength','MW34_SUN_STRENGTH',0,4),
    @('ambient','MW34_SUN_AMBIENT',0,2)
)) {
    if ($null -eq $p.($field[0])) {
        throw "Missing lighting field $($field[0])"
    }
    $value = [double]$p.($field[0])
    if ([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt $field[2] -or $value -gt $field[3]) {
        throw "Invalid lighting field $($field[0])"
    }
    $environment[$field[1]] = $value.ToString($culture)
}

# Required RGB gains allow HDR values up to 4. Haze is restricted to [0,1].
foreach ($field in @(
    @('sun_color','MW34_SUN_COLOR'),
    @('ambient_color','MW34_SUN_AMBIENT_COLOR'),
    @('sky_tint','MW34_SKY_TINT'),
    @('haze_color','MW34_HAZE_COLOR')
)) {
    if ($null -eq $p.($field[0]) -and $field[0] -in @('sky_tint','haze_color')) {
        continue
    }
    $values = @($p.($field[0]))
    if ($values.Count -ne 3) {
        throw "Invalid lighting color $($field[0])"
    }
    $parts = @(foreach ($component in $values) {
        $value = [double]$component
        $maximum = if ($field[0] -eq 'haze_color') {1} else {4}
        if ([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0 -or $value -gt $maximum) {
            throw "Invalid lighting color $($field[0])"
        }
        $value.ToString($culture)
    })
    $environment[$field[1]] = $parts -join ','
}

@{map=[string]$selection.map;preset=$name;environment=$environment} | ConvertTo-Json -Depth 4 -Compress
