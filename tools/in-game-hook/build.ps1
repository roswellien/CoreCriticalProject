param(
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Game = 'D:/Projects/MW34Recomp/MW3/Mech3.exe',
    [switch]$Launch,
    [switch]$MonitoredLaunch
)
$ErrorActionPreference = 'Stop'
$mwRoot = (Resolve-Path "$PSScriptRoot/../..").Path
if ($Launch -and $MonitoredLaunch) { throw 'Choose -Launch or -MonitoredLaunch, not both' }
if ($Launch -or $MonitoredLaunch) {
    $mwGamePath = (Resolve-Path -LiteralPath $Game).Path
    if (Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $mwGamePath }) {
        throw 'Close the existing MW3 session before launching with the hook'
    }
}
$mwCmake = "$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
function Invoke-MW([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Tool failed: $Program ($LASTEXITCODE)" }
}
$mwBuild = "$mwRoot/build/in-game-hook"
Invoke-MW $mwCmake @('-S', $PSScriptRoot, '-B', $mwBuild, '-G', 'Visual Studio 18 2026', '-A', 'Win32')
Invoke-MW $mwCmake @('--build', $mwBuild, '--config', 'Release')
$mwRun = "$mwRoot/reports/mw3-in-game/$(Get-Date -Format 'yyyyMMdd-HHmmss-fff')"
New-Item -ItemType Directory -Force $mwRun | Out-Null
$mwLauncher = "$mwBuild/Release/mw34_hook_launcher.exe"
$mwDll = "$mwBuild/Release/mw34_helper_hook.dll"
Invoke-MW $mwLauncher @('--selftest', $Game, $mwDll, "$mwRun/selftest.jsonl")
$mwRecord = [ordered]@{
    schema_version = 1
    game_sha256 = (Get-FileHash -LiteralPath $Game -Algorithm SHA256).Hash.ToLowerInvariant()
    hook_sha256 = (Get-FileHash -LiteralPath $mwDll -Algorithm SHA256).Hash.ToLowerInvariant()
    launcher_sha256 = (Get-FileHash -LiteralPath $mwLauncher -Algorithm SHA256).Hash.ToLowerInvariant()
    scope = 'one authored x86 replacement in the original x86 game; native x64 G2 remains separate'
    source_hashes = [ordered]@{}
}
Get-ChildItem -LiteralPath $PSScriptRoot -File | Sort-Object Name | ForEach-Object {
    $mwRecord.source_hashes[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
$mwRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$mwRun/build.json" -Encoding utf8
if ($Launch) { Invoke-MW $mwLauncher @($Game, $mwDll, "$mwRun/game.jsonl") }
if ($MonitoredLaunch) {
    & "$mwRoot/tools/game-monitor/start.ps1" -Mode hook -Game $Game -HookRun $mwRun
}
Write-Output "Research run directory: $mwRun"
