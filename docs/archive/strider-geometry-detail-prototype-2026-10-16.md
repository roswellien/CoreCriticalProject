# Detailed original MW3 Strider prototype R1

2026-10-16. The user found the original Strider's normal-map test less effective
than Avatar/Owens/Firefly and authorized adding model detail using available
MW3 references. The original MW3 silhouette, proportions and controls are the
design authority. This is an authored optional prototype, not a newly discovered
MW5/MW4 donor or a stock gameplay replacement.

## Geometry and materials

The original has 759 triangles in 16 rigid moving geometry parts. The prototype has
17,129triangles, merged into the same 16 controller-owned parts. Original geometry,
UVs and animation curves remain intact in the packed comparison scene.
Added 60 source-textured armor layers, five cockpit frames/glazing panes,
12 physical vent regions/louvers, two round port collars and 12 bearing/hub covers
plus their fasteners on existing thigh/knee/ankle controls. Original broad
surfaces receive edge bevels/weighted normals. No extra joint, limb fitting,
stretch or moved gameplay firing point. Feature placement follows existing UV
hardware and the intentional source UV repeats outside0..1.

The new joint covers are visual bearing caps at original joints, not a revised
skeleton. The vent/port cavities are shallow facade wells with the original core
behind them, not modeled internal machinery or a cockpit interior. Added armor
can overlap the retained core; this is assembled game geometry, not a watertight
manufacturing mesh. Complete damage/debris/LOD shapes are not authored here.

All 52 copied color/normal/height PNGs retain their previous bytes. No new texture
generation. Body response stays at 12x (Blender Normal Map Strength 10.20).
Cockpit glazing uses existing color artwork with a smooth material/no connected
normal map; the original tiny untextured white head face is blue in the detailed
version only. Its coordinates/control stay unchanged. New edge, joint and seal
materials use recorded procedural constants. The initial draft is retained in
initial-draft; thinner frames, smooth glass, blue head patch and exposed dark
vent/port wells are the final review refinements. Existing prototype relief
alignment, baked diffuse shading and interpretation limits remain.

## Animation, comparison and export

The prior original MW3 walk supplies all animation, with only horizontal hip
travel projected out for the earlier in-place review. The detailed pass changes
no control transform or source action curve. All 336 controller poses match
exactly: maximum matrix error0. Stock and detailed video passes have matching
camera/light/object transform signatures across all 336 frames. Geometry-only
gray stills disable normal maps on both versions, exposing the actual changes.
Four geometry inspection views use an extra weak fill; matched videos retain
the established reference light setup. All actual detailed vertices fit across
the full 336 frames with the saved camera; minimum X/Y margin is
0.117010.

Static glTF contains 16 mesh instances and 17,129 triangles, no animation. Export
freezes the evaluated hierarchy in memory, preserving world matrices within
3.814697265625e-06; reimport error is
1.9073486328125e-06. The saved editable Blender scene retains
the original walking animation, reference model and detailed variant. Static
export is not a native payload or an animated glTF port.

Three videos: 1280x960 individual / 2560x1020 comparison with 60px external header,
336 frames at 30 fps / 11.2 seconds, six walks and one light orbit. H.264 CRF8/slow/
grain/yuv420p/faststart from lossless PNGs. No model-image downscale in the
comparison. Retain downloadable originals; Drive streaming may reduce detail.

## Delivery and execution boundary

[Walking comparison](https://drive.google.com/file/d/15_1NRLX8XvgJibCm7MSLyBS8jiymCEKc/view?usp=drivesdk).
[Detailed walk](https://drive.google.com/file/d/18rDKM7vw1iQsUphb8hOxNMLl7ZSeP0P4/view?usp=drivesdk).
[Geometry-only comparison](https://drive.google.com/file/d/14tj-6_dxo45qTxE1Kr7E740OhmHqnvFI/view?usp=drivesdk).
[Organized Drive batch](https://drive.google.com/drive/folders/1m0CEmWk1wXHIKlkQGkWvIUvx0IYbAwEv). Thirteen files in four folders have
verified identity, names, MIME types, parents and exact remote/local byte sizes.
Previews, Model and Textures are separate; sharing settings were unchanged.

Local workspace: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/
mw3-strider-detail-r1. comparison.html links the videos, PNG boards, packed
strider-detailed-r1.blend, static GLB, material ZIP and method. Source pins,
geometry/action/controller checks, full vertex framing, static roundtrip,
video streams, PNG dimensions, ZIP integrity and local HTML references pass.
The copied 52 map files and their original normal-map provenance are included.

Boundary advanced: original stock model/material/walk -> authored higher-detail
geometry and matched offline review. NOT INSTALLED. Next is geometry appearance
review and original-control native visual payload/material registration, followed
by weapon alignment, damage/debris, LOD and live performance checks. The prototype
costs more geometry; no native FPS claim is made.

No game, desktop screenshots, registry/pilot edits, native renderer/launcher/
runtime writes or commit. Initial/observed live-context hashes unchanged:
True. Other graphics/asset writers and protected jobs preserved. Strict
acceptance stays paused 131/144; this offline geometry work earns zero credit.


Final inspection-sheet check: corrected camera framing in all four gray views
so complete feet/antennas remain inside the image. Per-view actual-vertex bounds
pass. The first sheet is retained as geometry-turnaround-first.png. The existing
Drive file was updated in place and its name/MIME/parent/byte size reverified.


Follow-up: the user found broad armor surfaces too wrinkled at12x. The
[smooth-plate material revision](strider-normal-surface-cleanup-2026-10-16.md)
keeps this geometry/walk and colors unchanged, cleaning twelve relief tiles.
R1 remains preserved; use the R2 packed scene/maps for the current material review.
