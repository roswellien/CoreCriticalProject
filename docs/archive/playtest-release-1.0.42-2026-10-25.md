# Marauder presentation and selected teammate skins

Published October 25, 2026: launcher **1.0.42-preview**, native MW3 runtime
**1.0.41**, signed catalog sequence **2026102509**. These immutable release
versions are now occupied; subsequent releases must use new versions.

The Marauder pack **0.1.1-preview** fixes the oversized live model and supplies
third-person camera placement calibrated against the public Mad Cat mesh.
Rest-pose dimensions alone were insufficient: the animated Marauder was still
17.6% taller than the reference. The final live height is 11.6894 versus
11.6994 game units, within 0.1%. At the same scripted scene and frame, its
projected upper and lower extents match the Mad Cat within 0.002 native pixels.
The natural chassis width is retained. The camera distance and pitch remain
the Mad Cat defaults; pack data supplies the small placement adjustment.

The chassis pack also supplies an original-compatible teammate silhouette,
the **Olive Drab** base skin label, and donor-bone weapon sockets. The matching
additional **Gun Metal 0.1.3-preview** skin pack has new mesh pins and retains
its stable skin ID. Install both revised packs; updating the native runtime
alone cannot replace an old installed asset pack.

The native Mech Lab selector now operates on the selected teammate rather than
always on the Commander. Actual native testing selected Sommerset for a
Bushwhacker ally, persisted its stable ID, and switched between that ally and
the Marauder Commander through the new silhouette. Sommerset **1.0.1** and
MW3 Remastered Models **1.3.0** remain the compatible public asset versions.

The new `additional-mech-chassis` capability version 2 supports pack-authored
silhouettes, base labels and sockets without adding per-mech native code.
Weapon-origin adjustment runs after successful original weapon lookup and
preserves original direction, random spread, ABI, state and weapon behavior.
The cumulative runtime retains the 1.0.40 normal-map/albedo lighting repair.
The launcher retains optional update checking and the 1.0.41 screenshot-folder
feature. Unfinished concurrent lighting-policy work is not included.

Validation: Python pack/catalog/icon fixtures, C# contract/import checks,
C++ catalog/selector/socket fixtures, actual native skin selection, missing
socket-bone rejection, and positive native weapon runs. The final exact packs
ran with the shipping native host and exited through normal shutdown. An
isolated installed launcher upgrade, runtime activation/rollback and full
installer hash validation passed. Remote downloads passed full SHA-256 and
HTTP Range verification before signed catalog promotion. Both protected
download catalogs retained unrelated packs and original-media entries.
The real DEV shortcut reports launcher 1.0.42 and uses the pinned bundled
runtime. Both revised packs were imported through its normal Mods & Packs UI
and remain enabled alongside Sommerset. The 1.0.41 client library verified the
live signed catalog and discovered both new releases.

Execution boundary: original Mech Lab selection and weapon-origin lookup now
consume optional authored pack data. Strict acceptance remains **131/144**;
these focused playtests do not grant further native-game acceptance credit.
Broad damage, AI and external-PC coverage remain preview validation work.
No commit was made. Private evidence is retained at
`D:/CoreCriticalMechPackRelease-20261025-r2/` and
`D:/MW3MarauderFramingMatch-20261025-r1/`.

Downloads:

- [Full signed installer](https://playtest.corecritical.dev/installers/2026-10-25-r7/corecriticalinstaller-1.0.42-preview.exe)
- [Launcher update wrapper](https://playtest.corecritical.dev/updates/corecritical-1.0.42/1.0.42-cc-update.zip)
- [Native runtime update wrapper](https://playtest.corecritical.dev/updates/1.0.41/1.0.41-mw3-update.zip)
- [Marauder 0.1.1-preview](https://playtest.corecritical.dev/packs/2026-10-25-additions-r2/com.corecritical.marauder-0.1.1-preview.mw3pack)
- [Gun Metal 0.1.3-preview](https://playtest.corecritical.dev/packs/2026-10-25-additions-r2/gunmetal-0.1.3-preview.mw3pack)

Offline wrappers contain correctly named `1.0.42.ccupdate` / `1.0.42.zip`
and `1.0.41.mw3update` / `1.0.41.zip`. Import the metadata with its matching
payload ZIP beside it. Optional packs remain under Mods & Packs.
