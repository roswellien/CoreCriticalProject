# Development summary â€” 2026-10-20


## 2026-10-20 â€” Default mech texture pass

Audited all18default sets; revised Daishi, ShadowCat, Avatar, Strider, Owens
and Firefly, retaining twelve already detailed/worn sets. Reconstructed crisp
panel/metal wear with calmer broad armor, original palettes/markings. Both
model registries and original banks installed;34color sidecars/profile checked
against every source pixel and batch index. Existing2main/32normal sidecars
unchanged;149selected bank entries changed,5497others exact.46newcolor keys
preserve existing native normal tuples; six stale Campaign1 manifest paths
aligned with already active object banks. Host/graphics/mesh/skinfields retained.
User explicitly kept main fullscreen_windowed despite its existing capability
mismatch; normalpreview preparation passes, main preparation verified directly.
No game/desktopcapture/pilotregistrywrite/commit;131/144strictpaused.
Owens/Firefly detailedgeometry remains offline. Beforeafterreviews/notes on
Drive; see [texture pass](default-mech-texture-pass-2026-10-20.md) for sources,
resolution limits, validation and remaining native visual checks.


## 2026-10-20 â€” All 18 models in the main Remaster

Integrated detailed Owens and Firefly into the current main HUD damage-colour/
lighting/window host. Main and GUI now resolve18chassis with the current default
textures and normal registry. Host ba86eac90b based on85a9a59eef; only exact new
rosters/table entries/arm-loss metadata differ, translated objects unchanged.
Owens21,170tri/16parts/42materials; Firefly23,688tri/21parts/53materials,
336bindings below0.000002matrixerror, source body UVs retained and56latestcolor
files byte-identical. Both distances currently retain full geometry. Adapter
7782checks/0failures; original Training116/116, GPU1150/1150, IA116/116 match.
NativeIA2000frames each with geometry/normals loaded. Main/GUI/normal preparation
passes18models,38color/36normal sidecars; original-model option retained. All
previous16records, graphics and runtimeenv preserved. GUI pack description now18.
No original registry/pilot writes or commit; strict131/144paused. NPCdistance,
damage/debris, precise muzzles, extended campaign/FPS remain. See
[all18 integration](all18-mechs-main-integration-2026-10-20.md).


## Launcher, input and campaign regression repairs

The launcher repairs retain ultrawide resolution, borderless/exclusive window
choices and 2x/4x SSAA. Updated model selection reaches native asset preparation;
normal catalog capacity is bounded at 512 MiB while individual pages retain their
256 MiB limit. F12 passes through to the original mission-objective input.
Original condition-schematic ownership preserves red per-component damage tint
in both status panels without bypassing world fog elsewhere.

The Operation 2 file-read error path now reports the real Windows failure for an
invalid handle instead of aborting the host. The user subsequently confirmed the
Operation 1 -> Operation 2 campaign transition in their playthrough. This closes
that reported case, not every campaign load or long-session stability concern.

## Depth precision and launcher dependency follow-up

The [D32 upgrade record](depth32-renderer-upgrade-2026-10-20.md) documents the
actual Strider geometry stress test, compatible guest-depth transfers, resident
precision, odd/scaled dimensions, SSAA, HUD and native Instant Action checks.
The main launcher selects the validated all-18-model D32 host. Stress-test
improvement is not a claim that every gameplay flicker has been eliminated.

A later GUI launch failed importing Pillow before the game started. Its runtime
selector had checked only the Python executable's existence. The repaired GUI
prefers the existing bundled runtime and probes Python version plus an actual
Pillow image operation in the launch environment. The regression rejects a Python
installation without user packages and successfully selects the bundled runtime.
Full native preparation using the failed launch's settings then passed for all
18 models and 39 banks. No game session was started by that preparation test.
Local evidence and previous launcher backups: local/launcher-runtime-repair-r1.

## Gemini campaign environment and editing work

The public note credits Gemini's campaign environment implementation and early
map/mission editing work. The [R7 repair](world-lighting-repair-2026-10-20.md)
records corrected behavior and measured costs rather than retaining the initial
all-weather and negligible-cost claims. The [light audit](texture-light-audit-2026-10-20.md)
and [placement drafts](reviewed-light-placements-2026-10-20.md) distinguish review
choices from live integrated lights.

The editor source provides a top-down editing slice, browser 3D preview, project
serialization and isolated pack export. This is prototype tooling, not accepted
custom-mission gameplay. Extracted original preview geometry is excluded from Git;
the locally bundled Three.js r128 source retains its MIT license and upstream
hashes. Authored source, notices and the example project can be reviewed without
publishing original game archives or derived geometry.

Formal acceptance remains 131/144. No original media, generated game code,
compiled launcher/game binaries or local preferences belong in the source commit.
