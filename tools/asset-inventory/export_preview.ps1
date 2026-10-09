param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [Parameter(Mandatory = $true)][ValidateRange(1, 8192)][int]$Width,
    [Parameter(Mandatory = $true)][ValidateRange(1, 8192)][int]$Height,
    [ValidateSet('nearest', 'bicubic')][string]$Sampling = 'bicubic',
    [switch]$PreserveSourceAlpha
)

# Deterministic export sizing after built-in image generation, or baseline export.
# No content synthesis, sharpening, color adjustment or original overwrite.
# Optional original-alpha transfer keeps its exact values on an integer scale grid.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$sourcePath = (Resolve-Path -LiteralPath $InputPath).Path
$destinationPath = [IO.Path]::GetFullPath($OutputPath)
$localPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../local'))
if (-not $destinationPath.StartsWith($localPath + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must stay under this project''s ignored local/ directory.'
}
if (Test-Path -LiteralPath $destinationPath) { throw 'Output already exists.' }
$ancestor = [IO.Path]::GetDirectoryName($destinationPath)
while ($ancestor -and $ancestor.StartsWith($localPath, [StringComparison]::OrdinalIgnoreCase)) {
    if ([IO.Directory]::Exists($ancestor) -and ([IO.File]::GetAttributes($ancestor) -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Output directories may not contain junctions or symlinks.'
    }
    $ancestor = [IO.Path]::GetDirectoryName($ancestor)
}
$source = [Drawing.Bitmap]::new($sourcePath)
try {
    if ([long]$source.Width * $Height -ne [long]$source.Height * $Width) {
        throw 'Export must preserve the source aspect ratio.'
    }
    if ($PreserveSourceAlpha -and ($Width -lt $source.Width -or $Width % $source.Width -or $Height % $source.Height)) {
        throw 'Preserving source alpha requires an integer upscale.'
    }
    $target = [Drawing.Bitmap]::new($Width, $Height, [Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $graphics = [Drawing.Graphics]::FromImage($target)
        $attributes = [Drawing.Imaging.ImageAttributes]::new()
        try {
            $graphics.CompositingMode = [Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
            $graphics.InterpolationMode = if ($Sampling -eq 'nearest') {
                [Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
            } else {
                [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            }
            $attributes.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY)
            $rectangle = [Drawing.Rectangle]::new(0, 0, $Width, $Height)
            $graphics.DrawImage($source, $rectangle, 0, 0, $source.Width, $source.Height, [Drawing.GraphicsUnit]::Pixel, $attributes)
            if ($PreserveSourceAlpha) {
                $integerScale = [int]($Width / $source.Width)
                for ($y = 0; $y -lt $Height; $y++) {
                    for ($x = 0; $x -lt $Width; $x++) {
                        $pixel = $target.GetPixel($x, $y)
                        $sourceAlpha = $source.GetPixel([int][Math]::Floor($x / $integerScale), [int][Math]::Floor($y / $integerScale)).A
                        $target.SetPixel($x, $y, [Drawing.Color]::FromArgb($sourceAlpha, $pixel.R, $pixel.G, $pixel.B))
                    }
                }
            }
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destinationPath)) | Out-Null
            $stream = [IO.FileStream]::new($destinationPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
            try { $target.Save($stream, [Drawing.Imaging.ImageFormat]::Png) } finally { $stream.Dispose() }
        } finally { $graphics.Dispose(); $attributes.Dispose() }
    } finally { $target.Dispose() }
} finally { $source.Dispose() }
Write-Output $destinationPath
