# Fog rendering investigation

The user's missing scenery fog was reproduced with the actual launcher
settings. A narrowly scoped device/cache repair restores the original fog
initialization. Both launchers retain stock800-unit scenery distance.

## Cause and repair

The old private test baseline selects original display mode5 (640x480), while
the user's settings select mode7 (1024x768). Modern output remains3440x1440.
The latter requires a graphics-device recreation when leaving the menu.
Registry comparison found this was the only settings value differing between
the two controlled cases. Earlier fog-positive mode5 tests therefore missed
the user's actual failure. Height-limited fog was not the cause of this failure.

The original fog setter at VA57BB70 compares a request against cached8093B0.
The first device is initialized with fog enabled and leaves that cache equal1.
The new device starts with Direct3D's actual FOGENABLE default0. Original
device initialization calls57BB70(1) again, but its stale cache suppresses the
actual SetRenderState call. World weather remains enabled while every sampled
terrain command on the replacement device has fog disabled.

The retained native trace proves the lifecycle:

```text
frame0: create640x480, cache0; original SetFog1
frame281: create1024x768, cache1; first draw device fog0/cache1
```

`apply_device_fog.py` adds opt-in `MW34_DEVICE_FOG_REBIND=1`. At successful
original HAL creation only (output809370, return57AA9E), it synchronizes the
original fog cache to the new device's actual fog state. Original initialization
then performs the enable request itself. The renderer does not force fog on,
alter world weather or override later fog-off requests. Missing/0 disables the
repair; invalid flag values and unknown boolean states fail visibly. Other
render-state caches are outside this proven repair.

The boundary advanced is original renderer state continuity across native
graphics-device recreation. The two new hosts preserve their respective
translated object lists and change only the provider hook, include and authored
helper. An independent original-disassembly/source review found no blocker.

## Direct renderer checks

The new authored `tools/remaster-launcher/test_vertex_fog.cpp` fixture renders
untextured red triangles against blue fog and checks actual Vulkan RGB565
readback. It verifies full, partial and zero vertex fog, plus fog disabled,
with specular lighting disabled. This catches dependence on the specular-enable
flag even though fog visibility occupies the original specular alpha byte.

The fixture passes against both selected host snapshots on the RX9070. With
`MW34_TEST_WORLD_FOG=1`, it also passes three raw GPU scenery draws using
separate original TL fog attributes and deliberately invalid TL screen
positions. Thus the alpha scenery shader can apply the original fog values.
These are renderer fixtures, not native-game acceptance evidence.

## Live stock-distance checks

Two private1000-frame IA runs use each launcher's selected executable,
3440x1440, FXAA, AF16, the existing model assets, stock800distance and the same
retained movement/yaw input. The alpha run additionally enables GPU scenery
and fast binding, with original CPU projection bypass disabled.

Both old-baseline runs reach their requested frame budget. At frame900, the original world fog
is enabled, linear, range32..750. The original TL terrain contains fog
visibility values spanning0..255. Inspected target captures show pale haze
on low distant terrain and buildings. This is direct image evidence in this
controlled scene; these old-baseline runs did not reproduce the user's settings.

Repeating with actual mode7 settings reproduces no terrain fog. After the
repair, the normal and alpha hosts each complete1000frames with visible haze
in matched captures600/900. Every original draw count/hash record matches the
unfixed mode7 control. The intentional image difference is the restored fog.
At900, all430 main terrain batches now enable fog, with original visibility
values0..255. The alpha test retains GPU scenery/fast binding and keeps the
experimental original CPU projection bypass disabled.

The normal fixed host also completes a real-clock1800-frame Campaign1 run
with original codec decoding and ordinary UI input, entering3D at frame800.
At1400,1320 main scenery batches enable fog with original visibility0..255.
A focused1150-frame original-compatible Training check matches all116 retained
framebuffer captures. An initial hidden-window attempt stayed in the menu and
is retained as an invalid gameplay control, not a rendering regression; its
parent-host repeat and the focused fixed run match the retained baseline.

Both launcher profiles now select their respective fixed hosts and explicitly
enable `MW34_DEVICE_FOG_REBIND=1`. Their launcher checks pass. No shared pilot
or registry contents were edited; tests used protected private copies.

The original game uses height-limited fog. Recovered `sub_555A70` combines
camera X/Z radial distance with an altitude plane derived from the original
camera matrix. The inspected IA1–3 and Mission1 world definitions use the
hardware range32..750, altitude band80..100, and gray fog RGB approximately
0.8157. Below80, the radial fog factor applies fully; between80and100 it
tapers; at/above100 the original routine returns no fog. Clear high terrain
therefore does not by itself prove a missing Vulkan fog blend. The affected
mountains' actual engine heights have not been established.

## Separate replacement-model defect

Source inspection found that `model_scene.vert` emits constant specular alpha1,
and the CPU replacement-model path emits `0xFF000000` specular values. Since
the fragment shader blends by that alpha, replacement mechs receive no fog
even when fog is enabled. Original TL scenery and raw GPU scenery have a
different attribute path and do not share this constant.

A faithful model correction must supply the original radial/altitude contract
to both GPU models and their CPU near-plane fallback. Do not replace it with
an assumed projected-depth fog equation or alter original scene weather to
hide the defect. This fix remains open; it is not established as the cause
of the user's missing scenery fog.

## Evidence and remaining work

Selected normal executable SHA256:
`ed568b419c2ac0b465950016bf9be3cb0e2f988d73bae01c76e183ee12ec41df`.
Selected alpha executable SHA256:
`e905a738bd4460492e09cfc0209594a1bc8f86a48455f49e33a4b0e248ca127c`.
These identify the pre-repair controls. Published normal fixed executable:
`866d6c7ce7e4aa566f9c06fa2b44afaaeb421591f58a44946830476121aba908`.
Published alpha fixed executable:
`7e31ec1df6e1911ece99778360f62fabf0fb9ebf4ce46ba0aea25978b789cd9d`.
Original image SHA256:
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Function addresses above are original VAs, image base0x400000.

Private fixture build/run logs and hashes are in
`local/fog-render-investigation-r1/results.json`. Live runs are retained under
`local/gpu-projection-bypass-r1/runs/fog-stock-normal` and `fog-stock-alpha`.
Original binary analysis is retained in
`local/terrain-distance-investigation-r1/rea-evidence.json`; original media
and generated code remain local.

Private fixed build identities are in
`local/fog-render-investigation-r1/build-identities.json`; recreated-device
traces, actual-settings baseline and fixed IA runs share that directory.
The before/after image is `fog-before-after-900.png` there.
Correct the replacement-model fog contract separately and verify GPU/CPU
fallback agreement. No new performance or strict acceptance claim is made.
