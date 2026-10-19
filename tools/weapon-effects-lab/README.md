# Isolated weapon effects lab

**Current direction (2026-10-18): keep the existing sprites/textures and add
dynamic lighting. Particle replacement previews are parked.** Start with the
[sprite-lighting direction and integration handoff](sprite-lighting-direction.md).
Lighting-only review: `C:/Users/jcbla/MW34EffectsLab/sprite-lighting-r1/preview.html`.
The particle revisions below remain historical experiments and are not approved
runtime replacements. No game/launcher/lighting-engine source is modified.

Authorized 2026-10-18 as a separate preparation lane, for integration after the
lighting engine is ready. Nothing in this directory is included by the main
project, host composition recipe, launcher or current playable build.

**Current revision: r13**, conical Gauss burst with denser sparks/embers, continuing the
[MW3/Pyrefall reference review](reference-direction-2026-10-18.md).
Earlier r1/r2 outputs are retained for comparison; they are not overwritten.
Current review: `C:/Users/jcbla/MW34EffectsLab/particles-r13/preview.html`.

## Side-by-side source-animation comparison

Open `C:/Users/jcbla/MW34EffectsLab/particles-r13/comparison.html` for a
synchronized PPC/Gauss/fire source-reference vs current particle-study view.
The left defaults to currently configured texture replacements; switch to stock
MW3 textures to see the original pixels. Pause/scrub or replay both panels
together, with adjustable playback speed. Muzzle/trail thumbnails are static
component references below the weapon impact playback.

This is **not captured default-game animation footage**. PPC uses the admitted
eight-frame texture order and fire the sixteen-frame `fire_f` order, with
explicitly assumed review rates. Gauss illustrates the source-linked
`green_puff` / `blue_starburst_small` composition; position, camera-facing
orientation, size and blending are not original-renderer validation. Source
`green_puff.flt` binds `green_exp01.tif`; `blue_starbursts.flt` binds
`blue_starburst.tif` and `spark_part5.tif`, recovered through Training GameZ
node -> model -> polygon material -> texture references. The reference draws
approximate those components rather than pretending to replay the full graph.
GameZ extraction produced transform-precision warnings; those exports grant
no native timing/transform fidelity claim. An exact in-game A/B remains pending
dedicated original-compatible firing captures. No fake scene capture is used.

The page embeds the unchanged r13 particle HTML and adds a parent-only,
validated scene/time message bridge in the embedded copy. Only local reference
assets and native snapshots are embedded; no network access or game launch is
needed. All proprietary imagery remains in the private output. Recreate into a
fresh filename beside a built lab preview:

```powershell
python tools/weapon-effects-lab/prepare_comparison.py --particle-preview C:/Users/jcbla/MW34EffectsLab/particles-r13/preview.html --output C:/Users/jcbla/MW34EffectsLab/particles-r13/comparison-next.html
node tools/weapon-effects-lab/test_comparison.cjs C:/Users/jcbla/MW34EffectsLab/particles-r13/comparison-next.html
```

Preparation reads only bounded selected entries from the published bank,
records exact source-entry hashes and checks file stability. Whole-bank current
identities remain inherited manifest hashes, explicitly not freshly verified.
Stock C1 bank identity is freshly checked. The first comparison passes offline
controls/synchronization tests (219 reference draws), including wrong-parent
and nonfinite time rejection. Browser composited pixels remain unverified.

## Build and review

From the project root, using the existing local Visual Studio C++ tools:

```powershell
python tools/weapon-effects-lab/build.py --out C:/Users/jcbla/MW34EffectsLab/particles-r13
node tools/weapon-effects-lab/test_preview.cjs C:/Users/jcbla/MW34EffectsLab/particles-r13/preview.html
```

Open the resulting `preview.html` in a browser. It is self-contained and uses no
network requests or proprietary assets. It embeds snapshots exported by the
actual C++ implementation, rather than duplicating the particle simulation in
JavaScript. Select PPC, Gauss, Fire or Explosion; pause/scrub, slow playback,
orbit, or disable particles/illustrative lighting independently. Every effect opens
on a populated review frame, including when reduced-motion preferences pause
playback. Burst loops skip the long empty tail; the timeline still exposes the full
four-second sample range. Standalone CMake also works on other hosts;
the convenience script uses the existing VS installation on Windows.

## Implemented boundary

