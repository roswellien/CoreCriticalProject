# Black Hawk and Champion MW5 port candidates

Update 2026-10-16: both initial clean color drafts now have separate
[maintained-but-well-used texture sets](blackhawk-champion-worn-textures-2026-10-16.md).
The approved Black Hawk walk is retained. These remain offline candidates.

The user selected Black Hawk (Clan Nova) and Champion as the next pair. Local
installed MW5 packages were found, decoded and assembled with exterior cockpits
and modular weapons. Black Hawk has twelve Clan ER medium lasers. Champion's
donor visual selection uses the original MW3 primary weapon classes, including
LB 10-X and ordinary medium/small lasers. Original game loadouts are unchanged.
The main donor body meshes have 34,407 and 32,162 triangles respectively, before
separate cockpit/weapon assemblies. Initial MW3-inspired color/material sets
and source comparison scenes are in the ignored workspace:
`local/work-ahead/mw3-blackhawk-champion-r1/`.

## Rejected Black Hawk leg fit

The user correctly rejected the first runtime-shaped preview: the affine fit
stretched the donor thighs to MW3's much longer upper-leg interval and raised
the body. Contact blending did not repair the underlying silhouette change.
The old payload is retained as rejected evidence, with a prominent marker;
its exporter refuses to regenerate Black Hawk. Champion can be reproduced
separately with `--champion-only`. Neither chassis is registered in the launcher.

The replacement in `leg-correction-r2/` starts from the pristine assembled donor
scene. Mesh coordinates, topology, UVs and all donor rest skeleton matrices
remain unchanged. Its rest pose matches the donor within 0.00000334 matrix
units. The source MW3 walk supplies root motion, foot lift and stride. A visual
two-link solve retains the donor hip/knee/ankle positions and rigid lengths.
The walking foot midpoint is aligned to the donor stance: using MW3's forward
standing-foot position as the stride center biased every goal backward. Each
knee retains its donor bend branch, and each thigh bends in its original plane.
There is no added joint/filler geometry or individual thigh side roll.

The full source cycle has 57 samples over 1.866667 seconds. At 225 sampled
times both legs retain their lengths, with maximum errors below 0.0000009 model
units; no foot goal requires stretching or reach clamping. Independent
evaluation of the saved Blender action checks 449 times, including between
keys: maximum knee contact error 0.00000258, ankle contact error 0.00000160,
and local scale error 0.00000036. The mesh/UV/rest-skeleton digest is
`215137d20aeea281e2e8907cb17db5099f3ac7f316491f8cdd2648cfc9efd3fd`.

Reviewed standing, walking and side renders, plus four phases from both front
and side. The 1440x720, 336-frame video repeats six cycles in 11.2 seconds.
Six preview files and their folder placement were verified by Drive metadata
readback under Models / Black Hawk - Nova / R2. Sharing settings are unchanged.

- [Corrected comparison and walking previews](https://drive.google.com/drive/folders/1_Kw5HzGsh9HHFGX1BRE4SUfmpEjW9X95).
- [Walking video](https://drive.google.com/file/d/1dBtdMWP_1kY0CsT1Xby__dHMPlCbNZ3a/view?usp=drivesdk).

## Execution boundary and remaining work

This advances decoded/assembled assets to a corrected offline stand/walk
candidate. It does not advance native game execution. The existing rigid
native mesh adapter cannot reproduce this visual joint solve simply by loading
the old stretched payload; an explicit optional visual retarget is required.
Original gameplay joints, simulation, weapons, collisions and animation
selection must remain authoritative. Do not install the rejected payload.

Damage/fall animation, firing-origin alignment, LODs, native integration and
in-game performance remain open. Three donor toe roots per side currently
share two source toe controls. Champion's donor SRM and small-laser visual
mounts use different controllers from their original MW3 firing nodes; this
is recorded, not resolved by moving the original gameplay firepoints. Its
initial fitted candidate also still needs visual/motion approval. The stronger
texture standard is now authored in the separate revision linked above.

The existing seven launcher models, all registered textures and native profile
are unchanged by the Black Hawk correction. Thor's separate R2 color revision
is documented separately. No game launch, desktop screenshot, protected
registry/pilot edit or commit. The composer/watcher processes were untouched.
Strict acceptance remains paused at 131/144; these assets earn no native credit.
