# FDIV reference replay contract

This additive experiment replays the 24 direct, debug-off original writer
inputs through the independently accepted native FDIV Registry. It leaves the
accepted Registry, Runtime r9, source pack, lifted bodies and earlier gates
unchanged. It grants no whole CRT startup, initializer-table or menu credit.

The original primary stream retains all 48 rows and every stack byte. Its 24
debug-on rows expose real Windows API return registers and the exact breakpoint
RF/DR6 interventions. Those rows clear legacy FP metadata during OS context
restoration. They are separate ABI observations and are excluded as native
architectural replay inputs.

The replay input comes only from direct original BEFORE CPU, FXSAVE512 and
FNSTENV28. An opaque native Remill State is newly authored, with every observed
32-bit GPR/arithmetic flag, CW/SW/tags/raw 80-bit storage, MXCSR and eight x86 XMM
registers projected into its corresponding architectural fields. Its legacy
IP/CS/OP/DP/DS come from FNSTENV; its separate Runtime FX512 remains the literal
original FXSAVE representation. Empty logical FP slots and State bytes that
x86 hardware does not expose remain declared authored storage. They cannot be
called original observations and must be preserved by the native source model.

The original real writer stack pointer W projects to the unchanged Registry's
owned guest frame at `0x20001800`. Each byte of the observed original window
that fits its guest page is copied from BEFORE using the explicit address
translation `guest = original - W + 0x20001800`. The remainder of that owned
native page is authored fill, labelled outside original observation. The outer
return word projects from the authored original capture `0x10000100` to the
Registry's admitted callback continuation `0x78004232`. All internal source
CALL/RET PCs and source pointer constants remain literal.

The provider starts from the same admitted sparse source/constant pack and
literal IAT/data pages. Original private IAT values are real 32-bit API pointers;
the native image retains its raw import words and the reviewed Registry projects
only the owning source import reads into typed module/function routes. Returned
host module handles and FARPROCs are bound to their actual platform module and
export identities. They project to Registry-issued guest tokens without claiming
32-bit and 64-bit pointer equality. The native service performs its own real
Windows lookups and feature query. Original AFTER results do not seed a native
result or initialized global.

The native Registry keeps its declared ECX/EDX/flags representative across API
calls. Real original volatile observations remain separate, including the two
source-copied ECX high halves at `[W-34,W-32)` and `[W-42,W-40)`. Those differences
must appear in comparison rather than silently becoming equal. The full original
Windows service stack footprint and instrumentation/caller storage remain raw;
they are not a portable native whole-stack output contract. A bounded comparison
must independently identify source-owned defined stores, source read dependencies,
the explicit outer-frame/token projection, and ABI unspecified bytes. Full native
State/FX/pages/events and actual routes must also pass their own source model.

The incoming domain stays the twelve measured normalized masked IC0 control
words, empty TOP0/SW0, MXCSR `0x1F80`, flat guest DS/SS and Runtime-owned guest FS.
It does not admit pending/deferred exceptions, nonempty FP stacks, NULL/fallback
queries, general Windows service emulation, or full SEH/unwind. A successful
reference capture or replay alone is not original/native equivalence acceptance.
