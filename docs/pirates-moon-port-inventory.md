# Pirate's Moon assets available for an optional MW3 port

Inventory date: 2026-10-29. Tracks issue #101. Read-only investigation of locally
supplied installations, with private decoded research output. No game assets were
installed, no runtime changed, and no native gameplay boundary was advanced.

## Result

Six additional chassis have donor geometry, textures, motion data, cockpit models,
reader definitions and UI icons: **Atlas, Awesome, Centurion, Clint IIC, Masakari
and Ryoken**. All six are credible port candidates. They are not drop-in MW3
archives or validated playable ports.

The existing Mech3AX tool decodes PM's model and motion banks. The existing typed
reader decoder accepts all 198 PM global reader documents after their v2 archive
directory is handled separately. The main remaining boundaries are converting
PM geometry/motion resource contracts, registering accurate chassis metadata,
and handling PM-specific weapons without changing stock MW3 behavior.

Scope: the common mech library and its supporting data, with targeted campaign
texture dependency checks. This is not a complete inventory of campaign terrain,
buildings, vehicles, cinematics or audio, and does not authorize their port.

## Additional chassis

Every row has `mech_<stem>.flt`, `mech_<stem>_1.flt` and
`mech_<stem>_hud.flt` in `zbd/mechlib.zbd`; `dfn_<stem>.zrd`,
`anim_<stem>.zrd` and `<stem>_prints.zrd` in global `zbd/reader.zbd`;
and green, grey and red `icon_<stem>_*` images in `zbd/rimage.zbd`.

| Mech / resource stem | Close / distance polygons | Named motion entries | Texture entries by donor prefix | Configuration records |
| --- | --- | --- | --- | --- |
| Atlas / `atlas` | 176 / 119 | 15 | 161 (`atlas`) | 5 |
| Awesome / `awesome` | 193 / 150 | 15 | 200 (`awsome`) | 5 |
| Centurion / `centurion` | 171 / 155 | 15 | 120 (`cent`) | 5 |
| Clint IIC / `clint` | 180 / 148 | 15 | 112 (`clint`) | 5 |
| Masakari / `masakari` | 204 / 144 | 14 | 160 (`masaka`, including `masakari`) | 5 |
| Ryoken / `ryoken` | 194 / 172 | 13 | 128 (`ryoken`) | 6 |

Counts are serialized polygons, not rendered triangles. Texture counts include
skins, damage/distance resources and any extra prefix matches; they are not
counts of unique artwork or proof every entry is used. Preserve actual spellings
such as `awsome` and `cent` when resolving references. PM's message resource
`MSG_MECH_CLINT` explicitly names **Clint IIC**; do not label it the base Clint.

Combined additions: 18 mech model members, 87 chassis-prefixed motion entries,
881 chassis-prefixed high-tier texture entries, 18 UI icons and 31 configuration
records. Each definition declares eight skin labels: primary and variants B-H.
The high-tier bank has 882 new names in total; the remaining name is
`vultur_d03_c`, not a seventh new chassis.

The different motion counts do not by themselves establish missing animations.
For example, Masakari's definition explicitly uses `masakari_trot` for both trot
and run. Ryoken has no separately named `ryoken_jump` or `ryoken_limpb` member;
its complete behavior and fallback rules still need to be checked.

## Available mech information

The six `dfn_*.zrd` documents have internal version 2 and provide:

- Torso and aim limits, turn/acceleration/deceleration settings, crouch height,
  recoil/lean/shake parameters and camera/cockpit attachment settings.
- Skin substitutions and damage texture mappings, firepoint names and body-part
  associations, motion-state references and canned-animation references.
- Engine settings, weapons and groups, ammunition and placement, equipment,
  internal-structure choices, armor mass and allocations for 31 configurations.
  Some configurations are explicitly hidden; the count is not the visible menu count.
- PM headlight offsets and selected technology/class metadata.

These documents are not a complete authoritative chassis catalogue. Atlas and
Centurion explicitly contain `max_mass` values of 100 and 50 respectively;
Awesome, Clint IIC, Masakari and Ryoken omit that field. Awesome and Clint IIC
also omit `weight_class`. Recover the effective executable metadata/defaults
before assigning gameplay statistics. Atlas/Awesome/Centurion say `clan=false`;
Clint IIC/Masakari/Ryoken say `clan=true`. Masakari and Ryoken declare
`omnimech=true`. A field's presence is data evidence, not proof of its runtime use.

`anim_*.zrd` supplies body damage/detachment, destruction and other effect
sequences; `*_prints.zrd` supplies footprint effects. `motion.zbd` supplies named
pose sequences for locomotion, falls, recovery and related states. Their timing,
node bindings and destruction behavior have not been exercised in MW3.

All six primary loadouts use weapon names present in the supplied MW3 weapon
table. Across all configurations, **13 of 31** reference at least one PM-only
weapon name, leaving **18** without that particular dependency. This comparison
folds case (`Narc` versus `NARC`); it does not certify equipment, balance, weapon
semantics or complete configuration compatibility.

