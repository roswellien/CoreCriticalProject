# Static analysis: `4C51C0`, fill-construct of 28-byte records

Prepared 2026-10-11. This report is static reverse-engineering evidence only.
It makes no change to source, translation tables, acceptance ledgers, frozen
inputs or existing reports. It claims no lift, recompilation, native execution or
acceptance credit, and it does not change the 131/144 count.

Image: `MW3/Mech3.exe`, SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`, the same
image named by the [initializer inventory](../reports/m4-initializer-inventory/r1/report.json).
Tooling: REA MCP server `rea-agents` 6.1.0 with its installed Ghidra 12.1.4
provider (default auto-analysis, ephemeral database, no annotations written).
The project's own llvm-objdump linear listing, already in
`reports/m4-initializer-inventory/r1/linear-lookup-only.txt`, was used as an
independent decoder cross-check.

## Why this target is outside the 144 gate

Before selecting the target, I checked the following sources:

1. **Inventory roots.** The 144 nonzero entries from the inventory report
   (`0x4040F0` to `0x5AE3E4`) do not include `4C51C0`. They also do not include
   any of its resolved call ancestors: `4C4DC0`, `4C1AB0`, `4C32C0`, `4C5470`,
   `4C3380`, `4C3600`, `4C3B50`, `4C3930` and `4C3DA0`. However, accepted root
   `4C3250` constructs the global object whose virtual method later leads here
   (see Reachability). That root only constructs the object and registers its
   destructor; it never dispatches the virtual method.
2. **Focused project work.** No hex form of `4C51C0` or any ancestor occurs in
   `docs/`, `recomp/`, `runtime/`, `tests/`, `tools/`, `games/` or `cmake/`.
   The address does occur under `reports/` and `local/`, but only in whole-image
   or whole-procedure dumps: linear disassemblies, the inventory's
   instruction-lookup table, REA evaluation procedure listings and the HUD heat
   disassembly. None of these is a focused claim. One `push 0x4C3600`
   instruction appears in a 512-byte decode window of
   `m4-onexit-batch-recovery` (`4C3AC0`–`4C3CE0`). However, that batch's
   `callback-graphs.json` references only `4C3AC0`/`4C3AE0`, not this cluster.
3. **Active lanes and plans.** The [active lanes](m4-active-native-lanes-2026-10-10.md),
   [execution plan r13](m4-execution-plan-r13.md) and
   [application workahead](m4-application-workahead.md) name the widget, font,
   FPS, constructor, numeric, version, registry, MFC, application, reader,
   widget-property, video, input/audio and menu batches. None of them includes
   this address range or this class.
4. **Prior analysis.** No document mentions `_Ufill`/`_Ucopy` or this helper.

### Reachability

Resolved direct callers, from Ghidra and confirmed by the linear listing:

```
4C51C0 <- 4C4DC0 (call sites 4C4EBA, 4C4F8E)
4C4DC0 <- 4C1AB0 (4C1F03, 4C1F5D)
4C1AB0 <- 4C32C0 (4C332C)
4C32C0 <- 4C5470 (4C5494)
4C5470 <- 4C3380 (4C34E9)
4C3380 <- 4C3600 (4C3619)
4C3600 <- address pushed at 4C3B5D inside 4C3B50 (passed as a callback to 4C3E50)
4C3B50 <- 4C3930 (4C3A51)
4C3930 <- 4C3DA0 (4C3DA7)
4C3DA0 <- data only: slot +4 of vtable 0x5CAC78 (stored at 0x5CAC7C)
```

A raw scan of the image for little-endian absolute pointers finds only two:
`4C3600` at file offset `0xC2F5E`, which is the push operand, and `4C3DA0` at
`0x1CA07C`, which is the vtable slot.

The vtable boundaries come from bytes at `0x5CAC40`. The node class's vtable
`0x5CAC6C` has three entries: `4C1A80`, `4C27F0` and `40BAB0`. A second vtable
starts at `0x5CAC78` with entries `4C3CC0`, `4C3DA0`, `4C3DC0`, `4C3DD0` and
`4C3DC0`. Code stores `0x5CAC78` at `4C3CAC` and `4C3D11`, which confirms it as
a separate vtable start.

The external entry into the cycle runs through that second class:

```
4C3250  accepted initializer root (startup109)
  -> 4C3260 -> 4C3C90   constructor: base 4E78D0, this[1]=0, vptr=0x5CAC78
       4E78D0           base constructor: vptr=0x5CD8C0; appends this to the
                        global registry list at 0x60B888
  -> 4C3270 -> 5AC140(4C3290)   registers the atexit destructor
                                (4C3290 -> 4C3CF0)

