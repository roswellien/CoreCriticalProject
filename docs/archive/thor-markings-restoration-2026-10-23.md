# Thor default texture restoration — 2026-10-23

The local developer mech pack now uses revised default Thor/Summoner Body and
Variant color atlases at both detail levels. The installed authoring sources
were first compared against their BWTEX1 records: all five material records
matched. Original thor09–25 and thor_d01–06 maps provided the gray-green paint,
red/yellow chest insignia and yellow/black caution references.

The pass replaces warm cream armor with a muted gray-green finish, lightens
raised paint wear, adds a small adapted chest insignia and restrained worn
caution bands. Existing dark mechanical recesses and blue cockpit remain.
These markings are adapted to the donor geometry/UVs, not exact original UV
projection. Built-in image_gen produced the 1254 × 1254 Body and Variant edits;
submitted prompts, references and output paths are preserved locally.

Execution boundary: default replacement-model color resources on the existing
native path. Meshes, size, controllers, simulation, original firing origins,
normal payloads and alternate-skin color bindings are unchanged. No native
rebuild, installer/R2 publication or commit was performed. Acceptance remains
131/144; this does not close gameplay or model compatibility criteria.

Checks:

- Matched front/rear/close/unlit offline views at both detail levels preserve
  geometry/UV/pose and action digests. Sources retain 21 close-detail and 20
  lower-detail parts. Installed native meshes match their authoring payloads.
- Each BWTEX1 batch table is unchanged. Weapons, Window and MissileHead records
  remain byte-identical. The different 21/20 batch tables are preserved.
- Current native runtime SHA256
  `0a787590a4f12f24fd99d0b3e09ccebf1656f43f569bd4dadd98a02865999aa8`
  completed a 1750-frame Grasslands presentation budget using the confirmed
  Thor pilot/loadout, full 38-bank environment resources and candidate colors.
  Model logs contain 90 non-preview Thor LOD0 replacement records. Third-person
  native screenshots show the rear; front paint placement was checked offline.
- The earlier screenshot host failed at guest PC 0x7800160e before gameplay.
  A first current-host attempt selected saved Daishi; neither attempt counts
  as Thor validation. Both are retained with their original logs.
- Installed registry/payload SHA pins and launcher `--check` pass. Only the two
  Thor default color bindings changed; all other model records compare equal.
  Both authoring registries now reference the revised Body/Variant images.

Private assets, source pins, prompts, before/after renders, payload checks,
backups and installation receipt:
`local/work-ahead/thor-markings-20261023-r1/`.
Native evidence: `native-capture/thor-runtime-review/` beneath that directory.

Installed color payload hashes:

- Close: `f0d74de42979f5ad38c3191a15c0f023b3660e63967035e76ba19908d4c61023`
- Distance: `7b84a6fdc79aa69ec4e6bbcec1654eec6f03afb4eca5b4e5a8ca5a8e0f0ace8e`

Limits: live lower-detail transitions, extended motion, damage states and
combat/firing alignment were not covered by this stationary color review.