PM's `weapons.zrd` has 18 names absent from MW3: three Heavy Lasers, ER Micro
Laser, three X-Pulse Lasers, Light Gauss, MRM10/20/30/40, light/heavy machine guns
and Thunderbolt 5/10/15/20 (`TBOLT*`). Their definitions are available to study;
importing those records does not implement weapon IDs, effects, Mech Lab rules,
AI or native firing behavior. Preserve MW3's own weapon table when isolating a
first chassis experiment.

## Archive inventory and overlap

Names and payloads were compared, not just filenames. The reader row below uses
the staged MW3 baseline; the installed MW3 reader differs, as described below.

| Resource | MW3 entries | PM entries | Shared names | Byte-identical shared payloads | PM-only names |
| --- | --- | --- | --- | --- | --- |
| Global `reader.zbd` | 178 | 198 | 172 | 100 | 26 |
| `mechlib.zbd` | 60 | 79 | 60 | 1 | 19 |
| `motion.zbd` | 258 | 364 | 258 | 0 | 106 |
| `rmechtex.zbd` | 3,360 | 4,242 | 3,360 | 3,330 | 882 |
| `rmechtex16.zbd` | 2,286 | 2,911 | 2,286 | 2,265 | 625 |
| `rmechtexs.zbd` | 2,286 | 2,911 | 2,286 | 4 | 625 |
| `rimage.zbd` | 394 | 376 | 341 | 229 | 35 |

The mech library retains all 19 MW3 families, including Elemental: Annihilator,
Avatar, Black Hawk, Bushwacker, Cauldron-Born (`cauldron`), Champion, Daishi,
Elemental, Firefly, Mad Cat, Orion, Owens, Puma, Shadow Cat, Strider, Sunder,
Supernova, Thor and Vulture. PM has 25 `dfn_` documents. The decoded library has
76 `.flt` model documents plus materials and manifest metadata. The extra
non-mech model is `headlight.flt`; `lab.flt` is shared by name.

Only the `format` member of the two mech libraries is byte-identical. This does
not mean all common geometry changed visually: format revisions, stored pointer
values and metadata can also change serialized bytes. Likewise, none of the
258 shared motion payloads is byte-identical; semantic equivalence is unmeasured.
Of 106 added motion names, 87 belong to the six newcomers and 19 are `_jump`
entries for inherited families.

The 30 changed shared high-tier mech textures are Elemental variants, `hole_*`
textures and `stump_damage02`. Copying the entire bank would change existing
content. All PM high-tier and both smaller mech banks pass the current RGB565
descriptor/span checks (4,242 / 2,911 / 2,911 accepted, zero rejected), as do
all 376 UI images. The supplied PM `rmechtexs.zbd` passes these RGB565 checks
despite its software-bank name; do not infer a general software-texture format
rule or equality with `rmechtex16.zbd` from it.

All texture references used by the 12 new exterior models resolve by exact name
in PM's high-tier mech bank. The six cockpit models also reference shared
`cpit*` / `madcat_cpit*` textures outside that bank. The union of these otherwise
missing names resolves in each supplied MW3 and PM `c1`-`c4/texture.zbd` bank.
This is a dependency-name check, not a pixel-equality or cockpit-rendering test.

Other PM-only global reader members include `cargotruck.zrd`, `mobile_hq.zrd`,
`packrat.zrd`, `bubbles.zrd`, `clutter_ani.zrd`, `dlgloadsave.zrd`,
`ia_progression.zrd` and `mprounds.zrd`. They are secondary research candidates;
their world-model dependencies were not enumerated. PM lacks six MW3 global
members: `camera.zrd`, `dlgmechlab.zrd`, `equipment.zrd`, `mechlibdemo.zrd`,
`mechs.zrd` and `player.zrd`. Wholesale reader replacement is inappropriate.

PM `Mech3Msg.dll` decodes to named UI message resources, including all six mech
names. Its numeric IDs must not be assumed interchangeable with MW3's. The
high-quality sound directory contains 812 records with duplicate filenames;
none contains one of the six chassis stems. This is not evidence that name
announcements are absent: logical-name-to-file mapping and playback remain open.

## Port boundaries and first useful experiment

1. **Resource conversion.** PM uses a 12-byte v2 archive footer rather than
   MW3's 8-byte v1 footer, and its mechlib version member is 41 versus 27.
   The extra footer DWORD's runtime meaning remains unresolved.
   The current [reader archive helper](../tools/remaster-launcher/reader_archive.py)
   rejects PM input. Mech3AX has explicit `pm` model/motion decoders, but this
   inventory did not repack anything into MW3 format. Preserve hierarchy,
   transforms, materials, UVs, damage nodes, LODs and motion bindings while
   investigating a selective conversion. Merely changing the footer is insufficient.
