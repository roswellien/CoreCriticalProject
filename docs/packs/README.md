# Content packs

How new content reaches the game: mechs, weapons, skins, Instant Action maps, missions,
campaigns and HD visuals. A player installs a pack in the launcher and the content is
usable in game, with no code change and no fixed list to edit.

This folder is the starting point for anyone working on that system.

- [Contracts](contracts.md): the five written agreements every part is built against.
- [Workstreams](workstreams.md): who owns which folders, what depends on what, and the
  rules for changing a contract.

Status on 2026-11-27: contracts 1 and 4 are at version 1.1 and contracts 2 and 3 at
version 1.0, with schema files, example packs and a pack check for contract 1 and
contract 4's kind table. Nothing else is implemented beyond what "What exists
today" below describes.

## Decisions

The owner made these on 2026-11-27. Treat them as settled.

1. **One pack, two possible payloads.** The asset pack is the only thing a player
   downloads, updates or installs. A pack may carry a gameplay payload, a visual payload,
   or both, so a new mech and its HD model ship and update together.
2. **Gameplay content uses the runtime's existing mod engine.** The gameplay payload is an
   ordinary MW3-RE mod folder with a `mod.txt`. We do not build a second gameplay system,
   and the in-game MODS screen stays.
3. **Visual content uses the existing asset pack method.** HD models, skins, normal maps,
   dynamic lights, environments, UI artwork, music and cinematics stay as prepared
   payloads.
4. **Where a newly installed gameplay pack is on by default:** Instant Action, multiplayer
   and custom campaigns. Never the game's own campaign, unless the player ticks it there.
5. **Where a player turns a pack on or off:** in the launcher and on the in-game MODS
   screen. Both read and write the runtime's own tick files, so they cannot disagree.
6. **A new mech always has an original-format base model**, borrowed from a stock mech or
   shipped by the pack. The HD model sits on top. A mech with only an HD model is not
   allowed, because it would vanish for players with HD visuals off and would break
   multiplayer between players with different settings.
7. **Distribution.** Our packs come from our feed. A third party hosts its own feed and a
   player adds its address. Packs are data only: no executables and no scripts.
8. **First proof.** A new mech with an HD model, installed from the launcher and playable.
9. **One pack may dress another pack's content**, for example a skin for a mech a
   different pack added, by declaring a dependency on that pack.
10. **A pack file can be installed by hand** with no feed behind it. It passes the same
    checks, is labelled as having no update source, and never auto-updates.

The earlier modular content work in the separate MW3-RE repository (its `src/content`
library and `mw3content` tool) is not used. Its ideas may be borrowed; its code is not
ported.

## What exists today

Two systems work and are not joined.

### The runtime's mod engine

Documented in [modding.md](../../runtime/mw3-re/docs/modding.md), with every key in
[modding-reference.md](../../runtime/mw3-re/docs/modding-reference.md).

- A mod is a folder in the write directory's `mods\`, laid out like the game's install,
  with a `mod.txt` (`runtime/mw3-re/src/mech3/mods.cpp`).
