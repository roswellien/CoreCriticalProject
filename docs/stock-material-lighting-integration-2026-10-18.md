# Stock material lighting and normal-map integration

Date: 2026-10-18. Continues the [current-main normal-map candidate](normal-mapping-integration-2026-10-17.md).
Acceptance remains **131/144**. Original media, prepared color/normal banks,
generated game code and executables remain local.

## Execution boundary

This work connects the approved original MW3 Avatar, Owens and Firefly material
previews to live original-model rendering. It retains their original geometry,
controllers, simulation, UVs and damage decisions. It also separates registered
material lighting from the normal-map option: disabling perturbation keeps
geometric sunlight on the same registered surfaces.

Original opaque texture/depth/world-camera guards remain. The material catalog
admits additional stock geometry outside the terrain-cell path; unrelated sky,
HUD, blended effects and unregistered materials retain their existing routes.
An exploratory all-opaque admission was narrowed back to registered materials
before the final build. No original producer or terrain transformation is bypassed.

## Exact material registration and bank alignment

The October 16 normal previews used approved color tiles from the primary mech
bank. The live hardware renderer reads the separate 16-bit mech bank. Native
texture hashes established that its tiles differed in dimensions and pixels.
Registering the preview colors alone therefore did not produce live stock hits.
The unmatched exploratory runs are retained; they are not successful material
coverage evidence.

[The catalog preparer](../tools/remaster-launcher/prepare_surface_normals.py)
checks pinned source-bank and preview-manifest hashes, every RGB565 color word,
normal source pins and source stability during preparation. The published bank
uses rounded RGB565 conversion; simple channel-bit truncation is not equivalent.
Names alone never admit a material. Conflicting normal interpretations for the
same complete color identity fail rather than silently selecting one.

[The optional bank aligner](../tools/remaster-launcher/align_surface_colour_bank.py)
creates a separate preview bank. It copies the exact reviewed primary-bank entry
bytes for 47 selected stock textures into the corresponding existing 16-bit bank
entries. It preserves the remaining 2,239 entries and their ordering. No entries
are added. The audited 26 damage-texture names absent from the 16-bit bank remain
in the existing primary bank; the tool requires an explicit exact missing-name
list. Existing banks and the regular Play asset configuration are untouched.

The new catalog preserves the earlier ground binding and contains **48 unique
full-content texture keys**. Source bytes, dimensions and 16-bit format identify
materials across maps and handle reuse. It was prepared twice with identical
output bytes. Shared `footpad` and `weap_hole` preview interpretations conflict,
and `mech01` does not match the selected live color layout; those shared bindings
remain unchanged. This is not complete material coverage for every chassis part.

Normals retain linear RGBA samples and source resolution. Stock texture rows use
the bank's stored order. The original top-down texture-V basis requires the
explicit green-channel inversion of the OpenGL preview normals; replacement
model pack orientation is unchanged. No additional relief artwork, color-space
conversion or strength baking is introduced.

## Runtime and preparation changes

- [The normal material contract](../runtime/graphics/material_normals.hpp) admits
  up to 256 surface bindings sharing up to 64 images, retaining the 256 MiB pixel
  budget and full image hashes. Packing shares byte-identical normal images.
- A common validated catalog-header reader exposes material registration without
  reading normal-image payloads. Mapping-disabled rendering loads these keys but
  allocates no surface normal images. Full enabled loads retain all image and
  material-name validation.
- [The actual surface adapter](../tools/remaster-launcher/native-overrides/surface_normals_stage.inc)
  caches registration separately from its optional normal index, preserving
  version, dimensions, format, pitch, backing address and address-wrap checks.
- [The integration installer](../tools/remaster-launcher/apply_material_normals.py)
  uses registration for stock lighting admission. Perturbation is an independent
  per-draw choice; the main composition recipe includes these changes.
- Zero-strength draws bind the flat normal descriptor. An earlier comparison
  exposed a one-pixel difference from sampling an unused normal texture at zero
  strength; the corrected disabled/zero-strength controls match all three captures
  byte for byte. Shader code and positive-strength sampling remain unchanged.
- Positive material-binding logs now contain complete source keys so native
  coverage can be joined to the registered material aliases. Optional
  `MW34_SURFACE_NORMAL_TRACE=1` also records misses once per cached source version.

## Checks and local evidence

Local workspace: `C:/Users/jcbla/MW34SunTests/stock-normal-integration-r1/`.
The final main-derived source reproduces exactly through the composition recipe,
with line endings normalized, and keeps the existing 37,201 native object list.
Heap, photo/replay, turret and guest-memory services are retained.
The remastered background/button asset configuration and restored original hover
wave remain included. The authored menu-wave CTest also passes.

During final reproduction, the active main host's `mfc_stage.hpp` no longer
matched its reviewed input pin. It was left untouched. A separate input copy used
the saved, exactly pinned pre-integration file; the other five pinned main adapters
still matched. That recipe reproduced all 88 final host files after normalizing
line endings. This does not review or integrate the newer concurrent main change.

