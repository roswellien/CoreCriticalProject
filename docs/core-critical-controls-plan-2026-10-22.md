# Core Critical per-game controls and controller setup

Requested 2026-10-22: launcher-managed key bindings for each game, plus
controller setup, calibration and bindings. This is an implementation plan;
no controls UI, controller backend or playable host is added by this document.
Acceptance remains 131/144. Active controls and performance jobs stay intact.

## Existing foundation and missing behavior

GameCatalog already supplies separate identities for MW3, Pirate's Moon, MW4
Vengeance, Black Knight and Mercenaries. Only MW3 is currently playable.
LauncherSettings currently has no controls profiles or calibration storage.

The [controls investigation](controls-modernization-investigation-2026-10-18.md)
records a native MW3 text-preset load, all 105 candidate commands persisted
correctly, normal shutdown, and a bounded original/candidate Training comparison.
That preset is isolated and not deployed. Physical keyboard/mouse feel and
broader input checks remain open. The packed button map does not include axes.

The existing Windows DirectInput service is not the proposed modern gamepad
backend. The investigation already records Xbox and PlayStation on Windows,
potential future Linux support, and an input-only SDL proposal. Joystick/HOTAS
axis, button and hat setup should fit this design, but specific hardware support
must be validated before being advertised.

## Player flow

Add Controls to launcher navigation. Show the selected game and active named
profile clearly, with Keyboard & Mouse, Controller, and Test & Calibrate views.
Changing games selects that game's saved profile. Planned games remain clearly
unavailable until their runtime adapters are implemented.

Keyboard & Mouse groups actions into movement, aiming, weapons, targeting,
systems and camera. Capture keys and modifiers; support secondary bindings,
clear/reset, conflict messages and explanations for launcher/runtime hotkeys.
Display actual supported actions. Preserve existing bindings on first use;
provide the original layout and reviewed Traditional preset as explicit choices.
Do not label the unimplemented FPS assistance mode as working.

Controller lists connected devices and shows live buttons, sticks, triggers,
axes and hats. Bind by selecting an action and pressing/moving the desired input.
Offer separate movement, torso/aim, throttle and menu bindings, plus a modifier
layer for commands that cannot fit on the ordinary button set. Match button
labels to the device, with a manual label override for remapped devices.

Test & Calibrate walks through resting the controls, moving through their full
range, checking direction and saving. Show raw and adjusted values so drift,
range and inversion are understandable. Offer reset/cancel and leave current
calibration intact when a step fails. Reject missing/near-zero axis travel;
never divide by an unusable range. Handle centered sticks, separate triggers
and single-ended throttle axes as different input types.

## Persistence and ownership

Store a versioned controls document under the existing per-user data root,
separate from graphics settings, content packs and save backups. Write atomically
and preserve the previous valid version. Invalid/unsupported documents produce
a visible error without replacing them with silently saved defaults.

- Per game: named profiles, active profile, action bindings, axis assignments,
  sensitivity, response curves, deadzones, inversion and controller preference.
- Per physical device: measured center, minimum/maximum and rest noise, shared
  across games. Game-specific tuning applies after calibration.
- Per launch: a validated snapshot of the selected game's profile. Editing the
  launcher during play takes effect on the next launch initially; no live
  rewriting of the game's controls or pilot files.

Use GameCatalog IDs and stable game-qualified action names, not a shared list of
numeric MW3 action IDs. Each game's adapter translates supported actions and
declares capabilities. Profile copying between games must expose unmapped
actions rather than assuming the controls are interchangeable.

Do not use a transient controller index as saved identity. SDL instance IDs
change after reconnect; its GUID identifies a device class, not a unique unit.
Use available serial/path/transport information plus an explicit player alias
and selection fallback for indistinguishable devices. Recalibration or device
selection must be explicit when identity is ambiguous. USB and Bluetooth may
need separate identity associations.

## Runtime integration and delivery

Reuse MW3's proved native preset parser/settings path for the first keyboard
integration. Preserve the player's original selection and axis configuration;
loading a keyboard preset alone does not implement axis calibration. Determine
ownership of in-game edits explicitly: initially import them on request and
apply launcher profiles only when the player explicitly selects one.

