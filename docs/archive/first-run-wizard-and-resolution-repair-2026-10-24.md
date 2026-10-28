# First-run wizard and detected-resolution repair — 1.0.32

Superseded later on October 24 by the
[1.0.33 CD-audio repair and default soundtrack](cd-audio-startup-and-default-soundtrack-2026-10-24.md).
The implementation/evidence below records the preceding release.

Published to both protected [playtest Setup catalogs](https://playtest.corecritical.dev/)
on October 24, 2026:

- [Full signed 1.0.32 installer](https://playtest.corecritical.dev/installers/2026-10-24-r4/corecriticalinstaller.exe)
- [1.0.32 launcher update](https://playtest.corecritical.dev/updates/corecritical-1.0.32/CoreCriticalLauncherUpdate.zip)
- [Cumulative native runtime repair](https://playtest.corecritical.dev/updates/mw3-display-resolution-20261024-r1/CoreCriticalGameUpdate.zip)

All nine release objects and both HTML catalogs were fully downloaded back and
hash-verified. The downloaded installer retains a valid timestamped signature.
Signed-out requests to the root, catalog and all three downloads reach Cloudflare
Access. Other download rows are preserved. Final `completion.json` and publication
receipts are retained in the wizard private root below. Installer SHA256:
`912e43ffa4e15dad4e83931cb0922e660d82aacd87d3b8009d5086b2b680164b`.
No portable release was uploaded and no Git commit/push was made.

The 1.0.30 clean-install report showed the coordinator's generic unsupported
graphics/assets error before native startup. The user changed no setup options.
The exact remote display size was not supplied; local reproduction identified
an inconsistency between automatic setup dimensions and the coordinator's
fixed resolution allowlist.

The exact unchanged signed host's `vk_scene.hpp::remaster_resolution` accepts
integer dimensions from 640 x 480 through 7680 x 4320. The packaged profile
advertised only a few common dimensions. Consequently 1536 x 864, 1366 x 768,
1920 x 1200 and 1280 x 1024 were rejected before the renderer could run. Windows
display scaling can also produce an automatically detected size outside that
list. The prior setup preference tests did not exercise the complete installed
launcher-to-coordinator admission path at these sizes.

## Changes

- `play_remaster.py` accepts explicitly advertised, bounded width/height ranges
  through `supported_graphics_ranges`. Other graphics choices retain their
  capability checks. Legacy profiles without ranges retain their original
  restrictions. Malformed, excessive and non-dimension ranges fail visibly.
- The error names the unsupported field/value and allowed values. `--check`
  now fails when the planned profile is unsupported; it previously returned
  success before checking that condition.
- Runtime staging preserves the new capability metadata. The corrected
  cumulative runtime is `mw3-display-resolution-20261024-r1`, sequence
  2026102406, compatible with launcher 1.0.30+. The signed host/module bytes
  and original game behavior are unchanged. DEV advertises the same bounds.
- `GameSetupWindow` uses four sequential pages: Game files, Display & graphics,
  Optional packs, and Review & install. Next validates the current page;
  installation/verification is available only on the final page. Back retains
  choices. Empty pack selection explicitly means stock content. Cancel does
  not save unfinished choices. Original-file verification and pack installation
  retain their existing strict underlying implementations.
- Launcher 1.0.32 includes the wizard; its launcher update has sequence
  2026102407. The full installer includes the corrected cumulative runtime.
  A 1.0.30 user can fix the resolution rejection with the game update alone;
  the launcher update adds the sequential setup experience.

## Validation

Private roots: `D:/MW3GraphicsLaunchRepair-20261024-r1` (resolution repair) and
`D:/MW3SetupWizard-20261024-r1` (final wizard/release).

- 23 focused Python capability, prepared-mech and presentation checks pass,
  including legacy behavior, malformed ranges, invalid AA/AF, boundary values,
  and failure status from `--check`. Full launcher fixtures also pass.
- The actual freshly installed 1.0.32 launcher assembly generates eight default
  launch profiles; its installed embedded coordinator accepts every profile:
  1280x1024, 1366x768, 1536x864, 1920x1080, 1920x1200, 2256x1504,
  2560x1440 and 3440x1440. A fixture binds the previously verified local original
  movie decoder, as normal game setup does; no original media is packaged.
- A 1366x768 native run presents 150 frames through Vulkan. Exit 1 is the
  explicitly requested frame-budget stop, not a successful interactive quit.
  This is a menu smoke check, not a campaign playthrough or performance claim.
- Actual WPF checks exercise invalid existing/media sources, required page
  progression, graphics capture, Back preservation, empty optional packs,
  review before install, cancellation, original-file verification, successful
  persistence and reloading Display controls. Native rendered captures of the
  existing-installation and review pages were inspected for layout/readability.
- Signed full setup installs into a fresh isolated directory; all 660 runtime
  files verify. The actual installed 1.0.30 updater stages and upgrades its
  launcher to 1.0.32, preserving runtime and a user fixture. Test uninstall
  registration is restored. Signed game-update install/activation/validation/
  rollback passes from both the published controller runtime and 1.0.30 stock
  runtime. Earlier harness path/provider failures are retained privately.

Separate clean-Windows retesting and the automatic updater helper/restart UI
remain unverified. Acceptance remains 131/144; no new native-function credit.

## Signing privacy and portable distribution

The existing individual certificate includes the publisher's legal name,
city, state and country; inspection found no street address or postal code.
The owner reported the disclosure and confirmed there is no registered business
yet. On October 24 the owner then explicitly authorized continuing the normal
signed playtest release for now. This release retains that signing identity;
it does not claim to remove personal publisher details or eliminate SmartScreen.
Future verified business signing requires the provider's identity validation.

A portable ZIP would still contain executable files and their signatures. The
current data root is AppData, runtime-update selection depends on application
location, and game/content paths can be absolute. Full extraction, relocation,
update behavior and Steam/shortcut integration need testing before advertising
true portability. No portable product was created or promised by this change.

See Microsoft's [Artifact Signing setup](https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart)
and [SmartScreen reputation guidance](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).
