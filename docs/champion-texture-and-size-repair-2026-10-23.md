# Champion stock textures and replacement size

Champion's old evolution video used the soft source-anchored texture pass on
the stock chassis. The replacement bank uses the sharper existing authored
artwork for Champion's primary body atlases and their existing damage aliases:
27 existing records across the two mech banks. Damage-named records also supply
visible undamaged surfaces; replacing only the ordinary body names left the
cockpit sides soft in the first in-game check. The final check includes those
linked records and visibly resolves the cockpit panels and vents.

The source inventory's actual alias relationships are retained: `champi_d02`
uses `champi_d01`, and primary `champi_d03`/`champi_d04` use `champion08`.
Descriptors, dimensions, RGB565 layout and UVs remain unchanged. Generic shared
mech textures, alternate paint schemes and every other bank record are retained
byte for byte, including the preceding Black Hawk repair.

The MW5 Champion replacement is uniformly enlarged by 5% at both LODs about the
donor ground origin. Identical-camera front views align the main body height much
more closely to the original. Different antenna and foot geometry remain donor
features; total exported bounds alone were not used as the visual fit criterion.
Bone rest translations and bone-local positions receive the same scale. Rest
rotations, UVs, normals, material bindings, original motion references and gameplay
displacements are unchanged. Original collision and weapon nodes are unchanged.

## Local validation and installation

- Reviewed original, upgraded-stock and enlarged-donor front views at the same
  Rolling Hills Instant Action spawn, sunset preset and camera coordinates.
- Checked 225 source walk times, including between-key samples, with Champion's
  existing general donor leg solver and actual toe-controller mappings. Rigid leg
  length error remains below 0.000001 model units; unreachable targets fail.
- Installed immutable new mesh files at both LODs in the existing MW5 model pack
  and updated its registry/integrity entries. Other chassis and all texture,
  normal and alternate-paint payloads are unchanged.
- Both installed model packs validate together, retaining all 18 chassis. The
  local profile changes only Champion's two mesh bindings and the cumulative
  texture-bank index. The Black Hawk repair and graphics preferences remain.

Private inputs, backup registries, build scripts and evidence remain under
`local/work-ahead/champion-repair-20261023-r1/`,
`reports/champion-repair-20261023/` and
`C:/Users/jcbla/MW34SunTests/champion-repair-20261023/`.

The video uses the current October 23 capture host with current menu/world
resources preserved, world normal mapping enabled throughout, and frame dumping
disabled to prevent recording gaps. The original and upgraded-stock comparison
stages exclude only identified Champion relief bindings; other world materials
are retained. The approved ten-second opening and original MW3 background music
are reused.

All source recordings passed their exact frame counts: 1,680 / 1,680 / 3,120.
The final replacement pass reports no visual reach clamps. All three receipts
identify the same current capture executable and retain the same menu/world
resource bindings.

The 1440p60 master and 1080p60 posting copy both pass full decoding, with 6,361
frames over 106.016667 seconds. Reviewed the opening, matched transitions,
front/rear views and endpoint. The full master is retained under
`reports/champion-evolution-repair-20261023/champion/`.

Updated all six existing [Champion Drive package files](https://drive.google.com/drive/folders/1685B_XnL9NkQX2Pm741unnSvVKsy9UQb)
in place, preserving file IDs and folder placement. Metadata readback verifies
their sizes and parent folder. The thumbnail uses the corrected views. No ZIP
or YouTube publication was performed.

This advances local visual assets and in-game presentation only. It advances
no native execution acceptance boundary; strict acceptance remains 131/144.
No commit or public content-pack release is performed.
