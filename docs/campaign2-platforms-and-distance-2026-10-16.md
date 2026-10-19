# Campaign 1 Mission 2 platforms and display distance

The user reported that Heavy Missile Platform Bravo could be selected but its
launcher was absent while still some distance away, before Alpha was destroyed.
This happened twice through Play MW3 Remaster. The campaign save remains at
Mission 2. A missing actor and destruction of Alpha are therefore insufficient
explanations. The reported mission blocker remains open until reproduced at the
platform or resolved by a controlled distance comparison.

## Platform investigation

Original local mission data contains both platform instances, identical intact
launcher geometry and separate destruction activations. Mission 2's Baker
objective requires both instances to be destroyed. The instances are about
433 units apart. Original media, decoded game data and addresses remain in
`local/campaign2-platform-investigation-r1/mission-data/`; they are not included
in public source.

An ordinary private copy of the current pilot/save loads Mission 2 and creates
both actors. Both register with the objective lookup, remain active, and have
active healthy, turret, gun and missile-model branches. Their local turret/gun
matrices are finite and equivalent before engaging the player. These observations
do not prove visibility at the user's later gameplay position. The scripted
campaign walk remained far from the platforms and encountered coastal terrain;
it did not reproduce a missing nearby launcher or complete the objective.

The original heavy-platform missile has a 1340-unit range and the turret inherits
that detection range. Ordinary LRMs use 800 units. Both live platform actors
retain the authored 1340-unit range. Thus firing beyond an 800-unit display
distance is possible without a weapon-range regression. No accepted platform
shot was observed in the distant private campaign walk, so the reported extreme
shot distance has not been measured. No AI, weapon, objective or save-state
changes were made.

Private opt-in tracing distinguishes range eligibility from an accepted
projectile, records both actor/part states, and preserves the guest FP state
around observation. Missing geometry at distance remains consistent with camera
admission, but this is a hypothesis rather than a confirmed root cause.

Follow-up playtesting after publishing 1200/1100: the user directly observed
Bravo visible for a minute, then disappearing as they moved closer. This makes
the simple far-distance cutoff explanation insufficient. The investigation now
tracks the first aim update, transform invalidation, bounds/visibility decisions,
mesh production and actor retirement together. The private diagnostic build is
separate from both published launchers. No fix for that transition is claimed.

The user further clarified that Bravo remained selectable, its targeting preview
was empty, and weapons did not hit it. They did not test backing away. The
approximately 20 m distance refers to Alpha, which remained visible throughout,
not to Bravo. If both observations apply at that position, the original 433 m
platform separation puts Bravo roughly 413–453 m away, well inside either draw
distance. This strengthens a branch-state/transform hypothesis; it does not prove
that collision was disabled. No backing-away/reappearance behavior is established.

The additional asset inspection finds single intact meshes, with no platform
LOD/switch nodes. A private input controller followed a route derived from the
original terrain and emitted ordinary replay keyboard events only; it did not
write positions, health, objectives, clocks or save state. Its `bravo-navigation-baker`
run reached approximately 338 m from Alpha and 774 m from Bravo before terrain
blocked further progress. Bravo's three intact meshes reached the original mesh
producer at every recorded 60-frame sample from 3060 through 5160. No retirement,
invalid transform or sampled disappearance was reproduced there. These are
producer observations, not proof of final visible pixels through the terrain.

The focused capture host records active hierarchy state, local/world matrices,
bounds, original clipping decisions, mesh production, aiming and actor retirement.
It scopes observations with full hardware FP save/restore, calls original bodies
once, and retains existing model override handling. Observations are sampled or
logged on state changes; this is diagnostic instrumentation, not a performance
benchmark. Tracking resets on a new turret load so restarted missions cannot
reuse stale actor identities. Independent review checked routing and found two
diagnostic exception-scope gaps; both initial observer calls now run inside their
restoration guards. The capture host contains no navigation controller.

