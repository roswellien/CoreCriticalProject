# Investigation of the recurring frame-487 difference

2026-10-15. Investigated the difference retained in the
[fast-binding tests](gpu-world-fast-binding-2026-10-15.md). **The cause remains
unresolved; no gameplay or rendering fix is claimed.** The difference predates
the fast-binding change: the earlier direct-r2 executable exhibited the same
original draw stream with GPU-world rendering disabled.

## Established facts

Both retained divergent routes have identical original draw count/hash streams:
914 records differ from the common reference, starting at frame487. The hash
folds original TL vertex/index data before world conversion and replacement
suppression. It does not fold texture or allocation addresses. This is not
merely a relocated pointer appearing in the hash.

The divergent routes use camera data0x50BD8460 at frame280; matching routes use
0x50BD84A0. Camera XYZ first differs at frame492. Existing distance logs do not
capture orientation/frustum, so that does not establish that the entire camera
state matches until492. Address-keyed distance/widescreen maps have no observed
address-bit arithmetic. The guest allocator uses first-fit reuse,16-byte size
alignment and retained freed contents for nonzero allocations. This identifies
a plausible state difference to inspect, not its causal mechanism.

## New controlled checks

Thirteen new live runs completed their intentional budgets with private
save/registry protections intact:

- Eight550-frame runs varied a diagnostic environment value from0 to112 bytes
  in16-byte steps. All original draw records match the common reference.
- Four550-frame launches used one fixed game/output path, the same executable,
  arguments and process environment. The private pilot and registry bytes were
  restored before each launch; outputs were archived after each process exited.
  All original draw records match. Raw vertex/camera captures of frames486–493
  are byte-identical across the four launches. Every captured frame independently
  reproduces the original logged draw count/hash.
- One1400-frame reconstruction used the earlier failing case's name, matching
  all argument lengths and the complete captured MW34 variable key set/value
  lengths in a separate private directory. It matches the common reference and
  all five successful audited-control captures.

The fixed-path launches also have identical semantic allocator operation streams
through frame280:304,404 operations per launch, comparing frame, operation,
address, size and zeroing request. Diagnostic frame-chain bytes are not treated
as allocator semantics. The camera's496-byte allocation occurs at frame236 at
0x50BD84A0. The earlier0x50BD8460 variant was **not reproduced** in this pass.
Neither padding nor path-length reconstruction establishes the cause. Successful
runs do not erase the two failures or prove general determinism.

## Diagnostic implementation and evidence

`apply_divergence_trace.py` adds opt-in capture to a fresh fast-r2 source copy.
`MW34_DIVERGENCE_TRACE` records original TL vertices/indices, render states,
camera/node bytes, matrix and projection globals for frames486–493.
`MW34_ALLOCATION_TRACE` records allocation/free requests and a diagnostic frame
chain through frame280. These capture functions do not write guest memory.
Payloads contain original game data and remain local.

Final diagnostic executable:
`local/remaster/gpu-native-divergence-r2/build/entry_commandline.exe`, SHA256
`6bed876988e82ff2ac92900d9fedd12eaf5a028816f0455928f301f75f71af5d`.
All37,201 translated object entries and shader bytes are unchanged from the
fast-r2 base. `source-snapshot.json` pins the compiled source. The original image
remains U.S.retail1.2, SHA256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.

Private harnesses, build logs, wire-format reader, protected-run records and
`investigation.json` are retained under `local/gpu-divergence-r1/`. Initial
diagnostic source/build attempts are retained separately. The fixed-path vertex
capture SHA256 is `515357030376cbee55180f00dbb50ab4c61e64887aeaff3930753c979a546141`.
The normalized allocator-operation SHA256 is
`95e3d5ec75a2e2e9aceebd69843b4a5fa6aab92ac6d110e4d21baf7d1bb5b901`.

## Remaining boundary

The missing evidence is a divergent run with this detailed recorder enabled.
That would permit comparison of the first differing allocation sequence and
vertex component, including orientation/projection state before XYZ changes.
Physical keyboard APIs, message timestamps and file metadata remain possible
external inputs; none was demonstrated causal here. Do not change their runtime
contracts, reseed game state or zero allocations merely to force matching hashes.

Play remains the Mech Lab build with unchanged executable/profile bytes. This
work adds diagnostic coverage for an identified defect; it does not remove
original CPU projection, publish a renderer change or alter strict131/144 credit.
