# First original CPU projection bypass test

Development experiment, 2026-10-15. The execution boundary advances from
GPU scenery draws that still run original CPU projection to conditionally
omitting original perspective iterations. This is not enabled in either
playable launcher. Strict acceptance remains 131/144.

## Implementation

`tools/remaster-launcher/apply_projection_bypass.py` pins the complete original
host IR and changes one positive-count edge inside translated `sub_53F2E0`.
Only one of 37,201 object-list entries is replaced. Retained original IR,
objects and the public launcher profiles remain unchanged.

The actual loop is the textured **lit** loop at VA `0x540985`, entered through
`0x540977`. A byte-identical unlit loop exists at `0x5412A5`; its callback
contract differs. Initial exploratory label mapping confused these loops.
Those runs admitted zero polygons and omitted zero iterations. Corrected
disassembly, live PC evidence and fixture results are retained locally.

Admission requires selected resident static scenery, matching source polygon
and reversed UVs, no clipping, layers, special/decomposed polygon path or depth
bias, opaque immediate material submission and the expected lit callback.
A pending raw-geometry token must reach the exact expected GPU draw; mismatch
or an abandoned token stops execution. Original color/fog/material callbacks,
mesh processing and game simulation continue.

For an admitted polygon with `n` corners, omit the first `n-1` perspective
iterations and run the original last iteration. This retains final integer
registers/flags, physical x87 slots and floating-point metadata. Admission also
bounds operands and requires the precision exception already sticky, so the
omitted prefix cannot add a different exception. The host gate preserves the
host FP image. These are bounded conditions, not permission to skip an entire
mesh producer.

## Completed checks

The authored `test_projection_loop.py` / `.cpp` fixture passes 840 cases for
the actual lit loop, both before and after the production x87 merge pass.
It compares complete State, memory except the deliberately omitted prefix
XYZ fields, and hardware FP status. Negative admission cases pass. The separate
`test_projection_contract.cpp` fixture passes operand bounds, dirty byte
tracking, overlap and partial-write cases. These establish local contracts;
they do not establish observation of every live memory access.

The corrected reference mode reserves the same GPU tokens while executing
every original iteration. Bypass mode uses the same executable, input,
private save baseline, assets, 3440x1440 output, FXAA, AF16 and 1600-unit scenery.
Semantic hashes include geometry, transforms, projection, material/render
state, color/fog/UV and draw order. The ordinary full TL hash is deliberately
unsuitable for comparing omitted CPU coordinates.

| Run | Result |
| --- | --- |
| 550-frame reference/bypass pair | Every frame's semantic draw record matches; 34,188 admitted draws and 89,155 omitted iterations |
| 1,400-frame walk/turn reference | Reaches the requested budget |
| Walk/turn bypass | Matches all 1,254 completed frame records; stops during the next frame after 230,935 omitted iterations across 93,039 consumed draws |
| Image comparisons before the stop | Targets 600, 900 and 1100, plus logical framebuffer readback 1000, are byte-identical |
| Diagnostic repeat | Reproduces the same guard alert at the same draw |

No frame-1300 bypass capture exists. This is **not a passing 1,400-frame test**.
Budget termination and a fault both use exit code 1 in this host, so the final
frame and stderr must be checked, not only the process exit code.

## Observation gap found by the longer test

The alert is a five-corner draw from TL buffer `0x72F41C`, returning to
`0x57DA68`, with no pending bypass token. The first tracked dirty byte is the
fifth corner's X field at `0x72F49C`. It fires while host frame count is 1254,
before the next present.

Investigation found that the retained optimized callback object accesses guest
memory directly, without the scalar bridge calls this experiment observes.
The current rebuilt producer uses scalar bridges; other retained objects can
therefore read or overwrite the same scratch without updating its dirty map.
The callback object at `merge-r7/lifts-r31/m_57d690-O2.obj` has no undefined
scalar memory bridge symbols. The project has an existing flat-memory lowering
in `ir_cleanup.flat_mem`; absence of inlined bridge fast paths in a build report
does **not** establish that memory goes through out-of-line bridges.

Consequently, the alert does not prove a real stale-coordinate consumer. It
can reflect an unobserved overwrite. Conversely, earlier runs cannot prove
there were no unobserved reads. Zero observed depth-copy reads in the bypass
log was another warning sign: those callback accesses were outside observation.
The images and semantic matches remain valid, but the live scratch-safety
claim is withdrawn. The guard stays strict; no read exemption was added.

## Next required test boundary

1. Observe actual flat guest loads/stores as well as host service transfers.
   Inventory linked object recipes and cover the original callback and clipping
   consumers; do not assume a changed bridge source affects lowered objects.
2. Verify that deliberately introduced omitted-coordinate reads are caught and
   ordinary flat overwrites clear the correct bytes. Require actual observed
   callback depth-copy reads when this bypass executes.
3. Repeat the complete movement/capture pair, disabled original controls and
   near-clipping/zoom/lifetime cases with that observation in place.
4. Measure matched alternating timing runs separately from captures and safety
   instrumentation before reporting an FPS gain. The current bridged producer
   also differs from the retained optimized producer's memory recipe, so this
   development host is not a fair performance comparison with Play.

No new performance percentage is established. Full transform/culling work,
unsupported rendering paths and simulation remain CPU-owned. Dynamic lighting,
normal mapping and shadows are still subsequent renderer work.

## Evidence identities

The follow-up [observed projection test](gpu-projection-watch-test-2026-10-15.md)
adds explicit State/token-aware flat-memory observers and passing optimized
loop/host fixtures. Its complete private watched build finishes a 1,800-frame
pair without a dirty-read guard failure, but image equivalence fails and original
draw counts diverge. It is not promoted or timed. These results are tracked
separately and do not retroactively close the observation gap in the runs above.

Original MW3 U.S. retail 1.2 image base `0x400000`, SHA256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Addresses above are original VAs except the named local object paths.

First test executable SHA256
`4aa852b9d6c23c732d88176606237a585f7099ae663dd7666ec505bc5fa36528`,
`local/remaster/gpu-native-projection-r2/build/entry_commandline.exe`.
Private disassembly, original-loop fixtures, source checks, run metadata,
protected-save hashes, semantic records, captures and diagnostic repeat are
retained under `local/gpu-projection-bypass-r1/`. Original media and generated
game code remain local. No commit or acceptance promotion was performed.
