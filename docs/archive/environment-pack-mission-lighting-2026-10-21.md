# Mission lighting carried by environment packs

Environment packs now carry their mission presentation settings alongside the
existing texture, normal-map and effect-light resources. No separate map pack
is required for these day/night and lighting changes. Actual mission geometry
and gameplay remain supplied by the user's original game data.

Launcher **1.0.10-preview** and its reviewed private native host are deployed at
the ordinary launcher location. Existing graphics, pack selection, environment
migration state and the soundtrack choice are preserved. The new environment
packs were tested in separate user storage, not enabled over the user's current
development visuals.

## Data contract

`prepared-environment-v1` optionally declares
`lighting: "environment/lighting.json"` in its environment registry. That file
must appear in the size/SHA-256 file table as `MW34-lighting-v1`; the format also
appears in `native_payload.required_formats`. Older packs without this member
remain supported. A lighting pack requires an explicitly matched host with
`mission_environment_versions: [1]`; unsupported hosts fail with an update error.

The lighting JSON is schema 1 with exactly `schema_version`, `missions` and
`maps`. Campaign packs contain their complete operation's mission IDs, and no
Training map entries. Training contains its registered BIG LAKE preset catalog
and no campaign missions. Operation 4 includes c4m1 through c4m6, including
missions read from C4b archives. Duplicate keys, unknown fields, out-of-operation
IDs, missing values, invalid RGB/boolean fields, nonfinite numbers and invalid
horizon intervals are rejected. Interior missions retain their existing zero
sky-horizon exception.

Campaign data covers sun/moon angles and colors, ambient fill, night world gain,
sky grading/glow/horizon, haze/fog, shadow settings, presentation weather
parameters and authored environment emitters. These are data values, not paths,
programs, arbitrary environment variables, scripts or gameplay rules. Dynamic
lighting/weather implementation remains native runtime code. Mission metadata,
reader identities and simulation behavior are not replaced by the catalog.

`mission-lighting.json` preserves all 20 current authored campaign environments,
including C2M4 ambient 0.40. The existing compiled defaults remain the fallback
for missions not covered by an enabled lighting pack. The first enabled pack
for an operation supplies the whole operation's resources and lighting, matching
the existing environment-pack priority rule. Disabling packs removes their
per-launch lighting binding and restores the published defaults; it does not
silently carry a previously selected pack into another launch.

Training pack presets are passed to the shared read-only PowerShell resolver
and retained in the final session profile. An automatic pack default does not
set manual campaign-preview mode. Existing explicit preview overrides continue
to use that mode.

The coordinator writes campaign selections as a fresh bounded `MW34ENV1`
catalog in writable per-user preparation storage. The native reader validates
lengths/counts, mission identities, flags, finite bounded values, emitter counts
and exact EOF, then publishes the complete updated table transactionally.
Successful original mission-reader opens still select the active environment;
failed opens, Training and mode reset retain their existing behavior.

## Build and evidence

All five local collections are rebuilt at
`local/asset-packs/environments-lighting-20261021-r1/`, version **1.1.0**:
Training and Operations 1–4. `packs.json` is the completed archive marker.
Every archive member was independently read back and hashed. Comparing old/new
file tables confirmed every texture, normal-map, surface-detail and effect-light
resource pin is unchanged; only registry metadata and the new lighting file vary.
The original 1.0 archives and their evidence remain intact.

`build_environment_packs.py` now includes these catalogs in fresh full builds.
`repackage_environment_lighting.py` upgrades verified installed environment
resources without rerunning texture conversion. Both preserve source data;
outputs require a fresh directory. Packs and original-derived resources remain
local under the existing distribution policy.

The reviewed host is `local/remaster/gpu-native-pack-lighting-r1`, SHA-256
`0d3d920f6b560ddcd92fbeeb4034d59430ddd46a19b75269255fc8ec83fe12ef`.
All 117 previous host-source pins were checked. Only `campaign_lighting.hpp`
changed, adding the optional loader around its unchanged builtin database;
`mission_environment_pack.hpp` is the new bounded reader. Mech bindings,
fixture definitions, shaders and other resource readers are unchanged. Exact
legacy mech/environment admissions include this reviewed successor. The selected
profile adds the new host/snapshot identities and capability; all other values
were compared and retained. Previous entry files and profile bytes are under
`reports/pack-lighting-20261021/before-deploy/`.

Checks passed:

- Native host build; actual native-reader roundtrip of all 20 campaign environments;
  changed ambient/weather selection through CampaignManager; failed reader-open
  and Training reset; truncated, trailing, NaN, duplicate and unknown-ID controls.
- Twenty-five Python checks, including pack priority/relocation, absent/disabled
  bindings, host capability, invalid catalogs, archive authoring and the real
  PowerShell Training resolver. Full C# launcher suite and self-contained publish.
- C# installation of new Training and Operation 1 packs into
  `D:/MW3LightingPackTrial-20261021-r1/UserData/mods`.
- Bundled external runtime in `D:/MW3LightingPackTrial-20261021-r2/App/Runtime`
  prepared those packs with both mech packs and soundtrack. Its final session
  profile points at Training's pack-owned preset catalog and a generated
  four-mission Operation 1 catalog. That actual catalog also passed the native
  baseline-reader check.
- Actual bounded Training presented all 340 requested frames through Vulkan,
  with final geometry 16,920 CPU vertices, 1,287 GPU vertices and two GPU batches.
  Evidence is in the r2 trial's `UserData/training-session/native`. Exit 1 is the
  requested frame-budget stop. This is not a new campaign appearance, dynamic
  lighting fidelity, weather-quality or audio-quality acceptance claim. Real
  campaign play and broader visual comparisons remain open.

The final snapshot audit restored two inherited nested-header entries
(`audio/local_cd_audio.hpp` and `memory/guest_memory.hpp`) omitted when the new
snapshot initially enumerated only top-level files. Their source bytes had
already passed the baseline audit and were unchanged. All 118 final source pins
now verify. A fresh r3 external runtime retains the complete snapshot; comparing
its file table with the executed r2 trial found only that metadata file differs,
with the other 697 files identical. The r2 evidence remains intact.

This advances installed environment content into native per-mission presentation
selection. Strict acceptance stays 131/144. No original-code fallback, generated
game-code publication, commit or upload was performed as part of this change.
