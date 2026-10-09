# Authored height to material data maps

`export_material_maps.ps1` takes independently authored height artwork and an
approved albedo PNG. It reads the albedo's dimensions and SHA-256 but never
changes its pixels or file. Creative height construction belongs to the image
tool; this exporter performs only deterministic sizing and normal calculations.

```powershell
pwsh -NoProfile -File tools/asset-inventory/export_material_maps.ps1 `
  -HeightPath local/work-ahead/material-pilot/height-authored.png `
  -ColorPath local/work-ahead/texture-ai-v2/example/final.png `
  -ExpectHeightSha256 <height-png-sha256> `
  -ExpectColorSha256 <approved-albedo-png-sha256> `
  -OutputDir local/work-ahead/material-pilot/example `
  -HeightChannel RedChannel -Strength 8 -FlatBorderPixels 4
```

Four fresh files are written to ignored project-local storage: `height.png`,
`normal-plus-y.png`, `normal-minus-y.png` and `export-report.json`. Both input
hashes are mandatory. PNG inputs must have the same aspect ratio; export
dimensions match the albedo exactly. Existing outputs and output directories
with junction/symlink ancestors fail before writing. Inputs are limited to
128 MiB, 8192 pixels per edge and 16 million pixels.

Height artwork must be opaque. Default `RedChannel` interprets only the authored
red byte; output grayscale repeats this value in R/G/B. It does not calculate
luminance or infer a color transfer function. `StrictGrayscale` instead rejects
any authored pixel whose R/G/B differ. The report records non-grayscale input
pixel count and maximum channel spread. Red-channel values are sized using
high-quality bicubic sampling, SourceCopy, PixelOffsetHalf and TileFlipXY.

The normalized height is `H = R / 255`. Gradients use central differences with
one **target texel** between neighboring samples:

```text
dx = (H(x+1,y) - H(x-1,y)) / 2
dy = (H(x,y+1) - H(x,y-1)) / 2
N  = normalize(-strength*dx, +strength*dy, 1)
```

Sampling clamps to the closest edge pixel. Image X points right and image Y
points down; tangent X points right, tangent Y points up and Z points outward.
Default strength is 8, with allowed finite values 0 through 128. Strength uses
target texels of height per normalized `[0,1]` height unit. Export resolution
therefore affects gradients; strength is not physical world displacement and
does not convert gradients to a normalized UV interval.

Normals are stored as RGB vector data with opaque alpha. Encoding is
`roundAwayFromZero((N * 0.5 + 0.5) * 255)`. Minus-Y keeps R/B unchanged and
inverts green exactly as `255 - plusGreen`. UNORM8 cannot encode zero exactly:
ideal flat normal `(0,0,1)` becomes plus-Y `(128,128,255)` and minus-Y
`(128,127,255)`. Decode using `RGB * 2 - 1`, then normalize. The names define the
actual channel convention rather than claim a particular renderer/API binding.

The default four-pixel outer collar forces only the normals to ideal flat;
height values remain unchanged. Set `FlatBorderPixels` to 0 for derivative
normals over the whole canvas. The collar may not exceed half the shorter target
edge. A flat outer collar does not establish internal atlas boundaries or
terrain tiling, and it does not make the height map tile seamlessly.

All exported PNGs contain only IHDR/IDAT/IEND chunks. Height and normal data are
interpreted linearly, with no sRGB/gamma/profile metadata or conversion. This
matches the linear tangent-space normal data representation described in the
[Khronos glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#material-normaltexture),
without asserting that these assets or their unknown tangent bindings are
glTF-ready.

The saved PNGs are reloaded to check opaque grayscale height, opaque normal
channels, exact green pairing, flat collar values and the RGB8 vector length
error bound `sqrt(3)/255`. Reports include input/output/tool hashes, settings,
dimensions, height range, decoded normal length error and tilt statistics.
Both input hashes are checked again after export. Mapped mesh/tangent direction,
handedness, materials, animation and original renderer behavior remain pending.

Four authored-fixture tests verify flat maps, central ramps and signs, paired
green, unit-length quantization error, unchanged height under the collar,
zero strength, RedChannel versus strict grayscale, alpha/size/aspect rejection,
expected source identity, overwrite prevention and output-root restrictions.
The existing `asset_tools` CTest discovery includes these tests automatically.
