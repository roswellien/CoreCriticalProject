# Automatic world normal-map preview

Date: 2026-10-18. Continues the [stock material integration](stock-material-lighting-integration-2026-10-18.md).
The user requested broad terrain/object coverage and selected an automatic first
pass, to refine later. Original gameplay and geometry remain authoritative;
acceptance remains **131/144**. No original media or generated assets belong in Git.

## Texture source and material coverage

The preparer reads the **configured upgraded color banks**, not original game
texture banks. All 36 selected world banks are registered as upgraded in
`local/work-ahead/texture-launcher-audit-v2/configured-banks.json`. Their complete
SHA-256 identities are checked before and after preparation. Source rows come
from the existing world-scene inventory across Training and the five campaign
bank regions. No colors, banks, UVs or original producers are changed.

The prepared package contains 3,998 full-content texture identities across 1,191
world texture names and 11,010 selected bank entries. These include all 296 terrain
texture names in the inventory and 895 other world/object names. Case-insensitive
matching retains the original bank spelling and covers uppercase building entries. Identical color identities
share bindings. Byte-plane alpha textures include explicit RGB565, ARGB1555 and
ARGB4444 candidate identities; the live renderer must match complete dimensions,
pixel format and every stored color byte before admitting one. Candidate identity
preparation is not proof that every alpha conversion occurs in native play.

Sky, identified water/shore textures, effects sequences and entries without
world-scene reference evidence are excluded. Inventory classification is retained
with its documented limits. Blended draws, frontend/HUD and unsupported geometry
retain their existing paths. This is broad catalog preparation, not a claim that
every game material or mission has been observed rendering with normals.

## Automatic relief

[The offline preparer](../tools/remaster-launcher/prepare_world_normals.py) derives
a conservative height estimate from the upgraded color pixels. Periodic filtering
removes broad illumination and suppresses small texel noise; tangent normals use
the stored texture-V direction. Maximum slopes are 0.35 for identified terrain
and 0.15 for other objects. Object atlases have a flat two-pixel border.

These are **color-derived estimates**, not individually authored or physically
recovered relief. Painted markings, reflections and baked lighting can still
produce false detail. Existing authored material maps and explicit exclusions
take precedence over automatic estimates. Future refinement can replace individual
materials without rebuilding the world package or altering their color artwork.

The first pass caps normal images at 128 pixels on their longest side to bound
memory and loading costs; upgraded base-color textures retain their resolution.
The package occupies approximately 148.05 MiB across 63 BWSNR2 pages. Pillow and
NumPy are offline preparation dependencies already present in the bundled tooling;
their actual versions are recorded. A project-authored hash helper accelerates
complete source-byte matching and is not a dependency of the game executable.

## Native boundary

`MW34_WORLD_NORMALS` selects a `MW34SNP1` manifest of relative BWSNR2 page names.
The [page adapter](../tools/remaster-launcher/native-overrides/world_normals_pages.inc)
loads validated headers for registration, then reads a page's image payloads only
on first use. Disabled normal mapping allocates no automatic normal images while
retaining geometric sunlight admission. Per-surface version/dimension/format/pitch/
backing caches prevent repeated source hashing on unchanged draws.

The manifest admits at most 256 pages / 16,384 unique keys / 512 MiB, with a
16 MiB per-page limit. Page names cannot escape their directory. Full reads retain
the existing normal-image bounds, complete hashes and EOF checks; changed page
keys are rejected. Unknown configured pages and corrupt pixels fail visibly.

Registered cutout world textures can now receive normal-mapped sunlight while
retaining their original alpha test. Existing blend, depth, world-camera and
frontend guards run first. The change does not replace transparency or treat
sky/effect sprites as solid surfaces. Renderer shaders and SPIR-V are unchanged.

## Sky treatment

The existing Big Lake sky shader shades a distant textured dome and horizon from
view direction, sun direction/color, ambient fill, glow and haze. Its sky branch
returns before ordinary surface-normal lighting. Terrain-style normal mapping
would shade the dome as a physical shell rather than create cloud volume.

Cloud-specific normal or height layers are possible future work with a dedicated
sky lighting model. They would be an approximation of cloud shape, separate from
atmospheric scattering and volumetric clouds. This continuation keeps sky textures
on the existing shared sunrise/sunset/midday atmosphere path.

## Original camera activation and Training effects

The first expanded Training control exposed an existing lighting assumption at
frame 733: it treated the renderer camera globals as an unchanged copy of the
current world camera node. Static inspection of the pinned original executable
shows that `520B00` also receives temporary stack matrices from `5A5B40` and
`5A6110`, while Euler construction reuses the forward matrix buffer.

