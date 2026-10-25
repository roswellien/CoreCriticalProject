# Campaign lighting and mission progression

Updated **2026-10-20** from the user's replacement campaign plan. Status:
**active art direction for all 20 campaign missions; automatic mission selection
and supported environment shading wired in R7**. Configuration/lifecycle checks
cover all 20 identities; bounded native checks cover Operation 1 Missions 1 and 3.
Full campaign visual review and the remaining weather effects are still open;
see the [repair evidence and limits](world-lighting-repair-2026-10-20.md).
This revision supersedes the previous twelve-entry schedule.
The [2026-10-18 plan](campaign-lighting-progression-plan-2026-10-18-superseded.md)
is retained as a historical reference; its conflicting timings and environments
no longer govern implementation.

## Scope and campaign order

| Operation | User's operation label | Mission map IDs | Lighting progression |
| --- | --- | --- | --- |
| 1 | The Beachhead — Tropical/Coastal Basin | `c1m1`–`c1m4` | Dusk → early night → midnight → foggy dawn |
| 2 | The Industrial Sector — High-Plains Badlands | `c2m1`–`c2m4` | Early morning → sealed industrial interior → early afternoon → sealed power facility |
| 3 | The Desert Plain — Arid Canyonlands | `c3m1`–`c3m6` | Noon → afternoon → dusk → underground interior → surface nightfall |
| 4 | The Core — Volcanic Caldera & City Center | `c4m1`–`c4m6` | Volcanic midnight → pre-dawn → first light → dawn → sunrise → full daylight |

The numbered entries below bind the user's proposed appearance to the recovered
campaign map order, **4 / 4 / 6 / 6**. Operation subtitles, mission titles,
locations and atmospheric explanations are supplied art-direction labels;
verify them against the actual maps and original briefings before placement.
They do not rename in-game missions or establish new canonical facts.
`c4m4`–`c4m6` use assets in the `c4b` region; that is not a fifth operation.

This replacement specifies relative times of day, but does not assign campaign
day numbers, exact hours, transition durations or event triggers. Do not invent
these assignments. The previous eight-day / roughly 27-hour-day framework remains
historical context pending reconciliation with this revision, not an implemented
clock or an explicit day assignment for any entry below. Individual mission
start/end transitions also remain to be authored unless explicitly described.
The Operation 2 mission-specific early-morning start takes precedence over its
broader introductory description of midday conditions.

## Mission-by-mission art direction

The following descriptions preserve the user's replacement schedule. Statements
about desired weather, visibility, reflections and environmental effects are
requirements to evaluate and implement, not claims about current capabilities.

## Operation 1 — The Beachhead (Tropical/Coastal Basin)

The campaign opens at dusk, moves into pitch black, and concludes under a dense, foggy morning dawn.

### Mission 1 — Dropzone (`c1m1`)

- **Time of day:** Dusk (Late Twilight). The sky is a deep, bruised purple fading into low amber on the horizon. Long, dramatic shadows stretch across the terrain.
- **Weather:** Clear but humid. The ocean air creates a slight atmospheric haze that scatters the light of low-angle weapon trails.

### Mission 2 — Beachhead (`c1m2`)

- **Time of day:** Nightfall / Early Night. Pitch black overhead, but the environment is artificially illuminated by burning drop-pod wreckage, distant base searchlights, and defensive flares.
- **Weather:** Light coastal drizzle. Rain drops should catch the glare of lasers, and the damp ground should provide sharp, wet reflections from explosions.

### Mission 3 — Bridgehead (`c1m3`)

- **Time of day:** Dead of Night (Midnight). Total reliance on night vision and thermal imaging. The sky is starless, choked by thick clouds.
- **Weather:** Heavy tropical downpour. Rain streaks obscure long-range visibility, and pooling water on the ground creates dynamic reflections. Lightning flashes occasionally silhouette the terrain and enemy mechs.

### Mission 4 — Hydro-Plant (`c1m4`)

- **Time of day:** Dawn (Early Morning). The sun is just cracking the horizon, casting a cold, pale blue-gray light across the massive dam structure.
- **Weather:** Low-lying valley fog. The river basin below the dam is completely choked with thick, heavy mist, requiring pilots to rely on sensors until enemy units emerge from the fog bank at close range.

## Operation 2 — The Industrial Sector (High-Plains Badlands)

Outdoor sections use high-plains morning/afternoon conditions. The installed
map-specific corrections of October 21 identify `c2m2` and `c2m4` as sealed
industrial interiors; those corrections take precedence over the earlier
outdoor midday/smog and late-afternoon electrical-storm draft for those two
rows. The October 24 campaign audit reconciles that direction here. Outdoor
weather and natural sky illumination must not be introduced into either map.

### Mission 1 — Trainyard (`c2m1`)

