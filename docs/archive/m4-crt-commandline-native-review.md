# Native CRT command-line writer review

The bounded OS-backed command-line writer/data route is accepted on
2026-10-07. The actual provider CALL at `0x7800188C` obtains the process's
ANSI command line, returns to `0x78001892` and stores an owned 32-bit guest
buffer address in `_acmdln` at `0x78037174`. Native code uses the unchanged
r9 runtime and preserves the original game data-IAT DWORD. Host addresses
do not enter guest data.

The [independent raw model](../../reports/m4-crt-commandline-native/independent-raw-foundation-r1/report.json)
checks 384 original and 768 native records: complete CPU, 3,504-byte State,
all five pages, raw80/environment state, ordered accesses and service routes.
Eight authored command-line fixtures are passed to ordinary Windows process
creation; each process measures its own actual OS bytes. Equality is checked
from those measurements. The reviewer rejects 1,256 corrupted observations.

The [independent source/build and causal closure](../../reports/m4-crt-commandline-native/independent-final-review-r1/report.json)
proves the complete translated body, all 34 ABI layouts and actual State
stores. Its compiled O0/O2 tests pass 638 checks across 56 scenarios, including
actual OS bytes, partial ownership cleanup, first-fault preservation and
complete host FX/environment restoration. All 2,221 physical bindings were
rehashed before acceptance. Compiler/tool/header hashes are recorded identity
associations, rather than complete execution-time dependency attestation.

The [separate service FP review](../../reports/m4-crt-commandline-native/independent-service-fp-r1/report.json)
checks all 768 native mid-service snapshots and rejects 1,344 additional
corruptions. Their complete non-SIMD FX storage and ENV28 match the separately
captured host entry. Mid-service SIMD values remain actual volatile API and
observer temporaries; complete outer SIMD restoration is checked separately.
All 2,224 bindings in this additive review were also rehashed.

The original writer stops at `0x78001897`, followed by an explicit capture
jump. It does not perform a complete DLL attach or original RET. Original
Windows-service volatile CPU/FP observations are retained; the native software
State preservation policy is a declared representative, rather than proof of
the full Windows implementation. The bounded inputs use twelve masked CWs,
empty TOP0/7, serial execution and stable mappings/borrowers.

The earlier [reference-only ownership gate](m4-crt-data-review.md) retains its
separate credit. This new route measures and copies actual native OS bytes;
full argv/environment parsing and provider initialization remain open.
`_adjust_fdiv`, complete CRT/SEH, all required initializer roots and native
startup/menu behavior still need implementation and review.
