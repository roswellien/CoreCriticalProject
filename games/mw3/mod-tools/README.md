# MW3 mod tools

Home for MechWarrior 3 modding tools built on the native recompilation (`MW34Recomp`).

| Component / Document | Status | Description |
| --- | --- | --- |
| [Map & mission editor](editor/) | **Working Slice (Phase 1/2)**, 2026-10-20 | Interactive 2D top-down map editor with selection, move, undo/redo, and isolated mod export |
| [Format Support Matrix](docs/format-support-matrix.md) | **Documented & Tested**, 2026-10-20 | Binary format specifications for ZBD, ZRD, GameZ, and explicit labeling of unresolved fields |
| [Map and mission editor plan](map-mission-editor-plan.md) | Architectural roadmap, 2026-10-17 | Long-term staged plan from viewer to full mission scripting and terrain sculpting |

## Quick Start: Launching the Editor

Launch the editor using the root shortcut:
```cmd
Play MW3 - Mission Editor.cmd
```
or via Python directly:
```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" games/mw3/mod-tools/run_editor.py --operation c1 --mission c1m1
```

## Running the Automated Test Suite

The browser-based 3D Map Studio is an additional prototype, launched with
`Play MW3 - Visual Map Studio.cmd`. Its HTTP/export checks are in
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
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" games/mw3/mod-tools/tests/test_editor_slice.py
```

## Ground rules for every mod tool

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
