# Heap-mode selector and genuine stack-probe boundary

This isolated Windows x64 experiment extends the accepted real HeapCreate
bridge. It reuses all 26 guest COFF objects and both FDIV libraries unchanged,
then links four new objects from the exact 37-byte selector prefix and complete
49-byte stack probe. The admitted provider remains a pinned data input.

The scheduler preserves the earlier State-only EIP projection to the literal
attach fragment. Source PUSH/CALL instructions, the real owned HeapCreate call,
its finite checked guest return and the original heap-global publication carry
into the selector without State, FX, existing-page or generic CPU reseeding.
The full x64 HANDLE remains privately owned and live through the new work.

The selector at `78003A0C` pushes its incoming EBP and calls the original probe
at `780058B5` with EAX `122C`. The translated probe reads both page-touch words,
restores saved ECX, moves ESP and genuinely pushes and reads its relocated
return word. Its source RET returns to `78003A19` with ESP `20000624` and EAX
`78003A19`. The selector then pushes saved EBX and its version-structure pointer,
stores only the original size DWORD `0x94` (148 bytes) at `200017B8`, and makes
the real indirect CALL at `78003A2B`. The worker refuses at the unique raw
`KERNEL32.dll!GetVersionExA` import before executing that API.

Twenty page captures preserve the previous eighteen mappings and add the raw
RX probe page at `78005000` and a fresh owned lower-stack page at `20000000`.
The latter is a declared research input, zero at ordinary initial admission.
It is neither an original-captured memory value nor proof of Windows guard-page
stack growth. Runtime stack policy and TIB bytes remain unchanged. Directed
independent fixtures can provide nonzero initial patterns before context
admission. The binding privately retains that input and the exact committed
source writes; subsequent unrelated lower-page changes are rejected.

The ordinary path executes 39 source instructions and 24 source DWORD accesses,
including five actual source CALLs and the probe RET. The earlier HeapCreate
API-return read remains separately recorded. The new compiled bodies total
86 bytes; 84 of those bytes execute. Combined with the earlier success path,
132 source bytes execute. Full source identity totals 2,026 bytes. XOR/TEST AF
is architecturally undefined at `39BF`, `39D6`, `58DB` and `58C5`; only the
exact generated representative zero is admitted at these sites. Other flags
follow the actual instructions and the declared probe input words.

All exits retain the first diagnostic and perform real cleanup of the privately
owned full handle. Source-written guest globals are retained as terminal
diagnostic evidence after the experiment closes its host heap. The guest token
does not remain a usable heap. The binding rejects duplicate, stale and foreign
use and preserves actual caller LastError and the admitted hardware state.

Production rows comprise 24 ordinary inputs and 12 source/ownership fault
controls per optimization level. Control 135 explicitly removes lower-page
read permission after the probe-before snapshot. The actual first TEST read
fails; its catch restores only that test permission so the partial machine
state can be captured. No bytes are reseeded, no denied access is committed and
no source continuation follows that fault. Controls also cover source identity,
relocated return corruption, source-store failure, observer exceptions and
cleanup. Native execution and packing use one serialized I/O window.

New row files use the `heap-mode-` prefix. The aggregate source ledger has
64 slots, the API ledger 8 slots, the event ledger 16 slots and the job record
44 DWORDs. The three added phases are `heap-mode-probe-before`,
`heap-mode-probe-after` and `heap-mode-query-before`; the earlier heap-create
phase tags remain. Their existing witness/registry field names capture the new
private owner with the same 16-QWORD and 18-QWORD layouts. The unused frozen
heap-create row job remains separately recorded.

No OS-query result, selected heap mode, selector return, allocator result,
heap-initializer return, locale/parser completion, original DllMain scheduling,
standalone game window or full M4 completion is established by this boundary.
