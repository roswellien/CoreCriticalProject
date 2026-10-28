# Bounded terrain perspective removal — 2026-10-17

The first bounded CPU-removal prototype passes the tested rendering and scratch
ownership comparisons, but **does not deliver a net performance win**. It is
private and not promoted. Big Lake Play retains the validated cache-fixed host
SHA256 `709fcac6625d6646356b32566259fdc69679b36ad348f894eb780e27619fcb08`.
Acceptance remains **131/144**. This is not completion of terrain migration.

## Recovered boundary and implementation

Inspected the current native host, prior projection experiments and the original
MW3 executable with REA/Ghidra. Original executable SHA256:
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Addresses below are original VAs. Static function evidence is distinct from the
executed comparisons below.

- `0x545720` performs general material lighting; it is not a dedicated terrain
  vertex transformer. `0x51FB30` composes camera matrices. Their earlier labels in
  the terrain plan were incorrect.
- The relevant vertex-transform and polygon perspective loops are inside
  `0x53F2E0`. The existing, pinned experiment patches the lit perspective loop
  at `0x540985`, admitted from state PC `0x540977`.
- `0x4F6720` retains tile/cell selection and dispatch. It also handles scene
  light flags and LOD-related decisions, so replacing the whole function with
  a terrain draw would omit required effects.
- `MW34_GPU_TERRAIN=1` already extends resident-world admission to `bwg` meshes.
  GPU retention does not remove the original CPU producers. The original plan's
  generic heightfield/skirt layout is not a recovered data contract.

The new `apply_terrain_projection.py` installs the existing observed projection
adapter into a fresh current Big Lake host copy, restricts it to admitted
`ter`/`bwg` meshes, and connects its model instance to current sun/shadow normal
and world transforms. Admission still checks the original polygon/material/
callback/device, UVs, clipping flags, source operands and FP conditions. Unsupported
polygons continue through their original recompiled path.

Mode 1 performs original projection and attaches the admitted resident geometry.
Mode 2 omits the first n−1 perspective iterations and executes the last original
iteration to retain machine state. CPU vertex transformation, original material
lighting, fog, clipping, tile/LOD selection and callbacks still execute. This is
real but deliberately narrow CPU-work removal; it is not full GPU terrain.

The adapter passes the gate's State explicitly and preserves FP/XMM and Win32
error state on normal and exceptional wrapper exits. Omitted scratch remains
observed in the safety build. Unexpected reads fail visibly; no AFTER-state
seeding, interpreter or original-binary execution fallback was introduced.

`terrain_work_profile.hpp` provides optional integer-QPC scopes for the mesh
body, lighting and fog, plus per-node-name mesh totals. Scopes are inclusive;
lighting/fog are already inside mesh-body time. Group and per-node rows are
alternative views and must not be added together. These measurements address
the missing terrain-only attribution in the older generic-function profile.

## Correctness evidence

Private root: `C:/Users/jcbla/MW34SunTests/terrain-cpu-removal-r1/`.
No assets or generated game code were added to Git. Reused the existing complete
37,201-object watched list rather than rebuilding it. Its original ordered-list
identity matches the playable list's `a0a4d56f…` receipt; the patched producer
object pin was checked. These are development tests, not strict acceptance.

- Original optimized-loop fixture rerun: **1,152** complete-State/FP/allowed-memory
  cases and adverse admission cases pass; **119,808** watched writes exercised.
- Observed reference/bypass runs `run-a`/`run-b` reach **1,200 frames** each.
  **51,868** polygons admitted/consumed and **128,116** perspective iterations
  omitted. Exactly **128,116** permitted callback depth-copy reads were observed;
  no unknown scratch read or pending-token guard failed.
- All 1,200 per-frame rendering-semantic records, admissions and rejection
  counters match except the deliberate omission/depth-read counters. Those
  semantic records exclude omitted CPU position/depth bytes for resident draws;
  full raw-TL hash equality is not claimed for a bypass.
- Full 3440×1440 captures at frames **600, 900 and 1100** are byte-identical.
  Sun, shadows, normals, fog, HUD and geometry are retained on this route.
- The observed reference matches all **1,000** original frame/draw/hash records
  from the prior playable smoke; scene pixels match outside that smoke's FPS
  overlay, which was disabled in the new experiment.
