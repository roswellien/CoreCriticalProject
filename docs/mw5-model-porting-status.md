# MW5 model porting status

## October 15: complete Daishi arms moved up/in

The current host supports torso-frame rigid placement. Daishi R3 restores the
donor shoulder connector shapes and moves the complete arms up/in, retaining
the user-approved legs/waist and the other six model records. This supersedes
the elongated R2 shoulder fit. Training116/116, GPU1150/1150 and IA116/116 match
the retained baseline; the new Daishi2600frame case matches all original draws.
[Current placement and previews](mw5-daishi-arm-placement-2026-10-15.md).

## October 15: Daishi waist and Shadow Cat thigh corrections

Daishi now uses the second connection revision: pelvis-owned hip connectors
and torso-owned clavicles fit to original limb joints. This supersedes the
central-only Daishi correction after the user identified remaining side/shoulder
gaps. Another 2,600-frame native check matches every original draw record.
The Shadow Cat thigh correction is retained. Current paths and R2 previews are
in [the correction record](mw5-fit-corrections-2026-10-15.md).

The optional geometry now fits Daishi's existing waist connector across the
original torso/pelvis interval and keeps Shadow Cat's upper legs vertical in
the front view. Original pivots, knee endpoints, UVs and weapon placements are
retained. Both corrected player models draw natively; all 4,700 original draw
records match the prior cases. Close/distance assets are registered in the living
launcher. See [the fit correction and previews](mw5-fit-corrections-2026-10-15.md).
The r17 executable is unchanged; acceptance stays 131/144, strict lane paused.

## October 15 follow-up: damage recognition and native distance models

Current Remaster r17 fixes the full-model fallback observed when Orion loses
its right arm. Surviving MW5 parts remain, with original stump/debris rendering.
All6500original combat draw records and the standard3regressions matchr15.
All3newLOD1 variants now draw natively. Other live destruction states, converted
debris, both distance transition directions and muzzle correction remain open.
See [the follow-up](mw5-arm-damage-fix-2026-10-15.md). Acceptance131/144strictpaused.

## October 15: three additional native candidates

Orion, Daishi and Shadow Cat now render in the native r15 Remaster build and
were registered with the existing four models in r15. All original regressions match
r14; 41 offline animation clips and the actual-adapter fixture pass. Primary
materials and distance payloads are prepared. Visible muzzle alignment,
controlled damage/debris and live distance switching remain pending.
See [the new batch and validation](mw5-next-mechs-2026-10-15.md). Avatar remains
excluded; 131/144 strict acceptance stays paused. No commit.

## October 14 finishing pass (historical)

The user chose to finish Mad Cat, Vulture and Thor before starting another
chassis. Avatar/STL work remains parked. The normal Remaster launcher still
uses its validated r5 executable and existing registered models; this pass
does not publish the new candidate into that profile. No commit was requested
for this continuation.

## Candidate changes

The private `local/remaster/gpu-native-r6-lod1` host recognizes exact original
LOD1 mesh rosters as well as LOD0. It leaves original distance selection and
hysteresis in control; it does not force high detail or change gameplay.
The source LOD1 controller pivots and ancestry match the surviving LOD0
controllers. Mad Cat and Vulture omit toe controllers at LOD1, so their toe
geometry is folded into the corresponding original foot controller.

| Model | Close triangles | Distance triangles | Reduction |
| --- | ---: | ---: | ---: |
| Mad Cat | 23,084 | 14,000 | 39.4% |
| Vulture | 29,822 | 15,101 | 49.4% |
| Thor | 30,408 | 14,776 | 51.4% |

Only main body geometry is simplified. Weapon assemblies, exterior cockpit,
UVs and normals in unsimplified groups retain their original payload values.
All LOD0 vertex records are byte-identical to the approved previous payloads.
An initial seam-split decimation was rejected after previewing cracks. The
current exporter welds geometric positions while retaining corner UVs/normals,
and refuses incomplete generations before preparing runtime bindings.
These triangle reductions are not measured FPS gains.

