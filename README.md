# MW34 RECOMP

MW34 RECOMP is an open-source research project exploring native static
recompilation of the original MechWarrior games. **MechWarrior 3 is the only
current implementation target.** The goal is to translate original 32-bit x86
game logic into a modern native executable while preserving gameplay and using
the user's own legally obtained game data.

This repository contains the engineering foundation and verified native x64
game initializer and provider components. A full recompiled game executable
is not available yet. The installed U.S. MW3 1.2 executable is admitted by exact
identity as `mw3-us-1-2-retail`. Pirate's Moon and the three MW4 titles are future
targets.

The installed MW4 Mercenaries has a [reconnaissance report](docs/mw4-reconnaissance.md)
and [execution plan](docs/mw4-execution-plan.md). Its protected code-image recovery
is the first implementation gate; this assessment adds no MW4 compatibility claim.

## What works now

- CMake/C++20 static runtime library with explicit 32-bit guest addresses,
  checked memory mappings, permissions, and little-endian scalar access.
- Python tools for SHA-256 identity validation and bounded PE32/i386 metadata
  analysis: headers, sections, imports, exports, relocation summary, executable
  regions, entry-point seeds, and a static-import API dependency report.
- A wrapper for optional local LLVM disassembly. Function boundaries and
  instruction semantics still require analysis.
- Automated tests using project-authored fixtures, compiler warnings, formatting
  configuration, optional static analysis, and Windows/MSVC + Linux/Clang CI.
- Architecture, evidence standards, framework research and an incremental plan.
- [First native MW3 function proof](docs/mw3-leaf-experiment.md): 16,609 original
  x86 inputs matched generated native x64 at O0/O2, with zero mismatches and
  49 rejection controls.
- [Connected native startup research](docs/m4-progress-startup131.md): 131 of 144
  selected initializer roots accepted, including 101 callback registrations,
  68 MFC owners, 19 duplicated strings, four formatter owners, normal FS records,
  Lockit association, a finite compound-cosine root and independently verified
  persistent source/provider, growth/cleanup and paired comparisons, plus the
  MFC current-thread/codepage initializer and all 24 connected fault cases.
  [Current milestones](docs/project-milestones-r13.md).
- [Active native work](docs/m4-active-native-lanes-2026-10-10.md): numeric
  execution and source comparisons, MFC resource tests, and the next widget
  and chronological startup captures, with accepted and pending work tracked separately.
- [Local live game diagnostics](tools/game-monitor/README.md): structured event
  timelines, incremental cursor/watch reads, debug messages and exceptions,
  hook/game logs, process metrics, exit codes and OS-reported window health.
- [Windowed Vulkan replay](docs/vulkan-windowed-replay.md): a project-built x64
  viewer redraws a saved Training scene, with tested presentation, resizing,
  minimize/restore and clean shutdown. Launch it with `Launch Vulkan Replay.cmd`.
  The saved viewpoint is fixed; native menus and playable Training remain open.

## Build and test

Requirements: CMake 3.24+, a C++20 compiler (MSVC or Clang recommended), and
Python 3.11+. The bootstrap uses no third-party runtime or Python libraries and
does not need any game files to build or test.

```sh
cmake --preset default
cmake --build --preset default
ctest --preset default
```

On Windows, install Visual Studio's Desktop development with C++ workload and
use its developer shell if CMake is not on PATH. For Visual Studio generators,
add `-A x64` to the configure command. On Linux with Clang:

```sh
cmake --preset default -DCMAKE_CXX_COMPILER=clang++
```

Configure a separate build directory when changing compilers or generators.
Tests can also be run directly:

```sh
python -m unittest discover -s tests -p test_binary_tools.py -v
```

When clang-format is available, `cmake --build build/default --target format-check`
checks C++ formatting and target `format` applies it. Optional clang-tidy
integration requires `-DMW34_ENABLE_CLANG_TIDY=ON` and Ninja or Makefiles.
See [contributing](CONTRIBUTING.md) and [dependencies](docs/dependencies.md).
The first session's actual results and limitations are recorded in
[bootstrap validation](docs/bootstrap-validation.md).

## Inspect a local executable

Keep original files outside the checkout or in ignored `local/`. The local
`MW3/` and `MW4/` media folders are also ignored. Do not commit proprietary input,
full disassembly, strings, memory dumps, or generated game translations.

