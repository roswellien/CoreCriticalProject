# CRT command-line parser connection (retail entry route)

Execution boundary advanced: the compiled game CRT entry (`0x5AC3A0`) now runs the
staged MSVCRT ordinary command-line parser body (`0x7800BC48`) natively, instead of
stopping at the builder's CALL `0x7800BBF7`. The parser body is the existing lifted
object `reports/m4-crt-mainargs/recovery-r3/normal_parser-{O0,O2}.obj`; no new lift.
After its admitted RET the literal builder loads the two counts, pushes
`numchars + 4*numargs` and stops truthfully at its `malloc` CALL
(`0x7800BC06 -> 0x780012B3`) with a typed `unresolved_translation` fault.

These sources are a versioned copy of the frozen
`reports/m4-crt-commandline-carry/preparation-r5` composition. Only these changes:

- `parser_stage.hpp` (new): exact counting-pass Stage owner. argv/args must be NULL.
  Byte reads only from the owned command line or the 256-byte `_mbctype` class table
  at `0x780379E1`; DWORD access only to its own pushes, argument words, the two
  reused argument slots and the two count words; any byte store refuses; RET must be
  `0x7800BBFC` with entry ESP+4 and restored EBX/ESI/EDI/EBP.
- `composition.cpp`: routes lifted intrinsics to the active Stage, connects
  `sub_7800bc48`, stops at `sub_780012b3`, and defines `__remill_write_memory_8` and
  the parser undefined-flag representative (AF only; the body has no AF consumer).
- `carry.hpp`/`carry_binding.inc`: `parser_call` keeps every `parser_stop` frame and
  argument check, then exact post-parser count loads/PUSH/CALL stores and `malloc_stop`.
- `main_v2.inc`: ordinary scenarios now require the malloc frontier and carried counts.
- `native/CMakeLists.txt`: links the parser object.

Build (Developer PowerShell, x64) with the same objects/flags as frozen `build-r6`
plus `-DMW34_PARSER_OBJECT=<repo>/reports/m4-crt-mainargs/recovery-r3/normal_parser-<level>.obj`,
`-DMW34_COMPOSITION_SOURCE=<repo>/tools/m4-crt-parser-carry/composition.cpp` and
`-DMW34_COMPOSITION_DIRECTORY=<repo>/tools/m4-crt-parser-carry`, into
`build/m4-crt-parser-carry-<level>`. Run exactly like the frozen worker:

```powershell
build/m4-crt-parser-carry-O0/entry_commandline.exe MW3/Mech3.exe reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O0.obj local/mw3-staged/Shared_DLLs/MSVCRT.DLL reports/m4-crt-fdiv/native-derived-r1/pack.bin reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin <fresh-output-dir>
```

Observed (2026-10-11): all 24 ordinary O0 scenarios stop at `malloc` with
`numargs=8,numchars=425` (request 457 bytes); an O2 run whose output path forces a
quoted argument ending in `\\"` yields `numargs=8,numchars=548`. Both equal an
independent implementation of the documented VC CRT counting algorithm applied to
the run's own owned command-line bytes. The twelve injected-fault controls still
refuse before the parser. Limits: still seeded from the frozen original BEFORE pack;
second (filling) parser pass, malloc/heap, environment and `__getmainargs` return are
not connected; no accepted-function, startup or menu credit.