- **Time of day:** Early Morning. Sharp, crisp golden light striking the high-altitude plains.
- **Weather:** High winds and clear skies. Dust kicked up by passing mag-lev trains creates localized windblown sand particles across the tracks.

### Mission 2 — Industrial Complex (`c2m2`)

- **Lighting:** Indoor / Sealed Environment. Functional industrial fixtures and
  the approved warm, dim ambient fill; no natural sunlight, sky or horizon glow.
- **Atmosphere:** Enclosed industrial air. Preserve authored interior effects;
  do not apply exterior rain, lightning, dust storms, volcanic ash or heat haze.
  This supersedes the former outdoor high-sun/smog assignment.

### Mission 3 — Mining Facility (`c2m3`)

- **Time of day:** Early Afternoon. The sun begins to slope, casting deep shadows into the open-pit excavation sites.
- **Weather:** Intense dust storm. Heavy particulate matter in the air reduces optical visibility drastically, forcing reliance on radar, while shifting winds buffet lighter mechs.

### Mission 4 — Power Plant (`c2m4`)

- **Lighting:** Indoor / Sealed Environment. Preserve industrial fixtures and
  the user-selected map ambient strength of **0.40**. No natural sunlight,
  sky/horizon glow or directional sun shadows.
- **Atmosphere:** Enclosed power facility. No exterior precipitation or
  lightning. This supersedes the former outdoor orange-sky/electrical-storm
  assignment and does not disable weapon or fixture lighting.

## Operation 3 — The Desert Plain (Arid Canyonlands)

A blistering descent into a dry, sun-scorched canyon system that cools down into an ominous twilight.

### Mission 1 — Canyon Approach (`c3m1`)

- **Time of day:** High Noon. Blistering, washed-out sunlight that bakes the red canyon rock.
- **Weather:** Extreme heat shimmer. Severe mirage effects warp distant horizons and long-range targeting reticles. The air is bone-dry.

### Mission 2 — Outpost (`c3m2`)

- **Time of day:** Mid-Afternoon. Harsh light cutting directly into the deep, narrow rock fissures.
- **Weather:** Wind-tunnel gusts. High-velocity winds howl through the canyons, kicking up columns of fine sand that partially obscure low-ground targets.

### Mission 3 — Fuel Depot (`c3m3`)

- **Time of day:** Late Afternoon. The sky turns a deep, fiery crimson as the sun sinks behind the canyon rims.
- **Weather:** Calm but hazy. A thick layer of heavy, unmoving dust sits in the basin, settling onto the military structures.

### Mission 4 — Supply Depot (`c3m4`)

- **Time of day:** Dusk. Deep orange and purple sky. The shadows of the canyon walls completely swallow the valley floor, leaving only the tops of structures illuminated.
- **Weather:** Clear. Rapidly cooling air creates clean, sharp visibility, making thermal signatures pop vividly against the freezing desert sand.

### Mission 5 — Underground Hangar (`c3m5`)

- **Time of day:** Indoor / Sealed Environment. No natural sky.
- **Weather:** Subterranean air filtration. Dim, functional industrial lighting (emergency reds and mercury-vapor greens). Mist from underground cooling vents and leaking pipe steam creates localized blindness in corridors.

### Mission 6 — Comm Array (`c3m6`)

- **Time of day:** Night fall. Emerging back onto the surface under a clear, starlit sky dominated by Tranquil's moons.
- **Weather:** Freezing desert night. Crystal-clear air with crisp visibility, though the pitch-black shadows of the terrain offer perfect cover for ambushes.

## Operation 4 — The Core (Volcanic Caldera & City Center)

The final push starts in a hellish volcanic night and builds toward the symbolic, final-sunrise climax.

### Mission 1 — Caldera (`c4m1`)

- **Time of day:** Midnight (Volcanic Glow). The sky is completely blotted out by a dense canopy of volcanic ash.
- **Weather:** Ash fall. Burning embers and heavy gray soot drift down like snow. The primary illumination comes from the glowing orange lava flows below, casting an eerie, underworld under-lighting onto the mechs.

### Mission 2 — Fortress (`c4m2`)

- **Time of day:** Pre-Dawn (Deep Night). The absolute darkest part of the night just before the sun breaks.
- **Weather:** Acid rain/Sulfuric mist. A caustic, chemically active fog rolls off the volcanic vents, corroding visibility and creating a heavily diffused, spooky glow around exterior base floodlights.

### Mission 3 — City Streets (`c4m3`)

- **Time of day:** First Light (False Dawn). A thin, horizontal strip of silver-blue light cuts across the skyline, while the street level remains cast in deep shadow.
- **Weather:** Clear but choked with urban destruction. Dust from collapsed buildings floats in static clouds down the city corridors, catching the early light.

