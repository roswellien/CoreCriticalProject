# MW3 map and mission editor — plan

Status: **plan only** (2026-10-17). No editor code exists yet. This document
records what is already known, what must exist before an editor is practical,
and a staged path from a read-only viewer to new maps and missions.

Editor work is a separate track from the native acceptance lane (131/144). It
grants no acceptance credit and must not change the game when no mod is loaded.

## 1. Goal

A desktop tool that lets a player:

1. **Edit missions:** objectives, player and enemy 'Mechs and loadouts, lances
   and spawn points, nav points, AI behaviour, triggers, briefings and timers.
2. **Edit maps:** place, move and remove buildings and props from the game's
   own object library; later, edit terrain height and surface textures.
3. **Create new content:** new Instant Action maps, new missions and
   eventually new operations, packaged as a **mod** that the recompiled game
   loads without touching the original installation.

Lighting already has per-map presets (sun direction and height, colours, sky
glow, haze, shadows). A map's lighting becomes part of the map in the editor.

## 2. What we know today

### Where MW3 keeps maps and missions

Each operation has a folder under the installed `zbd/` directory: `c1`, `c2`,
`c3`, `c4`, `c4b` (campaign operations) and `t1` (training). Each contains:

| File | Contents (current understanding) |
| --- | --- |
| `gamez.zbd` | The operation's world: texture references, materials, meshes and the scene node tree. |
| `anim.zbd` | Pre-baked animation definitions, also present in reader data (probably for load speed). |
| `reader.zbd`, `readerm1..m4.zbd` | Game data for the operation and its campaign missions (actors, regions, mission-specific names). |
| `readeria1..3.zbd` | Instant Action variants. |
| `readermp1..2.zbd` | Multiplayer variants. |
| `texture*.zbd`, `rtexture*.zbd` | Texture banks used by the world and by reader-named objects. |

Shared data lives in `zbd/` itself: `mechlib.zbd` ('Mech models and
materials), `motion.zbd` ('Mech animation), `interp.zbd` (small scripts that
decide which files the engine loads), `reader.zbd` (global data, including
cinematic script references) and the image and sound archives.

### Existing tools and evidence

- **mech3ax 0.7.0-rc3** (local, `local/tools/`) converts `reader*.zbd`,
  `gamez.zbd`, `anim.zbd`, `interp.zbd`, `mechlib.zbd`, `motion.zbd`, and the
  image and sound archives to JSON/PNG and back. Its authors state these
  conversions are byte-exact. Its `gamez` output is described as still rough,
  and its output formats are explicitly not yet stable. Licence: EUPL-1.2.
- **Project parsers:** `tools/m4-assets` reads the reader archive footer and
  0x94-byte directory; the original engine's reader object and lookup routines
  are mapped (`docs/m4-reader-bridge-research-r1.md`).
- **Texture work:** reader and GameZ names were cross-referenced to textures
  for Training (`docs/work-ahead-training-textures.md`); exact
  geometry-to-material bindings remain partly open.
- **Native host:** the recompiled game runs Instant Action and campaign
  missions on the Vulkan renderer, which already captures world geometry, the
  sky dome, cameras and replacement models. Scripted bounded runs, captures and
  draw-record comparisons give a repeatable test loop.

### Main unknowns

- The **meaning** of reader data: which records define objectives, spawns,
  AI orders, triggers, nav points and win/lose conditions, and how they refer
  to GameZ nodes.
- How **terrain** is represented (mesh vs height field), and how collision,
  line of sight and AI navigation are derived from it.
- How a new map or mission is **registered** in menus, Instant Action lists
  and campaign flow (`interp.zbd` and global reader data are the likely places).
- Whether `anim.zbd` must be regenerated whenever reader animation data changes.
- How the game caches or validates data (sizes, counts, checksums) and what
  breaks when objects are added rather than moved.

## 3. Prerequisites (build these first)

These are the "few things first". Each one is useful on its own and lowers
the risk of the editor.

### P1. Format documentation and schemas

Write project-authored descriptions of `reader`, `gamez`, `anim` and `interp`
data. Each record type needs fields, types, references between files, and
confidence and evidence. Start from mech3ax output and the engine's own
parsing code (recompiled functions and Ghidra), and confirm meanings by
observing the running game. Deliverable: a schema document plus a
machine-readable schema that the editor validates against.

### P2. Our own round-trip library

A project-owned C++ (or Python, for prototyping) library that reads and
writes the formats with byte-exact round trips on every file in a v1.2
install, with tests that use synthetic fixtures (no game files in CI).

Decision needed: use **mech3ax** as an optional external converter (never
vendored or linked into project code, because EUPL-1.2 is copyleft), or write
independent parsers from our own documentation. Recommendation: use mech3ax
only as a cross-check oracle during research, and keep the editor's format
layer independent.

### P3. Mod overlay loading in the native host

The host already mediates every file and reader access the game makes. Add an
optional overlay: when a mod is active, files and reader entries from the mod
take precedence over the original installation, and everything else falls
through to the original. Requirements:

- **Mod manifest:** id, version, target game build and hashes, list of
  replaced or added files and entries, dependencies.