The optional BWMESH2 stream adds a checked original visibility-node name to
each batch. Source node active flag `+0x24 & 0x4`, propagated through ancestors,
filters individual components without writing guest memory. The external
cockpit is associated with the original head marker's activity while still
being emitted under the torso controller. This avoids depending on the
transparent head marker's own tiny culling bounds. BWMESH1, including the
existing Bushwacker path, retains its prior behavior.

## Evidence and execution reached

All working assets, original analysis and rendered previews remain ignored
under `local/work-ahead/mw3-cinematic-mechs-r1/weapon-fit-review-r2` and sibling
`damage-lod-review-r2`.

- Forty-four distinct recovered clips were evaluated offline against serialized
  geometry in 49 model/clip evaluations, with
  standing/walking/running/limping/falling/getting-up previews.
  This is clip/coordinate evidence, not proof of live animation-state choices.
  The original Vulture locomotion definition selects `madcat_*` clips; archive
  clips named `vulture_*` alone do not establish its runtime selection. The
  actual five `madcat_*` locomotion bindings were also evaluated on Vulture,
  and its motion preview now uses those bindings.
- A standalone fixture includes the actual candidate adapter and roster
  headers. Its final artifact rerun passes 1,725 checks, including all six
  BWMESH2 payloads, Bushwacker BWMESH1, controller ancestry, inherited activity,
  reactivation, cache reset and fifteen malformed payload cases. It captures
  draw commands without a game or Vulkan device.
- `preserved-geometry-checks.json` verifies unchanged LOD0 vertex records and
  zero numeric differences in all unsimplified distance assemblies.
- Final-payload native Instant Action runs reached 1,900 frames with Mad Cat
  against Mad Cat, and 2,000 frames each with Vulture against Thor and Thor
  against Vulture. Logs validate and queue all three LOD0 identities. Mad Cat's
  same enemy instance additionally validates and queues LOD1, beginning at
  frame 754. Neither Vulture nor Thor selected LOD1 in these bounded runs.
  Exit 1 is the explicit frame-budget stop, not normal mission completion.
- Combat exposed a missing original MSVCRT `memmove` continuation. An original
  model baseline reproduced the same frame-1,301 fault, independently of the
  replacements. Four original short-copy continuations were translated and
  added to the private host. The same frozen input then reaches 1,750 frames;
  all 1,301 original draw records before the previous stop remain identical.
  The subsequent three model runs above use this corrected host. The bounded
  closure scanner fix and four asset-free table tests are authored source;
  generated bodies, DLL evidence and executable remain local.
- The test harness refuses to launch while a normal game is running. It uses
  a copied install/pilot and private registry; actual registry and pilot files
  are only hashed and are never written. Native target dumps and Blender
  renders provide previews; no desktop screenshots are taken.
- Fresh standard regression attempts stayed in the menu with foreground
  acquisition failure; a Windows system dialog held focus. An unchanged r5
  control did the same. Matching menu captures are excluded from gameplay
  validation. Training 116/116, GPU draw 1150/1150 and IA 116/116 remain pending
  on this candidate; the earlier r5 evidence is retained separately.

## Open boundaries

The original weapon-origin producer `0x4b36e0` feeds collision, continuous-beam
damage and random-number decisions. It must not be changed to fix presentation.
Several source firing points differ materially from MW5 barrel openings.
The recovered route for a future correction tracks exact beam/FIRE effect
instances and adjusts only host drawing geometry before projection/clipping,
keeping the original hit endpoint. That route is documented locally in
`weapon-presentation-contract.md`; no completed muzzle fix is claimed.

Actual combat limb loss, debris, head damage, both distance-transition
directions, Vulture/Thor LOD1 selection, clipping and final per-chassis performance remain unobserved for
this revision. Same-name/same-count geometry swaps are not recognized;
subtree removal conservatively restores original rendering. Static base-color
sidecars do not select original damage skins. The semantic cockpit/head-marker
association and same-scene visibility snapshot need live validation. Normal
maps remain available offline but are not consumed by this native base-color
path.

Next: verify the remaining distance paths and actual damage events for every
chassis after normal play has closed, then
implement and validate the scoped visual-effect origin correction. Promote
the candidate into the living launcher only after those checks. Strict
acceptance remains paused at **131/144**; this work adds no accepted credit.
