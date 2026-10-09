# CRT locale and parser prerequisites

This is static workahead from the exact staged `MSVCRT.DLL`. It grants no native parser, locale initialization, original DLL attach, allocator, or CRT output completion credit. The accepted command-line carry sources and objects remain unchanged.

The current command-line witness starts with `D` (`0x44`). The original parser therefore reaches its first required lead-byte table read at `7800BCE6`, testing `[78037A25] & 4`. The quoted program-token branch instead tests the table at `7800BC87`. The next executable gate can admit the real parser prologue, writable count locals, and bounded command-line reads, then refuse before that first table dereference. Completing the whole sizing pass needs separately reviewed table initialization.

Evidence is in [recovery-r2/report.json](../../reports/m4-crt-locale-workahead/recovery-r2/report.json) and [pins.json](../../reports/m4-crt-locale-workahead/recovery-r2/pins.json). The report SHA-256 is `cbccc6391f72121e2c9bda05b745beb6494a5e52cf9738507aa4b23f832b6188`. The first run is retained; it stopped after static extraction because its frozen witness path omitted the `native-` directory prefix.

## Table ownership and initialization

The exported `_mbctype` storage starts at `780379E0` and contains 257 bytes. The parser indexes its 256 classification entries from `780379E1` with a zero-extended input byte. All 257 source-file bytes are zero, but this proves file identity only. Source code explicitly initializes and modifies this writable table; the current accepted bootstrap has not executed that initialization.

The original default path is ordered as follows:

| Source site | Required operation |
| --- | --- |
| `780018A1` | Attach calls the initialization stub at `78003DD2`, after the still-unexecuted helper at `78001897`. |
| `78003DD4` | The stub calls `_setmbcp` at `78003DDB` with selector `-3`. |
| `78003DE6` | `_setmbcp` first calls the CRT lock helper for lock 25. |
| `7800107B` | Lock 25's zero source slot takes a real `malloc(24)` dependency before lock publication. |
| `7800108D` | Lazy lock publication takes lock 17, whose nonzero file pointer alone does not prove critical-section initialization. |
| `78003DEE` | Only after lock return does the code resolve the selector. Selector `-3` tailcalls `GetACP` at `78003EAB`. |
| `78003E29` | A code page outside the five built-in descriptors queries `GetCPInfo` before table clear and range stores. |

The source descriptor table contains code pages 932, 936, 949, 950, and 1361. The selected descriptor or actual `CPINFO` lead-byte range pairs drive bit-4 stores. Source clears occur in the hot and cold `_setmbcp` paths; `7800E50A` sets the lead-byte mask from `CPINFO`, and `7800E552` combines the descriptor masks. The later classification helper also requires its own string-type and locale-map helper contracts.

An import-free original helper at `7800E648` clears the full 257-byte table and associated code-page metadata. It is a possible source-qualified C/single-byte bootstrap experiment, but its use would need an explicit scheduling and domain contract. It does not establish the original default ANSI code-page or process-attach path.

`GetACP` returns the current Windows ANSI code-page identifier. `GetCPInfo` reports success or failure and fills `CPINFO`; `MaxCharSize` alone does not establish DBCS behavior, and lead-byte ranges do not fully describe every encoding. These API outcomes must be measured rather than inferred from file bytes. See Microsoft's [GetACP](https://learn.microsoft.com/en-us/windows/win32/api/winnls/nf-winnls-getacp), [GetCPInfo](https://learn.microsoft.com/en-us/windows/win32/api/winnls/nf-winnls-getcpinfo), and [CPINFO](https://learn.microsoft.com/en-us/windows/win32/api/winnls/ns-winnls-cpinfo) contracts.

## Parser gate

The full parser is the literal 436-byte body at `7800BC48..7800BDFC`. It has no outgoing calls. Its real current frame is `2000182C`, with return `7800BBFC` and arguments `[33000000, 0, 0, 20001850, 2000184C]`. The source first clears the character count at `7800BC53` and sets the argument-slot count to one at `7800BC5D`. Null output buffers suppress output writes in the sizing pass; they do not suppress input, table, counter, or caller argument-slot scratch accesses.

Every actual byte read, including lead-byte lookahead, must fit the immutable NUL-inclusive owned command-line extent. The implementation also needs bounded loops, checked 32-bit count and allocation-size arithmetic, exact source flag handling, and current typed ownership. The output pass needs separately owned vector and character buffers, actual allocator evidence, checked stores, and the source null sentinel.

The source return restores the saved registers, increments the argument-slot count at `7800BDF8`, and reads the real return word at `7800BDFB`. A sizing return would leave cdecl `ESP=20001830` and `EAX=20001850`. The builder then reads both counts, computes vector-plus-character allocation size, and calls the allocator at `7800BC06`; it does not immediately remove the parser arguments. The allocator, second parser call, published `argc`/`argv`, environment ownership, and full startup return remain separate gates.

## Reproduce the static recovery

Run from the project root with a fresh output name:

```powershell
& C:/Python314/python.exe tools/m4-crt-locale-workahead/recover.py recovery-r3
```

The script verifies each decoded instruction byte against the exact staged PE, extracts only the selected dependency spans, records source permissions and unique API import ownership, and physically hashes its critical inputs. It reads the frozen native command-line witness solely to select the first source branch. It does not execute the original DLL, native provider, or parser. The direct-reference inventory is bounded evidence, not an exhaustive alias analysis.
