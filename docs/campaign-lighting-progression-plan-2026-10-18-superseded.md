# Superseded campaign lighting plan — 2026-10-18

Archived on 2026-10-19 when the user supplied the complete 20-mission replacement.
Use [the active plan](campaign-lighting-progression-plan.md) for future implementation.
The original twelve-entry document follows unchanged.

---

# Campaign lighting and mission progression

Recorded 2026-10-18. Status: user-proposed art direction, saved for later in-game
integration. This document does not activate a campaign clock or change missions.

## Intent and working assumptions

Use sun position, sky, ambient fill, weather, haze and artificial light to convey
an urgent campaign progressing from a disastrous storm-bound insertion to a final
sunrise and rescue. Mission-to-mission continuity matters more than showcasing
unrelated attractive lighting presets.

The supplied creative schedule uses four Operations, twelve mission lighting
beats, eight campaign days and a roughly 27-hour planetary day on Tranquil.
These are **working assumptions supplied with the art-direction proposal**, not
verified claims about the retail campaign's mission count, chronology, location
or astronomy. Before integration, reconcile every row with the recovered mission
roster, map identifiers and original briefings. Preserve all original missions;
expand or redistribute these beats if the actual roster differs.

Operation subtitles below are working art-direction labels. Narrative context is
retained from the user's proposal and must be checked against the relevant maps.
Do not silently rewrite briefings, objectives, dialogue or campaign lore to fit
this lighting schedule.

## Operation 1 — The Drop · Days 1–2

Proposed context: a failed crash landing on a tropical peninsula during a severe
storm. The unit is fragmented and must link up with its Mobile Field Bases.

| Supplied mission beat | Campaign time | Lighting and atmosphere | Intended progression |
| --- | --- | --- | --- |
| Mission 1 | Day 1, late afternoon / dusk | Heavy storm clouds; oppressive overcast twilight; restrained, obscured sun; rain and darkening ambient fill. | Transition from the failed drop into a dark, rainy night. |
| Mission 2 | Day 1, night / midnight | Very dark rainy conditions; intense lightning; limited natural illumination. | Night visibility is a central part of the intended tactical atmosphere. |
| Mission 3 | Day 2, dawn / early morning | The storm clears; a crisp sunrise breaks through mist and remaining cloud. | Relief and regrouping as the MFBs are secured. |

Keep night readable enough to navigate and identify essential HUD/objective cues;
"pitch black" describes the intended mood, not a requirement to crush all detail.
Lightning flashes need controlled intensity and an accessibility option.

## Operation 2 — The Push Inland · Days 3–4

Proposed context: push through enemy territory toward a major Clan Smoke Jaguar
base, destroying infrastructure to cover the squad's tracks.

| Supplied mission beat | Campaign time | Lighting and atmosphere | Intended progression |
| --- | --- | --- | --- |
| Mission 1 | Day 3, mid-morning | Clear, bright daylight and high visibility at the train-depot assault. | A decisive, exposed advance after the storm. |
| Mission 2 | Day 3, afternoon | The sun begins to dip; harsh directional shadows across industrial and mining areas. | Increasing contrast and pressure during the inland push. |
| Mission 3 | Day 4, dusk / twilight | Deep orange and purple sunset over the ocean at the naval-port assault. | A strong coastal sunset closing the operation. |

## Operation 3 — The Urban Siege · Days 5–6

Proposed context: enter fortified urban and industrial sectors to destroy a Mech
factory and disrupt communications.

| Supplied mission beat | Campaign time | Lighting and atmosphere | Intended progression |
| --- | --- | --- | --- |
| Mission 1 | Day 5, noon | Harsh, high overhead sunlight over dense concrete structures; short shadows; heat shimmer as a later effect. | An oppressive, exposed urban assault. |
| Mission 2 | Day 5, late evening | Sun descending behind the skyline; long geometric shadows between structures. | Deepening street-level contrast as the day ends. |
| Mission 3 | Day 6, night | Artificial city lights, moonlight and fires from prior battles where supported by the actual mission state. | A night assault with localized pools of illumination. |

