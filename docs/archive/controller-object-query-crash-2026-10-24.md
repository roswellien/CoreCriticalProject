# Controller object-query startup crash (2026-10-24)

The playtest report `MW3-Playtest-20261024-074601.zip` records a native startup
stop at `0x38003420`: `IDirectInputDevice2A::GetObjectInfo` had a proxy vtable
entry but no marshalling implementation. The game stopped before submitting
gameplay draws. Launcher version was 1.0.29; the selected native runtime was
signed performance R7, SHA-256
`26b4767532758230ebb315887b2b1e43417540c62269b45dbcd25bcf4bb67270`.

The attached controller exposes this legacy input initialization path. The
MW5-style keyboard layout is retained. The saved modern controller gameplay
profile has `Enabled=false`, and the failed session explicitly clears
`MW34_CONTROLLER_CONFIG`/`MW34_CONTROLLER_SDL`. Calibration and modern gameplay
enablement are separate choices. The fix does not change either setting.

## Contract and implementation

The shared `IDirectInputDeviceA`/`IDirectInputDevice2A` dispatcher now handles
`GetObjectInfo` by calling the real Windows device provider. It validates the
guest output size and writable range, supplies host-owned output storage,
forwards object ID/lookup flags and the actual HRESULT, and copies successful
results only. Four 32-bit stdcall argument words are cleaned up, including
the guest COM `this` pointer. Unknown methods still stop visibly.

The ANSI modern and DX3 structures contain no pointers and have identical
x86/x64 field offsets. SDK assertions require their sizes to be 316 and 292
bytes, the inline name at offset 32 and extended fields beginning at offset 292.
Microsoft documents both supported query layouts and lookup modes in
[GetObjectInfo](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ee417906%28v%3Dvs.85%29).

Only `mfc_stage.hpp` differs from the pinned signed R7 composition. All rendering,
model/weapon effects, buffer reuse/preload, original translated gameplay and
controller mapping code remain byte-identical. The unchanged translated module
SHA-256 is `6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5`.
The execution boundary advanced is native DirectInput initialization through
controller-object queries into the live menu and bounded Training.
Formal acceptance remains **131/144**.

Maintained implementation and checks:

- `tools/remaster-launcher/native-overrides/mfc_stage.hpp`: actual handler.
- `tools/remaster-launcher/apply_directinput_object_info.py`: guarded, idempotent
  adapter for existing pinned host compositions; no whole-stage overwrite.
- `tools/remaster-launcher/test_directinput_object_info.py`: extracts the actual
  handler verbatim and tests it against Windows SDK layouts with authored fixtures.

## Validation

Private evidence: `D:/MW3ControllerCrash-20261024-r1/`.

- `before-full-launch-settings`: reproduces the exact reported method/site using
  the original signed R7 host, saved keyboard layout and attached controller.
- `after-full-launch-settings`: reaches the live menu and completes 150 Vulkan
  presentations with the legacy physical-controller path enabled as in the report.
- `after-modern-training`: 500 Vulkan presentations, 936 recorded 3D scenes,
  and physical-controller polling reports connected/armed. The modern controller
  configuration is an isolated export of the saved calibration/mappings, enabled
  only for this test. Saved preferences are untouched.
- 8,388 actual-handler checks pass: both layouts, output canaries, malformed and
  short output regions, unchanged guest output on Windows errors, exact parameter
  and HRESULT forwarding, and four-word stack cleanup.
- The adapter applies twice without changing the result. Source pins prove the
  one-file delta and preserve every R7 rendering/performance source file.

The native runs intentionally stop at a frame budget with exit 1; success is
determined from the exact presentation marker, rather than exit status alone.
These are startup and bounded Training checks, not sustained controller-play or
all-mission validation. No input action was injected into the live user session.

Early isolated harness attempts omitted local media or coordinator-provided
music settings and stopped at their respective existing guards. Those retained
attempts are not counted as native input success. The final before/after runs
include the user's actual media bindings, saved controls, music tracklist and
3440×1440 FXAA/AF16 settings, with a private writable game/registry copy.
Original assets remain read-only inputs. No protected background job was stopped.

## Delivery

The dev profile selects the signed successor runtime:
`D:/MW3ControllerQueryUpdate-20261024-r1/Runtime/bin/entry_commandline.exe`, SHA-256
`1feb3c5875e3affe88b6d71cf45748bfa098006b7d1dd771d2686e2fa1b0c034`.
Source verification remains enabled. All other profile fields and saved control
settings are preserved. The launcher application remains version 1.0.29.

Private update bundle:
`D:/MW3ControllerQueryUpdate-20261024-r1/CoreCriticalGameUpdate.zip`.
It contains the signed `mw3-controller-query-20261024-r1.mw3update` envelope,
matching payload ZIP and import instructions. Sequence 2026102401, minimum
launcher 1.0.27. Original input verification remains required; no client code
generation or original media is included.

The real launcher update checks pass from both the 1.0.28 installer runtime and
performance R7: signature verification, installation, activation, validation and
rollback. The executable has a valid timestamped Artifact Signing signature.
The initial fix was delivered locally. The owner's subsequent publication request
is completed in the [1.0.29 playtest release](playtest-release-1.0.29-2026-10-24.md):
the protected playtest page now offers both the cumulative game update and a full
installer containing it. No Git commit was made.
