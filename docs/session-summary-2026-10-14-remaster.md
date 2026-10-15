# October 14, 2026: native Remaster progress

The native game now has a substantially faster rendering path, a validated local
Remaster profile, true ultrawide presentation, broader original HUD coverage and
file-backed MW3 music. Original gameplay continues through native recompilation;
this work does not replace it with a remake.

## Completed

- **Native execution and software SEH:** completed the observed guest C++
  exception-dispatch/unwind path. The uncaught-exception failure came from
  incomplete read-only MSVCRT image data used by `strcpy` during abnormal
  termination. Loader startup now supplies the admitted image pages while
  preserving writable state, bound imports and the accepted FDIV path. Added
  the required real `CompareStringW` service and corrected CONTEXT/EFLAGS carry.
  Unsupported OS reporting/debugger behavior stops explicitly.
- **Rendering performance:** added indexed dispatch and guarded guest-memory
  fast paths, retained strict floating-point behavior, shared the Vulkan device
  for scene rendering/presentation, kept render targets resident, and uploaded
  replacement model geometry once. These changes remove the costly recurring
  rescale/readback path from the local enhanced profile.
- **AA and AF:** implemented authored FXAA at native resolution before the HUD,
  plus hardware anisotropic sampling, generated mip levels and trilinear
  filtering for world/model textures. The current profile uses FXAA and 16x AF.
- **True widescreen:** added 3440x1440 Hor+ world projection and culling while
  preserving vertical view and original zoom behavior. HUD components retain
  appropriate edge/center anchors; menus, movies and maps keep their proportions.
- **Original HUD behavior:** checked targeting, damage displays, radar modes,
  zoom, weapon groups, objectives/messages and HUD toggling through original
  commands. Corrected circle, clipped-line and pixel contracts; retained the
  original panel-noise/jitter producers and their random/FP side effects.
  Restored the distinct original zoom-state sprites in the local HUD pack.
- **Living launchers and local assets:** added both Remaster launch variants,
  build-identity checks, current texture/model registrations and atomic asset
  preparation. The profile supplies 39 cumulative texture banks and the
  Bushwacker, Mad Cat, Vulture and Thor registrations; Avatar is excluded.
  The original-model variant retains the textures, HUD and graphics settings.
- **Music:** connected the two supplied soundtrack FLACs to original CD slots
  2/3. Windows Media Foundation prepares checksum-verified PCM locally; a native
  WaveOut worker supplies real playback/cursor/notification behavior. Original
  music selection, volume, pause/continue and completion-driven repetition are
  retained. Private stereo gain does not change the system mixer. Intro/ending
  FLACs are excluded from the gameplay playlist; movie audio has its own AVI path.

## Validation and measured performance

Both final native builds retain the original-compatible reference results:

| Check | Result |
| --- | --- |
| Training captured frames | 116/116 identical |
| Mode 7 GPU draw stream | 1150/1150 identical |
| Instant Action captured frames | 116/116 identical |

The detailed HUD test exercised 41 original command actions over 2400 Instant
Action frames, produced all 19 requested native captures and recorded zero
GPU-HUD fallbacks or Vulkan validation warnings/errors. This is bounded feature
coverage, not exhaustive whole-game equivalence. A separate original-raster
comparison still has small GPU rasterization differences; pixel identity is not
claimed for enhanced rendering.

Full music passed menu-to-Training checks on both final hosts. Authored short
tracks exercised the actual original completion/repeat handler, and real audio
device fixtures checked pause, continuation, stop/seek/close, volume and cleanup.
Injected write/cursor failures confirmed queued audio stops and errors remain
visible; the production source contains no failure-injection hook.

Publication checks also pass all nine asset-free bootstrap test groups and the
C++ formatting gate. Pre-existing formatting issues in 16 authored fixture
sources were normalized without changing their intended tests. Formatting the
new audio header preserves its preprocessed code after C string concatenation;
the exact source used for native playback validation is retained locally.

Latest normal-play measurements on the development RX 9070, with current assets,
music, FXAA and 16x AF, using the same Training frames 651-1150 after loading:

| Output | Average | Mean frame time |
| --- | --- | --- |
| 3440x1440 ultrawide, repeat run | 120.06 FPS | 8.33 ms |
| 1920x1440 4:3 | 117.97 FPS | 8.48 ms |
| 3440x1440, matched music-off run | 120.37 FPS | 8.31 ms |

An initial music-enabled ultrawide pass measured 102.43 FPS and is retained as
observed variation. The repeat does not show a repeatable large music penalty.
Occasional approximately 34 ms frame spikes remain. These are short Training
measurements, not campaign-wide or cross-device guarantees. The texture pack
also changed after earlier measurements, so older numbers do not isolate music
or texture cost.

## Published source and local-only material

This update publishes project-authored native adapters, optimization tools,
Remaster launch/preparation tools, audio code and documentation. The reviewed
enhanced renderer/HUD/model-loader source is preserved in
[the native source overlays](../tools/remaster-launcher/native-overrides/README.md).
Generated shader headers come from the accompanying project-authored GLSL.

Original game media, replacement models/textures, music, decoded previews,
generated game translations, object lists, executables and detailed captures
remain local under the [distribution policy](legal.md). A clean checkout still
needs the user's own installation and prepared local toolchain/generated inputs
to build the game host; this is not a portable game or public asset-pack release.

Detailed execution boundaries, identities and local evidence locations are in
[the E0 execution record](e0-application-execution-path.md),
[native-host notes](../tools/m4-crt-heap-carry/README.md),
[Remaster launcher notes](../tools/remaster-launcher/README.md) and
[music preparation notes](../tools/music/README.md).

## Acceptance and remaining work

Accepted count remains **131/144; strict acceptance is paused**. No new native
game credit is inferred from probes, replay, original-process hooks or these
modernization checks. The accepted receipt and protected installation
registry/pilots remain unchanged.

Remaining work includes hardware-fault/nested SEH and OS-reporting contracts,
remaining Training/weapons/physics/AI comparisons, broader campaign/save/load
coverage, model encounter/weapon/damage/LOD validation and normal/PBR material
integration. Mad Cat, Vulture and Thor remain runtime candidates; the reported
Training geometry coverage primarily encounters the Bushwacker replacement.
