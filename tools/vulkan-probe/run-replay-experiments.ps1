param(
    [Parameter(Mandatory=$true)][string]$CaptureRun,
    [string]$Executable = "build/vulkan-replay/Release/mw34_vulkan_replay.exe",
    [string]$Compiler = "local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe"
)
$ErrorActionPreference = "Stop"
Push-Location (Resolve-Path "$PSScriptRoot/../..").Path
$previousLayerPath = $env:VK_LAYER_PATH
$previousImplicitPath = $env:VK_IMPLICIT_LAYER_PATH
try {
    python tools/graphics-trace/package_replay.py "$CaptureRun/frame" "$CaptureRun/scene.replay" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Capture profile rejected" }
    $destination = "$CaptureRun/experiments"
    New-Item -ItemType Directory -Force $destination | Out-Null
    $env:VK_LAYER_PATH = (Resolve-Path local/tools/vulkan-sdk-portable/Bin).Path
    $env:VK_IMPLICIT_LAYER_PATH = (New-Item -ItemType Directory -Force local/tools/empty-implicit-layers).FullName
    foreach ($variant in @('baseline','linear','affine','perspective-color')) {
        $shaderDirectory = "$destination/$variant"
        New-Item -ItemType Directory -Force $shaderDirectory | Out-Null
        $defines = @()
        if ($variant -eq 'affine') { $defines += '-DAFFINE_UV=1' }
        if ($variant -eq 'perspective-color') { $defines += '-DPERSPECTIVE_COLOR=1' }
        foreach ($stage in @('vert','frag')) {
            & $Compiler -V @defines "tools/vulkan-probe/replay.$stage" -o "$shaderDirectory/replay.$stage.spv" | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Shader compilation failed" }
            & $Compiler -V @defines -DFLAT_SHADE=1 "tools/vulkan-probe/replay.$stage" -o "$shaderDirectory/replay-flat.$stage.spv" | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Flat shader compilation failed" }
        }
        $sampling = if ($variant -eq 'linear') { 'linear' } else { 'nearest' }
        $candidate = "$destination/$variant.ppm"
        & $Executable "$CaptureRun/scene.replay" $shaderDirectory $candidate 0.5 $sampling 2>&1 |
            Tee-Object "$destination/$variant-run.txt"
        if ($LASTEXITCODE -ne 0) { throw "Replay validation failed" }
        python tools/graphics-trace/compare_replay.py "$CaptureRun/preview/final_target.png" $candidate "$destination/$variant-difference.png" |
            Tee-Object "$destination/$variant-comparison.json"
        if ($LASTEXITCODE -ne 0) { throw "Comparison failed" }
    }
    python tools/graphics-trace/compare_replay.py "$CaptureRun/preview/final_target.png" "$destination/linear.ppm" "$destination/linear-rgb565-difference.png" --rgb565 |
        Tee-Object "$destination/linear-rgb565-comparison.json"
    if ($LASTEXITCODE -ne 0) { throw "Quantization experiment failed" }
    $files = @($Executable,$Compiler,'tools/vulkan-probe/replay.cpp','tools/vulkan-probe/replay_scene.hpp',
        'tools/vulkan-probe/replay.vert','tools/vulkan-probe/replay.frag','tools/graphics-trace/compare_replay.py',
        'tools/graphics-trace/package_replay.py','tools/vulkan-probe/run-replay-experiments.ps1',"$CaptureRun/scene.replay")
    $files | ForEach-Object { @{ path=$_; sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLower() } } |
        ConvertTo-Json | Set-Content -Encoding utf8 "$destination/provenance.json"
} finally {
    $env:VK_LAYER_PATH = $previousLayerPath
    $env:VK_IMPLICIT_LAYER_PATH = $previousImplicitPath
    Pop-Location
}
