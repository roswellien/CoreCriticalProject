# Machine-gun impact animation pilot

Recorded 2026-10-07. After the
[sixteen-frame fire pilot](work-ahead-fire-animation-pilot.md), the user
authorized the next weapon-impact pilot. The selected complete family is
`mgun_impact01`–`mgun_impact04`. Local media and metadata are under
`local/work-ahead/weapon-impact-pilot-v1/`.

## Selection and source evidence

C1 texture entries 378–381 are 32 x 32, flags 11, RGB565 plus a byte alpha
plane. The container `MW3/zbd/c1/rtexture.zbd` has SHA-256
`56afd5738562ffd51596ce4b3557b734cacedfd187b09307e9b94281dd39269f`.
All source RGB bytes are white; alpha defines the visible flash and residue.
Mean alpha fades approximately **34.22, 26.27, 7.64, 1.64 / 255**, while peaks
are **255, 170, 144, 110**. The late peaks occupy sparse marks and do not mean
the late frames have a broad bright core.

The `Support\effects.gw` script in `MW3/zbd/interp.zbd` (SHA-256
`f4ae013c419984cd1139dcbe06695efddd1875e88baa55bf0997adf36907b171`)
configures node `mgun_impact` with the four ordered map names, count 4, raw
speed 15 and looping off. Independent bounded parsing verifies those tokens
and offsets. The review rate of 15 FPS is an assumption, not established native
timing.

Hash-bound reader-definition string observations associate the MGUN weapon
with damage animation `impact_mgun_mech`, and associate that animation with
`mgun_impact.flt` and texture-cycle node `mgun_impact`. The weapon-loader script
provides supporting parsed evidence. Window hashes, full string bounds and
observations are checked independently. This supports the family choice beyond
its name; the reader format and native hit dispatch have not been fully decoded.

## Preparation and review

The pilot refines the existing neutral white impact cue across all four frames,
using full AI RGB and alpha as the selected artwork. Original references remain
separate. The first generation retained too much later-frame density; a
generative revision corrects the transparency and rapid fade. Exact original
alpha or silhouettes are not imposed on the selected AI output.

An exact 2 x 2 original reference atlas retains all source RGBA. The selected
raw AI atlas is 1254 x 1254 with four 627 x 627 cells. One whole-atlas bicubic
downsize produces a 1024 x 1024 working atlas, followed by exact 512 x 512 cell
crops and byte-identical final copies. There is no further per-frame resizing.
Final export size is not a claim about intrinsic AI detail. Technical
original-reference expansion keeps alpha bytes exact.

Final mean alpha is about 42.15, 34.67, 9.76 and 2.05 / 255. The tail-to-opening
mean-alpha ratio is 0.0486, compared with source 0.0479, although absolute
opacity is somewhat higher. Sparse late highlights exceed source peaks.
Some fine detail reads as crystalline/electrical glints, with dark fringes and
minor edge contact. These are documented style and sampling concerns for review,
rather than evidence of exact original appearance or native compatibility.

The offline comparison provides one-shot playback, replay, optional looping,
frame stepping, alpha inspection, light/dark backgrounds and illustrative
blend controls. Static checks cover the embedded PNGs, resource links and
JavaScript; rendered browser behavior remains unverified. Alpha and encoded
RGB x alpha brightness measurements describe saved pixels, not physical
light or native engine output.

Source mapping and hashes, generation prompts/history, export recipes, editable
OpenRaster documents and independent checks are retained locally for hand-off.
Native timing units, activation, blending, gamma, tint, fades, depth, sampling,
placement and replacement routing remain open. Earlier six sealed packages
are preserved, and the full INTRO video upscale remains held.

Status: **complete four-frame prototype prepared for visual review; native
motion and rendering validation pending**. Smoke is the next recommended family.
