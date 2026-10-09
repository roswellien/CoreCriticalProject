# M4 native image foundation

Accepted 2026-10-07 as the first image-mapping prerequisite for
[M4 startup and menus](m4-startup-plan.md). M4 remains open. This native x64
diagnostic host loads the exact MW3 executable into checked guest storage;
it does not execute the startup entry or display menus.

The [build record](../reports/m4-startup/foundation-r1/build.json) binds fourteen
authored/dependency sources, nine tool files and 64 artifacts. The
[independent review](../reports/m4-startup/independent-review/report.json) passed
with SHA-256
`a18e7d752aa0d4c9a1c15d57afd6e1d0716a2edd97c48ac8e4a6b42b478519b5`.
Its [pins](../reports/m4-startup/independent-review/pins.json) also preserve the
4,774-file durable M3 map and supplement the generated build-rule/SDK resource
compiler binding. The build rules name that compiler; the nonverbose logs do
not establish a separate invocation. Full transitive Windows SDK headers and
import libraries are not claimed as independently pinned.

## Implementation and measurements

The C++ loader validates the PE32 structure, preferred image base, sections,
directories and complete imports before returning an owned `LoadedImage`.
It supports the reviewed fixed-base executable subset with stripped relocations.
Unsupported nonempty directories and malformed metadata reject. Custom limits
can tighten the default bounds; they cannot expand them.

The admitted image has base `0x400000`, entry `0x5AC3A0`, four sections and
18 ordinary imported libraries. Header/section mappings use exact guest
permissions and page-rounded extents. Raw section padding is copied; virtual
tails and remaining padding are zero-filled. Cross-region access retains the
existing checked-memory contract: a nonempty transfer must fit one mapping.
Directory admission establishes contiguous file backing and readability; it
does not decode the resource tree or establish native resource use.

The [actual mapping measurement](../reports/m4-startup/foundation-r1/actual-image/report.json)
compares all five regions and **6,246,400 bytes** with zero differences against
both a separate file model and Windows' passive image view. The latter is
observed by a separate executable with no project PE-loader dependency. It
uses `SEC_IMAGE_NO_EXECUTE`, runs no original instructions, invokes no DLL
loader and performs no import resolution. Its behavior is documented by
[Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createfilemappinga).
This comparison concerns pre-initialization image bytes on this host; it is
separate from a live game's CRT/DLL initialization, IAT fixups and runtime state.

All **474 imports** match an independent parser and retain their actual original
IAT dwords. The IAT is read-only `.rdata` in this image. Native service routing
and import fixups remain unimplemented; raw dwords are never converted into
host function pointers.

The tests pass 136 authored loader checks, nine causal public CLI rejections,
five native SHA/admission checks, and two modified-real-image identity
rejections. They exercise structure/span/alignment/overflow/overlap boundaries,
zero tails, padding, permissions, import names/ordinals/aliases, missing input
and exact identity. Checks remain active in the Release build. The independent
review reparses actual PE/import data without importing the primary Python
parser or mapping verifier.

## Reproduction

Use the admitted user-owned `MW3/Mech3.exe`, the accepted local toolchain and the
existing M3 evidence dossier. Missing prerequisites fail; there is no skipped
test or fallback game execution. All full inputs, mapped observations and
compiled artifacts remain in ignored directories.

From a normal Windows PowerShell session, choose a new experiment name:

```powershell
Set-Location D:/Projects/MW34Recomp
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/m4-startup/build_host.ps1 `
  -OutputDirectory D:/Projects/MW34Recomp/reports/m4-startup/foundation-replay
```

The output/build directories must be new. The script configures Clang 21.1.8
x64 with C++20, builds the standalone loader/host/tests/reference probe, runs
the authored controls and passive original-image comparison, and binds the
resulting sources/tools/artifacts. It changes execution policy only for that
PowerShell process. The project-level CMake and earlier runtime sources are
unchanged.

The diagnostic host is at:

```text
D:/Projects/MW34Recomp/build/m4-startup-foundation-r1/mw34_m4_startup_host.exe
```

`--inspect-image MW3/Mech3.exe` emits the mapped-region and import report.
`--image MW3/Mech3.exe` deliberately stops with exit code 3, guest PC
`0x5AC3A0`, and the unresolved CRT/SEH/initializer/MFC startup reason.
This verifies that required startup is not silently bypassed. Use the existing
original-game launcher for ordinary play; this executable is a research host.

The [first initializer gate](m4-initializer-experiment.md) now supplies one
verified real translated startup initializer. Full M4 still
needs the complete constructor/CRT/MFC context, application callbacks, required
services, native frame/menu creation and measured input/shutdown behavior.