- The final installer reproduces the private source exactly from a fresh current
  host copy. The final observed bypass rerun in `final-a` again matches all
  1,200 semantic records and all three capture files, with the same 51,868
  admissions, 128,116 omissions and 128,116 permitted depth reads. Final private
  observed executable SHA256:
  `f471e4d4a51e1855826613341f0ce3e942ef9906c929438a8082deda8e59d325`.

All bounded runs end at their intentional presentation-budget fault, exit 1;
this is not normal-quit, mission completion or full gameplay validation. Retain
the prior unexplained projection/control divergences from October 15; these
passing runs do not diagnose or erase them. Live zoom, near-plane, damage/LOD,
reload and additional maps remain outside this comparison.

REA identities, local pseudocode and snapshot are retained privately. Evidence
IDs: `ev_55c70e76f9c65453e2544c83e66f59a37962e8622d53608fedb84d59880277f6`
and `ev_5867658ebe07f2ce455edd7dd1b3b512f818c6e7fcdbcca62cfa877e1172dcb2`.

## Performance result and retained failure

Timing uses the same private 1,200-frame route, original 50 ms virtual clock,
3440×1440 FXAA/AF16, draw 1200/fog 1100, sunset, all model bindings and shadows.
Measure presentation intervals 400–1200, with no screenshot readbacks. Timing
disables command hashing and the full original-memory observer explicitly and
equally; it provides **no safety credit**. The safe observed build is retained
separately. The experimental recipe's host access hooks remain in these controls.

| Same-host case | Run means, ms/frame | Pair mean |
| --- | --- | ---: |
| Experimental geometry object, bypass off | 19.109 / 18.971 (`perf-a`, `perf-d`) | 19.040 |
| Experimental geometry object, bypass on | 19.166 / 19.209 (`perf-b`, `perf-c`) | 19.187 |
| Existing production geometry object restored | 12.221 / 12.295 (`base-a`, `base-b`) | 12.258 |

The bypass executes the same 128,116 omissions in each completed timing run; a
zero-admission result was not mistaken for a speedup. The small +0.147 ms bypass
difference does not establish an improvement. More importantly, replacing just
the experimental `m_53f2e0-O2.obj` with the existing production object, leaving
the C++ host identical, recovers about **6.78 ms/frame**. All 1,200 original
frame/draw/hash records match for that one-object disabled control. This isolates
the experimental rebuilt producer/hook integration as a major cost, not a scene
load difference. It does not separately attribute each compiler pass or callback
barrier. The old experimental object is 346,670 bytes versus production 128,130;
object size alone is not the timing evidence.

An earlier timing attempt, `time-b`, stopped at frame 324's first omitted draw:
its partial observer could not see subsequent original-code scratch overwrites,
leaving stale dirty marks and rejecting the draw. It is retained and excluded
from performance conclusions. `time-c`/`time-d` were not started. Later timing
cases explicitly disable observation with a stderr label; they do not weaken
the default observed mode or establish safety for unobserved production use.

## Measured scope and next execution boundary

With the production object restored, the current admitted-name `ter` and `bwg`
mesh bodies total about **0.23 ms/frame** on this route (inclusive, profiling
starts after presented frame 400). This is a bound on this selected mesh-body
subset, not all terrain cost: deferred material work, host TL capture/submission
and other geometry paths are outside that attribution. Skipping only a portion
of its perspective work cannot justify the added experimental overhead.

Do not promote this prototype or expand the same hook blindly. The next useful
step is source-bound ownership of the remaining terrain TL producers and material
queues, followed by admission before the expensive transform/lighting/submission
work while retaining original tile/LOD/culling decisions and every required
initializer/callback effect. Preserve the production optimization recipe and
measure an unchanged disabled control before timing further bypasses. A smaller
snapshot-based or outer-boundary admission may avoid a whole-State callback
barrier, but that is a proposal, not a proven fix for this measured regression.

The final development host is restored to the complete observed object list.
`MW34_TERRAIN_PROJECTION=0/1/2` selects disabled/reference/bypass. Audit and scratch
observation default on; their explicit timing-only switches are not user graphics
features. The playable profile and executable remain unchanged. Nothing committed;
no native milestone or accepted-function credit claimed.

Final verification is recorded in the private `result.json`. No game, compiler
or build process remained; protected Python PIDs 6536/5196 were untouched. The
owned REA analysis session was saved locally and closed.
