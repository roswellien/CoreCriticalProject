# MW3 controller gameplay integration

The user authorized controller integration after the discovery/calibration slice.
The launcher now has an MW3 action/axis editor, and an opt-in SDL3 native adapter
feeds the original game's command and analog input services. This advances
calibrated device state -> original command/axis consumers -> live native Training.
It does not grant acceptance credit: 131/144 remains unchanged.

## Player flow and initial layout

In the local launcher, open Controls -> Controller setup. Connect and select a
controller, test/calibrate and save it, then open MW3 bindings. Enable the layout
and save. Changes apply on the next compatible native launch. Bluetooth is the
user's selected Xbox test transport; that hardware test is pending because the
controller will be connected later. Xbox/PlayStation family or transport support
is not claimed from SDL facilities or authored virtual tests alone.

| Input | Default MW3 behavior |
| --- | --- |
| Left stick | Steering and proportional forward/reverse throttle |
| Right stick | Torso yaw and pitch |
| Right trigger | Hold fire for the selected weapon group |
| Left trigger | Original reticule zoom command |
| South / A / Cross | Jump jets |
| East / B / Circle | Center torso |
| West / X / Square | Next enemy target |
| North / Y / Triangle | Cycle camera |
| Back / Share | Original power-up/shutdown toggle |
| Start / Options | Pause |
| Left / right shoulder | Previous / next weapon group |
| Left / right stick click | Center legs / zero throttle |
| D-pad | Select weapon groups 1–4 |

Buttons and triggers can select any of the 105 recovered MW3 actions, or remain
unassigned. Sticks can be reassigned to the four input channels, with per-game
sensitivity and direction. Calibration remains device-specific and shared across
games. This is one MW3 controller layout, separate from the keyboard layout
library; other game action contracts and multiple named controller layouts are
not implemented. There is no controller-only menu/briefing/Mech Lab navigation
or command layer yet; use keyboard/mouse there. Gyro/rumble/trigger effects and
FPS torso/leg assistance remain outside this slice.

## Original input contracts

REA/Ghidra 12.1.4 inspected the user-supplied U.S. retail executable SHA256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Full private evidence is retained in
D:/CoreCritical-Controller-20261022-r4/original-input-evidence.json. Pseudocode
is a decompiler observation, not original source. The argument layout was also
checked against instructions and existing translated bodies.

- 0x51B360 polls original input providers. The adapter polls SDL once at this
  original input boundary rather than increasing the simulation rate.
- 0x51C370 returns command press/hold/release bits after checking the active
  manager's enabled byte at +0x3F58. The original function still runs; controller
  bits are ORed into its return only when enabled.
- 0x51C440/0x51C420 dispatch through the active original command callback table.
  Rising controller actions use that path. Caller guest registers/x87 state and
  host FP/last-error state are preserved around the added provider callback.
  Commands that are polled rather than callback-driven, including fire, can
  legitimately have no callback and still reach their held-action consumers.
- 0x427870 and 0x46AF30 supply analog inputs to the original player updates
  0x427D60/0x46B0A0. Outputs are throttle, steering, torso pitch and yaw. The
  0x427D60 receiver uses its base at receiver-0x14C. The adapter retains original
  mouse processing, adds normalized steering/aim, and supplies absolute throttle
  while the stick owns it. Only an adapter-modified temporary +0x3C throttle mode
  is restored after the update. Original clamps, smoothing, movement, aiming,
  targeting and weapon simulation remain in the translated code.

No OS keyboard injection, physics replacement, guest service success stub,
interpreter or original-code execution fallback is introduced.

## Safety, ownership and storage

Controller mode is off by default. An enabled selection needs native
controller_input_version=1; an older runtime fails visibly with update/disable
instructions. Disabled launch bindings explicitly clear inherited controller
config paths. Config files are exported per session, use invariant numeric text,
and are resolved to their physical paths before crossing the MSIX/native process
boundary. SDL loads from an explicit absolute application file path and checks
the pinned version. Dependency/version/license details remain in the
[discovery note](core-critical-controller-setup-2026-10-22.md).

The MW3 layout is controls/mw3/controller.json. Device calibration stays under
controls/devices. Both use bounded, versioned, link-checked, atomic storage with
previous files retained. Unknown games, actions, ranges and versions are rejected.
An identity without serial or connection path, or ambiguous simultaneous device
identity, can be tested but cannot be selected reliably for gameplay in the UI.

