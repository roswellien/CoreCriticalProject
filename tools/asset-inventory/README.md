# Asset inventory

Python standard-library, read-only discovery tool. Hashes files and recognizes
selected leading signatures; it does not extract assets or decode ZBD indexes.
Output must be outside the input directory. Inputs changing during hashing fail.

From the repository root:

```powershell
python tools/asset-inventory/inventory.py MW3 --exclude-dir MechWarrior-3_Patch_Win_EN_Patch-12 --exclude-dir MechWarrior-3_Win_EN_ISO-Version --exclude-dir MechWarrior-3-Pirates-Moon_Win_EN_ISO-Version --output local/work-ahead/inventory.json
python -m unittest discover -s tests -p test_asset_inventory.py -v
```

Exclusions match directory names, case-insensitively. Scan a quiescent
installation for reproducibility. Reports contain local paths and metadata;
keep them ignored. Signature candidates do not prove a valid full format.
WAVE metadata describes the first stream accepted by Python's wave reader;
it does not prove that a large container contains only that stream. RIFF size
mismatches are recorded and require investigation. Embedded assets and videos
are not detected by this leading-signature scan.

## Bounded format probes

```powershell
python tools/asset-inventory/probe.py images MW3/zbd/rmechtex.zbd --output local/work-ahead/rmechtex-probe.json
python tools/asset-inventory/probe.py riff MW3/zbd/soundsH.zbd --output local/work-ahead/soundsH-probe.json
python -m unittest discover -s tests -p 'test_asset*.py' -v
```

The image probe tests a specific table hypothesis and reports candidate
dimensions and span sizes. It does not decode pixels or identify materials.
The RIFF probe walks bounded chunks and successive streams, records any
non-RIFF trailing region as unparsed, and rejects malformed RIFF/chunk bounds.
Neither mode exports payloads. Reports belong under ignored `local/`.

## Strict local image decoder

```powershell
python tools/asset-inventory/decode_images.py MW3/zbd/rmechtex.zbd --expect-sha256 8f679537d33fb6da204d8dcb83d5b4d0e4d5dbcee1a16d0c63caeed9649fdbfe --entry 0 --entry 1513 --output-dir local/work-ahead/my-review/rmechtex
```

Requires an expected source hash. Outputs are restricted to a subdirectory of
the project's ignored `local/`; existing files and symlinks are rejected and
files are created exclusively. With no `--entry`, writes descriptor metadata
only. All requested entries decode before output starts; unknown flags, palettes,
stretch, invalid dimensions, mismatched spans and unsupported headers fail.
This intentionally supports a smaller subset than the external format research.

PNG previews retain stored size, row order and alpha. RGB565 channels scale to
RGBA8 by nearest rounding, without gamma adjustment or resampling. A manifest
records source/tool/parser hashes, decode policy and output identities.
The [pilot record](../../docs/work-ahead-texture-pilot.md) contains source
corroboration and the remaining original-renderer validation gate.

## Exact-size exports and alpha checks (Windows)

```powershell
./tools/asset-inventory/export_preview.ps1 -InputPath local/work-ahead/pilot-v2/rmechtex/entry-01513.png -OutputPath local/work-ahead/my-review/damage-4x.png -Width 128 -Height 128 -PreserveSourceAlpha
./tools/asset-inventory/compare_preview.ps1 -SourcePath local/work-ahead/pilot-v2/rmechtex/entry-01513.png -CandidatePath local/work-ahead/my-review/damage-4x.png
```

Exports use Windows System.Drawing bicubic sizing, or `-Sampling nearest` for
controls. `-PreserveSourceAlpha` retains exact original alpha values on an integer
upscale grid. It does not reconstruct new detail. Output must stay under ignored
`local/`; existing files, output-directory junctions/symlinks and aspect changes
are rejected. Comparison is read-only and reports normalized alpha differences
and intersection-over-union at threshold 128. Metrics are evidence, not approval.

## Protected texture batch exports (Windows)

