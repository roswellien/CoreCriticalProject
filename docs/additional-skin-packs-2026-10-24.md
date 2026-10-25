# Data-driven additional mech skins

Owner request: install a content pack and automatically discover its named skins
in game, preserving all existing skins. Creators must not modify or compile
engine code for every skin. Sommerset is the first authored example, not an
engine special case. This is optional presentation work; strict native
acceptance remains **131/144**. No commit or public upload is authorized here.

## Registration contract

An unsigned `.mw3pack` uses schema 2 and native profile `prepared-skins-v1`.
Its `pack.json` points to `skins/skins.json`, declares `BWTEX1` resources and
requires runtime capability `additional-mech-skins` version 1. The launcher
imports and verifies it through the same bounded content-pack storage as other
community packs. It does not claim ownership of a chassis or an original skin.

The registry contains a `skins` array. Each record supplies:

- `id`: stable namespaced identity, beginning with its pack ID and `:`.
- `name`: the display name read by the Mech Lab SKINS selector (printable ASCII).
- `chassis`: the model identity it fits.
- `mesh_sha256.close` and `.distance`: compatible mesh payload identities.
- `textures.close` and `.distance`: declared, integrity-pinned BWTEX1 files.

For example, Sommerset's identity is
`com.corecritical.sommerset:sommerset`, its name is `Sommerset`, and its chassis
is `bushwacker`. Those strings live in the local authored pack. Native runtime
and launcher implementations do not branch on that pack ID or skin name.

The coordinator first resolves the enabled model packs, then collects every
enabled skin pack. It checks mesh compatibility, both LODs, file closure and
integrity. Different skin IDs compose additively, regardless of whether a skin
pack appears before or after its model pack. Duplicate identities, wrong UV
meshes, missing model packs, missing LOD resources and corrupt files fail
visibly. An older runtime receives an actionable capability error.

The coordinator writes a bounded `BWSKIN1` catalog of resolved records for the
native reader. This is an internal launch artifact, not a creator's format.
The native reader enumerates that data to extend the original Mech Lab list. New names and
texture sets require new pack data, not new bindings or per-skin code.

## Selection and existing content

Installed compatible skin packs append their declared names after the original
Mech Lab **SKINS** rows. This works through Instant Action → Mech Lab and its
existing left/right arrow controls. Sommerset is an additional ninth choice
for Bushwacker; the original eight names and textures remain available. The
superseded Ctrl+Shift+F8 window and shortcut input hooks have been removed.

Added appearances use separate process-local texture slots starting at 8.
Original callbacks still receive a valid retail skin index, preserving original
preview-resource lookups and loadout records. Host preferences save the stable
namespaced ID per chassis outside original game saves. Selecting an original
row clears that chassis's additional appearance. This does not add a custom
skin field to original saved loadouts or establish per-loadout persistence.

A selected appearance applies to the player's mech and presentation previews.
It does not repaint live enemy actors with the same chassis. Disabling skin
packs removes their catalog entries. The registry name, chassis and compatible
meshes determine discovery; no Sommerset-specific native code is required.

## Authoring and scope

`tools/remaster-launcher/build_skin_pack.py` accepts a local skin project with
an arbitrary namespaced pack/skin identity, display name, chassis, material
images and close/distant mesh metadata. It produces both texture sidecars, a
portable registry, manifest and verified `.mw3pack`. No executable, source game
code or model mesh is included in this skin-only archive.

Sommerset's editable source and packaged output remain under ignored
`local/work-ahead/sommerset-skin-pack-20261024-r1/`. Its authored weapon-front
orange accents were baked into the material atlases, rather than relying on
the separate material assignment used only by the Blender preview. Base-color
damage and existing model normal maps are used by the current native material
path; the Blender preview's metallic/roughness nodes are not a new native PBR
material format. Generated review artwork does not establish new 4K detail.

This establishes data-driven **additional skins for supported model readers**.
It does not establish arbitrary new chassis or mission support. The existing
fixed model roster and original mission loader still require generic extension
work before those new content types can be advertised. The same owner rule
applies: implement each content-type reader once, then discover individual
assets through pack registries. Do not add per-asset engine switches, hardcoded
names or code-generation/recompile steps for ordinary creator content.

## Verification and DEV delivery

DEV now selects the signed Mech Lab runtime under
`D:/MW3MechLabSkins-20261024-r1/Runtime/`, based on the previously delivered
`MW3AdditionalSkins-20261024-r2` source. Its translated module is unchanged.
The seven changed host files remove the shortcut interface and integrate the
original list/callbacks; parent menu/audio/controller/graphics work is retained.
The separate private display/DPI candidate remains separate.

Verification includes:

- 16 Python checks: original bindings, independent community names,
  order-independent composition, disable cleanup, compatibility and corruption,
  and the final child launch profile retaining the generated catalog.
- Launcher content checks: unsigned skin import, capability rejection and
  existing pack/music/UI/cinematic paths. Release build has no warnings/errors.
- 61 native catalog and appearance-selection checks.
- Actual native Instant Action → Mech Lab mouse route: Madcat retains its eight
  stock rows; selecting Bushwacker adds Sommerset at row 8. Eight original-arrow
  clicks visit original rows 1–7 then Sommerset, updating its visible label and
  colored model preview. Returning left selects the original row 7 and clears
  the extra appearance.
- Original Done → Launch route completes 1,300 Vulkan presentations with the
  added skin applied to the player in gameplay. The original-skin route also
  completes 1,300 presentations. These runs stop at explicit frame budgets,
  not unexpected game crashes. Full combat/destruction coverage is not claimed.
- A clean application from the completed pre-skin parent reproduces the feature
  sources; no shortcut polling/header include remains in active composition.

Sommerset 1.0.1 changes pack guidance to Mech Lab while retaining the same stable
identity and texture payloads. Its archive is
`local/work-ahead/sommerset-skin-pack-20261024-r1/mechlab-1.0.1/sommerset-1.0.1.mw3pack`.
The pack is installed in DEV; existing pack choices and user graphics/control
settings are retained. Select **Bushwacker → SKINS → Sommerset** in Mech Lab.

Earlier shortcut prototype evidence remains under
`D:/MW3AdditionalSkins-20261024-r2/`; its UI checks do not establish Mech Lab
behavior. Current captures/logs, source pins, signed runtime manifest, preflight
and activation evidence are under `D:/MW3MechLabSkins-20261024-r1/`.
Destruction/wreck appearance remains the separate open issue MW3-003.
No installer, public update, R2 upload, Git commit or push was performed here.
