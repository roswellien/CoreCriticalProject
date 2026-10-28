# Stock presentation and first-run graphics — October 24, 2026

The first implementation milestone of the stock/community-pack direction is
available in **Core Critical 1.0.30-preview**. Normal launcher sessions use only
explicitly enabled content. With no packs and Dynamic Lighting off, replacement
models/banks/normals/UI, remaster campaign presets, weather shading and enhanced
missile exhaust are not activated. Compatibility, crash and performance fixes
remain. User-selected resolution, AA/AF, scenery and fog options still apply;
this is not a claim of pixel-perfect retail parity or complete campaign fidelity.

## Setup and saved graphics

Set Up Game now has **Game files**, **Display & graphics** and **Optional packs**
tabs. Setup and the normal Display tab share `GraphicsPreferencesPanel` and the
validated `GraphicsPreferences` value object. They expose:

- Resolution and borderless/fullscreen/windowed mode.
- FXAA, 2x/4x SSAA or AA off; AF 1x/2x/4x/8x/16x.
- Scenery draw distance and original/extended horizon fog.
- Dynamic Lighting and an independent saved Shadows choice.

Successful original-file verification/installation saves these choices before
setup returns and reloads Display. Cancelling leaves existing preferences
unchanged. A new installation remains marked incomplete until setup succeeds;
simply writing defaults or cancelling is not completion. Existing settings files
without the new marker are treated as already configured, retaining their saved
display and pack choices. Users can reopen Set Up Game to review the new panel.

New lighting/shadow choices default off. Shadows require Dynamic Lighting for
their added rendering, but turning lighting off preserves the saved shadow
preference. Original-game shadow draws are not removed by this remaster switch.
Mission interior/shadow restrictions still apply when enhanced lighting is on.

## Stock and pack composition

`GameRunner.ApplyContentSelection` composes explicit selections, including empty
lists, in DEV and installed launches. The former DEV environment-registry
fallback is removed. First-run discovery no longer enables every installed pack
automatically; existing explicit choices and order are retained. UI/cinematic/
model bindings clear when their packs are disabled.

`presentation_policy.py` applies the saved lighting/shadow choices after content
composition and again after resource-cache reuse. Pack preparation cannot turn
disabled lighting back on. No-pack lighting-on uses identity ambient/direct
lighting, the original sky/weather, and added fixture/weapon lights. It does not
select the remaster campaign schedule. Original source lighting colours remain
the receiver baseline before added lights.

The runtime includes an original-only full-colour material catalogue: **869 exact
native pixel identities** from the user's original banks. It contains hashes,
dimensions and authored light parameters, not texture images. Dynamic lighting
therefore works without an upgraded texture pack. A native-variant impact-power
option fixes ambiguous source-frame alpha quantization for this catalogue; the
existing strict authoring default remains unchanged. Catalogue creation is an
offline authoring step; NumPy is not added to the shipped runtime.

Original user-supplied soundtrack tracks in the recognized game `Music` folder
can play without a replacement music pack. Enabled soundtrack packs take
priority; audio off still wins. This does not recover CD audio absent from the
user's supplied files or implement arbitrary soundtrack naming/import formats.
Music preparation now respects the selected per-session asset output directory.

`MW3Launcher.cmd` now starts the actual `Core Critical Launcher.exe` rather than
falling back to the retired executable name. The normal DEV launcher is rebuilt
and signed. Explicit research/preview profiles without the new presentation
contract retain their diagnostic workflow.

## Checks and limits

Private evidence roots are `D:/MW3StockPresentation-20261024-r1` and the final
`D:/MW3StockPresentation-20261024-r2`; r1 release artifacts are superseded.

- **35 Python tests** cover pack composition, stock cleanup, cached off/on/off
  changes, disabled selections, mission catalogs, shadow preferences and invalid
  contracts. **Three effect-catalogue oracles** cover exact alpha transport,
  invalid spans and identical native impact pixels with different source alpha.
- The complete C# launcher suite passes, including graphics validation,
  persistence, new/legacy setup markers, retained pack choices and soundtracks.
- An actual isolated WPF run opens first-run setup automatically, captures all
  graphics choices, cancels without changes, verifies original game files on a
  second setup, completes successfully, saves every preference and reloads the
  same values in Display. Lighting/shadow controls and their persistence are
  exercised in the real windows. Preview images are in final `UiCheck`.
- Four isolated native Training checks cover no-packs/packs with lighting off/on,
  **500 real Vulkan presentations each**. Original models/textures/HUD/sky are
  present in the no-pack case; added light payloads are absent with lighting off.
  A further final 500-presentation check covers lighting on/shadows off. Each
  deliberately ends at the checked frame-budget marker, not a gameplay crash.
- The cumulative signed game update is verified, installed, activated, validated
  and rolled back against both the published controller runtime and the current
  vehicle-repair runtime.
- The exact signed full installer passes a fresh-directory install. Actual
  installed **1.0.29** updater code verifies/stages the **1.0.30** launcher-only
  package, whose installer upgrades an isolated install while preserving its
  previous game runtime and user fixture. The temporary uninstall registration
  is restored. A separate clean Windows PC and automatic helper restart UI were
  not tested.

The selected signed native executable/translated module and all native source
pins are unchanged from the current vehicle/heap/controller/performance repair.
This advances launcher/coordinator selection and setup boundaries; there is no
new native-function acceptance credit. Formal acceptance remains **131/144**.
The native smoke tests are not all-mission playthroughs or performance benchmarks.

## Delivery and remaining work

Final private artifacts:

- Full signed `FullInstaller/corecriticalinstaller-1.0.30-preview.exe` includes
  the precompiled current runtime and first-run setup. No code regeneration or
  mandatory content packs are required.
- `CoreCriticalLauncherUpdate.zip` contains the signed `.ccupdate`, matching
  payload ZIP and instructions.
- `CoreCriticalGameUpdate.zip` contains the signed cumulative
  `mw3-stock-presentation-20261024-r2.mw3update`, matching payload ZIP and
  instructions (launcher **1.0.30+**). Existing installs update the launcher
  first, then the game runtime. Fresh full setup already includes both.

All three live under `D:/MW3StockPresentation-20261024-r2`. Artifact identities
and DEV activation are in its `delivery.json`. Nothing is uploaded or committed.
Original media, generated source and signing keys are excluded from packages.

Existing v1 environment packs still bundle textures/normals and their authored
conditions; those conditions are activated with enhanced lighting. Separating
texture-only and independent environment/effects components is the next stage.
Enhanced missile exhaust is deliberately not an unconditional stock default;
it needs explicit effects-pack ownership. New map/mission/chassis/weapon IDs and
editor-to-runtime publishing still require their planned registries/hooks. This
milestone does not advertise those capabilities as implemented.
