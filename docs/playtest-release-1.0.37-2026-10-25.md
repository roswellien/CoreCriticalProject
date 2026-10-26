# Private playtest release 1.0.37 — October 25, 2026

Published Core Critical Launcher **1.0.37-preview** and MW3 native runtime
**1.0.37** to the protected playtest site. Both existing R2 download catalogs
now list the matching installer, launcher update and cumulative game update.
The execution boundary advanced is delivery of the current native additional
chassis/skin support through both fresh installation and installed updates;
this is not a new formal native-game acceptance result. Acceptance remains
**131/144**. No commit was made.

## Downloads

- [Full signed installer](https://playtest.corecritical.dev/installers/2026-10-25-r2/corecriticalinstaller-1.0.37-preview.exe)
- [Launcher update bundle](https://playtest.corecritical.dev/updates/corecritical-1.0.37/1.0.37-cc-update.zip)
- [MW3 runtime update bundle](https://playtest.corecritical.dev/updates/1.0.37/1.0.37-mw3-update.zip)
- [Playtest download catalog](https://playtest.corecritical.dev/packs/2026-10-21-r2/index.html)

The installer retains the exact filename from its build receipt. Update bundles
contain `1.0.37.ccupdate` or `1.0.37.mw3update`, respectively, and their matching
`1.0.37.zip`. Extract these bundles into **separate folders**. Existing players
install the launcher update first, restart the launcher, then install the game
update. Fresh players use the full installer, which already includes runtime
1.0.37. Original game verification remains required; testers need no compiler
or Windows SDK. Existing installation locations and user content are preserved.

Added Marauder 0.1.0-preview under Models and Sommerset 1.0.1 plus Marauder
Gun Metal - Worn 0.1.2-preview under the new Skins tab. These are optional
`.mw3pack` downloads. Sommerset requires MW3 Remastered Models 1.3.0. Gun Metal
requires the separate Marauder chassis pack. The named choices are discovered
from pack metadata and appear through the normal Mech Lab selection paths.
The existing combined model pack, stock-model texture option, all other pack
rows, ISO and patch links were preserved. Historical objects were not deleted.

## Validation and limits

- Signed full installer completed a fresh isolated installation; every bundled
  runtime member matched the runtime manifest, including the new signed host.
- Actual installed 1.0.36 launcher code verified and staged the signed launcher
  update. Its installer reused the previous directory without a `/DIR`
  override, preserved a user fixture, and left the game runtime unchanged.
  The temporary uninstall registration was restored.
- Signed MW3 update from published runtime 1.0.34 passed original-file
  verification, installation, activation, startup validation and rollback.
- Launcher fixture suite and 44 Python tests passed. The actual three new
  downloadable packs passed installed-launcher PackManager import, capability
  checks and stable additional chassis/skin identity checks.
- Native candidate and preceding host completed the same 700-frame stock Mech
  Lab route. The complete draw trace and captures at frames 650 and 699 were
  byte-identical. Prior additional-chassis camera and world-route evidence is
  retained under the Marauder preview/native work roots.
- All **14 release objects** and **6 catalog objects** were downloaded back
  from R2 and matched their staged SHA-256 hashes and lengths. Catalog writes
  guarded against concurrent changes. Unauthenticated download requests still
  redirect to the existing Cloudflare Access login.

Marauder remains an experimental MW3-compatible 75-ton field refit, not a
canonical MAD-3R. Full damage, AI and weapon alignment coverage remains open.
Gun Metal's actual pack import passed; complete live-game skin coverage remains
open. This exact release has not yet been tested on a clean second Windows PC.
The automatic updater helper's full interactive restart UI was not exercised.

Local artifacts, signing evidence, installation/update logs, remote readbacks
and publication receipts are retained in
`D:/CoreCriticalPlaytestRefresh-20261025-r1/`. The signed native host SHA-256 is
`e6f00aec41da337cd717c8d65fcbddfb18f735dcb76891d0aff69629ebdde9e8`.
The installer SHA-256 is
`c8cbc98f7802718917c44c85bcc637ef01b92db3957d650351f1fccee560f1c3`.
Cloudflare Wrangler's existing authenticated session supplied the working R2
publication route; the older rejected S3 credential was not used or exposed.
