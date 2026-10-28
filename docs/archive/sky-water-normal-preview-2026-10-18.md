# Sky and water surface-detail continuation

Recorded 2026-10-18. This is an isolated C1 preview extension of the current
Normal Mapping Preview, using its Big Lake sun/sky/ambient settings and current
upgraded texture-bank map, including the recent shoreline color correction.
It does not activate the [campaign progression plan](../campaign-lighting-progression-plan.md).

## Execution boundary

Extend the existing native Vulkan material path with optional water, surf and
cloud roles. Registration uses complete uploaded color content, dimensions and
pixel format. It never selects a material by a guest address or filename alone.
Original game logic, geometry, UVs, texture-bank bytes, alpha/color keys, surf
animation and all 37,201 original native objects remain unchanged.

Water previously received automatic terrain normals where registered. This
extension supplies a separate moving water field, rather than claiming water
was universally excluded from the previous pass.

## Material behavior

- Water uses a small periodic ripple-normal tile sampled in world XZ, with two
  counterflows and a restrained sun highlight. Host presentation time drives the
  movement; no guest clock is queried or replaced. Every scene in a presentation
  uses the same cached phase. A fixed phase is available for diagnostic captures.
- The water side of the C1 surf atlas uses the same field and phase. Normal-map
  alpha masks neutral foam and warm sand out of ripple lighting. The mask comes
  from the upgraded, color-corrected surf frames; it does not replace their color
  or original animation. Normal sampling repeats while albedo sampling retains
  the original sampler. Distant fine ripples fade to reduce shimmer. The surf
  mask uses explicitly clamped bilinear taps, so the repeating ripple sampler
  cannot pull sand/foam across the opposite atlas edge. Water skips the generic
  terrain-normal sample that its dedicated field would otherwise overwrite.
- Cloud relief is a conservative filtered height estimate from upgraded sky
  artwork. It gently changes the existing sky response around unity, using the
  sun direction and UV derivatives. It fades with the existing horizon blend.
  This is cloud-surface relief, not volumetric clouds or normal mapping of empty
  atmosphere. Existing glow, haze, original alpha and sky colors remain in use.
- Cloud registrations are explicitly excluded from ordinary opaque TL lighting.
  Without this exclusion, registering a sky texture admits it as a lit world
  surface before sky capture, creating polygon-shaped horizon edges.

The initial local selection covers C1 `txwat01d`, `sky01` and `wave01` through
`wave13` in all six upgraded bank variants: 4 water identities, 26 surf identities
and 2 cloud identities. The three packs total about 2.07 MiB. They read only
pinned upgraded banks, verified before and after generation. Other maps retain
their existing treatment pending explicit material selection and visual review.

## Controls and composition

`MW34_WATER_DETAIL` and `MW34_CLOUD_DETAIL` independently enable their paths;
both default off. Strength controls are `MW34_WATER_DETAIL_STRENGTH` (default
0.45) and `MW34_CLOUD_DETAIL_STRENGTH` (0.35). Water scale and speed default to
0.06 and 0.025. `MW34_NORMAL_MAPS=0` bypasses both effects. Enabled roles require
valid `MW34_WATER_NORMALS`, `MW34_SURF_NORMALS` and/or `MW34_CLOUD_NORMALS`
sidecars. Invalid parameters, missing required packs, conflicting registrations
and excessive pack sizes fail visibly. Each role is limited to 16 MiB and the
existing BWSNR2 image/key limits. Authored material registrations retain priority;
conflicts are rejected. Detail packs take precedence over automatic world pages.

The host adapter is authored in
`tools/remaster-launcher/apply_surface_detail.py`; apply it after the material
normal and camera adapters to a private copy. The generator is
`tools/remaster-launcher/prepare_surface_detail.py`. Authored shaders and all four
shared uniform declarations are compiled together. The sun uniform grows from
320 to 352 bytes; the shadow-only vertex shader uses push constants and is
unchanged. New provider work preserves full guest FP state and LastError.

Local build, selection, packs and run evidence are under
`C:/Users/jcbla/MW34SunTests/sky-water-detail-r1/`. Original-compatible launchers
and the current Normal Mapping Preview remain independently available. No assets,
original game code or binaries are committed. Formal acceptance remains 131/144.

## Verification

