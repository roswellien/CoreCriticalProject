# Isolated Vulkan HUD pass

First integration step for the private v3 component package described in
[the handoff](../../docs/hud-vulkan-integration-handoff.md). This emits SCN4 HUD
draw commands for the existing Vulkan replay backend. It does not replace the
HUD in MW3 or consume live gameplay state.

`prepare.py` admits the manifest-pinned `components.json`, uses explicit anchors
for four gauge frames, a center reticle and an ally arrow, and adds a diagnostic
`HUD PASS` label. It excludes synthetic telemetry, illustrative panels and the
identical zoom placeholders. `HudDraw` carries component/font IDs, logical
destination, anchor, clip, color and ordered layer. The sample positions are
static component placement, not recovered visibility or state rules.

`rasterize.cjs` executes the prototype's actual `vector()` function, with fresh
system-Arial rasterization. Individual textures have two transparent padding
pixels on every side and straight alpha. Logical component sizes, glyph advance
and baseline remain separate from physical texture dimensions. Bilinear samples
use clamp addressing. RGB values are blended in encoded UNORM space; this is an
explicit prototype choice, not original-game color-space equivalence. Original
GDI measurement and positive cell-height font semantics remain unrecovered.

The pass renders at final output resolution. Its isolated fixture has its own
depth initialized/cleared to zero, quads at one and no depth writes. A future
world compositor must use depth-disabled HUD pipelines or a separate HUD depth
attachment; it must not clear the world depth attachment to reuse this fixture.
Rectangular clipping adjusts quad positions and UVs. This pass has individual
texture uploads, not an atlas or a performance-optimized glyph cache.

Prepare a fresh ignored directory:

```powershell
python tools/vulkan-hud/prepare.py local/work-ahead/hud-fidelity-v3/components.json reports/vulkan-hud/new-input --width 3440 --height 1440 --density 3 --canvas-package C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas
```

`verify.py` prepares and executes six GPU cases, including 4:3, 16:9, ultrawide,
75% HUD size and 4x texture density at unchanged logical size. Its CPU oracle
independently computes bilinear samples and straight-alpha compositing, checks
padding, centered reticles and logical gauge sizes, and compares every pixel:

```powershell
python tools/vulkan-hud/verify.py local/work-ahead/hud-fidelity-v3/components.json reports/vulkan-hud/new-validation --canvas-package C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@napi-rs/canvas
```

Resolve the native Canvas dependency for other hosts. Font resolution fails
explicitly if Arial is unavailable. Existing Vulkan replay executable, shaders
and validation layers are prerequisites. Generated packages, RGBA payloads and
PNGs contain private source-derived material and belong under ignored local or
report directories.

The 2026-10-10 run is `reports/vulkan-hud/validation-v1/verification.json`:
six cases, zero Vulkan validation messages, maximum channel discrepancy one
against the CPU oracle. This validates compositing of these selected components,
not original HUD fidelity, timing, dynamic gameplay state or live replacement.

Next: recover host-side HUD state and visibility, feed component selection and
text through an explicit adapter, then identify/suppress original HUD commands
and establish final-frame ordering. Screen-center elements and world-projected
markers require different coordinate contracts. No recovered telemetry provider
currently exists in `runtime/graphics`; static binary addresses in the handoff
are investigation entry points rather than callable state contracts.

## Recorded original speed text (2026-10-10)

The optional graphics observer `build.ps1 -Launch -CaptureHudText` now hooks
the admitted MW3 text-cache DrawTextA IAT slot at 0x5bb6f8. It observes only
the three recovered measurement/shadow/main return sites after 3D scenes begin,
with a 256-record/512-byte-per-string bound. It forwards the original pointer,
length, rectangle and flags unchanged and preserves the real call's return and
FP/LastError state around instrumentation. It changes no installed file.

