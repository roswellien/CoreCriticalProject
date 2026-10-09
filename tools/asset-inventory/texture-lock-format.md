# Deterministic texture export locks

`lock_texture_export.ps1` prepares exact integer-size PNG exports after an
image tool has produced the creative candidate. It does not synthesize artwork.
The default scale is 4; candidate and decoded source must have the same aspect
ratio. Generated RGB is sized with Windows System.Drawing high-quality bicubic
sampling. The decoded original's alpha is repeated exactly on the integer grid.
Every fully transparent output pixel has black RGB, including keyed black.

The optional `-SourceAnchoredDetail -DetailStrength 0.5` mode limits the creative
candidate to fine detail. It makes original RGB opaque for bicubic baseline
sizing, calculates candidate channel means separately inside each enlarged
source-pixel cell (4x4 at scale 4), then subtracts those means from the candidate.
The residual is limited to +/-20 per channel and multiplied by the requested
strength (0 through 1, default 0.5), added to the original baseline and rounded
away from zero to RGB8 with values clamped to 0 through 255. Original alpha and
exact RGB locks are then restored normally. At strength 0.5 the pre-lock detail
can change each baseline channel by at most 10 levels. The report records the
formula, strength, cell size, cap and SHA-256 of row-major baseline RGB8.

This subtracts coarse candidate shading and color within each cell. The
unclipped residual has zero cell mean; clipping and rounding can change that
mean. Structured variation inside a cell may remain, so source anchoring reduces
generative drift rather than proving that all invented features are absent.
Without the switch the original candidate-RGB export behavior remains available.

The lock specification identifies the decoded source PNG by SHA-256 and records
rectangles in its original pixel coordinates. Right and bottom bounds are
exclusive, so a rectangle at `(10, 4)` with size `(12, 8)` covers source columns
10 through 21 and rows 4 through 11. The source border and named rectangles copy
original RGB by exact nearest replication, retaining markings and selected
boundaries rather than inventing detail in those areas.

```json
{
  "version": 1,
  "source_sha256": "<64-character SHA-256 of decoded source PNG>",
  "border_pixels": 2,
  "regions": [
    {"name": "original marking", "x": 10, "y": 4, "width": 12, "height": 8}
  ]
}
```

`regions` may be an empty array. Rectangle bounds must be positive integers
inside the original; a zero-width rectangle fails. Borders may be zero but
cannot exceed half the shorter source edge. Overlapping rectangles form a union.

```powershell
pwsh -NoProfile -File tools/asset-inventory/lock_texture_export.ps1 `
  -SourcePath local/work-ahead/batch/source.png `
  -CandidatePath local/work-ahead/batch/generated.png `
  -LockSpecPath local/work-ahead/batch/locks.json `
  -OutputPath local/work-ahead/batch/export.png `
  -ReportPath local/work-ahead/batch/compatibility.json `
  -CandidateColorPath local/work-ahead/batch/edit-color.png `
  -ProtectedLayerPath local/work-ahead/batch/protected-original.png `
  -SourceGridPath local/work-ahead/batch/source-grid.png `
  -LockMaskPath local/work-ahead/batch/protection-mask.png `
  -ResizedCandidatePath local/work-ahead/batch/generated-sized.png -Scale 4
```

All optional images use the exact export canvas. `CandidateColorPath` contains
resized generated RGB with original alpha but no source RGB locks.
`ProtectedLayerPath` contains original RGBA inside locks and transparent black
elsewhere. `SourceGridPath` is the original enlarged by nearest replication;
`LockMaskPath` is an opaque black/white mask, with white representing locks.
`ResizedCandidatePath` retains the sized candidate's own alpha for comparison.
When source anchoring is enabled, `CandidateColorPath` contains anchored color
with original alpha, while `ResizedCandidatePath` still records the raw resized
candidate. Use both to make the preservation treatment reviewable.

An ordinary source-over blend of the two edit layers does not reproduce the
verified export when the source has partial alpha: overlapping alpha increases
opacity. An editable package should keep the verified export as its visible
layer and merged preview, with raw candidate and preservation layers available
but initially hidden. A subsequent edited export must pass the same gates.

The saved final PNG is reloaded and checked against the original at every pixel.
The report records zero alpha mismatches, zero protected RGB channel mismatches,
zero nonblack transparent RGB channels, hashes and export settings. Output
paths must stay beneath ignored `local/`, existing files are rejected, and
output ancestors cannot be symlinks or junctions. No original is overwritten.

These checks establish exact alpha and explicitly authored coordinate locks.
Unknown atlas islands, UV mappings, internal seam positions, texture orientation,
tiling, shader sampling and game blending still need original-renderer or
integration review. Pixels outside the declared locks may retain generative
layout drift. Border locks preserve the original edge; they do not establish
that the original texture tiled seamlessly.

Three Windows tests use independently authored RGBA fixtures to verify border and
rectangle coordinates, all alpha values including 0/64/128/255, every output
pixel and edit-layer mask, hashes, bounds, aspect ratio, overwrite prevention
and output-root guards. Source-anchoring checks reject a uniform blue recolor,
retain fine checker detail at the requested cap, verify the baseline RGB hash,
and show that zero detail strength reproduces the source baseline. Proprietary
images are absent from the fixtures.
