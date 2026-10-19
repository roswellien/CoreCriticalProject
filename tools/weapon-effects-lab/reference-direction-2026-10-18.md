# Weapon and fire reference review — 2026-10-18

The user rejected the initial Gauss/explosion appearance and requested a study of
the effects currently configured for MW3 plus their local Pyrefall fluid fire.
This pass changes no effect implementation, playable build, lighting code or
Pyrefall files. The r1 previews remain initial scaffolding, not approved artwork.

## Material inspected and evidence boundary

Private output is `local/weapon-effects-reference-review-20261018-r1/`.
Original `reader.zbd` was exported using the existing local mech3ax
v0.7.0-rc3 tool; its directory identity matches the existing mission-data record
SHA256 `5e17037f3634480f74265b3e378e4513b84cae518e20bc55cd5c6e9c6683851a`.
Training `anim.zbd` was also exported to a private ZIP. The exporter printed
interval warnings, including `ppc_fire`; these exports are used for structural
reference, not timing validation or successful native activation claims.

Original C1/T1 texture entries were decoded with the existing strict decoder.
Current entries were read from the C1/T1 banks selected by
`local/work-ahead/texture-launcher-audit-v2/configured-banks.json`, which the
native asset preparer uses. These are enhanced textures, not unchanged originals.
The 13 selected entries in each bank cover both muzzles/trails, the eight PPC
impact frames and `laser_impact_blue`. Decoded source hashes/dimensions and
current entry comparisons are retained in `source-comparison.json`.

Current bank flag 43 has an additional 0x20 bit compared with original flag 11.
The private inspection requires the exact RGB565/byte-alpha plane size and
normalizes only a copied descriptor for the existing decoder. No bank is edited.
Selected-entry reading was narrowed to bounded file seeks after an initial
whole-bank decoder attempt refused flag 43. Whole current-bank hashes in the
comparison record are explicitly inherited manifest identities, not freshly
recomputed hashes. Bank size/mtime stability was checked over the bounded reads.

Two local contact sheets show original and current textures on black. They are
texture references, not game-rendered frames; blending, model geometry, tint,
clipping, branch selection and effective lifetime can change their appearance.
An active native lighting-performance job was observed and left undisturbed.
No additional live firing run was launched. Live side-by-side firing remains
required before calling the redesigned effects original-comparable.

## PPC: preserve the blue-violet electrical identity

`weapons.zrd` separates `ppc_muzl.flt`, `ppc_fire`, `ppc_trail.flt` and
`impact_ppc_mech`. The muzzle has a bright white body with a violet-blue fringe;
the current trail texture depicts connected lightning-like strands, not a string
of detached circular motes. `Support/effects.gw` binds both PPC impact nodes to
the eight `plsbrn01`–`plsbrn08` maps. They expand from a bright point into a ragged
electrical ring, then break up. Raw speed token 12 is not a measured FPS value.

Compiled Training animation data contains connected trail objects and a PPC
flight puffer using `laser_impact_blue`; its stored lifetime range is 0.5–0.7
and distance interval is 2. These are data values, not recovered wall-clock
units or evidence that every branch currently executes. Original data also
defines blue-violet flight/muzzle/impact point lights, some inside rendering
conditionals. Their presence does not prove the current Vulkan backend lights
receivers from them.

Revised target: white-hot compact core, connected irregular blue-violet ribbon,
secondary fine motes, and a ring-shaped electrical impact using the original
sequence as a silhouette/timing reference. Preserve distinct launch, flight and
impact stages. The r1 dot trail and radial orange-firework vocabulary are not
sufficient. Do not change trajectory, impact location or simulation duration.

## Gauss: preserve green launch/flight and its own impact response

`weapons.zrd` separates `gaus_muzl.flt`, `gaus_fire`, `gaus_trail.flt` and
`gaus_impact`; dirt additionally references `large_pock.flt`. Original and current
`GAUSMUZ` are green-white directional flashes. `gaustrail` is an elongated green
streak/cluster. `gaus_fire` has an attached green flight-light definition with
RGB approximately (0.2, 0.9, 0.2); the muzzle uses the same green family.

The impact is not simply an orange explosion: the compiled definition calls
`blue_starburst_small` and `green_puff`, and contains a pale green-white light
and green framebuffer-flash branches. Rendering branches, original visibility
checks and native timing still need live confirmation.

