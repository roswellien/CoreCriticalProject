# Big Lake directional sun test

Remote review screenshots belong on Google Drive, as requested by the user.
The comparison and four full-resolution views are uploaded in
[Big Lake directional sun test](https://drive.google.com/drive/folders/1tN9VCLV95oWMAaaQS3BV5H6_cx8jpoxN)
under MW3 Remaster — Project Previews.
[Open the comparison](https://drive.google.com/file/d/1Wi5jU6C827MBxHNd6Kru6NkdCe2X5dDL/view).

> **Update 2026-10-16:** GPU replacement mechs now cast sun shadows (on by default in this
> launcher; `-NoShadows` disables). See [Big Lake mech sun shadows](big-lake-mech-shadows-2026-10-16.md).

Authorized 2026-10-16. A separate native Big Lake test instance now has a
per-pixel directional sun and constant ambient fill. This is a direct-light
prototype, not bounced global illumination. Shadow maps, normal textures,
physically based water/specular materials and a changing sky are not implemented.

## Launch and controls

Run [Play MW3 - Big Lake Sun Tests.cmd](<../../launchers/Play MW3 - Big Lake Sun Tests.cmd>),
then choose Instant Action / Big Lake. The copied pilot already defaults to
**BIG LAKE / Battle**; an original-menu capture confirms the selection.
The test uses a separate game/pilot/registry under
`C:/Users/jcbla/MW34SunTests/big-lake-r1/instance/MW3`, with its native host,
logs and captures beside it. The registered configuration is the ignored local
`local/remaster/big-lake-sun-tests.json`.

Default preset: azimuth 225°, elevation 35°, direct strength 0.85, ambient 0.30.
Graphics are 3440×1440, FXAA, AF16, draw 1200 and fog 1100, using the frozen
39-bank/seven-model test assets. These are local development artifacts and
require the existing admitted original executable, providers and resource pack.

Optional launcher arguments apply on the next launch:

```powershell
& '.\Play MW3 - Big Lake Sun Tests.cmd' -Azimuth 45 -Elevation 35
& '.\Play MW3 - Big Lake Sun Tests.cmd' -Strength 1 -Ambient 0.35
& '.\Play MW3 - Big Lake Sun Tests.cmd' -Original
```

`-Original` disables the new light while retaining the same GPU geometry profile.
Normal interactive launches use the live clock and ordinary original menus.
The developer-only `-Frames` / `-Script` arguments enable bounded replay tests;
their 50 ms virtual clock is not used in ordinary play.

## Rendering boundary

The stable alpha geometry path remains enabled, with CPU projection bypass **0**.
Original simulation, animation, clipping, culling and geometry producers continue
to execute. No new AI, weapon, damage, visibility or save-state writes are added.

- GPU replacement models and admitted original-world meshes pass transformed
  normals to the fragment shader. An inverse-transpose handles instance scale
  and orientation; sun direction is expressed in world coordinates.
- Remaining opaque textured world draws retain their original TL geometry.
  The vertex shader reconstructs visible positions from reciprocal depth and
  the captured projection/camera. Fragment derivatives supply geometric face
  normals, oriented toward the visible surface. This covers the Big Lake ground
  and hills without pretending they have migrated to retained raw geometry.
  It supplies no off-camera/occluded casters, smooth authored terrain normals or
  general shadow scene representation.
- Opaque world receiver admission requires the actual cell traversal, world/zoom
  role, enabled depth test/write, texture, finite positive reciprocal depth and
  an authenticated bound camera. Blended/alpha-tested draws and unrelated
  preview/HUD contexts retain their existing path. Opaque water can receive this
  diffuse light; its animated texture is retained and no water BRDF is added.
- Sun shaders neutralize the original CPU-lit vertex RGB for textured original
  world receivers, then light the texture result. Replacement models use their
  batch tint instead of the old fixed camera-space shade. Painted shading in
  textures remains; this is not an albedo/material-remaster result.
- Lighting precedes the existing fog operation. Original alpha, texture
  combination and fog coefficients are retained. The inherited replacement-model
  fog gap is not repaired by this experiment. Sky and HUD keep their original
  shaders, and the sun does not insert a visible solar disc.

The 128-byte model push block is unchanged. A separate dynamic uniform binding
holds per-draw light/normal or TL reconstruction data. Uniform strides honor the
device alignment, scene fences protect buffer/descriptor reuse, and original TL
vertex bindings restore after model draws. GPU geometry is reused rather than
uploaded again for each light calculation. The prototype makes no FPS-gain claim.

## Camera and FP contracts

The initial live attempt found zeroes in an unused scenery world-matrix cache.
It stopped visibly. A parent-only reconstruction also rejected a non-mesh
ancestor; neither attempt is treated as successful lighting. The final path
uses the original active camera and already captured draw transforms instead.

Read-only original-code inspection establishes that `4F444A` copies the camera
matrix to camera data +0x44. `520B00` changes its Y/Z columns into the renderer
basis at `73FC00`, then produces the inverse at `73FBC0`. The final adapter reads
the actual `73FC00` camera-to-world matrix and checks it against the authenticated
camera after that exact axis conversion. Using the unconverted matrix inverted
terrain up; the normals diagnostic exposed and corrected it. No guest cache
update, transform repair or alternate camera guess is performed for lighting.

Actual main/zoom camera ownership is checked, including the original separate
zoom owner. Float work runs under the host FP environment inside a complete
FXSAVE/FXRSTOR guard, with XMM clobbers declared and LastError restored. No original
body runs inside this guard. Invalid transforms, normals or required camera
bindings fail visibly. This is a renderer extension, not original-code fallback.

## Validation and artifacts

Authored CPU/GPU fixtures pass on RX 9070: inverse-transpose scale/shear/reflection,
singular rejection, actual capture-adapter camera cancellation and Y/Z conversion,
unauthenticated/preview rejection, zoom ownership, unchanged mock guest memory,
FP flags/rounding and LastError, camera-invariant lighting, ambient-only backfaces,
model/world agreement, TL terrain normals across camera turns, fog ordering, HUD
exclusion, geometry reuse and actual sunlight draw counters.

Native live cases use original UI input and private Big Lake copies at the full
graphics profile. Final captures include normal diagnostics and opposite 45°/225°
sun angles. The accepted 1000-frame comparisons preserve every original
frame/draw/hash record. After the final FP compiler-clobber fix, the sun run still
matches the control records and prior sun captures exactly. One sun-off run first
differs in original hash at frame 487; it is retained as `final-off`, with cause
unestablished. Its repeat, `final-off-repeat`, matches all 1000 control records
and both control captures exactly. This is not a claim of universal replay stability.
Sun-off captures at frames 600 and 900 match the pre-sun alpha control byte-for-byte.
The normals view shows world-up ground and mech roofs; changing sun direction
changes hillside and mech-face illumination. At frame 1000, the tested sun path
records 109,850 retained-world, 326,095 TL receiver and 21,877 replacement-model
sun draws. These are cumulative draw calls, not distinct objects or triangles.

All cases end at intentional frame budgets, not a claimed normal-quit or mission
completion result. The separate launcher itself also reaches 1000 Big Lake frames
using its registered private game directory and default sun preset. Vulkan
validation layers are unavailable (create-instance -6); these fixtures/native
checks do not claim validation-layer coverage. Near-clipped replacement batches
retain their original CPU branch, and live zoom, damage/LOD, reload and sustained
gameplay lighting remain broader follow-up checks.

Local evidence: `C:/Users/jcbla/MW34SunTests/big-lake-r1/validation.json`,
`published-profile.json`, fixtures, source/build logs, original-menu map capture,
native captures and `comparison.png`. The ignored profile records the final
executable hash. Earlier failed/partial prototypes remain local and separate.

The existing Remaster/alpha launcher profiles and protected original pilot,
registry and Mission 2 save hashes remain unchanged. No original media or generated
game source is added to the repository. Acceptance remains **131/144**; no commit
was made. The boundary advanced is native visible world/model geometry to
world-fixed per-pixel directional lighting, with an explicitly limited TL receiver
bridge. Dynamic local lights, normal mapping and shadow collection remain next work.
