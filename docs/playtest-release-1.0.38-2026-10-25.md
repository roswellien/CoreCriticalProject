# Core Critical 1.0.38 — online updates

Published signed launcher **1.0.38-preview**, its matching `.ccupdate` bundle,
and a signed online release catalog on October 25. Native runtime remains
**1.0.37**, unchanged from the preceding release. The new full installer
includes that runtime. Existing users upgrade the launcher once, then use
**Settings & Steam → Updates** for discovery, downloads and installation.

- [Full installer](https://playtest.corecritical.dev/installers/2026-10-25-r3/corecriticalinstaller-1.0.38-preview.exe)
- [One-time launcher update bundle](https://playtest.corecritical.dev/updates/corecritical-1.0.38/1.0.38-cc-update.zip)
- [Playtest downloads](https://playtest.corecritical.dev/packs/2026-10-21-r2/index.html)

Updates now have a shared screen, byte progress, pause/cancellation, verified
caching/resume, independent installed/bundled version reporting, launcher-first
ordering, saved restart continuation and runtime rollback. Existing local signed
imports remain available. Downloads do not hold the installation gate. Game
launch and installation share a cross-process gate; installations never close
the player's game automatically. Failed runtime installation keeps the previous
selection. An interrupted Inno replacement still requires the signed setup
repair path; whole-launcher atomic rollback is not claimed.

The owner selected public **update-only** delivery. A read-only Worker exposes
the promoted signed catalog and four approved metadata/payload objects. Full
installers, content packs, original ISO/patch links and both download catalogs
retain their existing Cloudflare Access protection. No bucket listing or write
API is exposed. Existing asset/media rows and historical objects were retained.
The operational contract is in [update-service documentation](../tools/update-service/README.md).

## Verification

- Complete C# launcher fixture suite passes, including signed catalog freshness,
  channel/product/architecture/host policy, dependency planning, independent
  package checks, resume, cache tampering, invalid ranges, cancellation,
  inactivity and launch/install exclusion. Three Worker tests pass.
- Actual released launcher 1.0.37 imported the real signed 1.0.38 package through
  its UI, closed, ran the copied helper and installer, and restarted at 1.0.38.
  Its entire runtime and user fixture were preserved. This was not a stage-only
  or direct full-installer upgrade check.
- Installed 1.0.38 discovered, downloaded, verified and installed runtime
  1.0.37 online over a verified 1.0.34 baseline. UI reporting distinguished the
  newly selected runtime from the bundled baseline. Explicit rollback returned
  to 1.0.34 while retaining the installed version and highest sequence.
- A private online-enabled 1.0.37 source prototype exercised the two-product
  workflow against the real signed release: both downloads, launcher-first
  helper replacement, automatic reopening of the saved plan in 1.0.38, fresh
  catalog/helper-result checks, then runtime activation and pending-plan removal.
  The prototype was not a shipped version of 1.0.37; the ordinary released
  launcher/helper upgrade above was checked separately. Minimum-launcher
  dependency rejection/order is additionally covered by signed fixtures.
- The signed full 1.0.38 installer completed a separate fresh isolated install.
  Every bundled runtime member, launcher DLL and online configuration matched
  the staged identities. No native code generation was invoked.
- A private byte-identical copy of the actual online-installed runtime and its
  selection state launched through `GameRunner` with copied original inputs and
  isolated player data. It reached the live menu and closed normally, exit 0.
  Initial fixture attempts correctly rejected missing original support files
  and a junction in the original-data tree; those failures are retained.
- All four public artifacts passed complete HTTP size/hash readback and real
  Range checks. Public asset/media paths returned 404 and write methods 405.
  Six bootstrap download objects and six private website catalog objects were
  read back from R2 with matching hashes. Catalogs were promoted after artifacts.

Evidence is local at `D:/CoreCriticalOnlineUpdates-20261025-r1/`, including signed
build receipts, public/private publication journals, helper result/setup log
references, preserved failure logs and integration outcomes. Test applications
used custom directories; temporary uninstall registration and incidental legacy
settings serialization are restored after the trials. The original settings'
existing values were not changed by the updater; older files acquired three
default/migration fields when the historical launcher UI opened.

This is local standalone Windows evidence. A clean second-PC test, protected
directory elevation, MSIX execution, forced mid-Inno interruption/restart failure
and a dedicated 125% scaling run remain unverified. Native gameplay/renderer
acceptance remains **131/144**. No native recompile, Git commit or push was made.
