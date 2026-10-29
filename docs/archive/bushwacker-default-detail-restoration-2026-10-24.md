# Bushwacker default texture follow-up — 2026-10-24

The default replacement-model Bushwacker already had a detailed worn set and
the approved white/red shark-mouth nose art. The original MW3 default tiles
confirm a pale grey/olive stock finish, blue glazing and stripe, ribbed vents,
round access parts and two small red rear service lamps. The dark gold/graphite
Commander Freya skin is a separate alternate and was not used as this default's
palette reference.

This pass retains the existing 4096×4096 Body UV atlas and the mouth pixels
exactly. It adds a brighter, cool metallic rub along exposed armor edges while
keeping recesses dark. The existing detailed machinery stays visible. The two
red lamps were placed on the replacement model's paired rear panel UVs after a
camera-ray UV probe, matching the cue from the MW3 `bushwacker13` tile.
Variant and Weapons received the same restrained edge treatment. Window and
MissileHead colors are unchanged.

Actual edited sheets and matched front/rear/unlit renders are under
`local/work-ahead/bushwacker-default-detail-20261024-r1/`. The mouth
protection mask comparison reported no altered protected pixels. Blender
reported unchanged geometry/UV/pose. Both LOD texture bindings in the local
optional model pack point to the new content-addressed BWTEX1 payload; its
batch table and the Window/MissileHead material records are unchanged. Both
local Windows views of the pack verified the payload and manifest hashes.
Source texture registries point to the new Body, Variant and Weapons sheets;
other chassis and all Bushwacker alternate skins remain unchanged.

This is a default replacement-model color pass. It changes no original-game
texture bank, normal map, geometry or gameplay execution boundary. Native
acceptance remains 131/144. An in-game visual check is still open.
