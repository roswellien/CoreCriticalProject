# Mech Lab canvas repair — 2026-10-15

The native Remaster host now composes the original Mech Lab on one centered,
aspect-preserving canvas. The previous host combined wide-world presentation,
independently narrowed preview geometry and original raster coordinates, causing
overlapping panels and displaced content. This repair advances the live menu
boundary: an original editable Lab can render, accept a loadout change, close,
and carry that loadout into a native mission.

## Implementation

`tools/remaster-launcher/apply_frontend_canvas.py` applies checked substitutions
to a fresh host snapshot. The authored `frontend_stage.inc` follows original Lab
initialization/teardown, flushes and synchronizes the previous composition before
changing render domains, and restores world presentation on exit. Renderer target
ownership, GPU HUD, CPU presentation and readback share the Lab domain. Original
Lab geometry and raster coordinates remain together, without double fitting.

`frontend_canvas.hpp` provides the fit and inverse absolute pointer mapping.
Relative DirectInput and original equipment rules remain unchanged. The fixture
checks 1080p, 1440p, odd dimensions, portrait fit, margins and pointer round trips.
Host floating-point calculations are scoped outside original execution.

At 3440×1440 the Lab occupies a centered 1920×1440 canvas. This is an interim
layout repair. Fully resolution-adaptive menu reflow remains a future goal, as
does an in-game settings menu exposing implemented graphics options. Dynamic
lighting and normal mapping remain planned features; this change adds neither.

## Bounded validation

Final local executable SHA256:
`ed568b419c2ac0b465950016bf9be3cb0e2f988d73bae01c76e183ee12ec41df`.
The source base includes the latest Daishi arm repair and retains the same
37,201 translated object entries. Source pins and private results are in
`local/remaster/gpu-native-mechlab-canvas-r1/source-snapshot.json` and
`local/mechlab-canvas-r1/verification.json`.

- Genuine Instant Action briefing → editable Lab entry, with no seeded flags or
  direct entry call. Chassis, loadout and weapon-grouping panels were exercised.
- In the final 1,050-frame full-profile run, clicking the assigned machine gun
  removed it from the Madcat: 75.0 → 74.8 tons, one free critical slot and a
  “modified” configuration. Closing the Lab and launching the mission retained
  the edited weapon list and restored widescreen world rendering.
- Final ultrawide Lab render targets at frames 300/450 and logical CPU readback
  at frame 350 are byte-identical to the retained 4:3 control. The frame after
  readback resumes the same composition.
- Final original-compatible Training CPU: 116/116 PPM captures identical to r17.
  Training GPU: all 1,150 original draw records identical to r17.
- The full-profile edit run uses 3440×1440, FXAA, 16× AF, current texture banks
  and seven replacement model bindings. Protected original pilot/registry hashes
  are checked by the private harness. Test termination is the intentional frame
  budget exception, not a normal quit or whole-mission completion.

Panel navigation was checked before the final Daishi-only source rebase; the
final binary separately covers actual editing, readback and mission transition.
These are bounded tests, not exhaustive armor/ammo/chassis or campaign coverage.
The exact campaign Win → Continue → Lab sequence remains unobserved here; the
shared authentic Instant Action route provides editable live Lab coverage.

The 30/60/120 FPS and uncapped real-time interaction matrix remains open. Fixed
virtual-clock runs do not establish frame-rate independence. No global FPS cap
or engine timing rewrite was introduced. Strict acceptance remains 131/144.

See [the earlier investigation](mechlab-layout-timing-investigation-2026-10-15.md)
for original function contracts and the outstanding timing investigation.
