# Campaign environment audit — October 24, 2026

All **20 installed campaign presets match the authored mission-lighting data**.
Three maps are sealed interiors: **C2M2, C2M4 and C3M5**. Their existing zero-sun,
no-outdoor-weather assignments are retained and now enforced by mission identity
even if an older pack supplies exterior settings. The current campaign plan has
been reconciled with the October 21 Operation 2 interior corrections.

The main visible mismatch was broader than C3M1: most missions only tinted
legacy cloud artwork, including clear-weather rows. The corrected native host
selects a clear daytime, twilight, clear-night, dust-haze, retained-cloud or
sealed-interior sky treatment by mission. Numeric sunlight, ambient, haze and
weather presets are unchanged. **This is a configuration/source/GPU audit with
a native Training smoke test, not an all-20 gameplay visual sign-off.**

The established schedule is project art direction. Its descriptive titles and
atmospheric explanations are not independently verified canonical lore.

The selected DEV profile has automatic campaign lighting and supported weather
enabled, manual lighting disabled, fixture shadows enabled, and **directional
sun shadows disabled**. This audit preserves those user settings. A preset
requesting long or crisp sun shadows cannot override the global disabled option;
the table does not claim those shadows are currently visible. Partial tunnels
inside an outdoor mission do not have a newly authored per-room weather mask.

## Mission-by-mission result

“Sky corrected” means the original storm-cloud texture no longer determines
the colour/pattern of the selected sky dome. Existing glow and horizon haze
still follow each mission's preset. Outdoor directional light at night is the
existing moonlight approximation, not an additional physical sun/moon system.

| Mission | Required setting | Audited/corrected native presentation | Remaining effect work or review |
| --- | --- | --- | --- |
| C1M1 | Clear, humid dusk; purple sky and low amber horizon | Clear twilight sky corrected; warm directional glow and purple haze retained | Humid scattering and complete in-map colour/readability review |
| C1M2 | Early night, coastal drizzle, damp surfaces | Cloud artwork retained; dark blue lighting and wet-surface response | Preset-driven rain density, rain catching weapon light, pooled reflections |
| C1M3 | Midnight, thick clouds, heavy downpour and lightning | Cloud artwork retained; dark lighting, wet response and lightning flash | New rainfall-density control, pooling/reflections and live storm review |
| C1M4 | Cold dawn, dense low valley fog | Cloud artwork retained; dawn glow, blue-gray haze and height-fog response | Dense localized/volumetric fog banks and sensor-readability review |
| C2M1 | Clear golden early morning, windblown track dust | Clear daytime sky corrected; golden light and dust-haze response | Wind-driven particles and source placement |
| **C2M2** | **Sealed industrial interior** | **Interior enforced: no sunlight, natural sky, exterior weather or sun shadows; existing warm ambient/fixtures retained** | Live interior review; former high-noon/smog draft superseded |
| C2M3 | Early afternoon, intense dust storm | Dust-coloured sky canopy corrected; warm light and strong dust-haze response | Moving dust, wind presentation and effective visibility tuning |
| **C2M4** | **Sealed power facility** | **Interior enforced; approved 0.40 ambient strength and fixture/weapon lighting preserved** | Live interior review; former outdoor electrical-storm draft superseded |
| C3M1 | Clear, dry high noon; heat shimmer | Preceding clear daytime repair retained; strong noon light and warm horizon | Genuine heat distortion/mirages; current heat channel adds colour only |
| C3M2 | Clear afternoon, canyon gusts and fine sand | Clear daytime sky corrected; warm light and sand-haze response | Gusts and moving sand particles |
| C3M3 | Crimson late afternoon, calm suspended dust | Clear twilight sky corrected; red/orange glow and dust haze retained | Static localized dust clouds and complete in-map colour review |
| C3M4 | Clear orange/purple dusk, sharp visibility | Clear twilight sky corrected; no dust/rain weather channels | In-map canyon silhouette/readability review |
| **C3M5** | **Sealed hangar, dim industrial lighting, vent mist** | **Interior enforced; local dampness and height-fog response retained; no natural sky or exterior weather** | Localized vent steam and evidence-based red/green emitters; no guessed lights added |
| C3M6 | Clear freezing desert night, stars and moons | Clear-night sky corrected; existing lunar-coloured directional light | Stars and visible moons are not implemented by the new sky path |
| C4M1 | Ash-covered volcanic midnight, lava illumination | Dark cloud/ash-canopy artwork retained; warm fill and particulate-haze response | Falling ash/embers and verified lava-emitter placement; no artificial map-wide lava light enabled |
| C4M2 | Deep pre-dawn, acid rain and sulfur mist | Cloud artwork retained; dark cool light, wetness and height-fog response | Preset-driven acid-rain particles, localized sulfur mist and floodlight review |
| C4M3 | Silver-blue false dawn, destruction dust | Clear twilight sky corrected; cool horizon glow and dust-haze response | Localized urban dust and street-level review |
| C4M4 | Pink/gold dawn, wind and horizontal smoke/debris | Clear twilight sky corrected; pink/gold light and haze retained | Wind-driven smoke/debris and source placement |
| C4M5 | Golden sunrise, rocket/explosion heat haze | Clear twilight sky corrected; gold directional glow and heat-channel tint | Actual heat distortion and glare/readability review |
| C4M6 | Brilliant clear blue daylight, maximum clarity | Clear daytime sky corrected; no rain, dust, ash or heat channels | Live final-mission visibility/shadow review; global user shadow preference remains respected |

