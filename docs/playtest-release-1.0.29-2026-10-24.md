# Current playtest launcher and cumulative runtime — 2026-10-24

Superseded later on October 24 by the
[1.0.30 branded installer and current native runtime](playtest-release-1.0.30-2026-10-24.md).
The evidence below records the earlier publication.

The owner's request to bring the protected playtest downloads up to date is
complete. Both existing Setup pages now offer Core Critical Launcher 1.0.29-preview,
the matching launcher update, and the latest cumulative MW3 native game update.

- [Playtest downloads](https://playtest.corecritical.dev/)
- [Full installer](https://playtest.corecritical.dev/installers/2026-10-24-r1/corecriticalinstaller-1.0.29-preview.exe)
- [Launcher update bundle](https://playtest.corecritical.dev/updates/corecritical-1.0.29/CoreCriticalLauncherUpdate.zip)
- [Cumulative MW3 game update](https://playtest.corecritical.dev/updates/mw3-controller-query-20261024-r1/CoreCriticalGameUpdate.zip)

The full installer embeds the same signed native runtime as the game update,
including the controller `GetObjectInfo` startup repair and all previous R7
performance, missile/PPC, status-model and full-bank texture fixes. Fresh installs
need no second game-code update. Existing installations can update the launcher
with `.ccupdate` (minimum 1.0.27), then import the cumulative `.mw3update`.
Ordinary ZIP bundles contain each signed metadata/payload pair to avoid unfamiliar
download-extension handling. Original inputs remain required and verified;
no client-side native code generation is needed. Optional content packs stay separate.

The launcher adds the editable MW5-style and MW3-default presets already present
in DEV. Existing layouts, controller settings, packs and saves are preserved.
Calibration alone does not enable modern controller gameplay; that remains a saved
choice in MW3 bindings. This release does not change gameplay or acceptance credit.
Formal accepted count remains **131/144**.

## Identity

| Artifact | SHA-256 |
| --- | --- |
| Full 1.0.29 installer | `b92ee506d76cb5ac560966219d55dcf53019dbd212de76b7a3ae3ff8f9994e60` |
| Latest native executable | `1feb3c5875e3affe88b6d71cf45748bfa098006b7d1dd771d2686e2fa1b0c034` |
| Cumulative game bundle | `50b022a797091bbf34811687e546f6c7c8bd0dad9a605e3967ef1480d3eaa9c3` |

Both launcher and game update use sequence 2026102401 in their independent state
domains. The launcher application version is 1.0.29.0; the release label is
1.0.29-preview. The translated native module is unchanged from R7.

## Validation and publication evidence

Private root: `D:/CoreCriticalPlaytest-1.0.29-20261024-r1`.

- Self-contained Release publication, media-tool admission, complete launcher
  fixture suite, and controls-specific checks pass.
- The full signed installer was installed into a fresh isolated directory. All
  runtime manifest files match, including the latest signed host.
- A real installed 1.0.28 launcher assembly verifies and stages the signed 1.0.29
  `.ccupdate`. Its exact staged signed installer upgrades the isolated app to the
  new release. The existing runtime and a user-file fixture remain unchanged.
- These tests do not exercise automatic helper/restart UI or establish a new
  clean-machine Windows result. Tests do not interrupt the player's game session.
- All nine release objects are uploaded and completely downloaded back; every
  size/SHA-256 matches. The readback installer has a valid timestamped Windows
  signature. Each prefix includes instructions and SHA256SUMS.
- Both HTML objects are guarded against concurrent changes before publication
  and read back identically afterward. All non-Setup rows and the ISO/patch rows
  remain unchanged. The combined model and stock texture releases are preserved.
- Signed-out checks of the root/catalog and installer redirect to Cloudflare
  Access. No DNS, Access policy, bucket public URL or main website deployment changed.

Key evidence: `Release/launcher-release.json`, `installer-checks.json`,
`launcher-checks.log`, `files-publication.json`, `catalogs-publication.json`,
`access-check.json`, and `source-pins.json`. Earlier fixture/harness failures stay
retained and are not counted as passing validation. No Git commit/push was made.
