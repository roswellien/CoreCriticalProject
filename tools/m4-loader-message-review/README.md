This work is a compile-only message-provider candidate for the remaining
`47F760` loader root. It grants no accepted function or native game-launch credit.

`physical-r4/report.json` binds both local DLL identities separately. The current
`MW3/Mech3Msg.dll` has 1,577 pairs/messages; the staged DLL has 1,540. Executable
entry `10001B30` runs CRT initialization and user DllMain `10001710`, which calls
the sorter `10001000` on every notification. A datafile mapping omits those
effects. The source CRT allocates 128 bytes, initializes an empty exit table,
copies `_adjust_fdiv`, and traverses a one-null-pointer initializer range.

The current sort direct CFG has 952 physical instruction sites and no unresolved
calls. Entry's raw-hook and exit-callback edges remain explicit dynamic frontiers.
The source has no TLS directory or delay imports. Its 1,618 HIGHLOW relocations,
whole table pointers, and RT_MESSAGETABLE 11 / ID 1 / language 1033 resource are
retained physically. No source instruction execution is claimed by this review.

`native-build-r1` contains two genuinely executable PE32+ DLLs, compiled at O0/O2.
Their whole 68,528-byte message leaf matches the current source byte hash. The
native table carries authenticated 32-bit name-pointer metadata without treating
those integers as host pointers. Its independent insertion sort preserves the
complete unique name/ID permutation. This does not prove instruction, stack,
flags, or complete quicksort equivalence. The native module's own CRT allocation
and startup are separately scoped; they do not establish original MSVCRT parity.

`ABI-build-r1` compiles source-frame size/offset and native handle-width witnesses,
plus a wrapper calling actual native LoadLibraryA and GetProcAddress. The wrapper
is a prototype requiring caller-authenticated Context/thread/module aliases,
whole call-frame bytes, native hardware CPU/FX witnesses and module file identity.
Nonzero tokens and correct PCs alone do not authenticate these relations. It
retains incoming/outgoing LastError around APIs and preserves the physical source
boolean: successful module loading succeeds even if export resolution returns 0.
No wrapper or DLL has been executed.

Before any runtime admission, root must independently review the current source,
compiled bodies, table/comparator/resource identities and all frontiers. A later
bounded experiment must load the approved executable x64 candidate with real
LoadLibraryA, resolve ZLocGetID, measure its actual path/whole identity/import
owners/generation, observe attach allocation and the whole sorted table, retain
resources through the source lifetime, and scope teardown separately. A datafile
fallback is forbidden. Candidate selection requires an explicit relation between
the original bare-name CWD/search result and the derived native module file.

There are two honest implementation boundaries: a reviewed x64 source/provider
projection closing original CRT/module/State/CPU/FX effects, or an owning 32-bit
broker that genuinely executes the original loader/import/DllMain lifecycle and
returns typed opaque module/export aliases to the 64-bit caller. Neither boundary
is currently admitted, and no runtime observation may be replaced by DLL names,
resource similarity, success booleans, or this compilation evidence.