### Mission 4 — Starport (`c4m4`)

- **Time of day:** Dawn. The sky shifts rapidly into vibrant pinks and golds as the sun begins to breach the skyscrapers.
- **Weather:** Windy. Heavy crosswinds sweep across the open tarmac of the spaceport, blowing smoke and debris horizontally across the combat zone.

### Mission 5 — Control Tower (`c4m5`)

- **Time of day:** Morning Sunrise. The sun clears the horizon, flooding the battlefield with an intense, blinding gold glare directly into the player's primary optical view.
- **Weather:** Heat haze from burning rocket fuel and base explosions, creating rippling air currents that distort the final defensive line.

### Mission 6 — Final Confrontation (The Dropship / Core) (`c4m6`)

- **Time of day:** Final Full Sunrise. The sky clears into a brilliant, unblemished, triumphant sky-blue. The bright daylight symbolizes the breaking of the Clan hold on the planet.
- **Weather:** Perfectly clear. Total atmospheric clarity. Shadows are crisp and sharp, offering maximum visibility for the ultimate duel.


## Integration rules and remaining decisions

1. **Use this schedule as the active source.** In particular, Operation 1 Mission 1
   is now clear/humid dusk, Mission 3 is stormy midnight, and Mission 4 is foggy
   dawn. The former storm-at-insertion and Mission-3-dawn assignments are superseded.
   Operation 3 now follows canyon/interior/night progression; Operation 4's full
   sunrise belongs to Mission 6.
2. **Bind to verified mission state.** Resolve each map through the actual native
   mission load path. Starting, restarting, loading saves and moving between
   missions must restore the right visual state. Asset discovery or user wall
   time alone must not select a mission. Keep Training and Instant Action separate
   from campaign progression, and retain manual lighting previews.
3. **Preserve original gameplay.** This is a lighting/weather art plan. References
   above to wind buffeting lighter mechs, reliance on night vision/thermal/radar,
   optical obstruction, cold thermal contrast or corrosive weather do not by
   themselves authorize changes to physics, sensors, targeting, AI, damage,
   objectives or mission scripts. Keep the original simulation and save contracts.
   Heat shimmer must not move HUD reticles or change targeting calculations.
4. **Author bounded transitions.** Specify any within-mission start/end states,
   approved event cues or durations before implementing them. Do not run a full
   accelerated day/night cycle through each mission. Keep the presentation clock
   separate from simulation time and respect photo-mode freezing.
5. **Coordinate the whole scene.** Sun and independent moonlight, ambient fill,
   upgraded sky/cloud artwork, haze, terrain/vehicle normals, water and surf,
   wetness, emissive surfaces and shadows must agree. Set map-specific directions
   after checking terrain and skyline visibility. The sealed hangar needs an
   interior lighting treatment; do not apply exterior sunlight indiscriminately.
6. **Place environmental lights from scene evidence.** Check actual wreckage,
   flares, searchlights, industrial fixtures, vents, fires and lava surfaces before
   attaching visual lights. Use original effects/state where available. Do not
   fabricate persistent destruction, move objectives or change the rescue sequence
   to fit an atmospheric description. Any additional decorative effects must be
   identified as remaster-side visual authoring.
7. **Keep darkness and glare playable.** Interpret pitch black, blinding glare,
   localized blindness and maximum contrast as mood targets subject to readability
   review. Keep essential controls/HUD legible. Provide controlled lightning
   intensity and an accessibility option.
8. **Separate existing features from planned effects.** The integrated preview
   supplies manual sun/sky/ambient presets, upgraded material normals, bounded
   water/cloud detail, a moonlit-night treatment and experimental unshadowed
   weapon lights. Automatic campaign selection, independent sun/moon progression,
   weather transitions, rain response, pooling/wet reflections, localized
   volumetric fog, dust/ash/embers, searchlights and heat shimmer require separate
   capability checks and implementation. This document enables none of them.

## Implementation and review order

- Verify each mission's geography, briefing identity, relevant scene emitters and
  original weather/effects against the assigned row.
- Establish static starting states for all 20 missions, beginning with Operation 1.
  Match scene-wide color and night readability before adding weather transitions.
- Connect mission selection and restart/load lifecycle handling in the native host.
- Add supported environmental light sources and weather effects in bounded stages;
  keep existing upgraded artwork and its UV, alpha and animation contracts intact.
- Define and then test within-mission transitions where required. Preserve the
  clear full-sunrise endpoint for the final mission without changing victory timing.
- Capture matching viewpoints and benchmark each environment, including lighting,
  shadows and weather costs. Test photo mode and save/restart transitions.

Saving this revision changes documentation only. Existing launcher presets and
native mission behavior remain unchanged. Formal acceptance stays **131/144**;
fixtures, captures and renderer improvements do not grant native-game credit.
