# Independent default-locale prefix review

The reviewed native candidate is `m4-crt-locale-default/preparation-r4` and `build-r2`. Its explicit host scheduling seam runs before command-line production and before the ordinary mainargs body. It changes only the carried State EIP/ESP and writes a separate scheduler return word at `2000185C`. The generic Runtime CPU and its actual eleven call records stay unchanged. Sixteen existing mappings remain; one literal raw RX page at `78003000` makes seventeen.

The original source stub pushes selector `-3`; real source calls enter `_setmbcp`, lock 25, and then `malloc(24)`. The native test stops after the real call at `7800107B` writes return `78001080` into frame `20001810`, before the malloc body begins. The bounded prefix has fifteen completed source DWORD accesses and twenty executed source PCs. The compiled source extents are 9, 169, and 43 bytes; the identity guard retains the entire 91-byte lock body, giving 269 bytes of locale source identity. No source bytes are patched or appended.

The private known locale authority controls opaque-token routing, including a null or invalid public owner. The binding compares its public parent to its immutable private association before dereferencing it. Stale direct entry uses the current authority for rejection. Cleanup clears both public owner and private authority across terminal observer faults.

## Receipts

| Proof | Result | Report SHA-256 |
| --- | --- | --- |
| [Independent static source contract](../../../reports/m4-crt-locale-default-contract/review/source-r2/report.json) | 15 accesses, 20 PCs, real malloc frame | `1098249ae0c9a4403de5cd50749b6e45e2d07bd9baae07fa9f892671760b92c8` |
| [Source, State ABI and COFF audit](../../../reports/m4-crt-locale-default-contract/review/audit-r1/report.json) | 16 previous objects and two FDIV libraries unchanged; six new AMD64 objects; guest32/host64 State layouts agree | `c3e38a3e9373c986ef2efe32b2f166f681db720cce70dd9c6d0a9eaf036b0fef` |
| [Independent native fixtures](../../../reports/m4-crt-locale-default-contract/review/native-r1/report.json) | 132 cases, 4,838 recorded assertions, 50 malformed-token denials | `488989b1598b8b11a9db014e6013006f9d11d0d70f1ccff0c547b842dd646af2` |
| [Hardware and closed inventory checks](../../../reports/m4-crt-locale-default-contract/review/check-r3/report.json) | 264 actual hardware pairs, 548 semantic denials, 14 inventory/request denials | `7fadc54a04f85c840773557ab265962a0aad24123eb0c92684f73de347a9c56d` |

Each optimization executes six clean original-BEFORE cases, twelve author controls, and forty-eight independently authored controls. The tests include malformed public and parent tokens, whole stale-object preservation, partial source CALL stores before ESP/target publication, CMP reads before flag publication, terminal owner republishing with exceptions, and poisoned retries. The recorded assertion count excludes the extra native report-stream completion check printed afterward.

The hardware validator bodies are reused unchanged from the accepted carry review. Actual native caller captures retain raw 80-bit x87 registers, complete legacy environment and tag fields, MXCSR, and ABI nonvolatile XMM registers. Volatile XMM0–5 equality is not claimed. The independent logical inventory specifies the exact sixty-six requests, their required and absent phases, and all records. Each archive contains 59,878 logical files; physical source, tool, object, header, log and archive closure is rehashed without a metadata-only cache. Original flat captures remain historical output after strict publication.

The current reader converts the publisher's exact `{bytes, sha256}` records into the frozen transport's exact `{size_bytes, sha256}` schema without changing names, extents or hashes. Checker attempts `check-r1` and `check-r2` are retained with their source snapshots and failure receipts: the first stopped on this schema mismatch, and the second stopped on a source-manifest attribute typo after semantic checks. Neither changed the candidate or caused another native run. Static `source-r1` retains the superseded proposed CPU projection; the final contract is `source-r2`.

This proves the bounded native source prefix and its required allocation dependency. It grants no malloc body, allocated buffer, initialized critical section, default code page, locale-table initialization, original DLL attach, parser completion, or full M4 credit. File-zero table bytes remain source identity only. The next source dependency is the real allocator path and its provider heap/SEH requirements.

## Reproduce with fresh directories

Run `discover.py source-r3` for the independent static contract. Run `audit.py <fresh-preparation> <passed-production-build.json> <fresh-audit-directory>` for the source audit. The generated fixture compiles with `build_controls.ps1 -CompileOnly`, executes with `run.py <compiled/flat-build.json> native-r2`, and is checked by `check.py <native/report.json> <fresh-check-directory>`. Compilation and native fixture execution use the exact prepared production composition and frozen original-BEFORE inputs; original x86 and the game are never launched.
