# M4: heap selector and stack probe

This gate advances the x64 startup research path through the original heap-mode selector's prologue and stack probe, stopping at its first `GetVersionExA` import. The probe executes its original relocated return. The version query, selector return and heap-initializer return remain unfinished.

The earlier live helper and numeric-initializer tests still apply. This gate runs isolated x64 workers; it does not launch the game. Standalone menus remain an M4 objective, and native Training remains an M5 objective. The selected initializer inventory remains **27 of 144**; these helper steps do not add initializer roots or support an overall completion percentage.

## Implemented boundary

The accepted heap-creation path supplies a privately owned, full-width Windows heap handle. The original x86 source sees an opaque guest token. The selector then saves its frame, calls the original stack probe, touches the declared lower stack page, relocates its return address and returns to the selector. Original source instructions prepare the version-query argument and execute its indirect CALL.

Execution stops before the OS query. Only the structure's size DWORD has been initialized by source; the remaining version information is not invented. The heap is destroyed through its private full-width handle on completion of this bounded run and on tested faults.

The new source footprint is 86 guarded bytes, with four new AMD64 objects for the two optimization levels. It preserves the prior 26 objects and two FDIV libraries. The combined path executes 132 original source bytes, 39 instructions, 24 source memory accesses, five CALLs and one probe RET. The heap API's return read is recorded separately.

## Stack domain and limits

The research worker adds one declared, owned lower stack page and one raw code page, preserving all 18 previous mappings. Ordinary runs start the lower page at zero; directed fixtures declare other initial contents. These bytes are research inputs, not an original-game memory capture. The original TIB and runtime stack-limit metadata remain unchanged. This gate therefore does not prove Windows guard-page stack growth.

The source's defined flags are checked from those inputs. Undefined AF uses the generated representative zero at four exact source sites; universal equivalence of undefined flags is not claimed. State, floating-point state, runtime CPU data and complete mapped pages are checked at each checkpoint.

## Next gate

Implement and review the `GetVersionExA` bridge with a declared guest output contract and authentic CALL return. Then recover and verify the selector's subsequent decisions and return before completing the heap initializer. The locale, argument parser and remaining startup services still need their own bounded gates.

Both optimization levels passed **204 native scenarios** across the author and independent reviewer, including directed faults and six declared lower-stack inputs. The ordinary model matched all 48 rows across 34 complete checkpoints; the independent final audit also passed. There were 156 actual heap creations and 156 matching successful destructions.

Evidence and final verification are recorded in [the technical review](m4-crt-heap-mode-review.md). The preceding accepted boundary is documented in [heap creation](m4-progress-heap-create.md).
