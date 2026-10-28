# Build the shipped native host

This is the maintained host-only build for issue #25. Its baseline is the source
used for MW3 native runtime 1.0.44, with one portability edit replacing an absolute
include in `control_context.hpp`. The complete patched host is in `host/`;
`build_host.ps1` builds those files directly. It never runs an `apply_*.py` chain
or reads an owner's host folder, saved compile command, lift report or object list.

## Inputs

- Windows x64, Python 3.11 or newer, Visual Studio C++ Build Tools and a Windows
  SDK. The wrapper imports the installed x64 compiler environment using `vswhere`.
- LLVM **21.1.8**, including `clang-cl.exe`, `lld-link.exe`, `llvm-lib.exe` and
  `llvm-readobj.exe`. CMake 3.24+ and Ninja are included with Visual Studio's CMake
  component; `-CMake` and `-Ninja` select independent installations.
- Remill **v6.0.1** headers, commit
  `0e324aee8c67a63ec759ef379dcfafa0b3cb1448`, and Vulkan-Headers **v1.4.321**.
  Download their source from the official repositories linked in
  `host-dependencies.json`, then supply their `include` directories. No Remill
  library, lifter, Vulkan SDK tools or shader compilation is needed. All 25
  consumed third-party headers are hash-checked before compilation. The Remill
  CMake patch in this repository does not change those headers.
- An original supported MW3 U.S. retail 1.2 installation. Its `Mech3.exe` identity
  is verified before building; original files are read-only inputs.
- A locally available, previously generated native runtime containing
  `runtime.json` and `bin/MW3Translated.dll`, for example the runtime in an
  authorized installed playtest. This DLL remains outside Git. The host and DLL
  are separate pieces: this command builds the host and requires the existing
  translated DLL to link its native seam. Generating that DLL from original media
  remains the separate native-preparation workflow and is outside issue #25.

The existing translated DLL and runtime support files are checked against the
supplied runtime's manifest. LLVM reads symbol metadata from that DLL to generate
`translated.def`, `translated.lib` and `host.def` in the output directory. The DLL
is copied unchanged; no translated `.obj` files are needed or regenerated.

The first local build used clang-cl 21.1.8, MSVC headers/libraries 14.51.36231
and the installed Windows SDK. Build receipts record actual tool fingerprints.
An independent physical-PC build remains an acceptance check, not a claim made
by having these files available.

## One build command

From a clean checkout, with the dependencies above installed:

```powershell
pwsh -File tools/m4-crt-heap-carry/build_host.ps1 `
  -GameDirectory 'C:/Games/MechWarrior 3' `
  -RuntimeDirectory 'C:/Games/Core Critical/Launcher/Runtime' `
  -RemillInclude 'C:/Dev/remill-6.0.1/include' `
  -VulkanInclude 'C:/Dev/Vulkan-Headers-1.4.321/include' `
  -LLVMDirectory 'C:/Dev/LLVM-21.1.8/bin' `
  -OutputDirectory 'C:/Dev/MW3-host-build' -Release
```

Use a fresh output directory. Omit `-Release` while editing host source locally;
the development receipt records modified host files and dirty checkout state.
`-Release` requires a clean checkout matching `host-source-manifest.json`.
The output contains `entry_commandline.exe`, the unchanged DLL/support files,
seven newly compiled host objects, logs, regenerated import/export definitions
and `source-snapshot.json`. No signing credential is needed for a developer build.
Release Windows signing is a separate existing release step.

The historical object-based build in `native/CMakeLists.txt` remains available
for its dated research users. The wrapper selects `MW34_HOST_ONLY=ON`, whose
`host-only.cmake` has no translated-object or private-report dependencies.

## Source decisions and maintenance

`host-source-manifest.json` records every canonical file, its size, SHA-256,
classification and decision. `host-dependencies.json` pins consumed external
headers. The owner approved committing the reviewed interoperability metadata
on October 27, 2026; see [the scoped distribution decision](../../../docs/legal.md).