Continue the input-only SDL proposal for normalized gamepads and lower-level
joysticks, sharing calibration and mapping behavior between launcher preview
and native runtime. Pin and review the acquired dependency before integration.
Do not replace window, Vulkan or audio ownership. Avoid general OS keyboard
emulation; feed the recovered game actions/axes at their simulation input boundary.

Release adapter-owned commands on focus loss, disconnect and handoff. Do not
leave fire or throttle held. Pause/neutral behavior must be explicit for each
game and each throttle mode. Prevent duplicate input from SDL, legacy DirectInput
and Steam/remapping software; the launcher calibration preview releases device
ownership before game launch.

Implement in these slices:

1. Per-game profile storage, action/capability catalog and MW3 keyboard editor;
   connect explicit selection to the proved native preset load path.
2. Shared device discovery/live test and calibration, then a bounded native
   Traditional gamepad path with Xbox/PlayStation labels and remapping.
3. Complete menu, briefing, Mech Lab and combat navigation; verify reconnect,
   focus transitions, mixed keyboard/controller use and joystick/HOTAS devices.
4. Add other game adapters as those runtimes become playable. FPS assistance,
   rumble and specialized device features need independent validation.

Launcher UI/profile changes can ship in .ccupdate. A new native input adapter
also requires the corresponding signed game runtime update, initially .mw3update.
Both must advertise compatible controls schema/capabilities; older hosts must
not claim they applied unsupported profiles. Installer packaging must include
the chosen input dependency and license once that backend is implemented.

## Checks needed before shipping

Prove game/profile isolation, settings migration, corrupt-document preservation,
binding conflicts and hotkey handling, and recovery after a failed apply.
Exercise the actual native preset load/save with the selected launcher profile,
then compare meaningful Training movement, aim, throttle, centering and firing.
Calibration tests need off-center/asymmetric axes, noise, unusable ranges,
trigger rest values and finite/clamped outputs. Device tests must include
unplug/replug while firing or moving, focus loss, duplicate device instances,
and real supported controllers over each claimed transport. Authored virtual
device tests help regression coverage but do not prove physical-device support.

The intended execution boundary is launcher-selected per-game profile -> native
input adapter -> recovered actions and axes. A saved profile or moving test bar
alone does not establish working in-game controls.

