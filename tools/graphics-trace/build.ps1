param(
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Game = 'D:/Projects/MW34Recomp/MW3/Mech3.exe',
    [switch]$Launch,
    [switch]$Capture,
    [ValidateRange(0,36000)][int]$CaptureSkipScenes = 0,
    [ValidateRange(0,2048)][int]$CaptureMinimumDraws = 0
)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$taskGame = (Resolve-Path -LiteralPath $Game).Path
if ($Launch -and (Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $taskGame })) {
    throw 'Close the existing MW3 session before tracing'
}
$taskCmake = "$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$taskBuild = "$taskRoot/build/graphics-trace"
& $taskCmake -S $PSScriptRoot -B $taskBuild -G 'Visual Studio 18 2026' -A Win32
if ($LASTEXITCODE -ne 0) { throw 'Configure failed' }
& $taskCmake --build $taskBuild --config Release
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$taskRun = "$taskRoot/reports/graphics-trace/$(Get-Date -Format yyyyMMdd-HHmmss-fff)"
New-Item -ItemType Directory -Force $taskRun | Out-Null
$taskLauncher = "$taskBuild/Release/mw34_graphics_launcher.exe"
$taskDll = "$taskBuild/Release/mw34_graphics_trace.dll"
& $taskLauncher --selftest $taskGame $taskDll "$taskRun/selftest.jsonl"
if ($LASTEXITCODE -ne 0) { throw 'Typed trace selftests failed; game was not launched' }
$record = [ordered]@{
    schema_version = 1
    scope = 'bounded call-through graphics observations in original x86 MW3; no renderer replacement'
    game_sha256 = (Get-FileHash $taskGame -Algorithm SHA256).Hash.ToLowerInvariant()
    dll_sha256 = (Get-FileHash $taskDll -Algorithm SHA256).Hash.ToLowerInvariant()
    launcher_sha256 = (Get-FileHash $taskLauncher -Algorithm SHA256).Hash.ToLowerInvariant()
    sources = [ordered]@{}
}
foreach ($source in Get-ChildItem $PSScriptRoot -File) {
    $record.sources[$source.Name] = (Get-FileHash $source.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
foreach ($source in @('launcher.cpp','identity.hpp')) {
    $record.sources["shared/$source"] = (Get-FileHash "$PSScriptRoot/../in-game-hook/$source" -Algorithm SHA256).Hash.ToLowerInvariant()
}
$record | ConvertTo-Json -Depth 5 | Set-Content "$taskRun/build.json" -Encoding utf8
foreach ($sourceName in $record.sources.Keys) {
    $sourcePath = if ($sourceName.StartsWith('shared/')) { "$PSScriptRoot/../in-game-hook/$($sourceName.Substring(7))" } else { "$PSScriptRoot/$sourceName" }
    $snapshot = "$taskRun/sources/$sourceName"
    New-Item -ItemType Directory -Force (Split-Path $snapshot) | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $snapshot
}
New-Item -ItemType Directory -Force "$taskRun/binaries" | Out-Null
Copy-Item -LiteralPath $taskLauncher,$taskDll -Destination "$taskRun/binaries"
if ($Launch) {
    $taskConfig = Join-Path (Split-Path -LiteralPath $taskGame) 'dgVoodoo.conf'
    if (Test-Path -LiteralPath $taskConfig) {
        Copy-Item -LiteralPath $taskConfig -Destination "$taskRun/dgVoodoo.conf"
        @{ scope='App-local config file immediately before launch; effective runtime config unproven';
            sha256=(Get-FileHash -LiteralPath $taskConfig -Algorithm SHA256).Hash.ToLowerInvariant() } |
            ConvertTo-Json | Set-Content -Encoding utf8 "$taskRun/wrapper-config.json"
    }
}
if ($Capture) { "$CaptureSkipScenes $CaptureMinimumDraws" | Set-Content -Encoding ascii "$taskRun/capture.request" }
if ($Launch) {
    $arguments = '"{0}" "{1}" "{2}"' -f $taskGame, $taskDll, "$taskRun/game.jsonl"
    $child = Start-Process -FilePath $taskLauncher -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput "$taskRun/launcher.txt" -RedirectStandardError "$taskRun/launcher-error.txt"
    [ordered]@{ launcher_pid = $child.Id; run = $taskRun } | ConvertTo-Json | Set-Content "$taskRun/launch.json" -Encoding utf8
}
Write-Output "Graphics trace run: $taskRun"
