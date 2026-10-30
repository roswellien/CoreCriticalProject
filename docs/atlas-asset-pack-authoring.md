# Pirate's Moon Atlas asset-pack prototype

Start with [How to add a mech with an asset pack](authoring-additional-mechs.md)
for the reusable workflow and pack README template. This page is its ongoing
Atlas worked example and compatibility record.

Issue #104 starts Atlas through the same portable project, `.mw3pack` builder,
launcher import and private resource composition used by modders. The pack is
data-only. Its stable identity is `com.corecritical.pm-atlas:mech`; no Atlas
registration, numeric ID or executable is added to runtime source.

**This is an unreleased compatibility prototype.** The proposed
`additional-mech-chassis: 3` contract is deliberately absent from released
runtime profiles. Existing runtimes reject activation. Do not edit an installed
profile to claim support: the modern headlight adapter remains under validation,
and compiled effect dependencies remain unfinished. Neither this change nor a
successful import publishes an update.

## Build from the user's original installation

Use Python 3.11+ and the separately installed Mech3AX v0.7.0-rc3 Windows x64
converter already documented in [dependencies](dependencies.md). Conversion
runs only on the author's machine. The receiving pack needs neither Mech3AX nor
the donor installation. Keep projects, conversions and packs outside original
installations and Git; the [distribution policy](legal.md) still applies.

From the repository root, select fresh output directories:

```powershell
python tools/remaster-launcher/prepare_legacy_chassis.py `
  --game-root 'C:/Games/MechWarrior 3 Pirates Moon' `
  --source-game pm --resource atlas `
  --converter-dir 'C:/Tools/mech3ax-v0.7.0-rc3' `
  --output 'local/atlas-authoring' `
  --pack-id com.corecritical.pm-atlas --name Atlas `
  --metadata-template annihilator

python tools/remaster-launcher/build_chassis_pack.py `
  --project 'local/atlas-authoring/project/project.json' `
  --output 'local/atlas-pack'
```

The second command produces
`com.corecritical.pm-atlas-0.1.0-preview.mw3pack`. Import with the development
launcher's normal **Mods & Packs → Install Pack** path. Import validates the
manifest and references; it does not grant runtime capability or prove fidelity.
The C# `PackManager.InstallPack` path was exercised locally with the resulting
archive, using an isolated library rather than the player's installed packs.

`project/` is portable: all resource paths are relative. `conversion/` contains
editable converter JSON and conversion logs; `provenance.json` records source
bank and tool hashes, commands and a final source-unchanged check. No proprietary
binary, mesh, texture or generated translation is part of this source change.

`metadata_template: annihilator` supplies the existing mass/class/technology
getter ABI only, checked against Atlas's 100-ton Inner Sphere assault metadata.
It does **not** supply Atlas's model, skeleton, collision definition, motion
tracks, weapon locations or loadout.

## Included content and proposed contract

| Resource | First Atlas project |
| --- | --- |
| Model hierarchy | PM close, distance and cockpit models, selectively converted to MW v27 |
| Materials/textures | Compact material table; 39 primary, damage and cockpit texture payloads |
| Motion | All 15 Atlas clips, converted to MW v4; original part tracks retained |
| Definition | PM fields and primary configuration; headlight field retained; modern lamps use explicit pack attachments |
| Reader animation data | Atlas damage/effect and footprint scripts |
| UI | Original green silhouette converted to the existing 41×50 mask contract |
| Not yet included | Other four configurations, seven alternate skins, headlight model and five footprint objects/compiled effects |

The existing `additional-chassis-v1` registry accepts a `legacy` descriptor in
place of prepared visual bindings. It requires `required_formats: ["MW3LEGACY"]`
and exact capability version 3. A descriptor has schema version 1, source
`resource`, `definition`, `materials`, `silhouette`, three `models` roles
(`close`, `distance`, `cockpit`), and named `motions`, `animations`, `textures`.
All files are content-addressed and SHA-256 pinned by the normal builder.
Legacy and prepared-visual chassis are kept in separate packs.

