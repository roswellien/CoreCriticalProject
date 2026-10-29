# C3M1 clear noon sky — 2026-10-24

The agreed Operation 3 Mission 1 direction in
`campaign-lighting-progression-plan.md` is high noon, dry canyonlands and
washed-out sunlight. The selected mission was correct, but sky grading still
multiplied the original dark cloud artwork. Tinting could not remove its storm
cloud coverage.

## Change and execution boundary

`tools/remaster-launcher/apply_c3m1_day_sky.py` adds an automatic C3M1-only
direction-space daylight gradient to the existing sky dome shader. It retains
the original directional sun glow, horizon haze, dithering and alpha. Other
missions and manual lighting keep the preceding texture-based path. No new
texture, draw, descriptor or uniform allocation is introduced. No heat
distortion is implemented by this repair.

The sky mode occupies the previously constant/unused `sky_tint.w` value.
The **selected composed host's uniform remains 912 bytes**, including its
existing emission-region data. The private host is composed from the selected
heap-collision repair rather than replacing it with an older common shader.
Only `sun_lighting.hpp`, `sun_scene.frag`, `sun_scene_frag.h` and
`effect_scene_frag.h` differ from that parent. Both shader variants are compiled
from the exact composed source. Terrain/sky classification is unchanged.

This advances the native Vulkan presentation boundary for automatic C3M1 sky
colour. It changes no simulation or original guest resources. Acceptance stays
**131/144**.

## Evidence

Private evidence/build directory: `D:/MW3C3Sky-20261024-r1`.

- CPU checks exercise 20 missions, frontend/Training transitions, automatic,
  manual, disabled campaign lighting and disabled weather. All 928 checks
  across the predecessor/candidate pass. The older combined campaign/fixture
  test fails at its fixture-location assertion on the predecessor as well;
  it is not counted as a passing regression check. The October 24 full-campaign
  audit records that distinction explicitly.
- Full uniform-byte comparisons change only C3M1's sky selector in automatic
  and weather-disabled modes. All other mission records and complete manual/
  disabled-mode outputs are byte-identical to the parent.
- The authored Vulkan fixture renders 12 scenes per build. Candidate C3M1 sky
  output is identical for a dark patterned texture and a bright alternative.
  C3M2, textured distant terrain and HUD controls remain byte-identical to the
  parent and continue to distinguish the two source textures. These are GPU
  regression fixtures, not original-game screenshots.
- An isolated copied-save native Training run reaches 500 presentations through
  the real Vulkan swapchain with the current prepared asset packs and controller
  adapter. It ends at the intentional checked frame-budget marker.
- An isolated copied-save C3M1 frontend run reaches its 2,500-presentation budget
  without the heap mapping fault. Scripted deployment remains at the unallocated
  salvage warning. **Full C3M1 gameplay visual validation remains pending.**
- The signed cumulative `.mw3update` is verified, installed, activated, validated
  and rolled back by LauncherChecks against the controller-query runtime in an
  isolated install. The initial attempt correctly refused while our test game
  was still running; the stopped-game retry passed.

## Delivery

The timestamped Windows signature is valid. The signed host SHA-256 is
`bf90863c49f324e3a7e817abd1ccb9aecf02910bfdafa6b50d295289a023c6f9`.
See `delivery.json` in the private evidence directory for authoritative pins.
DEV selects the new signed runtime with full source-snapshot verification,
retaining the current heap, controller, R7 performance, weapon and status-preview
repairs. All other launcher settings and asset bindings are preserved.

`CoreCriticalGameUpdate.zip` in that directory contains the signed
`mw3-c3m1-sky-20261024-r1.mw3update`, its matching payload ZIP and import
instructions (sequence 2026102402, minimum launcher 1.0.27). It is cumulative
precompiled code; no native regeneration is required. It contains no original
media, generated source or signing private key. This repair has not been
published to the playtest site or incorporated into its full installer. No
commit was made.
