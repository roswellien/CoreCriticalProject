# Launcher 1.0.49 playtest release: MW3-RE is the game

Release preparation for the November 2026 playtest (#301). This records intended scope, not
completed publication. Build only from the exact merged source after its checks pass.

## Changes

- **MW3-RE is the default and only shipped game runtime.** Play starts the native MW3-RE engine
  with your saved resolution, window mode (windowed, fullscreen or borderless), antialiasing,
  anisotropic filtering, scenery distance and enabled prepared mech and map packs. The old
  precompiled Remaster runtime is no longer shipped, and upgrading removes its installed
  `Runtime` folder. The separate "Original Game (D7VK)" developer option is unchanged.
- **Selectable view distance.** Scenery distance 800 (original, default), 1200, 1600, 2400 or 3200.
  Only rendering sees the longer range: targeting range, vehicle code and other gameplay keep the
  mission's authored camera range. Original-style proportional haze scales with the view distance,
  and an altitude-independent edge band covers distant cuts, including high terrain and fog-off
  missions. At 800, geometry remains unchanged. Saved 2400 and 3200 choices retain their selection.
- **Renderer fixes for the playtest:** native scene-lighting cache retirement and overflow-draw
  preservation (#319), native weapon and fixture lighting (#320), owned producer views through
  native submission (#321), native sky semantics during geometry handoff (#322), validated
  distance donor toes for the replacement mechs (#323), and native sky kept out of ordinary
  surface sun and normal lighting so it no longer shows dark panels and seams (#328).

## View-distance fog

The single runtime table is `kViewDistanceOptions` in
`runtime/mw3-re/src/gamez/zclass/visual_distance.h`. Owner playtests selected these edge-band
starts to hide geometry pop-in. They do not replace the mission's proportional haze interval.
This is render-only view-distance cover, independent of weather fog.

| View distance | Edge start | Full edge fog |
| --- | --- | --- |
| 800 | 700 | 800 |
| 1200 | 1050 | 1200 |
| 1600 | 1450 | 1600 |
| 2400 | 2250 | 2400 |
| 3200 | 3050 | 3200 |

Mission near/far distances are multiplied by `visual_far / authored_far`. For example, c3 hardware
fog 32–750 m becomes 48–1125 m at 1200 and 128–3000 m at 3200, retaining visible haze at long
distances. A linear interval extending beyond the cut is capped at the visual far distance,
with its start clamped between the table start and the cut. Shorter mission intervals retain
their proportional haze; exponential density retains its inverse-distance scaling.

The mission altitude taper remains authored. A separate linear edge amount ramps from zero at
the table start to one at the cut, regardless of altitude or mission fog on/off. The combined
amount is `1 - (1 - mission_amount) * (1 - edge_amount)`, so terrain at Y=500 cannot escape edge
fog. Both terms use the same colour. Campaign lighting retains its existing sky-matched haze
selection and also applies it to world-frame clears; lighting off retains the mission colour.
Above the horizon blend's lower boundary, fully fogged terrain still uses haze rather than the
sky dome's elevation-dependent colour; the optional colour feather is not included here.

At 800, only qualifying world cameras with an authored far plane of 800 receive the fog scope;
outside its edge band the authored proportional interval is retained. CPU sampling inside a
scope uses Euclidean horizontal distance to match the GPU, while unscoped original fog retains
its legacy square-root approximation. Geometry and gameplay clips stay unchanged.
The 2400 and 3200 options cost much more GPU time and still need gameplay validation.

## Delivery

- `corecriticalinstaller-1.0.49-preview.exe`: the launcher, the MW3-RE runtime and its planner.
- `1.0.49.ccupdate` with its matching launcher `1.0.49.zip` updates the launcher only. Players
  coming from 1.0.48 should run the full 1.0.49 installer, because the MW3-RE runtime is
  delivered by the installer in this release.

Players need their original game files. The shared-mech texture bank (over 2 GiB) is not
loaded by MW3-RE; that pack is left out and reported in the session log.

## Validation and known limits

- The prior playtest baseline had two independent non-author model reviews and passed CI. Its source
  passes the asset-free suite, GPU adapter checks (materials in four presentation/thread
  variants, geometry, prepared, producer view, POM) and the launcher runtime-layout checks.
- Not yet verified: proportional haze, altitude-independent edge fog, sky-matched world clears
  and their new fixtures need coordinator builds, tests and independent review; owner gameplay
  at all five distances (pop-in and horizon appearance), signed installer build, clean-machine
  install and upgrade from 1.0.48 also remain unverified.
- Known open visual issues: Big Lake horizon bands are not fully resolved; a runtime update
  channel for MW3-RE is future work.
