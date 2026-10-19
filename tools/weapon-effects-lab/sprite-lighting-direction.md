# Current direction: existing sprites with dynamic lighting

User decision 2026-10-18: retain the default/existing effect sprites and textures;
park the particle replacement direction. Earlier particle previews are retained
as experiments, not approved runtime visuals. No launcher, source bank, game
host or shared lighting-engine file is changed by this direction.

## Separate lighting-only preview

`C:/Users/jcbla/MW34EffectsLab/sprite-lighting-r1/preview.html` shows identical
existing source sprites on ambient-only and locally lit receiver fixtures.
The preview defaults to currently configured texture replacements, with stock
MW3 as an optional reference. No custom particle core, Gauss cone, hot lobes,
ember shower, electrical ribbon or four-color particle palette is used.

This is an actual CPU diffuse point-light calculation over authored panel/floor
positions and geometric normals, with distance attenuation and a simple display
response. It is an isolated capability/appearance study, not live game rendering
or integration with the Vulkan lighting branch. Illumination changes the receiver
image; identical source sprite pixels are then drawn on each side. Lights are
unshadowed. Size, scalar intensity/radius mapping, source composition and timing
remain review assumptions. No native light activation credit is claimed.

The original animation definitions are useful source leads:

| Producer/reference | Observed source color | Later receiver behavior |
| --- | --- | --- |
| PPC muzzle / flight | (0.4, 0.3, 1.0) | Flash attached to actual muzzle, then an observed moving projectile light |
| PPC impact `ppc_bluelight01` | (0.2, 0.1, 1.0) | Brief blue-violet light at the actual hit |
| Gauss muzzle / flight | (0.2, 0.9, 0.2) | Retain original effect decisions; do not invent a different projectile |
| Gauss impact `gauss_light` | (0.9, 1.0, 0.9) | Source-defined pale contact light and its actual animation curve |
| Fire | Warm authored preview value | Recover the active original fire/light producer before binding |

Some definitions are inside rendering conditionals and compiled exports have
interval warnings. Definition presence does not prove the current native host
executes them or the Vulkan path illuminates receivers from them. The current
preview uses authored decay curves. In particular, it does not promote the
raw texture-cycle speed tokens to measured FPS.

## Work to connect after lighting-engine readiness

1. Recover actual light creation/update/stop boundaries from the original
   animation `LightState` / `LightAnimation` execution, including conditional
   branches. Prefer those existing producers over a new weapon-specific guessed
   flash system. Inspect the current translated host contracts before hooking.
2. Join light instance + generation to the live effect/weapon/projectile/hit
   identity and authenticated world transform. Preserve original initialization,
   simulation cadence, random calls, lifetimes, ABI/FP/LastError and source
   renderer/resource side effects. Do not infer ownership from texture names or
   brightness, and do not spawn one light per draw/camera view.
3. Convert the recovered native position/range/color semantics to the lighting
   engine's reviewed source-list interface. Do not interpret legacy range units,
   `LightAnimation` deltas or source color space by assumption. Keep host-owned
   handles, capacity outcomes, generations and mission cleanup explicit.
4. In a private integration build, first bind one original PPC impact light to
   nearby admitted terrain/armor receivers. Then add muzzle/flight, Gauss and
   fire. Leave original sprites, blend/depth/fog order and animation unchanged.
   Do not admit blended effects into opaque material lighting indiscriminately;
   luminous sprites are emitters, their surrounding geometry is the receiver.
5. Compare lighting-disabled frames with the existing baseline, then matched
   enabled frames at the same original state. Check attachment, camera/zoom,
   near clipping, destroyed limbs, resource reuse, simultaneous weapons, unload
   and normal quit. Measure bounded source counts and CPU/GPU time before
   expanding coverage. This preparation makes no production-default change.

The saved r1 source receipt binds the exact comparison asset input, keeps PNGs
byte-identical, identifies source-derived vs authored colors and records the
timing limits. All proprietary image data remains in the local output.

Recreate into a fresh output:

```powershell
python tools/weapon-effects-lab/prepare_sprite_lighting.py --reference-comparison C:/Users/jcbla/MW34EffectsLab/particles-r13/comparison.html --output C:/Users/jcbla/MW34EffectsLab/sprite-lighting-r2/preview.html
node tools/weapon-effects-lab/test_sprite_lighting.cjs C:/Users/jcbla/MW34EffectsLab/sprite-lighting-r2/preview.html
```

Offline checks execute the actual light math and controls: receiver response,
unchanged disabled images, expired-light extinction, source-bank/effect switching
and identical sprite drawing. They do not verify final browser pixels or a
native-game frame. No new native execution boundary or acceptance criterion is
closed; the verified count remains 131/144. Nothing is committed.
