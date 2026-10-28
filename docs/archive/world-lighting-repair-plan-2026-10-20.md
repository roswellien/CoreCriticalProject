# World lighting repair plan — 2026-10-20

Authorized scope: repair the concrete defects in the Gemini R6 review and publish
a workable native lighting build through the existing launchers. Retain the active
20-mission art plan, upgraded assets, original simulation and acceptance 131/144.

| Step | Change | Completion check |
| --- | --- | --- |
| 1 | Separate point, laser capsule and spotlight types | Actual Vulkan point/capsule/spot receivers, cone rejection, normals and HUD tests pass |
| 2 | Use one effective campaign environment throughout each scene | All 20 mission settings resolve; receiver, sky, fog and shadows share the selected settings; manual overrides remain available |
| 3 | Give supported weather effects dedicated uniform fields | Neutral weather adds nothing; wetness, fog and dust vary independently of water/cloud controls |
| 4 | Track fixture source identity and lifetime | Movement/material replacement/destruction and map changes cannot leave stale emitters; verified static sources can illuminate off camera |
| 5 | Enforce one combined light budget | Total never exceeds configured limit; weapon lights have reserved capacity; fixture toggle supports matched cost measurements |
| 6 | Correct mission load observation | Failed opens and save writes do not change missions; successful exact reader loads and non-campaign transitions reset state correctly |
| 7 | Validate, benchmark and publish | Fixtures plus bounded native campaign/Training/IA checks, matched fixture off/on samples, screenshots, source/executable pins, launcher checks and rollback profiles |

Implementation uses a separate R7 host copied from current R6 source, preserving
concurrent model changes and recording the copied source identity. No production
interpreter or original-code fallback is introduced. Existing reports and failures
remain intact; generated source/assets stay local.

Weather scope is the renderer capabilities actually implemented: wet surface
response, height fog, atmospheric dust/smog and lightning illumination. Rain
particles, pooled reflections, volumetric beams, falling ash and genuine heat
distortion must not be reported as finished merely because parameters exist.
Source placements without verified scene identity are excluded from the repaired
default. No changes to movement, AI, sensors, targeting, damage, missions or saves.

Status: **core repair implemented and published as R7**. All seven steps have
bounded completion evidence in the [implementation record](world-lighting-repair-2026-10-20.md).
Vulkan/CPU checks pass; native Campaign 1 Missions 1 and 3, Training, Instant
Action and normal launcher shutdown were checked. Eight matched fixture trials
average +0.571 ms / −5.67% FPS in the measured Training scene. Moving paired
captures demonstrate fixture illumination; static benchmark images remain
identical and are not presented as appearance evidence.

Material Normal Preview passes profile validation and asset preparation. All
three profiles select R7 with their prior graphics preferences retained. The
main GUI's concurrently developed display settings need their own compatible
display host; R7 does not claim support for arbitrary new resolution/AA/window
choices. Use the verified Material Normal Preview shortcut for this lighting
repair. Remaining weather artwork and per-map fixture placement are explicitly
listed in the implementation record; all-20 native playthroughs are not claimed.