The normal launcher's optional `native.platform_visibility_trace` switch places
the trace in each fresh run directory as `platform-visibility.txt` and records its
path in `run.json`. This permits the next ordinary-play disappearance to be
correlated with the actual actor and renderer transition. The disappearance is
still an unresolved gameplay defect; instrumentation is not its fix.

The normal profile now selects the completed capture host. Trace-enabled stock
Training matches all 116 previous baseline captures, and a 1150-frame private
Mission 2 load records both platforms. The launcher profile/hash check passes.
The alpha profile retains its previous 1200/1100 build. Exact capture build and
scope are recorded in `local/campaign2-platform-investigation-r1/bravo-capture-validation.json`.
The prior normal profile is backed up before this switch. No automated navigation
is included in the capture host, and no test game is left running.

Protection checks for this follow-up use the pilot hash recorded before its
first private run. The user's preceding play had already changed the pilot file
from the earlier investigation baseline; all follow-up runs preserve that newer
pilot and the unchanged Mission 2 campaign save. The earlier baseline remains
intact as historical evidence rather than being overwritten.

The latest ordinary play also ended with a guest-memory fault in an original UI
chassis/configuration-list refresh. No connection to Bravo has been established;
that failure is retained separately rather than treated as a rendering diagnosis.

## Short-frame turret aiming defect (candidate cause)

The user confirmed that no player weapon had been fired before Bravo disappeared.
This excludes player-inflicted damage as the trigger in that observation. Original
aiming code contains a separate, concrete short-frame defect: its exponential
smoothing lookup truncates `51 * (3 * dt)` to a table index. Below approximately
6.536 ms (153 FPS), the first bucket returns exactly one, leaving an initially
vertical filtered direction unchanged. The subsequent horizontal-normalization
shortcut can then publish a finite but singular turret yaw matrix. The alternate
`8 * dt` branch has the corresponding threshold near 408 FPS. Zero delta also
needs protection. These thresholds describe engine update deltas, not necessarily
the displayed or average renderer FPS.

The user's last recorded run contains 133 of 10,636 sampled 3D presentation
intervals below 6.536 ms, but presentation timing is not a capture of the original
aim delta. Neither this count nor source analysis proves the cause of Bravo's
reported disappearance. Actual transition capture remains necessary.

An optional private correction runs the original lookup first, retaining its
initialization and ABI effects, then interpolates only the first positive input
interval when its original return is exactly one. At zero delta it restores only
the four collapsed yaw words from a valid previous orientation, before the
original transform publication/invalidation routine. Actor, node, matrix and call
site authentication restrict both changes to the original turret aiming scope.
The ordinary 30/60/120 FPS lookup buckets remain unchanged. This intentionally
corrects short-frame behavior; it does not claim original-equivalent results there.

The pure math fixture and the fixture including the actual authored adapter pass.
The latter checks disabled/enabled/observation-only modes, exact ten-byte x87
payload replacement, original callback ordering, register/stack/state preservation,
four-word restoration before commit, rejected contexts, nested/exception scope
restoration, FP environment and LastError preservation. Original bodies in that
fixture are mocked; it is not a gameplay reproduction. The compiled private
candidate completes 1150 Training frames at stock 800/0 and matches all 116
baseline captures with the correction enabled.

The subsequent native comparison reproduces this defect in the original aiming
body, rather than only in a mocked fixture. Both private runs use the same
ordinary keyboard navigation route, original Mission 2 load, 1200/1100 distances,
3440-wide FXAA/AF16 profile and assets. A private test host advances its existing
scripted clock at 50 ms through presentation 2800, then 6 ms per presentation.
This changes test timing without writing actor transforms, damage or objectives.
Both runs complete their 5200-frame budgets. Alpha's first collapsed publication
is at frame 2809. Without repair, all 240 recorded lookup/publication pairs
collapse the yaw; all 40 subsequent periodic yaw samples have determinant zero.
With repair, all 240 first-interval lookups are corrected, no collapsed yaw is
published, and all 40 sampled yaw determinants are one. Neither run records actor
retirement or an accepted platform shot. Bravo's particular reported transition
is still not reproduced; the tested defect is shared original turret code.

