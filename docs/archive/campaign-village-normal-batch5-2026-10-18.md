# Campaign village and ruin normals — batch 5, 2026-10-18

Campaign encounter ranks 18–21 now have reviewed relief candidates in Material
Normal Preview: `m4ruin01c`, `fishvill05`, `fishvill03` and `fishvill04`.
Terrain/object strength stays at 1.5. The batch changes normal data only;
upgraded colors, previous road/rock artwork, dedicated ground selection,
water/cloud tuning, model geometry and replay settings are retained.

## Treatment and source review

| Material | Treatment | Normal resolution |
| --- | --- | --- |
| m4ruin01c | Restrained high-pass grain; no invented architectural seams in the indistinct mottled source; further authored relief remains open | 512 × 256 |
| fishvill05 | Door/window frames, floor ledges, vents and panel divisions; glass flat and painted stripe excluded from grain | 512 × 512 |
| fishvill03 | Pillars, doors, window rims and pipe; window glass flat | 512 × 128 |
| fishvill04 | Vertical plate seams, cross members and vent frames | 256 × 256 |

Structural relief for the three village families uses explicit normalized UV
features aligned to upgraded color references. Shallow color-derived grain is
supplementary, with glass/paint masks; bright or dark paint is not automatically
interpreted as a structural step. The ruin treatment remains a technical draft,
not a recovered physical surface. Editable 16-bit heights and RGBA8 normals stay
local. This does not change geometry or provide displacement.

All four first-encounter color sources differ from the original entries and
have 16 times their original linear dimensions. All 24 matching C1 alias entries
in the currently selected upgraded banks were checked byte for byte against the
pinned sources. Those live color entries are unchanged. Eleven full-pixel
identities pass coarse layout screening, minimum zero-offset correlation .9644,
with no preferred tested offset. This screening does not establish exact
placement of every small feature or final art approval.

## Catalog and native verification

All 4,001 world keys remain. Eleven normal values change; 3,990 remain identical.
Every output page round-trips, and the existing 16 MiB per-page and 512 MiB total
limits remain. One changed page splits; the final 78 pages total 524,919,424 bytes
(500.60 MiB), leaving 11.40 MiB. Future batches require bounded resolutions and
an explicit memory plan before adding larger maps. No sample reaches the .4
slope cap; maximum authored slope is .115. Global strength is not baked in.

Fresh original C1M1 route runs preserve all 2,600 frame/draw-count/hash triples.
Renderer logs confirm the four encountered material keys bind to world normals,
beyond the dedicated catalog indices; this is evidence for those four live keys,
not a claim that all eleven variants appeared. Runs use the same resolved midday
light, world strength 1.5 and replay video off. Both stop intentionally at the
presentation budget, rather than crashing or completing the mission.

The village frame changes 35,885 pixels with mean absolute channel difference
.0283/255 over the full image. At this distance the effect is modest; this
measurement is content-response evidence, not a quality score. The field frame
changes 5,692 pixels. Close-range inspection and user review remain necessary.

Only `Play MW3 - Material Normal Preview.cmd` selects this batch. Installation
changes exactly its `MW34_WORLD_NORMALS` field; the corrected batch 4 dedicated
ground catalog and all other profile fields stay identical. No engine/executable
change or new performance benchmark is part of this asset batch.

Execution boundary advanced: three more village material families now have
source-matched structural relief reaching original campaign rendering, and one
ruin family has a restrained grain refinement. Acceptance remains 131/144;
whole-campaign coverage, final art approval and the first-100 pass remain open.
Next in encounter order are `thedude06/05/03/04/07`, followed by power-line materials.

Local evidence: `C:/Users/jcbla/MW34SunTests/campaign-village-batch5-20261018/`.
Editable recipes/maps: ignored `local/material-authoring-r1/authored-batch5/`.
No original or derived asset is added to version control; no commit is made.

## Posted screenshots and zoom check

- [Village before](https://drive.google.com/file/d/10M8AApUNnOIR3zt0r524L5YfNzSiPZmb/view?usp=drivesdk)
- [Village after](https://drive.google.com/file/d/1jaZeYIuA3xUKbOn33OQj_D7pKHVM-VTf/view?usp=drivesdk)

Both are lossless 3440 × 1440 native frames. Drive metadata readback confirms
names, byte sizes and destination folder; sharing is unchanged. Original texture
and height assets are not uploaded. These distant views do not establish final
close-range quality. A separate pair holding original reticule zoom also matches
all 2,600 draw triples, but primarily frames a roof and surrounding ground;
those captures remain local and are not presented as close façade proof.