2. **Accurate chassis registration.** The existing
   [catalogue bridge](../tools/remaster-launcher/chassis_catalog.py) and
   [native stage](../tools/remaster-launcher/native-overrides/additional_chassis_stage.inc)
   inherit mass/class/technology from a stock metadata template. That boundary
   does not establish arbitrary PM chassis support, save compatibility or a
   publishable pack. Recover missing donor metadata and validate registration,
   selection, saves and spawn paths before calling a port playable.
3. **Behavioral dependencies.** Check animation commands, PM headlights,
   equipment, weapon IDs/effects, damage and cockpit behavior independently.
   Do not silently drop unknown required fields or grant fake service success.
4. **Bounded first candidate.** Atlas with its primary loadout is a useful first
   investigation: its definition includes mass/class, both exterior LODs and
   cockpit exist, all 15 named motions exist, and the primary weapon names are
   already in MW3. First prove offline model/motion conversion and reference
   closure; then validate a separate optional native Mech Lab/mission experiment.
   This is a proposed next task, not an implemented port or a choice to overwrite
   Annihilator or any other stock chassis.

Existing PM [native startup evidence](archive/pirates-moon-native-startup.md)
is separate from importing PM content into MW3. Neither that menu result nor
these offline decodes prove any of the six mechs works in native MW3. Original
assets and derived packs remain local under the [distribution policy](legal.md).

## Evidence and reproducibility

Sources: `D:/Projects/MW34Recomp/MW3-PiratesMoon`, `MW3`, and the corresponding
`local/mw3-pirates-moon-staged` / `local/mw3-staged` trees. All eight inspected
PM common banks match their staged copies. MW3's installed reader and interpreter
bank differ from staged copies; no cause or retail provenance is inferred. The
reader table above uses the staged hash. The installed reader comparison instead
has 101 identical shared payloads. The weapon-name sets used for the dependency
comparison are unchanged between these MW3 reader copies.

| Input | SHA-256 |
| --- | --- |
| PM `Mech3.exe` | `57cd2ee74bafda3eeb9e9353c7c78a8b7c213a81f3040f1be7c2a164c505ddd9` |
| MW3 `Mech3.exe` | `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf` |
| PM `reader.zbd` | `f5bbe76e6a4aea33aa65a0751ba1e00b792c7f57717446b25790d1842ca35dfb` |
| Staged MW3 `reader.zbd` | `fde31f93949aec52c0b22f51c57659b66ef667337f40f1ea42bc54204fb811bd` |
| PM `mechlib.zbd` | `b519966d6c5da2b5e40912e61b24df1bbbc929b41a910da602c63f5a079d5b2d` |
| PM `motion.zbd` | `33acf1ed176904e02290bdf083d77c7330f5147b6276946be9c872f963411f89` |
| PM `rmechtex.zbd` | `ac1d8cca763b33c9e17c2e3be06488c1617979221e922c783878b7e881d53c60` |

Private scripts, inventories, decoded JSON/ZIPs and logs are retained under
`reports/pirates-moon-port-inventory-20261029/` in that original checkout.
`inventory.py`, `summarize.py` and `dependencies.py` reproduce metadata checks;
the scripts import project parsers from the isolated inventory worktree.
`inventory.json`, `summary.json` and `dependencies.json` retain per-bank hashes,
member counts, payload comparisons and dependency results. No private report or
decoded game content is included in this documentation commit.

Python 3.14.7 ran bounded directory/name/span checks with 148-byte records;
duplicate names and overlapping payloads were rejected for the three main
archives. Sound directory names were separately retained as a list, since they
are not unique. The existing [typed decoder](../tools/remaster-launcher/zrd_document.py)
fully consumed 198 PM documents. Existing image probes checked descriptors and
spans; no PNG/rendering comparison was performed.

The installed Mech3AX `unzbd` version is `0.7.0-rc3`, SHA-256
`51cb49e53323b8d5a2f12fce3929c6aad134d72287f2545db9847626f1a20f0a`.
With a fresh private output directory, reproduce its decodes using:

```powershell
unzbd.exe pm mechlib MW3-PiratesMoon/zbd/mechlib.zbd <private-output>/pm-mechlib.zip
unzbd.exe pm motion MW3-PiratesMoon/zbd/motion.zbd <private-output>/pm-motion.zip
unzbd.exe pm messages MW3-PiratesMoon/Mech3Msg.dll <private-output>/pm-messages.json
```

All three commands exited 0. The model decoder emitted **24 transform comparison
warnings**, retained in `pm-mechlib.log`; the displayed matrices differ in small
floating-point values. No tolerance or fidelity acceptance is granted here.
The motion and message logs are empty. No game binary was executed.

Validation: six existing typed-document tests and seven image-decoder tests pass;
the MW3 reader archive helper accepts the installed MW3 archive and explicitly
rejects PM's. Links, evidence consistency and the documentation diff are checked
for the PR. No runtime build, game playtest, save/load check, pack installation or
release publication was performed. Binary addresses are not claimed by this
inventory; offsets used by the scripts are file offsets, not VA/RVA.