`effects.hpp` consumes explicitly supplied visual events in host-owned state and
produces bounded particle/ribbon snapshots and representative light requests. The
native standalone exporter also runs an authored fixed-step 2D flow bake in
`flow.hpp`; heat/density fields produce separate flame/smoke images. The viewer
projects native geometry and draws the baked images on layered Canvas sheets.
This is a reusable CPU effect foundation and an illustrative renderer,
not Vulkan particle rendering or a live-game PPC implementation. No E1-E4 game
boundary or formal acceptance criterion is closed. Acceptance remains 131/144.

Profiles: directional blue-violet PPC flash, connected electrical ribbon and
ragged ring impact; green-white Gauss muzzle, fast green flight streak and
separate compact energy impact; coherent fluid-driven flame/smoke with sparse
embers; expanding fire body followed by smoke billows and secondary sparks.
These are authored appearance studies. Material-specific impacts, GPU flow
simulation, soft depth intersections, HDR/bloom, scene occlusion and physical
debris are not implemented. Particle gravity affects
only visual sparks, never original projectiles. Smoke has no gameplay occlusion.

## Contract for the later game adapter

- Input has scene epoch, source identity plus monotonically increasing generation,
  kind, activation/end times, position and velocity. The lab uses right-handed
  Y-up metres/seconds; native game units/axes still require measured conversion.
  The current moving profile supports straight constant-velocity observations.
  Real varying trajectories require a sampled/updated original trajectory contract
  before use; do not substitute this extrapolation for original projectile state.
- End times are explicit bounded inputs (maximum 30 seconds per event). Stop
  shortens emission and extinguishes source lights while born particles finish
  their tails. A continuous fire longer than that bound needs an explicit renewal
  design before game integration. Bursts fire once, at activation.
- A `sample(time)` call is pure: it doesn't spawn into mutable pools or advance
  random state. Birth slots and per-key hashes make it independent of render rate
  and camera passes. Visual randomness never calls the original RNG. This is
  same-build repeatability, not a cross-platform bitwise floating-point promise.
- Duplicate/stale generations are rejected. New generations may coexist with
  older tails. Explicit retirement drops expired records while retaining source
  generation tombstones until scene reset. Reset requires a different nonzero
  scene epoch; the adapter must allocate unique epochs and reject stale inputs.
- Validate finite values, supported kinds, nonzero identities and bounded times/
  coordinates. Invalid inputs throw, while duplicate/stale, wrong-scene and
  capacity outcomes are explicit `Submit` values. Failed capacity admission does
  not consume a generation. Caller must handle each outcome visibly in dev logs.
- Default limits are 128 event records, 1024 source tombstones, 4096 particles,
  128 ribbons and 8 lights. Ribbon paths have at most 65 authored points.
  Particle/ribbon truncation uses stable source/generation order; lights use
  relative intensity followed by identity. Omitted counts expose saturation.
  These are initial safety limits, not measured game quality/performance targets.
  Long missions require measured tombstone budgets or a separately proven source
  ownership release contract; never clear generations to bypass the limit.
- Snapshot scene/time accompany a complete light list. The lighting consumer must
  replace this lane's prior list once per scene/time, then reuse it for camera
  views; it must not accumulate requests per draw. Reset/unload must clear the
  consumer's list as well. Colors are linear RGB; brightness/radius are authored
  relative values awaiting calibration. No shader descriptor/ABI is imposed here.

Continuous emitters birth at fixed time slots before the observed end. PPC trails
remain behind the observed moving source. Impact is a separate explicit event;
the lab never computes a collision from a destination or creates game damage.
The preview's PPC hit at 1.15 seconds is an authored fixture only.

Gauss preview flight lasts 0.25–0.61 seconds; its impact is an independently
supplied event at 0.61. Muzzle and impact have distinct source identities.
These times and speeds are convenient lab values, not measured game behavior.

## Revision 2 flow and visual boundary

The asset-free C++ baker uses a 64×96 two-dimensional field: semi-Lagrangian
advection, buoyancy, vorticity confinement, a 16-iteration pressure solve, and
independent cooling/density dissipation. A distributed irregular source feeds
fire continuously or gives an explosion a brief expanding impulse. Coherent
noise shapes the burn edge and smoke shading, following the reference's idea of
flow plus procedural flame shaping. No Pyrefall source/assets/dependencies were
copied. This is a visual solver, not a validated physical combustion model.

