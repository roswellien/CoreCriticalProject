# MW3 1.2 executable memory map

Observed on 2026-10-06 for `mw3-us-1-2-retail`, SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
The bounded Python PE parser and LLVM 21.1.8 `llvm-readobj` agree on the reviewed
headers, sections and all ordinary imports. This map describes the file, not a
running process or a working general loader.

The file is 2,384,384 bytes (`0x246200`), PE32/i386, Windows GUI subsystem.
Preferred image base is `0x00400000`; entry RVA is `0x001AC3A0`, VA `0x005AC3A0`.
Image size is `0x005F5000`; headers occupy `[0, 0x400)` in both file and RVA
space. Section alignment is `0x1000`, file alignment `0x200`. Ranges below are
half-open; add the preferred base to an RVA to obtain a VA.

| Section | File range | Declared virtual RVA range | Raw bytes | Permissions |
| --- | --- | --- | --- | --- |
| `.text` | `[0x400, 0x1BA400)` | `[0x1000, 0x1BAF98)` | `0x1BA000` | Read/execute |
| `.rdata` | `[0x1BA400, 0x1DEE00)` | `[0x1BB000, 0x1DF8B2)` | `0x24A00` | Read |
| `.data` | `[0x1DEE00, 0x1F3C00)` | `[0x1E0000, 0x5A17F4)` | `0x14E00` | Read/write |
| `.rsrc` | `[0x1F3C00, 0x246200)` | `[0x5A2000, 0x5F4590)` | `0x52600` | Read |

`.data` has a zero-filled virtual tail `[0x1F4E00, 0x5A17F4)`, 3,852,788 bytes
(`0x3AC9F4`). The other sections' raw sizes include file padding beyond their
declared virtual sizes. These declared ranges do not include all loader page
rounding. There are no overlapping ranges under the parser's bounded model,
no writable executable section, and no file overlay after the final section.
Do not translate file offsets directly into guest addresses or read virtual
zero-filled storage from an unrelated part of the file.

## Directories and loader questions

| Directory / property | Observed state | Consequence or next work |
| --- | --- | --- |
| Imports | RVA `0x1DDFB8`, size `0x17C`; 18 libraries / 474 entries | See [API inventory](api-dependencies.md). |
| IAT | RVA `0x1BB000`, size `0x7B0` | Guest import routing remains unimplemented. |
| Resources | RVA `0x5A2000`, size `0x52590` | Present; resources were not decoded/extracted in this review. |
| Exports | Absent | No exported function seeds. |
| Base relocations | Absent; COFF relocations-stripped flag set; dynamic-base flag clear | Safe whole-image rebasing is not established; preserve reviewed guest VAs. |
| TLS, delay/bound imports | Directory entries zero in both tools | No tables declared here; DLL TLS and dynamic loading remain separate questions. |
| Exception, debug, load-config, certificate, CLR | Directory entries zero in both tools | Does not establish absence of x86 SEH or C++ exceptions. |
| Architecture, global pointer, reserved | Directory entries zero | No declared directory content to decode. |

At entry VA `0x005AC3A0`, decoded instructions install an FS-relative exception
frame; CRT imports include exception handlers. Windows x86 SEH is therefore a
tracked dependency despite the empty PE exception directory. No entry point,
DLL initialization, TLS callback or import has been executed by these tools.

The [selected leaf](first-function.md) fits entirely within file-backed `.text`.
It needs a small executable reservation and an initialized stack for its isolated
comparison; it does not need the full image, IAT, `.data` tail or process startup.
A future full loader must separately validate page permissions, zero fill,
import identities, entry/TLS/SEH behavior and fixed-base address assumptions.

Private evidence: `reports/mw3-recon/pe.json`, `llvm-headers.txt`,
`disassembly.txt` and hash/provenance record `review.json`. Full-image disassembly
is a linear decoding view and cannot establish every function or code/data boundary.
