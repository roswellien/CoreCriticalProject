# Weapon presentation and status preview repair

The requested boundary is original game rendering into modern presentation:
retain simulation, damage, weapon timing, projectile paths and original smoke.
This work does not advance the formal native-game acceptance count of 131/144.

The status defect is a mismatched depth clear, rather than replacement model
framing. The original HUD owner calls its player and target depth-fill producers
at saved returns `0x43c748` (player/right) and `0x43c72a` (target/left).
The surface `DDBLT_DEPTHFILL` path
previously filled the original rectangle, while the preview geometry used the
widescreen rectangle. Nearby cockpit or world depth can therefore hide part of
the schematic. Only those two authenticated depth-fill scopes now use the same
rectangle transform as their preview draws.

The authored near-occluder regression reproduces 1,600 hidden pixels out of
4,300 player-preview pixels at 3440x1440 (37.2%), and 900 out of 5,700 at 16:9.
The corrected functions pass 52 checks with no hidden preview pixels, unchanged
4:3 coverage, retained unrelated world depth, unchanged unknown/frontend scopes,
and preserved guest floating-point control. A native Thor comparison then
reproduces the missing right lower leg/boot and restores it with the corrected
clear. All 2,100 original draw fingerprints and 1,379 detailed draw records
match the control. Damage tint, wireframe and component-bar modes are retained.

Rocket exhaust attaches to actual live original missile bodies. The original
`0x585010` factory supplies a definition and a pooled projectile descriptor;
its flyout root and active-list ownership authenticate the instance. Complete
original LRM/SRM body geometry hashes identify each body within multi-rocket
models. The original post-`0x51fb30` body matrix supplies the nozzle transform,
avoiding the projectile position field that can advance ahead of the visual.
The local rear points along +Z. Authored crossed flame ribbons and a nozzle glow
use a procedural RGBA texture, depth testing, and no depth writes. No original
media needs to be repacked for the effect.

Each nozzle has a tracked orange point light in the existing combined 64-light
budget, with at most eight rocket lights so salvos leave capacity for other
effects and fixtures. Movement replaces that source's previous position. Retirement, pooled
reuse, root destruction and mission changes remove its light, including while
the presentation clock is frozen. Smoke is not a light source. The feature can
be disabled for comparison with `MW34_MISSILE_EXHAUST=0`.

PPC muzzle and bolt/trail light power is multiplied by 1.25 at uniform emission.
Existing installed MWFX1 catalogs remain valid and unchanged. Radius, colour,
lifetime and budgets retain their previous values. Shared blue impact textures
also represent lasers, so those ambiguous impacts are not boosted.

Authored checks cover 291 PPC cases, 635 tracked-light cases, 19,574 flame
geometry/texture cases and 41 asset-free stage-integration cases. An additional
private original-geometry input exercises 84 binding checks, including exact
body admission, world-space nozzle placement, floating-point preservation and
unchanged guest memory. Private original vertices are not embedded in tests.
The native firing comparison observes LRM15 and LRM20 salvos, 38 authenticated
projectile creations and 1,524 exhaust submissions, with bright plumes visible
through the retained smoke and warm illumination on nearby models.

Maintained entry points are `apply_weapon_presentation.py` and
`apply_status_preview_clear.py` under `tools/remaster-launcher`. Apply them to a
fresh copy of the selected host source. The effect applicator preserves the
selected fixture-shadow uniform extension. Existing performance batching and
the separate clean-install texture-storage repair must remain in the combined
runtime. Native binaries are delivered through the existing signed precompiled
`.mw3update` path; no original media or code regeneration is required.

The final runtime is signed and selected by the dev profile. The current
38-bank environment completes a 2,100-frame native Thor firing run with replay
off, retained performance batching, correct preview clears and actual PPC
catalog matches. Native muzzle/bolt values are 2.8 to 3.5 and 2.2 to 2.75.
SRM attachment is covered by private original-geometry binding checks; the
Thor/Vulture native route exercises LRM15 and LRM20 rather than SRMs.

