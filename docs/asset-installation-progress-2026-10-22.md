# Asset installation status and progress — 1.0.21-preview

The launcher now reports `GAME STATUS: INSTALLING ASSETS (NOT READY)` and
disables Launch throughout an asset import batch. A persistent action-bar meter
shows the current pack and batch count, phase and measured percentage. Archive
inspection starts indeterminate; extraction and schema-2 hash verification use
byte progress. Progress stays below 100 until activation succeeds. File picker,
drag/drop and setup imports share the same batch behavior. Successful imports
are retained if another pack fails, with one final batch summary.

The execution boundary advanced is asset installation readiness in the launcher.
Native gameplay and runtime bytes remain unchanged from playtest-20261022-r5;
formal native acceptance remains 131/144.

## Validation and delivery

The full launcher check suite passes. Storage checks cover measured totals,
monotonic progress, completion after activation and corrupt-pack preservation.
An isolated real two-pack UI import produced 76 active samples: every sample
reported Not Ready with Launch disabled; both packs and changing progress were
observed. Both packs installed successfully. The signed installer passed an
isolated install, installed-file comparison, runtime validation and timestamped
uninstaller check; the test installation was then removed.

Private evidence: `D:/MW3AssetProgressPlaytest-20261022-r1`.

The signed precompiled installer is 92,301,392 bytes, SHA-256:
`eb758a503f8b8f1812a32caa5581ff40ea379d2b20c6176002a1a02682c09de3`.

[Download 1.0.21-preview](https://playtest.corecritical.dev/installers/2026-10-22-r6/MW3Remaster-Playtest-Preview-Setup.exe).

Both existing catalog Setup lists now link this installer, notes and checksum.
Full remote installer readback matches its size/hash and retains a valid,
timestamped Windows signature. Catalogs and sidecars match intended bytes.
Other asset, ISO and patch links are preserved. Access policies and update
feeds are unchanged. This release retains precompiled delivery and does not
generate native game code on the tester's machine.
