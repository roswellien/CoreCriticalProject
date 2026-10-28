# Photo-mode target-marker crash repair

The Material Normal Preview now uses a rebuilt Campaign 1 host with a narrowly
scoped photo-mode display repair. Launch with `Play MW3 - Material Normal Preview.cmd`.
F11 toggles photo mode, F9 saves a PNG, C cycles camera modes, H hides the HUD,
F1 hides the controls legend, and Escape returns to gameplay. With the standard
repository game path, screenshots are saved in `local/screenshots/`.

## Cause and execution boundary

Two October 19 player runs failed with "Widescreen target triangle has no current
camera provenance" at VA 0x563B80. Photo mode freezes the simulation and skips
the original target-marker projection update, but its drawing routine could
still execute. Detached cameras also invalidate player-camera marker positions.

The photo/replay dispatcher now suppresses the original player target-marker
display routine at VA 0x441490 when the simulation is frozen or the camera is
detached. Its original thiscall epilogue is `ret 4`; the existing skip helper
removes the return address and its single stack argument. Paused Game camera
mode is included. Live gameplay keeps the existing projection update and strict
current-frame camera checks. Simulation, targeting logic, textures and lighting
settings are unchanged. The installer description now names the actual hotkeys.

## Verification and limits

- Clang-CL/Ninja release build completed; photo camera/math/replay unit tests pass.
- A separate private test build supplied held-key states at the existing async
  keyboard polling boundary. It ran the original Campaign 1 Mission 1 route for
  1,600 native Vulkan frames, ending at its intentional presentation budget.
- That test entered Photo/FreeFly, saved a decodable 3440 by 1440 PNG through F9,
  hid the HUD, cycled Orbit, Dolly, Game and FreeFly, resumed through Escape,
  then entered photo mode again and resumed through F11 without the reported fault.
  PNG checks at this point covered structure/dimensions, not pixel correctness;
  see the screenshot readback correction below.
- Native captures show paused FreeFly and Game modes, followed by restored live
  HUD and advancing mission time. The first 1,099 unpaused draw triples match the
  uninstrumented fixed build.
- Automated desktop key presses did not reliably reach GetAsyncKeyState. The
  scripted result verifies mode transitions/rendering/capture, not physical-key
  delivery. The installed source and executable contain no test key injection.
- The separate desktop-input attempts ended with an unimplemented WinHelpA path;
  they are not counted as successful hotkey tests or silently treated as budget
  stops. Repair of that separate help/window-message path remains outside this fix.

The initial crash-repair executable SHA-256 was
`a85b9e1527145c37734fe0440a9842b80c531ea62b11e005096c26e4ea9b5894`.
Its source differs from the previous Campaign 1 host only in
`photo_replay_stage.inc`. The preview profile and source pins match the new build,
and its launcher check passes. All current Campaign 1 materials, 15 model
candidates, lighting presets, normal strengths and menu enhancements are retained.
Replay video remains off by default. The separate standard launcher is not promoted.

Local evidence is indexed at `reports/photo-mode-fix-20261019/verification.json`.
The accepted receipt still hashes to
`aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061`;
formal acceptance stays 131/144. No game media or generated source is published,
and no commit or push is made.

## Follow-up: preserve water and camera framing

The subsequent player report identified a visual defect that the crash test
did not cover. The updated preview removes the automatic 14-unit backward and
3.5-unit upward camera offset on FreeFly entry. It also stops writing generic
transform matrices to camera-data offsets +0x30/+0x60. Those offsets belong to
type-5 transform nodes, not the active type-1 camera. Original VA 0x4F4370 derives
the camera eye at +0x2C, world matrix at +0x44 and forward vector at +0x74 from
the injected matrix-stack result. The override now leaves those original writes
to that routine, including when returning to the game camera.

HUD hiding previously discarded every draw inside VA 0x57E110, a shared sorted
transparency flush. Suppression now checks the resolved HUD role of each draw
and preserves world draws. Original texture/alpha/depth settings and ordering
are unchanged. This repairs photo-mode composition rather than changing water
assets, mech placement or gameplay.

A separate 1,500-frame live control preserves all original draw triples against
the prior host. Another 1,500-frame native test enters Photo, toggles the HUD
shown/hidden/shown at the same camera pose, captures three valid full-resolution
PNGs, cycles all four cameras and resumes through Escape and F11. A 1100 by 390
water crop is pixel-identical across the three paused HUD states; the two clean
HUD-shown PNGs also have identical SHA-256. Seventy-five registered water/surf
submission records are retained, with zero suppressed. Entry framing and the
mech waterline were visually compared. The live-to-photo crop is not pixel-exact
(mean absolute RGB change about 4/255); this test does not claim complete visual
parity across all animated surfaces, weather, viewpoints or missions. Physical
keyboard delivery retains the earlier test limitation.

The new installed executable SHA-256 is
`112f4308525f969de216a24129deeac4e231c4b53af1b04270f9d48162d208f4`.
Its source differs from the initial crash repair only in the photo stage and
its draw-provider call site. The profile, source pins and launcher check match.
Evidence and screenshots are under `reports/photo-water-fix-20261019/`, on the
Games-drive report archive. Private key injection remains absent from the
installed host; replay video remains off and material settings stay unchanged.

The earlier report-directory move followed a test-media junction across volumes
and emptied the baseline test copy's media folder. The intact 122-file archive
copy was restored and each file verified by SHA-256 before the successful tests.
The main game media was unaffected. New report archiving copies only explicit
report files, excluding private game directories and their media junctions.

## Screenshot validation correction

The earlier PNGs were structurally decodable but their pixels were corrupted:
the capture path interpreted packed RGB565 readback as 32-bit pixels. The water
comparisons above used the independent native PPM dumps, whose conversion was
correct. The repeated PNG hashes only established repeatability of that capture
path, not accurate colors or layout. The [screenshot readback repair](screenshot-readback-fix-2026-10-19.md)
adds format-aware conversion and image comparisons against same-frame native
references. Do not use the earlier F9 PNGs as visual acceptance evidence.
