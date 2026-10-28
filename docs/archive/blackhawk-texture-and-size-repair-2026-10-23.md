# Black Hawk stock textures and replacement size

The evolution video's middle stage did load upgraded texture records, but those
records used the older soft, source-anchored artwork. The sharper existing
authored primary Black Hawk atlases are now used for the twelve `blkhwkNN` body
families in both `rmechtex` banks: 24 records. Each record retains its existing
dimensions, descriptor, UV contract and RGB565 encoding. All other bank records,
including alternate paint schemes and damage textures, are byte-identical.

The optional MW5 Nova replacement is uniformly enlarged by 10% at both LODs.
Identical-camera in-game views now place its head and shoulders much closer to
the original. This is a silhouette adjustment: the original and donor export
bounds were already about 8.30 units tall, and different foot depth and stance
made their projected silhouettes differ. The change does not claim identical
foot outlines or identical donor/original proportions. It preserves the approved
donor proportions rather than reinstating the rejected stretched-thigh fit.

Bone rest translations and bone-local positions receive the same scale about
the donor ground origin. Rest rotations, normals, UVs, visibility/material
bindings, original motion references and gameplay displacements are unchanged.
The current native visual two-link solver remains in use. Original collisions,
weapons, loadouts and simulation are unchanged.

## Local installation and checks

- New immutable mesh payloads are installed in the existing MW5 model pack;
  its registry and integrity table identify the new hashes. All other chassis
  records, Black Hawk textures/normals and alternate paint bindings are retained.
- The authoring registry points to the revised close/distance mesh candidates.
  The main local launcher selects the new meshes and revised texture-bank index.
- Both installed model packs validate together: all 18 chassis remain available.
- A 225-time source walk check, including between-key samples, retains rigid leg
  lengths; maximum measured error is below 0.000001 model units. Unreachable
  foot goals fail the check rather than being stretched.
- In-game original, sharper-stock and enlarged-replacement front views were
  reviewed at the same Grasslands spawn, sunset settings and camera coordinates.
  The enlarged standing capture reports no visual reach clamp.

Private build inputs, original media, scripts, backup registries and evidence:
`local/work-ahead/blackhawk-repair-20261023-r1/` and
`reports/blackhawk-repair-20261023/`. Neither original media nor generated game
code belongs in Git.

## Capture boundary

The replacement video uses the current October 23 capture host, the approved
ten-second opening and original MW3 music. It preserves current menu and world
resource bindings and enables world normal mapping across all three stages.
Only the stock Black Hawk's identified normal bindings are disabled for the
two stock comparison stages. Source recording checks require 1,680 / 1,680 /
3,120 frames, with frame dumping disabled to avoid readback gaps.

All three source frame counts passed. The 1440p60 master and 1080p60 posting copy
each contain 6,361 frames over 106.016667 seconds and pass full decoding. Reviewed
the opening, transitions, front/rear views and endpoint. The sharper texture
stage is visibly distinct. The thumbnail uses the corrected views and omits
the green ground targets. The final 1440p master is retained locally under
`reports/blackhawk-evolution-repair-20261023/blackhawk/`.

The six existing [Drive package files](https://drive.google.com/drive/folders/1SIuoOvQEJDnQ6gP17fhNyiXvtCwLjikW)
were updated in place, preserving file IDs and folder placement. Metadata
readback verifies their sizes and parent folder. No ZIP or YouTube publication.

This advances local visual assets and their in-game presentation only. It does
not advance the native host/menu/Training execution acceptance boundary.
Acceptance remains 131/144. No commit or public release is performed.