The exporter advances exactly two 1/60-second steps per 30-Hz review frame.
`build.py` packages native RGBA planes as embedded PNGs using only Python's
standard library. Separate smoke and seven partially transparent flame sheets
suggest volume. Their shared flow and differing chord-like widths give a
connected body; embers/sparks remain sparse. The viewer image cache is bounded
by the finite exported sequence. Pixel colors are explicitly authored Canvas
display colors, not a calibrated native linear/HDR material contract.

The bake is outside the game's update loop and lighting engine. Free-camera 3D
geometry intersections, side-on sheets, scene occlusion and native depth/fog
remain integration work. No runtime-performance improvement or visual parity is
claimed from this bake. Fire light-source wobble follows the broad emitter sway;
floor spill remains illustrative. The consumer's lighting ABI is unchanged.

## Integration sequence after lighting readiness

1. Recover a live PPC weapon -> projectile -> original effect/impact association,
   including generations, actual transform/timing and stop/destruction/unload.
   The existing Orion laser observer is reusable research, not PPC coverage.
   Recover the required projectile trajectory and native coordinate conversion.
2. In a private host clone, create a read-only producer adapter. Preserve guest
   ABI/FP/LastError, original random calls, timing and required producer effects.
   Never infer ownership by texture, proximity or a shared weapon definition.
3. Add an isolated Vulkan billboard/trail renderer with the original depth/fog
   ordering. Keep additive emission separate from alpha-composited smoke. Match
   alpha convention; sort smoke appropriately, depth-test particles and avoid
   transparent depth writes. Prove near clipping, zoom and authenticated views.
4. Bind representative light requests through the lighting engine's reviewed
   interface. Start with one moving PPC light and one impact light. No per-spark
   lights or shadow resources are requested by this preparation lane.
5. Compare disabled controls and matched original state; then inspect moving-arm
   attachment, impact position, destruction, reload and sustained combat. Measure
   CPU/GPU frame costs and overdraw before expanding budgets or adding bloom.
   Add Gauss tracer/impact and other weapons only after their own associations.

All future enhancements remain independently configurable. Missing associations
must be identified explicitly and leave original presentation in place. The
separate visual correction for replacement-model laser muzzle positions must
preserve original simulation origins and hit endpoints; this lab does not apply it.

## Checks and limitations

Revision 13 adds 120 fast fine sparks and 40 slower cooling ember motes to the
Gauss impact, within the same outward cone. They vary deterministically in
velocity, size and lifetime; gravity bends their travel and brightness cools.
The slower motes continue after the hot body ends. Existing four-color accent
mapping applies. No extra light requests or lifetime/budget expansion is added.
Release CTest verifies the 160-mote shower and surviving embers; viewer controls
pass. Removing only the new ordinal range from the export reproduces r12 exactly,
including the hot body, dust, fragments, all other effects and light records.
The current game/lighting work and prior preview outputs remain untouched.

Revision 12 makes Gauss's hot explosion conical: three axial groups of hot lobes
start narrow near the hit and widen away along the authored armor normal (-X).
The 0.75 body scale factor, fast timing and warm fire ramp remain. Dust, metal
chips and glowing chunks now share a roughly 35-degree half-angle outward cone;
gravity bends their subsequent motion. Real surface-normal binding remains a
future game adapter contract, not an inferred collision. Release CTest verifies
initial ejecta containment and a hot body that extends/widens away from the hit;
viewer controls pass. Native PPC/fire/explosion and Gauss launch/travel samples
match r11 exactly. No current game or lighting files were changed.

Revision 11 reduces Gauss's hot explosion body to 75% of r10's linear size:
both lobe offsets about the hit and individual lobe sizes scale by 0.75.
Timing, colors, opacity, glowing fragment trajectories, dust and light requests
are unchanged. Release CTest and viewer controls pass. A direct native-export
comparison verifies the 0.75 scaling within JSON output precision and equality
of every non-body particle and all other scene/light/ribbon samples. Earlier
previews and the current game/lighting work remain untouched.

