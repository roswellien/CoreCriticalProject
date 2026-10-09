param(
    [Parameter(Mandatory=$true)][string]$CaptureRun,
    [string]$Executable = "build/vulkan-replay/Release/mw34_vulkan_replay.exe",
    [string]$Compiler = "local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe"
)
$ErrorActionPreference = 'Stop'
Push-Location (Resolve-Path "$PSScriptRoot/../..").Path
$oldLayers = $env:VK_LAYER_PATH
$oldImplicit = $env:VK_IMPLICIT_LAYER_PATH
try {
    python tools/graphics-trace/verify_filtering.py $CaptureRun | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Legacy evidence rejected' }
    $destination = "$CaptureRun/edge-experiments"
    New-Item -ItemType Directory -Force $destination | Out-Null
    python tools/graphics-trace/package_replay.py "$CaptureRun/frame" "$destination/scene.replay" --filter-source legacy | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Capture profile rejected' }
    $env:VK_LAYER_PATH = (Resolve-Path local/tools/vulkan-sdk-portable/Bin).Path
    $env:VK_IMPLICIT_LAYER_PATH = (New-Item -ItemType Directory -Force local/tools/empty-implicit-layers).FullName
    $variants = @(
        @{name='baseline';defines=@();offset='0.5'},
        @{name='offset-0.49';defines=@();offset='0.49'},
        @{name='offset-0.51';defines=@();offset='0.51'},
        @{name='snap-16';defines=@('-DSNAP_GRID=16');offset='0.5'},
        @{name='snap-256';defines=@('-DSNAP_GRID=256');offset='0.5'},
        @{name='rgb565-before-blend';defines=@('-DQUANTIZE_565=1');offset='0.5'},
        @{name='dither4-before-blend';defines=@('-DQUANTIZE_565=1','-DDITHER_4X4=1');offset='0.5'}
    )
    $metrics = @()
    foreach ($variant in $variants) {
        $name = $variant.name
        $directory = "$destination/$name"
        New-Item -ItemType Directory -Force $directory | Out-Null
        $defines = $variant.defines
        foreach ($stage in @('vert','frag')) {
            foreach ($flat in @($false,$true)) {
                $arguments = @('-V') + $defines
                $prefix = 'replay'
                if ($flat) { $arguments += '-DFLAT_SHADE=1'; $prefix = 'replay-flat' }
                & $Compiler @arguments "tools/vulkan-probe/replay.$stage" -o "$directory/$prefix.$stage.spv" | Out-Null
                if ($LASTEXITCODE -ne 0) { throw "Shader compile failed: $name" }
            }
        }
        $candidate = "$directory/output.ppm"
        & $Executable "$destination/scene.replay" $directory $candidate $variant.offset captured 1 d32 2>&1 |
            Tee-Object "$directory/run.txt"
        if ($LASTEXITCODE -ne 0) { throw "Replay/validation failed: $name" }
        $report = python tools/graphics-trace/compare_replay.py "$CaptureRun/preview/final_target.png" $candidate "$directory/difference.png"
        if ($LASTEXITCODE -ne 0) { throw "Comparison failed: $name" }
        $report | Set-Content -Encoding utf8 "$directory/comparison.json"
        $metric = $report | ConvertFrom-Json
        $metrics += @{experiment=$name;mean_error=$metric.mean_absolute_channel_error;outliers=$metric.pixels_exceeding_8_per_channel;exact_pixels=$metric.exact_pixels;maximum_error=$metric.maximum_channel_error}
    }
    foreach ($offset in @('0.5','0.16666667')) {
        $candidate = "$destination/scale3-$offset.ppm"
        & $Executable "$destination/scene.replay" "$destination/baseline" $candidate $offset captured 3 d32 2>&1 |
            Tee-Object "$destination/scale3-$offset-run.txt"
        if ($LASTEXITCODE -ne 0) { throw 'Scaled replay/validation failed' }
        foreach ($filter in @('nearest','box','bilinear')) {
            $name = "scale3-$offset-$filter"
            $report = python tools/graphics-trace/compare_replay.py "$CaptureRun/preview/final_target.png" $candidate "$destination/$name-difference.png" --resize-filter $filter
            if ($LASTEXITCODE -ne 0) { throw 'Scaled comparison failed' }
            $report | Set-Content -Encoding utf8 "$destination/$name-comparison.json"
            $metric = $report | ConvertFrom-Json
            $metrics += @{experiment=$name;mean_error=$metric.mean_absolute_channel_error;outliers=$metric.pixels_exceeding_8_per_channel;exact_pixels=$metric.exact_pixels;maximum_error=$metric.maximum_channel_error}
        }
    }
    $metrics | ConvertTo-Json | Tee-Object "$destination/summary.json"
    $files = @($Executable,$Compiler,'tools/vulkan-probe/replay.cpp','tools/vulkan-probe/replay_scene.hpp',
        'tools/vulkan-probe/replay.vert','tools/vulkan-probe/replay.frag','tools/vulkan-probe/run-edge-experiments.ps1',
        'tools/graphics-trace/compare_replay.py','tools/graphics-trace/package_replay.py',"$destination/scene.replay", "$CaptureRun/preview/final_target.png", "$CaptureRun/frame/capture.jsonl")
    $files += (Get-ChildItem -LiteralPath $destination -Filter *.spv -Recurse).FullName
    $files | ForEach-Object { @{path=$_;sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()} } |
        ConvertTo-Json | Set-Content -Encoding utf8 "$destination/provenance.json"
} finally {
    $env:VK_LAYER_PATH = $oldLayers
    $env:VK_IMPLICIT_LAYER_PATH = $oldImplicit
    Pop-Location
}
