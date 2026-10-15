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