The adapter now observes the original `520B00` activation, checks its complete
12-word copy and sign conversion exactly, and retains the resulting forward and
inverse matrices in host memory. World lighting requires the activation source
to be the authenticated world/zoom camera node and the active inverse to match
exactly. Temporary effect cameras do not receive world-surface lighting. No
floating-point tolerance, guest-memory mutation or replacement producer is used;
the original body executes outside the host FP preservation scope.

## Focused checks and local evidence

Local workspace: `C:/Users/jcbla/MW34SunTests/world-normal-integration-r1/`.
`assets-r2/receipt.json` records each upgraded source bank, selected aliases, source
format transformations, generated normal identity and exclusions.
`generation-source-check.json` confirms that no original game bank supplied pixels.

Authored C++ controls exercise the actual page adapter: lazy allocation, unused
page retention, mapping-disabled registration, authored precedence, corrupt image
rejection and path escape rejection. Python fixtures exercise flat/capped relief,
aspect and tangent-axis behavior, exact upgraded-bank identity, sky exclusion,
alpha candidates and read-only source preservation. Native comparisons and the
selected preview build are recorded in `native-comparisons-release.json`.

The selected executable SHA-256 is
`95716007bbe79483c046ab1bb94f7cc93676171baa47696cbbb7d1d73877c8d2`.
The isolated Normal Mapping Preview profile retains all 30 model bindings,
detailed MW3 Strider, reviewed stock-material catalog, remastered menu and shared
sunset default. Sunrise and midday shortcuts use this same profile. The regular
main Play and Big Lake profiles were not changed.

- Training world/stock controls each reached 1,200 presentations with identical
  original draw triples. Training observed 60 automatic material identities,
  loading six pages / 14.35 MiB of CPU normal pixels.
- Instant Action world/stock/flat/zero/off controls each reached 1,800
  presentations with identical original draw triples. World mapping observed
  49 automatic identities plus one authored identity that retained precedence;
  eleven pages loaded / 26.64 MiB of CPU normal pixels. These are CPU page figures,
  not total GPU residency or a performance benchmark.
- All three no-world captures match the previous stock-material release byte for
  byte. All three flat/zero-strength captures match each other byte for byte;
  disabled mapping loads no automatic pixel pages. Zero strength still loads
  registered pages but skips normal sampling in the existing shader.
- GPU fixtures pass actual camera capture, temporary effect exclusion, exact copy
  and inverse alteration rejection, FP/LastError preservation, lighting, fog,
  HUD, normal equivalence and caching. Three Python generation tests, four C++
  material/page controls and two shared lighting-preset tests pass.
- The integration recipe reproduces all 90 host source files semantically; one
  retained diagnostic upgrade has a duplicate comment block. The 37,201 native
  object-list entries and protected heap/photo/replay/turret/guest-memory services
  are unchanged. Source hashes are pinned in the local preview snapshot.

This advances upgraded-color world materials into the native lighting renderer.
It does not establish full mission completion, whole-game material appearance,
all alpha conversions, model damage/LOD fidelity or a performance improvement.
Native runs used isolated copied pilots and verified protected originals.
Acceptance remains **131/144**. No commit or push was made.


The ordinary preview launcher passed its profile check and a two-presentation
startup smoke in `local/remaster/runs/20261018-085213-322`. Its effective settings
select sunset, the upgraded menu background and the new world manifest. The
bounded exit is the expected presentation-budget termination. Final verification
rechecked all 90 source pins, all 63 page hashes and protected originals.

Launch with `Play MW3 - Normal Mapping Preview.cmd`, or use its existing Sunrise
and Midday variants. This remains the isolated testing profile before main Play
promotion.


## Firefly texture and coverage clarification

A follow-up audit matched complete live color bytes from `runs/world-r5` against
12 Firefly base-skin bank entries. These include `firefly01` at 2048x1024 and
`firefly06` at 1024x2048. The result is retained locally in
`firefly-texture-audit.json`; this verifies the upgraded base skin in that
controlled run, not an unspecified player observation or alternate skin.

Lettered Firefly skin entries are smaller (for example, `firefly01_b` is
256x256). The Firefly artwork package documents those as 8x upgraded exports
selected for legacy archive capacity, so smaller dimensions alone do not mean
original artwork. Those alternate identities are not covered by the reviewed
base-skin normal catalog. Shared excluded parts also remain unchanged.

Normal mapping is broadly available in the isolated preview, not universal for
every material, alternate skin, transparency path or mission. Full coverage and
visual sharpness should not be inferred from catalog counts or image dimensions.
