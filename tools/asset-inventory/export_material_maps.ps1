param(
    [Parameter(Mandatory = $true)][string]$HeightPath,
    [Parameter(Mandatory = $true)][Alias('AlbedoPath')][string]$ColorPath,
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectHeightSha256,
    [Parameter(Mandatory = $true)][Alias('ExpectAlbedoSha256')][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectColorSha256,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [ValidateSet('RedChannel', 'StrictGrayscale')][string]$HeightChannel = 'RedChannel',
    [ValidateRange(0.0, 128.0)][double]$Strength = 8.0,
    [ValidateRange(0, 4096)][int]$FlatBorderPixels = 4
)

# Deterministic data-map export from separately authored height artwork.
# Albedo is read for dimensions/identity only and is never modified.
# Gradients use target texel steps, image rows down, tangent Y up.
$ErrorActionPreference = 'Stop'
if ([double]::IsNaN($Strength) -or [double]::IsInfinity($Strength)) { throw 'Strength must be a finite value.' }
Add-Type -AssemblyName System.Drawing
$heightFile = (Resolve-Path -LiteralPath $HeightPath).Path
$colorFile = (Resolve-Path -LiteralPath $ColorPath).Path
$heightHash = (Get-FileHash -LiteralPath $heightFile -Algorithm SHA256).Hash.ToLowerInvariant()
$colorHash = (Get-FileHash -LiteralPath $colorFile -Algorithm SHA256).Hash.ToLowerInvariant()
if ($heightHash -ne $ExpectHeightSha256.ToLowerInvariant() -or $colorHash -ne $ExpectColorSha256.ToLowerInvariant()) {
    throw 'Height or approved albedo SHA256 does not match expected identity.'
}
$localRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../local'))
$outputRoot = [IO.Path]::GetFullPath($OutputDir)
if (-not $outputRoot.StartsWith($localRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Outputs must stay under this project''s ignored local/ directory.'
}
$targets = @('height.png', 'normal-plus-y.png', 'normal-minus-y.png', 'export-report.json') | ForEach-Object { Join-Path $outputRoot $_ }
foreach ($target in $targets) {
    if (Test-Path -LiteralPath $target) { throw "Output already exists: $target" }
}
$ancestor = $outputRoot
while ($ancestor -and $ancestor.StartsWith($localRoot, [StringComparison]::OrdinalIgnoreCase)) {
    if ([IO.Directory]::Exists($ancestor) -and ([IO.File]::GetAttributes($ancestor) -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Output directories may not contain junctions or symlinks.'
    }
    $ancestor = [IO.Path]::GetDirectoryName($ancestor)
}
function Assert-PngBounded([string]$Path) {
    if ((Get-Item -LiteralPath $Path).Length -gt 134217728) { throw 'Input exceeds 128 MiB.' }
    $stream = [IO.File]::OpenRead($Path)
    try {
        $header = [byte[]]::new(24)
        if ($stream.Read($header, 0, 24) -ne 24 -or [BitConverter]::ToString($header, 0, 8) -ne '89-50-4E-47-0D-0A-1A-0A' -or [Text.Encoding]::ASCII.GetString($header, 12, 4) -ne 'IHDR') {
            throw 'Inputs must be PNG files with an IHDR header.'
        }
        [long]$width = [long]$header[16] * 16777216 + [long]$header[17] * 65536 + [long]$header[18] * 256 + $header[19]
        [long]$height = [long]$header[20] * 16777216 + [long]$header[21] * 65536 + [long]$header[22] * 256 + $header[23]
        if ($width -lt 1 -or $height -lt 1 -or $width -gt 8192 -or $height -gt 8192 -or $width * $height -gt 16777216) {
            throw 'Input dimensions exceed 8192 edges or 16 million pixels.'
        }
    } finally { $stream.Dispose() }
}
Assert-PngBounded $heightFile
Assert-PngBounded $colorFile

$drawingReferences = @([Drawing.Bitmap].Assembly.Location, [Drawing.Color].Assembly.Location)
$gdiInterface = [Drawing.Graphics].GetInterfaces() | Where-Object { $_.Assembly.GetName().Name -eq 'System.Private.Windows.GdiPlus' } | Select-Object -First 1
if ($gdiInterface) {
    $drawingReferences += $gdiInterface.Assembly.Location
    foreach ($reference in $gdiInterface.Assembly.GetReferencedAssemblies() | Where-Object { $_.Name.StartsWith('System.Private.Windows.') }) {
        $drawingReferences += [Reflection.Assembly]::Load($reference).Location
    }
}
Add-Type -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.IO;
public static class MWMaterialMaps {
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
    public static byte[] HeightRgb(byte[] source, bool strict) {
        byte[] gray = new byte[source.Length];
        for (int i = 0; i < source.Length; i += 4) {
            if (source[i + 3] != 255) throw new ArgumentException("Authored height must be opaque; transparent height values are undefined.");
            if (strict && (source[i] != source[i + 2] || source[i + 1] != source[i + 2])) throw new ArgumentException("Strict grayscale requires R=G=B at every authored pixel.");
            gray[i] = gray[i + 1] = gray[i + 2] = source[i + 2];
            gray[i + 3] = 255;
        }
        return gray;
    }
    public static long[] InputMetrics(byte[] source) {
        long nonGray = 0, maxSpread = 0;
        for (int i = 0; i < source.Length; i += 4) {
            int spread = Math.Max(source[i], Math.Max(source[i + 1], source[i + 2])) - Math.Min(source[i], Math.Min(source[i + 1], source[i + 2]));
            if (spread > 0) nonGray++;
            maxSpread = Math.Max(maxSpread, spread);
        }
        return new long[] { nonGray, maxSpread };
    }
    public static Bitmap Resize(Bitmap source, int width, int height) {
        Bitmap target = new Bitmap(width, height, PixelFormat.Format32bppArgb);
        try {
            using (Graphics graphics = Graphics.FromImage(target)) using (ImageAttributes attributes = new ImageAttributes()) {
                graphics.CompositingMode = CompositingMode.SourceCopy;
                graphics.PixelOffsetMode = PixelOffsetMode.Half;
                graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
                attributes.SetWrapMode(WrapMode.TileFlipXY);
                graphics.DrawImage(source, new Rectangle(0, 0, width, height), 0, 0, source.Width, source.Height, GraphicsUnit.Pixel, attributes);
            }
            return target;
        } catch { target.Dispose(); throw; }
    }
    public static byte Encode(double value) {
        return (byte)Math.Max(0, Math.Min(255, Math.Round((value * 0.5 + 0.5) * 255.0, MidpointRounding.AwayFromZero)));
    }
    public static byte[][] Normals(byte[] height, int width, int rows, double strength, int collar) {
        byte[] plus = new byte[height.Length], minus = new byte[height.Length];
        for (int y = 0; y < rows; y++) for (int x = 0; x < width; x++) {
            int pos = (y * width + x) * 4;
            double nx = 0, ny = 0, nz = 1;
            if (!(x < collar || y < collar || x >= width - collar || y >= rows - collar)) {
                int left = (y * width + Math.Max(0, x - 1)) * 4 + 2;
                int right = (y * width + Math.Min(width - 1, x + 1)) * 4 + 2;
                int above = (Math.Max(0, y - 1) * width + x) * 4 + 2;
                int below = (Math.Min(rows - 1, y + 1) * width + x) * 4 + 2;
                double dx = (height[right] - height[left]) / (2.0 * 255.0);
                double dy = (height[below] - height[above]) / (2.0 * 255.0);
                nx = -strength * dx; ny = strength * dy;
                double inverseLength = 1.0 / Math.Sqrt(nx * nx + ny * ny + 1.0);
                nx *= inverseLength; ny *= inverseLength; nz = inverseLength;
            }
            plus[pos] = minus[pos] = Encode(nz);
            plus[pos + 1] = Encode(ny); minus[pos + 1] = (byte)(255 - plus[pos + 1]);
            plus[pos + 2] = minus[pos + 2] = Encode(nx);
            plus[pos + 3] = minus[pos + 3] = 255;
        }
        return new byte[][] { plus, minus };
    }
    public static double[] Metrics(byte[] height, byte[] plus, byte[] minus, int width, int rows, int collar) {
        double maxLengthError = 0, maxTilt = 0, tiltTotal = 0, flatBorderCount = 0;
        int minHeight = 255, maxHeight = 0;
        for (int y = 0; y < rows; y++) for (int x = 0; x < width; x++) {
            int i = (y * width + x) * 4;
            if (height[i] != height[i + 1] || height[i] != height[i + 2] || height[i + 3] != 255) throw new ArgumentException("Saved height is not opaque grayscale data.");
            minHeight = Math.Min(minHeight, height[i + 2]); maxHeight = Math.Max(maxHeight, height[i + 2]);
            if (plus[i] != minus[i] || plus[i + 2] != minus[i + 2] || plus[i + 1] + minus[i + 1] != 255 || plus[i + 3] != 255 || minus[i + 3] != 255) throw new ArgumentException("Saved paired normal channel or alpha check failed.");
            double nx = plus[i + 2] / 127.5 - 1.0, ny = plus[i + 1] / 127.5 - 1.0, nz = plus[i] / 127.5 - 1.0;
            double length = Math.Sqrt(nx * nx + ny * ny + nz * nz);
            maxLengthError = Math.Max(maxLengthError, Math.Abs(length - 1.0));
            double tilt = Math.Acos(Math.Max(-1, Math.Min(1, nz / length))) * 180.0 / Math.PI;
            maxTilt = Math.Max(maxTilt, tilt); tiltTotal += tilt;
            if (x < collar || y < collar || x >= width - collar || y >= rows - collar) {
                flatBorderCount++;
                if (plus[i] != 255 || plus[i + 1] != 128 || plus[i + 2] != 128) throw new ArgumentException("Saved flat normal collar check failed.");
            }
        }
        if (maxLengthError > Math.Sqrt(3.0) / 255.0 + 1e-12) throw new ArgumentException("Quantized normal length exceeds RGB8 error bound.");
        return new double[] { minHeight, maxHeight, maxLengthError, maxTilt, tiltTotal / (width * rows), flatBorderCount };
    }
    public static void SaveLinearPng(Bitmap bitmap, string path) {
        // Keep only structural PNG chunks, excluding any gamma/profile metadata.
        byte[] encoded;
        using (MemoryStream memory = new MemoryStream()) { bitmap.Save(memory, ImageFormat.Png); encoded = memory.ToArray(); }
        using (FileStream target = new FileStream(path, FileMode.CreateNew, FileAccess.Write)) {
            target.Write(encoded, 0, 8);
            int pos = 8;
            while (pos < encoded.Length) {
                uint length = ((uint)encoded[pos] << 24) | ((uint)encoded[pos + 1] << 16) | ((uint)encoded[pos + 2] << 8) | encoded[pos + 3];
                int chunkSize = checked((int)length + 12);
                string type = System.Text.Encoding.ASCII.GetString(encoded, pos + 4, 4);
                if (type == "IHDR" || type == "IDAT" || type == "IEND") target.Write(encoded, pos, chunkSize);
                pos = checked(pos + chunkSize);
            }
        }
    }
}
'@ -ReferencedAssemblies $drawingReferences

$authored = [Drawing.Bitmap]::new($heightFile)
try {
    $albedo = [Drawing.Bitmap]::new($colorFile)
    try {
        $width = $albedo.Width
        $height = $albedo.Height
        if ([long]$authored.Width * $height -ne [long]$authored.Height * $width) { throw 'Authored height and albedo must have identical aspect ratio.' }
        if ($FlatBorderPixels * 2 -gt [Math]::Min($width, $height)) { throw 'Flat collar cannot exceed half the shorter target edge.' }
        $authoredBytes = [MWMaterialMaps]::Read($authored)
        $inputMetrics = [MWMaterialMaps]::InputMetrics($authoredBytes)
        $grayBytes = [MWMaterialMaps]::HeightRgb($authoredBytes, $HeightChannel -eq 'StrictGrayscale')
        $gray = [MWMaterialMaps]::BitmapFrom($authored.Width, $authored.Height, $grayBytes)
        try { $sized = [MWMaterialMaps]::Resize($gray, $width, $height) } finally { $gray.Dispose() }
        try {
            $sizedBytes = [MWMaterialMaps]::Read($sized)
            $normals = [MWMaterialMaps]::Normals($sizedBytes, $width, $height, $Strength, $FlatBorderPixels)
            $normalPlus = [MWMaterialMaps]::BitmapFrom($width, $height, $normals[0])
            $normalMinus = [MWMaterialMaps]::BitmapFrom($width, $height, $normals[1])
            try {
                [IO.Directory]::CreateDirectory($outputRoot) | Out-Null
                [MWMaterialMaps]::SaveLinearPng($sized, $targets[0])
                [MWMaterialMaps]::SaveLinearPng($normalPlus, $targets[1])
                [MWMaterialMaps]::SaveLinearPng($normalMinus, $targets[2])
            } finally { $normalPlus.Dispose(); $normalMinus.Dispose() }
        } finally { $sized.Dispose() }
        $savedHeight = [Drawing.Bitmap]::new($targets[0])
        $savedPlus = [Drawing.Bitmap]::new($targets[1])
        $savedMinus = [Drawing.Bitmap]::new($targets[2])
        try { $metrics = [MWMaterialMaps]::Metrics([MWMaterialMaps]::Read($savedHeight), [MWMaterialMaps]::Read($savedPlus), [MWMaterialMaps]::Read($savedMinus), $width, $height, $FlatBorderPixels) } finally { $savedHeight.Dispose(); $savedPlus.Dispose(); $savedMinus.Dispose() }
        if ((Get-FileHash -LiteralPath $colorFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $colorHash -or (Get-FileHash -LiteralPath $heightFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $heightHash) { throw 'Input identity changed while exporting.' }
        $files = @()
        foreach ($target in $targets[0..2]) {
            $files += [ordered]@{ file = [IO.Path]::GetFileName($target); sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant(); dimensions = @($width, $height) }
        }
        $report = [ordered]@{
            schema_version = 1
            status = 'authored-height material pilot; mesh/tangent/mapped-render validation pending'
            source_height_path = $heightFile
            source_height_sha256 = $heightHash
            albedo_path = $colorFile
            albedo_sha256 = $colorHash
            albedo_unchanged = $true
            source_height_dimensions = @($authored.Width, $authored.Height)
            target_dimensions = @($width, $height)
            tool_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
            height_channel = $HeightChannel
            height_formula = 'H=authored red byte/255; output R=G=B=red byte after bicubic size conversion; alpha255; no luminance or gamma conversion'
            authored_non_grayscale_pixels = $inputMetrics[0]
            authored_max_rgb_channel_spread = $inputMetrics[1]
            resize = 'System.Drawing HighQualityBicubic, SourceCopy, PixelOffsetHalf, TileFlipXY'
            strength = $Strength
            gradient_units = 'normalized height difference per target texel; not per normalized UV interval'
            strength_units = 'target texels of height per normalized [0,1] height unit'
            derivative = 'central difference: dx=(Hright-Hleft)/2; dy=(Hbelow-Habove)/2; clamped sampling at image edges'
            image_axes = 'x right; image y down; tangent x right; tangent y up; tangent z out'
            normal_plus_y = 'normalize(-strength*dx,+strength*dy,1)'
            normal_minus_y = 'identical R/B; encoded G=255-normal-plus-y.G'
            normal_encoding = 'opaque RGBA8 PNG; RGB linear vector data; round-away-from-zero((N*0.5+0.5)*255); no sRGB/gamma/profile chunks'
            quantization_note = 'zero cannot be represented exactly in UNORM8; flat plus=(128,128,255), minus=(128,127,255); shader should decode RGB*2-1 then normalize'
            flat_border_pixels = $FlatBorderPixels
            flat_border_policy = 'normal-only collar forces ideal N=(0,0,1); height values remain unchanged; does not prove texture/UV seam compatibility'
            metrics = [ordered]@{ height_min = $metrics[0]; height_max = $metrics[1]; max_decoded_normal_length_error = $metrics[2]; max_tilt_degrees = $metrics[3]; mean_tilt_degrees = $metrics[4]; flat_border_pixels_checked = $metrics[5] }
            validation = 'saved PNGs reloaded; grayscale/opaque height, paired channels, opaque normals, collar and RGB8 unit-length-error bound checked'
            format_reference = 'https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#material-normaltexture'
            files = $files
        }
        $json = ($report | ConvertTo-Json -Depth 8) + [Environment]::NewLine
        $stream = [IO.FileStream]::new($targets[3], [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        try { $bytes = [Text.Encoding]::UTF8.GetBytes($json); $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
        Write-Output $json
    } finally { $albedo.Dispose() }
} finally { $authored.Dispose() }
