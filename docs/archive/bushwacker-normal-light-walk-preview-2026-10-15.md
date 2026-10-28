# Bushwacker walking normal-map and light preview - 2026-10-15

The user requested a Blender demonstration with normal maps, walking and a light
moving around the mech. This is an isolated offline material/animation preview;
it does not modify the game renderer, launcher, registered models or live textures.

The R7 worn prototype scene already retained eight synchronized animation
bindings covering the main rig, weapon attachments and cockpit glass. Their
existing57-sample walk has56intervals at30fps. Six repeats supply336frames,
11.2seconds of walking in place. Sampled rig/bone/glass matrices at five points
in each of three repeats have maximum difference0 from the original cycle.
This validates looping of the retained animation, not new gameplay motion or IK.

The retained Body, Variant, Weapons and Window donor normal maps are used as
Non-Color, OpenGL tangent-space data with UVMap explicitly selected. Their
strength is.85 except Window.3. The R7 base colors are unchanged. Roughness and
metallic are illustrative constants. The newly painted gouges are color only;
this preview does not claim their relief has been authored into normal maps.

A soft area light makes one full orbit during the clip, with weak fixed fill
and a ground plane. Blender5.2.2 Eevee renders1280x960 at30fps. This is Blender
lighting/shading and shadows, not evidence of native game support or comparable
game FPS. Baked color shading may need adjustment for future dynamic materials.

Ignored workspace:
`local/work-ahead/mw5-bushwacker-extract/normal-light-walk-r1/`.
It contains the packed scene, frame sequence, video/GIF, a same-pose/light normal
toggle comparison and an orbit contact sheet. Source texture/scene/registration
pins, geometry/UV checks and processing metadata remain local.

[Organized Drive preview folder](https://drive.google.com/drive/folders/1Q5CAhOLFr-vebh4DyDHe2O-cZeYn7lhK).
All seven uploads were read back to verify filenames, IDs and destination folder.
[Full-quality video](https://drive.google.com/file/d/1BPoOzVdjpvaamxwnfbszJ8AyMAMv-wgO/view)
and [normal toggle](https://drive.google.com/file/d/1BvmhC5-CtIhwZf-X7yycqn5O_KYVxXgP/view)
are included. Video validation confirms336frames,1280x960,30fps and11.200seconds.
The smaller GIF has90frames. The normal toggle changes115572pixels by more than
4/255 in at least one channel. Geometry/UV and source pins remain unchanged.
The native execution boundary remains unchanged. No game launch, desktop
screenshots, pilot/registry edits, commit or native acceptance credit.
Accepted131/144; strict lane stays paused.
