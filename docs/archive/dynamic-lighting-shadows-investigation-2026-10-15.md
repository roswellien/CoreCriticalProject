# Dynamic lighting and shadows: feasibility investigation

2026-10-15. Source inspection and API reference research only. No renderer,
launcher or gameplay change; no native execution boundary advanced. The current
play build remains the Mech Lab canvas build. Strict acceptance stays 131/144.

## Findings in the current native renderer

The inspected executable profile points to
`local/remaster/gpu-native-mechlab-canvas-r1/build/entry_commandline.exe`, SHA256
`ed568b419c2ac0b465950016bf9be3cb0e2f988d73bae01c76e183ee12ec41df`.
Its pinned host snapshot is the authority for the current seven-model build;
some reusable override templates have older roster declarations.

| Surface | Existing implementation | Missing for modern lighting/shadows |
| --- | --- | --- |
| Original world geometry | Game-produced transformed-and-lit vertices: screen XYZ, reciprocal W, diffuse/specular colors and UV | General world-space geometry, surface normals, material identity, reliable camera/instance provenance and light sources |
| Replacement mechs | Mesh positions, normals, UV and per-instance local-to-camera transform; persistent GPU geometry | Per-pixel lighting, a consistent world/light coordinate contract, tangents/normal textures, shadow participation |
| Fragment stage | One color texture; fixed-function color/alpha combination, specular addition, vertex fog, alpha test | Light/material buffers, normal-map sampling, light attenuation, shadow sampling |
| Vulkan resources | Color/depth targets, geometry buffers, texture cache, FXAA, GPU HUD | Sampled shadow depth images, shadow pipelines/descriptors, pass scheduling, synchronization and caster collection |

Evidence:

- `tools/m4-crt-heap-carry/d3d_scene.vert`: 32-byte TL input explicitly has no
  original position/normal attribute. Colors are already calculated upstream.
- `tools/m4-crt-heap-carry/d3d_scene.frag`: one sampled color image; no light list
  or shadow map. Specular addition alone is not a modern specular material model.
- `tools/remaster-launcher/native-overrides/model_scene.vert`: replacement
  vertices receive `0.35 + 0.65 * max(dot(light, normal), 0)` shading using a
  fixed vector in camera space. The CPU near-clip branch in
  `mesh_override_stage.inc` has corresponding shading. Neither branch receives
  a moving world light or computes light occlusion.
- Current frozen `vk_scene.hpp`: `ModelVertex` is 32 bytes, `ModelPush` already
  occupies 128 bytes, descriptor layout has one color sampler, and depth targets
  are created as attachments/transfers rather than sampled shadow maps.
- `mesh_override_stage.inc`: source model-view stack and validated original
  hierarchy already provide a useful model capture point. The existing render
  hooks include 0x53F2E0 and 0x51FB30. These are model integration points, not
  proof of a complete terrain/building/effect representation.
- Asset parsing (`tools/asset-inventory/analyze_training_mech_uvs.py`) recognizes
  normals and variable light records. This is a recovery lead; their presence
  does not establish runtime dynamic illumination or shadows.

**Scope of the absence finding:** this inspected Vulkan path has no modern
dynamic-light/shadow-map implementation. It does not prove the original MW3
has no changing vertex colors, projected/blob shadows, emissive-looking sprites
or other lighting effects. Those original producers need separate inspection
before replacing their appearance. Pirate's Moon light-map/headlight evidence
in `pirates-moon-initial-comparison.md` must not be treated as MW3 evidence.

## Recommended architecture

Keep enhancements in the host renderer behind independent options. Original
simulation, weapon hits, AI visibility, damage, animation and save semantics
continue unchanged. Read actual event/object state to drive visual lights.
Never advance or rerun the original update/render producers to obtain a light
view: capture host geometry and render that geometry in extra passes.

1. **Establish geometry and material contracts.** Capture world/camera transforms,
   original positions/normals and stable material identity before projection.
   Identify terrain, opaque buildings, mechs, cockpit, sky, sprites, water and
   HUD separately. Validate axis, units, near plane, zoom and mirror handedness.
   Terrain must be able to receive a mech shadow; a model-only prototype cannot
   establish this. Recover the relevant world/terrain producers next.
2. **Introduce enhanced per-pixel lighting.** Start with one known directional
   light and a small bounded list of unshadowed local lights. Replacement mechs
   already have useful geometry; terrain/buildings need the additional capture.
   Use a buffer for lights/materials rather than extending the already 128-byte
   model push block. A forward lighting path is a reasonable initial design;
   tiled/clustered lighting becomes useful if measured light counts justify it.
3. **Add one directional shadow map in a bounded live scene.** Render opaque
   casters from the light, then sample the depth map during direct lighting.
   Include replacement pose, lost parts and LOD state. Preserve ambient fill:
   shadow visibility should attenuate direct light, not make everything black.
4. **Expand to outdoor shadows.** Investigate stable cascaded sun shadows for
   wide outdoor views, with an independently configurable shadow distance.
   The 1600-unit scenery setting need not imply detailed shadows to 1600 units.
   Start with nearby coverage and fade; choose cascade count/resolution from
   measured quality and cost, not an assumed universal preset.
