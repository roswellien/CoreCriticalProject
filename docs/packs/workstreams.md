# Content pack workstreams

How the pack system is split so that different people and agents can build its parts at
the same time. Read the [README](README.md) for the decisions and the
[contracts](contracts.md) for what each part may assume about the others.

## The idea

Each workstream owns a set of folders and meets the others only at a contract. A stream
tests against shared example packs, not against another stream's unfinished code. The
pieces are joined in one place, workstream G.

```text
A  Contracts and example packs
|
+--> B  Runtime: gameplay delivery ---+
+--> C  Runtime: visual discovery ----+--> G  Reference pack and acceptance
+--> D  Launcher --------------------+
+--> E  Authoring tools
+--> F  Modder documentation
```

B, C, D, E and F start once A's first version lands and run in parallel.

## The streams

Paths under "Owns" are the only places a stream edits. "Uses" names the contracts it is
built against, by their number in [contracts.md](contracts.md).

### A. Contracts and example packs

- **Owns:** `docs/packs/` with its schema files in `docs/packs/schemas/`, the shared
  example packs in `tests/fixtures/packs/` (no original game files in them), and the
  pack check in `tools/packs/`.
- **Delivers:** each contract's open questions closed, a schema file per contract, and a
  small set of example packs: one valid pack of each kind, and one broken pack per rule a
  contract states.
- **Depends on:** nothing. It goes first.

### B. Runtime: gameplay delivery

- **Owns:** `runtime/mw3-re/src/mech3/mods*` and `runtime/mw3-re/src/upgrades/mods/`.
- **Uses:** contracts 1, 2 and 3.
- **Delivers:**
  - the second, read-only mods folder (contract 2);
  - the gameplay half of the content report (contract 3);
  - the mech model library merged entry by entry, so two packs that each bring a mech
    model can both be on ([gap 1](README.md#can-an-hd-model-attach-to-a-mech-a-mod-added)).

### C. Runtime: visual discovery

- **Owns:** `runtime/mw3-re/src/frontend/core_critical/` and
  `runtime/mw3-re/src/platform/prepared_*`.
- **Uses:** contracts 1, 3 and 4.
- **Delivers:**
  - the runtime reading a pack's `visuals` section itself, in place of flags worked out
    by the launcher;
  - skins keyed by model name in the Mech Lab and the renderer (gap 2);
  - per-model corrections moved from chassis names in code to binding fields (gap 3);
  - the visual half of the content report.
- **Shared file:** `runtime/mw3-re/src/mech3/mech_reader.cpp` builds the Mech Lab's skin
  list. Stream C changes that one function; stream B does not touch it.

### D. Launcher

- **Owns:** `tools/mw3-remaster-launcher/`, `tools/mw3-remaster-launcher-tests/` and the
  planner `tools/remaster-launcher/mw3_re_launch.py` with its tests.
- **Uses:** contracts 1, 2, 3 and 5.
- **Delivers:**
  - install, update and uninstall of schema 3 packs;
  - pack toggles per entry, written to the runtime's tick files, with the default ticks
    of contract 2;
  - the pack list drawn from the runtime's content report;
  - third-party feed addresses (contract 5);
  - the fixed chassis lists and the per-pack flag building removed, once stream C lands.

### E. Authoring tools

- **Owns:** `games/mw3/mod-tools/`. It builds on workstream A's `tools/packs/` and asks A
  for changes there.
- **Uses:** contracts 1, 3 and 4.
- **Delivers:** a pack builder that writes `pack.json` and the file hashes, a checker
  that runs the runtime's content report on a pack folder, starter packs, and Mod Studio
  export to a pack.

### F. Modder documentation

- **Owns:** the modder guides under `docs/packs/` (not the contracts).
- **Uses:** all five contracts.
- **Delivers:** one guide per content kind, written from the example packs: a mech, a
  weapon, a skin, an Instant Action map, a mission, a campaign. Each guide is finished
  when someone who has not seen the code can follow it to a working pack.

### G. Reference pack and acceptance

- **Owns:** the reference pack and the acceptance run. It edits no other stream's code;
  a defect it finds is filed against the stream that owns it.
- **Depends on:** B, C and D.
- **Delivers:** the [first milestone](README.md#first-milestone), then our own packs
  converted to schema 3 one at a time.

## Rules

### Working inside a stream

- A task edits only the folders its stream owns. A task that seems to need another
  stream's folder is two tasks.
- Every task is an issue filed with the Task form, written so a person or agent can pick
  it up with no other context. It names its stream and the contract versions it is built
  against.
- The usual workflow applies unchanged: a topic branch from `origin/develop`, a PR into
  `develop`, and review by someone who did not write it
  ([github-workflow.md](../github-workflow.md)).
- A stream's tests use the shared example packs. A test that needs another stream's code
  to pass belongs to workstream G.

### Changing a contract

A contract is the only thing two streams share, so it changes in the open and first.

1. Open a PR that changes only `docs/packs/contracts.md`, the schema file and the example
   packs. It says what changes, why, and which streams are affected.
2. Someone from each affected stream reviews it.
3. It raises the contract's version: a new optional field or a clarification raises the
   minor number; anything that makes an existing pack or reader wrong raises the major
   number.
4. Code that relies on the change is opened only after that PR merges.

A stream that finds a contract unclear asks in the contract's issue. It does not settle
the question in its own code.

### Keeping the runtime mergeable

The runtime in `runtime/mw3-re/` follows an upstream project. Streams B and C keep new
behaviour in `src/upgrades/` and `src/frontend/core_critical/` where they can, and keep
changes to files that mirror the original game small and marked, so upstream changes
still merge.

### What is never acceptable

- A list of content names fixed in code.
- The launcher or a tool deciding for itself what a pack contains or whether it is valid.
  That is the runtime's content report.
- A pack that can stop the game from starting.
- A change to the game's own campaign from a pack the player did not tick for it.

## Order of work

1. **A1:** close the open questions in contracts 1 to 4 and add their schema files and
   example packs. Contract 5 can follow, since the first milestone installs from a file.
2. **In parallel:**
   - B: the second mods folder, then the model library merge;
   - C: skins by model name, then reading `visuals` in the runtime;
   - D: schema 3 install and toggles;
   - E: the pack builder and checker.
3. **Both runtime streams:** the content report, then the launcher's list drawn from it.
4. **G:** the reference mech pack and the first milestone's eight checks.
5. **After the milestone:** third-party feeds (contract 5), the remaining content kinds
   one at a time, our own packs converted, and the modder guides.
