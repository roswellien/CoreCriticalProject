# Campaign 1 Mission 1 shoreline colour matching

Date: 2026-10-18. This follows the automatic world-normal preview, with dedicated
sky/cloud and animated-water normal work still deferred at the user's request.
Original gameplay, geometry, UVs and animation remain authoritative. Acceptance
remains **131/144**. Prepared media, banks and captures stay local.

Later same-day continuation: the user authorized dedicated sky/water work after
saving the [campaign lighting plan](campaign-lighting-progression-plan.md). The
[separate C1 sky/water preview](sky-water-normal-preview-2026-10-18.md) builds on
this color correction; the diagnosis and original color-grade evidence below
remain unchanged.

## Diagnosis

The reported bright green strip is the water portion of the existing animated
surf atlas. Its source palette is already close to the adjoining open-water
texture, but the original vertex modulation differs. In the controlled C1M1 run,
the first open-water draw used `FF929292`, while observed surf frames ranged from
`FFA0A0A0` to `FFBDBDBD`. Both use opaque, depth-tested, depth-writing draws,
texture-times-diffuse modulation, the existing Sun TL shader and the exact active
world-camera binding. This is not evidence of an unlit surf shader or alpha-blend
admission failure. The first registration-only control produced identical
captures and was not promoted.

The whole surf atlas receives that modulation, including its water border.
Matching file colours alone therefore does not match the rendered water. The
correction targets only that border; brighter neutral foam and warm sand retain
their source pixels.

One clarification to the earlier coverage description: the broad automatic pass
classified `txwat01d` as terrain and supplied an estimated normal map to that
open-water tile. Water was not universally excluded. Dedicated wave/cloud normal
work remains deferred; this sidebar adds no normal maps or shader changes.

## Texture preparation

[The preparer](../tools/remaster-launcher/prepare_shore_colour.py) applies one
reviewed colour grade to all 13 wave frames in each of the six configured,
SHA-pinned upgraded C1 banks. The built-in image-generation tool supplied a
palette reference based on the live surf atlas and adjoining upgraded water.
Only its water colour statistics are used in production: generated pixels do not
replace the original foam motion, sand or UV layout.

The water mask selects green water on the water side of the atlas, protects
bright foam, and leaves the warm beach unchanged. RGB565 quantization is explicit.
Each bank retains the original entry headers, dimensions, offsets, stretches,
file size, black colour-key positions and every unrelated entry payload. Source
files are checked before and after preparation. Output is written to a fresh
directory; the bank map and receipt are published after the six banks complete.

Local evidence is under
`C:/Users/jcbla/MW34SunTests/c1-shore-blend-r1/`. The generated reference and exact
prompt are `shore-color-reference.png` and `artwork-reference.txt`. Candidate
receipts retain every source/output bank identity, selected frame and changed
pixel count. The darker first candidate is retained separately from the refined
water mask.

## Test-window investigation

Two earlier diagnostic windows were recorded by Windows as application hangs.
The campaign automation still pressed Escape at frames 30/38 to skip an intro,
but the selected profile was already at its main menu. Captures show the Quit
dialog receiving the later campaign clicks. Removing those obsolete inputs
restored the campaign route; subsequent bounded hidden C1M1 runs reach gameplay
and complete their presentation budgets. This does not establish that every
shutdown/hang path is fixed. The preceding manual play session logged normal
`ExitProcess(0)`.

The corrected route uses copied test pilots and preserves the player's files.
Hidden captures still execute original native gameplay and GPU rendering; they
do not grant additional acceptance credit. Diagnostic render-state logging and
the trial lighting override stay in a private host, outside the selected preview.


## Selected preview and checks

The selected candidate is `candidate-r2/`, with its six prepared banks,
`texture-banks.bin` and `receipt.json` under the local evidence directory above.
Normal Mapping Preview now selects that bank map. The executable SHA remains
`95716007bbe79483c046ab1bb94f7cc93676171baa47696cbbb7d1d73877c8d2`;
all 90 source pins, shaders, normal catalogs, model bindings and shared sun
presets remain unchanged. Main Play and the standalone Big Lake profile were not
changed. Original banks remain read-only. No commit or push was made.

- All 78 selected entries across six banks were checked; 3,411 unrelated entries
  retain exact bytes. Entry headers, table bytes, source black-key masks and
  protected foam/sand pixels are checked during packing.
- Paired sunset and midday runs each reached 1,200 presentations with identical
  original draw triples. All four capture differences are confined to the
  shoreline band. Comparison images are `sunset-shore-comparison.png` and
  `midday-shore-comparison.png` in the local evidence directory.
- The final sunset candidate and prior control each reached 1,800 presentations
  with all original draw triples identical. Protected original files and source
  bank hashes were rechecked. The launcher profile check passes.
- `comparison-release.json` records the results. Preview profile and snapshot
  backups are retained in `preview-before-shore/`.

This improves the colour boundary, while the original animated brightness,
texture pattern differences, fog interpolation and wave geometry remain. It is
not a new water renderer or a claim of seamless matching at every camera angle.
Close-range player review remains useful.

The generated colour reference and exact prompt also have a project-local copy
under `local/work-ahead/c1-shore-colour-r1/`, which stays outside Git.

## Artwork reference prompt

Built-in image-generation edit, target `wave01-live.png`, with
`txwat01d-live.png` as the adjoining upgraded-water colour reference:

> Edit target: FIRST image, a 512x1024 opaque vertical MW3 game shoreline texture
> atlas. SECOND image is a color reference ONLY for the adjoining open water.
> Make a strictly restrained COLOR BALANCE correction ONLY to the green water at
> the right of the first image. Match its water hue, saturation and brightness to
> the second image's darker muted blue-green/olive open-water palette so the
> right edge can join that open water without a bright green rectangular strip.
> Preserve the exact vertical 1:2 canvas, shoreline position, UV layout, foam
> shape, wet sand, sand grain, all borders and all existing texture detail. Do not
> redraw the foam, beach or water pattern. Do not add new highlights, waves,
> reflections, objects or lighting. Keep foam neutral white and sand completely
> unchanged. This image is a palette correction reference for an existing
> 13-frame animated surf texture, NOT a new scene or illustration. Output ONLY
> the corrected first texture, no labels or contact sheet.