48FAF0  mission loader (strings "C:\zipper\Mech3\mission.cpp", "Loading HUD",
        "Loading Textures (%d/%d) %s %s", "Failed to Interpret: %s -- Mission
        Load Aborted"; callers 44FFC0, 490AB0, itself)
  -> 4900E3: call 4E7B00   walks registry 0x60B888 and calls 4E7C10 per entry
       4E7C10: mov eax,[ecx]; jmp [eax+4]   -> 4C3DA0 for this object
         4C3DA0 -> 4C3930 -> 4C3B50 -> 4C3E50(callback 4C3600)
           4C3E50: saves callback in global 0x60B39C, calls 4C3ED0, restores it
           4C3ED0: recursive walk via 4C3F70/4C3FB0/4C40E0
             call [0x60B39C] at 4C4092 (in 4C3FB0) and 4C412A (in 4C40E0)
               -> 4C3600 -> 4C3380 -> 4C5470 -> 4C32C0 -> 4C1AB0 -> 4C4DC0 -> 4C51C0
```

Both indirect calls through `0x60B39C` appear in Ghidra xrefs and in the
linear listing. The global has five references in total: one load, two stores
and two calls, all in `4C3E50`–`4C4163`.

The registry has four parallel walkers: `4E7B00` (slot +4, called from
`4900E3`), `4E7B40` (slot +8, `490BAB`), `4E7B80` (slot +0C, `49049A`) and
`4E7BC0` (slot +10, `491801`). Their dispatchers are `4E7C10`/`4E7C20`/`4E7C30`/`4E7C00`.
This was cross-checked against the bytes at `4E7C00` and the linear listing.

**Conclusion:** `4C51C0` executes only when the mission loader dispatches slot
+4 on registered objects. The startup initializer gate executes construction and
registration only. `[vptr+4]` is not dispatched anywhere in the 144 roots'
resolved graphs: `4E78D0` stores the object and returns. This target therefore
belongs to mission loading, outside the 144 gate and outside the application
workahead batches, which end at the retail menu.

**Shared state:** The object created by accepted root `4C3250` is the
receiver at mission load. A future reimplementation of this path must consume
that object and the registry list at `0x60B888` from the accepted startup state.
It must not recreate them. `docs/m4-execution-plan-r6.md` already notes that
`0x60B888` is shared across five roots.

`4C1FF0` writes `0x5CAC6C` at `4C2011`. **Inference:** `4C1FF0` is the node
destructor. It frees +0x3C, then calls `58B390` on `this+4`; its only caller
is `4C1A80`, slot 0 of `0x5CAC6C`, which matches a scalar deleting destructor.

**Uncertain:** The four walkers' callers (`48FAF0` and others) were identified
statically. The mission-load call order and how often `4E7B00` runs per mission
have not been observed at runtime.

## Identity

| Property | Value |
| --- | --- |
| Entry | `0x4C51C0` (`FUN_004c51c0`) |
| Body | `0x4C51C0`–`0x4C51EF`, 48 bytes, one contiguous range, 7 basic blocks |
| Bytes | `8b44240885c076255756538b5c24188bd08b44241085c0740bb9070000008bf38bf8f3a583c01c4a75eb5b5e5fc20c00` |
| Callees | None (leaf) |
| Strings, globals, imports | None |
| Sibling helper | `0x4C5180`, which has the same caller only and is a 28-byte range copy (see Dependencies) |

## Disassembly (Ghidra)

```
4C51C0  MOV  EAX, [ESP+8]        ; count
4C51C4  TEST EAX, EAX
4C51C6  JBE  4C51ED              ; count == 0 -> return (EAX = 0)
4C51C8  PUSH EDI
4C51C9  PUSH ESI
4C51CA  PUSH EBX
4C51CB  MOV  EBX, [ESP+18h]      ; src  (arg 3)
4C51CF  MOV  EDX, EAX            ; remaining = count
4C51D1  MOV  EAX, [ESP+10h]      ; dst  (arg 1)
4C51D5  TEST EAX, EAX            ; loop head
4C51D7  JZ   4C51E4              ; null slot: skip copy, still advance
4C51D9  MOV  ECX, 7
4C51DE  MOV  ESI, EBX
4C51E0  MOV  EDI, EAX
4C51E2  REP MOVSD                ; copy 7 dwords = 28 bytes
4C51E4  ADD  EAX, 1Ch
4C51E7  DEC  EDX
4C51E8  JNZ  4C51D5
4C51EA  POP  EBX
4C51EB  POP  ESI
4C51EC  POP  EDI
4C51ED  RET  0Ch
```

## Calling convention

- **Stack:** The function takes three 4-byte arguments, `[ESP+4]=dst`,
  `[ESP+8]=count` and `[ESP+0C]=src`, and the callee pops them (`RET 0Ch`).
- **ECX:** Both callers load `ECX` with their own `this` (`MOV ECX, EBX`),
  but the callee never reads it. This matches an MSVC `__thiscall` member
  function that ignores `this`. Ghidra reports `__stdcall` because the two
  conventions are indistinguishable when `ECX` is unused. A reimplementation
  can treat it as stdcall with three arguments and `ECX` unconstrained.
- **Preserved:** `EBX`, `ESI` and `EDI` are saved and restored. `EBP` is not
  touched.
- **Clobbered:** `EAX`, `ECX`, `EDX` and flags.
- **Direction flag:** `REP MOVSD` assumes `DF=0`, the normal Win32 ABI state.
  The function does not set or clear DF.
- **No x87/FS use:** The function does not touch the FPU or the FS segment and
  does not register SEH.

## Inputs and outputs

| Input | Meaning |
| --- | --- |
| `dst` (`void*`) | First destination slot. Slots are spaced 28 bytes apart. |
| `count` (`uint32`) | Number of slots. It is tested as unsigned: `JBE` exits only on 0. |
| `src` (`const void*`) | One 28-byte record that is copied into each slot. |

- **Declared output:** None (inferred `void`).
- **Incidental EAX:** On `count == 0`, `EAX` is 0. Otherwise it equals
  `dst + count*28`. Neither caller reads `EAX` after the call: `4C4EBF`
  overwrites `ECX` and then uses `EDI`, and `4C4F93` reloads `EAX` from memory.
  This value should be treated as unspecified rather than as a contract.
- **Final volatile state:** `EDX` is 0 on any `count > 0` path. If the last slot
  was non-null, `ECX` is 0. If every slot was null, `ECX` keeps the caller's
  value.

## Side effects

- For each of `count` slots where `dst + i*28` is non-null, the function writes
  exactly 28 bytes copied from `src`. Each slot receives the same source bytes.
- It reads `src` once per non-null slot and does not snapshot it.
  **Inference:** If `src` overlaps an earlier destination slot, later copies see
  bytes that have already been rewritten. Neither observed caller can create
  that overlap: in one path `dst` is freshly allocated memory, and in the other
  `dst` is the vector's uninitialized end.
- There is no allocation, no global state, no API call and no exception path.
- A null slot address only skips that copy; the pointer still advances by 28.

## Control flow

1. If `count == 0`, return immediately with registers unchanged except
   `EAX = 0` and flags.
2. Otherwise save `EBX`, `ESI` and `EDI`, then loop exactly `count` times:
   - copy 28 bytes from `src` when the current `dst` is non-null;
   - advance `dst` by 28 bytes and decrement the remaining count.
3. Restore the saved registers and return, popping 12 bytes.

A very large unsigned `count`, such as a negative value cast to unsigned, would
loop that many times. Both observed call sites pass 1 (see below).

Equivalent C (derived, not recovered source):

```c
void fill28(uint32_t (*dst)[7], uint32_t count, const uint32_t (*src)[7]) {
    for (; count != 0; --count, ++dst)
        if (dst) memcpy(dst, src, 28);
}
```

## Callers

Both calls are in `4C4DC0`, a 602-byte member function that takes one stack
argument (`RET 4`). It treats `this+4/+8/+0C` as begin/end/capacity pointers of
a vector with 28-byte elements; the stride comes from the `0x92492493` reciprocal
used for division by 28. The caller passes `P = this->end` as its insertion
point.

| Site | Path | Arguments `(dst, count, src)` |
| --- | --- | --- |
| `4C4EBA` | No spare capacity. The caller allocates `max(1, size)+size` elements through `operator new` (`5ABD26`), copies the old range inline, then calls this helper. | `(new_buf + size*28, 1, &value)` |
| `4C4F8E` | Spare capacity exists. The caller first calls `4C5180` to shift `[P, end)`. | `(end, 1 - (end-P)/28, &value)` |

At `4C4F8E`, the count is `1 - (end - P)/28` with `P` equal to the end pointer
read at entry, so the static data flow yields 1. Ghidra marks part of
`4C4DC0`'s alternate path (`4C4FBC`–`4C5005`) as unreachable on the same basis.

`4C4DC0` is itself called twice from constructor `4C1AB0`, once in each branch
of a loop over `*param_2 & 0xFF` items. Each iteration first calls `4C1110`.

## Dependencies

`4C51C0` itself depends only on its stack arguments and memory. The following
functions in its immediate cluster are listed for context; this report has not
analyzed any of them beyond the details stated here.

- **`4C5180`:** A leaf that copies 28-byte records from `[first, last)` to
  `dest`, applies the same null-destination skip and returns the advanced
  `dest`. Its only caller is `4C4DC0`.
- **`40BAF0`:** An empty `RET` body that the caller invokes on the old
  `[begin, end)` range. It probably serves as a shared destroy routine for
  trivially destructible elements. Because this function is shared, it may also
  appear in other graphs, including startup work; it is not part of the target.
- **`5ABD26` / `5ABD1A`:** `operator new` / `operator delete` thunks used by the
  caller, not by the target.

## Interpretation (marked inferences)

- **Probable STL origin:** The routine is very likely MSVC 6 Dinkumware
  `std::vector<T>::_Ufill(iterator, size_type, const T&)` for a 28-byte
  trivially copyable `T`. The loop shape (`for (; 0 < _N; --_N, ++_F)`), the
  placement-new null check, the unused `this`, and the sibling `_Ucopy` and
  empty `_Destroy` helpers all match that library. `4C4DC0` would then be an
  inlined `insert(end(), 1, x)` / `push_back(x)`. **Not verified** against
  library signatures or FLIRT.
  The rest of the vector family has the same 28-byte stride and the same null
  checks:

  | Address | Role |
  | --- | --- |
  | `4C4C60` | Constructor: allocator byte, then three null pointers |
  | `4C4C80` | `reserve(n)`: grows only if `capacity < n` |
  | `4C4DC0` | `insert`/`push_back` |
  | `4C5180` | `_Ucopy` |
  | `4C51C0` | `_Ufill` |
  | `40BAF0` | `_Destroy` |

  This strengthens the structural match, but no signature tool was run.
- **Element layout:** `4C1110`, which builds each record before
  `push_back`, defines the layout:

  ```
  +0x00  dword[3]  v      copied from the argument
  +0x0C  dword[3]  v      second copy of the same three dwords
  +0x18  dword     0
  ```

  **Inference:** The two triples are likely float x/y/z and form a
  current-plus-original or min/max pair seeded from one point. The type of the
  dwords is not confirmed by any float instruction inside `4C1110`.
- **Owning class (unverified):** The class built by `4C1AB0` has vtable
  `0x5CAC6C` with three entries. Its field layout, from `4C1AB0` and `4C4C60`:

  | Offset | Field |
  | --- | --- |
  | +4..+0x10 | The 28-byte-element vector |
  | +0x18 | Constructor argument 4 |
  | +0x1C / +0x28 | Two ±`FLT_MAX`-initialized 3-float bounds |
  | +0x34 / +0x35 | Two flag bytes |
  | +0x38 | A 0–3 mode selected by comparing a float triple against four constant triples at `0x5E8A20`–`0x5E8A58` |
  | +0x3C | `strdup`'d name |

  `4C32C0` allocates a 0x40-byte node only when the source record's
  `(*rec & 0xFF) > 2` and bit 10 is clear. `4C1AB0` then pushes one element per
  point, `*rec & 0xFF` times. **Inference:** Each node is a named polygon or
  outline of three or more points with a bounding box, built while walking a
  scene tree at mission load.
- **Owning subsystem (partially established):** The path runs through the
  mission loader `48FAF0` (`mission.cpp`) and the registry object constructed by
  root `4C3250`. The specific game feature has not been named. `4C3930` gates
  the build on global `0x60861C` and on a flag returned by `4C36C0`.

## Open questions

1. **Resolved:** which call site enters the cycle, and whether it runs during
   startup. The entry is slot +4 of vtable `0x5CAC78`, dispatched by the
   mission loader through `4E7B00`/`4E7C10` (see Reachability). Runtime
   observation of a real mission load would confirm the ordering.
2. **Partially resolved:** the 28-byte element layout. The field numeric types
   and the meaning of the trailing zero dword remain unconfirmed.
3. **Open:** whether the `_Ufill` identification holds under a library-signature
   match. The sibling-function family supports it structurally.
4. **New:** which game feature the `0x5CAC78` registry object implements, and
   what `0x60861C` and `4C36C0` gate.

## Evidence identifiers (REA, this session)

| Observation | Evidence ID |
| --- | --- |
| Binary overview | `ev_5cfc2884…` |
| `batch_decompile` survey including `4C51C0` | `ev_e8cc404c…` |
| `procedure_assembly 4C4DC0` | `ev_590aa647…` |
| `procedure_pseudo_code 4C4DC0` | `ev_2f3a6b12…` |
| `get_call_graph 4C51C0` backward | `ev_213e1db6…` |
| `get_call_graph 4C3B50` backward | `ev_ac297fb8…` |
| `xrefs 4C3600` | `ev_746c5cba…` |
| `xrefs 4C3DA0` | `ev_9a8bc69b…` |
| `xrefs 5CAC6C` | `ev_b7d6844c…` |
| `read_bytes 4C51C0` | `ev_1d6f1684…` |
| `procedure_callers 4C5180` | `ev_08408b24…` |
| Decompilation of `4C5180`, `40BAF0`, `4C1AB0` | `ev_25eca888…` |
| Decompilation of `4C1FF0` | `ev_f9a6e396…` |
| `read_bytes 5CAC40` (vtable boundaries) | `ev_373f800d…` |
| `xrefs 5CAC78` | `ev_c5a23e97…` |
| Decompilation of `4C3C90`, `4C3CF0`, `4C3CC0`, `4C3DA0`, `4C3930`, `4C3B50` | `ev_233a5e0d…` |
| `get_call_graph 4C3C90` backward (to root `4C3250`) | `ev_7888c0c7…` |
| Decompilation of `4C3260`, `4C3270`, `4C3290`, `4E78D0`, `4E79D0` | `ev_08bf8052…` |
| `xrefs 60B888` (registry) | `ev_ca9cacb0…` |
| Decompilation of the registry walkers | `ev_b34c3db3…` |
| `read_bytes 4E7C00` (slot dispatchers) | `ev_b7d82e7e…` |
| `get_call_graph 48FAF0` backward | `ev_38e5b8e2…` |
| `procedure_pseudo_code 4C3E50` | `ev_428c43fe…` |
| `xrefs 60B39C` (callback global) | `ev_4a7615ce…` |
| `get_call_graph 4C3ED0` forward | `ev_a5b61bb0…` |
| Decompilation of `4C1110`, `4C1160`, `4C4C60`, `4C4C80`, `4C32C0` | `ev_361417a1…` |

The mission-loader strings come from `analyze_function 48FAF0`. Its
4.7 MB dossier was read only for referenced strings, callers and the code
surrounding the `4E7B00` call. The rest of that output was not reviewed.

These records belong to an ephemeral REA session and were not exported as a
bundle. Opening the same image with the Ghidra provider and repeating the calls
reproduces them.