- **Off means off:** with no mod active, frames and draw records are
  byte-identical to today.
- **Visible failures:** loading fails with a clear message if hashes don't
  match or a required file is missing; no silent fallback.
- **Selection:** the launcher picks the mod, separately from game settings.

### P4. Mission catalogue and quick-launch

- **Catalogue:** a generated, human-readable catalogue of every operation,
  mission and Instant Action map, with its files, objects, 'Mechs and
  objectives as currently understood.
- **Quick-launch:** start a chosen mission or IA map in a private game
  instance with a scripted input route, bounded frames and captures. This is
  the editor's "play test" button and its regression test.

### P5. Runtime introspection

Read live mission state from the recompiled game: object positions, AI
targets, trigger state, objective completion. This confirms what reader
fields mean (change a value, observe the effect) and later gives the editor a
live overlay.

### P6. Editor viewport rendering

Decide how the editor draws the world: reuse the project's Vulkan renderer
pieces (GPU world geometry, sun, shadows, sky) in a standalone viewer, or
render through the running game with a free camera. Recommendation: a
standalone viewer that reuses the renderer code, so editing never depends on
running the game.

## 4. Editor architecture (proposed)

- **Format layer (P2):** loads an operation's files into typed records and
  writes them back.
- **Document model:** one editable "map project" per operation and mission,
  including undo/redo, validation and references between objects.
- **Viewport:** world rendering with free camera, selection, gizmos for
  move/rotate, nav and spawn markers, trigger volumes, terrain overlays.
- **Panels:** object library (from the operation's GameZ and mechlib), mission
  properties, lances and 'Mechs, objectives, triggers and timers, lighting
  preset.
- **Validation:** schema checks, missing references, unreachable objectives,
  AI paths that leave the map, budget limits (object counts, texture memory).
- **Export:** writes a mod folder with manifest (P3), never the installation.
- **Play test:** quick-launch (P4) into the edited mission with the mod active.

UI technology is open (a native C++ app reusing the renderer, or a separate UI
layer talking to a C++ core). Decide after P1–P3 show what the core needs.

## 5. Phases

Each phase ends with something usable and a concrete exit check.

| Phase | Deliverable | Exit check |
| --- | --- | --- |
| 0. Inventory | Mission catalogue (P4) and first format notes (P1) | Every op/mission/IA map listed with its files; unknowns recorded |
| 1. Read-only viewer | Load an operation, render terrain and objects, show spawns and nav points | Viewer matches in-game captures of the same location |
| 2. Mission data edits | Change existing values only: enemy 'Mechs and loadouts, spawn positions, nav points, objective text, timers | "Hello world" mod: a different enemy lance on Big Lake IA, loaded through the overlay and verified in a bounded run |
| 3. Object placement | Move, add and remove buildings and props from the existing library | Added objects render, collide and are targetable; AI still functions |
| 4. Mission logic | Edit objectives, triggers and AI orders; add new missions to an existing operation | A new mission is selectable and completable |
| 5. Terrain | Height and surface texture editing | Collision, line of sight and AI movement correct on edited terrain |
| 6. New maps and operations | New IA maps and operations registered in menus | New map selectable from Instant Action with its own lighting preset |

Phases 2 and 3 depend on P1–P4. Phase 5 depends on solving the terrain and
navigation unknowns and is the highest-risk phase.

## 6. Toward general MOD tools

The same foundation (format library, overlay loading, manifests, quick-launch)
supports other tools later:

- 'Mech and variant editor (stats, loadouts, `mechlib`/reader data).
- Texture and model packs (formalising the existing replacement-model and
  texture work as mods).
- Lighting and atmosphere presets per map (already started).
- A mod manager in the launcher: enable, order and check compatibility of mods.

## 7. Validation and rules

- **Round trips:** byte-exact round trip of every supported file before
  editing is allowed.
- **No-mod parity:** with no mod active, frames, draw records and acceptance
  results are identical to the current build.
- **Mod tests:** run in private game instances only; never in the user's main
  install, pilots or campaign saves.
- **Legal:** follow [docs/legal.md](../../../docs/legal.md). Commit no game
  files, extracted assets or generated translations. Shareable mods contain
  authored data and references to original assets by name and hash.
- **Faithful modernization:** mods run on the recompiled original logic; no
  engine replacement or interpreter fallback is introduced for modding.

## 8. Risks

- Reader semantics may be only partly recoverable; some behaviour may be
  hard-coded in the executable rather than in data.
- Adding objects may hit fixed-size engine tables or precomputed data
  (collision, AI navigation, `anim.zbd` bakes).
- Terrain changes may require regenerating data the game never expected to
  change.
- mech3ax output formats are unstable, and its licence limits how it can be
  combined with project code.
- Multiplayer compatibility of modded maps is out of scope until the network
  layer is native.

## 9. Decisions for later

1. Whether mech3ax may be used as an optional external converter or only as a
   research cross-check.
2. Editor technology (native C++ with the Vulkan renderer, or a separate UI
   over a C++ core).
3. Mod file layout and manifest format.
4. First target map for the Phase 2 "hello world" (proposed: Big Lake Instant
   Action, already used for the lighting and shadow work).
