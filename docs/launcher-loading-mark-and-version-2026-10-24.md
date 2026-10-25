# Core Critical loading mark and version — 1.0.34

The launcher now places a 14-pixel Core Critical mark beside Game Status.
Its stationary amber sections receive a warm radial backlight in clockwise
order: upper-right, lower-right, lower-left, upper-left. Each light fades in
and out; the complete cycle takes 2.8 seconds. This indicates startup/asset
preparation activity, not measured percentage completion or a hang detector.

Native launch validation and preparation run away from the WPF dispatcher so
the mark and window can repaint. Launch settings are captured before worker
execution. Repeated launch clicks are blocked during preparation. The mark
stops when the native process starts or the launch fails, pauses while hidden
or minimized, and releases its animation clocks and preference subscriptions
on unload. Windows' disabled-animation preference produces steady light.
Existing asset-install status/progress remains in use, with the mark active
during installation as well.

## Version presentation and execution boundary

The launcher header shows `Core Critical 1.0.34` immediately before the detected
original executable version, normally `MechWarrior 3 1.2.22.0`. Both launcher
version labels derive from the actual launcher assembly version.

`GameRunner.CreateLaunchProfile` supplies that version to the native process
through `MW34_CORE_CRITICAL_VERSION`. The native title adapter prefixes only
MW3 captions. The actual main-menu footer also displays the Core Critical
version just left of the original white version text.

The footer is bitmap presentation rather than a Windows text control. The host
recognizes the original footer's white-stroke digest at its logical 640×480
location and draws the badge into the copied presentation buffer only. The
scrolling background is excluded from recognition. The guest surface and game
state are untouched, and unrelated frames do not receive the badge. The small
font coverage mask is cached. The native change preserves the host FP boundary
and last-error state around font creation. Missing/invalid optional version
text leaves the original presentation intact.

This advances launcher responsiveness and host menu presentation. It does not
change original gameplay or translate additional guest code. The previous
audio/controller/heap/graphics/performance repairs and default soundtrack are
retained. Formal native acceptance remains **131/144**. No performance gain is
claimed from these checks; Blender was active during this work, so no timing
comparison was attempted.

## Verification and delivery

Private evidence is retained at `D:/MW3LaunchIndicator-20261024-r2`:

- Real WPF control checks verify the four clockwise peaks, current version,
  idle state, minimized state, launch reset/failure cleanup and unload cleanup.
  The first run found clocks remaining attached after removal; explicit
  property animation cleanup fixes it, and the corrected checks pass.
- Full launcher fixtures and the native caption tests pass. Caption tests
  cover the original suffix, wide/ASCII strings, unrelated windows, duplicate
  prefixes and absent/invalid version input.
- Actual native menu capture shows the amber badge beside the original white
  version. A live window inventory verifies the prefixed window title. The
  final signed host presents 150 Vulkan menu frames, ending at the deliberate
  frame-budget exception (exit 1), not an interactive quit. The original
  translated module is unchanged; the source snapshot pins 151 host files.
- Signed full setup passes isolated fresh installation and all 664 registered
  runtime-file hashes. The actual installed 1.0.33 updater verifies/stages
  `1.0.34.ccupdate`; the signed launcher-only upgrade preserves the game runtime
  and user fixture. Uninstall registration is restored after the tests.
- The signed cumulative `1.0.34.mw3update` passes verification, installation,
  activation, validation and rollback from published runtime 1.0.33.
- DEV selects the same signed native runtime and launcher version; user
  preferences are preserved. Signed host SHA256 is
  `791e8ec706c06a1f7d612c7c07465ab52aa6a53535d800036af33724ea7de9f8`.

The launcher and game update use public version **1.0.34** and sequence
**2026102409** in their separate update state domains. Update metadata filenames
are `1.0.34.ccupdate` and `1.0.34.mw3update`, each with a matching `1.0.34.zip`
payload in a separate target folder. Download wrappers identify both version
and target. The game update requires launcher 1.0.34+. Full setup includes
both and needs no separate update on a fresh install.

Release targets on the protected playtest site:

- [Full signed installer](https://playtest.corecritical.dev/installers/2026-10-24-r6/corecriticalinstaller-1.0.34-preview.exe)
- [Launcher update download](https://playtest.corecritical.dev/updates/corecritical-1.0.34/1.0.34-cc-update.zip)
- [MW3 runtime update download](https://playtest.corecritical.dev/updates/1.0.34/1.0.34-mw3-update.zip)

The initial publication incorrectly removed the installer's version from its
cloud basename. The October 24 filename correction publishes the exact signed
build filename `corecriticalinstaller-1.0.34-preview.exe`, updates both download
catalogs, instructions and checksum, and leaves installer bytes unchanged.
Correction evidence is retained at `D:/MW3InstallerFilename-20261024-r1`.
Future publication must use `setup_filename` from the build receipt verbatim.

The private `completion.json` records successful publication: all nine
software/instruction objects and both catalogs verified by full R2 readback,
with signed-out requests still protected by Cloudflare Access. The downloaded
installer also has a valid Authenticode signature. Catalog edits
check for concurrent changes and preserve all unrelated asset/media entries.
The owner-approved individual signing identity remains in use. No Git commit
is made. A separate clean-Windows retest, all campaign missions, and automatic
updater-helper/restart UI are outside the checks performed here.
