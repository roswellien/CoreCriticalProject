# Next control-provider integration boundary

The independently accepted provider component is ready for a fresh connected
game-wrapper gate. Static preparation now lifts both complete game functions:
the wrapper at `0x5AC5A0` (19 bytes, five instructions) and its import thunk at
`0x5AC5D6` (6 bytes, one indirect tail JMP). They link to two actual Remill
definitions without missing-block fallback. No native execution or import
admission is granted by this preparation.

The [preparation record](../../reports/m4-crt-control-integration/preparation-r1/report.json)
has SHA-256 `2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a`.
It binds the exact game/provider files, named `_controlfp` import at IAT
`0x5BB578`, provider export `0x780042E1`, complete source slices, lifter,
semantics, linked IR and actual command logs. The actual CRT-entry CALL at
`0x5AC431` targets the wrapper and returns at `0x5AC436`; this single source
site is linkage evidence, not complete CRT-entry execution.

The wrapper pushes mask `0x30000` and new value `0x10000`. Its CALL at
`0x5AC5AA` reaches the thunk with return word `0x5AC5AF` already on the guest
stack. The thunk's indirect JMP transfers that same frame to `_controlfp`.
The real compiled provider must RET to `0x5AC5AF`, after which the compiled
wrapper executes its own `ADD ESP,8` and RET. Adding a second guest CALL frame
at the import thunk would produce the wrong stack and continuation.

The first implementation should use a separately reviewed typed import port
around the frozen shared Runtime r9. The port must bind the owning CALL/thunk,
named IAT slot, original IAT bytes, real existing return frame and exact provider
identity before dispatch. No host function pointer belongs in the guest IAT.
The callback-to-object and provider code associations need actual build and
review records. Every unsupported route or memory fault must propagate through
the outer runtime call and leave it incomplete.

One possible port uses r9's existing checked `call_import`: project the
already-pushed frame to its caller-ESP convention, then let the runtime write
the same return word at the same address and invoke the native provider.
That orchestration must be explicit and separately observed; it must not
consume an extra stack word or be recorded as a second original instruction.
The guest State remains at the real frame throughout the handoff. If that
representation cannot prove ownership, return integrity and fault propagation,
a separately compiled runtime extension is required; frozen r9 stays unchanged.

The original reference should execute the complete wrapper, thunk and four
provider bodies with the declared loader resolution of this one IAT slot.
Record complete CPU, every stack byte, guest FX512/ENV28 and host restoration.
Any return broker must be disjoint from all required bodies and identified as
instrumentation. The native counterpart keeps the image's original raw IAT
and routes through its typed port. Protect every State byte and retain actual
entry, tail transfer, provider CALL/RET and wrapper cleanup observations.

Begin with the provider's twelve measured incoming CWs, empty tags, SW0/TOP0
and MXCSR `0x1F80`. Guest masks may change, but this component performs no
numerical instruction afterward. Later connect the reviewed 26-root sequence
and prove that its numerical callbacks use the resulting guest CW with actual
host isolation. Initialized data imports, other CRT calls, SEH and the complete
144-root initializer ledger remain separate required work.
