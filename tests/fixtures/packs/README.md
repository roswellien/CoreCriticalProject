# Example content packs

Shared examples for the content pack contracts in
[docs/packs/contracts.md](../../../docs/packs/contracts.md). Every workstream tests against
these instead of against another workstream's unfinished code.

No file here comes from the game. Each pack is an unpacked folder: what a `.mw3pack`
archive holds once extracted.

- `valid/`: one pack of each shape. `gameplay-only`, `visuals-only`,
  `gameplay-and-visuals`.
- `broken/`: one pack per rule. Each folder is named for the problem code it must
  produce — with a suffix when one code has more than one example, as
  `manifest-invalid-nan` — and breaks that rule only.
- `expected.json`: which packs are valid, and for each broken pack its code and who finds
  it. `pack-check` means `tools/packs/check_pack.py` finds it from the pack alone.
  `runtime` means only the runtime can find it, so the pack checker must call that pack
  valid.
- `example-content-report.json`: a contract 3 report, valid against
  `docs/packs/schemas/content-report-v1.schema.json`.

## Limits of these examples

- The visual files (`.bwmesh`, `.bwtex`) are short text placeholders, not real prepared
  files. They give the manifest something to list and hash. A test that needs the
  renderer to load a model must supply a real one.
- The gameplay examples add the mech `example_thor_b`. The runtime mounts a mech row only
  when its definition, `zbd/dfn_example_thor_b.zrd`, is present, and that file is made
  from the player's own copy of the game (as `mw3 --make-starter mech` does). So these
  packs are valid as packs but are not playable as they stand.

## Changing an example

Git stores these files byte for byte (`.gitattributes`), because each `pack.json` records
the size and SHA-256 of every other file in its pack.

After changing a file in a valid pack, rebuild its table:

```text
python tools/packs/fill_file_table.py tests/fixtures/packs/valid/<name>
```

Do not run that on `broken/file-undeclared`, `broken/file-missing`,
`broken/file-hash-mismatch` or `broken/path-unsafe`: a wrong table is their point.

Then run the check:

```text
python tools/check.py --only pack-contracts
```

A new rule in a contract gets a new folder under `broken/` and a line in `expected.json`.
