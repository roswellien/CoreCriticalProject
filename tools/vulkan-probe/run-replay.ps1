param(
    [Parameter(Mandatory=$true)][string]$CaptureRun,
    [ValidateSet('stage','legacy')][string]$FilterSource = 'stage',
    [ValidateSet('d32','d16')][string]$DepthMode = 'd32',
    [ValidateSet('rgba8','rgb565')][string]$ColorMode = 'rgba8',
    [string]$Executable = "build/vulkan-replay/Release/mw34_vulkan_replay.exe",
    [string]$ShaderDirectory = "build/vulkan-replay"
)
$ErrorActionPreference = "Stop"
$taskRoot = (Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $taskRoot
$previousLayerPath = $env:VK_LAYER_PATH
$previousImplicitPath = $env:VK_IMPLICIT_LAYER_PATH
try {
    if ($FilterSource -eq 'legacy') {
        python tools/graphics-trace/verify_filtering.py $CaptureRun |
            Tee-Object "$CaptureRun/filtering-verification.json"
        if ($LASTEXITCODE -ne 0) { throw "Legacy filtering evidence rejected" }
    }
    python tools/graphics-trace/package_replay.py "$CaptureRun/frame" "$CaptureRun/scene.replay" --filter-source $FilterSource
    if ($LASTEXITCODE -ne 0) { throw "Capture profile rejected" }
    $env:VK_LAYER_PATH = (Resolve-Path local/tools/vulkan-sdk-portable/Bin).Path
    $env:VK_IMPLICIT_LAYER_PATH = (New-Item -ItemType Directory -Force local/tools/empty-implicit-layers).FullName
    New-Item -ItemType Directory -Force "$CaptureRun/preview" | Out-Null
    python tools/graphics-trace/describe_capture.py "$CaptureRun/frame" "$CaptureRun/preview"
    if ($LASTEXITCODE -ne 0) { throw "Capture decode failed" }
    foreach ($offset in @('0','0.5')) {
        $candidate = "$CaptureRun/preview/vulkan-$offset.ppm"
        & $Executable "$CaptureRun/scene.replay" $ShaderDirectory $candidate $offset captured 1 $DepthMode $ColorMode 2>&1 |
            Tee-Object "$CaptureRun/replay-$offset.txt"
        if ($LASTEXITCODE -ne 0) { throw "Replay/validation failed" }
        python tools/graphics-trace/compare_replay.py "$CaptureRun/preview/final_target.png" $candidate "$CaptureRun/preview/difference-$offset.png" --initial-reference "$CaptureRun/preview/initial_target.png" |
            Tee-Object "$CaptureRun/comparison-$offset.json"
        if ($LASTEXITCODE -ne 0) { throw "Comparison failed" }
    }
} finally {
    $env:VK_LAYER_PATH = $previousLayerPath
    $env:VK_IMPLICIT_LAYER_PATH = $previousImplicitPath
    Pop-Location
}