```sh
python tools/analysis/analyze.py "local/mech3.exe" --output reports/mw3.json
python tools/binary-validator/validate.py "local/mech3.exe"
```

The analyzer labels an unrecognized hash `unknown_binary`. The validator returns
exit code 2 for an unknown identity. Add `--require-supported` to the analyzer
when a pipeline must stop on unrecognized input. Validation never trusts the
filename alone. Both tools read
files without executing them. See [the manifest specification](docs/supported-binaries.md).

Optional disassembly requires a separately installed `llvm-objdump`:

```sh
python tools/analysis/disassemble.py "local/mech3.exe" --output reports/mw3-disassembly.txt
```

Linear disassembly can decode inline data as instructions. It is a research aid,
not recovered function boundaries or a recompilation. Detailed limitations and
tool instructions are in [tools/analysis](tools/analysis/README.md).

The installed MW3 1.2 image now has a reviewed
[memory/API inventory](games/mw3/docs/api-dependencies.md) and a
[first-function contract](games/mw3/docs/first-function.md) for `sub_00409ED0`.
Its hash-bound slice has passed original-versus-native comparison. The extraction
tool accepts only this reviewed identity; proprietary inputs and generated code
remain local.

## Recompilation direction

Vulkan is the user-selected graphics backend target. The first standalone
[Vulkan learning prototype](docs/vulkan-learning-prototype.md) passes authored
GPU transfer/readback on Windows x64. The later
[windowed replay](docs/vulkan-windowed-replay.md) rasterizes and presents a saved
Training scene. Complete frame/sequence replay and live runtime integration
remain next steps.

The proposed pipeline is local binary validation, reviewed function/control-flow
analysis, offline instruction lifting, native compilation, and a project-authored
runtime. Guest pointers stay 32-bit; host pointers never replace guest fields.
Win32/COM/API bridges and explicit function replacement routing will preserve
the original ABI. Unsupported behavior must fail visibly.

The [framework evaluation](docs/recompilation-research.md) recommends a bounded
Remill experiment, with SRW/llasm as a comparison candidate. The
[authored fixture suite](docs/fixture-suite-experiment.md) passes 40,576 original
x86 cases against compiled native x64 at O0/O2, including branches, partial
registers, memory writes, shifts and stack cleanup, plus 135 rejection/bridge check entries.
The Remill pipeline also passes the isolated MW3 leaf comparison. Broader runtime
and floating-point behavior still need independent validation.

The [initial-phase execution plan](docs/initial-phase-plan.md) defines two tracks:
prove the lifting/reference harness on authored x86 fixtures, and select an
evidence-backed integer leaf function from the admitted MW3 executable. The
original installation and 1.2 patch are complete; exact identity validation and
strict metadata analysis passed. Provenance and version observations are in
[media observations](docs/media-inventory.md), with the admitted profile described
in [supported binaries](docs/supported-binaries.md). Both tracks meet at a
differential test of a real MW3 function against its native x64 translation.
The bounded MW3 Bootstrap initial phase is complete. The next phase validates
x87 behavior, calls and import bridges before expanding to a game subsystem.

## Project map

The [work-ahead asset backlog](docs/work-ahead-assets.md) defines parallel
preparation for textures, videos, normal maps, effects and related optional
modernization, with explicit integration gates.

| Path | Purpose |
| --- | --- |
| `docs/` | Architecture, roadmap, legal policy, research and evidence standards |
| `tools/` | Offline validation and analysis |
| `runtime/` | Guest memory and future API compatibility layers |
| `recomp/` | Translator integration, local generated output and shared patch contracts |
| `games/mw3/` | Exact binary profiles, symbols, authored patches and findings |
| `tests/` | Synthetic fixtures and runtime boundary tests |
| `cmake/` | Shared build configuration |

Start with [project goals and milestones](docs/project-milestones.md),
[the full initial-phase plan](docs/initial-phase-plan.md),
[architecture](docs/architecture.md), [roadmap](docs/roadmap.md),
[reverse-engineering workflow](docs/reverse-engineering.md), and
[MW3 findings](games/mw3/docs/findings.md).

## Distribution

Project-authored code is MIT licensed. Original game content is not included or
licensed by this project. Users supply their own legally obtained installation.
Read [the distribution policy](docs/legal.md) before contributing. Preserve
original behavior first; modernization is later, optional work.
