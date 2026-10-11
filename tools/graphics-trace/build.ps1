param(
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Game = 'D:/Projects/MW34Recomp/MW3/Mech3.exe',
    [switch]$Launch,
    [switch]$CaptureHudText,
    [switch]$CaptureHudHeat,
    [ValidateRange(0,36000)][int]$CaptureHudSkipScenes = 0,
    [switch]$Capture,
    [switch]$CapturePresentation,
    [ValidateRange(0,36000)][int]$CaptureSkipFlips = 0,
    [ValidateRange(0,36000)][int]$CaptureSkipScenes = 0,
    [ValidateRange(0,2048)][int]$CaptureMinimumDraws = 0
)
$ErrorActionPreference = 'Stop'
if (!$CaptureHudText -and $CaptureHudSkipScenes -ne 0) { throw 'CaptureHudSkipScenes requires CaptureHudText.' }
if ($Capture -and $CapturePresentation) { throw 'Choose scene capture or presentation capture, not both.' }
if ($CapturePresentation -and ($CaptureSkipScenes -ne 0 -or $CaptureMinimumDraws -ne 0)) { throw 'Presentation capture uses CaptureSkipFlips; scene selection parameters do not apply.' }
if (!$CapturePresentation -and $CaptureSkipFlips -ne 0) { throw 'CaptureSkipFlips requires CapturePresentation.' }
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
if ($CapturePresentation) { "$CaptureSkipFlips" | Set-Content -Encoding ascii "$taskRun/present.request" }
if ($CaptureHudText) { "$CaptureHudSkipScenes" | Set-Content -Encoding ascii "$taskRun/hud-text.request" }
if ($CaptureHudHeat) { 'bounded heat display input observations' | Set-Content -Encoding ascii "$taskRun/hud-heat.request" }
if ($Launch) {
    $arguments = '"{0}" "{1}" "{2}"' -f $taskGame, $taskDll, "$taskRun/game.jsonl"
    $child = Start-Process -FilePath $taskLauncher -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput "$taskRun/launcher.txt" -RedirectStandardError "$taskRun/launcher-error.txt"
    [ordered]@{ launcher_pid = $child.Id; run = $taskRun } | ConvertTo-Json | Set-Content "$taskRun/launch.json" -Encoding utf8
    # Observe modules as soon as DirectDraw is loaded, before asking for gameplay.
    # Never substitute an inventory from another process or a later session.
    $taskModuleDeadline = (Get-Date).AddSeconds(15)
    do {
        $taskObservedGame = Get-Process -Name Mech3 -ErrorAction SilentlyContinue |
            Where-Object { $_.Path.Replace('/','\') -eq $taskGame.Replace('/','\') } | Select-Object -First 1
        if ($taskObservedGame) {
            $taskObservedModules = @($taskObservedGame.Modules)
            if ($taskObservedModules | Where-Object ModuleName -eq 'DDRAW.dll') {
                $taskInventory = @($taskObservedModules | ForEach-Object {
                    $taskModulePath = $_.FileName
                    # The module API can return System32 for a WOW64 image.
                    if ($taskModulePath.StartsWith("$env:WINDIR\System32\",[StringComparison]::OrdinalIgnoreCase)) {
                        $taskWowPath = "$env:WINDIR\SysWOW64\" + $taskModulePath.Substring(("$env:WINDIR\System32\").Length)
                        if (Test-Path -LiteralPath $taskWowPath) { $taskModulePath = $taskWowPath }
                    }
                    $taskModuleBytes = [IO.File]::ReadAllBytes($taskModulePath)
                    $taskHasher = [Security.Cryptography.SHA256]::Create()
                    try { $taskModuleHash = [BitConverter]::ToString($taskHasher.ComputeHash($taskModuleBytes)).Replace('-','').ToLowerInvariant() }
                    finally { $taskHasher.Dispose() }
                    [ordered]@{name=$_.ModuleName; path=$taskModulePath; reported_path=$_.FileName; base=$_.BaseAddress.ToInt64(); size=$_.ModuleMemorySize; file_sha256=$taskModuleHash}
                })
                ConvertTo-Json -InputObject $taskInventory -Depth 4 | Set-Content "$taskRun/modules.json" -Encoding utf8
                break
            }
        }
        Start-Sleep -Milliseconds 100
    } while ((Get-Date) -lt $taskModuleDeadline)
    if (!(Test-Path "$taskRun/modules.json")) { Write-Warning 'Runtime module inventory unavailable; this run cannot pass provider verification.' }
}
Write-Output "Graphics trace run: $taskRun"
