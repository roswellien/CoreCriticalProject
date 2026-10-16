# Validated enhanced native source overlays

These are project-authored source files from the local `gpu-native-r5` host.
They preserve the enhanced renderer/HUD, replacement-model adapter, registered
texture-bank redirection, FXAA/AF and widescreen implementations reviewed for the
[October 14 update](../../../docs/session-summary-2026-10-14-remaster.md).
They contain no model vertices, texture pixels, music or generated game bodies.
Mesh names/counts describe the observed format contracts.

Files replace or supplement matching files in the private host's `host-source`
directory. Unchanged authored base files come from `tools/m4-crt-heap-carry/`.
`runtime/audio/local_cd_audio.hpp` supplies the shared native music service.
`source-sha256.json` records the copied source identities and the validated local
executable identity; it is metadata, not a supplied executable or build receipt.

This is a source snapshot, not a standalone game build/install recipe. Building
the host additionally requires the admitted user installation, pinned compiler,
local generated entry/dispatch metadata and the optimized translated object
list. Those inputs are intentionally not published. Overlaying sources does not
publish a completed launcher profile: only a rebuilt and validated executable
may replace the hash-pinned local profile. Existing frozen builds are preserved.

`fxaa.vert`, `fxaa.frag` and `model_scene.vert` are project-authored GLSL;
their accompanying `_vert.h`/`_frag.h` files contain compiled shader SPIR-V.
The original game uses its existing scene shader. Replacement model geometry
and its shader are optional and separately scoped from original gameplay.

The original-compatible regressions and enhanced rendering/music checks are
recorded in the daily summary and E0 document. No whole-game compatibility,
pixel-identical enhanced rendering, downloadable media or formal acceptance
completion is implied by this source snapshot.

`hud_deferred_stage.inc` is a later authored repair, applied to a fresh private
r8-compatible tree by `../apply_hud_repairs.py`. It preserves each original
translucent HUD panel's display anchor across the sorted deferred queue. The
same applicator restores original diagnostic schematic geometry in the two
status previews. It does not update the historical r5 snapshot or its manifest.
See [the October 15 investigation](../../../docs/hud-mechlab-investigation-2026-10-15.md)
for r9 validation, unresolved zoom/radar checks and the separate Mech Lab proposal.

`zoom_alignment_stage.inc` is the later r12 repair. `../apply_zoom_alignment.py`
applies its exact source changes to a fresh frozen r9 host tree. It captures the
original movable zoom camera center before deferred submission, then uses that
center for scene projection and clipping. The full-target D3D scissor midpoint
does not identify the zoom camera's viewport. Missing metadata fails visibly;
original input/FOV/gameplay and the widescreen-off path are unchanged. Matched
locked cockpit/external sweeps, a1920x1440 control, real-clock cockpit use and
all three original-compatible regressions are recorded in the investigation.
This does not alter the historical r5 source manifest or implement Mech Lab.

`target_marker_stage.inc` and `../apply_target_marker_alignment.py` are the
later r14 repair, applied to a fresh frozen r12 host. They capture the original
normal/zoom camera choice per target owner/frame for the three triangle lines.
The original normal-marker occlusion comparison is adapted to the displayed
zoom footprint through one scoped, post-conversion display temporary. Original
target choice, clip flags, lead cues/arrows, gameplay, legitimate overlap hiding
and per-edge clipping remain. The current hardware coordinate profile0 is
required in widescreen; unknown conversion profiles fail visibly. The matched
cockpit reproduction,4:3 controls, original regressions and unavailable Vulkan
validation-layer attempt are recorded in the October15 investigation.
