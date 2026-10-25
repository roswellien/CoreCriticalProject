# One combined DEV/playtest model pack — 2026-10-24

The 1.2.0 release described below has been superseded by the private
[1.3.0 model pack](model-pack-1.3.0-2026-10-24.md). This page retains the
original 1.2.0 installation and publication record.

The user selected one combined pack for all 18 upgraded mechs. This release put DEV on
`MW3 Remastered Models` 1.2.0, retaining ID `com.mw3remaster.mw5-mechs` so it
replaces the former 14-model collection when imported. The four upgraded
original chassis are included. Current installed model resources were frozen
directly, preserving all recent model, default texture, alternate-livery and
normal work without regenerating older authoring candidates.

The deliverable is the exact archive installed into DEV through the launcher's
existing `PackStorage.Install` implementation, via its existing integration
command. It contains only the referenced resources, manifest and registry:
18 models, 360 bindings, 254 archive members, 2,278,019,124 compressed bytes.
Archive SHA-256:
`9e539e3b74ce51394ef31964e76157f841eadcbea468417e55b6b574fed6a074`.
All archive member sizes/hashes and registry closure passed.

Thirty-seven superseded payloads (1,272,582,856 bytes) were excluded. The
separate Updated MW3 Mechs installation, duplicate pre-Sunder collection and
old model rollback directories were moved out of active Mods discovery into
the existing data root's `pack-backups/combined-models-20261024-r1/` directory.
They are recoverable backups, not enabled/discovered model packs. Environment,
shared original textures, music, HUD and menu packs remain separate and intact.

DEV selection changes:

- One `prepared_pack_roots` entry selects the installed combined pack.
- Legacy `model_registry` selection and all 360 loose model environment
  overrides were removed from the base DEV launch profile.
- GUI settings enable the combined pack and remove the separate old
  Updated MW3 Mechs selection, preserving unrelated settings and pack order.
- A full `play_remaster.py --prepare-only` run completed with 18 models and
  the existing 38 environment banks. The emitted session profile has all 360
  model paths inside the combined pack. Every resource SHA matches its prior
  approved selected resource, including current model attachments and size.

Execution boundary: packaged model-resource selection, import and preparation.
There is no native code, gameplay, normal response or asset pixel change in this
consolidation. Native runtime remains the current selected r7 build. No new
gameplay/acceptance credit; 131/144 unchanged. No commit performed.

Private deliverable and evidence:
`local/work-ahead/combined-model-pack-20261024-r1/`, including the `.mw3pack`,
release.json, source snapshots, launcher's import receipt, DEV selection receipt,
prepared launch verification, settings/profile rollback inputs and logs.

Publication status: **published and fully read back on October 24**. The user
renewed the bucket-scoped upload credential, which is stored with Windows DPAPI;
the plaintext staging file was removed. Both this archive and the independent
stock-model texture archive passed complete remote SHA-256 readback. Both
protected catalog pages, their metadata and checksum lists were updated and
read back byte-for-byte. Setup, ISO, patch and unrelated asset rows were retained.
The two new objects are under `packs/2026-10-24-models-r1/`. Remote publication,
old-object backup/deletion and verification are journaled in the private
`r2-publication.json` and `publish.log`. Original superseded archives are retained
locally before their R2 copies are retired.

Existing testers should import this combined pack,
then uninstall the separate Updated MW3 Mechs pack. Retaining the existing
14-model pack ID replaces that former collection automatically. The current
launcher does not automatically remove a different installed pack ID; the
staged download entry explicitly gives this migration instruction.