After connection or focus recovery, sticks/triggers/buttons must return to
neutral before arming. Focus loss, photo/replay input ownership and unplugging
release held actions and feed zero to adapter-owned throttle. Centered throttle
returns to zero rather than retaining cruise speed. The stop command overrides a
held stick until it is released to neutral. Original keyboard throttle increase/
decrease can take throttle ownership back. Other original throttle shortcuts can
be superseded while the stick still owns throttle; use the stick or W/S-style
throttle increment bindings when switching devices in this initial slice.

While enabled, SDL owns controller delivery: original DirectInput joystick
enumeration is filtered and non-keyboard/mouse legacy device creation is denied
with its real failure result. Keyboard/mouse services remain real. This prevents
the same pad arriving via SDL plus legacy DirectInput; remappers that synthesize
keyboard/mouse can still duplicate inputs and need physical validation.

## Builds and checks

The first local build used the draw-submission host. During integration the
selected host advanced to texture warmup; the final build was prepared on that
newer pinned host, preserving its complete rendering/startup changes.

- Final private host: local/remaster/controller-input-r2/build/entry_commandline.exe.
- SHA256: `d4395d19e9cb715920f88ea1da856a5db55083839db710d0b201ef9f12aad027`.
- Matching source-snapshot.json retains inherited metadata and hashes all source
  files. gpu_hud.inc, vdd.inc and vk_scene.hpp are byte-identical to the selected
  texture-warmup base. Artwork/movie compatibility registers this exact successor.
- Development local/remaster/launcher.json selects it and advertises input v1.
  The preceding profile is retained in controller-input-r2/launcher-before-controller.json.
- Launcher: local/launcher-controller-integration-20261022-r1/MW3RemasterLauncher.exe.
- prepare_controller_host.py verifies/clones a pinned completed base and applies
  apply_controller_input.py without replacing translated objects. The staging
  helper retains controller_input_version. Development source verification checks
  that the profile and snapshot agree on controller support.

Launcher calibration/profile/compatibility checks pass, including wrong game,
unknown action, invariant wire format, original-controls preservation and physical
config path resolution. Native math checks cover endpoints, deadzones, inversion,
shared bindings, stop behavior, connection/focus/unplug arming and parser failures.
The C++ parser also accepts an actual launcher-exported config. The complete
launcher suite passes, including signed update fixtures and pack selection.
The WPF editor was inspected in the existing launcher theme. Its gameplay toggle
was changed and saved through the UI in an isolated library; the disabled state,
action assignments and previous-version backup were independently checked.

Live native evidence: D:/CoreCritical-Controller-20261022-r4. It retains an immutable
host copy, source hashes, config, input scripts, logs and Training frames. The
process uses SDL's real virtual joystick APIs with authored inputs; stderr marks
this diagnostic explicitly. The SDL device reads, mapper, original callbacks,
analog helper and held-action query all execute in the native game process.

At frame500 power command63 dispatches successfully. At frame900 the original
0x427870 helper receives throttle0.418501, steering0.141077, torso yaw0.279798 and
pitch0.141077. Fire query61 returns1 on press,2 while held,4 on release, then0.
Focus loss at1050 yields neutral controls through1080/1140; held controls do not
rearm at1100. A second fire/throttle period at1200 reaches the same path. Stop
command27 dispatches at1220. Unplug at1260 produces zero throttle and releases
fire; reconnect with controls held remains unarmed until neutral. Camera command97
dispatches at900/1440. Independent math tests cover the throttle stop latch.

This is a diagnostic 50ms clock with original-compatible geometry and no optional
world/model packs. It is not a physical feel/performance test, projectile/damage
validation, menu support, full combat coverage or mission-completion credit.
Runs end at an explicit1600-frame budget (expected exit1), not a crash or normal
game quit. The earlier r2 trial remained powered down and supplied no movement
evidence; r3 and the final r4 correct that using the original power-up command.

No installed application replacement, installer build, signature, update archive,
R2 upload or commit was performed. Shipping requires the launcher .ccupdate plus
an input-v1 .mw3update through the existing source-preparation/update pipeline.
The first physical validation should use the user's Xbox controller over Bluetooth.
