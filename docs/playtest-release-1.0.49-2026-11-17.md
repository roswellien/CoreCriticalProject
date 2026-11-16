# Launcher 1.0.49 playtest release: MW3-RE is the game

Release preparation for the November 2026 playtest (#301). This records intended scope, not
completed publication. Build only from the exact merged source after its checks pass.

## Changes

- **MW3-RE is the default and only shipped game runtime.** Play starts the native MW3-RE engine
  with your saved resolution, window mode (windowed, fullscreen or borderless), antialiasing,
  anisotropic filtering, scenery distance and enabled prepared mech and map packs. The old
  precompiled Remaster runtime is no longer shipped, and upgrading removes its installed
  `Runtime` folder. The separate "Original Game (D7VK)" developer option is unchanged.
- **Selectable view distance.** Scenery distance 800 (original, default), 1200 or 1600. Only
  rendering sees the longer range: targeting range, vehicle code and other gameplay keep the
  mission's authored camera range, and 800 behaves exactly as before. Fog stretches with the
  view so the far edge fades instead of cutting off. A saved 2400 or 3200 loads as 1600.
- **Renderer fixes for the playtest:** native scene-lighting cache retirement and overflow-draw
  preservation (#319), native weapon and fixture lighting (#320), owned producer views through
  native submission (#321), native sky semantics during geometry handoff (#322), validated
  distance donor toes for the replacement mechs (#323), and native sky kept out of ordinary
  surface sun and normal lighting so it no longer shows dark panels and seams (#328).

## Delivery

- `corecriticalinstaller-1.0.49-preview.exe`: the launcher, the MW3-RE runtime and its planner.
- `1.0.49.ccupdate` with its matching launcher `1.0.49.zip` updates the launcher only. Players
  coming from 1.0.48 should run the full 1.0.49 installer, because the MW3-RE runtime is
  delivered by the installer in this release.

Players need their original game files. The shared-mech texture bank (over 2 GiB) is not
loaded by MW3-RE; that pack is left out and reported in the session log.

## Validation and known limits

- Each change had two independent non-author model reviews and passed CI. The merged source
  passes the asset-free suite, GPU adapter checks (materials in four presentation/thread
  variants, geometry, prepared, producer view, POM) and the launcher runtime-layout checks.
- Not yet verified: owner gameplay at 1200/1600 (pop-in and horizon appearance), signed
  installer build, clean-machine install and upgrade from 1.0.48.
- Known open visual issues: Big Lake horizon bands are not fully resolved; 2400/3200 distances
  are not in this release; a runtime update channel for MW3-RE is future work.