The offline `mw3-weapon-presentation-20261023-r1` update uses sequence
2026102310 and requires launcher 1.0.27 or newer. Its exact signed payload
passes verification, installation, activation, validation and rollback from
both installer 1.0.28 and performance revision 6 in isolated application roots.
The ordinary ZIP wrapper is `CoreCriticalGameUpdate.zip`; it contains matching
`.mw3update` metadata and payload ZIP for local import. Public downloads were
not changed by this task.

## Upgraded models in both HUD previews

The follow-up implementation admits installed replacement geometry into the
original player and target textured 3D previews. It captures the original
model-view matrix after 51FB30, then waits for each original component's first
actual primitive before copying its complete render state and rounded vertex
fog factor. The model shader carries that diagnostic factor separately from
opaque diffuse alpha. World atmosphere remains excluded. Original game code,
component health, visibility, missing-limb decisions and both generic 2D damage
display modes continue executing unchanged.

Preview emission and donor-pose caches reset at each original 4F73F0 preview
entry, before the existing extended-distance adapter can return. This avoids
sharing a rendered-owner cache with the world or another status window. An
early test exposed the importance of this ordering: an incorrectly placed
reset displayed the replacement once, then suppressed it on later frames.
That candidate was never selected in the dev profile.

Native 2,100-frame tests observe Thor/player plus Vulture/target simultaneously,
and Mad Cat on both sides. The Thor left-arm diagnostic factors progress from
255 to 183 to 110 before original arm-loss identity changes at frame 2075.
The replacement disappears with the destroyed arm; original stump handling is
retained. A matched baseline/candidate route retains all 2,100 original draw
count/hash records exactly. The resident GPU fixture passes 18 checks for
independent actor damage, healthy and absent components, changing damage over
frames, world-haze exclusion and zero CPU-transformed TL payload.

Mad Cat's upgraded walking pose exposed an additional concrete defect: a foot
can extend below the original preview rectangle. A follow-up fit pass uses the
actual original per-window depth-clear rectangle, before widescreen adjustment.
It bounds resident GPU batches using eight corners rather than transforming
their vertices, then changes only queued preview projections and retained CPU
preview parts. It never enlarges geometry and leaves fitting models in place.
The authored fit checks pass 902 cases. The original depth-clear/near-occluder
fixture passes 60 checks including rectangle capture at 16:9, ultrawide and 4:3.

Maintained sources are `apply_status_models.py`, `compile_model_shader.py`,
`native-overrides/model_scene.vert`, `status_model_fit.hpp` and
`status_model_fit_stage.inc` under `tools/remaster-launcher`. Native evidence
showed that 4F73F0 ends its D3D scene before returning, so the fit must run at
the start of `render_scene`, while that preview's commands still exist. A
per-preview applied flag prevents a second adjustment. The explicit device
argument retains the correct scene after EndScene clears its `in_scene` flag.
The earlier after-return fit candidate is retained as a failed experiment.

The final candidate is `D:/MW3StatusModels-20261023-r4`. It also retains the
installer chat's exact two validated compact-monitor sources, including its
transparent tile and smaller glyphs. With the monitor enabled, native runs
cover Mad Cat on both sides and Thor/player plus Vulture/target. Three final
candidate runs each complete 2,100 presented frames. The matched monitor-on
parent/candidate comparison has all 2,100 original draw count/hash records
identical. All logged replacement-preview batches use resident GPU geometry;
none takes the CPU near-plane path. Actual captures show both Mad Cat feet
inside the frame during walking and preserve Thor damage tint and arm loss.

One initial combined run faulted after presented frame 1991, in
`flat_fault_throw`, with host exception C0000005 at a MOVAPS instruction
while constructing the fault message; a stack-alignment fault is suspected.
Its primary guest-fault cause was not recovered. It did not recur in three
subsequent complete candidate runs or the matched parent control. This is
retained as an unresolved isolated failure, not claimed fixed or attributed
to the monitor. Evidence is in the final candidate's `final-review.json`,
`candidate-madcat-fit-r3` failure and subsequent native run directories.

