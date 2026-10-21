# World lighting repair — 2026-10-20

R7 repairs the procedural fixture and campaign environment integration in the
existing native host. It retains the upgraded texture/normal assets, remastered
menu and current 16-model registry, including the experimental detailed MW3
Avatar. Original simulation, weapons, AI, missions and saves remain in control.
Acceptance stays **131/144**. The [repair plan](world-lighting-repair-plan-2026-10-20.md)
records the authorized scope.

## Changes and execution boundary

- Point lights, laser capsules and spotlights now use distinct GPU protocol tags.
  Spotlight direction no longer changes laser segment interpretation.
- One selected environment supplies terrain, object and mech receiver lighting,
  sky, atmosphere and shadow preparation. User-disabled sun shadows stay disabled.
  The active [20-mission art plan](campaign-lighting-progression-plan.md) supplies
  the mission settings; no replacement schedule or invented clock is introduced.
- Wetness, dust/smog and height fog have dedicated uniform fields, separate from
  water motion and cloud controls. Lightning follows presentation time and holds
  during a paused rendering clock. A minimum ambient fill preserves night
  readability while retaining the authored ambient hue.
- Successful, read-only mission-reader opens select exact campaign identities.
  Failed opens and save filenames cannot select missions. Pending loads survive
  the loading frontend; returning to the frontend and entering Training, Instant
  Action or multiplayer clears the campaign context.
- Fixture sources track node/polygon identity, source state, material generation
  and map lifetime. Verified static sources survive camera culling; anonymous
  sources expire each frame. Changed or removed sources lose their emitters until
  safely observed again. The cache is bounded to 512 sources.
- The configured 16-light limit covers both weapons and fixtures. Eight slots
  remain reserved for weapons by default; fixtures use at most eight. Procedural
  emission uses bright texture regions without the previous whole-texture floor.
  Unverified hard-coded map emitters and map-wide lava-height lighting are disabled.
- Launcher defaults keep automatic campaign selection active. An explicit
  `--lighting-preset` selects manual lighting. The selected profile's upgraded
  normal-map registry is used unless `--registry` explicitly overrides it.

## Verification

The R7 Clang-CL/Ninja executable is
`local/material-authoring-r1/native-lighting-integrated-r7/build/entry_commandline.exe`,
SHA-256 `f250b3002f363ffcf70090824a0394ce91bc0be28652d21d9f9b8f0df962d2d5`.
All 37,201 existing translated objects remain; generated source and media stay local.

Actual Vulkan receiver tests on an AMD Radeon RX 9070 cover point/capsule/spot
lighting, cone rejection, radius, normal response, HUD exclusion and stale lists.
Campaign lightning is pixel-identical at a held presentation time and changes
after time advances. Surface fixtures cover water phase, surf continuity,
protected masks, clouds and disabled controls. CPU contracts exercise all 20
mission identities, manual mode, load failures, menu/mode resets, weather-field
independence, fixture updates/removal/expiry and combined light budgets.

Bounded original-input native runs enter Operation 1 Missions 1 and 3, Training
and Instant Action. The actual PowerShell launch path entered Campaign Mission 1
and completed normal native shutdown with a successful Windows Help release and
`ExitProcess(0)`. These checks do not establish all-20 live playthroughs or mission
completion. Physical photo-mode hotkeys and long-session stability were not
revalidated in this repair.

Evidence resides at `reports/world-lighting-repair-20261020`, through the existing
Games-drive reports junction. Earlier review failures remain at
`reports/world-fixture-review-20261020`. Earlier diagnostic R7 images and runs
precede the final night-fill adjustment; files named `final` use the hash above.

## Matched fixture performance

Four trials per setting used the same stationary Training view, original input,
1,500 measured presentation intervals after warm-up, 3440×1440, FXAA, 16× AF,
1200-unit draw distance, manual night lighting, sun shadows off, weather off and
replay off. Weapon lighting remained enabled; fixture emission and illumination
toggled together. Simulation used a controlled 16.666667 ms step; timings use
actual wall-clock presentation intervals. Optional traces were disabled; the
existing world audit remained. The fourth pair captured images after measurement.

| Pair | Fixtures off FPS | Fixtures on FPS |
| --- | ---: | ---: |
| 1 | 103.53 | 102.56 |
| 2 | 109.80 | 108.44 |
| 3 | 103.68 | 90.95 |
| 4 | 104.28 | 96.93 |

Mean frame time was **9.500 ms off / 10.071 ms on**, an increase of **0.571 ms**
and a **5.67% reduction in average FPS**. Eight fixture lights were submitted in
the on trials; geometry counters matched across all eight runs. The slower
third and fourth on trials remain included. This is a bounded scene cost,
not a whole-game estimate or evidence of negligible overhead. Raw results,
percentiles, run identities and executable hashes are in `performance.json`.

The stationary Training captures are pixel-identical: the submitted fixtures
do not visibly illuminate that captured view. They establish a rendering-cost
baseline, not an appearance comparison. The Instant Action night capture shows
PPC/impact illumination of a structure and terrain; it is weapon-light evidence.
Two additional 3,600-frame moving Training controls differ only in the fixture
toggle. Paired captures show warm illumination on the ground; the frame-2000
pair demonstrates the effect more clearly than the stationary benchmark view.
The original game's rain remains present in both controls. That is not evidence
of newly implemented rain particles.

## Use and remaining limits

**Subsequent launcher update:** Play MW3Remaster and the GUI now select the
display/material/F12 derivative of R7. Its source/executable identities and
maintained lighting headers are verified in the
[texture audit and launcher check](texture-light-audit-2026-10-20.md). The
borderless limitation below records the original R7 publication state and is
superseded for that newer main-launcher host.

Use **`Play MW3 - Material Normal Preview.cmd`** for the verified R7 lighting
configuration, or the existing Dynamic Night Lighting Preview shortcut. All three
lighting profiles select R7. The main GUI's concurrent display work adds choices
outside this host's published capabilities; the retained `fullscreen_windowed`
setting fails the graphics-support check until its compatible display host is
published. The lighting repair does not silently substitute a different display
mode. The published profiles and rollback
copies are identified in `reports/world-lighting-repair-20261020/publication.json`.
Display preferences and other writers' asset changes are preserved; replay stays
off by default. The independent CLI controls are `--fixture-lights 0|1` and
`--weather 0|1` on `tools/remaster-launcher/play_remaster.py`.

Local lights remain unshadowed and can shine through obstacles. The catalog
recognizes a limited set of texture families; it is not a complete authored lamp
placement pass. Texture luminance approximates luminous regions; authored UV
masks, spotlight directions and per-map appearance still need art review.
Anonymous billboard sources do not persist off camera. Scene-state validation
can conservatively remove an emitter until it is reobserved.

Wet surface response is not pooled reflections. Rain particles, volumetric beams,
falling ash and genuine heat distortion remain unfinished. The old broad claims
of fully implemented campaign weather and negligible fixture cost are superseded
by this record. Mission-start/end transitions still need durations and triggers
where the art plan does not specify them.

Remote review: [screenshots and results on Google Drive](https://drive.google.com/drive/folders/1zRIL6kyJlFCmAVx1_mkjNLpEWGXHaPbJ).
