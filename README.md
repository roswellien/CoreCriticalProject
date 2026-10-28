# MechWarrior 3 Recomp

**Original gameplay. A modern core.**

An experimental native recompilation of MechWarrior 3, with Vulkan rendering,
modern Windows services, an optional enhanced visual profile, and developing
map and mission editing tools. The aim is to preserve the original game's
logic and behavior while making it usable on modern systems.

[![MechWarrior 3 Recomp announcement trailer — in-game development footage](docs/media/announcement-trailer.jpg)](https://www.youtube.com/watch?v=2olchoLkZro)

**[Watch the announcement trailer](https://www.youtube.com/watch?v=2olchoLkZro)**
· [Development videos](https://www.youtube.com/channel/UC0YGz5FEh7-ij1miUmXECiw/videos)
· [Screenshots and media](docs/media/README.md)
· [Setup](docs/setup-game.md)
· [Known playtest issues](docs/known-issues.md)
· [Mod Tools](#mod-tools)
· [Contributing](CONTRIBUTING.md)
· [GitHub PR workflow](docs/github-workflow.md)

> **In development.** A playable portable release is being prepared and is not
> available yet. A source checkout builds the asset-free runtime and tests, but
> does not by itself build or run the complete game. You must supply your own
> legally obtained original installation. No original game or replacement asset
> pack is included.

## What the project does

The native host executes recompiled original 32-bit game logic in a project-built
64-bit application. Project-authored services handle graphics, input, audio,
files and Windows integration. Vulkan is the selected graphics backend.
Modernization preserves original gameplay; visual and behavioral enhancements
need separate configuration and comparison against original-compatible behavior.

The local development build has run startup, the animated menu, Training,
Instant Action and selected campaign play, including normal shutdown. The
October 20 work added launcher repairs, all 18 chassis in the enhanced profile,
32-bit depth rendering, and fixes for objectives input and damage-display colors.
A player confirmed the reported Operation 1 → Operation 2 transition repair.
These observations do not establish complete campaign compatibility or fidelity.

| Area | Current development capabilities | Remaining work |
| --- | --- | --- |
| Native gameplay | Live menu, Training, Instant Action, selected campaign play and original HUD | Broader campaign, saves, physics/AI/timing comparisons and sustained playtests |
| Vulkan graphics | Ultrawide output, window modes, FXAA, anisotropic filtering, SSAA and improved depth precision | Broader hardware coverage, performance and visual regressions |
| Enhanced visuals | Optional updated models, textures, material normals and environment lighting in local profiles | Asset distribution review, damage/LOD/muzzle checks and remaining lighting effects |
| Launcher | Installation validation, graphics choices, model selection and local preparation | Portable runtime import/build and first-run installation |
| Mod Tools | Top-down editor and browser Map Studio prototypes with project save/edit/export paths | Portable setup, input hardening and native custom-mission validation |
| Pirate's Moon | Experimental native startup/menu/Options/quit slice | Missions, cinematics and broader input/play validation |

The separately maintained **D7VK compatibility track** runs the original 32-bit
executable through a Vulkan wrapper. It is a distinct launch option, not the
native host or a fallback inside it. See [wrapper status](docs/d7vk-wrapper-launcher-summary.md).
MW4 remains a later target.

## In-game development

| Mad Cat — Grasslands at sunrise | Cauldron-Born — Gorge at sunrise |
| --- | --- |
| ![Mad Cat rendered in the native development build](docs/media/mad-cat-grasslands.jpg) | ![Cauldron-Born rendered in the native development build](docs/media/cauldron-born-gorge.jpg) |

These October 19 trailer captures show the optional enhanced profile with
replacement visuals and a filming camera. They are real development footage,
not a promise that those assets are included in a download. The
[media page](docs/media/README.md) explains capture scope and links the evolution videos.

## Downloads and user setup

Two separate packages are being prepared:

- **Game / Launcher for Windows x64:** import the user's supported original
  installation, prepare the required runtime locally and launch through the GUI.
  Portable setup and distribution review are still open. Follow
  [game setup and current limits](docs/setup-game.md).
- **Mod Tools source preview:** a separate editor package with its own setup
  instructions and dependency checks. It reads the user's own archives and
  keeps extracted caches and exports local. See [Mod Tools setup](docs/setup-mod-tools.md).

Do not treat an existing development shortcut or the current Inno installer
script as a self-contained playable release. The release preparation record is
[here](docs/public-release-readiness.md).

## Mod Tools

The [Mod Tools](games/mw3/mod-tools/README.md) are a separate workstream and will
have a separate download/setup path from the Game / Launcher.

- **Map & Mission Editor:** a desktop top-down view with object selection,
  movement, property editing, undo/redo, saved projects and isolated local export.
- **Visual Map Studio:** a browser-based 3D preview and placement prototype with
  lighting controls and experimental map-pack generation.
- **Format documentation:** recovered archive structures and a
  [support matrix](games/mw3/mod-tools/docs/format-support-matrix.md) that identifies
  unresolved fields.

Editing or exporting a project does not establish that its custom mission plays
correctly. Original preview geometry is extracted locally; it is not bundled.
Exported archives may contain original-derived material and are not automatically
shareable community packs. See [setup](docs/setup-mod-tools.md) and the
[distribution policy](docs/legal.md).

![Visual Map Studio prototype with the local demo scene, asset palette and environment inspector](docs/media/mod-tools-studio.jpg)

The current browser prototype, captured October 21. This local workspace has
extracted preview assets; the separate source package does not include them.

## Build the asset-free runtime

The bootstrap needs CMake 3.24+, a C++20 compiler and Python 3.11+. It builds
project-authored runtime components and tests without installing or downloading
game content. This is separate from building the integrated game host.

```sh
cmake --preset default
cmake --build --preset default
ctest --preset default
```

On Windows, use Visual Studio's C++ developer shell and add `-A x64` to the
configure command when using its generator. With Clang on Linux:

```sh
cmake --preset default -DCMAKE_CXX_COMPILER=clang++
```

Use a separate build directory when changing compilers. See
[contributing](CONTRIBUTING.md), [dependencies](docs/dependencies.md) and the
[native-host build notes](tools/m4-crt-heap-carry/README.md) for their distinct scopes.

## Help develop and test

Read the [October 21 development update](docs/archive/development-update-2026-10-21.md)
for the current presentation, setup and source-readability work.

Read the [contribution guide](CONTRIBUTING.md) and [code guide](docs/code-guide.md)
to find the maintained entry points. Useful contributions include reproducible
bug reports, focused contract tests, readable host-service code, documentation,
hardware playtesting and editor improvements. Never attach original media, memory
dumps, private logs or generated game translations to public issues.

| Reference | Purpose |
| --- | --- |
| [Roadmap](docs/roadmap.md) | Development direction and remaining validation |
| [Faithful modernization plan](docs/faithful-modernization-plan.md) | Original behavior, native execution and modernization contracts |
| [Latest recorded daily update](docs/mechlab/2026-10-20.md) | October 20 changes and their limits |
| [Architecture](docs/architecture.md) | Guest ABI, runtime and graphics boundaries |
| [Milestones](docs/project-milestones.md) | Evidence and formal acceptance criteria |
| [First native function proof](docs/archive/mw3-leaf-experiment.md) | A bounded original/native comparison |

Track progress through demonstrated native functionality, fidelity/compatibility
coverage, known defects and release validation; see the
[status reporting rule](docs/project-status-reporting.md). The paused startup
equivalence audit remains historical evidence. Live execution, optional enhanced
visuals, saved replay and original-process diagnostics have different scopes.

## License and original content

Project-authored contributions use the [MIT license](LICENSE). Third-party tools,
fonts and libraries retain their own licenses. MechWarrior and original game
content belong to their respective rights holders; no affiliation or endorsement
is implied. This project supplies no game installation, media, music, generated
game code or derived replacement pack. Read [the distribution policy](docs/legal.md)
before contributing or preparing a release.
