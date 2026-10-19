Add-Type -AssemblyName System.Drawing

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$sourcePng = Join-Path $repoRoot "website\assets\plates\brand-mark.png"
$targetIco = Join-Path $PSScriptRoot "Assets\app-icon.ico"

if (-not (Test-Path (Split-Path $targetIco -Parent))) {
    New-Item -ItemType Directory -Path (Split-Path $targetIco -Parent) -Force | Out-Null
}

$src = [System.Drawing.Image]::FromFile($sourcePng)
$sizes = @(16, 24, 32, 48, 64, 128, 256)
$pngStreams = @()

foreach ($s in $sizes) {
    $bmp = New-Object System.Drawing.Bitmap $s, $s
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.Clear([System.Drawing.Color]::Transparent)
    $g.DrawImage($src, 0, 0, $s, $s)
    $g.Dispose()

    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    $pngStreams += $ms
}
$src.Dispose()

$fs = [System.IO.File]::Create($targetIco)
$bw = New-Object System.IO.BinaryWriter $fs

# Header: 6 bytes
$bw.Write([uint16]0) # Reserved
$bw.Write([uint16]1) # Type (1 = ICO)
$bw.Write([uint16]$sizes.Count) # Image Count

# Directory entries: 16 bytes each
$offset = 6 + ($sizes.Count * 16)
for ($i = 0; $i -lt $sizes.Count; $i++) {
    $s = $sizes[$i]
    $stream = $pngStreams[$i]
    $bytes = $stream.ToArray()

    $wByte = if ($s -ge 256) { [byte]0 } else { [byte]$s }
    $hByte = if ($s -ge 256) { [byte]0 } else { [byte]$s }
    $bw.Write($wByte)
    $bw.Write($hByte)
    $bw.Write([byte]0) # Colors
    $bw.Write([byte]0) # Reserved
    $bw.Write([uint16]1) # Planes
    $bw.Write([uint16]32) # BPP
    $bw.Write([uint32]$bytes.Length) # Image Size
    $bw.Write([uint32]$offset) # Image Offset

    $offset += $bytes.Length
}

# Image Data
for ($i = 0; $i -lt $sizes.Count; $i++) {
    $bytes = $pngStreams[$i].ToArray()
    $bw.Write($bytes)
    $pngStreams[$i].Dispose()
}

$bw.Flush()
$fs.Dispose()

$fileInfo = Get-Item $targetIco
Write-Host "Created $targetIco ($($fileInfo.Length) bytes)"
