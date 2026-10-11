param(
    [string]$CaptureRun = "reports/graphics-trace/20261009-055506-103",
    [double]$AutoCloseSeconds = 0,
    [switch]$SelfTest,
    [string]$BuildDirectory = 'build/vulkan-windowed'
)
$ErrorActionPreference = "Stop"
function Get-WindowedSha256([string]$Path) {
    $taskStream = [System.IO.File]::OpenRead($Path)
    $taskHasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.BitConverter]::ToString($taskHasher.ComputeHash($taskStream)).Replace("-", "").ToLowerInvariant()
    } finally {
        $taskHasher.Dispose()
        $taskStream.Dispose()
    }
}
$taskRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$taskPython = "C:/Python314/python.exe"
$taskShaders = (Resolve-Path (Join-Path $taskRoot $BuildDirectory)).Path
$taskViewer = Join-Path $taskShaders "Release/mw34_vulkan_windowed.exe"
$taskReportRoot = Join-Path $taskRoot "reports/vulkan-windowed"
$taskRunId = (Get-Date -Format "yyyyMMdd-HHmmss-fff") + "-" + [guid]::NewGuid().ToString("N").Substring(0,8)
$taskOutput = Join-Path $taskReportRoot $taskRunId
$taskPreviousLayer = $env:VK_LAYER_PATH
$taskPreviousImplicit = $env:VK_IMPLICIT_LAYER_PATH
$taskPassed = $false
$taskStarted = Get-Date
$taskResult = $null
New-Item -ItemType Directory -Path $taskOutput | Out-Null
Push-Location $taskRoot
try {
    if (-not (Test-Path -LiteralPath $taskViewer -PathType Leaf)) {
        throw "Build the Vulkan windowed viewer first; see tools/vulkan-windowed/README.md."
    }
    $taskCapture = (Resolve-Path -LiteralPath $CaptureRun).Path
    & $taskPython -B tools/graphics-trace/verify_filtering.py $taskCapture |
        Out-File "$taskOutput/filtering-verification.json" -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw "Captured filtering evidence rejected." }
    & $taskPython -B tools/graphics-trace/package_replay.py "$taskCapture/frame" "$taskOutput/scene.replay" --filter-source legacy |
        Out-File "$taskOutput/package-log.json" -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw "Captured scene profile rejected." }
    $taskPins = @{}
    $taskPinFiles = @(
        $taskViewer, "$taskOutput/scene.replay", "$taskOutput/scene.json",
        "$taskCapture/frame/capture.jsonl", "$taskCapture/game.jsonl",
        "$taskCapture/wrapper-config.json", "$taskCapture/dgVoodoo.conf",
        "$PSScriptRoot/viewer.cpp", "$PSScriptRoot/presenter.hpp", "$PSScriptRoot/run.ps1", "$PSScriptRoot/verify.py",
        "$PSScriptRoot/CMakeLists.txt", "$taskRoot/tools/vulkan-probe/replay_scene.hpp",
        "$taskRoot/tools/vulkan-probe/ordered_commands.inc",
        "$taskRoot/tools/vulkan-probe/replay.vert", "$taskRoot/tools/vulkan-probe/replay.frag",
        "$taskRoot/tools/graphics-trace/package_replay.py", "$taskRoot/tools/graphics-trace/verify_filtering.py",
        "$taskRoot/tools/graphics-trace/verify_capture.py", "$taskRoot/tools/graphics-trace/verify.py",
        "$taskRoot/local/tools/vulkan-sdk-portable/Bin/VkLayer_khronos_validation.dll"
    ) + @(Get-ChildItem -LiteralPath $taskShaders -Filter "replay*.spv" | ForEach-Object FullName) +
        @(Get-ChildItem -LiteralPath "$taskCapture/frame" -Filter "*.bin" | ForEach-Object FullName)
    foreach ($taskFile in $taskPinFiles) {
        $taskFullPath = (Resolve-Path -LiteralPath $taskFile).Path
        $taskPins[$taskFullPath] = Get-WindowedSha256 $taskFullPath
    }
    $env:VK_LAYER_PATH = "$taskRoot/local/tools/vulkan-sdk-portable/Bin"
    $env:VK_IMPLICIT_LAYER_PATH = (New-Item -ItemType Directory -Path "$taskOutput/empty-implicit-layers").FullName
    $taskArguments = @("$taskOutput/scene.replay", $taskShaders, "$taskOutput/replay.ppm",
                       $AutoCloseSeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture))
    if ($SelfTest) { $taskArguments += "self-test" }
    @{
        status = "running"; wrapper_pid = $PID; started = $taskStarted.ToString("o")
        capture = $taskCapture; output = $taskOutput; executable = $taskViewer
        self_test = [bool]$SelfTest; files = $taskPins
        powershell_version = $PSVersionTable.PSVersion.ToString()
    } | ConvertTo-Json -Depth 5 | Out-File "$taskOutput/launch.json" -Encoding utf8
    Write-Output "Windowed Vulkan replay: $taskOutput"
    & $taskViewer @taskArguments 2>&1 | ForEach-Object {
        $taskLineText = $_.ToString()
        Add-Content -LiteralPath "$taskOutput/run.txt" -Value $taskLineText -Encoding utf8
        Write-Output $taskLineText
    }
    $taskExit = $LASTEXITCODE
    if ($taskExit -ne 0) { throw "Windowed replay exited with code $taskExit." }
    $taskLine = Get-Content "$taskOutput/run.txt" | Where-Object { $_ -like "WINDOWED_RESULT: *" } | Select-Object -Last 1
    if (-not $taskLine) { throw "Missing windowed completion receipt." }
    $taskResult = $taskLine.Substring("WINDOWED_RESULT: ".Length) | ConvertFrom-Json
    if ($taskResult.validation_messages -ne 0 -or -not $taskResult.resources_released -or
        -not $taskResult.window_destroyed -or $taskResult.presented_frames -lt 1) {
        throw "Windowed completion checks failed."
    }
    foreach ($taskFile in $taskPins.Keys) {
        if ((Get-WindowedSha256 $taskFile) -ne $taskPins[$taskFile]) {
            throw "A windowed replay input changed during execution: $taskFile"
        }
    }
    $taskPassed = $true
} catch {
    $_ | Out-String | Out-File "$taskOutput/failure.txt" -Encoding utf8
    throw
} finally {
    @{
        passed = $taskPassed; started = $taskStarted.ToString("o"); finished = (Get-Date).ToString("o")
        capture = $taskCapture; result = $taskResult; files = $taskPins
        full_frame_equivalence = $false; native_gameplay = $false; initializer_credit = 0
        powershell_version = $PSVersionTable.PSVersion.ToString()
    } | ConvertTo-Json -Depth 8 | Out-File "$taskOutput/report.json" -Encoding utf8
    $env:VK_LAYER_PATH = $taskPreviousLayer
    $env:VK_IMPLICIT_LAYER_PATH = $taskPreviousImplicit
    Pop-Location
}
if ($taskPassed) {
    & $taskPython -B "$PSScriptRoot/verify.py" $taskOutput
    if ($LASTEXITCODE -ne 0) { throw "Independent presentation verification failed; inspect $taskOutput." }
}
