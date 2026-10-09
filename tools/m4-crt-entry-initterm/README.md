# Actual first CRT initializer interval

This isolated additive experiment connects the game's compiled CALL at
`0x5AC440` to the frozen compiled import thunk `0x5AC598`, named `_initterm`
slot `0x5BB510`, and the complete staged MSVCRT provider at `0x780014F8`.
The 28 original provider bytes are statically lifted and lowered to Windows
x64 after verifying all 34 guest/host State layouts. The instruction body
remains intact, including its indirect callback CALL. Annotation helpers use
their upstream identity bodies; the undefined TEST AF bridge has its own name.

The first actual interval `[0x5E0248,0x5E024C)` contains one null DWORD. The
compiled provider pushes/restores ESI, reads the real arguments, visits that
null slot, rereads the end argument, and returns to `0x5AC445`. Its callback
branch is terminally denied by the typed supervisor when exercised by a late
causal mutation; no callback success or selected initializer execution is
invented. Real game continuation sets up five argument pointers and stops at
unimplemented `__getmainargs`, source CALL `0x5AC468`, IAT `0x5BB514`.

The same admitted Runtime, 3,504-byte State and separate FX512 persist from
FDIV initialization through control, math-error registration and this interval.
Fourteen previous captured pages become sixteen: the already admitted game
table page `0x5E0000` is borrowed unchanged, and a complete literal provider
page `0x78001000` is mapped RX before execution. No provider data, FP metadata,
CW or State is reseeded between these components. Checkpoints retain 934 source
identity bytes, complete pages, guest TIB/globals, both CPU views, events and
first-fault status. Positive paths have 48 game accesses, eight initterm
accesses (one thunk and seven provider), six initterm routes, and ten Runtime
records with only the root incomplete.

The new private Session derivative has exactly three edits: a forward
declaration, replacing the old `_initterm` registration pointer with the actual
compiled provider adapter, and withholding the old callback continuation
publication. That unused continuation would map an overlapping 28-byte slice;
this gate owns the complete literal RX page instead. The preceding three
service bodies and globals retain their original behavior. Frozen Session
files and accepted objects are unchanged. No callback continuation is admitted.

Final author candidate: `preparation-r3` and `build-r3`. The actual
`execution-r2` passes 48 positive compositions and 96 causal denials at O0/O2,
with 282 direct host boundary pairs. The twelve new controls cover source/IAT
and table changes, an actual nonnull callback CALL denial, first PUSH permission
failure, a later stack read bounds failure, RET word/nonvolatile closure,
observer failure, argument rejection and a later end-pointer change. All
required faults clear current ownership and nesting; terminal retry retains
the complete stopped State, FX, pages and logs. BridgeAbort becomes a named
standard exception at the typed execution boundaries. The existing caller
FX/legacy ENV guard and `/EHs` remain in place.

The artificial ESP mutation after the MOV argument read has different next
operand observations at O0 and O2. O0 computes `0x20002008`; O2 retains the
earlier compiled operand `0x20001874` while the observed StateESP is changed.
Both are denied by the current operand guard at `0x78001502`. This injected
observer case does not grant original architectural partial-fault equivalence.

Acceptance requires separate root instruction modeling and independent compiled
host/fault reviews. See `docs/m4-crt-entry-initterm-review.md`. Full CRT startup,
the main 144-root table, argument setup service, native menus and a complete
game remain open. The accepted selected initializer count remains 27.

Use fresh immediate report names for `prepare.py`, `derive.py`, `build.ps1`,
`run.py`, `observe.py` and `seal.py`. The final build reads the literal
preparation; historical source materializers and unsuccessful preparations,
builds and observations remain retained.
