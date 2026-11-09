# Authenticated camera history (FidelityFX P2a)

Development work for [issue #107](https://github.com/roswellien/MW3Recomp-Private/issues/107),
following [world/output separation](fidelityfx-world-resolution.md). P2a captures
camera state and real-frame history. It does not implement jitter, sampled temporal
depth/motion buffers, object history, FSR dispatch or frame generation. Those remain
P2b/P3 and later work; a valid camera pair is not complete temporal scene input.

## Contract

`MW34_TEMPORAL_INPUTS=0|1` is development-only and defaults Off. Invalid values
fail explicitly. It adds no launcher setting or persisted preference. Immutable
camera/inverse words, projection/near/far values, viewport, target/view identity,
configured dimensions and load/reset epochs are captured at original draw
recording. Optional sun/effect lighting and replacement packs are not prerequisites.
Aspect/zoom adaptation copies the actual adapted model projection; an unproved TL
projection is omitted. No guest camera, simulation, clipping or surface ABI changes.

The renderer owns at most eight current/previous view entries. It observes the
original resident world submission once, before reduced shading/reconstruction
replay. Only authenticated world-mesh projections that agree with the captured
projection contribute camera history. Cockpit/effect submissions can share a camera
address while using a different projection; they cannot silently join that view.
Ordinary movement retains prior camera pose. Conflicting same-view snapshots
invalidate the frame. Motion for moving or unknown geometry is not manufactured.

History commits once after successful processing of a real guest Flip, before the
existing frame-budget stop. EndScene, coverage replay and non-Flip presentation
cannot advance mission history. Snapshots contain owned values; no presentation
thread reads guest memory or runs callbacks. Missing/invalid frames, view/target,
projection/dimension/load changes and explicit reset events discard prior history.
Duplicate completion is rejected without overwriting the completed pair.

External guest imports, partial/interleaved fills and writable surface locks
invalidate temporal state. A full surface clear before the first world submission
is recognized as normal frame initialization. Read-only locks/readback do not
become writes. Known GPU HUD composition keeps its existing ordered output path.
These classifications do not change authoritative guest color or D16/D32 storage.

## Original controller and reset producers

Inspected original: MW3 U.S. retail 1.2 `Mech3.exe`, SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Addresses are preferred-image virtual addresses (base `0x400000`). LLVM 21.1.8
static inspection and standard-library PE table reads supplied the observations;
private disassembly/range hashes remain under `local/p2a/`. The
[function index](../games/mw3/symbols/functions.tsv) retains `sub_XXXXXXXX` names
and bounded confidence. No original instruction bodies are committed.

| Boundary | Original evidence and use |
| --- | --- |
| Activation | `sub_00520B00` adjusts camera basis and prepares the inverse. Existing `CameraBinding` authenticates exact source/copy/inverse words. Capture is enabled independently of sun. |
| Context/controller | `sub_0040ADF0` replaces target/controller with teardown/init; `sub_0040AE70` selects/reinitializes it, including same-value reselection. Both invalidate on invocation. |
| Target identity | Mech tables `0x5BCEF8` and `0x5C3508` have receiver getter `sub_004D2A70`; `context+0x64` directly identifies the selected actor. Unsupported target tables are rejected. |
| Continuous modes | Exact mode-zero table `0x5BD2F8` uses `sub_00421760`; mode-one table `0x5BE9F0` uses `sub_00421E40`. Controller/context backlink and selected mode must agree. Only the frozen camera recipient may use absolute translation/rotation setters in these update scopes. |
| Terrain adjustment | `sub_0040AF30` reaches relative camera translation; this is a separate permitted scope, not a camera-cut flag. Context `+0x68` is not admitted as one. |
| Presets/configuration | `sub_00421C00`, `sub_00421900` and forwarding `sub_00421D40` can initialize pose. `sub_00421D50` changes mode-one attachment. They conservatively reset rather than rely on final-value comparison. |
| Relocation | Teleport UI `sub_004A37A0` and mission action `sub_004E3BA0` reach actor virtual `+0xDC`, `sub_00418F30` -> `sub_00418E90`. Orientation/position and physics/velocity are reset. These are distinct from ordinary camera updates and invalidate same-controller history. |
| Lifetime | `sub_004F32E0` constructs the camera; `sub_004F3390` routes retirement through `sub_004EB050` and eventual `sub_004EAF90`. Camera and associated world-root retirement cannot inherit old history at reused addresses. |
| Association/setters | `sub_004F3560` assigns world association, `sub_004F3620` viewport. `sub_004F36B0` writes rotation; `sub_004F3870` absolute and `sub_004F3920` relative translation. Writes outside the proven recipient/update scopes change that camera's epoch. |
| Pause | `sub_00482AD0` constructs "Pause State", table `0x5C40F0`. Its entry `sub_00493040` creates the native pause dialog; teardown `sub_004931E0` releases it. Both reset and the interval is excluded. Zero timer delta is not used as a pause flag. |
| Load/frontend | Successfully recognized mission-reader opens advance a separate reader epoch, including same Training reload; existing lighting generation semantics remain intact. Frontend, nonlive/detached Photo/Replay, focus and size transitions invalidate. |

Camera hierarchy admission is deliberately narrow. A camera may be parentless, or
have exactly one reciprocal edge to its own type-two, parentless world association.
`sub_004ED280` applies no transform for that world-root type. Ambiguous/cyclic or
animated ancestry and alternate pose storage are rejected. The mode-one head
attachment (`actor+0x39C` component/head) is not admitted: `sub_00460280` can write
cached head matrices directly, bypassing generic setters. Head/ancestor producer
coverage remains future recovery. The "Restore node" routines in
`zeff_anim_save.c` are animation restoration, not proven generic game-load signals.

New adapter targets are included in fast body-dispatch classification, including
the original camera-retirement tail route. The original compiled bodies still run;
there is no interpreter/original-code fallback, guest state seeding or fake service.

## Bounded validation

The implementation's pre-review development host SHA-256 is
`e2a154cfd8d0fd3ed2c13da9187cf14cdd561df058f0a1efbfc4c953bb6c7206`.
Its build receipt records all 169 host source hashes and 186 repository dependencies;
the runs in the table below matched those source hashes. The translated DLL is unchanged.
Native runs used RX 9070, unchanged installed driver, explicit Vulkan/DXGI bridge,
3440x1440/FXAA/16x AF and synchronization validation. Every run below reached its
deliberate presentation-budget stop (exit 1), with zero VUID/validation errors.
These are bounded native runs, not normal-quit or whole-game acceptance.

| Native configuration | Actual presentations / guest scenes | Camera result |
| --- | --- | --- |
| Published packs, 100%, temporal Off | 2,200 / 6,142 | No camera-history records |
| Published packs, 100%, temporal On | 2,200 / 6,142 | 1,471 valid pairs, including final frame |
| Published packs, 50%, temporal On | 2,200 / 6,142 | 1,471 valid pairs, including final frame |
| Stock, sun/effects Off, pause/resume, 100% | 2,200 / 5,819 | 1,388 valid pairs; pause interval excluded, then recovery |
| Stock, camera cycling, 100% | 2,200 / 6,442 | 869 valid pairs across admitted modes zero/one; unsupported mode two excluded |
| Stock, sun/effects Off, movement/zoom input, 50% | 2,200 / 6142 | 1,471 valid pairs, including final frame |
| Published menu/Lab, temporal On | 1,300 / 2,211 | No mission camera pairs inherited by frontend/Lab |

At frames 1801 and 2101, published 100% temporal Off/On captures are byte-identical
to each other and the P1 references. SHA-256 values are
`0c822b3dd82b25444b1c0dc66dd14bdc26ffb1f49c89a64087404b4ff24389cd` and
`0f7f6f526a793c5cbdd63748fd69949471a298582e83544fe87111dd4d52638e`.
The 50% captures match their P1 references:
`6f13822cc471e0dc0e3e49e382819aabca76b32cb34c8caeed38629ed09b72ed` and
`6af77b31b2c6cf6e39686e2a925918825cf9ce017a26fb88b0d73a22a5b4ceb4`.

Pause entry at frame 1501 invalidates; frames 1501-1581 retain no pair. Exit at
1582 invalidates; the following fresh view starts without history and then recovers.
Camera cycling at 1301 resets mode zero before mode one starts; a later mode-two
controller is rejected even though it reuses the mode-zero table. These are
original scripted input and controller/pause bodies, not seeded observer events.
Same-Training reload epoch behavior is checked in the lifecycle fixture; a native
same-mission reload is not claimed. Main/zoom separation is checked with authored
view snapshots; native zoom producer coverage remains bounded by hierarchy admission.

Checks: CMake build, 25/25 CTest, format-check, launcher .NET and eight dispatch
Python tests, seven function-index tests and two host-builder tests pass. Existing
Windows fixtures cover immutable history, Off/invalid control values, activation
with lighting Off, FP/LastError preservation, reader epochs and fast dispatch.
The campaign fixture now uses an authored spotlight and current distance-retention
semantics instead of relying on catalog order and obsolete frame-only expiry.

RX 9070 GPU checks pass 60 display/color/order cases (50/67/100%, AA Off/FXAA,
RGB565/RGBA and temporal Off/On), six D32 transfer/residency/precision modes, two
25-presentation bridge cases, full sun lighting and camera-history integration.
The latter verifies repeated original submissions, normal initialization clears,
interleaved guest writes and captured/actual projection agreement. All have zero
VUID/validation errors. Temporary negative controls fail for per-submission
advancement, omitted load epoch, erased sticky guest-write invalidation, bypassed
inverse admission, omitted camera dispatch target, missing reader epoch,
lighting-only activation and bypassed projection agreement. Source mutations were
restored and positive checks rerun.

Independent branch review completed in two correctness/structure passes. It found
that the new reader epoch inherited legacy substring matching, so unrelated names
such as `readeria.txt` advanced temporal load identity. Epoch admission now uses
the known Training/Instant Action/Multiplayer archive names while preserving
existing lighting classification. The extended lifecycle fixture failed before
the fix and passes afterwards, including all recognized mode-reader variants.
The removed-reader-epoch and lighting-only activation negative controls still fail.
No major or minor review findings remain.

The post-review development host SHA-256 is
`0290443b55b59902265f3a8846f391bf3f9c38ce97ba22f57574a2fd26563d15`;
all 169 current host sources match its build receipt. Its matched published 100%
temporal-On Training run (`local/p2a/review-published100-on-reference/`) completes
2,200 actual RX 9070 Vulkan/DXGI presentations / 6,142 guest scenes, with 1,471 valid
pairs including the final frame, zero validation errors and deliberate budget exit 1.
Captures 1801/2101 match the stored temporal-Off/On and P1 references above byte for
byte. The full native configuration table remains evidence for the pre-review
host, rather than an unperformed repeat of every configuration after this fix.
Fresh review checks also pass the CMake build, 25/25 CTest, format-check, games-closed
launcher .NET checks, eight launcher-dispatch tests, seven function-index tests,
two host-builder tests, history/capture/dispatch/lifecycle fixtures and all 70 RX 9070
renderer cases described above. The two inherited web-style failures below remain.

Receipts and captures remain local under `local/p2a/`. The live update catalog
selects runtime 1.0.44; a fresh read of the published R2 pack catalog confirms all
13 isolated archive byte counts, SHA-256 values, versions and extracted manifest
hashes. Newer local-only packs are excluded. An earlier admission preflight used
older prototype guards and is retained privately, without final-source credit.

## Limits and release impact

P2a does not close #107. Unknown camera controllers, head/animated hierarchies,
unsupported projections and incomplete input coverage stay invalid. GPU motion,
jitter, depth validity and complete world-only temporal composition require P2b;
object/part motion and effects require P3. No performance or whole-game fidelity
claim follows from a camera pair or fixture.

The earlier review recorded two inherited web-style failures in the crash-report
files. Their fixes from [PR #110](https://github.com/roswellien/MW3Recomp-Private/pull/110)
are now included through `develop`; current CI still determines style acceptance.

No SDK binary, pack format, installer/update/version or public graphics setting
changes. P1/#100 remains an unmerged dependency; its presentation bridge dependency
from #105 is already in `develop`. Raw RX 9070 Vulkan WSI remains outside this fix. No merge or release is implied.


## Refreshed integration review, 2026-11-02

This branch now includes the reviewed #100 source and its captured-vertex
fixture-shadow repair, together with current `develop`. Conflict resolution
preserves headlight dispatch, surface-material records, and Training time-of-day
selection. Exact Training readers 1 through 4 advance camera load identity;
the existing mission-reader regression table covers each name.

A fresh Windows asset-free build exposed a C4996 warning treated as an error in
the new surface-access history target: `camera_history.hpp` uses `std::getenv`.
The target now applies the existing repository CRT-warning definition; production
camera behavior and warning policy for other targets are unchanged.

The refreshed RX 9070 checks passed 60 presentation/persistence/ordered-write
cases with temporal inputs Off/On, six depth modes, and both 25-presentation
DXGI bridge cases. Camera history/reset checks, lighting-independent camera
capture with FP/LastError preservation, world-camera integration, dispatch
membership, mission-reader epochs, sunlight and the inherited fixture-shadow
regression passed. No synchronization-validation diagnostics were observed.
These are authored fixtures, not a new native campaign, same-mission reload,
physical-PC or original-game fidelity acceptance run.