Run `reports/graphics-trace/20261010-060714-562` produced 256 valid observations:
Training objectives, timers, labels and changing speed strings. The user
confirmed normal Training/HUD/quit; its passive monitor recorded exit code 0,
zero alerts and zero dropped segments. Module evidence was collected manually;
automatic module collection remained unavailable in the legacy child shell.

`observe_state.py` verifies trace identity and passive evidence, then extracts
48 completed main-draw speed observations with explicit KPH units. The selected
last complete sample is `30.4\nKPH`, with Arial height -8, weight 300, original
COLORREF and a 29x21 logical cache rectangle. This is displayed/rounded speed,
not a recovered internal simulation field. Text-cache calls are generic; no
component ownership is inferred merely from the callsite. No heat amount,
heading, weapon selection, zoom or target coordinates are populated.

Prepare this recorded input with `--observed-state` pointing at the JSON emitted
by `observe_state.py`. The builder re-verifies the original run and requires
exact agreement with the supplied state; altered values cannot silently become
original-game evidence. The recorded text is rendered at output density while
retaining observed logical dimensions, font height and color. Line spacing is
inferred from returned text height; baseline and exact GDI equivalence remain
unproven. Its right-side placement remains the prototype's placement, since the
cache rectangle is local, not the final on-screen destination.

`reports/vulkan-hud/recorded-speed-v2/verification.json` records a 3440x1440
GPU/oracle comparison: maximum channel discrepancy one, zero Vulkan validation
messages. The six static component regressions also passed freshly under
`reports/vulkan-hud/validation-v2`. Neither pass replaces MW3's HUD or streams
live state. Next recover downstream cache destination, clipping and layer,
then add runtime updates and original-HUD suppression.

## Observed speed destination (2026-10-10)

The text draw at 0x5a10d0 calls the image dispatcher at 0x55b1f0 through two
identity-checked CALL sites, 0x5a1169 and 0x5a1192. The optional HUD observer now
records these calls before tail-jumping to the original routine. A naked x86
bridge saves integer registers/flags, guards instrumentation FP/LastError state,
and forwards original ECX=image, EDX=X and stack Y/flags/rectangle unchanged.
The caller's ESI supplies the text object; its +0x248 image pointer must equal
the image argument. The forwarding fixture verifies register/stack arguments,
rectangle mutation, return register and LastError. The original draw remains
enabled. The two CALL operands change only in the launched process.

Run `reports/graphics-trace/20261010-061535-504` produced 512 valid text draws,
including ten speed draws. It used the RGB16 software dispatcher 0x55b3c0 and
a 640x480 target with 1280-byte stride. The speed cache was drawn at **602,304**,
size **29x21**, source rectangle **[0,0,29,21]**. Static instructions in that
dispatcher subtract source rectangle endpoints to obtain width/height and clip
the destination against target bounds; the rectangle is a source crop, not a
destination viewport. Admission currently rejects other dispatchers, crops,
target sizes and out-of-target speed draws rather than approximating them.

The user confirmed normal HUD/gameplay/quit. The passive monitor
`reports/mw3-monitor/20261010-061559-7d56b3bd` recorded exit code 0, no alerts
and no dropped segments. Provider/module/source identity verification passed.
The 512-record prefix ended during early Training, so its correlated speed
sample is `-0.0\nKPH`. Later text-cache updates alone do not establish later
destination/order observations. Records carry text-draw sequence and completed
scene/draw counters; they do not establish total world/HUD command order.

`observe_state.py` now correlates speed text, cache dimensions/font and source
crop within this verified run, selecting the last admitted text/destination
pair. It retains the draw-log digest and source object/image identity. This is
a correlation of matching text and compatible counters, not a recovered owner
pointer in the earlier GDI observation. The 640x480 renderer reproduces the
observed destination. Wider outputs use an explicit right/top anchor policy
for this speed element; that policy is not an observed original widescreen
layout. GDI baseline and pixel equivalence remain open.

Receipts:

- `reports/vulkan-hud/placed-speed-640x480-v1/verification.json`
- `reports/vulkan-hud/placed-speed-3440x1440-v1/verification.json`
- `reports/vulkan-hud/placement-controls-v1.json`

