# Playtest launcher 1.0.40 and native runtime 1.0.39

Published October 25, 2026 to the signed online update feed and both existing
playtest download catalogs, under Setup. Automatic checking remains opt-in and
off by default for new and existing users. Setup and Settings & Steam expose
the same saved preference; manual checking, download and installation remain
available regardless of that preference.

Current files:

- Full installer: `corecriticalinstaller-1.0.40-preview.exe`, including freshly
  compiled native MW3 runtime 1.0.39 and the existing default soundtrack.
- Launcher update: `1.0.40.ccupdate` with matching `1.0.40.zip`.
- Native runtime update: `1.0.39.mw3update` with matching `1.0.39.zip`.
- Optional download wrappers: `1.0.40-cc-update.zip` and
  `1.0.39-mw3-update.zip`, each containing the correctly named metadata/payload
  pair and instructions.

The native host was freshly compiled from the pinned, validated chassis-selection
source, linked to the retained translated native module, signed and packaged.
It preserves pack chassis through original Instant Action roster validation,
including unlimited inventory-item behavior for Commander and lancemates sharing
one chassis. Commander, three lancemate and six enemy selectors discover added
chassis from packs. Existing skins, preview framing, controls, audio, graphics
and performance work are retained. No game-specific mod registration is hardcoded.

The execution boundary tested is installed catalog -> original selection and
inventory validation -> original configuration construction -> live native
mission actors. A fresh bounded Instant Action run created three Marauder
actors and rendered Marauder without a Strider substitution. Its 2,200-frame
budget stop is intentional. Sustained combat and clean external-PC coverage
remain playtesting work; strict acceptance stays 131/144.

Actual installer checks upgraded a signed 1.0.39 installation using the
launcher-only 1.0.40 installer, preserving its runtime and user fixture. The
signed native update installed, activated, passed complete runtime validation
and rolled back with sequence retention. The full 1.0.40 installer then installed
runtime 1.0.39 with all file hashes matching. Test installations were removed and
the previous uninstall registration restored.

All four public metadata/payload objects passed full download hash and HTTP
Range checks before signed catalog sequence 2026102506 was promoted. The live
DEV launcher subsequently discovered runtime 1.0.39 from that feed. Nine private
Setup objects and six private catalog objects passed complete R2 readback checks.
Original-media links, asset rows and historical public update routes were retained.
The website, original media and optional asset packs remain access-protected.

Private local evidence: `D:/CoreCriticalUpdateNoticeRelease-20261025-r1/`,
including `completion.json`, signing receipts, native build/run evidence,
installed-upgrade results, cleanup receipt, object readbacks and catalog copies.
Original game inputs and generated source remain local. No commit was made.