Sources checked 2026-10-22: SDL's [gamepad API](https://wiki.libsdl.org/SDL3/CategoryGamepad)
describes standardized layouts and hotplug; its [joystick API](https://wiki.libsdl.org/SDL3/CategoryJoystick)
describes arbitrary axes/buttons/hats and the distinction between instance IDs
and device-class GUIDs. These are library capabilities, not verified game support.

## First implementation slice: MW3 keyboard and mouse profiles

The user subsequently authorized the first slice. Source now includes a Controls
entry in launcher navigation and a keyboard/mouse editor using the existing
launcher visual system. The navigation wraps at smaller window widths.

The editor copies the native game's saved bindings, shows all 105 registered
actions in groups, filters actions, captures primary/secondary keys and modifiers,
assigns the three MW3 mouse buttons, clears assignments, names/saves layouts and
selects the next-launch layout. Existing shared bindings are shown rather than
silently removed; new assignments cannot introduce a duplicate key or mouse
button. F9-F11 and Windows-reserved capture shortcuts are rejected. Standalone
modifiers and Pause are not offered as ordinary game bindings. A window-scoped
key-message hook retains physical scan codes, allowing Numpad Enter to be
distinguished from Return rather than relying on the WPF key name alone. The
format conversion is covered by an authored extended-Enter test; physical-device
Numpad Enter validation remains open. The automated injected-key trial reported
an ordinary Return scan, so it is not claimed as hardware Numpad Enter evidence.

The versioned library lives at controls/mw3/profiles.json under the player's
existing data root. No library means no changed launch behavior. Other games are
listed as planned and cannot edit or apply the MW3 library. There are no controller
discovery, calibration, device axes, FPS assistance or runtime input backend changes.

An explicit selected layout is converted to a local keys/CC-<content-hash>.zrd
in the selected game copy and loaded through the original ActiveCtlCfg input.
Zero fields are emitted so clearing an assignment actually clears it. Existing
joystick button assignments are carried through without exposing controller edits.
For a custom text preset, only its KEYS section is replaced; AXES and other
sections remain. Unsupported/binary/missing original presets fail visibly instead
of quietly substituting an axis setup. Retail DefaultCtlConfig uses the existing
native initialization and registry settings rather than shipping captured defaults.

The first activation backs up the original ActiveCtlCfg and DefaultCmdMap rows
before changing either. "Use game's own controls" restores those rows on the next
native launch while retaining unrelated preferences subsequently saved by the
game. "Reset layout to original" copies the original rows into the working layout;
"Copy current controls" can instead capture the latest game-saved map. Existing
original preset files are never rewritten. In development, the published registry
seed is cloned into the per-user native settings directory before custom controls
are applied. The installed/native launcher uses the same preparation method.

Edits apply on launch. Changes made inside the game are not automatically written
back into a launcher layout: after quitting, copy current controls to save them as
a layout. Returning to the game's own controls restores the pre-activation button
map and selection. Imports/resets require MW3 to be closed; saved layouts can be
edited while it runs. Malformed or future-version libraries are preserved and
reported, not silently replaced with defaults. Writes are atomic with previous
versions retained.

Local checks cover game identity, import packing, modifiers and extended arrows,
clear/reset semantics, custom axis-section retention, clone isolation, restart
persistence, shared keys, corrupt-file preservation, original selection recovery,
unrelated native settings preservation and failed-apply preservation. The WPF
editor was inspected and a Ctrl+Shift+F8 camera binding was captured, saved and
selected through its actual UI. The native game then persisted all 105 commands
exactly as that layout specified and completed normal ExitProcess(0).

Private evidence and builds are under D:/CoreCritical-Controls-20261022-r1.
The first moving Training comparison retained later old camera keys and is not
claimed as a matched rendering comparison. Native-r2 was blocked at startup by
an independent game and supplies no native comparison evidence. Native-r3 uses a
fresh namespace, identical copied pilot/configuration and initial registry data,
the same host, and frame-based menu/camera input without the old timed camera
events. Original X and the new physical Ctrl/Shift/F8 sequence produce byte-identical
images at frames 800, 900, 1000, 1100, 1200 and 1400, including samples after the
camera transition. The candidate persists all 105 bindings exactly and quits
normally with ExitProcess(0); the baseline ends at its explicit 1500-frame budget
(expected exit 1). This is a bounded camera-remap check, not extended physical
keyboard/mouse feel or a complete movement/firing comparison.

These live checks use the existing original-compatible geometry, GPU HUD,
diagnostic 50 ms clock and no optional replacement-model/world packs. They are
input-path checks, not performance measurements or a new enhanced-renderer claim.
The full launcher suite was initially blocked by independent native performance
runs; those games were left intact. Temporary editor windows and owned scheduled
tasks are removed after the corresponding tests finish.

Final focused controls and launcher-profile/pack-selection checks pass. The full
suite also passed its component checks through signed runtime updates in an idle
window, then exposed an outdated monitor test assumption: the current published
host now advertises that capability. Its negative fixture now explicitly removes
the capability, and the profile-only checks pass against the current host. Later
whole-suite attempts are blocked by a live game; no complete final-suite pass is
claimed. Release win-x64 self-contained publish completed successfully at
local/launcher-controls-preview-20261022-r1/MW3RemasterLauncher.exe. This is a local
launcher build, not a rebuilt/signed installer or R2 release.

This advances launcher-selected MW3 profile -> original preset loader -> native
command map, with live Training execution. It does not grant acceptance credit or
physical-controller support. The running installed launcher and cloud setup are
not replaced by this source/build work. No native recompile, commit, signing or
upload. This keyboard slice can use the existing native controls parser; future
controller integration still needs its native runtime update.

The next input-only controller discovery/calibration slice is now implemented;
see [controller setup](core-critical-controller-setup-2026-10-22.md) for its
dependency, checks and remaining gameplay boundary. Earlier keyboard-only scope
statements above describe that first slice, not current device-test availability.