Both GPU cases passed with maximum channel error one against the independent
compositing oracle and zero Vulkan validation messages. Four controls rejected
mixed PID, reordered draw, unsupported dispatcher and altered source crop.
Next: sample later gameplay draw changes without exhausting the prefix on
repeated unchanged text; recover the remaining HUD paths and presentation order
before replacing or suppressing original HUD rendering.

### Transition sampling and combat check

The optional original-runtime observers now suppress consecutive identical
records per source: caller/HDC for text-cache calls and caller/text-object for
final draws. Signatures include text, geometry and the recorded rendering
contract. A transition back to an earlier value is retained. Each observer
keeps at most 128 source signatures; additional sources remain observable.
The existing 256 text and 512 draw record limits remain unchanged. Records
identify `sampling: source_transitions`; their sequence numbers enumerate
retained observations, not every original call. Unchanged calls are omitted,
so this capture cannot establish complete frame ordering or frame counts.
Forwarding and transition fixtures run before launch. Future manual gameplay
checks use Instant Action with movement and firing, then a normal quit.

Instant Action run `reports/graphics-trace/20261010-062518-318` passed
identity/provider checks and passive monitor `20261010-062526-10d21190`;
the user confirmed normal gameplay, HUD and quitting. Text capture retained
256 records through scene 860 and draw capture 512 through scene 2230.
There are 53 admitted main speed samples; the last correlated text/destination
pair is 16.7 KPH at (602,304), with a 29x21 logical cache. Weapon labels were
also observed, but weapon selection/ammunition/heat semantics are not recovered.
Both observers reached their budgets, so later combat coverage is incomplete.
The recorded speed passed isolated Vulkan checks at 640x480 and 3440x1440:
maximum channel error one against the compositing oracle, zero validation
messages. Wider placement remains host policy. Receipts are under
`reports/vulkan-hud/instant-action-speed-*`; four negative placement controls
passed in `instant-action-placement-controls.json`. This is recorded-state
replay, not a live replacement HUD.

`build.ps1 -CaptureHudText -CaptureHudSkipScenes 600 -Launch` delays both
observers until completed scene count exceeds 600. This is a scene-count
selection, not a fixed elapsed-time delay. The default remains zero. The
request stores the delay; the selected value is bounded to 36000. Older
non-numeric request markers retain zero-delay compatibility. The follow-up
manual check fires while stationary before movement to reduce speed/range
churn consuming the bounded logs. `instant-action-display-inventory.json`
groups prior observed strings by object without assigning gameplay semantics.

Delayed Instant Action run `20261010-062956-833` passed identity/provider and
passive shutdown checks (`20261010-063001-f2cf1de4`); the user confirmed normal
gameplay, HUD and quitting. Text retained scenes 605–893 and draws 605–1931.
The moving target's range updates still dominated the budgets even with this
selection. Five numeric weapon-area objects remained unchanged (20, 200, 200,
360, 360). No ammunition decrement or numeric heat value was established.
`reports/vulkan-hud/delayed-instant-action-inventory.json` pins and groups this
evidence. A later capture needs per-source budget isolation or recovered
weapon/meter paths, rather than another identical delay-only run.

The follow-up observer limits final draws to 16 retained transitions per
caller/object pair, and text-cache calls to eight per caller/DC/text-pattern
bucket. A pattern collapses digit runs to `#`; this groups changing target
distances without assigning gameplay semantics. The pattern uses the safely
captured input text, not the possibly mutated buffer after DrawText returns.
At most 128 sources are tracked per observer; new sources beyond that limit
are omitted. Global limits remain 256 text and 512 draw records. Records
declare `bounded_source_transitions` and their per-source limit. This deliberately
omits later transitions in a busy source and cannot establish complete combat
coverage. Pre-launch fixtures check duplicate suppression, transitions back,
per-source exhaustion and isolation, plus original ABI forwarding. The new
check starts at the first gameplay scenes to retain initial weapon readouts.

