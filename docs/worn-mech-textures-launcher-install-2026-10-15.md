# Worn Bushwacker and Mad Cat textures connected to the launcher

2026-10-15. The user requested that the new Bushwacker and Mad Cat color sets
be installed for `D:/Projects/MW34Recomp/Play MW3Remaster.cmd`. Updated only the
five `textures` paths for each model in ignored `local/remaster/models.json`:

- Bushwacker: `mw5-bushwacker-extract/mw3-material-r7-worn-prototype/textures/`.
- Mad Cat: `mw3-cinematic-mechs-r1/madcat-worn-textures-r1/textures/`.

Both paths are under ignored `local/work-ahead/`. The existing launcher reads
this registry and repacks the source PNGs on every launch. No engine rebuild or
launcher code change was necessary. The regular launcher retains all seven
replacement models and 39 texture banks; Avatar remains excluded. The separate
launcher without replacement models continues to use original model geometry.

Executed the actual root `Play MW3Remaster.cmd --prepare-only` to successful exit
without starting the game. The configured native build remains
`local/remaster/gpu-native-fog-stock-r1/build/entry_commandline.exe`, SHA256
`866d6c7ce7e4aa566f9c06fa2b44afaaeb421591f58a44946830476121aba908`.
The existing profile remains 3440x1440, FXAA, AF16 and 800-unit scenery distance.
This publication does not select a different build or change the graphics profile.

Independently parsed both actual prepared BWTEX1 files and checked material
names, source batch indices/counts, dimensions, content hashes, complete RGB565
pixel arrays and end-of-file boundaries against the registered sources:

| Model | Batches | Prepared material dimensions | File size |
| --- | --- | --- | --- |
| Bushwacker | 32 | Body 2048x2048; Variant/Weapons 1254x1254; Window/MissileHead 64x64 | 14,695,440 bytes |
| Mad Cat | 38 | Body/Variant/Weapons 1254x1254; Window/MissileHead 64x64 | 9,451,888 bytes |

The existing preparation path limits each image to 2048 pixels and flips rows
for the runtime texture convention. Bushwacker's 4096-pixel authored Body source
is preserved; its runtime image uses that existing cap. Both prepared files have
changed from their previous versions and match all expected pixels. The native
host snapshot consumes the same texture environment bindings, and the profile
does not override them. Eight unrelated prepared model/LOD files retain their
previous hashes. All non-texture model fields, other model records, mesh files,
old/new PNG sources, launcher scripts, profile and executable retain their
starting identities.

Rollback and publication/verification records are in ignored
`local/work-ahead/worn-texture-launcher-install-r1/`; its `before/models.json`
retains the complete prior registry, with prior target prepared files and receipt.
The earlier offline-art manifests remain historical evidence from before this
explicitly authorized publication. No original textures were overwritten.

Execution boundary: the regular launcher now resolves and prepares the selected
worn base-color sets for the existing native adapter. This is asset preparation,
not an in-game visual, performance or new native-execution validation. Painted
wear is static; normal mapping and the selected future 12x-equivalent response
remain separate renderer work. No game launched, desktop screenshot,
MW3/mw34-registry.txt or pilot edit, or commit. Strict acceptance stays paused
at 131/144.