The normal launcher now selects the completed correction host
`local/remaster/gpu-native-turret-aim-r1/build/entry_commandline.exe`, SHA-256
`a7454e3e8ff168f037bd6d49001f47bada8bd425202c738710fc462616bf7f5f`.
Its full-profile private Mission 2 load completes 1150 frames. This published
host contains neither the navigation controller nor the test clock change;
its translated object list matches the preceding capture host byte-for-byte.
`MW34_TURRET_AIM_REPAIR=1` enables the scoped correction, with per-run
`turret-aim.txt` alongside the existing platform trace. Launcher hash/profile
validation passes; the previous normal profile is backed up as
`launcher.before-turret-aim-20261016.json`. Alpha retains its prior build.
Protected original pilot/registry/campaign-save hashes still match the follow-up
baseline. This advances the native short-frame aiming/transform-publication
boundary. Bravo's disappearance, weapon-hit behavior and mission completion need
ordinary-play confirmation; acceptance remains 131/144 and no commit was made.

## Requested display changes

The new configuration uses a 1200-unit scenery far plane and a 1100-unit linear
fog endpoint. Both the main view and the authenticated original zoom camera
receive the distance extension. Target-marker preparation also authenticates the
zoom owner before its later scene draw. Original target choice, sensor/lock
rules, weapon range, near clipping, FOV and range-text calculations remain intact;
there is no justified hardcoded 800-unit marker/text limit to replace in the
inspected projection path.

Live testing exposed a camera ownership mistake: the global gameplay camera
context deliberately remains the main camera while the original zoom context
draws its own camera. Requiring that global context to equal the zoom camera
silently rejected the extension. The repair authenticates the exact zoom owner,
its camera node, camera/view classes, name and bounded viewport. Renderer binding
selects this camera only when its data matches the incoming binding; original
main-camera restoration inside the zoom scope remains valid.

Fog is applied after original world weather setup at renderer camera binding,
covering cached cameras as well as frustum rebuilds. The override retains the
authored near/far ratio, mode, enable, color, altitude taper and density. Main
C1 fog becomes approximately 46.93–1100; the original zoom-specific ramp becomes
573.47–1100. Six distance-fog fields and nested scope flags restore on normal and
exceptional exits. Implicit legacy fog retains its previous once-per-scope
scaling. Disabled/nonlinear fog and unrelated preview/Lab cameras are preserved.
Original altitude taper means elevated terrain need not become fully obscured
at the radial endpoint. Replacement-model fog remains a separate known gap.

## Validation and boundary

Asset-free tests include the actual authored helper and pass at 1200/1100,
stock 800/0 and legacy 1600/0. They cover main and zoom ownership with the global
context still main, marker preparation, cached renderer binding, invalid owners,
preview rejection and nested normal/exception restoration. An independent source
review found no blocking defect after restoring the legacy nested-scaling guard.

Private live runs include `mission2-aim-route-repeat` (2200 presented frames) and
`alpha-ia-platforms-range1200` (1000 frames, GPU world and fast binding, CPU
projection bypass disabled). Both log main and zoom far planes of 1200 and actual
original fog-consumer endpoints of 1100. Runs terminate at their requested frame
budget; this is not a full mission-completion result. These diagnostic runs are
not performance benchmarks. The final normal build also completes a 650-frame
cockpit IA run: capture 420 displays a selected target at 803 m and its main-view
marker. A distant selected target inside the magnified window remains unverified.

The final normal build's stock 800/0 Training run matches all 116 captures from
the previous fog-fixed baseline. Both public launcher profiles now select their
new completed builds with draw 1200 and fog 1100; profile checks verify both
executable hashes and supported settings. The prior profiles were backed up.
Exact local source/build identities are in
`local/campaign2-platform-investigation-r1/published-build-identities.json`.

The execution boundary advanced is native main/zoom scene presentation with
independent draw/fog distances. Gameplay and campaign completion are not newly
credited. Acceptance remains 131/144. Original pilot/save files are protected by
hash checks; all gameplay tests use private copies. Lighting/shadow/normal-mapping
work remains held. No commit was requested or made.