Run `20261010-063325-171` passed provider/identity and passive shutdown checks
with monitor `20261010-063331-e496e016`; user gameplay/HUD/quit were normal.
It retained 184 text records and 226 draws, reaching results/menu screens.
Four independent text objects at x610, y70/80/90/100 each displayed 40 through
25 in unit decrements. `recover_counters.py` admits this observed profile and
preserves strings, logical 15x13 bounds, destinations, source object/image,
scene counters and draw sequences. It does not assign internal ammunition
fields or weapon identities. Receipts: `combat-counter-state.json` and
`combat-counter-controls.json` under `reports/vulkan-hud`; altered geometry,
broken decrement and missing row were rejected. Heat meter values remain
unrecovered. The counters are prepared recorded-state evidence and are not yet
drawn by the isolated Vulkan HUD pass.

### Recorded counters in the Vulkan pass

`prepare.py --counter-state <verified-state.json>` now adds four recorded
counter strings with 15x13 logical sizes independently of raster density.
The state is regenerated from the admitted source run and must match exactly.
`recover_counters.py` correlates each retained counter with an earlier matching
main text-cache draw to recover Arial -10, weight/color and cache dimensions.
The latest correlated value is 33, although final-draw observations reach 25.
The rasterizer's GDI baseline equivalence remains unproven.

Receipts `combat-counters-640x480-v1/verification.json` and
`combat-counters-3440x1440-v1/verification.json` under `reports/vulkan-hud`
confirm four counters, original destinations at x610/y70,80,90,100,
maximum channel error one against the compositing oracle and zero validation
messages. The ultrawide uses explicit host right/top anchoring. The preview
combines independently selected speed and counter samples from different
moments; it is not a synchronized frame or live replacement. A forged display
value is rejected in `combat-counter-state-control-v1.json`. The older
`combat-counter-state.json` predates font correlation and is historical evidence;
use `combat-counter-render-state-v1.json` with the current preparer.

User review corrected the left triangle to green and smaller. The isolated
pass overrides `hud_allyarrow_right` to #00eb00 and half its source logical
size (7x12.5); private v3 assets remain unchanged. This size is a preview
choice, not a recovered original-game measurement. Both original-resolution
and ultrawide `combat-counters-*-arrow-v2` receipts passed with maximum channel
error one and zero validation messages. The rasterizer applies logical scale
before output density, retaining independent texture resolution.

### Same-scene counter sequence

verify_counter_sequence.py replays the eight cache-correlated snapshots (40
through 33) with all four rows observed in the same completed scene. It omits
independently selected speed. Nine cases (eight at 640x480, final at 3440x1440)
passed with maximum channel error one and zero validation messages in
reports/vulkan-hud/counter-sequence-v2. An unobserved scene is rejected; all
eight GPU images are distinct (image-uniqueness-verification.json).

This exposed a prior font bug: LOGFONT weight zero means FW_DONTCARE, but the
rasterizer passed invalid CSS weight zero, leaving counter glyphs absent.
It now maps zero to normal CSS weight 400. Earlier counter previews and the
counter-sequence-v1 receipt are superseded; their compositing oracle checks
did not establish that glyphs were present. The current verifier requires
both distinct packages and distinct GPU images. Source run/frame timing,
full-HUD synchronization, GDI pixel equivalence and live replacement remain
unproven. Use counter-sequence-v2/counter-state.json with the updated schema.

### Heat input observer

`build.ps1 -CaptureHudHeat -Launch` enables the admitted heat CALL observer
at 0x43c532. The bridge preserves integer registers/flags, guards observer
floating-point state and LastError, and tail-jumps the original RET-8 function.
The pre-launch forwarding fixture checks ECX/EDX, both stack payloads, EAX
and LastError. The log contains two raw float bit patterns, HUD identity,
pre-update crop/arrow position and source dimensions; it does not capture
post-update results. At most 256 observations are retained, at least 60
completed scenes apart. This spacing is not elapsed time. `verify_heat.py`
checks source/provider/monitor identity, sequence, finite values, owner and
target profile. Raising/cooling heat is verified by an Instant Action user
check and recorded trends before any heat value is connected to Vulkan.

