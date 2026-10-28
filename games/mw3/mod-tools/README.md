# MW3 mod tools

Home for MechWarrior 3 modding tools built on the native recompilation (`MW34Recomp`).

| Component / Document | Status | Description |
| --- | --- | --- |
| [Map & mission editor](editor/) | **Working Slice (Phase 1/2)**, 2026-10-20 | Interactive 2D top-down map editor with selection, move, undo/redo, and isolated mod export |
| [Format Support Matrix](docs/format-support-matrix.md) | **Documented & Tested**, 2026-10-20 | Binary format specifications for ZBD, ZRD, GameZ, and explicit labeling of unresolved fields |
| [Map and mission editor plan](map-mission-editor-plan.md) | Architectural roadmap, 2026-10-17 | Long-term staged plan from viewer to full mission scripting and terrain sculpting |

## Quick Start: Launching the Editor

For a separate source-preview installation, follow
[Mod Tools setup](../../../docs/setup-mod-tools.md). `launchers\Setup Mod Tools.cmd` at the
package root selects your own game and Mech3AX folders and creates an isolated
Python environment. Preview geometry and exported game-derived archives remain
local; see the setup guide for Studio's additional prerequisites.

Launch the editor using the launcher shortcut:
```cmd
launchers\Play MW3 - Mission Editor.cmd
```
or via Python directly:
```powershell
& ".venv-mod-tools/Scripts/python.exe" games/mw3/mod-tools/run_editor.py --operation c1 --mission c1m1
```

## Running the Automated Test Suite

The browser-based 3D Map Studio is an additional prototype, launched with
`launchers\Play MW3 - Visual Map Studio.cmd`. Its HTTP/export checks are in
`tests/test_studio_server.py`. Editing and export tests do not establish that a
custom mission plays correctly in the native game.

The preview's `editor/web/static/assets/game_assets_3d.json` contains extracted
original geometry and is local-only. Generate it from your own installation
with `editor/core/extract_assets_3d.py` after preparing the local archive tools;
it is intentionally excluded from the repository. The bundled browser renderer
is Three.js r128; its MIT license and exact upstream identities are in
`editor/web/static/js/THREE-LICENSE.txt` and `third-party.json`.

Run the full verification suite covering format round-trips, mission discovery, undo/redo, project serialization, and isolated mod export:
```powershell
& ".venv-mod-tools/Scripts/python.exe" games/mw3/mod-tools/tests/test_editor_slice.py
```

## Ground rules for every mod tool

### Source maintenance map

| Component | Owns | Important boundary |
| --- | --- | --- |
| `editor/config.py` | Installation/tool paths and a writable cache root | The user's game directory is input, not workspace storage |
| `editor/core/formats.py` | Converter subprocesses and temporary ZIPs | Converter success does not prove unchanged round-trip identity |
| `editor/core/mission_loader.py` | Loaded scene and unedited extraction paths | Node indices belong to that exact source archive |
| `editor/core/project.py` | Serialized deltas and reversible commands | History, live objects and persisted deltas are separate state |
| `editor/ui/main_window.py` | Selection, commands and save/export orchestration | UI refresh must record the object actually changed |
| `editor/core/exporter.py` | Temporary edit copies and local export files | Output is incremental and game-derived; export does not grant distribution rights |
| `editor/core/map_pack.py` | Prototype overrides of an existing operation | Browser terrain/health/faction previews are not all applied to game data |
| `run_studio.py` | Loopback HTTP, export requests and process start | Host/Origin/body/path checks precede mutations; process start is not successful game loading |

Placements use the source world's coordinate units. Object `rot_y` is radians;
the inspector exposes `yaw_degrees`. Spawn headings are degrees. Transform
extraction uses row-major matrices acting on column vectors, with parent/local
composition; changing this convention changes placements even if a preview looks
plausible. The original node hierarchy/unknown fields remain relevant on export.

Keep these responsibilities separate when making repairs. The known undo/save,
failed-load, source-cache and export/run defects remain tracked in the
[code review](../../../docs/archive/code-provenance-review-2026-10-21.md); the comments
describe the current implementation and do not mark those defects fixed.

The browser's `editor/web/static/js/studio.js` has a different state model from
the desktop command history. `state.project` is JSON-compatible requested data;
`assetObjectMap` owns Three.js display groups keyed by `asset_id`. A mesh child
is not itself a project entity. Selection changes the inspector/transform gizmo;
placing or dragging changes project coordinates and refreshes the view.
`syncSceneAssets` updates transforms on existing groups; it is not a complete
geometry/material rebuild or GPU-resource disposer. The history fields in the
browser state do not implement complete undo/redo.

Optional extracted geometry loads asynchronously after viewport initialization.
Procedural shapes keep the preview usable while it loads or when the catalog is
absent. Preview Y coordinates snap to the browser terrain function; export still
uses the selected original operation terrain. `yaw_deg` crosses the JSON boundary
in degrees and is converted to radians only for Three.js display rotation.

Export posts the current project snapshot to `/api/export-pack`; launch posts
only its ID to `/api/launch-map`, which starts an existing exported launcher.
Launching does not implicitly export later edits. Server success means files
were written or a process was started, not that a mission loaded successfully.
Maintain the server's request/path validation alongside client-side UI changes.

- **Original game logic runs the mods.** Mods change game data that the
  recompiled MW3 engine already loads (missions, maps, objects, textures,
  lighting). They do not replace the game with a remake or a new engine.
- **The user's installation is never modified.** Tools read the user's own
  legally obtained game files and write mods to a separate folder. The native
  host loads a mod as an overlay at launch; removing the mod restores the
  original game exactly.
- **No original content is distributed.** Following [docs/legal.md](../../../docs/legal.md),
  tools, documentation and format descriptions are project-authored. Original
  files, extracted assets, and derived replacements are never committed or
  shipped. A shareable mod carries only its own authored content plus
  references to original assets by name and hash.
- **Every format change is round-trip tested.** Reading and then writing an
  unmodified file must reproduce it byte-for-byte before any editing is allowed.
- **Mod support stays optional.** With no mod loaded, the game must render and
  behave exactly as without mod support (same draw records and captures).

## Existing pieces that are already mod-like

- Per-map lighting presets: [`tools/remaster-launcher/sun-presets.json`](../../../tools/remaster-launcher/sun-presets.json)
  (sun, ambient, sky and haze per map).
- Replacement mech models and texture packs used by the Remaster launchers.
- The Big Lake private test instance pattern (separate game copy, pilot and
  registry per experiment).
