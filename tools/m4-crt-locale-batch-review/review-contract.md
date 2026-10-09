# Independent whole-locale batch review contract

This is a source/ABI review plan. It adds no native execution or completion
credit. Canonical original input is the pinned staged MSVCRT provider SHA
2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7
and its existing full provider-decode.stdout. Accepted ancestors remain frozen.

## Complete source unit

The unit must return through all four InitializeCriticalSection calls in the
41-byte static helper 78003BF4..78003C1D, the default locale stub and _setmbcp,
both original parser passes, original argv/argc stores and builder RET7800BC47.
The builder's genuine caller is 7800BA9E, from CALL7800BA99. Following BA9E
through the full __getmainargs RET would additionally copy the environment
pointer; that needs its own explicit contract and must not imply environment
construction. An intermediate helper/import is an observation, not completion.

External research CALL stores, argument cleanup and EIP transitions must have
separate ledgers. Nested malloc/free uses its authentic source stack and SEH
chain. Complete carried State, Runtime FX/CPU, source pages and guest FS are
preserved except for source, measured API transport and declared research
effects. Expected output cannot be seeded from AFTER captures.

## Native critical-section ownership

The original guest CS size is 24 bytes; malloc rounds this to 32. Native SDK
CRITICAL_SECTION storage is a separate correctly aligned 40-byte object.
Static guest objects are only 24 bytes apart, so native object bytes must never
be written to their guest slots. Treat the finite source's CS pointers as
opaque checked guest tokens, not native pointers or a bytewise x86 API model.

Each private native object binds the active Runtime, parent private heap,
guest extent/token, generation, host thread and initialization state. Enter
and Leave require matching live authority and recursive ownership depth.
Foreign-runtime/thread, stale, interior and forged aliases are refused before
any native wait or release. Publication of the lazy guest pointer belongs
exclusively to original source store780010A3. The source race-loser/free path
has no real concurrent execution credit unless safe private concurrency is
implemented and witnessed.

Initialize/Enter/Leave/Delete are void APIs. Do not manufacture a native BOOL
or advertise a meaningful guest EAX result. Use a declared finite preserved
volatile-register representative with a genuine checked guest stdcall return
read and argument consumption. _setmbcp writes EAX from ESI after unlock at
78003E7D, so this path needs no invented return value.

Fault cleanup unwinds recorded native recursive entries, deletes every
initialized owned CS once, releases owned lazy/parser allocations, then
destroys the private heap. Never delete an entered object, free backing still
associated with a live CS, or destroy a heap with owned allocations/CS. If an
actual OS release fails, retain ownership and honest evidence. Cleanup is a
research lifecycle action, not original CRT detach. The native deletion
requirements follow [Microsoft's DeleteCriticalSection contract](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-deletecriticalsection).

## Typed actual NLS transport

GetACP supplies an actual UINT32. CPINFO is typed/aligned SDK storage with a
20-byte witness, including failure bytes. WCHAR and WORD are 16-bit; BOOL and
signed native return counts are 32-bit. GetStringTypeW and A have distinct
argument counts. Conversion/map size queries must pass genuine null output
pointers, retain actual response counts and distinguish byte capacity from
UTF-16 code units. Optional default-character/used-default pointers need
separate private typed storage and checked guest transport.

Copy genuine inputs to private scratch before invocation, and validate full
guest input/output permissions again after hooks immediately before native
work. Input/output witnesses and API export identities remain immutable;
record API output commits separately from source stores and API return reads.
Actual failures drive original source branches; do not hardcode ACP, selector
caches, Unicode probe outcomes, classifications, lengths or case maps.

LCMAP_SORTKEY uses byte-oriented output despite the W signature, as documented
by [Microsoft's LCMapStringW contract](https://learn.microsoft.com/en-us/windows/win32/api/winnls/nf-winnls-lcmapstringw). Ordinary
classification calls use the source's measured 0x100/0x200 paths. Any broader
flags/response support must be explicit; a reachable unimplemented contract
must refuse with its genuine source frontier rather than gain wrapper credit.
Negative input lengths require bounded NUL-inclusive reads from an owned
guest input. Dynamic stack reservations/probes require declared admitted pages
and checked arithmetic; real source stack effects remain visible.

## Parser ownership and bounds

Sizing count includes the terminal argv NULL slot. Source allocation request
is char_count+4*vector_count; source publishes argc=vector_count−1. Bound the
vector and character subranges separately, including required NUL writes.
Every source lead-byte/lookahead read stays within its actual NUL-inclusive
input. A lead byte immediately before the last NUL must retain any actual
source fault rather than receive invented padding. Guest allocation tokens
map to independent full native pointers; multiple lazy/parser allocations
remain live under the same parent heap until research cleanup.

## Bounded independent evidence

Use ordinary source-input variations and declared empty/quoted/escaped parser
inputs with explicit provenance. Declared parser inputs are distinct from
measured GetCommandLineA bytes; neither is an injected NLS/API success.
Target post-creation/acquisition faults, alias/runtime/thread denial, recursive
ownership, post-CALL IAT/export mutation, partial NLS transport and parser
vector/character bounds. Final row counts depend on the frozen candidate's
available hooks and are declared before execution, never reported as actual
until passed. Avoid broad ancestor reruns and per-instruction gate captures.

Independent host observers actively load rich nonzero legacy ENV/raw80 state
and capture complete ENV28, CW/SW/FTW, raw80x8, MXCSR, XMM6..15, LastError and
ABI DF. Full State/FX/CPU and every mapped page are captured at functional
milestones and terminal retry. Checked native direct archives are the only
capture emission path; strict unchanged readers admit their complete union.