Eight asset-free Python tests cover named packing, catalog sharing/bounds,
truncation/hash rejection, exact bank colors, normal row/Y conversion, conflicting
source interpretations, unchanged bank entries and existing launcher/cache
contracts. CTest covers the real surface adapter and a separate mapping-disabled
process that retains material registration from a header without loading images.

The initial exploratory input runs reused a private test pilot whose selection
was saved during mission loading. Subsequent controls use a fresh frozen game,
pilot, configuration and registry copy per run, with a junction to existing assets.
The original protected pilot/registry identities are checked separately. Earlier
exploratory files remain intact.

## Completed stock controls and preview identity

The Normal Mapping Preview selects
`C:/Users/jcbla/MW34SunTests/stock-normal-integration-r1/host/build/entry_commandline.exe`,
SHA256 `e1ba9e73edbd416dcde92903390262b32f38e65ae0bbc0eb2b5d4d2bf90fd1b7`.
The profile and 88-file source snapshot were updated together, retaining backups.
Regular main Play and the separate Big Lake launcher retain their earlier builds.

Final cases under `runs/` each reached the intentional 1,800-frame limit; exit 1
is the expected budget stop, not a normal-quit or mission-completion result.
Original protected pilot/registry hashes remained unchanged.

| Comparison / case | Result |
| --- | --- |
| `baseline-firefly-r3` / `disabled-firefly-r4` | All 1,800 original frame/count/hash records and captures 1600/1700/1750 identical. |
| `geometric-firefly-r4` / `zero-strength-firefly-r4` | Same original records and all three capture files identical. Mapping-off loads 48 registered keys and zero surface normal images. |
| `geometric-firefly-r4` / `firefly-r4` | Original records identical; expected rendered normal-detail differences. |
| Owens, Avatar, Firefly r3 / r4 | Positive-strength repeat captures identical for each chassis; original records identical. |
| Live registered identity matches | Owens 14; Avatar 15 chassis-specific identities plus shared `mech02`; Firefly 11. All enabled cases load the 48-image surface catalog. |

`native-comparisons-release.json` retains the full local comparison and key joins.
Equal-color aliases do not establish a specific damage state from their names.

## Big Lake atmosphere and preset selection

The first stock controls deliberately used neutral daylight and the original sky.
Following the user's appearance feedback, the preview now selects the existing
Big Lake **sunset** preset by default through the shared
[sun preset catalog](../tools/remaster-launcher/sun-presets.json).
This restores its low-angle sun direction, warm direct light, colored ambient
fill and automatic sky/haze treatment. The renderer already contains the Big Lake
atmosphere implementation; this continuation connects its configuration.

[The shared resolver](../tools/remaster-launcher/resolve_sun_preset.ps1) validates
the preset and emits the exact runtime values used by both launcher checks and
native launches. `--lighting-preset sunrise`, `sunset` or `midday` selects another
registered preset through `Play MW3 - Normal Mapping Preview.cmd`. Selection is
recorded with the effective environment. Invalid names and invalid color values
fail visibly. Two asset-free tests exercise the real resolver.
Dedicated [Sunrise](<../Play MW3 - Normal Mapping Preview (Sunrise).cmd>) and
[Midday](<../Play MW3 - Normal Mapping Preview (Midday).cmd>) shortcuts expose the
selection without editing a profile; the ordinary preview shortcut uses sunset.

Sunset uses azimuth 225, elevation 9, direct strength 1.6 and ambient 0.32;
sunrise uses azimuth 45, elevation 11, strength 1.4 and ambient 0.32. These are
static Big Lake preview presets, not automatic mission-map detection or an
advancing day/night cycle. Normal strengths remain independently configured;
cast shadows retain the preview's disabled setting in these atmosphere checks.

The ordinary native launcher also now accepts absolute executable paths without
incorrectly prefixing the project directory. The preview uses such a path.
The actual launcher prepared assets and presented two bounded menu frames using
the registered absolute executable, sunset, automatic sky/haze and the remastered
5760x4320 background. Its stderr records the expected two-frame budget stop;
this is a launch-path smoke check, not a gameplay test. Evidence is local at
`local/remaster/runs/20261018-074351-522/`.

Both `firefly-sunset-r5` and `firefly-sunrise-r5` reached 1,800 frames with original
draw triples equal to the neutral Firefly route. Each recorded 16,128 tinted sky
draws and 598,023 haze draws. Captures show the intended atmosphere and directional
lighting changes. `atmosphere-comparisons.json` retains settings and counters.

## Remaining integration work

Native strength calibration against the approved 12x preview, broader world
material registration, shared-material interpretation, near-plane/zoom behavior,
damage and LOD transitions, weapons, campaign play and settings-menu integration
remain open. The stock tests do not establish whole-game coverage, a performance
gain, mission completion or additional formal acceptance credit.
