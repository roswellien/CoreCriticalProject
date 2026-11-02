# Static temporal inputs (FidelityFX P2b)

Development work for [issue #107](https://github.com/roswellien/MW3Recomp-Private/issues/107),
following [authenticated camera history](fidelityfx-camera-history.md).
The execution boundary is immutable original static-source/camera observations to
private GPU depth, motion and validity images. FidelityFX dispatch, object motion,
reactive masks and frame generation remain outside this change.

## Opt-in diagnostic contract

`MW34_TEMPORAL_INPUTS=1` enables the diagnostic pass. `MW34_TEMPORAL_JITTER=0|1`
defaults to zero and requires temporal inputs when enabled. Malformed settings fail
explicitly. These are development environment settings, with no launcher preference.

The original renderer remains authoritative for guest color, depth transfers,
Lock/Blt/readback, presentation and HUD. The diagnostic pass runs once per original
public renderer submission, outside reduced-resolution shading/coverage replay.
It allocates separate R32_SFLOAT depth, R32G32_SFLOAT motion, R8_UNORM validity and
D32_SFLOAT visibility images at the configured internal world dimensions.
The three exported images finish in shader-read-only layouts. Completion occurs
only at the real guest Flip; capture never reads guest memory.

Motion is previous minus current unjittered render-pixel position, with X right and
Y down. Perspective interpolation reconstructs the same static surface point in
both cameras. Previous near/far and screen bounds constrain validity. Exported depth
is reversed infinite `near_clip/camera_z`; finite guest far clipping still applies.
Visibility uses the existing `near_scale/camera_z` depth convention. These two near
values are distinct. The existing guest half-pixel center is applied exactly once.

Render-only jitter is Halton bases 2 and 3, centered about zero, with sequence length
`ceil(8*(output_width/internal_width)^2)`. A view advances once per completed real
frame, independent of scene count. Rejected/missing/reset history restarts the phase.
Raw geometry and supported transformed/lit occluders receive the same pixel offset.
No original camera or culling state is modified.

The diagnostic pass preserves original draw/clear order, culling, depth state and
texture alpha rejection. Unproved geometry masks its actual rasterized footprint
with invalid motion. Unsupported alpha-bearing model geometry rejects the view.
Known output-only HUD work retains its existing output path. Unknown coverage does
not acquire static zero motion by default. A rejected frame cannot supply the next
frame's diagnostic history.

## Original static-source producers

Inspected MW3 U.S. retail 1.2 `Mech3.exe` SHA-256:
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Addresses below use preferred base 0x400000. LLVM 21.1.8 static inspection and
bounded native observations supplied this evidence; original instruction bodies
and private disassembly stay local under `local/p2b/`.

Context+0 is a vtable, rather than the scenery ownership root. A recorded parent
with no reciprocal child membership is insufficient for static admission.

| Producer | Recovered contract |
| --- | --- |
| `sub_004F6720` | Original cell-render scope owns the selected cell data, frame locals and visible-table row. Bank/index, sector-array entry and 72-byte cell identity must agree. |
| `sub_004F5910` | Original node dispatch is observed only inside that cell scope, at exact original return sites. |
| Return 004F69DC / 004F6B59 | Separate unfiltered/filtered calls use the cell's bounded object list at +3C, count from +38 high word, and original ESI index. Selected root membership must be unique. |
| Return 004F6AE0 | Placement list at cell+44 has bounded count at +40 and 0x44-byte records. Original EBX identifies the record, its first word the subtree, and its next 12 words the independently produced transform. |
| 004F6AB8..004F6AC9 | Placement producer copies the record matrix to type-five data+30 and data+60. Both copies must agree at the observed producer boundary. |
| `sub_004F4AB0` | Type-five renderer applies the selected local transform; reciprocal descendant membership and supported type-five storage are required. |
| `sub_004F4370` | Camera-offset setup freezes the cell/tile offset values into this original scope. Different offsets have different static identities. |
| `sub_004F4170` / `sub_004F41B0` | Camera setup entry/delegate: the first supplies zero offset; the delegate forwards the optional offset to 004F4370 and refreshes camera projection/clipping state. |
| `sub_0051E930` | Matrix-stack copy updates data+60 with camera-dependent render storage. It is checked at the placement producer, then excluded from stable cross-frame identity. |

Static placement is built from independently authenticated cell/local matrices.
It is compared with the captured local-to-camera transform and every original
world vertex using existing world-projection tolerances. Reconstructing a world
matrix solely from camera and local-to-camera values cannot establish ownership.
Nonfinite transforms, unsupported animation/storage, ambiguous membership and
source changes lose admission.

Exact mesh and ownership bytes are shared immutable snapshots. Node/mesh/polygon,
cell/record/route/tile identity, pose, texture version and load/lifetime epochs
must agree across consecutive real frames. Original retirement 004EB050/004EAF90
and tracked guest heap releases invalidate retained sources, including freed blocks
that contain tracked cell/pose addresses. Reader-epoch changes clear current lookup
owners; deferred owners retain their budget charge until released.

At most 2,048 source entries and 64 MiB are retained, including pending/completed
owners and static-source metadata. Overflow fails explicitly. GPU attachments use
at most eight view slots and 512 MiB; missing views release their slots at completion.
Temporal Off allocates no diagnostic attachments.

## Validation scope

The authored RX 9070 fixture checks sampled depth, signed pixel motion, repeated
submissions within a real frame, jitter phases, opaque/texture-alpha occlusion,
reset publication and missing-view cleanup. An independent ray/plane oracle checks
camera rotation plus XYZ translation at 50%, 67% and 100% internal resolution.
A deliberate reversed-motion shader fails the motion assertion; canonical sources
are restored afterward. These GPU fixtures are separate from live native gameplay.

Native acceptance remains incomplete. On November 2, a development host using the
published 1.0.46 translated module and all 13 verified published asset packs reached
live Training and completed 3,300 RX 9070 Vulkan/DXGI presentations with the existing
driver. The registry-selected control profile uses P/W/D; earlier scripts using S
and arrow keys did not establish moving-camera coverage. Corrected input demonstrated
movement and tutorial advancement. No Vulkan validation errors were found, but
moving gameplay repeatedly rejected history with guest-write/view-state resets.
The available stationary captures had zero valid static pixels. Neither result
satisfies native motion acceptance; P3/P4 and frame generation remain gated.

The private preparation required restoring normal_codec.py from the exact signed
release's source commit because that file was absent from the published preparation
payload. This does not establish successful preparation from a pristine release.
No installed runtime, asset pack or driver was changed.

After temporary per-draw tracing was removed, the cell/source CPU fixture, world
binding fixture, seven function-table tests, two host-builder tests and nine RX 9070
temporal GPU cases passed. The GPU cases cover world motion/validity at 50/67/100%
with jitter Off/On, plus three depth precision runs. These authored fixtures do not
replace the missing native acceptance. The newer P2a surface-access dependency
(c998419) is integrated locally. Its comparison completed 2,200 presentations with
zero Vulkan validation errors; the same write resets begin at frame 1401 after
power-up at frame 1400. Authoritative color captures at 801/999/1801/2101 match the
pre-dependency run byte-for-byte. At that checkpoint the actual writing producer was unknown;
view-state in the last-draw log alone does not identify a main-camera failure.
The write guard remains enabled. All 27 CTest cases passed across the initial run
and a targeted source-pin recheck. Native acceptance, final regression checks and
independent review remain pending.
No normal playtest release is produced by this development branch.

## Powered-up depth-clear correction

The subsequent bounded trace identified a DirectDraw z-buffer fill after power-up:
rectangle (962,658)-(1005,758), clear value zero, original return site 005777AB.
A full z-buffer clear at return 0057788F precedes it. No CPU surface-write or HUD
fallback trace fired at the first reset. These are observations from the same
verified executable; no new original-function hook is introduced.

GPU depth fills now carry their real frame and target into the diagnostic pass.
A depth-only, clear-only submission is accepted only with bounded rectangles and
a matching current pending view/diagnostic slot. It clears private visibility in
order while retaining color-associated depth/motion/validity. Untagged, stale or
wrong-target writes, color fills and CPU writes retain conservative rejection.

Six RX 9070 temporal GPU cases pass at 50/67/100%, jitter Off/On. The regression
preserves underlying metadata and proves that geometry previously hidden behind
the old depth can cover the cleared rectangle. Omitting the diagnostic depth clear
in a private negative control fails that assertion. The earlier whole-view guest
write regression still passes. All 27 CTest cases and enforced web style pass;
other style categories remain report-only under the repository policy.

The corrected native run completed 3,300 RX 9070 presentations with zero Vulkan
validation errors. Frames 801/999/1801/2101/3001 match the pre-fix authoritative
color captures byte-for-byte. Power-up no longer causes a continuous reset:
1,574 of the 1,900 post-power frames report reset=none. The remaining 326 frames
still reject history; the first is 2042. Captured temporal images at
801/999/1801/2101 still contain zero valid static pixels, and 3001 has no accepted
temporal image. Thus the power-up defect is narrowed, while native visibility
coverage and remaining history rejection still block P2 acceptance. No FSR or
frame-generation dispatch is enabled, and no release is produced.

## Visible source and color isolation

A private offscreen prefix replay isolated the earlier all-invalid result: the
72 inspected `healthy` draws produce 184 valid pixels alone, all occluded by earlier
native geometry. That replay is diagnostic evidence, not live native acceptance.
The visible occluder was `g29`, an ordinary 39-polygon, 54-vertex mesh in an existing
cell placement, excluded by the candidate-name filter. No new original hook is
needed. It is now an opt-in diagnostic candidate, still subject to the existing
cell/placement/descendant ownership, source-byte/lifetime, texture-version and
projection checks. The name itself never establishes static validity.

Its geometry travels in a separate immutable diagnostic model. The original TL
vertices, color commands and guest depth remain authoritative. Only candidates
whose captured vertex bytes remain identical qualify; reconstructed/clipped changes
are rejected. Diagnostic geometry shares the existing immutable upload queue and
has an independently adapted widescreen projection. The ordinary color path does
not consume it. A native experiment that used the ordinary raw-world color bridge
changed the reference image and was rejected.

The corrected native run completed 2,200 RX 9070 Vulkan/DXGI presentations with the
published 1.0.46 translated module, all 13 verified published packs, 100% scale,
jitter On and lighting Off. Four color captures at 801/999/1801/2101 match the prior
reference byte-for-byte. Valid static coverage is sparse: 57,015 pixels at 801,
56,999 at 999, 57,015 at 1801, 56,725 at 2031, 53,684 at 2071 and 49,031 at 2101.
All valid pixels at 2071 and 2101 have finite motion exceeding 0.01 render pixels
during W-key movement; median vectors are (1.36084,-0.86129) and
(3.47107,-0.26893). Vulkan validation reports zero errors. This demonstrates live
native moving inputs for the inspected surface, not full-scene coverage or FSR.

The first movement rejection at 2042 is a tracked 32-byte source-storage release.
The lifetime guard remains intact. History now retains the first rejection so a
later depth clear cannot replace a transition with a misleading guest-write label.
The regression fails the old behavior and verifies both rejection and recovery.
Eight transitions remain among frames 1401..2200; other post-power frames retain
history. This interval differs from the earlier 3,300-frame test.

An authored GPU case places diagnostic geometry separately from original TL color
and requires unchanged color/guest depth plus valid diagnostic coverage. All six
50/67/100% jitter Off/On cases pass; a private color-alias control fails the new
assertion. The 70-case renderer regression matrix and launcher .NET checks pass.
The initial .NET run lacked SDL3; the existing SHA-256-pinned 3.4.18 archive supplied
the ignored test dependency before the successful rerun. Remaining native modes,
current-develop integration, final source matching and independent review are still
required before P2 acceptance. FSR dispatch and frame generation remain Off.
