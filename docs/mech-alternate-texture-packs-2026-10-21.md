# Faithful mech alternates and launcher packs

The selected method reuses approved upgraded detail, transferring the original
MW3 B–H colours and markings. Matching original UV panels use spatial colour
transfer; replacement atlases learn their palettes from paired original panels,
with original camouflage variation adapted to the replacement UVs. Shared dark
mechanisms, glazing, weapons, geometry and primary normal maps are retained.
The existing original-model Bushwacker alternates and replacement skin D remain.
Earlier individually generated candidates are retained locally as unused work.

Local deliverables are in
`local/asset-packs/mech-alternates-20261021-r1/`:

* `shared-mech-textures-1.0.0.mw3pack`: the two global original-model texture
  banks, shared across Training and all four operations; includes Elemental.
* `com.mw3remaster.mw5-mechs.mw3pack`: 14 replacement chassis, B–H at both LODs.
* `com.mw3remaster.updated-mw3-mechs.mw3pack`: four updated original chassis,
  B–H at both LODs.
* `launcher/MW3RemasterLauncher.exe`: launcher with shared-pack installation
  support. It uses the matching native profile in this checkout.

The five separate environment packs remain in
`local/asset-packs/environments-lighting-20261021-r1/`. No mech banks are
duplicated into those operation packs. All artifacts remain local; creating a
pack does not grant redistribution rights.

The shared pack uses the existing `prepared-environment-v1` file contract with
the explicit `shared-mechs` ownership role. Only `zbd/rmechtex.zbd` and
`zbd/rmechtex16.zbd` are admitted. It contains authored normals only, and cannot
override world lighting, atmosphere or surface-detail settings. First enabled
pack wins for this ownership role independently of operation selection. Turning
it off removes its bank and normal bindings. Whole-chassis priority remains
unchanged for the two model packs.

The optional host adapter selects a livery from each original actor's actual
material names. Close and distant resources must both be complete. Unknown,
mixed or incomplete optional identities preserve original rendering. Exact
pixel comparisons share unchanged images between skins and LODs; a short hash
collision cannot merge different pixels. Original simulation remains in control.

The all-skin host was rebased on the selected cinematic-capable host. Only the
mech adapter and the translation-unit helper include changed; the new helper
is separately pinned. Fixture, atmosphere, light retention, mission ambient,
normal readers, keyboard services and cinematic routing sources were retained.
The compiled host SHA-256 is
`a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c`.

Evidence is under
`local/work-ahead/mech-alternates-completion-20261021-r1/`:

* `conversion-r1/models.json`, `stock-banks.json`: source identities, converted
  outputs, original coverage and conservation of every unrelated archive entry.
* `conversion-r1/model-review/`: 378 offline images covering 126 alternates on
  all 18 registered models, with front/opposite/rear contact sheets reviewed.
* `conversion-r1/stock-review-*.jpg`: representative original/detailed panels
  across all remaining stock chassis and all seven alternate palettes.
* `rebase.json`, `native-build-r3.log`, `source-checks.log`: source conservation,
  successful native build and 3,327 original material-name identity controls,
  independent actors, mixed/unknown handling and exact-image sharing.
* `conversion-r1/shared-pack.json`, packaged `packs.json`: exhaustive member
  hashes and archive closure. The original banks remain untouched; the rebuilt
  larger bank is below the unsigned 32-bit archive offset limit.
* `launcher-checks.log`, `conversion-r1/installation-check.json`: launcher
  installation and relocated ordinary preparation, combined content, shared
  content alone and disabled content. Preparation is guarded against launching
  the game.

Existing authored primary normal images are rebound to the new stock colour
keys where present. A primary with no authored registration retains that
unregistered behaviour; no speculative normal image is substituted. The shared
pack has 711 normal keys in three pages. Native page and aggregate budgets were
not increased.

These are offline asset, model, archive and preparation checks. No game was
launched for this work. Walking, combat, gameplay LOD transitions, performance
and campaign-wide appearance still require playtesting. Strict native gameplay
acceptance remains **131/144**. No commit was made.
