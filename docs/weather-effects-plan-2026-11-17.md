# Weather effects and view-distance fog plan

## Status

This is a planning document only. Weather work starts after the playtest, and
only when the owner says to start it. The view-distance fog table below is
being implemented separately in its own pull request; this document records
the decisions so both efforts stay consistent.

## Owner decisions

Recorded on 2026-11-17:

- View-distance fog is not weather. It starts before the view distance so that
  geometry popping in at the edge of the draw range is hidden. It follows the
  view-distance setting. There is no separate Fog Distance slider.
- A new 2400 m view-distance option is added wherever 3200 m is supported.
- The default headlight toggle key is `L`.
- Future weather effects are weather fog, sandstorms and better rain (streaks,
  splashes and wet surfaces).
- A user toggle decides whether weather affects gameplay (for example sensors
  or heat) or is visual only. The recommended default is visual only, to
  preserve original MW3 gameplay. The project direction is faithful
  recompilation, not a remake.
- In the campaign, weather is set per map or mission. Eventually Instant
  Action lets players choose both the weather conditions and the time of day.
- Sandstorms and the performance budget are later work.

## View-distance fog table

This is the clear-weather baseline. Fog start is always inside the view
distance, so the far edge of the world is already fogged when geometry appears.

| View distance (m) | Fog starts at (m) |
| --- | --- |
| 800 | 700 |
| 1200 | 1050 |
| 1600 | 1450 |
| 2400 (new option) | 2250 |
| 3200 | 3050 |

## Weather feature plan

This is a proposal and has not been approved.

- Build one shared weather-state system holding the current weather,
  transitions between weathers and the user settings. Weather fog, sandstorm
  and rain all read from it.
- Time of day uses the same system, because it also drives sun direction,
  shadows and light colour.
- Weather fog pulls the fog start and end distances inward from the
  clear-weather baseline in the table above. Clear weather always returns to
  the table values.
- The gameplay-affecting mode touches recompiled game logic. Before promising
  any effect, inventory what the original code exposes (for example whether
  sensor range or heat are reachable values) and record the findings with
  evidence. The visual-only mode must not change recompiled game state.
- Measure frame time on the Vulkan renderer (particles and fog) before fixing
  a design, so the performance budget comes from numbers rather than guesses.

## Open questions

- Which gameplay effects are feasible with what the original code exposes.
- Where the weather settings go in the settings UI.
- The data format for per-mission weather.
- The Instant Action picker UI for weather and time of day.

## Out of scope for the playtest

- All weather effects: weather fog, sandstorms and rain improvements.
- The weather-affects-gameplay toggle.
- Time-of-day selection and the Instant Action weather picker.
- Performance budgeting for weather.

Only the view-distance fog table (separate PR), the 2400 m option and the `L`
headlight key are in the playtest scope.