Revision 10 addresses the user's report that the hot material was not visible.
Gauss now has nine large high-opacity hot lobes at the hit plus sixteen glowing
ejecta chunks, on a dedicated hot-material layer with an irregular flame outline
and white/yellow/orange/red heat ramp. This is distinct from faint additive glow
dots and preserves the warm hot-body appearance regardless of spark palette.
The body expands rapidly and fades within 0.31 real preview seconds; glowing
fragments last up to 0.45 seconds. A warm representative light follows the hot
body instead of ending after the contact flash. Dust/metal fragments persist.
Release CTest and offline viewer checks pass, including all 25 incandescent
elements, warm light lifetime, and nine large opaque hot lobes on the initial
Gauss review frame. Native PPC/fire/explosion and pre-hit Gauss snapshots remain
exactly equal to r9. The current game, lighting engine and prior outputs are
untouched. This remains a visual armor-impact concept, not an armor-physics
claim; final browser composited pixels remain unverified.

Revision 9 applies the owner's correction: the four-color request was Gauss
only, and its impact should erupt outward like a heavy round striking ablative
armor. The preview opens on Gauss. Its burst increases to 192 particles, with a
broader outward surface-facing hemisphere, faster/larger fragments, denser dust
and a short-lived hot-material flare. No electrical arcs or ring are introduced.
Green/orange/purple/teal accents apply only to Gauss hot particles and illustrative
contact spill; dust and armor chips remain material-colored. PPC ignores the
palette completely and returns to its blue-violet appearance. Launch/travel and
the fast impact clock are retained. This is a cosmetic spall/burst study, not a
model of real armor penetration, projectile energy or armor damage.
Release CTest and viewer checks pass, including the dense fragment/dust burst,
Gauss initial selection and exclusion of PPC from the palette. Native PPC,
fire/explosion and pre-impact Gauss samples match r8 exactly. Game/lighting files
and earlier preview outputs are untouched; final browser pixels are unverified.

Revision 8 adds green, orange, purple and teal impact color choices plus an
"All four together" mode. Following the owner's clarification, the preview
defaults to all four together. In mixed mode,
attached PPC arc pairs share colors and sparks vary by stable particle ordinal;
the representative floor spill is neutral rather than spawning extra lights.
Dust and physical metal fragments retain their material colors. Launch/travel,
fire/explosion, geometry, brightness peaks and timing are not recolored or
retimed. This is a display-only review palette: the exporter adds explicit
authored-fixture impact/ordinal tags; it does not guess real game ownership.
Native particle/light/geometry values remain identical to r7 after removing
those new tags. Release CTest and offline viewer controls pass, including all
five modes, brightness preservation, mixed color distribution and exclusion of
debris/unrelated draws. No game build or lighting code/defaults were changed.

Revision 7 follows the owner's clarification that Gauss is a heavy slug strike.
Its impact no longer emits a green shockwave, electrical streaks or an energy
halo. Hard irregular metal fragments use a new non-emissive debris layer with
ordinary alpha compositing. They rebound toward the incoming shot and fall under
the existing visual gravity. A small number of hot-metal sparks, a broader
neutral dust plume and a brief warm-white contact flash complete the hit.
The contact light ends within 0.08 real preview seconds under the 2× impact clock.
Fragments/dust remain cosmetic; no armor damage, terrain collision or persistent
crater is implemented. Gauss launch/travel retain the earlier reference styling.
Release CTest and offline viewer controls pass, including checks for no impact
ribbons/green energy, fragment rebound, dust/spark presence and contact-light
expiry. PPC/fire/explosion and pre-impact Gauss exports match r6 exactly. Current
game/lighting files and all previous preview revisions remain untouched.

Revision 6 corrects the interpretation of "lightning strike": the owner intended
an electrical explosion outward FROM the hit, not a separate bolt arriving from
above after the projectile. Twelve irregular primary channels now start exactly
at the impact point and expand rapidly in distributed directions/depth. Each
has an attached outward fork. The incoming overhead channel is removed; short
electrical pulses, localized fragments/vapor and the fast clock are retained.
CTest verifies all primary roots equal the hit position and every fork is
attached to its own channel. Release build and viewer controls pass. Gauss,
fire, explosion and all pre-impact PPC native snapshots match r5 exactly.
No current game build, lighting work or prior preview output was modified.

Revision 5 replaces PPC impact shells with a full-length jagged 17-point
white-violet strike and ten attached forks. The strike appears immediately;
two brief restrikes drive channel brightness, central flash and illustrative
light requests together. Spark count falls to 72 and bright fragments remain
localized, so discharge geometry is the primary cue. Cooling vapor remains.
This is a stylized local electrical strike, not weather or a changed projectile.
The 2× impact clock is retained. CTest and offline viewer controls pass; added
checks require attached forks, an open main channel, no closed blast rings and
a distinct restrike pulse. Native export comparisons retain every Gauss, fire,
explosion and pre-impact PPC frame exactly from r4. Prior previews and the game
build/lighting files remain untouched. Final browser pixels remain unverified.

