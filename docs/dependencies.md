# Dependencies and reproducibility

The bootstrap runtime depends only on the C++20 standard library. Binary tools
use only Python 3.11+ standard-library modules. No libraries are fetched by CMake.
Build requirements are CMake 3.24+, a C++20 compiler, and Python for tests/tools.
The separate authored-fixture experiment uses Remill/LLVM below. Neither is
required by ordinary builds. Native equivalence is proven for the reviewed
ADD/branch/memory fixture suite at O0/O2; MW3 coverage remains pending. Original
game launch uses app-local dgVoodoo2, recorded in the MW3 findings.

CI pins checkout/setup actions to immutable commits. Hosted runner images and
compiler servicing versions can still change; these builds are verification,
not a byte-for-byte release reproducibility claim. Record compiler, CMake and
Python versions alongside experimental results. Reports should not embed
wall-clock timestamps or absolute input paths unless specifically needed.

Every future dependency must be pinned to an exact version or commit and record
its license, build flags and integrity hash where applicable. Record the LLVM
revision and target triple with translated IR. Do not automatically track a
lifter's default branch. clang-format/clang-tidy are optional developer tools;
agree on a formatting major version before enforcing it for release builds.

## Opt-in arithmetic experiment

| Dependency | Pin observed in the built source | License |
| --- | --- | --- |
| LLVM portable Windows MSVC distribution | 21.1.8 / `llvmorg-21.1.8` | Apache-2.0 with LLVM exception |
| Remill | v6.0.1 / `0e324aee8c67a63ec759ef379dcfafa0b3cb1448` | Apache-2.0 |
| Intel XED | v2025.06.08 / `dc6bdbe036515c7ef55d3b2d50bafc5232bfe534` | Apache-2.0 |
| Intel mbuild | v2024.11.04 / `7c4497f41f576b43a80bb0f8d8452bbcfd58b6e2` | Apache-2.0 |
| gflags | `52e94563eba1968783864942fedf6e87e3c611f4` | BSD-3-Clause |
| glog | v0.7.1 / `7b134a5c82c0c0b5698bb6bf7a835b230c5638e4` | BSD-3-Clause |
| GoogleTest | v1.17.0 / `52eb8108c5bdec04579160ae17225d66034bd723` | BSD-3-Clause |
| lifting-bits Sleigh | `7c6b7424467d0382a1303c278633e99b0d094d5b` | Apache-2.0 |
| Ghidra source fetched by Sleigh | Base `80ccdadeba79cd42fb0b85796b55952e0f79f323`, plus pinned Sleigh patches | Apache-2.0; component notices apply |

LLVM archive: `clang+llvm-21.1.8-x86_64-pc-windows-msvc.tar.xz`, downloaded
from the official llvm-project release; SHA-256 matched its published digest:
`749d22f565fcd5718dbed06512572d0e5353b502c03fe1f7f17ee8b8aca21a47`.
Remill v6.0.1 source archive SHA-256:
`763831798f36985b867693301cd11770838ee7eed550f705eaabdea4eef39abc`.
Original dependency license files remain in the ignored local tool checkouts;
their licenses do not change the project's MIT license.

Build recipes are `tools/lifting/build_remill.ps1` and
`tools/lifting/build_fixture.ps1`; `tools/lifting/remill-v6.0.1-x86.patch` records
the only Remill source changes. Clang-cl/LLVM 21.1.8 builds the Release lifter with
the static MSVC CRT (`MultiThreaded`), external LLVM, upstream tests off,
SPARC32 semantics off, barriers treated as no-ops, and
`MW34_X86_FIXTURE_ONLY=ON`. Targets are `remill-lift-21` and `x86` only. The ADD
fixture has no barrier instructions; this flag establishes no general barrier
semantics. XED decodes the selected x86 instructions.

The portable LLVM package omits the SPARC backend; the patch conditions those
library links on backend availability. Unused PowerPC spec compilation was
excluded after its local Sleigh compiler was blocked by Device Guard. Sleigh
support libraries still build; no blocked compiler was executed through another
route. This is a scoped x86 experiment, not a validated multi-architecture build.
Upstream tag-based dependency recipes were used; the full resolved commits above
must be checked when reproducing, rather than assuming tag names are immutable.

The archive's LLVM CMake export names a nonexistent Visual Studio 2019 DIA
library. Its local text configuration was corrected to the installed Visual
Studio 18 Community `DIA SDK/lib/amd64/diaguids.lib`. LLVM binaries were unchanged.
Ghidra's patched local commit IDs depend on patch-application identity/timestamps;
reproduce its pinned base and patches, not those generated commit IDs.

The fixture targets are `i686-pc-windows-msvc` and `x86_64-pc-windows-msvc`.
Host compilation uses `llc -O0`, and separately `opt default<O2>` then `llc -O2`.
The x64 C++ bridge requires Clang's Remill-compatible State layout. Records include
lifter, semantics, official LLVM DLL, generated IR/object and executable hashes.
See [the experiment record](fixture-add-experiment.md) for measured results,
reproduction, the State alignment contract and the resolved Application Control blocker.
The [G1 suite](fixture-suite-experiment.md) extends that same pinned pipeline to
signed branches, partial registers, memory writes, callee stack cleanup and shifts
whose undefined intermediate flags are overwritten before observation.
`tools/lifting/run_fixture_suite.ps1` builds/tests all four reviewed fixtures and
verifies their combined evidence. `tools/lifting/build_mw3_leaf.ps1 -RunComparison`
uses the same toolchain for the [admitted MW3 leaf](mw3-leaf-experiment.md).
No additional external dependency is required.

## Separate Mod Tools source preview

These dependencies apply to the editor setup, not the asset-free C++ bootstrap.

| Component | Pin and license | Use and distribution |
| --- | --- | --- |
| Pillow | 12.3.0; MIT-CMU | Desktop map images; installed into `.venv-mod-tools` from hash-pinned Windows x64 wheels in `tools/release/mod-tools-requirements.txt` |
| Mech3AX | v0.7.0-rc3 Windows x64; EUPL-1.2 | Archive extraction/reconstruction; user installs separately; observed `unzbd.exe`/`rezbd.exe` SHA-256 pins are enforced by setup |
| Three.js | r128 / 0.128.0; MIT | Browser scene preview; included source hashes, official upstream URLs and license are recorded in `games/mw3/mod-tools/editor/web/static/js/third-party.json` |
| Tkinter | Supplied with the user's CPython distribution | Desktop UI; setup checks its availability without fetching another GUI framework |

The Pillow pin matches the existing local editor environment, rather than tracking
the latest release. Exact wheel hashes were read from
[PyPI's version metadata](https://pypi.org/pypi/Pillow/12.3.0/json). The wheels keep
their embedded dependency notices; the source-preview ZIP does not redistribute
Python, Pillow wheels or Mech3AX binaries. The observed converter binary pins are
local identities, not independent verification of an upstream release signature.
See [Mod Tools setup](setup-mod-tools.md) for requirements and remaining limits.
