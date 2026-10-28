# Installed content and fresh pilot follow-up

The private installed-layout trial now reaches live Training with two mech packs,
the Training environment pack and user-supplied music. Fresh pilot-name entry
also works after repairing two missing native USER32 services. This advances
external runtime/data startup through actual menu input and Training execution;
it does not complete a distributable installer or award acceptance credit.
Strict acceptance remains 131/144.

## Installation and music

The existing-installation route verifies the selected original data. If its exact
admitted CRT provider is absent, setup asks for user ISO media and imports only
the required support file into a hash-named per-user cache. The original game
folder remains unchanged. The importer verifies the cabinet, extractor and
provider identities; unrelated system DLLs are rejected. The positive import
trial retained the user's existing F: disc mount.

Installed setup offers optional original soundtrack selection; Graphics & Display
also provides **Select Original Music Tracks…**. Users select two FLAC or stereo
16-bit/44100 Hz PCM WAV files. Preparation writes to the user cache, never the
application directory or original sources. Missing inputs fail with instructions
to select tracks or disable music. The FLAC decoder in this private trial is a
local generated artifact and is not cleared for distribution.

## Native keyboard repair

Actual fresh-pilot trials exposed missing `MapVirtualKeyA`, then `ToAscii`.
The maintained override now forwards real host translations, validates guest
keyboard/output buffers and preserves the signed translation result. The
[Windows ToAscii contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-toascii)
uses a WORD output that can hold two packed characters.

The final isolated host is `local/remaster/gpu-native-installer-keyboard-r2`,
SHA-256 `3f34ec34ac6fb6f729a8c544b387b79b81495e7c0f250b566ef25008772b4fa2`.
Its base is `gpu-native-detached-cockpit-r1`, SHA-256
`7e1c939111b219f32bd765e25d840c6196c1d9c5b7cfb073ac21b949aedfa5d9`.
Of 117 pinned sources only `mfc_stage.hpp` changed; CMake input definitions
match except the three staging-path variables. Exact mech/environment host
admissions include the reviewed successor; unknown hosts remain rejected.

The private selected `local/remaster/launcher.json` now points to this host and
snapshot. Every other profile field was compared and preserved. Its prior bytes
are retained under `local/work-ahead/installer-source-20261021-r1/`.

## Evidence and limits

The final external runtime is `D:/MW3InstallTrial-20261021-r5/App/Runtime`.
Original game data, music and writable user state are under the r3 external trial
directory. The game directory deliberately lacks `native-inputs`, exercising the
new provider-cache route. The actual coordinator used bundled Python outside
the checkout. The initiating C# test harness still ran from the checkout; this
was neither a clean-machine trial nor an OS-enforced checkout-access denial.

Interactive session `292a544c5c824b169a1084182f006d6e` under
`D:/MW3InstallTrial-20261021-r3/UserData/sessions/` displayed fresh pilot entry,
accepted a real `i` key and Return, and showed that pilot in the Training menu.
Alt+F4 returned normal exit 0 through host, coordinator and C# GameRunner.
No input script or frame limit was used in this run. Automated absolute mouse
movement was unsuitable for the relative DirectInput cursor; human mouse
usability remains to be checked directly.

The separate bounded Training run is retained at
`D:/MW3InstallTrial-20261021-r3/UserData/training-check/`, session
`session-5e07081f06f6453180406174116d9b0e`. It used the existing Training input
script and stopped at the requested 340-frame budget (diagnostic exit 1).
All 340 frames reached the Vulkan swapchain. Final geometry reported 16,920 CPU
vertices, 1,287 GPU vertices and two GPU batches; world execution reported
6,935 draws executed. Logs recorded 38 loaded textures, 36 loaded normals,
16 replacement queues and eight loaded world-normal pages. Music logs recorded
tracks 2 and 3 and nonzero queued PCM, not a subjective audio-quality assessment.
The selection comprised both existing mech packs plus the relocated Training
pack, including all six Training texture banks. This does not establish campaign
coverage or fidelity. Earlier failed pilot-entry sessions remain intact.

C# launcher checks, authored installed-music/cache-repair checks, Python dispatch,
installed-runtime and both prepared-pack suites pass. A self-contained
1.0.6-preview GUI and media tools are staged at
`reports/installed-content-20261021/launcher`.

## Remaining installer work

The ordinary open GUI remains 1.0.4; the newly staged GUI has not replaced it.
Only the selected private host was updated. The ordinary mods directory still
contains two mech packs. The new explicit environment-pack selection must be
migrated before deploying the new GUI, so empty selection does not unexpectedly
replace the user's legacy environment bindings.

Next gates are the permitted local generation/import path for native host and
codec inputs, dependency notices/build provenance, environment-pack migration,
and an actual Inno Setup install/update/uninstall trial on clean Windows.
`installer.iss` remains explicitly a GUI development installer. The private
trial contains generated/derived files that current `docs/legal.md` keeps local;
it is not a payload to send to playtesters. No commits, uploads or publication
were performed.