`lock_texture_export.ps1` exports an integer-size creative draft while restoring
every original alpha byte and exact RGB inside source-coordinate border and
rectangle locks. Optional `-SourceAnchoredDetail` retains original coarse color
and shading, adding bounded within-cell draft detail. Saved PNGs are read back
and checked for alpha, protected RGB and transparent RGB mismatches. Outputs
must stay under ignored `local/`; source-hash, bounds and no-overwrite checks
apply.

See the [lock specification and command example](texture-lock-format.md) for
settings and editable component behavior, and the
[12-texture batch record](../../docs/work-ahead-texture-batch.md) for source
mapping, packaging and validation. Source-coordinate locks do not establish
unknown UV mappings or renderer behavior.
The later [full-AI batch](../../docs/work-ahead-texture-ai-batch.md) keeps generated
RGBA as the selected starting version. It invokes this tool without RGB locks or
source anchoring only for separately labeled original-alpha comparisons.

## Authored height and normal-map exports (Windows)

`export_material_maps.ps1` converts a separately authored height PNG to scalar
data matching an identity-checked color PNG, then computes paired tangent-normal
maps. The color PNG is unchanged. The defaults are red-channel height, strength
8 in target-texel units, and a four-pixel flat-normal border. Output identity,
size, aspect, fresh local paths and saved-PNG invariants are checked.

See the [material-map numerical specification](material-map-format.md) for the
command, conventions and importer requirements, and the
[four-material pilot](../../docs/work-ahead-material-pilot.md) for local outputs,
moving-light review and remaining mesh/tangent gates. Four authored fixtures
cover gradient signs, encoding, quantization, border, channel and input guards.
The [eight-material batch](../../docs/work-ahead-material-batch.md) extends that
pilot to all selected mech and terrain textures, retaining the original pilot
maps unchanged and independently checking all sixteen paired normal maps.

## Local effect animation preparation

The [six-frame dust pilot](../../docs/work-ahead-effects-animation-pilot.md)
combines strict source decoding with separately checked interpreter map-order
evidence. Its local package retains full generated AI RGBA, exact atlas-cell
exports, editable layers and descriptive alpha/motion checks. Script speed
tokens are not treated as verified native frame rates. Local preparation recipes
remain prototypes; native timing, blending and replacement routing are open.
The [dust transparency revision](../../docs/work-ahead-effects-transparency-revision.md)
is visually accepted. The [sixteen-frame fire pilot](../../docs/work-ahead-fire-animation-pilot.md)
adds a configured one-shot burst, a recorded whole-atlas bicubic conversion,
editable layers and descriptive brightness/fade checks. Its 512-pixel working
exports do not imply intrinsic generated detail at that resolution.
The [four-frame weapon-impact pilot](../../docs/work-ahead-weapon-impact-pilot.md)
uses explicit source indexes and count-aware evidence/validation, including
bounded weapon-definition observations, while retaining unknown native dispatch
and timing. Its neutral white flash and residue remain a review prototype.
The [four-state smoke concept](../../docs/work-ahead-smoke-animation-concept.md)
was followed by a [two-frame source-associated smoke pilot](../../docs/work-ahead-smoke-animation-pilot.md).
The interpreter/model name evidence supports a jump-smoke association, but
compiled playback order and native timing remain unverified.

## Disc-video inventory

```powershell
python tools/asset-inventory/video_probe.py "MW3/MechWarrior-3_Win_EN_ISO-Version/Mechwarrior 3.iso" --expect-sha256 08c26c0d71375d6130df7716abc2c282147494d869bd48ce13bd5f972f763e49 --output local/work-ahead/my-review/disc-video-inventory.json
```

Traverses primary ISO9660 extents and recognizes leading signatures. Bounded AVI
headers/chunks yield timing, dimensions, FOURCC and audio metadata; payloads
are not decoded or copied. Multi-extent/interleaved files, unsupported sector
sizes, malformed bounds and cycles fail. Full source identity must match the
expected hash. Outputs are new metadata files under `local/work-ahead/`.
See the [enhancement/video record](../../docs/work-ahead-enhancement-experiment.md)
for current results and unresolved codec/index checks.