Do not invent persistent battle damage or fires by changing original mission
state. Use original scene evidence, or explicitly authored optional visual effects.

## Operation 4 — The Final Stand · Days 7–8

Proposed context: breach a volcanic caldera where Galaxy Commander Brendon
Corbett is preparing the final counterattack.

| Supplied mission beat | Campaign time | Lighting and atmosphere | Intended progression |
| --- | --- | --- | --- |
| Mission 1 | Day 7, midday | Bright, oppressive daylight filtered through volcanic ash and smoke in the upper atmosphere. | Severe visibility and an increasingly hostile environment. |
| Mission 2 | Day 7, sunset / dusk | Fiery crimson sky; setting sunlight visually combines with caldera lava glow. | The most intense red/orange palette of the campaign. |
| Mission 3 | Day 8, sunrise / new day | Sunlight breaks over the caldera rim as Corbett is defeated and the rescue dropship arrives. | A symbolic new dawn and definitive visual closure to the squad's struggle against the Smoke Jaguars. |

The last sunrise should support the original victory/rescue sequence. It must
not change the conditions or timing of victory, enemy behavior or dropship arrival.

## Rules for later integration

1. **Mission anchors first.** Give each verified mission a starting lighting and
   weather state. Preserve the intended gaps between campaign days; loading the
   next mission can advance the visual campaign schedule without simulating the
   intervening hours.
2. **Authored transitions second.** Where a row calls for a change during play,
   define start/end states and approved cues. Prefer bounded visual transitions
   tied to existing mission events; use presentation elapsed time only where an
   authored duration is appropriate. Do not rush a 27-hour cycle through a short
   mission or introduce a universal accelerated clock by accident.
3. **Keep game time intact.** The lighting clock is host presentation state. It
   must not replace guest clocks, simulation ticks, AI timers, weapons, physics,
   weather gameplay rules, mission scripts or save semantics.
4. **Coordinate the whole scene.** Sun direction/color, cloud lighting, ambient
   fill, haze, water response, shadows and emissive materials must follow the same
   state. Avoid abrupt horizon, water/surf or indoor/outdoor color boundaries.
5. **Use upgraded artwork.** Preserve the upgraded texture source and its UV,
   alpha, color-key and animation contracts. Water receives a surface lighting
   model; cloud relief receives a dedicated sky model rather than lighting the
   sky dome as a solid wall.
6. **Define night explicitly.** The current positive-elevation sun presets are
   insufficient for night. Add proper below-horizon solar behavior, night ambient
   and a moon/cloud treatment before exposing these beats as implemented. Point
   lights, rain, lightning, wetness, lava illumination, ash and heat shimmer are
   separate capabilities; a recorded direction is not proof they exist.
7. **Handle mission lifecycle.** Starting, restarting, loading and transitioning
   missions must resolve the correct visual state consistently. Specify any
   remaster-side persistence without altering original save files. Do not infer
   campaign progress from a folder name, menu frame number or user wall clock.
8. **Preserve controls.** Keep original-compatible visuals and manual lighting
   previews available. Campaign lighting, water detail and cloud detail need
   independent controls and clear effective settings. Unknown optional mission
   mappings should retain original visuals with an explicit diagnostic.

## Implementation order and review

- Recover and verify the actual campaign mission/map mapping, then bind these
  twelve proposed beats to that roster.
- Finish upgraded-texture water normals and cloud-specific sky lighting in an
  isolated preview before creating mission-dependent transitions.
- Author static day, dusk, dawn and night anchors, including consistent water,
  surf, ambient and fog response.
- Add bounded transitions and lifecycle handling without changing original
  gameplay. Connect weather and local-light capabilities as each is implemented.
- Review matching viewpoints at mission start/end and transition boundaries;
  check night readability, water seams, sky seams, temporal stability and frame
  cost. Compare original native behavior where the change crosses a game-facing
  boundary. Do not grant acceptance credit for fixture or screenshot evidence.

The current shared Big Lake sunrise/sunset/midday presets remain the preview
baseline. Saving this plan does not replace them or promote the lighting preview
to the regular main-game launcher. Formal acceptance remains **131/144**.
