# Marauder: first additional chassis investigation

The owner selected the MW5 Marauder MAD-3R as the first genuinely additional
MW3 chassis, using the existing Mad Cat integration as a reference. This stage
extracts and compares the visual donor. No native game execution boundary is
advanced, no content is installed, and strict acceptance remains **131/144**.

## Verified donor and comparison

Local evidence: `local/work-ahead/marauder-addition-20261024-r1/`.
The existing repak 0.2.3 and CUE4Parse exporter read the owner's installed
`G:/Games/MW5Mercs/MW5Mercs/Content/Paks/MW5Mercs-WindowsNoEditor.pak`.
Its footer and main-index identities match the earlier extraction. The bounded
visual dependency scan records 1,232 extracted files with hashes; it is not a
complete Unreal import-graph closure. No game was run or installation modified.

`Marauder_MDL`, `Marauder_HPS` and `Marauder_SKM` decode successfully. The main
skeletal body exports to glTF; the source metadata declares four LOD entries,
but this first exported comparison includes LOD0 only. Cockpit and weapon
modules are separate assets, not part of the body-only comparison.

| Raw MW5 body LOD0 reference geometry | Mad Cat / Timber Wolf | Marauder |
| --- | ---: | ---: |
| Height, exported units | 15.676 | 16.262 |
| Lateral extent | 11.846 | 9.089 |
| Front-to-back extent | 7.671 | 12.519 |
| Body triangles, excluding attached weapons/cockpit | 15,222 | 36,904 |
| Exported skeleton joints | 121 | 133 |
| Bones used by nonzero vertex weights | 33 | 34 |

These are donor reference-pose bounds, not final MW3 collision dimensions or
measurements of fully assembled combat poses. The relative height is close
(+3.7%), but the Marauder is narrower (-23.3%) and longer (+63.2%). Simply
copying Mad Cat bounds, sockets or all limb offsets would be incorrect.

112 bone names are shared. All 111 shared internal parent links match; the
root's different parent name is only the differently named exported model
container. The Marauder uses the shared MW5 `Mech_SKL` skeleton. Its weighted
bone set also includes hip/talon/twist bindings absent from the Mad Cat's
weighted set; inspect these rather than assuming identical skin partitions.

`comparison.json` retains all bone positions, hierarchy, weighted sets, input
hashes and exact bounds. The neutral-material comparison scene/PNG preserves
the original relative model scale. It is a geometry review, not an in-game
render or a completed textured/weapon-assembled Marauder.

## What transfers from Mad Cat

Use the existing MW3 Mad Cat controller structure and retargeting procedure as
the starting template: pelvis, independent torso twist/pitch, left/right arm
aiming and articulated reverse-jointed legs. Preserve Marauder mesh proportions
and calculate its own shoulder/arm/foot offsets, ground contact and cockpit.
Check standing, walking, turning and aiming before selecting final bounds.

The decoded hardpoint definitions explicitly include a torso AC/5 slot and
left/right forearm PPC and medium-laser slots suitable for the intended 3R
configuration. Slot identifiers are present, but their blueprint/socket
transforms, muzzle locations and assembled geometry still need validation.
Separate intact/damaged exterior cockpit meshes are declared. Damage-section
bindings and wreck appearance must be tested explicitly rather than inheriting
the existing unresolved replacement-wreck behavior.

## Required integration boundary

The current prepared model reader accepts 18 fixed replacement chassis IDs;
the retail Mech Lab name lookup uses a 19-entry original catalogue including
non-player content. Skin-pack discovery does not extend either chassis list.

The next implementation must add a generic chassis registry, with the Marauder
as its first data-defined record. Keep stable pack/chassis identity separate
from process-local original catalogue indices. Audit stat/loadout lookups,
Mech Lab/Instant Action enumeration, instance construction, weapon locations,
damage, AI and save/load references before extending those indices. Do not
overwrite the Mad Cat slot or silently reinterpret a saved Mad Cat as Marauder.

First playable target: enable a chassis pack → select Marauder independently in
Instant Action/Mech Lab → edit a valid loadout → launch and exercise MW3 movement,
weapons and damage → save/reload without changing original chassis identities.
Missing/disabled content must produce an actionable saved-content error. The
template/controller/visual bindings belong in pack data so subsequent compatible
chassis do not require per-mech engine branches or native recompilation.

The donor comparison is complete. DEV, published packs, installer and runtime
remain unchanged. The prototype below advances offline assembly and motion;
generic chassis registration, LODs, gameplay, damage and save/load remain open.

## Assembled moving prototype

`local/work-ahead/marauder-prototype-20261024-r1/` contains the next stage:

- Decoded the actual MAD-3R loadout and shared skeleton sockets. Attached its
  AC/5, two PPCs, two medium lasers and exterior cockpit from source-declared
  weapon components/bones. Five muzzle bones are retained for later firing
  origin work. No guessed weapon translation was applied.
- Scaled the donor uniformly using the current fitted Mad Cat geometry's
  standing height as the size reference; preserved Marauder proportions.