The coordinator checks bounded model/material/image/motion layouts, resource
names and references. It assigns a stable generated resource name, relocates
material indices, namespaces references and composes private MW3 banks. It
extends `reader.zbd`, `mechlib.zbd`, `motion.zbd`, high-tier `rmechtex.zbd` and
`rimage.zbd`; source installations stay read-only. Only the material index and
common animation index are replaced; unrelated stock members remain unchanged.
Low-tier texture selection and independent additional-skin packs are not part
of this prototype's supported route.

The original actor dynamically constructs fall/get-up motion names. The
composer therefore retains `<generated-resource>_fallb`, `_getupf`, `_getupb`
and the other original suffixes. Numbering clips would silently break those
lookups. Camel-case footprint identifiers are also namespaced. Motion records
remain byte-identical after author-side format conversion.

## Demonstrated native boundary

On October 29, 2026, the imported pack was composed with the development
coordinator and explicitly supplied to the existing native host for a bounded
compatibility test. This bypass of profile admission was a local diagnostic,
not a change to production capability declarations.

- The normal Instant Action → Mech Lab path listed and selected **Atlas**.
- The native original definition parser constructed index 32; the preview
  displayed Atlas's original geometry, silhouette, 100-ton capacity and PM
  primary weapons. The loadout displayed 99 tons in MW3; no PM equivalence
  claim is made for that total yet.
- Accepting the selection created an additional-chassis actor and entered a
  live Instant Action mission. Third-person captures show Atlas with its PM
  weapons in the HUD and advancing mission time through 12 simulated seconds.
  Movement/fire inputs were sent; a full motion/weapon-output comparison was
  not performed.
- The hidden-window run stopped at the requested 2,200-frame budget, exit 1
  with `Presentation frame budget reached`. It was not a normal-quit test and
  did not present through a visible swapchain. Captures came from the live
  native render target, not recorded-scene replay.

Private evidence is under
`local/work-ahead/atlas-pack-20261029-r1/`: `authoring-r3`, `built-r3`,
`import-r2`, `composed-r3`, and `native-r7` (`run.json`, `stderr.txt`,
`target-1099.png`, `target-1700.png`, `target-2199.png`). The tested pack hash is
`0c4ac605401ef8404114e57ef3732fb089b2ad8b4aaec1e49d0c5b13b6adf44c`;
native host hash is
`01b17fa52ba1f939d271a412c50c5353b2e1fcd885367549e25897dff67cb714`.
The final reproducibility run is `authoring-final`/`built-final`; its archive
hash is `0c4e7666e505d2cb11f88b247b06584193158b6b096729cf19e83126c591cfd4`.
`final-validation.json` confirms the same manifest, payloads and five composed
banks as the native test; ZIP member timestamps account for the archive change.
The host uses the existing translated module; no original executable fallback
or PM instruction-body port was introduced.

## PM behavior that still needs porting or verification

Preserve PM behavior rather than substituting a stock controller. Static
comparison and the native prototype narrow the next work to concrete gaps:

