# Daishi default texture restoration — 2026-10-24

Follow-up: `docs/daishi-dark-detail-pass-2026-10-24.md` supersedes this pass's
dark mechanical colors and updates the Weapons atlas. The notes below describe
the first installed revision.

The optional Daishi replacement-model default skin now draws more clearly from the
original MW3 textures. Body and Variant keep their existing 2048×2048 UV layout
while shifting tan armor toward the original pale finish. Exposed armor rims
receive light metallic wear; dark vents and panel recesses remain dark. A small
red service light was placed on the launcher face beside its port row after a
model-space UV probe confirmed the location. The existing blue canopy remains.

Local authoring and review artifacts are in
`local/work-ahead/daishi-markings-20261024-r1/`. The actual revised sheets are
`textures/Body_basecolor.png` and `textures/Variant_basecolor.png`; matched
Blender front, rear, close, and unlit images compare them with the prior sheets.
The original MW3 tile contact is local only.

The installed optional model pack now points Daishi default LOD0 and LOD1 to
new BWTEX1 color payloads. Their batch tables and their Weapons, Window, and
MissileHead records are byte-identical to the previous payloads. Alternate
skins, normal maps, geometry, rig and walk animation were not changed.
`local/remaster/models.json` and
`local/material-authoring-r1/normal-registry.json` point to the new source
sheets. The installed pack's model registry and manifest were updated for the
two new content-addressed payloads. Previous small registry files were backed
up under `installation-backup-r2/`.

Blender 5.2.2 rendered matched views and reported unchanged geometry/UV/pose
and animation hashes. Both Windows views of the installed pack resolve to the
new content hashes. This is an optional asset-pack presentation change; it
does not advance native host, live menu, live Training, or the 131/144
acceptance count. No in-game visual pass was run in this change.
