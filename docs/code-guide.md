# Finding your way around the code

The native game preserves original game logic through offline recompilation.
Project-authored host services connect that code to Windows and Vulkan. Guest
addresses remain 32-bit; host objects and handles belong to checked host registries.
Read the [architecture](architecture.md) and [modernization plan](faithful-modernization-plan.md)
before changing this boundary.

## Active components

| Component | Start here | Responsibility and review focus |
| --- | --- | --- |
| GUI launcher | `tools/mw3-remaster-launcher/Core/GameRunner.cs`, `Core/D7VkRunner.cs`, `MainWindow.xaml.cs` | Validate installation, select Python, prepare a session, apply settings, capture errors; separate UI from launch/profile decisions ([executable naming](core-critical-executable-naming.md), [stock baseline and packs](stock-baseline-and-community-packs-plan.md), [pack capabilities](content-pack-capabilities.md)) |
| Original-game compatibility launcher | `mw3_launcher.py` | Own the isolated D7VK profile, staged bank links, temporary current-user registry choices and original-process handles; this is separate from native recompilation |
| Native launch preparation | `tools/remaster-launcher/play_remaster.py`, `play_native.ps1` | Verify pinned host and registrations, prepare local data and start the host; make path ownership, schemas and failures understandable ([additional mech packs](additional-mech-packs.md), [authoring additional mechs](authoring-additional-mechs.md)) |
| Native application host | `tools/m4-crt-heap-carry/composition.cpp`, `mfc_stage.hpp` | Connect translated entry, initialization, ABI, callbacks and services; distinguish authored adapters from local generated game bodies ([MP4 cinematics plan](mp4-cinematic-playback-plan-2026-10-27.md)) |
| Enhanced renderer | `tools/remaster-launcher/native-overrides/`, `runtime/graphics/` | Surface/command lifetime, GPU scene transport, HUD, materials, lighting and capture; document format and state contracts at their boundaries ([GPU geometry plan](gpu-geometry-development-plan.md), [campaign lighting plan](campaign-lighting-progression-plan.md)) |
| Shared services | `runtime/memory/`, `runtime/mfc/`, `runtime/audio/` | Checked guest memory, receiver ownership and local music; retain cleanup and error behavior |
| Desktop Mod Editor | `games/mw3/mod-tools/run_editor.py`, `editor/core/`, `editor/ui/` | Read original archives, represent edit deltas, undo/redo and local export; keep source installation read-only |
| Browser Map Studio | `games/mw3/mod-tools/run_studio.py`, `editor/web/static/js/studio.js` | Loopback preview and prototype pack APIs; validate request input and separate preview from accepted gameplay |
| Binary analysis and lifting | `tools/analysis/`, `tools/binary-validator/`, `tools/lifting/` | Exact identity ([supported binaries](supported-binaries.md)), PE parsing ([reverse-engineering workflow](reverse-engineering.md)) and pinned offline compilation ([recompilation research](recompilation-research.md)); generated translations remain local |
| Authored regression fixtures | `tests/`, `tools/mw3-remaster-launcher-tests/`, focused `test_*` files | Exercise contracts and rejection paths without proprietary data where possible |

`tools/m4-*/` and `tools/x87-*/` also contain dated source models, comparers and
acceptance work. Their names and source hashes may be pinned by evidence. Dated
session summaries, handoffs, superseded plan revisions and one-off investigations
live in `docs/archive/`. A
historical interpreter used to measure a contract is not a production fallback.
Do not delete, rename or format these files as general cleanup. Extract reusable
active code into reviewed modules without silently replacing frozen inputs.

## How code should explain itself

The launch boundary has three owners. `GameRunner.CreateLaunchProfile` copies
the published profile and applies UI choices. `play_remaster.plan` reads profiles,
registrations and capability pins; it returns data without launching.
`play_remaster.main` owns preparation and starts the selected backend.
`native_assets.prepare` writes local sidecars and returns their environment
bindings. This order is intentional: do not start the host with partially prepared
files or silently change a requested backend after validation fails.

The desktop editor has three different kinds of state: `MissionData` is the live
mutable scene plus unedited extraction paths, `ModProject` stores serialized
deltas keyed by source indices/names, and `CommandHistory` stores reversible
actions against live objects. A redraw is not a project save. Document and test
how changes travel between these owners, especially after selection changes or
failed mission loading. See the component README's maintenance map.

Binary transport names identify contracts, not general-purpose archive formats:

| Format | Writer / reader entry | Meaning |
| --- | --- | --- |
| `MWBANK1` | `native_assets.prepare`, editor `build_bank_file` / native bank routing | Relative game archive keys mapped to absolute local source paths |
| `BWTEX1` | `native_assets.material_pixels` and `prepare` / model material loader | RGB565 albedo images and a batch-to-image index list |
| `BWNRM2` | `normal_materials.pack_normals` / `runtime/graphics/material_normals.hpp` | Explicit per-batch normal bindings and linear RGBA pixel identities |
| `BWSNR2` | `normal_materials.pack_surface_bindings` / material-normal loader | Full source-surface identity keys followed by a `BWNRM2` payload |
| `MW3CD1` | `local_music.prepare_music` / `runtime/audio/local_cd_audio.hpp` | Local decoded WAV tracks, sample-frame counts and UTF-8 paths |

Field widths/byte order, image orientation and count limits must agree at both
ends. Runtime comments explain owned buffers, callback threads and guest/host
pointer distinctions. A format hash is not automatically a rights or trust check.

- Give each maintained module a short purpose and its main entry points. State
  required inputs, produced outputs and where local files may be written.
- Use names that describe proven behavior. Retain guest VA/RVA distinctions,
  `sub_XXXXXXXX` names and provenance where semantics remain unresolved.
- Explain units, ownership, resource lifetime, binary layout, bounds and unusual
  ABI/FP behavior near the code that enforces them. Link the relevant contract.
- Prefer named helpers and normal formatting over dense one-line statements.
  Keep validation visible; unknown required services must fail explicitly.
- Keep UI, configuration, asset preparation and process execution separate.
  Take paths/configuration as inputs rather than adding another workstation path.
- Review duplicated code by provenance before consolidating it: two frozen
  evidence versions are not necessarily redundant runtime implementations.
- Add a meaningful regression for behavior changes. Readability-only edits need
  a diff review and the existing narrow checks, rather than tests of comments.

## Review order and completion record

Review release-facing code first: setup and package manifests; launcher and pack
imports; Mod Tools and HTTP/file boundaries; native services and initialization;
graphics/audio/input; lifter/analysis tools; historical evidence tooling last.

For each reviewed directory record the inspected revision/files, concrete issues,
changes, test results and remaining limits. Inventory/pattern scans do not count
as a line-by-line review. The October 21 initial audit found portable setup gaps,
an inconsistent binary identity, prototype Studio input risks and a CI compile
failure. The [code/provenance review](archive/code-provenance-review-2026-10-21.md) records
the subsequent reproduced defects, provenance dispositions and remaining coverage.
Full source review is still open in [release readiness](public-release-readiness.md).

The local readability pass expands maintained Python control flow, documents
launch/asset/music/editor ownership, gives launcher Core types and operations XML
summaries, and explains shared memory/MFC/audio lifetimes at their interfaces.
It preserves the historical M4/x87 sources and source-overlay snapshots instead
of silently changing their evidence hashes. This is source cleanup, not closure
of the separately recorded functional defects or a whole-host semantic review.
