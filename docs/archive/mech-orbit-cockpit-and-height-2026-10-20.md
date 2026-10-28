# Replacement orbit cockpit visibility and Annihilator height

The user identified a broken Annihilator cockpit and insufficient height in the
second five-mech evolution batch. The previous visual review missed these
defects. Earlier media and captures remain local as superseded evidence.

This advances the optional native visual adapter and visual asset fit only.
Original gameplay transforms, simulation, weapon origins and damage rules are
unchanged. Strict acceptance remains **131/144**; no additional credit is claimed.

## Confirmed causes and corrections

The separate object above the Annihilator's modern head was the **original
attached cockpit**, still being drawn when the photo camera detached. The
replacement's serialized exterior cockpit matches its Blender source bounds.
Disabling normal mapping reproduced the defect, excluding normal shading as its
cause. A detached-camera-only suppression removes the original attachment in
front and side native captures while retaining the donor's actual head.

The adapter recognizes only the existing complete cockpit mesh signatures on a
validated replacement chassis. It omits those draw commands only when the photo
camera is detached. Original rendering producers continue; no guest scene or
visibility flags are rewritten. The per-scene attachment cache is cleared with
the existing identity cache. First-person and original-model paths retain their
previous behavior.

The Annihilator's earlier uniform fit used its highest donor point, including
the tall thin antennae. The actual cockpit roof was approximately 11.0392 scene
units above the donor foot baseline, versus the original standing armor height
of approximately 12.3131. The candidate enlarges the complete donor uniformly by
**1.11539146665** at both distances, keeping the donor's proportions and grounding
baseline. The original reference transforms and all vertex/UV payload bytes are
unchanged; donor rest matrices and the donor walking pelvis-drop length scale
together. The previous forearm-axis correction is retained. This is an authored
visual fit; exact muzzle-to-gameplay-origin fitting and broad combat/damage
validation remain open.

The main launcher and material-preview profile select the corrected current
host. Both model registries select the new Annihilator close/distance assets.
Unrelated models, colors and normal-map registrations were preserved.

## Implementation and evidence

- Authored patch: `tools/remaster-launcher/apply_detached_cockpit_visibility.py`.
  The normal-mapping composition and world-light repair paths reapply it so
  subsequent authoring retains the correction.
- Current native host:
  `local/remaster/gpu-native-detached-cockpit-r1/build/entry_commandline.exe`,
  SHA-256 `e0d723602d4381f1b7c062fe1c701f9a9781ef921ed18668968b1c764781f330`.
  Its source snapshot retains the current D32 host and changes only
  `mesh_override_stage.inc`. The actual adapter is byte-identical to the tested
  private capture adapter; capture automation remains outside the normal host.
- Height assets: `local/work-ahead/annihilator-roof-fit-20261020-r1/`.
- Investigation, source/serialized bounds, no-normal control, native checks,
  installation preimages and receipt:
  `C:/Users/jcbla/MW34SunTests/annihilator-review-20261020/`.
- Paired production-host first-person frame 1246 is byte-identical before/after,
  SHA-256 `7d073e61ebb4acf706f4025609b4985e21d154a7a15efb815749f33166b87a23`.
  Both runs reach their explicit budgets, with no detached suppression event.
- Main, original-model and material-preview launcher checks pass with the new
  executable. Preparing all registered assets into a separate validation
  directory succeeds with 18 models and 39 texture banks; current graphics and
  lighting selections are retained.
- All five revised four-angle framing checks complete. New replacement passes
  contain 3120 source frames each and confirm normal-map loading. The earlier
  original/model-texture passes are retained. Source pins match at closure.
- All ten revised final encodes decode fully: 6361 frames, 60fps,
  106.016667 seconds. Each contact sheet was visually reviewed for stage order,
  transitions, complete silhouettes and final head-on view. These are controlled
  visual captures, not gameplay performance measurements or exhaustive model QA.

## Media revision

The five existing Drive video IDs were updated in place. The Annihilator's JPEG
and PNG thumbnails now show the actual corrected head without the floating
original cockpit; the other thumbnail models are retained. Titles, descriptions,
tags, maps, approved opening and MW3 audio retain the established formula. No
YouTube publication was performed.

Revised 1440p60 masters and 1080p60 Drive copies are under
`reports/mech-evolution-series-2-20261020-r2/`. `Drive-delivery.json` records the
readback of all 30 individual files; names, uniqueness and remote/local sizes
match. The earlier `-r1` package remains local. No ZIPs or game assets were
uploaded. No commit was made.
