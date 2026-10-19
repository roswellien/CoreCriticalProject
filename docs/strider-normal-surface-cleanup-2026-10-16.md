# Strider normal-map surface cleanup R2

2026-10-16. User feedback: broad flat armor surfaces, particularly the head roof,
looked wrinkled and over-detailed in the12x normal preview. The existing authored
height atlases contained irregular fine surface noise, amplified by the normal
response. This revision targets that material defect on the detailed Strider.

## Change and fidelity boundary

Edited both technical height atlas pages through the built-in image_gen tool.
Plate interiors are smooth; existing seams, vents, bolts and housings remain.
Converted twelve height tiles to OpenGL normals using the prior crop/blur1/
derivative gain16 pipeline. A numerical slope noise floor flattens derivatives
at or below.06 and smoothly restores full response at.10. This deliberately
reduces minor surface relief while retaining strong mechanical transitions.
Blender Normal Map strength remains10.20, the12x reference from.85.

All22base-color PNGs and three shared relief groups (mech01, weap_hole, footpad)
remain byte-identical. Paint wear/scars/scorch/grime and baked source shading
are retained in the color artwork. The52-map package contains22color,15height
and15normal images. No new diffuse/weathering artwork or geometry changes.
The sampled roof plateau's mean tangent-normal angle from flat fell from
3.6213degrees to.31775degrees (91.2percent); this is a fixed local map sample
before shader strength, not a whole-model or global-strength reduction.

Both comparison passes use the SAME17,129-triangle detailed model and16moving
parts, original walk, camera and orbiting light. Geometry/UV hash is unchanged;
all336object/camera/light pose signatures match the source in both passes.
The earlier full336frame vertex-framing result carries across unchanged
vertices/camera. Close views intentionally crop legs/antenna tips and include
the complete roof. A neutral-gray roof pair removes base color on both sides
to isolate normal relief. The packed scene's15bound normal maps match the
delivered PNG bytes; all normal-node strengths remain10.20. R1 is preserved.

## Review and delivery

[HQ walking comparison](https://drive.google.com/file/d/1bhLiTvouPAXr8k59BpbTTLa4vZE2OM3V/view?usp=drivesdk).
[Cleaned12x walk](https://drive.google.com/file/d/1rWYrFDLe_gPjHL3ZDmoy6T4fdYNfjJP1/view?usp=drivesdk).
[Roof close-up](https://drive.google.com/file/d/1JPDBwAd-3ivYa4Q0BgPTafDBsYcDyoRG/view?usp=drivesdk).
[Neutral-gray relief comparison](https://drive.google.com/file/d/1cPKHzypBqoX8RKP4F2NPWp4b47NrJhML/view?usp=drivesdk).
[Organized Drive revision](https://drive.google.com/drive/folders/1hRkIHkTC-sJ0W41adAwYlzkSe52fkz6f). Eleven files in four folders verified
for name, MIME type, parent and remote/local byte size. Local SHA256 hashes
recorded separately; no claim of remote checksum equality. Sharing unchanged.

Individual videos1280x960; comparison2560x1020 with60px header and no model
downscale. All336frames,30fps,11.2seconds; six original walk cycles and one light
orbit. H.264 CRF8/slow/grain/yuv420p/faststart from lossless PNGs. Three video
stream checks pass. PNG dimensions, ZIP integrity, all source/map pins and
local HTML references pass. Download video originals for detailed inspection.

Workspace: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/
mw3-strider-normal-cleanup-r1. Editable strider-smooth-plates-12x.blend,
textures/, full built-in edit prompts in generation-prompts.json, conversion/
render scripts, lossless frames, checks and comparison.html retained. This
material-only revision does not supply a new staticGLB; R1's old export remains.

Boundary advanced: wrinkled offline Strider relief -> smooth plate normals and
matched review. OFFLINE, NOT INSTALLED. Native visual/material integration,
weapon/damage/LOD and live performance checks remain. No native FPS claim.
No game launch, desktop screenshots, pilot/registry edits, runtime/launcher
changes or commit. Live context hashes unchanged; protected jobs/other work
preserved. Strict acceptance remains paused131/144, zero native credit.