- Drove a standing pose and all 57 original Mad Cat walk samples through the
  existing `donor_retarget.hpp` solver. All 58 poses solve without reach clamps;
  the maximum checked bone-pivot error before the contact bake is about 1e-5
  exported units. The solver itself was not changed.
- Added a **baked planar sole-contact height curve** for this offline animation.
  This preserves relative solved bone transforms and keeps the lowest skinned
  sole on the review plane. It is separate from native retargeting and does not
  establish a live terrain/contact solution. Do not silently claim equivalence
  between this authoring preview and the current runtime solver alone.
- Rechecked all six attachments through all sampled poses: maximum matrix drift
  about 2.2e-6, minimum sole height about -1.8e-7 (floating-point error). The
  rendered model uses simple review materials, not a completed texture set.

Review artifacts include `marauder-stand.png`, `marauder-walk.png`,
`marauder-walk-preview.gif` and editable `marauder-assembled-walk-review.blend`.
Input/output pins and checks are retained locally. No live gameplay, collision,
firing, damage, LOD or save/load result is implied.

## Original engine boundary trace

The existing Ghidra project was opened read-only against the pinned original
image. The retained local exports identify these required extension points:

- `0x4845f0`: resolves a name through a fixed, 60-byte-stride original table.
- `0x484650`: returns a name only for indices below 19; otherwise `notmech`.
- `0x4846a0`: loads/caches a definition only for indices below 19.
- `0x46b7a0`: loads the named definition resource, calls the original definition
  constructor and validator; allocates a 0x1a8-byte definition object.
- `0x4844b0`: destroys the original cached definitions through a bounded table
  walk. Added definitions require their own corresponding ownership/cleanup.

59 references from 43 containing functions were found for the three queried
catalogue/getter addresses. This is a scoped reference inventory, not proof of
all enum-indexed consumers or save paths. Extending only the visible menu would
leave definition lookup and ownership incomplete.

`tools/remaster-launcher/zrd_document.py` adds the bounded typed reader-document
codec needed to author input for the original definition loader. It preserves
integer/float distinctions, single-byte text and empty-list semantics; unknown,
truncated, excessive or nonfinite data is rejected. Six asset-free checks cover
an independent binary fixture and malformed boundaries. Private original
definition roundtrips are recorded in `definition-roundtrip.json`. The codec
does not create guest objects, replace original parsing with seeded state,
advertise a chassis capability or make the Marauder selectable by itself.

## Generic additional-definition loader

The shared modder workflow and remaining integration are tracked in
[additional mech packs](additional-mech-packs.md). The first native loader
implementation adds independent catalogue records, name/display lookup,
definition caching and matching destruction. It preserves original indices
0–18 and reserves 19, which is also the Mech Lab's unselected marker; added
runtime indices begin at 32. Durable saved identity must use a namespaced pack
ID rather than that session-local number.

`chassis_catalog.py` compiles validated data to the bounded native catalogue.
`reader_archive.py` appends authored definition members without replacing any
original payload or directory record. `apply_additional_chassis.py` narrowly
extends a copy of the completed current host source, preserving the existing
model, skin and graphics implementations. Additional definitions still run
through original factory `0x46b7a0`, constructor `0x46b890` and parser
`0x46ba40`. Cleanup uses original destructor `0x46b9b0` and cdecl operator delete
`0x5abd1a`; catalogue-owned text uses the host's checked guest heap.

The private check in `D:/MW3AdditionalChassis-20261024-r1/` adds two independently
named diagnostic definitions to a local reader archive copy, retaining all 178
original members unchanged. Both use the original Mad Cat definition as parser
input; this does not establish Marauder gameplay stats. Native execution
constructed indices 32 and 33 as separate objects, returned the same object on
repeated lookup, retained stock Mad Cat index 9 and completed additional-object
cleanup. The subsequent original Mech Lab route still selected Bushwacker and
its additional Sommerset skin through the normal UI and reached its bounded
700-frame Vulkan stop.

All three captured Mech Lab frames (400, 650 and 699) are byte-identical to the
existing no-additional-chassis baseline; the frame/count/hash columns match for
all 700 draw-log rows. Six catalogue/archive checks and six reader-document
checks pass. The asset-free C++ catalogue check additionally rejects every
truncated prefix, collisions, bad identities, unsorted entries and trailing
bytes, and reads the Python-produced two-entry catalogue.

The final private host was rebuilt after making the cdecl cleanup argument
explicit and reserving `notmech`, the original invalid-name fallback. Its
compilation and catalogue checks pass; another independent capture session
became active, so that final binary's native rerun was deferred. The successful
native run and final build have separate pinned identities in
`implementation-checks.json`; neither was activated in DEV.

The first diagnostic attempt is retained: host-initiated `call_guest` invoked
its top-level body directly, bypassing the catalogue adapters. The correction
adds an explicit opt-in to apply existing body adapters to nested calls; default
behavior for all existing callers is preserved. Original returns, stack cleanup
and callee-saved registers still pass the same nested-call contract checks.