Heat run `20261010-065415-270` passed identity/provider and passive monitor
checks (`20261010-065422-224b3e5c`); the user confirmed normal gameplay, meter
and quit. `heat-observation-v1.json` contains 131 finite samples from one HUD
owner, first-argument range 0 to 0.666225, 27 rising and 88 falling steps.
Observed bar/meter sizes are 15x120 and 17x122. The peak first input occurs at
scene 2754; prior crop is [0,39,15,120] and prior arrow Y202. These geometries
precede the sampled update and must not be presented as that input's exact
result. `heat-observation-controls-v1.json` rejects mixed PID, nonfinite input,
invalid spacing and wrong phase. Next is pairing post-update crop and arrow
results before admitting a Vulkan heat geometry adapter. No physical heat
units, timestamps or Vulkan dynamic heat replacement are established.

The follow-up uses a typed fastcall wrapper: ECX/EDX and two unchanged stack
payloads are passed to the original function first, then guarded observation
reads the resulting crop and arrow Y. The fixture verifies original argument
forwarding, stack cleanup, EAX and LastError. This replaces the earlier naked
tail-jump; it follows the admitted calling convention rather than promising
identical caller-volatile registers or flags. New records explicitly declare
`after_original_update` with `result_crop`/`result_arrow_y`. The verifier keeps
historical pre-update compatibility, rejects mixed phases and missing phase
geometry. This pairs an input with that call's resulting geometry, while
retaining the 60-scene spacing and 256-record bound.

Post-update run `20261010-065854-250` passed identity/provider and passive
monitor checks (`20261010-065905-62a76905`); user gameplay/meter/quit were normal.
All 89 samples exactly match crop [0,120-ceil(120*first),15,120] and arrow
Y=280-ceil(122*clamp(first+second,0,1)). `recover_heat.py` admits this profile,
requires post-update records and retains the peak observed sample. Modified
crop, arrow and mismatched phase are rejected in `heat-geometry-controls-v1.json`.

`prepare.py --heat-state` now renders the original v3-package heat-bar bitmap
using the observed source crop, independent logical 15x120 size and output
density. Full-source UVs are clipped to the selected visible rows. Bar placement
uses the authored layout's (18,163); final destination was not captured here.
The arrow's geometry is verified but its asset mapping is not yet rendered.
The rasterizer supports bitmap components alongside vectors using fresh
output-density textures. `heat-bar-640x480-v1` and `heat-bar-3440x1440-v1`
receipts passed with maximum channel error one and zero Vulkan validation
messages. These previews use only one recorded heat sample, not synchronized
speed/counter state, physical heat units or live replacement.

User review corrected the heat artwork/alignment: the simplified vector had
incorrect section widths. The preview now uses the source 17x122 meter bitmap,
which has graduated right edges in green/orange/red, and moves the bar from
logical x18 to x16 to align its left edge with the meter interior. Its source
shape already widens to the right. This is a reviewed host layout correction;
the original runtime final bar destination has not been captured.
`heat-aligned-640x480-v2` and `heat-aligned-3440x1440-v2` receipts passed with
maximum channel error one and zero validation messages. Source v3 assets are
unchanged; a future vector trace should preserve this bitmap's stepped geometry.

The reviewed green triangle now sits left of the meter. Its half-size polygon
tip at logical x6.5 plus origin x9.5 touches meter x16 exactly. It uses left/top
anchoring, not viewport-center anchoring. In heat previews its center follows
the recorded arrow Y plus the source 12.5 center offset; reduced triangle size
remains a host presentation choice. `heat-triangle-*-v3` receipts verify tip
alignment and GPU/oracle maximum channel error one with zero validation messages.
