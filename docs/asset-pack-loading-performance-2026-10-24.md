# Asset pack loading: demand loading and reusable preparation

This change advances installed content → prepared resources → replacement
rendering. Original instance identity, source skin selection, game callbacks
and rendering are retained. Strict native acceptance remains **131/144**.

## Changes

The native renderer previously read every enabled replacement chassis, both
LODs, all eight original skin sets and every added skin when replacement
resources initialized. It now initializes the resource system separately and
loads a model/LOD after an original instance matches its roster and skin.
Original alternate textures load when that skin is requested; a pack skin
loads when selected for the player or its preview. Resources stay resident for
the process lifetime, so repeated use does not reread them. Missing optional
original appearances retain the original rendering path. Invalid required
payloads still fail visibly; launcher pack admission remains upfront.

Geometry/texture indices append monotonically; existing queued geometry and
texture identities remain stable. Original gameplay, skin names and Mech Lab
callbacks are unchanged. Native resource log messages include chassis, LOD,
skin and read duration. First use can still incur a resource read/upload; this
does not establish asynchronous streaming or eliminate all loading stalls.

Prepared environment cache keys now depend on selected verified inputs,
resource-generation settings and producer source identities, without including
the native executable hash. A compatible EXE-only update reuses the same images.
Fresh pack/capability admission still runs before cache use. Changed inputs,
producers, budgets, corrupt output or incomplete receipts still invalidate it.
The cache-key change itself requires one initial rebuild; historical caches
are retained. Per-launch bindings are recomposed from the current profile.

## Validation

Evidence lives under `D:/MW3LazyResources-20261024-r1/`, with a fresh source clone
of the completed Mech Lab build. Only `mesh_override_stage.inc` and
`additional_skins_stage.inc` differ in native host sources. The translated
module and parent audio/controller/Mech Lab/renderer work are retained.

The same full installed model pack was enabled in both native tests:

| Bounded route | Previous | Demand loading |
| --- | ---: | ---: |
| Mech Lab route, 700 presentations | 47.56 s | 38.11 s |
| Model/LOD records read | 36 | 2 |
| Albedo sets read, including cycling all Bushwacker skins | 290 | 10 |
| Mech Lab → mission, 1,300 presentations | 60.61 s | 51.71 s |
| Model/LOD records read on mission route | 36 | 7 |
| Albedo sets read on mission route | 290 | 20 |

These times include original menu navigation, rendering and captures, not pure
startup duration or a prediction for another PC. The initial main-menu-only
route has no 3D model resource demand and showed no established speedup.

All 700 Mech Lab and 1,300 mission original draw-count/hash rows match their
references. All three Mech Lab captures and six mission captures match byte for
byte. The mission candidate is the signed, staged executable and preserves
Sommerset player appearance, original enemy skins and both observed LODs.
Runs stop at explicit presentation budgets, not unexpected game crashes.

29 Python checks pass across startup cache, environment packs, models and skins.
The EXE-update cache test performs fresh admission with the updated host before
asserting resource reuse and current session bindings. Existing incompatible
host, file replacement/corruption, damaged output, producer/budget changes and
interrupted-writer checks remain in place.

Actual installed-pack preparation rebuilt once, reaching soundtrack preparation
at 134 seconds. Subsequent complete preparation-only runs took **0.870 s** with
the new host and **0.873 s** with the previous compatible host. Both logged
resource reuse after fresh admission. These measurements exclude native game
startup. DEV's prepared cache is already populated for the new identity.

A 500-presentation native check removes only Madcat's optional original B-skin
binding. Its selection remains usable, reports replacement unavailable for
skin 1 and preserves original rendering without a crash.

DEV now selects `D:/MW3LazyResources-20261024-r1/Runtime/`. Authenticode is valid;
all 665 runtime member pins and 155 host source pins were checked. Profile
activation preserves existing graphics, controls and enabled pack roots.
The separate model-pack writer and private display/DPI candidate were untouched.

## Initial launch clarification

The owner clarified that the reported delay is **before the game window**, not
Mech Lab or mission loading. The route timings above are regression/performance
evidence for demand loading; they do not measure that reported wait.

Initial-launch investigation is under `D:/MW3InitialLaunch-20261024-r1/`.
Read-only C# preflight probes measured game validation, runtime lookup, profile
creation, soundtrack/UI/cinematic selection and Python discovery at roughly
0.44 seconds combined; this excludes controls preparation and the UI handler.
The actual Python coordinator → PowerShell → native path reached its first
presentation in 6.51 seconds with changed-file checks, then 2.02 seconds on a
warm run. Neither number is a complete Play-button-to-interactive-menu measure.
No mission route or replacement model loading is involved in these measurements.

The observed cold preparation spent about 128 seconds generating environment
resources before native startup. EXE-independent cache reuse prevents repeating
that work solely because of a compatible runtime update. First preparation and
changed environment inputs/producers can still incur it; cold generation was
not eliminated by the demand-loading change.

`tools/remaster-launcher/apply_lazy_model_resources.py` applies the narrow native
change to a fresh completed Mech Lab source snapshot. The maintained base mesh
template predates current readers and must not replace a completed host.
No installer, public update, upload or Git commit is part of this change.
