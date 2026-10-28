# M4: real version query and selector return

The current startup gate implements a real native `GetVersionExA` bridge and continues the original heap selector through its genuine return. All 48 ordinary author runs returned the selector value **1** and stopped at the original caller, before heap-mode publication. The heap initializer itself has not returned.

The bridge copies the actual guest structure into a private, aligned host object, calls the named Windows API, records its full BOOL and all 148 output bytes, and transports those observed bytes through checked guest writes. The source then makes its own decisions. Other responses lead to the next original environment-variable query, which remains unresolved. No OS response is invented in production tests.

The source model matches the 48 ordinary runs across **40 complete checkpoints**, preserving State, floating-point state, runtime CPU data and 21 mapped pages. The additional page contains the original cold return path. TIB and Policy limits remain unchanged; the declared lower page changes only through checked source stores. Heap ownership stays private and uses full-width host handles through query, source execution and cleanup.

The author and independent reviewer passed **268 integrated native scenarios** in total. Independent review checked **396 hardware-state pairs** and witnessed 148 real heap creations with 148 matching successful releases. Its four additional host-only malformed-size API diagnostics remain separate from integrated source coverage. An initial legacy floating-point metadata failure is preserved; the identical compiled retry passed every unchanged strict check, and the initial loss remains unexplained.

The selected initializer inventory remains **27 of 144**. These CRT helper steps do not add initializer roots. Standalone menus remain an M4 objective, and native Training remains an M5 objective. Earlier live helper and numeric tests retain their separate scope.

## Next gate

Admit the original caller's comparison and mode-global store, verify the mode-dependent continuation and complete the heap initializer's genuine return. The remaining locale, argument-parser and startup services still need their own acceptance evidence.

The current gate's evidence and final checks are recorded in [the technical review](m4-crt-heap-version-review.md). The preceding accepted boundary is [the selector prologue and stack probe](m4-progress-heap-mode.md).
