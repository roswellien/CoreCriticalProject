param(
    [Parameter(Mandatory = $true)][string]$SourcePath,
    [Parameter(Mandatory = $true)][string]$CandidatePath,
    [ValidateRange(1, 16)][int]$Scale = 4
)

# Read-only comparison against source alpha expanded on the same coordinate grid.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$source = [Drawing.Bitmap]::new((Resolve-Path -LiteralPath $SourcePath).Path)
try {
    $candidate = [Drawing.Bitmap]::new((Resolve-Path -LiteralPath $CandidatePath).Path)
    try {
        if ($candidate.Width -ne $source.Width * $Scale -or $candidate.Height -ne $source.Height * $Scale) {
            throw 'Candidate must match source dimensions multiplied by Scale.'
        }
        [long]$mwOccupied = 0
        [long]$mwPartial = 0
        [long]$mwAlphaTotal = 0
        [long]$mwAbsDifference = 0
        [long]$mwIntersection = 0
        [long]$mwUnion = 0
        [double]$mwWeightedX = 0
        [double]$mwWeightedY = 0
        for ($y = 0; $y -lt $candidate.Height; $y++) {
            for ($x = 0; $x -lt $candidate.Width; $x++) {
                $alpha = [int]$candidate.GetPixel($x, $y).A
                $sourceAlpha = [int]$source.GetPixel([int][Math]::Floor($x / $Scale), [int][Math]::Floor($y / $Scale)).A
                $mwAbsDifference += [Math]::Abs($alpha - $sourceAlpha)
                if ($alpha -gt 0) { $mwOccupied++ }
                if ($alpha -gt 0 -and $alpha -lt 255) { $mwPartial++ }
                if ($alpha -ge 128 -and $sourceAlpha -ge 128) { $mwIntersection++ }
                if ($alpha -ge 128 -or $sourceAlpha -ge 128) { $mwUnion++ }
                $mwAlphaTotal += $alpha
                $mwWeightedX += $alpha * ($x + 0.5) / $candidate.Width
                $mwWeightedY += $alpha * ($y + 0.5) / $candidate.Height
            }
        }
        $pixelCount = [long]$candidate.Width * $candidate.Height
        $iou = if ($mwUnion) { $mwIntersection / $mwUnion } else { $null }
        $centroid = if ($mwAlphaTotal) { @(($mwWeightedX / $mwAlphaTotal), ($mwWeightedY / $mwAlphaTotal)) } else { $null }
        [ordered]@{
            source_sha256 = (Get-FileHash -LiteralPath $SourcePath).Hash.ToLowerInvariant()
            candidate_sha256 = (Get-FileHash -LiteralPath $CandidatePath).Hash.ToLowerInvariant()
            width = $candidate.Width
            height = $candidate.Height
            occupied_fraction = $mwOccupied / $pixelCount
            partial_alpha_fraction = $mwPartial / $pixelCount
            mean_opacity = $mwAlphaTotal / ($pixelCount * 255)
            alpha_mae_against_nearest_original = $mwAbsDifference / ($pixelCount * 255)
            alpha_iou_at_128 = $iou
            alpha_centroid_normalized = $centroid
        } | ConvertTo-Json -Depth 4
    } finally { $candidate.Dispose() }
} finally { $source.Dispose() }
