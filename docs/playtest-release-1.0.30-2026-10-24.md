# Playtest installer and native runtime publication — 1.0.30

Superseded later on October 24 by the
[1.0.32 first-run wizard and resolution repair](first-run-wizard-and-resolution-repair-2026-10-24.md).
The evidence below records the earlier release.

The protected [playtest downloads](https://playtest.corecritical.dev/) now offer
the signed branded Core Critical 1.0.30-preview full installer and matching
launcher/game update bundles. Both existing Setup catalogs were updated.

- [Full installer](https://playtest.corecritical.dev/installers/2026-10-24-r2/corecriticalinstaller.exe):
  includes the current DEV precompiled native runtime. Fresh installations need
  no separate game update or native-code generation. Original inputs remain
  required. First-run setup provides display and graphics choices.
- [Launcher update](https://playtest.corecritical.dev/updates/corecritical-1.0.30/CoreCriticalLauncherUpdate.zip):
  signed `.ccupdate` and matching payload ZIP, for launcher 1.0.27 or newer.
- [Cumulative game update](https://playtest.corecritical.dev/updates/mw3-stock-presentation-20261024-r2/CoreCriticalGameUpdate.zip):
  signed `.mw3update` and matching payload ZIP. **Requires launcher 1.0.30+**;
  existing installs update the launcher first. Earlier game updates are unnecessary.

The runtime is `mw3-stock-presentation-20261024-r2`, sequence 2026102405. It
matches the currently selected DEV host and module, retaining heap/controller/
vehicle fixes and previous performance/weapon/status work, plus the stock and
optional-lighting selection contract. This does not claim completion of the
planned community content registries or independent environment/effects packs.

| Artifact | SHA-256 |
| --- | --- |
| Branded full installer | `0168cc1e2ca51f85827c2c84cef4863811ed2668262083fa2736fd6c8f614586` |
| Launcher bundle | `1966f79b04138287cb72bb90fd2434f57fa89bfd29e837650dbf10a66cc768f4` |
| Cumulative game bundle | `83f390460ed12049cedc83084197f9fedc6d8eecebb97636076090d49de75734` |
| Native host | `aaa5881fa9f4b72cc9f3c1277d81c37d25510ed9ea5ced4ba49759751f4ce1a0` |

## Publication evidence and limits

Private evidence root: `D:/CoreCriticalPlaytest-1.0.30-20261024-r1`.

- All nine versioned release objects were uploaded and fully downloaded back;
  byte sizes and SHA-256 match. ZIP integrity, signed-envelope payload pins and
  all 660 runtime file hashes were checked against the prepared release.
- Downloaded installer Windows signature is valid. The full branded installer
  passed isolated fresh installation; installed launcher and runtime match.
- Existing evidence verifies the actual installed 1.0.29 updater stages and
  upgrades to 1.0.30, preserving runtime/user fixtures. The signed game update
  passed install/activation/validation/rollback from the published controller
  runtime and the newer vehicle runtime. No new code changes or benchmarks were
  required for publication. Build evidence is retained in the stock-presentation
  and installer-skin roots referenced by their separate documents.
- Both HTML objects were guarded against concurrent changes immediately before
  writing, then read back identically. All non-Setup rows and retained media rows
  are unchanged. Previous release objects remain for recovery; only their
  catalog rows were superseded.
- Signed-out root, catalog and all three new download links redirect to
  Cloudflare Access. No Access policy, DNS, bucket visibility, redirect target
  or main website deployment was changed. Authenticated tester UI was not
  separately exercised in this publication pass.
- A separate clean Windows machine and automatic updater helper/restart UI are
  not established by these local checks. No Git commit or push was made.

`upload-plan.json`, `files-publication.json`, `catalog-plan.json`,
`catalogs-publication.json`, `access-check.json` and `completion.json` retain the
publication identities. If links or content prove incorrect, restore the
saved `catalog-r1-before.html` / `catalog-r2-before.html` only after checking for
concurrent changes; the previous release objects remain intact. No database or
service migration is involved. Native acceptance remains **131/144**.
