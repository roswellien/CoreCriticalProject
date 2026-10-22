# Pirate's Moon compared with the MW3 native target

Initial local static investigation, 2026-10-14. This evaluates reuse; it does
not launch Pirate's Moon, admit a new supported binary, or claim native gameplay.
MW3 acceptance remains **131/144**. Existing runtime and asset work is unchanged.

## Finding

Pirate's Moon is a close engine relative and a promising additional native
target. Its platform imports and retained engine module names support substantial
reuse of the MW3 translation infrastructure and host services. Its executable
addresses, dependencies, data archives and lighting still require separate
recovery and validation. This is not a measured percentage of shared gameplay
code, and substituting its executable into the current host is not supported.

## Exact local inputs

| Property | Current MW3 target | Pirate's Moon candidate |
| --- | --- | --- |
| Local executable | `MW3/Mech3.exe` | `MW3-PiratesMoon/Mech3.exe` |
| SHA-256 | `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf` | `57cd2ee74bafda3eeb9e9353c7c78a8b7c213a81f3040f1be7c2a164c505ddd9` |
| File bytes | 2,384,384 | 2,220,057 |
| Format / preferred base | PE32 i386 / `0x400000` | PE32 i386 / `0x400000` |
| Entry VA | `0x5AC3A0` | `0x5CEFE8` |
| Image size | `0x5F5000` | `0x714000` |
| `.text` virtual bytes | 1,810,328 | 1,952,280 |
| `.data` virtual bytes | 3,938,292 | 5,293,172 |
| Static import symbols | 474 | 474 |
| Imported libraries | 18 | 15 |

The PM executable's Windows version resource reports `1, 0, 11, 5`; its local
README identifies Version 1.0 (U.S.), 15 November 1999. These identify the supplied
candidate; its full installation/patch/modification provenance is not established.
The MW3 identity is already recorded in
[supported-binaries.json](../games/mw3/config/supported-binaries.json).

PM's smaller file does not imply a smaller engine: its code section is 7.84%
larger, while its resource section is much smaller. Static section sizes are
neither function counts nor runtime memory measurements.

## Platform and engine overlap

Comparing `(case-folded DLL name, exact symbol name or ordinal)` gives **448
shared imports**, or **94.5% of each executable's 474 imports**. Each has 26
imports absent from the other. This measures static import overlap only; it
does not cover dynamically resolved calls or COM interface methods.

- Both import `DirectDrawCreate`, `DirectDrawEnumerateA`, `DirectInputCreateA`,
  DSOUND ordinal 1 and DPLAYX ordinal 4. Their import cells have different RVAs.
  Identical entry APIs do not establish identical queried COM interfaces.
- Both use MFC42 and MSVCRT. PM has 225 MFC imports versus 219 in MW3 and uses
  MSVCP60 instead of MSVCP50. The MSVCP lock constructor/destructor names match
  across the changed library, but that does not establish DLL equivalence.
- PM adds imports including `_msize`, resource enumeration/loading, rectangle
  operations and keyboard-state handling. MW3's static AVI/VfW imports are
  absent from PM; PM's actual cinematic route remains unresolved.
- A printable ASCII scan followed by terminal C/C++ source-basename extraction
  finds 89 unique basenames in each image and 85 shared. Retained paths place
  PM under Zipper's `branchep1/gamez` and `branchep1/mech3ep1` trees, versus
  MW3's `GameZMech3` and `Mech3` trees. Shared names include mission, player,
  weapons, mech animation, geometry, render, input, sound and network modules.
  This supports common lineage; assertions/string retention are incomplete
  source inventories and do not prove matching implementations.

The bounded disassembly at PM's entry shows an ordinary x86 startup sequence
installing an FS exception record and making CRT-related indirect calls. This
supports using the existing guest ABI/SEH infrastructure as a starting point;
required initializers and the application entry still need a complete PM map.

## Concrete adaptation boundaries