Revision 4 speeds both complete impact envelopes to 2× while retaining r3's
large geometry: shock expansion, discharges, ejecta, flash/light and dust/vapor
fade advance together. PPC/Gauss maximum tails are now 0.8/0.7 seconds;
retirement uses the same shortened clock. Impact review frames are adjusted
accordingly. Release CTest and offline viewer checks pass, including shortened
envelope completion. Fire/explosion and every pre-impact weapon snapshot match
r3 exactly. Previous preview files and game/lighting files remain untouched.

Revision 3 responds to the user's request for larger, more violent PPC/Gauss
impacts. Rapid shock-front expansion replaces the small slow rings: PPC has two
ragged shells and eleven crooked discharge branches; Gauss has a large shock
front, seven shorter streaks and faster ejecta biased back toward the incoming
shot in this authored +X test scene. Both gain a short white-hot flash, a colored
envelope and larger cooling vapor/dust. Impact particle budgets rise from 22
to 120 PPC / 96 Gauss; tails are 1.6 / 1.4 seconds. Light requests are broader
and stronger, but remain illustrative consumer inputs, not lighting-engine edits.
Surface-normal-based ejecta and real material responses remain future bindings.

PPC/Gauss now open on an impact review frame, and **Replay impact** starts just
before the hit. The existing full-shot timeline/loop remains available. Release
CTest passes 59,059 authored checks, including enlarged impact radius, branching,
ejecta count and surviving aftermath. Offline viewer checks pass 1,768 image
draws (296 fluid sheets), 351 ribbon strokes and both impact replay controls.
The final native export matches r2 exactly for all pre-impact PPC/Gauss frames,
both fire/explosion scene snapshots and all 484 raw fluid planes. No other
effect animation or game/lighting source was changed by this revision.

Revision 2 Windows x64 Release build passes with warnings treated as errors.
The final fixture passes 29,266 checks including connected-ribbon finiteness and
budgets, green Gauss identity, fixed-step flow repeatability, a visible flame
body and persistent explosion smoke. Offline viewer checks exercise all four
selectors, reduced-motion initial frames, scrubbing/looping and layer controls:
749 image draws (288 fluid sheets) and 72 ribbon strokes. Exported fire/explosion
PNG sequences were visually inspected as a local contact sheet at
`C:/Users/jcbla/MW34EffectsLab/particles-r2/flow-review.png`. This verifies the
baked imagery, not the browser's final composited pixels; browser appearance
remains unverified because local-file access is blocked by the browser tool's
policy. The prior r1 preview remains intact for comparison.

The C++ fixture checks repeatability across sampling rates, duplicate callbacks,
source reuse, stop/tail behavior, scene reset, budget/order behavior, malformed
inputs and finite output throughout every profile. Release builds treat warnings
as errors. Offline viewer checks execute the actual viewer script against a
minimal Canvas/DOM fixture, exercising controls and finite draw coordinates.
They do not verify browser pixels, appearance, GPU performance or native game
behavior. A visual review and live integration remain required.

Initial Windows x64 Release build on 2026-10-18 passed with MSVC 19.51 `/W4
/WX`: CTest passed, including 34,071 authored particle checks. The offline viewer
control test passed with 1,639 sprite draw calls. Browser automation refused the
local-file URL under its security policy; no workaround was attempted, and no
browser appearance or pixel validation is claimed. Built review output is
`C:/Users/jcbla/MW34EffectsLab/particles-r1/preview.html`.

Follow-up on 2026-10-18: the user reported visible controls/grid with no particles.
The viewer started and selected every scene at time zero, before all emitters
activated at 0.25 seconds; reduced-motion mode paused there indefinitely. This
blank-start defect is corrected with populated per-effect review frames, explicit
paused status and shorter occupied-range loops. Regression checks require actual
sprite draw calls immediately on initialization and selection of all four scenes,
and check the short-burst loop boundary. Updated offline checks pass (2,348 sprite
draw calls); CTest remains passing. Browser policy still blocks local-file
observation, so actual displayed browser pixels remain unverified.

Existing dirty files, current game binaries/configuration, lighting shaders,
host adapters, original pilots/registry and protected processes are outside this
build. No original media or generated game code is needed; no commit is made.