Three authored Python checks cover shared water/surf normal RGB, protected
foam/sand, unchanged source pixels, exactly neutral flat clouds and bounded cloud
slopes/atlas borders. Actual Vulkan fixtures cover moving ripples, matching
water/surf phase, masked regions, cloud response, phase wrapping and global
maps-off. They also exercise the actual TL capture adapter to prevent sky
registration from becoming ordinary world lighting. Existing sun, camera,
normal-binding, HUD and fog fixtures continue to pass on the RX 9070.

The first native candidate exposed the sky-admission defect above. Its captures
are retained as failed visual evidence; it is not an installable release.
`host-r2` corrected that admission and passed sunset, midday, fixed-phase and
global maps-off native comparisons, each with 1,200 original draw records intact.
`host-r3` adds the clamped atlas-mask edge treatment and avoids the redundant
generic water normal sample. Clean composition retains all 92 source files,
and the original object list is byte-identical to the current preview.

The final `host-r3` SHA-256 is
`b6d5ea85f0c0c4f2fec5ece30ac015d59e901cff071cb98a6b9ddbab840408a0`.
Its four 1,200-frame native runs cover detail disabled, both effects at sunset,
an alternate fixed water phase, and both effects at midday. Each exactly retains
the corresponding installed build's original frame/draw-count/hash triples.
The runs reached their expected diagnostic frame-budget stop; this is not a
claim of mission completion or normal interactive quit. All tests used hidden
windows and independent test pilots/registries.

Live matching records show the open-water texture, all 13 surf animation frames
and the upgraded sky texture receiving their dedicated normals. The alternate
phase changes only the water region (rows 668–1439 in these views), while original
draw records and the sky stay unchanged. Sunset and midday captures were reviewed
for continuous sky/horizon appearance. Close shoreline travel still needs live
playtesting; this fixed camera is farther out in the water.

The recompiled feature-off shader is **not bit-identical** to the old build:
one capture matches exactly, while two captures each differ by one RGB565 pixel
(maximum channel differences 8 and 4). No broader visual change or original draw
divergence was observed in those controls. The supplemental `host-r2` global
maps-off native pair shows the same small differences and allocates no world
normal pixel pages. Final `host-r3` GPU fixtures separately verify maps-off.

Local evidence: `comparison-release.json`, `sunset-comparison-release.png`,
`midday-comparison-release.png`, the retained `runs/` directories and the source
snapshot in `local/sky-water-detail-r1/`. The launcher rejects incompatible host
metadata and changed detail packs; the existing Normal Mapping Preview still
passes its launch check.

## Testing entry point

Use **Play MW3 - Sky and Water Preview.cmd** for C1 testing. Its default is the
existing sunset preset. The **(Sunrise)** and **(Midday)** launchers select those
same shared presets. Interactive launches use the host's real presentation time;
they contain no hidden-window, scripted-input, virtual-clock or fixed-phase
override. The profile retains the current model roster, remastered menu, rollover
animation, general world normals and C1 shoreline color correction. It does not
include the unpromoted Firefly texture candidate.

These bounded checks do not establish campaign completion, all-map coverage,
complete absence of sky seams during camera travel, or a performance benchmark.
The effects add shader work; no performance improvement is claimed. Campaign
lighting transitions, night/weather capabilities and material selection for
Training and other Operations remain separate work.

## User visual review: improvement remains unfinished

The user reported that the before/after overview screenshots show no discernible
improvement. Functional/native checks above do not establish visual acceptance.
At frame 1190, representative cloud and water crops average only 0.503 and
1.064 absolute RGB-channel steps out of 255 from the existing preview. These are
small changes, particularly in the reduced overview comparisons.

A further 1,200-frame diagnostic used water strength 1.4 and cloud strength 1.2,
with original draw records still exact. Those crops average 1.721 and 2.629
channel steps respectively. Native-resolution review still shows mostly modest
lighting/contrast changes over the existing painted artwork. The interactive
defaults and final-host binary were not changed by this experiment.

The visible result should therefore be treated as unfinished. Recommended next
work is a more convincing water reflection/highlight response and directional
cloud lighting, assessed in close and moving views. Increasing normal strength
alone has not demonstrated the intended visual improvement. The diagnostic
evidence is retained locally under `sky-water-detail-r1/visibility-diagnostic/`;
it is not a promoted release or new acceptance credit.
