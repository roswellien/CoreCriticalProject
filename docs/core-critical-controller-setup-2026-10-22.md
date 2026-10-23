# Controller discovery and calibration

Subsequent work adds the [native MW3 gameplay adapter and binding editor](core-critical-controller-native-integration-2026-10-22.md).
This page retains the initial discovery/calibration slice and its original scope.

Controls -> Controller setup now opens an input-only device tester with six
standardized axes, pressed buttons, per-axis deadzone/response/inversion and
explicit resting-center / full-range calibration. The keyboard profile flow
remains available. No MW3 action mapping or native controller delivery is enabled
by this slice; the window states that directly.

The boundary advanced is Windows controller -> SDL normalized state -> launcher
display / device calibration. The game retains its existing input services.
There is no OS key injection, guest service success stub, original-code fallback
or native recompile. Formal acceptance stays 131/144.

Private settings live under controls/devices/<identity-hash>.json. Identity uses
SDL device-class GUID plus reported serial or connection path, with session
identity when neither exists. A GUID alone never identifies a unit. Simultaneous
ambiguous identities are separated by instance. No-serial devices warn that
changing connection/transport may require calibration again. Serial identities
are device-reported, not authentication. Nothing is uploaded.

Calibration measures resting samples before range samples. It rejects too few
samples, excessive rest movement, held sticks/triggers, incomplete ranges,
invalid versions/identities and nonfinite tuning. Sticks normalize to -1..1 and
triggers to 0..1, then receive deadzone, response and optional inversion. These
are independent per-axis deadzones, not radial stick filtering. No gameplay
sensitivity/aiming model is active. Writes use existing link-checked atomic
controls storage and retain a previous version; malformed files are preserved.

Polling pauses on focus loss, which clears readings and cancels measurement.
Unplugging also clears readings/cancels measurement. An unsaved draft stays
attached to its disconnected device rather than moving to the next enumerated
controller. Explicit device changes/closing ask before discarding changes.
Cleanup closes handles and quits the SDL gamepad subsystem. Backend failures
stop the test visibly.

## Dependency

SDL3 **3.4.18**, upstream commit
`829a65d769d935c4852f8159e964312c0957260a`, zlib license. It supplies standardized
Xbox/PlayStation mappings and discovery that the existing legacy DirectInput
bridge does not provide. SDL is input-only here; WPF/Vulkan/audio are unchanged.

[Upstream release](https://github.com/libsdl-org/SDL/releases/tag/release-3.4.18):

- SDL3-3.4.18-win32-x64.zip SHA256:
  `75c2c0fc74e7d1206aaedc22893a35887332f4f85f5c8b74fddc10d177985f2c`
- Unsigned SDL3.dll SHA256:
  `2b4b128d8d510cc2d442693cf848c050d700d43dc667afe9e5fd82b0570d667e`

Run tools/mw3-remaster-launcher/fetch_controller_runtime.ps1 before building.
It downloads/verifies the pinned archive into ignored local/third-party. The
project verifies source DLL bytes and copies SDL3.dll and SDL3-LICENSE.txt to
build/publish output. Ordinary builds never download. Without the dependency,
source still builds and setup reports the missing backend. Installer publication
requires both files. Existing signing can sign the DLL; runtime loads only from
the application directory and checks SDL version rather than comparing the
unsigned hash after Authenticode changes the PE certificate.

API contracts checked against upstream:
[updates](https://wiki.libsdl.org/SDL3/SDL_UpdateGamepads),
[axis ranges](https://wiki.libsdl.org/SDL3/SDL_GetGamepadAxis),
[serial](https://wiki.libsdl.org/SDL3/SDL_GetGamepadSerial),
[joystick identity](https://wiki.libsdl.org/SDL3/CategoryJoystick).

## Checks and remaining work

LauncherChecks --controllers-only passes calibration normalization/inversion,
rest/range rejection, persistence, device separation and corrupt-file preservation.
Real SDL virtual-joystick APIs with authored inputs verify attach, enumeration,
open/identity, stick values, separate triggers, button press/release, disconnect
and cleanup. These are software checks, not physical hardware evidence. SDL
enumerated zero mapped physical controllers during validation.

The no-controller WPF window was inspected at its default desktop size, including
disabled calibration and connection instructions. Focused keyboard controls and
launcher profile/pack-selection checks pass. Self-contained Windows x64 local
publication: local/launcher-controller-preview-20261022-r1. No installer, signing,
R2, installed launcher replacement or commit was performed.

The broader suite passed through calibration, save backups and installed runtime
discovery, then its runtime-update checks were blocked by a native game starting
during the run. That game was left intact; no complete full-suite pass is claimed.

Next: actual Xbox/PlayStation USB/Bluetooth testing, per-game action/axis profiles,
and a version-gated native MW3 input adapter at simulation cadence. It must
release held commands on focus loss/unplug, neutralize throttle explicitly,
prevent duplicate legacy/remapper delivery and preserve original actions.
Menus and combat need live native validation. Launcher changes can ship through
.ccupdate; native input needs .mw3update. Other titles need their own action
contracts rather than MW3 numeric IDs.
