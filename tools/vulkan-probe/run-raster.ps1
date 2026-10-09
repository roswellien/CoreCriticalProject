param(
    [string]$Executable = "build/vulkan-probe/mw34_vulkan_raster.exe",
    [string]$ShaderDirectory = "build/vulkan-probe",
    [string]$LayerDirectory = "local/tools/vulkan-sdk-portable/Bin",
    [string]$OutputDirectory = "reports/vulkan-probe"
)
$ErrorActionPreference = "Stop"
$taskRoot = (Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $taskRoot
$previousLayerPath = $env:VK_LAYER_PATH
$previousImplicitPath = $env:VK_IMPLICIT_LAYER_PATH
try {
    $env:VK_LAYER_PATH = (Resolve-Path $LayerDirectory).Path
    # Isolate this child process from installed game/recording overlays.
    $emptyLayers = New-Item -ItemType Directory -Force "local/tools/empty-implicit-layers"
    $env:VK_IMPLICIT_LAYER_PATH = $emptyLayers.FullName
    New-Item -ItemType Directory -Force $OutputDirectory | Out-Null
    foreach ($mode in @("default", "depth-off", "fog-off", "opaque-front")) {
        $ppm = Join-Path $OutputDirectory "raster-$mode.ppm"
        & $Executable "$ShaderDirectory/scene.vert.spv" "$ShaderDirectory/scene.frag.spv" $ppm $mode 2>&1 |
            Tee-Object (Join-Path $OutputDirectory "raster-$mode-run.txt")
        if ($LASTEXITCODE -ne 0) { throw "Raster/validation failed: $mode" }
        python "$PSScriptRoot/verify_raster.py" $ppm --mode $mode |
            Tee-Object (Join-Path $OutputDirectory "raster-$mode-verification.json")
        if ($LASTEXITCODE -ne 0) { throw "Pixel oracle failed: $mode" }
    }
} finally {
    $env:VK_LAYER_PATH = $previousLayerPath
    $env:VK_IMPLICIT_LAYER_PATH = $previousImplicitPath
    Pop-Location
}
