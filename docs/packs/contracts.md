# Content pack contracts

Five agreements that the runtime, the launcher, the mod tools and pack authors are all
built against. A part of the system may assume only what a contract says about another
part, never how that part happens to be written.

Background and the decisions these follow from: [README](README.md). How a contract
changes: [Changing a contract](workstreams.md#changing-a-contract).

| Contract | Version | Fixes | Relied on by |
| --- | --- | --- | --- |
| [1. Pack manifest](#1-pack-manifest) | 1.0 | The fields of `pack.json` | Everyone |
| [2. Installed layout](#2-installed-layout) | 1.0 | Where payloads sit on disk and how ticks are stored | Runtime, launcher |
| [3. Runtime content report](#3-runtime-content-report) | 1.0 | What the runtime says it found | Launcher, Mod Studio |
| [4. Visual binding rules](#4-visual-binding-rules) | 1.0 | How visuals find the thing they dress | Runtime, mod tools, pack authors |
| [5. Feed format](#5-feed-format) | 0 (draft) | The catalogue a launcher downloads | Launcher, pack publishers |

Version 1.0 means the contract is fixed enough to build against. It does not mean
anything is implemented: on 2026-11-27 only the checker for contract 1 exists.

**Shared material**

- Schema files: [schemas/](schemas/).
- Example packs, one valid of each shape and one broken per rule:
  [tests/fixtures/packs/](../../tests/fixtures/packs/README.md).
- The check: `python tools/check.py --only pack-contracts`. To check one pack folder:
  `python tools/packs/check_pack.py <folder>`.

## Problem codes

Every rule below has a code. The pack checker, the runtime's content report and the
launcher use the same codes, so a pack author sees the same word everywhere.

| Code | Rule broken | Found by |
| --- | --- | --- |
| `manifest-invalid` | `pack.json` is missing, unreadable, repeats a key, or a field has the wrong form | Pack check |
| `manifest-unknown-field` | `pack.json` has a field the schema does not name | Pack check |
| `file-undeclared` | A file in the pack is not in `files` | Pack check |
| `file-missing` | An entry in `files` is not in the pack | Pack check |
| `file-hash-mismatch` | A file's size or SHA-256 differs from its entry | Pack check |
| `path-unsafe` | A path could leave the pack folder or is not portable | Pack check |
| `payload-executable` | The pack holds a program, script or library | Pack check |
| `gameplay-root-invalid` | `gameplay.root` has no `mod.txt` listed in `files` | Pack check |
| `visual-target-invalid` | A visual's `target` does not follow the target grammar | Pack check |
| `visual-file-undeclared` | A visual names a file that is not in `files` | Pack check |
| `visual-needs-gameplay` | A visual says it needs the pack's gameplay payload and there is none | Pack check |
| `visual-target-unknown` | Nothing enabled provides the visual's target | Runtime |
| `pack-id-clash` | A pack's `id` is also a folder in the player's `mods\` | Runtime |
| `pack-dependency-missing` | A pack this one depends on is absent, off or too old | Runtime |

A new rule gets a new code here, a broken example pack named for it, and a line in the
examples' `expected.json`. "Pack check" codes are all errors. The runtime adds its
existing mod warnings under codes starting `mod-`.

## 1. Pack manifest

`pack.json` at the root of a `.mw3pack` archive. Schema versions 1 and 2 are in use
today (`tools/mw3-remaster-launcher/Core/PackManifest.cs`) and keep working unchanged.
This contract defines schema version 3:
[schemas/pack-manifest-v3.schema.json](schemas/pack-manifest-v3.schema.json).

### Fields

- **Identity:** `schema_version` (3), `game_id` (`mw3`), `id`, `name`, `version`.
  Optional: `author`, `homepage`, `description`, `category`.
  - `id` is lowercase letters, digits, `_` and `-`, at most 40 characters, starting with
    a letter or digit. It is narrower than schema 2's because it is also the mod's folder
    name once installed.
  - `version` is three numbers, `1.4.0`.
- **Compatibility:** `min_engine_version`, `dependencies` (each `id`, optional
  `min_version`, optional `optional`), `conflicts`.
- **`files`:** every file in the pack except `pack.json`, each with `sha256` (lowercase)
  and `bytes`, and an optional `format`.
- **`gameplay`:** `root`, the folder inside the pack that holds an ordinary mod: a
  `mod.txt` and files laid out like the game's install. Everything
  [modding.md](../../runtime/mw3-re/docs/modding.md) allows in a mod is allowed here and
  nothing else.
- **`visuals`:** a list of bindings. Each has a `target` and a `kind`
  ([contract 4](#4-visual-binding-rules)), `files` (role to pack-relative path), and
  optionally `lod`, `name`, `needs_gameplay` and `options`.
- **`provides`:** a summary for display (`mechs`, `weapons`, `skins`, `maps`,
  `missions`, `campaigns`), written by the pack tool. Nothing may decide behaviour from
  it.

Schema 2's `native_payload` is not part of schema 3. Its registries become `visuals`
bindings.

### Rules

- **Data only.** A file ending in `.bat`, `.cmd`, `.com`, `.dll`, `.dylib`, `.exe`,
  `.jar`, `.js`, `.lua`, `.msi`, `.ps1`, `.py`, `.scr`, `.sh`, `.so` or `.vbs` makes
  the pack invalid.
- **The file table is complete both ways.** Every file is in `files` and every entry in
  `files` is a file, with the stated size and hash.
- **Paths** are relative, use `/`, are at most 240 characters, and have no empty, `.` or
  `..` part, no `\`, no `<>:"|?*` or control character, no part ending in a dot or space,
  and no Windows device name (`CON`, `NUL`, `COM1` and the like). These are the rules
  `PackStorage.ValidatePath` applies today.
- **An unknown field is an error.** A pack author finds a typing mistake at build time,
  not in the game.
- **A repeated key is an error.**
- **Multiplayer.** A pack with a `gameplay` section counts toward the multiplayer match
  check. A pack with only `visuals` never does.

### Settled questions

- `mod.txt` stays the authored file for gameplay. The runtime, its reference and its
  editor already read and write it, and a second form would have to be kept in step.
- A visual that dresses something its own pack adds sets `needs_gameplay: true`. The
  runtime then uses it only where the pack's gameplay payload is ticked.

## 2. Installed layout

### Where things are

| What | Where | Written by |
| --- | --- | --- |
| An installed pack | `<pack library>/<pack id>/`, with `pack.json` at its root | Launcher |
| A pack's mod | `<pack library>/<pack id>/<gameplay.root>/` | Launcher (as part of the pack) |
| A player's own mod | `<write dir>\mods\<name>\` | Player, runtime |
| An entry's ticks | `<write dir>\campaigns\<entry>\mods.txt` | Runtime, launcher |

The pack library is the launcher's existing one (`PackManager.cs`). The entries are the
runtime's existing ones: `mw3` (the game's campaign), `ia` (Instant Action), `mp`
(multiplayer), `<mod>~<id>` for a mod's campaign, and the player's copies
(`runtime/mw3-re/src/upgrades/mods/campaign_entries.cpp`).

### Rules

- **The launcher never writes into `<write dir>\mods\`.** The runtime is told the pack
  library's location with `--pack-library <folder>` and treats each installed pack's
  gameplay root as one more mod, read only.
- **A pack's mod is named by the pack's `id`.** That is the name in a tick file.
- **Search order** for a file two sources both hold: the write directory, then the
  ticked mods in their tick-file order, whether a mod is the player's or a pack's. A
  pack has no special rank.
- **A name clash is refused, not resolved.** A pack whose `id` is also a folder in the
  player's `mods\` is left out with `pack-id-clash`. The player's mod is used.
- **Install** extracts to a staging folder, runs the contract 1 check, and only then
  moves the folder into place. A pack that fails is never present under its final name.
- **Ticks stay in the runtime's files.** The launcher turns a pack on or off for an entry
  by adding or removing its `mod=<pack id>` line in that entry's `mods.txt`, writing a
  new file beside it and renaming it over the old one, as the runtime does. The launcher
  keeps no second copy of that state.
- **The launcher edits tick files only while no game process is running**, and says so
  when one is.
- **Default ticks at install**, for a pack with a `gameplay` section: `ia`, `mp`, and
  each custom campaign entry present. Never `mw3`. A new line goes at the end of the
  file, so it never outranks what the player already ordered. A pack that is being
  updated keeps the ticks it had.
- **A visual-only pack has no ticks.** It is on or off as a whole, in the launcher.
- **Uninstall** removes the pack's folder and its line from every `mods.txt`. Saves are
  left alone; the runtime already names a missing mech or weapon.

### Settled questions

- Multiplayer takes a new gameplay pack by default, as the owner decided. The launcher
  tells the player at install that others need the same pack to join, and the runtime's
  existing lobby check says what differs.

## 3. Runtime content report

One command prints one JSON document and exits:

```text
mw3 --content-report --install <game folder> --write-dir <folder> --pack-library <folder>
```

It mounts nothing and starts no game. The document's form is
[schemas/content-report-v1.schema.json](schemas/content-report-v1.schema.json), and
[an example](../../tests/fixtures/packs/example-content-report.json) sits with the
example packs.

### What it holds

- `report_version`, `game_id`, `runtime_version`.
- `sources`: every pack in the library and every mod in the player's `mods\`. Each has:
  - `id`, `name`, `version`, `origin` (`pack` or `player-mod`), `location`;
  - `used`: false when an error leaves the whole source out;
  - `counts_for_multiplayer`;
  - `adds`: what it brings, by kind (`mechs`, `weapons`, `skins`, `maps`, `missions`,
    `campaigns`, `visuals`). Each item has a stable `name`, and where it applies a
    `title`, a `target`, a `kind`, and `used: false` when that one item is left out;
  - `ticked_for`: the entries it is on for;
  - `problems`.
- `problems`: those that belong to no one source.

A problem has a `code` from [Problem codes](#problem-codes), a `severity` (`error`: the
item or source is left out; `warning`: it is used), a plain-sentence `message`, and where
they apply a `file` and a `line`.

### Rules

- **The launcher and Mod Studio show this report.** Neither works out for itself what a
  pack contains or whether the game will accept it.
- **A broken pack never stops the game.** It is left out and named.
- **Stable order.** `sources` are sorted by `origin`, then `id`; items by `name`. The
  same files give the same document.
- **Versioning.** A reader refuses a `report_version` whose first number it does not
  know. Within a known first number an unknown field is an error, so a field is added
  only together with a rise in the second number.
- **No absolute paths of the player's machine** in `message`. `location` is the one
  place a path appears.

### Settled questions

- This command checks manifests, file tables, names and targets. It does not decode
  meshes or textures. A file that fails to decode is found when it is first needed, falls
  back to the base model or texture, and is named in the log with the same problem form.

## 4. Visual binding rules

The evidence for how binding works today is in the README, under
[Can an HD model attach to a mech a mod added?](README.md#can-an-hd-model-attach-to-a-mech-a-mod-added)

### Targets

Every visual names what it dresses as `<target kind>:<name>`.

| Target | Names | Example |
| --- | --- | --- |
| `mech-model:<model>` | A mech's base model: what a `mech=` line gives as `model=`, or a stock mech's name | `mech-model:thor` |
| `world:<folder>` | A world folder, the game's or a `world=` line's | `world:c1` |
| `mission:<world>/<n>` | One mission of a world, as a campaign's `mission=` line names it | `mission:c1/2` |
| `game:mw3` | The game as a whole | `game:mw3` |

A name is lowercase letters, digits, `_` and `-`, at most 32 characters.

### Kinds and their files

| `kind` | Allowed targets | `files` roles |
| --- | --- | --- |
| `model` | `mech-model` | `mesh`, `textures`; optional `normals`, `materials` |
| `skin` | `mech-model` | `textures`; optional `normals` |
| `environment` | `world`, `mission` | `registry` |
| `ui`, `music`, `cinematic` | `game` | `registry` |

- A `model` has a `lod`: 0 is the close version and 1 the distant one. A target may have
  one of each.
- A `skin` has a `name`, shown in the Mech Lab.
- `registry` is the existing registry file for that kind of payload. Those four kinds
  keep their present inner format; giving each typed fields is later work in workstream C.

The pack check enforces the target grammar today. Checking a kind against its allowed
targets and roles is a follow-up to this contract's first version.

### Rules

- **Skins and models are keyed by model name everywhere.** The Mech Lab's skin list and
  the renderer use the same key. Two mechs that share a base model share its HD model and
  its skins. The condition that a mech must have exactly eight original skins is removed.
- **A mech that wants its own look has its own base model.** A variant that only changes
  numbers borrows a stock model and is drawn as that stock mech.
- **The HD model follows the base model's skeleton.** Each part name the HD model refers
  to exists exactly once in the base model. The pack tool checks this at build time. The
  runtime checks again and, on a mismatch, draws the base model and reports a warning.
- **No behaviour is keyed on a chassis name in code.** What one model needs is a named
  entry in its binding's `options`: `headlights` for the sockets the model's lights
  attach to, and `guard_fit` for the correction the Orion's model needs today.
  Workstream C defines each option's fields when it moves it out of code.
- **Weapon mounts are gameplay, not visuals.** Where a mech's weapons sit comes from its
  definition (`dfn_<mech>.zrd`) in the gameplay payload, as it does for stock mechs.
- **One pack may dress another pack's content.** It declares a dependency on that pack.
  Without it, or with that pack off, the visual is left out with
  `pack-dependency-missing` or `visual-target-unknown`.
- **Two packs that give the same model and `lod`:** the launcher's pack order decides,
  first wins, and the report names both.

## 5. Feed format

Version 0, a draft. It is not needed for the first milestone, which installs from a
file.

### Today

A signed catalogue document: `schema_version`, `type`, `channel`, `sequence`, issue and
expiry times, and a list of packs. Each pack has `id`, `game_id`, `version`, a minimum
runtime version, the archive with its hash, and the manifest hashes of installed copies
it may replace (`tools/mw3-remaster-launcher/Core/AssetPackUpdateCatalog.cs`). There is
one feed, ours.

### Proposed

- **The same document for every feed.** A third party publishes a catalogue in this
  format at an address of their own, and a player adds that address in the launcher.
- **Each feed has its own signing key**, shown to the player as a short fingerprint when
  the feed is added and pinned from then on. A catalogue signed by a different key is
  refused, not offered as an update.
- **A feed can only update packs it first installed.** A third-party feed can never
  replace a pack from our feed or from another feed, whatever `id` it claims.
- **Third-party packs are labelled** with their feed's name wherever they are listed.
- **The safety of a pack never depends on its feed.** Every pack from every feed passes
  the same contract 1 check at install.

### Settled

- A `.mw3pack` file can be installed by hand with no feed behind it. It passes the same
  check, is labelled "no update source", and never auto-updates (owner, 2026-11-27).

### Open questions

- Whether we keep a list of known third-party feeds on the website.
- How a feed's key is replaced when its owner loses it.
