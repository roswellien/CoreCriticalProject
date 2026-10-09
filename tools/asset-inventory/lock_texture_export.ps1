param(
    [Parameter(Mandatory = $true)][string]$SourcePath,
    [Parameter(Mandatory = $true)][string]$CandidatePath,
    [Parameter(Mandatory = $true)][string]$LockSpecPath,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [Parameter(Mandatory = $true)][string]$ReportPath,
    [string]$ResizedCandidatePath,
    [string]$SourceGridPath,
    [string]$LockMaskPath,
    [string]$CandidateColorPath,
    [string]$ProtectedLayerPath,
    [switch]$SourceAnchoredDetail,
    [ValidateRange(0.0, 1.0)][double]$DetailStrength = 0.5,
    [ValidateRange(1, 16)][int]$Scale = 4
)

# Deterministic compatibility restoration after creative image editing.
# Rectangles use source pixels, with exclusive right/bottom boundaries.
# This does not establish unknown UV mappings or original renderer equivalence.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$sourceFile = (Resolve-Path -LiteralPath $SourcePath).Path
$candidateFile = (Resolve-Path -LiteralPath $CandidatePath).Path
$specFile = (Resolve-Path -LiteralPath $LockSpecPath).Path
$localRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../local'))
$destinations = @($OutputPath, $ReportPath, $ResizedCandidatePath, $SourceGridPath, $LockMaskPath, $CandidateColorPath, $ProtectedLayerPath) | Where-Object { $_ }
$absoluteTargets = @()
foreach ($destination in $destinations) {
    $absolute = [IO.Path]::GetFullPath($destination)
    if (-not $absolute.StartsWith($localRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Outputs must stay under this project''s ignored local/ directory.'
    }
    if (Test-Path -LiteralPath $absolute) { throw "Output already exists: $absolute" }
    if ($absoluteTargets -contains $absolute) { throw 'Output paths must be distinct.' }
    $absoluteTargets += $absolute
    $ancestor = [IO.Path]::GetDirectoryName($absolute)
    while ($ancestor -and $ancestor.StartsWith($localRoot, [StringComparison]::OrdinalIgnoreCase)) {
        if ([IO.Directory]::Exists($ancestor) -and ([IO.File]::GetAttributes($ancestor) -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Output directories may not contain junctions or symlinks.'
        }
        $ancestor = [IO.Path]::GetDirectoryName($ancestor)
    }
}

$spec = Get-Content -LiteralPath $specFile -Raw | ConvertFrom-Json
$sourceHash = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
if ($spec.version -ne 1 -or $spec.source_sha256 -notmatch '^[a-fA-F0-9]{64}$' -or $spec.source_sha256.ToLowerInvariant() -ne $sourceHash) {
    throw 'Lock spec version or decoded source SHA256 does not match.'
}
function Test-Integer($Value) { return (($Value -is [int]) -or ($Value -is [long])) }
if (-not (Test-Integer $spec.border_pixels) -or $spec.border_pixels -lt 0) { throw 'border_pixels must be a nonnegative integer.' }
if ($null -eq $spec.regions -or $spec.regions -isnot [array]) { throw 'regions must be an array, including when empty.' }
foreach ($property in $spec.PSObject.Properties.Name) {
    if ($property -notin @('version', 'source_sha256', 'border_pixels', 'regions')) { throw "Unknown lock property: $property" }
}

Add-Type -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class MWTextureLock {
    public static byte[] Read(Bitmap bitmap) {
        BitmapData data = bitmap.LockBits(new Rectangle(0, 0, bitmap.Width, bitmap.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        try {
            byte[] bytes = new byte[checked(bitmap.Width * bitmap.Height * 4)];
            for (int y = 0; y < bitmap.Height; y++) Marshal.Copy(IntPtr.Add(data.Scan0, y * data.Stride), bytes, y * bitmap.Width * 4, bitmap.Width * 4);
            return bytes;
        } finally { bitmap.UnlockBits(data); }
    }
    public static Bitmap BitmapFrom(int width, int height, byte[] bytes) {
        Bitmap bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
        BitmapData data = bitmap.LockBits(new Rectangle(0, 0, width, height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        try {
            for (int y = 0; y < height; y++) Marshal.Copy(bytes, y * width * 4, IntPtr.Add(data.Scan0, y * data.Stride), width * 4);
        } finally { bitmap.UnlockBits(data); }
        return bitmap;
    }
    public static byte[] OpaqueRgb(byte[] bytes) {
        byte[] opaque = (byte[])bytes.Clone();
        for (int i = 3; i < opaque.Length; i += 4) opaque[i] = 255;
        return opaque;
    }
    public static byte[] RgbBytes(byte[] bgra) {
        byte[] rgb = new byte[bgra.Length / 4 * 3];
        for (int i = 0, j = 0; i < bgra.Length; i += 4, j += 3) {
            rgb[j] = bgra[i + 2]; rgb[j + 1] = bgra[i + 1]; rgb[j + 2] = bgra[i];
        }
        return rgb;
    }
    public static byte[] AnchoredDetail(byte[] baseline, byte[] candidate, int width, int height, int scale, double strength, double cap) {
        byte[] detail = (byte[])baseline.Clone();
        int outWidth = width * scale;
        for (int sy = 0; sy < height; sy++) for (int sx = 0; sx < width; sx++) {
            double[] means = new double[3];
            for (int y = 0; y < scale; y++) for (int x = 0; x < scale; x++) {
                int index = ((sy * scale + y) * outWidth + sx * scale + x) * 4;
                for (int channel = 0; channel < 3; channel++) means[channel] += candidate[index + channel];
            }
            for (int channel = 0; channel < 3; channel++) means[channel] /= scale * scale;
            for (int y = 0; y < scale; y++) for (int x = 0; x < scale; x++) {
                int index = ((sy * scale + y) * outWidth + sx * scale + x) * 4;
                for (int channel = 0; channel < 3; channel++) {
                    double residual = Math.Max(-cap, Math.Min(cap, candidate[index + channel] - means[channel]));
                    double value = Math.Round(baseline[index + channel] + strength * residual, MidpointRounding.AwayFromZero);
                    detail[index + channel] = (byte)Math.Max(0, Math.Min(255, value));
                }
            }
        }
        return detail;
    }
    public static byte[][] Apply(byte[] source, byte[] candidate, int width, int height, int scale, bool[] locked) {
        int outWidth = checked(width * scale), outHeight = checked(height * scale);
        byte[] result = (byte[])candidate.Clone(), grid = new byte[result.Length], mask = new byte[result.Length];
        byte[] color = (byte[])candidate.Clone(), protectedLayer = new byte[result.Length];
        for (int y = 0; y < outHeight; y++) for (int x = 0; x < outWidth; x++) {
            int cell = (y / scale) * width + x / scale, input = cell * 4, output = (y * outWidth + x) * 4;
            byte alpha = source[input + 3];
            for (int channel = 0; channel < 3; channel++) {
                grid[output + channel] = alpha == 0 ? (byte)0 : source[input + channel];
                if (alpha == 0) color[output + channel] = 0;
                if (locked[cell]) protectedLayer[output + channel] = grid[output + channel];
                if (alpha == 0) result[output + channel] = 0;
                else if (locked[cell]) result[output + channel] = source[input + channel];
                mask[output + channel] = locked[cell] ? (byte)255 : (byte)0;
            }
            result[output + 3] = grid[output + 3] = alpha;
            color[output + 3] = alpha;
            protectedLayer[output + 3] = locked[cell] ? alpha : (byte)0;
            mask[output + 3] = 255;
        }
        return new byte[][] { result, grid, mask, color, protectedLayer };
    }
    public static long[] Check(byte[] source, byte[] candidate, int width, int height, int scale, bool[] locked) {
        long alphaMismatches = 0, rgbMismatches = 0, zeroRgbMismatches = 0, protectedPixels = 0, zeroPixels = 0;
        int outWidth = width * scale, outHeight = height * scale;
        for (int y = 0; y < outHeight; y++) for (int x = 0; x < outWidth; x++) {
            int cell = (y / scale) * width + x / scale, input = cell * 4, output = (y * outWidth + x) * 4;
            byte alpha = source[input + 3];
            if (candidate[output + 3] != alpha) alphaMismatches++;
            if (locked[cell]) {
                protectedPixels++;
                for (int channel = 0; channel < 3; channel++) if (candidate[output + channel] != (alpha == 0 ? 0 : source[input + channel])) rgbMismatches++;
            }
            if (alpha == 0) {
                zeroPixels++;
                for (int channel = 0; channel < 3; channel++) if (candidate[output + channel] != 0) zeroRgbMismatches++;
            }
        }
        return new long[] { alphaMismatches, rgbMismatches, zeroRgbMismatches, protectedPixels, zeroPixels };
    }
}
'@ -ReferencedAssemblies @([Drawing.Bitmap].Assembly.Location, [Drawing.Color].Assembly.Location)

function Write-Png($Bitmap, [string]$Path) {
    $absolute = [IO.Path]::GetFullPath($Path)
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($absolute)) | Out-Null
    $stream = [IO.FileStream]::new($absolute, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try { $Bitmap.Save($stream, [Drawing.Imaging.ImageFormat]::Png) } finally { $stream.Dispose() }
}

function Resize-Rgb($Bitmap, [int]$Width, [int]$Height) {
    $target = [Drawing.Bitmap]::new($Width, $Height, [Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [Drawing.Graphics]::FromImage($target)
    $attributes = [Drawing.Imaging.ImageAttributes]::new()
    try {
        $graphics.CompositingMode = [Drawing.Drawing2D.CompositingMode]::SourceCopy
        $graphics.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
        $graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $attributes.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY)
        $graphics.DrawImage($Bitmap, [Drawing.Rectangle]::new(0, 0, $Width, $Height), 0, 0, $Bitmap.Width, $Bitmap.Height, [Drawing.GraphicsUnit]::Pixel, $attributes)
    } catch { $target.Dispose(); throw } finally { $graphics.Dispose(); $attributes.Dispose() }
    return $target
}

$source = [Drawing.Bitmap]::new($sourceFile)
try {
    $candidate = [Drawing.Bitmap]::new($candidateFile)
    try {
        if ([long]$source.Width * $candidate.Height -ne [long]$source.Height * $candidate.Width) {
            throw 'Creative candidate must preserve the source aspect ratio.'
        }
        $width = $source.Width * $Scale
        $height = $source.Height * $Scale
        if ([long]$width * $height -gt 16777216) { throw 'Export exceeds 16 million pixels.' }
        if ($spec.border_pixels * 2 -gt [Math]::Min($source.Width, $source.Height)) { throw 'Border exceeds half the shorter source edge.' }
        $locked = [bool[]]::new($source.Width * $source.Height)
        for ($y = 0; $y -lt $source.Height; $y++) {
            for ($x = 0; $x -lt $source.Width; $x++) {
                if ($x -lt $spec.border_pixels -or $y -lt $spec.border_pixels -or $x -ge $source.Width - $spec.border_pixels -or $y -ge $source.Height - $spec.border_pixels) {
                    $locked[$y * $source.Width + $x] = $true
                }
            }
        }
        foreach ($region in $spec.regions) {
            foreach ($property in $region.PSObject.Properties.Name) {
                if ($property -notin @('name', 'x', 'y', 'width', 'height')) { throw "Unknown region property: $property" }
            }
            if (-not $region.name -or -not (Test-Integer $region.x) -or -not (Test-Integer $region.y) -or -not (Test-Integer $region.width) -or -not (Test-Integer $region.height) -or $region.x -lt 0 -or $region.y -lt 0 -or $region.width -le 0 -or $region.height -le 0 -or [long]$region.x + $region.width -gt $source.Width -or [long]$region.y + $region.height -gt $source.Height) {
                throw 'Lock rectangle must have a name and positive integer bounds inside the source.'
            }
            for ($y = $region.y; $y -lt $region.y + $region.height; $y++) {
                for ($x = $region.x; $x -lt $region.x + $region.width; $x++) { $locked[$y * $source.Width + $x] = $true }
            }
        }
        $resized = Resize-Rgb $candidate $width $height
        try {
            $sourceBytes = [MWTextureLock]::Read($source)
            $resizedBytes = [MWTextureLock]::Read($resized)
            $colorBytes = $resizedBytes
            $detailRecord = [ordered]@{ enabled = $false }
            if ($SourceAnchoredDetail) {
                $opaqueSource = [MWTextureLock]::BitmapFrom($source.Width, $source.Height, [MWTextureLock]::OpaqueRgb($sourceBytes))
                try { $baseline = Resize-Rgb $opaqueSource $width $height } finally { $opaqueSource.Dispose() }
                try { $baselineBytes = [MWTextureLock]::Read($baseline) } finally { $baseline.Dispose() }
                $residualCap = 20
                $colorBytes = [MWTextureLock]::AnchoredDetail($baselineBytes, $resizedBytes, $source.Width, $source.Height, $Scale, $DetailStrength, $residualCap)
                $sha = [Security.Cryptography.SHA256]::Create()
                try { $baselineHash = [BitConverter]::ToString($sha.ComputeHash([MWTextureLock]::RgbBytes($baselineBytes))).Replace('-', '').ToLowerInvariant() } finally { $sha.Dispose() }
                $detailRecord = [ordered]@{
                    enabled = $true
                    formula = 'round-away-from-zero(clamp(bicubic-original-RGB + strength * clamp(resized-AI-RGB - mean-AI-RGB-in-source-pixel-cell, -20, 20), 0, 255)); then original alpha and exact RGB locks'
                    strength = $DetailStrength
                    residual_cap_per_channel = $residualCap
                    mean_cell_dimensions = @($Scale, $Scale)
                    baseline_policy = 'Source RGB made opaque before bicubic sizing; original alpha restored separately.'
                    baseline_rgb_sha256 = $baselineHash
                    baseline_rgb_hash_layout = 'row-major RGB8 without alpha, exact export canvas'
                }
            }
            $outputs = [MWTextureLock]::Apply($sourceBytes, $colorBytes, $source.Width, $source.Height, $Scale, $locked)
            $final = [MWTextureLock]::BitmapFrom($width, $height, $outputs[0])
            try { Write-Png $final $OutputPath } finally { $final.Dispose() }
            if ($ResizedCandidatePath) { Write-Png $resized $ResizedCandidatePath }
            if ($SourceGridPath) {
                $grid = [MWTextureLock]::BitmapFrom($width, $height, $outputs[1])
                try { Write-Png $grid $SourceGridPath } finally { $grid.Dispose() }
            }
            if ($LockMaskPath) {
                $mask = [MWTextureLock]::BitmapFrom($width, $height, $outputs[2])
                try { Write-Png $mask $LockMaskPath } finally { $mask.Dispose() }
            }
            if ($CandidateColorPath) {
                $color = [MWTextureLock]::BitmapFrom($width, $height, $outputs[3])
                try { Write-Png $color $CandidateColorPath } finally { $color.Dispose() }
            }
            if ($ProtectedLayerPath) {
                $protection = [MWTextureLock]::BitmapFrom($width, $height, $outputs[4])
                try { Write-Png $protection $ProtectedLayerPath } finally { $protection.Dispose() }
            }
            $saved = [Drawing.Bitmap]::new([IO.Path]::GetFullPath($OutputPath))
            try { $checks = [MWTextureLock]::Check($sourceBytes, [MWTextureLock]::Read($saved), $source.Width, $source.Height, $Scale, $locked) } finally { $saved.Dispose() }
            if ($checks[0] -or $checks[1] -or $checks[2]) { throw 'Saved export failed alpha/protected RGB/transparent RGB verification.' }
            $fileRecords = @()
            foreach ($path in @($OutputPath, $ResizedCandidatePath, $SourceGridPath, $LockMaskPath, $CandidateColorPath, $ProtectedLayerPath) | Where-Object { $_ }) {
                $fileRecords += [ordered]@{ path = [IO.Path]::GetFullPath($path); sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
            }
            $report = [ordered]@{
                schema_version = 1
                status = 'local-work-ahead; authored source locks pass; UV/render integration pending'
                source_path = $sourceFile
                source_sha256 = $sourceHash
                candidate_path = $candidateFile
                candidate_sha256 = (Get-FileHash -LiteralPath $candidateFile -Algorithm SHA256).Hash.ToLowerInvariant()
                lock_spec_path = $specFile
                lock_spec_sha256 = (Get-FileHash -LiteralPath $specFile -Algorithm SHA256).Hash.ToLowerInvariant()
                tool_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
                source_dimensions = @($source.Width, $source.Height)
                export_dimensions = @($width, $height)
                scale = $Scale
                rgb_resize = 'System.Drawing HighQualityBicubic, PixelOffsetHalf, SourceCopy, TileFlipXY'
                source_anchored_detail = $detailRecord
                alpha_policy = 'Every source alpha byte is repeated on the exact integer grid; alpha-zero RGB is black.'
                protected_rgb_policy = 'Source RGB is repeated by nearest grid inside named rectangles and source border.'
                border_pixels = $spec.border_pixels
                regions = @($spec.regions)
                alpha_mismatched_pixels = $checks[0]
                protected_rgb_mismatched_channels = $checks[1]
                transparent_rgb_mismatched_channels = $checks[2]
                protected_export_pixels = $checks[3]
                transparent_export_pixels = $checks[4]
                files = $fileRecords
            }
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($ReportPath))) | Out-Null
            $reportJson = ($report | ConvertTo-Json -Depth 8) + [Environment]::NewLine
            $stream = [IO.FileStream]::new([IO.Path]::GetFullPath($ReportPath), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
            try {
                $bytes = [Text.Encoding]::UTF8.GetBytes($reportJson)
                $stream.Write($bytes, 0, $bytes.Length)
            } finally { $stream.Dispose() }
            Write-Output $reportJson
        } finally { $resized.Dispose() }
    } finally { $candidate.Dispose() }
} finally { $source.Dispose() }
