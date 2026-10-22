# Lower horizon rendering correction

The user confirmed terrain was corrected, then reported that the lower sky
was broken again. The preceding restriction only admitted an untextured lower
backdrop if depth writes were disabled or all vertex depths were exactly zero.
It consequently excluded the positive-depth, depth-writing untextured horizon
case that the initial broad sky change admitted.

The correction admits an untextured far horizon even with depth writes enabled.
Both solid-lighting capture and atmosphere use the same bounded far-depth test.
Registered textured sky keeps its existing role-based exclusion; ordinary
textured terrain stays on its solid-lighting path at every tested distance.
Untextured geometry with nearby or mixed depths and explicitly overridden
textures retain surface lighting. No camera distances or asset packs changed.

The actual capture-adapter fixture reproduces unwanted horizon lighting on the
preceding build and passes on this successor. Controls cover textured distant
terrain, nearby untextured geometry, mixed depths, texture overrides, registered
sky and invalid depth. This is offline regression evidence; the reported live
lower-sky appearance has not been independently captured or visually confirmed.

Only `sky_backdrop.hpp` and `sun_tl_capture_stage.inc` differ from the preceding
host. All other existing host sources, including artwork/mech/resource readers
and camera-distance handling, are identical. Exact successor admissions retain
installed pack compatibility, including the previously rejected menu revision.
The native profile and self-contained launcher are published locally. Evidence
and publication hashes: `local/work-ahead/lower-horizon-repair-20261022-r1/`.

No game was launched and no user processes were stopped. No pack was removed,
reinstalled or changed. Strict acceptance remains 131/144; no commit was made.