1. **Headlights.** `headlight/model_offset` is present in PM chassis definitions
   and absent from all MW3 chassis definitions. Keeping the key does not make
   MW3 implement it. PM also supplies `headlight.flt` in its mech library.
   The development adapter consumes explicit pack attachments; retaining this
   PM key alone still does not enable it. See the [headlight authoring contract](authoring-additional-mechs.md#optional-headlights-development-runtime).
   Atlas's recovered torso-local offset is `(0.96, 2.06, -2.2)`. The modern cone
   starts at that mount; PM's illumination center was 80 units forward.
   Time-based fading and immediate reversal are intentional modern behavior.
   Native toggling and fading have been demonstrated as described below;
   broader lifecycle and appearance validation remains required before
   advertising compatibility.
2. **Compiled effects and footprints.** The 33 definitions in PM
   `anim_atlas.zrd` match MW3 `anim_annihilator.zrd` after chassis-name
   normalization, but adding reader scripts does not prove registration in
   compiled operation banks. PM's five Atlas footprint objects are in
   `gamez.zbd`/`anim.zbd`, absent from MW3. Mech3AX supports PM gamez conversion
   but its compiled animation reader/writer is MW-only. Preserve Atlas's
   footprint dimensions, offsets and opacity while resolving those banks.
3. **Fidelity validation.** Compare PM and native MW3 locomotion, falls/get-up,
   muzzle origins, recoil, damage/detachment, collision, torso/arm constraints,
   cockpit, both LODs, equipment and save/reload behavior. Then cover all
   configurations, skins, texture tiers, pack disable/re-enable and stock-only
   regression. A successful mission load does not close these criteria.

Focused static PM function candidates (virtual addresses, **not RVAs**):

| Address | Observed behavior; remaining scope |
| --- | --- |
| `0x46D8D0` | Definition parser callsite finds `headlight`, passes mech field `+0x1A8` to `sub_479440` |
| `sub_479440` | Reads `light0`, `model_offset`, `lodrange`; computes range constants |
| `sub_479510` | Loads `headlight.flt`, allocates a 64-byte supporting object |
| `sub_4795C0` | Creates/names `spotlight`, initializes and offsets that object |
| `sub_479780`, `sub_4799B0` | Constructor callees; update/render closure remains unresolved |

These are LLVM 21.1.8 static observations of PM executable SHA-256
`57cd2ee74bafda3eeb9e9353c7c78a8b7c213a81f3040f1be7c2a164c505ddd9`.
The MW3 dynamic-motion lookup observations at `0x431620–0x431724` use
SHA-256 `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Function candidates are not renamed or treated as complete ports.

Keep engine support generic and capability-versioned. Pack installation must
never execute bundled code, transplant pointers between executable layouts,
or claim success for an unimplemented required PM service.

## Modern headlight development result

The reusable adapter takes the optional `headlights` array documented in the
[authoring guide](authoring-additional-mechs.md#optional-headlights-development-runtime).
The local Atlas project was rebuilt, imported through the C# pack installer and
composed through the normal content pipeline. A second authored variant adds a
left lamp at `(-0.96, 2.06, -2.2)` beside the recovered right mount; this is a
multi-lamp test, not a claim about the original Atlas equipment.

The October 29 development host (`7b634fbfc295bf908d5fd61db4ebc9a94d98824798eba70d47bba78b5269b2fe`)
reached live Instant Action and ran 2,400 frames with the unchanged translated
module. One input toggled the mounted lamp on, its intensity reached one, and
the next input faded it to zero. An otherwise identical master-off run emitted
no headlight. Captures before activation and after fade-out were pixel-identical
between those runs; while on, the difference covered the illuminated ground.
The two-lamp variant toggled both lamps together with fixture shadows enabled
and completed the same frame budget. Scenery fixture lighting was disabled.

These are hidden-window live native render-target results, not replay renders
or visible-window playtests. Visible-window attempts failed Vulkan surface setup
with result `-13`. Each successful bounded run ended at its requested frame
budget, not normal quit. Private receipts and captures are in
`local/headlights/native-hidden-r3`, `native-master-off`, `native-two-shadows`
and `paired-captures.json` in the headlight worktree.

The final reviewed host
(`247b2abdccec83f895c79593587e236bf60ee60413e47e4af4cb0fe52d658f9a`)
completed another 2,400-frame run in `local/headlights/native-final-matrix`.
Holding the key for 15 frames caused one toggle; subsequent presses reversed
the fade immediately. Both lamps survived the external-to-cockpit camera
switch. After the original shutdown sequence completed, intensity fell to zero
and an attempted on request was suppressed. Shadows remained enabled.

CPU/GPU checks cover frame-rate-independent fading at 30/60/120/240 Hz,
reversal, input edges, attachment transforms, shared light budgets, cone
shading and replay serialization. Actual launcher controls were also exercised.
Those checks do not establish live damaged-mount retirement, full LOD/offscreen
coverage, original save/load, controller hotplug, replay restoration or crowded
scene performance. These remain [playtest requirements](https://github.com/roswellien/MW3Recomp-Private/issues/115)
before capability promotion. Released runtime profiles and original game save formats remain
unchanged; no update or installer is published by this work.