This advances native **additional definition construction and ownership**, not
selection, additional model rendering, AI, damage or saved-content support.
Metadata currently inherits stock mass/class/technology through the original
getters. No chassis capability is advertised, no installable Marauder pack is
claimed, DEV is unchanged and strict acceptance remains 131/144.

## Native selectable Marauder: October 25

The next private host is `D:/MW3MarauderNative-20261025-r1/`. It extends the
completed selected parent snapshot through narrow authored applicators; the
translated DLL remains unchanged. The maintained source is in
`apply_additional_chassis.py`, `apply_chassis_visuals.py` and the associated
`native-overrides/*chassis*` includes.

### Selection and construction

The original Instant Action primary list at `0x48aac0` now appends catalogue
entries using `0x48bac0`, including the original localized Commander label.
The original 18 rows remain. The Mech Lab initializer `0x44ffc0` receives
additional preview objects through original allocator `0x5abd26` and constructor
`0x44fcc0`; its existing owning-vector teardown destroys them normally.

The actual stockpile source is supplied to `0x449220`; it is not necessarily
the initially observed global inventory pointer. Additional chassis enter an
unlimited Instant Action inventory through original insertion `0x471c10` before
the original widget populates. Finite campaign salvage is not augmented.
The stockpile sorts by original chassis identity, so new IDs follow the stock
entries rather than automatically sorting between alphabetic display names.

Native input selected the appended Marauder row, loaded its own definition,
displayed its original Mech Lab statistics, and exited with the normal Done
control. The authored MW3-compatible refit is 75 tons: standard 300 engine,
standard internal structure, 11.5 tons of armour, two ER PPCs, two medium lasers,
an Ultra AC/5 with ammunition and 15 total single heat sinks. This deliberately
uses existing MW3 weapon types; it is not a completed classic MAD-3R weapon fit.

### Independent visuals and first mission

Catalogue v2 separates the metadata template from the visual controller and
contains two coordinator-resolved geometry/texture pairs. The existing 36
stock visual records are retained; generic records append from catalogue data.
Resource-root identity distinguishes a new Mech Lab model before mesh-roster
matching. Live actors may rename their roots, so their recovered
actor → MechData → chassis identity also binds the live root independently of
that name. Root retirement clears the host-owned binding; stock actor lookups
erase an obsolete binding if an address is reused.

This live binding was necessary: a successful initial mission run still showed
the Mad Cat template. The retained `mech-marauder-current-packs` run documents
that incomplete outcome. After binding actual actor identity, the
`mech-marauder-bound-actor` run identifies chassis 32 and queues the Marauder
geometry on that exact live root during mission frames, including frame 1200.
It reaches the intentional 1600-frame Vulkan stop with movement/firing input.
This is a bounded smoke test, not sustained gameplay/fidelity acceptance.

Two other recovered boundaries were required. Actor helpers `0x41e9a0` and
`0x41df10` fuse direct tail jumps into their translated bodies, bypassing an
ordinary lookup router. Their adapters execute the original return path and
obtain the genuine extended definition/technology result. Without that support,
the mission stopped at `0x465204` reading a null definition. A subsequent
texture-sidecar stop came from stale test-harness paths after the installed
combined model pack changed; recomposing the current verified model roots fixed
those inputs without altering DEV or the pack itself.

The assembled donor export contains 41,572 triangles, including the cockpit and
five weapon meshes, with 38 rigid donor-bone batches. Per-vertex and rigid
experiments are retained separately under the ignored Marauder prototype's
`native-visual-r1/`. The first per-vertex payload was reproduced to its exact
SHA and preserved under `cpu-first/`. Native Mech Lab presentation now fits
additional geometry into the logical preview panel without moving mission
cameras, simulation, original models or guest state.

Original reader/mechlib media are copied locally and extended with named
definition/model/HUD aliases; no stock archive member is replaced. Review
colours are provisional, LOD1 reuses full donor geometry, and the original
Mad Cat controller/collision/HUD resources remain the starting template.
Texture finishing, attachment/muzzle alignment, damage/wreck behaviour,
collision tuning, sustained movement and save/load need further work.

The current native catalogue proves shared registration, selection and a first
live mission instance. Launcher pack discovery/building is still unfinished;
no installable Marauder pack or additional-chassis capability is advertised by
the installed host. DEV remains on its existing signed build. Acceptance stays
131/144.

Final October 25 validation is pinned in the private host's
`implementation-checks.json`. Both maintained applicators reproduce the compiled
host source exactly; the translated module is unchanged. Thirteen asset-free
Python checks and the native v1/v2 catalogue checks pass. Both isolated stock
captures (frames 650 and 699) are byte-identical to the selected parent, and all
700 original frame/count/hash rows match. The earlier comparison with a shared
skin-preference file is retained separately; the corrected harness initializes
an empty preference file for each isolated run. Archive comparison retains all
178 original reader members and all 60 original mechlib members unchanged.
