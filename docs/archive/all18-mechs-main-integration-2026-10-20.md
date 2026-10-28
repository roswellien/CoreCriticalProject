# All 18 mech models connected to the main Remaster

2026-10-20. The standard Remaster profile and GUI now select all 18 updated
chassis with the current default texture sets and material normals. This adds
the previously offline detailed Owens and Firefly. The other 16 model records,
including the repaired MW5 attachments and detailed Avatar/Strider, are retained.

The main launch path reads `local/material-authoring-r1/normal-registry.json`;
both that registry and `local/remaster/models.json` now contain 18 entries.
The GUI's existing Upgraded Mech Models pack is enabled in the current settings.
Its description and future default stub now describe 18 models instead of the
stale claim of 15 MW5 chassis. No gameplay or graphics setting was changed.

## Current host and source changes

Selected executable:
`local/remaster/gpu-native-all18-r1/build/entry_commandline.exe`

SHA-256:
`ba86eac90bb04a62a1cf6b822eaf363a693fd2f5659fbe8bfd1a3526f356c989`.

Built from the main HUD damage-colour host observed at task start, SHA-256
`85a9a59eefedd52fb310e4a7648d4ec3900e077f3bca827a1a32f6af2535dfe2`.
It preserves that build's rendering, lighting, window and HUD work. The earlier
borderless capability mismatch has been resolved by that newer main build;
the user's `fullscreen_windowed` setting remains unchanged.

Three private host-source files differ from the selected main source snapshot:

- `override_owens_firefly_rosters.inc`: exact original close/distance mesh names,
  vertex counts and controller ownership for both chassis;
- `mesh_override_stage.inc`: four optional visual entries, increasing the table
  from 32 to 36 bindings;
- `override_arm_damage_plans.inc`: eight original arm-subtree/stump alternatives,
  increasing the table from 62 to 70 plans.

The translated object list and all other copied host source files retain their
hashes. Matching source snapshots, build definitions, source pins and local
build scripts accompany the selected executable. No shared gameplay runtime or
production service implementation was substituted. The tracked GUI source
change is only the official model-pack description; existing UI changes remain.

## New model payloads and materials

| Chassis | Source moving parts | Triangles per distance | Material slots | Normal bindings |
|---|---:|---:|---:|---:|
| Owens | 16 | 21,170 | 42 | 40 |
| Firefly | 21 | 23,688 | 53 | 50 |

BWMESH2 payloads retain original visibility/controller ownership. All 336
checked binding poses match, maximum matrix error below 0.000002. Geometry,
part transforms and existing body UV corners retain their authoring identities.
At distance, the original omitted toe controls fold into the corresponding
foot; full detailed geometry is currently retained. Distance optimization is
still needed before claiming an efficient final LOD set.

The latest texture pass's 24 Owens and 32 Firefly source color files remain
byte-identical. New mechanical surfaces use baked versions of their existing
procedural preview materials. Their separate atlas UVs change only the new
detail faces. Existing per-material Blender normal response is baked into
tangent images for native strength 1; optical exceptions remain explicit.
This carries the approved preview response into the new payloads without
changing normal maps or strength settings for the previous 16 chassis.

Selected assets, packed scenes and receipts:
`local/work-ahead/main-model-refresh-20261020-r1/`.
The earlier [default texture pass](default-mech-texture-pass-2026-10-20.md)
remains installed. Alternate-skin registrations, the current 39 texture banks,
world/effect lighting, music and existing graphics settings are preserved.

## Validation

- Actual compiled adapter: **7,782 checks, zero failures**. Both payloads at
  both distances, exact source-roster rejection, all triangles emitted once,
  material/normal bindings, optical exceptions, hidden arms, all arm-loss
  combinations, GPU emission, CPU/near path and unchanged fixture guest bytes.
  The first fixture incorrectly assumed Owens had a separate hand node; that
  test assumption was corrected to exercise its arm-owned weapon geometry.
- Original-compatible comparisons against the current main executable:
  **Training 116/116 frames**, **mode-7 GPU 1,150/1,150 draw records**,
  **IA 116/116 frames** identical. Both versions use private baseline game
  copies. No new strict acceptance credit is inferred from these checks.
- Separate native IA runs: **2,000 presented frames each** for Owens and
  Firefly at 3440×1440, FXAA and AF16, with movement/firing input. Positive
  replacement GPU records: 152 Owens and 185 Firefly; both normal sidecars
  load for each. These are virtual-clock frame-budget exits, not mission
  completion, normal quit, or FPS measurements.
- Actual main and normal-preview root asset preparation passes. GUI's
  `prepared-launcher` path also passes. Each prepared directory contains
  **38 color sidecars**, **36 normal sidecars**, 18 model identities and
  39 bank bindings. All new packed artifacts are byte-identical to the packs
  exercised by the native runs and adapter fixture.
- Main, normal-preview and original-model launch plans pass. Both existing
  registries' first 16 records compare equal to their task-start snapshots.
  Resolution, AA/AF, window mode, draw/fog distances and runtime environments
  remain unchanged. The original-model option still selects no replacement
  geometry while retaining the texture-bank path.

Native render-target captures were inspected; these are not desktop screenshots.
The external follow camera crops the lower model in these stills, so they are
not full-body fit proof. NPC distance transitions, full damage/debris, precise
muzzle presentation, extended campaign play and real-clock performance remain
open. Existing runtime-candidate labels remain. A fixture does not establish
whole-game fidelity or completeness of damage behavior.

The original registry and pilots remain unchanged. Protected jobs and other
graphics writers were preserved; regression attempts refused to start while an
independent diagnostic game was active. No commit. **Strict acceptance remains
paused at 131/144.**

## Play and review

Use the usual GUI with **Upgraded Mech Models** enabled, or root
`Play MW3Remaster.cmd`. Both read the newly published main configuration on the
next launch. The selected host retains all current main features rather than
switching back to an older model-test build.

[Native Owens/Firefly checks and notes on Drive](https://drive.google.com/drive/folders/1-rhFMeFg6XfGgq_jgKwTgcXQGOa9nWUI).
Only rendered previews and notes are uploaded; raw models, source media and
generated game code remain local. No sharing permissions changed.

Private scripts, retained failures, source recovery, fixture and run evidence:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/main-model-refresh-20261020-r1/`.
Boundary advanced: offline detailed candidates → native visual registration
and live IA rendering → main/GUI launcher preparation for all 18 chassis.
Next model work is distance optimization and sustained NPC/combat validation.