5. **Bind actual weapon/explosion lights, then normal maps.** First prove source
   position, color, lifetime and attachment identity. A glowing sprite is not
   automatically an illumination source. Keep most short-lived local lights
   unshadowed initially. Normal maps require verified UV/tangent handedness,
   linear data textures, suitable format/mips and material bindings. Existing
   authored normal-map drafts need mapping to the actual original/replacement
   meshes; their presence is not runtime support.

Normal mapping shares the new lighting/material foundation but is not a
prerequisite for dynamic light or geometric cast shadows. World-space geometric
normals are sufficient for the first version. Existing textures contain painted
shading; color-space handling and material tuning must avoid double lighting.
An enhanced color target may be useful for bright lights, but HDR/tone mapping
is a separate decision, not a prerequisite for a first diffuse-light prototype.
Original RGB565 readback and HUD composition contracts still need to work.

## The principal shadow risk: missing casters

### Moving the geometry handoff earlier

The actionable upgrade is a host-owned retained scene representation. Instead of
receiving only screen-space triangles, Vulkan should receive cached local-space
vertex/index buffers (position, normal, UV, tangent), material bindings, per-frame
instance transforms/visibility and camera/light data. Mesh data changes only on
asset load or an actual deformation; rigid articulated mech parts can update
their matrices without uploading all vertices. Source animation and destruction
still decide those matrices and which parts exist.

The current replacement-model path already demonstrates GPU-resident mesh data
and vertex-shader projection. Extend that design to original meshes, buildings
and terrain; do not convert the whole engine to compute shaders first. Standard
vertex/fragment shaders can perform the initial transforms, normal mapping and
lighting. GPU culling/indirect draws are later optimizations if justified.

The migration order is: recover stable asset/instance ownership; cache opaque
geometry with material/normal data; render enhanced objects with GPU transforms;
add per-pixel lights and normal textures; provide pre-camera-cull caster access;
then add shadow passes. Keep original UI/sprites on their established path.
During bring-up the original render producers may still run so their side
effects and original draw comparisons remain observable. Only bypass CPU
transform/lighting/clipping work after proving that specific work has no required
simulation or guest-state side effects. Early bridge versions may duplicate work
and are not automatically performance improvements.

This moves the rendering boundary, not gameplay ownership: CPU original logic
continues to own physics/collision, AI, weapons, animation decisions and saves;
the GPU owns enhanced vertex transformation, rasterization, per-pixel material
lighting and shadow-map rendering. A renderer upgrade does not require replacing
the faithfully recompiled simulation.

Current commands largely describe what survives the player's camera/frustum and
original terrain visibility selection. A building behind the camera can cast
a shadow in front of it; reusing only current visible draws will make shadows
disappear when turning. Inverting visible TL projection can help a diagnostic
receiver prototype but cannot recover culled casters, original smooth normals
or original unclipped mesh topology.

Collect opaque casters before view culling, or recover a separate read-only
scene/terrain traversal for the light volume. Track asset lifetime and animated
transforms; invalidate on mission unload and destruction. Persistent caches
must not keep destroyed limbs/buildings casting shadows. Alpha-tested foliage
needs matching cutout sampling; ordinary blended smoke should not become solid
shadow geometry. HUD, Mech Lab, cockpit and zoom scopes need explicit policy.

## Performance and verification

Dynamic illumination and shadow cost must be measured separately. Extra light
math and shader resources differ from the additional geometry passes required
for shadows. Omnidirectional shadowed lights can require multiple views per
light; do not begin with every missile/explosion casting shadows. Ray tracing
is unnecessary for the initial raster shadow design and would add another
geometry/acceleration-structure integration problem.

There is no measured FPS cost yet. The prior scenery-distance measurements
cannot predict shadow overhead. Record matched routes at 3440×1440, FXAA/AF16,
1600-unit scenery: existing rendering, lights only, then each shadow preset.
Measure CPU/GPU time, median/tail presentation time, upload volume, memory and
caster/draw counts. Reuse cached GPU geometry; avoid per-frame CPU readback.
Negotiate an acceptable budget after observing actual results.

The first live acceptance target should be deliberately small: a moving mech,
terrain receiver and opaque building under one light, with a moving local light.
Check foot contact, camera rotation with stationary light, self-shadow bias,
off-camera casters, terrain slopes, damage/LOD changes, zoom/cockpit views,
near clipping, fog ordering, mission reload and clean teardown. Test both model
projection branches. Normal-map tests additionally need neutral material and
grazing/moving-light views to expose inverted Y, seams and painted-depth errors.

Every option disabled must preserve original-compatible CPU images and original
draw records. Settings should independently expose dynamic lights, shadows and
normal mapping only after implementation; shadow quality/distance should remain
independent of scenery distance. No production defaults change in this study.

## Primary implementation references

[Khronos: multiple render passes / shadow mapping](https://docs.vulkan.org/samples/latest/samples/performance/multithreading_render_passes/README.html)
demonstrates a light-view depth pass followed by camera-view lighting and the
required image synchronization. This is API guidance, not a performance estimate
for this game.

[Sascha Willems: cascaded shadow mapping source](https://github.com/SaschaWillems/Vulkan/blob/master/examples/shadowmappingcascade/shadowmappingcascade.cpp)
provides a concrete Vulkan reference for layered cascade depth resources and
split light matrices. No external code or dependency was imported.

Existing project material context: [authored normal-map pilot](work-ahead-material-pilot.md).