The signed release is `D:/MW3StatusModelsUpdate-20261023-r2`, version
`mw3-status-models-20261023-r2`, sequence 2026102311, minimum launcher 1.0.27.
Its signed host SHA256 is
`6f6b6e341a37989a3353313d3675a93a648ea6d12f0e9ed1411cfc9628f4c85d`.
The translated module remains unchanged. The ordinary ZIP wrapper contains
matching `.mw3update` metadata and payload for local import, with no code
regeneration. The provisional release under `MW3StatusModelsUpdate-20261023-r1`
predates the fit correction and must not be deployed. Public downloads are
unchanged; formal acceptance remains 131/144.

The exact signed final package passes verification, installation, activation,
validation and rollback against isolated installer 1.0.28 and prior
weapon-presentation runtimes. The dev launcher now selects the final signed
host, and its ordinary preflight passes with all prepared models and installed
bank bindings. Deployment changes only native executable/module/snapshot
identity fields; graphics, monitor preference, installed packs and performance
flags are preserved, including replay off. The final offline wrapper is
`D:/MW3StatusModelsUpdate-20261023-r2/CoreCriticalGameUpdate.zip` (35,938,766
bytes). Nothing was uploaded or committed for this follow-up.

## Doubled missile thrust visibility

The next user-requested tuning doubles the plume length, width and nozzle-glow
size relative to the original exhaust implementation. The procedural atlas
uses twice the additive opacity gain, clamped to the existing texture channel
range; RGB heat colors and transparent borders are retained. Its texture hash
changes so a cached older atlas cannot satisfy the new binding. Attached
rocket-light intensity increases from 2.2 to 4.4. Radius 8, lifetime .055,
eight-rocket/64-total light limits, primitive counts, original smoke and all
projectile simulation stay unchanged. PPC's separate 1.25 gain is retained.

Only `missile_exhaust.hpp` and `missile_exhaust_stage.inc` change in the native
host. `apply_missile_exhaust_gain.py` admits the known previous revision or an
identical already-applied revision, avoiding replacement of other writers'
changes. The candidate inherits the complete signed status-model runtime,
including preview fitting, damage tint, compact monitor and prior performance
and texture-storage repairs.

The authored checks pass 19,578 exhaust cases, 48 binding/emission cases,
291 unchanged PPC cases and 635 tracked-light cases. The emission fixture
checks actual cache-uniform intensity 4.4, one draw and 18 vertices, and zero
guest-memory changes. Matched native Thor LRM runs each complete 2,100 frames;
all 2,100 original draw count/hash records match, with original projectile
creation counts unchanged. Dense frames 1280/1282/1284/1286 show larger,
brighter orange exhaust. The private comparison is
`D:/MW3MissileGain-20261023-r1/thrust-before-after.png`. This native route
exercises LRM15/LRM20; the common SRM presentation gain shares the same code.

The signed release is `D:/MW3MissileGainUpdate-20261023-r1`, update version
`mw3-missile-thrust-20261023-r1`, sequence 2026102312, minimum launcher 1.0.27.
Native executable SHA256 is
`0a787590a4f12f24fd99d0b3e09ccebf1656f43f569bd4dadd98a02865999aa8`.
Its `.mw3update` delivery uses the same original-input verification and
no-regeneration runtime-copy path. Formal acceptance remains 131/144.

The exact package passes signed verification, installation, activation,
validation and rollback against installer 1.0.28 and the prior status-model
runtime. The dev launcher now selects it, with the final selected-runtime
preflight passing and existing graphics, monitor preference, pack bindings
and replay-off/performance flags preserved. Its offline wrapper is
`D:/MW3MissileGainUpdate-20261023-r1/CoreCriticalGameUpdate.zip` (35,940,164
bytes). No public upload or commit was performed.