Revised target: directional green-white muzzle pulse, a fast coherent green
flight cue, and a compact sharp impact combining green/blue energy cues with
surface-appropriate dust/fragments. The generic warm radial muzzle sparks in
r1 miss the game's weapon identity and omit travel/impact entirely. Keep the
effect readable at native projectile speed; do not slow the shot for spectacle.

## Pyrefall: shared flow, shaped flame, separate smoke and embers

The local product named PYREFALL is in `D:/Projects/CitySurvivor`, with a separate
Phaser 4 checkout at `D:/Projects/CitySurvivor-phaser4`. Inspection used the former
and did not build or modify either. The README identifies the product despite
the older folder name. Inspected source hashes are in the private comparison.

Primary references:

- `src/render/fx/fluidSim.ts`: GPU 2D velocity/dye fields with semi-Lagrangian
  advection, buoyancy, vorticity confinement and pressure projection. It is not
  a full 3D combustion/temperature solver.
- `src/config/fluidSimConfig.ts`: 256-square motion/pressure grid, 512-square
  dye, 20 pressure iterations and a capped slowed visual timestep. These are
  Pyrefall parameters, not MW3 budgets or game-unit defaults.
- `src/render/fx/pyreFluidFirePipeline.ts`: shaped burn/noise flame whose
  silhouette bends and tears with the fluid gradient; density feeds/starves
  its body. Flame color and opacity come from the burn model rather than a
  pile of additive glow discs.
- `src/config/pyreFireConfig.ts`: seven differently seeded/depth-offset sheets,
  each partially transparent, with different heights/widths/speeds. Hot core,
  orange body and darker tips accumulate into an apparent volume.
- `src/render/fx/pyreFluidSmokePipeline.ts` and `src/config/pyreFluidConfig.ts`:
  smoke shares the field but has independent motion/opacity/coupling controls.
  Embers drift with the same plume; lights sway/breathe with the flame.
- `src/render/fluidPyre.ts`: emitter, field, flame, smoke, lights and ember
  coupling. It is a substantially closer appearance reference than r1's dots.

Performance lesson: `fluidSim.ts` documents previous GPU readback stalls and
now harvests an older encoded velocity field before encoding the next one.
For MW3, prefer GPU-side particle/flow coupling; any CPU sampling must use a
measured delayed/asynchronous design. Do not introduce a per-frame wait for
fresh GPU flow. No Pyrefall timings are claimed as MW3 measurements.

Revised target: a coherent anchored flame with torn upward tongues and hot-core
color structure; billowing smoke carried by the same broad flow; sparse embers
that rise, curl and cool; bounded representative lights driven by that motion.
Use the same visual language for explosion fire/smoke, with a rapid initial
expansion and slower buoyant billow. Spark fragments are secondary to the body.

This is inspiration, not a direct engine port. Pyrefall's screen-space/isometric
field and layered sheets cannot be dropped unchanged into a free-camera 3D
mech game. Test layered billboards or baked flow-driven flipbooks first in the
isolated lab, then investigate a bounded local 3D/2.5D field if the appearance
and measured cost justify it. World axes/units, camera rotation, depth/fog,
near clipping, overdraw, intersecting geometry and receiver lighting need native
contracts. No dependencies or code from Pyrefall are copied in this review.

## Next separate implementation

1. Replace the lab's Gauss muzzle-only scene with launch -> green travel cue ->
   explicitly supplied impact. Add connected PPC ribbon and electrical ring
   alongside a local original/current texture reference, with timings labelled.
2. Replace round fire blobs with a shaped layered plume driven by coherent flow;
   keep independent smoke and sparse embers. Rework explosion body/billow after
   that foundation, rather than increasing the current radial particle count.
3. Review silhouette, palette, motion and opacity before integrating lights.
   Add native PPC/Gauss live-reference captures in a private run only when the
   existing long job is clear. Preserve actual original source state and timing.
4. Bind only through the lighting engine's reviewed interface after readiness.
   Do not modify the current playable host, shader bindings or launcher defaults.

No native execution boundary or acceptance count advances in this research pass.
The existing verified count remains 131/144. Proprietary assets/exports remain
local; only authored guidance is added to source. Nothing is committed.