The three interior overrides suppress outdoor precipitation/lightning, dust,
smog, heat shimmer, ash, lava fill, directional sunlight, sky glow and natural
sky/horizon colour. They preserve interior ambient hue/intensity, local damp
surfaces, height-fog response, material-based fixtures and weapon lights. The
existing ambient readability floor remains; C3M5's authored ambient of 0.18 may
be raised by that floor. C2M4's authored/effective 0.40 remains unchanged.

## Implementation gaps found by source tracing

- **Heat distortion:** `sun_scene.frag` reads the heat channel but adds a warm
  distance tint. It does not warp the image or create mirages. HUD/targeting
  coordinates are unchanged.
- **Rain and ash particles:** their intensities are stored/evaluated, but no
  current renderer consumer uses them to drive particle emission. Original-game
  rain/effects may still be present; that does not prove preset-driven weather.
- **Fog distance:** each preset has a `fog_distance`, but it is not consumed by
  the native rendering path. The original fog factors/global launcher fog
  controls and the existing height-fog shader response remain in effect. The
  table therefore does not certify the desired mission-specific visibility.
- **Environment-light lists:** the stored `env_lights` coordinates are parsed
  but never submitted as lights. Active fixture lights instead come from
  material/scene evidence, alongside weapon/effect lights. The audit does not
  activate unverified placeholder coordinates for wreckage, beacons or lava.
- **Wet reflections:** wetness darkens surfaces and adds a specular highlight;
  it is not a reflected scene, puddle system or pooled water simulation.
- **Localized weather and sky objects:** volumetric mist, vent steam, dust/ash
  particles, wind-driven smoke and independent stars/moon artwork remain open.

These findings supersede broad claims that all planned campaign weather is
fully implemented. No physics, sensor, AI, damage or mission-script changes
are authorized by the art schedule.

## Changes and checks

Maintained implementation:

- `tools/remaster-launcher/native-overrides/campaign_environment_policy.hpp`:
  explicit sky source and sealed mission identities.
- `tools/remaster-launcher/apply_campaign_environment_policy.py`: composes the
  policy after the C3M1 sky repair into the exact current host and recompiles
  both fragment variants; it does not replace the host with older common code.
- `campaign_lighting.hpp`, `sun_lighting.hpp` and `sun_scene.frag`: weather/light
  suppression for interiors and sky selection. An interior backdrop exits with
  black RGB and the original alpha, avoiding an undefined `smoothstep(0,0,...)`
  for C3M5's valid zero-width interior horizon interval.

The native Vulkan presentation/weather-selection boundary advances; original
guest simulation/resources and translated module are unchanged. The selected
composed uniform remains **912 bytes**; its previously unused sky selector
component carries the mode without changing descriptor/layout contracts.

Evidence directory: `D:/MW3CampaignEnvironmentAudit-20261024-r1`.

1. Full pack selection verifies the installed files and all 20 mission records.
   The installed JSON data equals `tools/remaster-launcher/mission-lighting.json`.
2. **640 authored CPU checks** cover all missions, mission-selection/menu/Training states,
   automatic/manual/disabled lighting, weather disabled, correct sky sources
   and retained interior dampness/mist. **150 additional checks** load an authored
   adversarial catalog with exterior sunlight, rain, lightning, ash and false
   interior flags in all three sealed maps; identity-based protection holds.
3. **320 actual Vulkan authored renders**, 160 per build, cover every mission's
   sky, horizon, textured distant terrain and HUD with two contrasting source
   textures. All clear/haze/interior skies are independent of legacy artwork;
   retained-cloud missions are pixel-identical to the predecessor. All 40 terrain
   and 40 HUD before/after pairs are pixel-identical. Interior sky/horizons are
   black. These are fixtures, not original-game screenshots.
4. Complete before/after uniform bytes change only the sky selector component
   for the existing presets. All other light/material/haze/weather bytes are
   identical. Manual and campaign-disabled outputs are completely identical.
5. An isolated copied-save native Training run reaches **500 real Vulkan
   presentations** and ends at the intentional frame-budget marker. No user
   saves, controls or active session are modified. All-20 native playthroughs,
   sustained performance and full mission visual review remain open.
6. The older combined campaign/fixture test fails its fixture-location assertion
   on both the predecessor and candidate. It is retained as an existing failure,
   not counted as a passing check. The new focused lifecycle tests pass.

One initial GPU command reused predecessor output paths. It was corrected to
separate audit outputs; the predecessor's original two-mission fixtures were
regenerated from their unchanged sources and the full audit comparison rerun.

Formal acceptance remains **131/144**. No commit or public upload is made by
this audit. The cumulative signed update and DEV activation are recorded in
the private `delivery.json`; public installer 1.0.29 is not automatically
replaced by this local repair.

The signed host is
`b8e8055b49015407da2b89a0fb2f7274e1db3492e34efa70345888ae00095b68`.
The local cumulative bundle is
`D:/MW3CampaignEnvironmentAudit-20261024-r1/CoreCriticalGameUpdate.zip`, containing
the signed `mw3-campaign-environment-20261024-r1.mw3update` and matching ZIP
(sequence **2026102403**, launcher **1.0.27+**). Install/activation/validation/
rollback checks pass against both the published controller runtime and the
preceding C3M1 DEV runtime. No source regeneration or asset-pack reinstall is
required for these policy changes. DEV preflight verifies the full selected
source snapshot and current asset pack closure.

## Next weather work

First visually review the corrected sky/timing in representative clear day,
twilight, night, dust, rain and sealed maps. Then connect the per-mission
visibility/rainfall controls and implement actual heat distortion for C3M1 and
C4M5, preserving the HUD and simulation. Author localized particles and emitters
from map evidence rather than enabling placeholder coordinates. Benchmark each
new effect with matched views before claiming campaign-wide completion.