| File family | Decision and provenance |
| --- | --- |
| Host C++ adapters, platform services, graphics/input/audio code | Commit the complete authored patched source used by runtime 1.0.44 |
| `additional_skin_picker.hpp`, `platform_trace_stage.inc` | Commit authored UI/diagnostic source; these are not missing proprietary instruction bodies |
| `mfc_entries.inc`, `mfc_routers.inc` | Commit reviewed address/symbol declarations and routing metadata. Historical producer: `gen_mfc_dispatch.py` from pinned lift reports. These files contain no lifted instruction bodies |
| `override_*roster*.inc`, `override_arm_damage_plans.inc`, `override_bushwacker_lod1.inc` | Commit reviewed mesh-name/count/attachment lookup metadata. Preserve the shipped snapshot; the prior ad hoc authoring recipe is not a build dependency |
| `c1_material_fixtures.inc` through `c4_material_fixtures.inc`, `t1_material_fixtures.inc` | Commit reviewed material-name/hash and authored lighting/UV-region metadata; no texture pixels |
| `spec.hpp` | Commit reviewed admission range/size/hash metadata previously generated into an ignored report directory; no original instruction bytes |
| `body_dispatch.hpp` | Commit authored dispatch classification; historical generator `tools/remaster-launcher/apply_body_dispatch.py` |
| Authored GLSL and compiled `*_vert.h` / `*_frag.h` | Commit matching source and compiled shader arrays. The arrays are compiled project shaders. Existing shader scripts remain authoring tools, not an ordered host-build prerequisite |
| `audio/local_cd_audio.hpp`, `graphics/menu_version.hpp`, `memory/guest_memory.hpp` | Commit and recursively fingerprint these previously omitted nested host dependencies |
| `MW3Translated.dll`, translated `.obj` files, native preparation buffers, original EXE/provider files and original assets | Remain local; original game instructions/assets are not added to Git |

Treat `host/` as the canonical compiled implementation. A host fix must update
that source and its manifest in the same PR, then be built/tested through this
command. The older `native-overrides/` files remain historical patch inputs;
editing one alone does not change the maintained host. When migrating an older
PR such as #14, apply its reviewed behavioral change to the canonical host and
run its focused tests; do not assume two different file copies are synchronized.

Preserve exact source bytes through the host-specific `.gitattributes` rule.
Deliberate formatting or code edits require refreshed manifest pins and a new
review/build; never rewrite historical release receipts to match a later edit.

## Validation and release integration

Run `python tools/m4-crt-heap-carry/test_host_build.py` for authored seam parser
and per-file coverage checks. A real build must additionally:

1. Start from a fresh clone at the reviewed commit, at a different absolute path,
   using only the explicit install/runtime/dependency/tool inputs above.
2. Build with `-Release`. Compare `source-snapshot.json.host_source_pins` with
   the committed manifest. Compare the recorded repository dependency hashes as
   well; nested and external-to-`host/` project headers are part of the closure.
3. Verify `translated_module_unchanged: true`, `generation_required: false`,
   `translated_object_inputs: 0`, and the original DLL hash before/after.
4. Validate startup/menu and the changed host behavior in an isolated launcher
   runtime, preserving the player's installation. A successful compile is not
   a force-feedback hardware test or a complete gameplay fidelity claim.
5. Repeat on a second physical Windows machine. Retain its tool versions,
   logs, source fingerprints and result; this remains required before closing
   the independent-machine acceptance criterion.

For the next native release, build the host from merged `main` using this command
and retain its receipt. Copy the built host into runtime staging, sign it, refresh
the runtime's executable/file pins, and copy the build's complete
`host_source_pins`, `repository_source_pins` and tool/dependency provenance into
`metadata/source-snapshot.json`. Signing changes binary bytes, not source hashes;
record pre/post-signing executable hashes separately. Compare staged metadata to
the build receipt and fail publication on a mismatch. Keep the existing native
DLL unchanged for host-only fixes. Never reconstruct a release from a local
patched host folder or silently include unrelated working-tree edits.

The fingerprints establish the source used by a build. Authenticode timestamps,
compiler/SDK versions and debug paths can change executable bytes; this work
does not promise byte-identical signed EXEs across machines.
