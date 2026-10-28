# Recovered CRT provider contract

The four complete staged x86 MSVCRT functions `_initterm`, `__set_app_type`,
`__p__fmode` and `__p__commode` now match the native service model across 1,728
actual original provider records and 3,456 native records at O0/O2. The private
comparison is [provider-comparison-r1](../../reports/m4-crt/provider-comparison-r1/report.json).
This is a bounded provider contract gate. Actual connected game initializer
execution through `_initterm`, the full CRT entry, exception handling and menus
remain open.

The original probe executes only those four exact measured provider bodies at
their preferred guest addresses, plus small authored callbacks. It does not
load the DLL, resolve its imports, invoke DllMain or execute game instructions.
The staged provider's identity is explicit; the DLL selected by the host when
running the original game has not been observed. Public tools contain authored
fixtures and source hashes. Original provider code is extracted privately from
the user's local file.

Nine cases cover null slots and callback order, last-callback volatile results,
empty and reversed intervals, a callback replacing the next table pointer,
a callback shrinking the caller's end argument and each MOV-only global
service. Each case runs with twelve masked control words, all eight x87 TOP
positions and two repetitions. Physical x87 tags are empty; raw 80-bit storage
and XMM input bytes are nonzero. This does not validate unmasked exceptions,
occupied x87 arithmetic or callback exception dispatch.

The native workers replay only original **before** CPU, FX, legacy environment
and memory fields as common inputs. They never read original after fields as
expected results. The comparison checks all ten CPU DWORDs, all captured FX512
bytes, separate legacy ENV28 and every one of the 8,204 owned stack, table and
provider-global bytes before and after. The original worker captures actual
host FP state before/after restoration. All 864 guest repetitions match exactly
and both native optimization levels produce identical raw streams.

Windows hardware FX metadata is zero in these observations while legacy ENV
retains the deliberately nonzero prior FOP/FIP/FDP/selectors. The native worker
seeds and captures these fields separately in the pinned 3,504-byte Remill
State; it checks complete State preservation after the integer-only services.
Reserved environment bytes remain an input representation, with architectural
legacy fields captured from State. There is no original Remill State or
original event trace. The native visit/CALL ledger is separately checked against
the recovered provider control flow and authored callback memory effects.

All 118 observer corruptions and eighteen actual worker admission controls
reject with their intended diagnostics. Existing output sentinels remain exact;
workers create owned staging files with `CREATE_NEW` and publish without
replacement. A build-relative include-path failure and a control-runner Windows
newline mismatch are preserved in separate failed attempts. Neither is counted
as a semantic failure control or discarded before a fresh run.

The fresh native build consumes the independently accepted runtime r9 and
compiles both native service implementations again. Older chain artifacts keep
their archived runtime ABI. The earlier [native model contract](m4-crt-contract.md)
is an acceptance-time preflight document; this experiment adds original
equivalence evidence without changing that frozen source snapshot.

The reproducible sequence is:

```powershell
C:/Python314/python.exe tools/m4-crt/prepare_probe.py --out reports/m4-crt/fresh-extraction
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File tools/m4-crt/build_probe.ps1 -ExtractionDirectory reports/m4-crt/fresh-extraction -OutputDirectory reports/m4-crt/fresh-original-build
C:/Python314/python.exe tools/m4-crt/run_original.py --build reports/m4-crt/fresh-original-build/build.json --extraction reports/m4-crt/fresh-extraction --out reports/m4-crt/fresh-original-run
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File tools/m4-crt/build_crt.ps1 -OutputDirectory reports/m4-crt/fresh-native-build -ReplayInclude reports/m4-crt/fresh-original-run
C:/Python314/python.exe tools/m4-crt/run_native.py --build reports/m4-crt/fresh-native-build/build.json --original reports/m4-crt/fresh-original-run/original.bin --out reports/m4-crt/fresh-native-run
C:/Python314/python.exe tools/m4-crt/compare_replay.py --original-report reports/m4-crt/fresh-original-run/report.json --native-report reports/m4-crt/fresh-native-run/report.json --out reports/m4-crt/fresh-comparison
```

Original execution requires normal Windows pre-CRT reservations and fresh
ordinary private directories. Concurrent writers, reparse paths and production
publication are outside this worker contract. Required unresolved services,
including `_controlfp`, `__getmainargs`, allocators, locale/thread/environment,
termination and SEH dispatch, still fault explicitly. M4 is incomplete.
