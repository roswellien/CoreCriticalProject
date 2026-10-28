# Photo mode: stretched terrain texture repair

The screenshot readback repair fixed PNG colors and layout, but its photo-mode
sample still contained horizontal terrain streaks. This was a separate rendering
defect. Matching PNG pixels to the rendered frame did not validate the materials
in that frame.

## Cause and change

A bounded Big Lake Instant Action route reproduced intact ground during live
gameplay and stretched triangles after F11. The same defect remained with GPU
world binding disabled, and with direct-binding shortcuts disabled. At frame
1091 the principal ground surface used repeat sampling on 189 draws. At paused
frame 1121 it unexpectedly used clamp-V sampling on nine draws. Texture edges
then stretched across the affected triangles. Forcing repeat sampling removed
the bands in a diagnostic build, but would change legitimate material settings.

Photo/replay snapshots restored guest memory, including the game's cached
graphics settings, without restoring the corresponding host Direct3D provider
state. The guest consequently skipped setters that the host still needed.
Simply removing the repeated Photo restore caused a nonfinite transform in a
diagnostic run and was rejected.

Each frame now captures and restores device render states, texture-stage states,
texture bindings, current viewport and viewport settings alongside guest memory.
Restoration invalidates the provider's shared draw-state snapshot. It preserves
live command queues, scene ownership, render targets and Vulkan resources; missing
devices or incompatible viewport ownership fail visibly. Material sampling is
restored individually, without changing texture artwork or disabling GPU terrain.

The saved rewind format is now MW3RPLY3. Older files lack provider-state data and
are rejected; record a new rewind file with this build. This is separate from
the replay video buffer, which remains disabled by default.

## Verification and limits

- The repaired host completes the same 1300-presentation route with scripted
  F9, F11, hidden HUD and Escape resume. Ground detail remains across the previously
  smeared triangles. Three saved PNGs match native reference pixels outside the
  screenshot-confirmation message.
- Unpaused frame 1091 matches the previous host exactly outside that message.
- Replay unit checks cover all device-state arrays, viewport data, frame-window
  trimming, disk roundtrip, random seeks and rejection of version 2 files.
- A separate shipping build removes diagnostic key injection and sampler
  overrides and completes the ordinary 1300-presentation Big Lake route.

Native testing uses the RX 9070 at 3440x1440, FXAA and AF16. This repairs the
observed photo-mode terrain defect; it does not establish full campaign visual
acceptance or complete rewind resource-lifetime fidelity. Physical key delivery
retains the earlier automation limitation. Formal acceptance remains 131/144.

The installed executable SHA-256 is
7fa3ef53000c11df73a6d98e48e73a98f45f3b4a4bfb0a58e2f0f26a0ffb8610.
Evidence and before/after PNGs are indexed in
reports/terrain-smear-fix-20261019/verification.json on the Games-drive archive.
The updated test entry remains Play MW3 - Material Normal Preview.cmd. The
standard launcher is not promoted. No commit or push is made.