## Short local video pilot

Requires locally installed FFmpeg/FFprobe. The current preparation contract
accepts the observed zero-start 15 fps video and mono 22050 Hz 8-bit PCM only.
Output must be a fresh directory under ignored `local/work-ahead/`.

```powershell
python tools/asset-inventory/prepare_video_pilot.py --iso "MW3/MechWarrior-3_Win_EN_ISO-Version/Mechwarrior 3.iso" --expect-iso-sha256 08c26c0d71375d6130df7716abc2c282147494d869bd48ce13bd5f972f763e49 --disc-path "VIDEO/C2M1.AVI;1" --expect-asset-sha256 a4ceb7c9cc222fe4a690717d670449cc2dacdc251512c9708fd9e29a62881385 --frames 75 --output-dir local/work-ahead/my-video-pilot
```

The source is bounded and identity checked before extraction. Display holds are
reconstructed at the original rate before trimming; audio is sample trimmed.
The installed Video2X models, exact processing parameters and output hashes are
recorded in the local pilot's manifest. See the
[video pilot record](../../docs/work-ahead-video-pilot.md) for methods and results.

```powershell
python tools/asset-inventory/validate_video_pilot.py local/work-ahead/my-video-pilot
```

Validation expects the four named five-second masters: `source-5s.mkv`,
`lanczos2x-master.mkv`, `ai-native2x-master.mkv` and `ai-general2x-master.mkv`.
It checks the exact frame grid, dimensions, duration, continuous audio timestamps
and PCM equality with the first five seconds of `source.avi`. It creates a new
`validation.json` exclusively; this is a fixed pilot validator, not a general
replacement-pack approval tool. Perceptual motion and native playback remain
separate checks.

## Full opening cinematic upgrade

The opening movie has a separate full-length stereo contract. After the source
has been extracted into its verified project directory, run:

```powershell
python tools/asset-inventory/upgrade_opening_cinematic.py local/work-ahead/opening-cinematic-v1
python -m unittest discover -s tests -p test_asset_opening_cinematic.py -v
```

The workflow checks the exact source identity, installed pilot tool/model hashes,
2737 display frames at 15 fps, and all 4023397 stereo PCM sample frames. It
creates and validates the reference, general 4x intermediate, 2880x2160 lossless
master, and separate original/upgraded browser exports. Existing outputs must
pass validation before they can be reused. Failed or partial outputs require
inspection and a fresh output location before retrying; they are not overwritten.
`processing.json` records argument vectors, elapsed times, output hashes and
checks. Full-speed visual and playback review remains separate. See the
[opening cinematic project](../../docs/opening-cinematic-upgrade.md).

The separate full-movie interpolation workflow verifies the existing upscale
and pilot RIFE identities, then produces and validates a 30 fps master and
full-quality review export in a fresh local directory:

```powershell
python tools/asset-inventory/interpolate_opening_cinematic.py local/work-ahead/my-opening-30fps
python tools/asset-inventory/package_movie_download.py local/work-ahead/my-opening-30fps/opening-2160p-30fps-review.mp4 local/work-ahead/my-opening-30fps/download-package
```

Download packaging splits exact bytes into 90 MiB parts with per-part hashes,
reconstruction verification and Windows/Python reassembly scripts. It does not
apply further compression. See the [full 30 fps record](../../docs/opening-cinematic-30fps-full.md).

For the admitted disc's remaining 18 videos, use the per-movie batch contract:

```powershell
python tools/asset-inventory/upgrade_cinematic_batch.py local/work-ahead/my-cinematic-batch
python tools/asset-inventory/upgrade_cinematic_batch.py local/work-ahead/my-cinematic-batch --resume
```

This keeps each source's mono-8-bit or stereo-16-bit PCM format and exact complete
sample count. Hash-matching validated outputs can resume; changed/partial outputs
require inspection. See the [batch record](../../docs/cinematics-2160p-30fps-batch.md).
