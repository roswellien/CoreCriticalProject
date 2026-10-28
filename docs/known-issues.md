# Known playtest issues

Updated October 27, 2026. Keep unresolved reports here until their fixes have
been verified in the affected scenario. A passing startup or Training check
does not by itself close a campaign or combat issue.

## MW3-001 — Harasser rear raised above the front

**Status: Open — investigating.**

- **Reported behavior:** Harasser hover tanks sit or move with the rear
  substantially higher than the front, producing an incorrect hover stance.
- **Expected behavior:** A stance consistent with the original vehicle and
  terrain, without unexplained excessive nose-down pitch.
- **Reproduction:** Mission/location and behavior while stopped on flat ground
  have not yet been recorded. This missing detail does not close the report.
- **Findings:** Original model support points are level. The original
  ground-contact and pitch routines have been identified, but the cause has
  not been verified and no Harasser correction has been deployed.
- **Next step:** Capture an affected vehicle's pose and ground contacts,
  identify the cause, then verify the correction in the reported situation.
- **Workaround:** None verified.

See the [Harasser investigation](archive/vehicle-lighting-and-harasser-investigation-2026-10-24.md#harasser-investigation--unresolved).

## MW3-004 — Main-menu pointer confined to the edges on one laptop

**Status: Open — display-scale trigger confirmed; native correction being validated.**

- **Reported behavior:** In the main menu, the pointer remains near the screen
  edges and cannot be moved to the center. The owner used Ctrl+Alt+Delete to
  terminate the game. This also occurred previously on the same laptop.
- **Comparison:** The owner tested another laptop and its mouse works normally.
  The affected laptop uses 1920×1080 at 125% Windows display scale.
  Both its external mouse and built-in touchpad exhibit the problem. The owner
  reduced Windows display scaling and confirmed that pointer control returned.
  Monitor configuration and selected game window mode remain unrecorded.
- **Findings:** The selected 1.0.34 native adapter forwards interactive mouse
  state through real DirectInput, and cursor clipping/positioning through
  USER32. Scripted captures substitute virtual mouse state and therefore cannot
  verify or close this physical-device report. The selected host source has no
  explicit DPI-awareness initialization. A manifest-based PerMonitorV2
  correction is packaged as signed runtime test update 1.0.35 for launcher
  1.0.34+. Local checks pass; affected-laptop retesting remains pending.
- **Next step:** Verify the native process's effective DPI contract, retain
  matching native-pixel cursor/window coordinates, then retest physical menu
  input at 125% on the affected laptop before closing this issue.
- **Workaround:** Reducing Windows display scaling restored mouse control on
  the affected laptop, confirmed by the owner. This is temporary; it does not
  count as a software correction.

See the [DPI investigation and retest candidate](archive/main-menu-dpi-mouse-2026-10-24.md).

## MW3-002 — APC/vehicle headlight direction and destruction cleanup

**Status: Fix in DEV — combat confirmation pending.**

- **Reported behavior:** Lights illuminate the ground around the entire APC
  rather than forward, and can remain after the vehicle is destroyed.
- **Repair:** Headlamps use forward-facing spotlights; light lifetime follows
  the original vehicle's healthy/active state.
- **Verified:** Fifteen focused lighting checks and a 500-frame native Training
  run passed. The repair is in the signed DEV runtime and retains the current
  campaign lighting and heap fixes.
- **Still required:** Confirm forward beam appearance and removal after
  destruction in live combat, including looking away and back at the wreck.

See the [vehicle lighting repair](archive/vehicle-lighting-and-harasser-investigation-2026-10-24.md#vehicle-lighting-repair).

## MW3-003 — Destroyed mech reverts to the stock model

**Status: Open — reported, not yet investigated.**

- **Reported behavior:** Sometimes, when a mech using an MW5 replacement model
  is killed, its model switches to the original stock MW3 model.
- **Expected behavior:** The mech retains the replacement model's visual
  identity through destruction and its wreck state.
- **Reproduction:** Intermittent. Affected chassis, mission and viewing distance
  have not yet been recorded.
- **Findings:** Cause unverified; no correction has been deployed for this report.
- **Next step:** Capture an affected kill and trace replacement selection across
  the living, destruction and wreck states, including any LOD changes.
- **Workaround:** None verified.

## MW3-005 — Force-feedback wheel or joystick stops the game at startup

**Status: Fix in review — reaches the main menu with a G920 connected; launcher check pending.**

- **Reported behavior:** With a force-feedback device connected (a Logitech
  G920 wheel on launcher 1.0.43, runtime 1.0.44), the game exits at startup with
  "Unimplemented host service: IFORCE2.dll!_IFLoadProjectFile@8".
- **Expected behavior:** The game starts and the device works as a joystick.
- **Findings:** The host passed the device's real force-feedback capability to
  the game, which then loads its effects through IFORCE2.dll. The host has no
  IFORCE2 or effect service. The repair reports devices without force-feedback
  capabilities, so the game takes its original plain-joystick path. Force
  feedback itself is not supported yet.
- **Workaround:** Unplug the force-feedback device before launching.

See [issue #11](https://github.com/roswellien/MW3Recomp-Private/issues/11).
