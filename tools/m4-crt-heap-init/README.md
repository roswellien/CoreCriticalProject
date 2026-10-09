# Bounded CRT heap bootstrap research

This isolated x64 worker extends the accepted locale-default research caller at its actual `mainargs-before` checkpoint. The original provider and game are read as pinned source data. Neither is launched.

The explicit scheduler projects only the low guest State EIP to the exact original seven-byte attach fragment at `7800183C`. Guest ESP stays `20001860`; the generic Runtime CPU stays at its actual `__getmainargs` service slot and frame. There are no scheduler guest-memory stores. The compiled fragment executes the original `PUSH 1` and `CALL 780039BF`, providing the genuine initializer argument and return frame. This is fragment bootstrap scheduling; preceding DllMain instructions were not executed.

The full 77-byte source heap initializer is lifted separately at O0 and O2. The admitted path executes nine source instructions and eight checked DWORD accesses across the two bodies. Its original indirect `CALL [7802E0A8]` reads the pinned raw import value `0003461E` and commits return word `780039D6` before the generated ESP and EIP updates. The raw import is independently resolved from the original PE metadata to the unique `KERNEL32.dll!HeapCreate`, hint 411. At that frontier the guest frame is `20001848`, with arguments `[0, 4096, 0]`.

The worker raises a typed unresolved-import fault before any host API call, allocation, API return, or heap-global publication. No heap initializer completion, locale initialization, parser progress, original DllMain completion, or full M4 completion is claimed. The prior 17 pages, 22 guest COFF objects, and two FDIV libraries remain the accepted inputs. No heap-global page is added for future source paths.

`XOR EAX,EAX` at `780039BF` has undefined AF. The generated scalar bridge supplies a recorded representative zero for this exact compiled artifact. Early faults may retain that representative; no universal AF value is claimed. The later source CMP defines all terminal arithmetic flags.

`prepare.py` pins the accepted baseline and source recovery receipts, derives additive caller and bridges, and compiles the two exact source bodies. `build.ps1` composes the worker while binding its compiler, headers, objects, and libraries. `run.py` executes 36 bounded research sequences at each optimization and strictly packs every capture. It labels execution as performed by the delegated author; root acceptance independently checks the source-derived original-BEFORE model and the recorded archives.

The 24 ordinary rows per optimization use the frozen startup input corpus. Controls 109 through 120 exercise source mutations, checked stack protection, partial CALL stores, argument and IAT corruption, opaque-token rejection, pre-CMP flag publication faults, API frontier State/source mutations, and terminal observer exceptions. Failed attempts are retained in separate report directories.

The public binding tokens and parent pointer are compared against private current authority and an immutable admitted parent before dereference. Source accesses are checked against exact PC, address, width, direction, and value. Observers cannot silently modify guest State, generic CPU, FX, lifecycle, or source ledgers. Partial faults retain completed stores before generated register publication, keep the first diagnostic, revoke authority, preserve caller FP and LastError, and reject replay.