**Host startup and translation.** The present host explicitly selects MW3's
`0x5AC3A0` entry in
[composition.cpp](../tools/m4-crt-heap-carry/composition.cpp), binds a pinned
MSVCP50 image and uses MW3-specific addresses in
[main_v2.inc](../tools/m4-crt-heap-carry/main_v2.inc). PM requires its own image
identity, import bindings, startup/initializer map, translation closure and
guest-global layout. Share infrastructure after checking each contract;
do not share MW3 addresses or treat platform import overlap as game-code reuse.

**Lighting.** The shipped PM README describes Light Maps / A / B modes using
multitexturing. PM also retains light-map and headlight-related strings. The
current native draw path selects texture stage zero in
[d3d_provider.inc](../tools/m4-crt-heap-carry/d3d_provider.inc), and
[d3d_scene.frag](../tools/m4-crt-heap-carry/d3d_scene.frag) implements one sampled
texture stage. This identifies a concrete rendering compatibility question:
recover PM's actual draw/interface/state usage and validate its light-map
combination before claiming faithful PM lighting. Merely storing several
texture-stage states is not proof they are rendered.

**Assets.** The staged content uses familiar ZBD archives and texture-bank
directories, with concrete reuse and concrete incompatibilities:

- Existing strict RGB565 format inspection accepts all 376 PM interface images
  and all 4,242 entries in its high-quality hardware mech texture bank. All
  3,360 MW3 names in that mech bank are retained, with 882 additional names.
  The alphabetically first 30 shared mech payloads are byte-identical; this
  bounded sample is not a whole-bank equality result. No image rendering was
  performed. The three supplied fonts are byte-identical by SHA-256.
- PM reader archives have a 12-byte `version=2, count, extra DWORD` footer,
  versus MW3's 8-byte `version=1, count` footer. The existing runtime
  `ReaderArchive::parse` in [assets.cpp](../tools/m4-assets/assets.cpp) rejects
  the PM layout. With the candidate v2 footer, 148-byte directory records
  validate structurally across 52 PM database archives / 1,495 entries.
  The extra DWORD's meaning and actual PM reader behavior remain unresolved.
- Sampled geometry and animation archives retain MW3 magic values but change
  their following header words and add a DWORD. Their compatibility is unknown.
- The selected PM world hardware texture package has five entries rejected by
  current strict inspection; the software package also fails its package-header
  check. Interface/mech results must not be generalized to all textures.
- Sound banks retain concatenated PCM WAVE records, with 812 clips per PM bank
  versus 999 in MW3. Eight PM high-quality clips use 16-bit PCM. PM sound
  directories also use the changed v2 footer; audio playback is untested.

Detailed bounded results and methods are in the private `asset-summary.json`.

## Method, evidence and next step

Metadata/imports were read with the existing `tools/analysis/pe.py` PE32 parser;
version metadata with Windows file inspection; source basenames with an ASCII
scan of strings of at least six printable characters. Startup inspection used
the existing LLVM 21.1.8 disassembler over VA `0x5CEFE8..0x5CF090`. Source review
checked current startup bindings and the Vulkan texture-stage path. REA with
Ghidra 12.1.4 independently imported the exact PM image and reported 10,949
procedures and 3,741 analyzed strings, evidence
`ev_4904960ec31df427134fbc490956fff9a1e8c6326947607d60f0fd5c794c8b76`.
Those analyzer inventories are not source-function counts or code matching;
analyzed string objects differ from the raw printable scan above. No game
process, active SQLite database, full acceptance job or game build was started.

Private metadata and retained strings are under
`reports/pirates-moon-comparison-r1/`. Original media and derived binary content
remain local under the [distribution policy](legal.md).

The next implementation investigation is a separate PM identity/startup map:
bind its exact dependencies, map required initializer effects through its
application/menu entry, and identify the first unresolved service. In parallel
with that future work, recover the changed archive layout and lighting contract.
This session advances understanding of the PM input -> loader/asset/renderer
boundaries; it advances no executed native PM boundary. Physics, AI, save
compatibility, timing and whole-function similarity remain unmeasured.