- `mod.txt` can add mechs (`mech=`, numbered after the game's 19), weapons (`weapon=`,
  after the game's 37), worlds (`world=`), Instant Action maps (`ia_world=`), campaigns
  (`campaign=`) and text (`strings.txt`). `needs=` and `conflicts=` warn and never block.
- Mods are ticked per campaign entry and for Instant Action and multiplayer. Each entry
  keeps its ticks in `<write dir>\campaigns\<id>\mods.txt`
  (`runtime/mw3-re/src/upgrades/mods/campaign_entries.cpp`). A plain start mounts no mod.
- Saves record added mechs and weapons by name, and the multiplayer lobby compares a hash
  of the mounted gameplay files.

### The launcher's asset packs

- A pack is a `.mw3pack` archive with a `pack.json` manifest and a hash for every file
  (`tools/mw3-remaster-launcher/Core/PackManifest.cs`, `PackStorage.cs`).
- The launcher downloads and auto-updates packs from a signed catalogue
  (`AssetPackUpdateCatalog.cs`, `AssetPackUpdateService.cs`).
- At launch the planner (`tools/remaster-launcher/mw3_re_launch.py`) reads each enabled
  pack's registry and turns it into command-line flags for the runtime: `--cc-model`,
  `--cc-model-skin`, `--cc-skin-catalog`, `--cc-environment-pack`, `--assets` and others.
  The runtime does not look for packs itself.

### Where they fail to meet

- The launcher never puts anything in the runtime's `mods\` folder and never writes a
  tick file.
- The runtime never scans the pack library.
- Lists of stock chassis names are fixed in code: the `Templates` set in
  `tools/mw3-remaster-launcher/Core/ChassisPack.cs` and `stock_names` in
  `tools/remaster-launcher/native-overrides/additional_chassis.hpp`.

[additional-mech-packs.md](../additional-mech-packs.md) describes an earlier route for
additional chassis that numbers new mechs from 32. The runtime's mod engine numbers them
from 20. Decision 2 makes the mod engine's route the one to build on; the earlier
route is not extended.

## Can an HD model attach to a mech a mod added?

Yes in principle, with three gaps. This comes from reading the code on `develop`
(commit `74cc4f76`). It was not run in the game.

**How attachment works.** The renderer matches an HD model to whatever the game is drawing
by the name of the original model file: `mech_<model>.flt`, or `mech_<model>_1.flt` for
the distant version (`mech_asset_key` and `model_for_asset` in
`runtime/mw3-re/src/frontend/core_critical/prepared_models.cpp`). `--cc-model` takes any
lowercase name of up to 32 characters, not only the stock chassis.

- A mod mech that borrows a stock model (`model=thor`) is drawn with the Thor's HD model
  with no extra work.
- A mod mech with its own base model should get its own HD model the same way. No test or
  run proves this yet.

**Gap 1: two mods that each bring a mech model cannot both be on.** A mod's `mechlib.zbd`
replaces the whole archive, so the first enabled mod hides every other mod's models
(the `mech_<model>.flt` check in `runtime/mw3-re/src/mech3/mods.cpp`). The runtime
already merges reader archives entry by entry
(`runtime/mw3-re/src/upgrades/mods/entry_archives.cpp`); the model library needs the same.

**Gap 2: skins are matched by two different names.** The Mech Lab appends pack skins to a
mech by the mech's own name (`read_dfn` in `runtime/mw3-re/src/mech3/mech_reader.cpp`),
while the renderer looks them up by the model's name. For a variant `thor_b` that uses
`model=thor` the two disagree, so the pack's skins would not be listed. The Lab also
appends pack skins only when the mech has exactly eight original skins
(`base_skin_count` in `runtime/mw3-re/src/platform/prepared_skins.h`).

**Gap 3: special cases tied to stock names.** The launcher accepts only a fixed list of
chassis templates (`ChassisPack.cs`), and the Orion's guard fit is tied to the name
`orion` (`prepared_models.cpp`).

**A rule for modders that follows from this.** An HD model's parts are attached by the
base model's part names, and each named part must exist exactly once in the base model
(`require_batch_source` in `prepared_models.cpp`). An HD model must be built against the
skeleton of the base model it sits on.

## First milestone

A reference pack that adds one new mech with an HD model.

It is done when all of these hold, on a normal install with HD visuals on:

1. The pack installs from the launcher with no file edited by hand.
2. With no further step, the mech is listed in Instant Action and in the Mech Lab.
3. It is drawn with its HD model close up and at a distance, and with its base model when
   HD visuals are off.
4. A second pack that adds a different mech can be on at the same time (gap 1).
5. A skin from the pack is listed for the mech and is drawn (gap 2).
6. The game's own campaign started from the main menu is unchanged.
7. Turning the pack off in the launcher shows it off on the in-game MODS screen, and the
   other way round.
8. Uninstalling the pack leaves a saved pilot loadable, with a plain message about the
   missing mech.
