# Weapon and night lighting preview — 2026-10-19

An experimental native preview connects original weapon-effect draws to local
Vulkan lights. Original weapon firing, hits, damage, AI and animation remain
read-only. Whole-game acceptance remains **131/144**. The user subsequently released the Mad Cat and Vulture holds; fresh corrected-model footage is documented in the announcement revision 3 summary.

## Testing the preview

- `Play MW3 - Dynamic Night Lighting Preview.cmd` selects the revised night preset.
- `Play MW3 - Weapon Lighting Preview.cmd` selects sunset with the same weapon lights.
- Both use `local/effect-lighting-r1/launcher.json` and the material-normal registry.
- The existing main playable profile is preserved while model repairs continue.
- Replay video remains off by default. Lighting traces and texture diagnostics
  are off in the playable preview.

The preview executable is a private derivative of the existing Big Lake/main
normal-map and photo renderer, with BWMESH6 support. Its pinned local executable
is `C:/Users/jcbla/MW34SunTests/effect-lighting-20261019/validated-r3/entry_commandline.exe`
(SHA-256 `8002410fbdbb05d75021070d052201a44a21e9e2e84bc70d70ee948451369c53`).
This is a separate lighting build, not publication of the ongoing model repairs.

## Rendering changes

The execution boundary advanced is **original live effect draws → authenticated
world positions → bounded light uniform → normal-mapped world/model receivers**.

`runtime/graphics/effect_lighting.hpp` owns the strict material-catalog reader,
reciprocal-depth reconstruction, observation cache, fading and light selection.
`effect_lighting_stage.inc` observes original textured draws before widescreen
adaptation. It reuses validated sun-view captures and never advances the guest
clock or writes weapon state. A maximum of 16 influential lights is selected
from a bounded cache; the renderer supports an upper limit of 32.

Laser beams use capsule lights along their observed endpoints. Muzzle flashes,
energy-trail draws, impacts and fire use local lights at their observed world
positions. These lights use the same perturbed normals as existing terrain,
building and mech normal mapping. True position transforms, rather than
inverse-transpose normal transforms, determine light distance.

The local lights are unshadowed. Original luminous sprites retain their own
emission; HUD/menu passes receive no local illumination and do not clear the
world's fading-light cache. Fades use a monotonic presentation clock with an
explicit photo-mode pause, so pausing preserves the captured lighting. The
adapter reads the host clock without advancing the guest clock. The per-scene light uniform
is separate from the existing sun uniform and its ABI.

`prepare_effect_lights.py` reads the active upgraded bank map without editing
artwork. Its catalog uses complete pixel hashes, dimensions and native format,
including the game's alpha-upload conversion. In particular, original 8-bit
alpha zero clears unused RGB before packing, while alpha values 1–15 retain RGB
even when their final 4-bit alpha rounds down to zero. Names alone never admit
a live surface. The final catalog has 598 keys from 1,800 bank entries; the
large entry count reflects repeated effects across map banks.

## Night visibility

The initial night test was too dark. After user review, ambient fill increased
from 0.09 to **0.18**, and cool directional moonlight increased from 0.18 to
**0.32**, at 35° elevation. Sky brightness is 0.28, with dark blue haze and a
0.24 gain for otherwise unlit opaque world draws. HUD and effect sprites retain
their brightness. The directional light supplies moonlight; no new moon disk,
stars or automatic campaign time progression is claimed.

Night is selectable through the shared preset resolver. The campaign's planned
mission-to-mission progression remains separate work.

## Verification

- Clang-CL/Ninja host build and both fragment variants compile successfully.
- Three launcher-preset tests pass, covering daylight preservation, night
  selection and rejection of invalid night values.
- The authored Vulkan fixture passes on AMD Radeon RX 9070: point/capsule
  illumination, finite radius, surface direction, normal-map response, HUD
  exclusion, stale-list replacement and bounded/fading cache contracts.
- A native Campaign 1 laser control is pixel-identical before firing. At the
  same firing frame, enabling local lights changes 488,624 of 4,953,600 pixels,
  visibly illuminating nearby terrain and cockpit geometry.
- A native Puma test independently matches complete PPC muzzle, PPC trail and
  blue-impact textures. All three produce local illumination.
- Photo-mode captures 50 frames apart have identical world pixels while the
  source is paused; the test returns to gameplay and reaches its intentional
  presentation budget. A bounded 16-light list remains present during the pause.
- Native runs end at their explicit presentation budgets. This diagnostic
  budget stop is not an unhandled gameplay crash.

Raw private runs live under
`C:/Users/jcbla/MW34SunTests/effect-lighting-20261019/`. Selected review evidence
is stored in `reports/weapon-night-lighting-20261019-r1`, through the repository's
existing reports junction on the Games drive. The original native screenshots
are ungraded full-resolution PNGs.

## Earlier prototype performance control

One matched 1,500-frame sample per setting used repeated ordinary PPC input at
3440×1440, FXAA, AF16 and 4096-pixel moon shadows on AMD Radeon RX 9070.
Replay video, screenshots and diagnostics were disabled during timing. Menu
time and the initial world warm-up were excluded.

| Local weapon lights | Average FPS | Mean frame time | 95th percentile |
|---|---:|---:|---:|
| Off | 78.43 | 12.75 ms | 16.11 ms |
| On, capped at 16 | 75.63 | 13.22 ms | 16.91 ms |

This R2 prototype control measured approximately **3.6% lower FPS / 0.47 ms
additional mean frame time**. It predates the fade-clock correction below and
is retained as evidence for that exact binary, rather than relabeled as an R3
measurement. It is not a general overhead promise or a replacement for broader
environment/combat baselines.

## Live-capture clock correction

Moving announcement takes exposed a missed criterion: the initial pause test
did not verify expiry after live firing stopped. The field read as a mission
clock was not supplying advancing elapsed time, leaving stale flashes lit.
R3 replaces it with the explicit presentation clock described above.

The authored clock fixture checks live advancement, paused holds, resume
without accumulating paused time and backward-clock reset. A native check
preserves identical paused world pixels at frames 1050/1100, resumes play, and
independently records an empty light list at frame 1440 after firing stops.
Fresh night captures use the corrected binary. The earlier source and evidence
remain preserved; this correction changes no gameplay or acceptance criteria.

## Limits and next integration work

The first pass observes effects submitted by the original renderer. Fully
offscreen emitters are not recovered from simulation objects. Unshadowed local
lights can bleed through nearby occluders. Whole-campaign, all-weapon-family,
water and longer-session checks remain necessary before promoting this into
the main playable profile. Environment fixtures do not establish full-game
performance or grant additional native acceptance credit.

The installer `apply_effect_lighting.py` verifies all current-host anchors
before writing and keeps the effect fragment variant separate from the existing
sun-only variant. Reapply it to the final model-repair host, preserving that
host's current source, rather than replacing the model host with this preview.
