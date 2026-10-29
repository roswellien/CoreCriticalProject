# Downloadable additional skins — October 25, 2026

**Later publication:** the protected playtest site now includes Sommerset
1.0.1, Marauder Gun Metal - Worn 0.1.2-preview and its required Marauder chassis
pack, alongside launcher/runtime 1.0.37. See the
[1.0.37 release record](playtest-release-1.0.37-2026-10-25.md) and
[download catalog](https://playtest.corecritical.dev/packs/2026-10-21-r2/index.html).
The Drive delivery and initial rejected S3 credential attempt below are retained
as historical evidence. Existing Wrangler authentication subsequently enabled
R2 publication with complete remote SHA-256 readback. Gun Metal 0.1.2 updates
installation guidance for the published runtime; its texture payloads are
unchanged. DEV runtime selection was not changed by website publication.

The owner requested separate downloadable packs for the Marauder Gun Metal
finish and the Bushwacker Sommerset skin. Both are data-only `.mw3pack` files
that add named Mech Lab choices, preserving existing skins and gameplay.

Downloads and installation/checksum files are in the private
[Skin Pack Downloads folder](https://drive.google.com/drive/folders/1_0juGlou1dGir8Nvlg6OnyD-VUqafvqh).
Existing Drive sharing was preserved; no public-link permission was added.

| Pack | Download | Requirements/status |
| --- | --- | --- |
| Sommerset 1.0.1, Bushwacker | [sommerset-1.0.1.mw3pack](https://drive.google.com/file/d/1lbDGpfjnRCe8PuK2jbOdrxTtfO80yzUs/view) | Matches the close/distance Bushwacker meshes in MW3 Remastered Models 1.3.0. Requires additional-mech-skins v1. |
| Gun Metal - Worn 0.1.1-preview, Marauder | [gunmetal-worn-0.1.1-preview.mw3pack](https://drive.google.com/file/d/1Hw_-6H6S7wS-PaWgwgmmNlvnLKapFccd/view) | Requires the separate Marauder chassis pack and additional-mech-chassis v1 plus additional-mech-skins v1. The newer chassis runtime remains staged, not activated in DEV. Live-game skin validation remains open. |

Import with **Mods & Packs → Install Pack**, enable the pack, then select the
named skin under **SKINS** in Mech Lab. Downloading a skin does not install its
required model or supply a newer runtime. The folder includes
[installation guidance](https://drive.google.com/file/d/13qTEXXrym9Tp6rzD-FoxD41TqoCY6mPS/view)
and [SHA-256 checksums](https://drive.google.com/file/d/1jdRQAB98BSKpNdkXdf_mIgTjdcRzuSUW/view).

Sommerset retains its existing 1.0.1 bytes and stable identity. Gun Metal 0.1.1
updates its human-readable Marauder name, preview guidance and explicit chassis
capability requirement; its texture payloads and mesh identities remain those of
the reviewed 0.1.0 candidate. The skin builder now accepts a chassis display name
and requires the chassis capability for skins targeting namespaced added mechs.
There is no per-Marauder engine registration or executable in either skin pack.

Both archives passed full local member closure/size/hash checks, real launcher
PackManager import into an isolated root and Python composition. Sommerset was
checked against the selected combined model pack. Gun Metal was discovered from
installed manifests with the skin listed before its chassis; the current DEV
host correctly rejected its missing newer chassis capability. Original skin
choices and selected DEV settings were not changed.

Drive upload readback confirmed all four filenames, byte lengths and folder
membership. This is metadata verification, not a claim of complete remote
SHA-256 readback. Local release/compatibility/publication receipts are under
`local/work-ahead/skin-pack-downloads-20261025-r1/`.

R2's saved credential returned AccessDenied on the initial GetObject preflight.
No R2 files or protected download catalogs were modified. The Google Drive files
provide the requested downloads while that credential issue remains unresolved.
No commit or native acceptance change was made; acceptance stays 131/144.
