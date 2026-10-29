# MW3 runtime 1.0.42 lighting correction

The cumulative 1.0.42 runtime builds on the published 1.0.41 mech and skin
update. Dynamic Lighting now enables the native host's authored campaign sky,
sun, ambient, and weather settings even when an installed environment pack has
no mission metadata. When Dynamic Lighting is off, the launch coordinator does
not apply an environment pack's sun or night preset; the renderer receives
`MW34_SUN=0` and uses the original MW3 lighting path.

Only three coordinator files changed relative to the published 1.0.41 runtime:
`presentation_policy.py`, `play_native.ps1`, and `play_remaster.py`. The normal
map texture correction from 1.0.40 and the native host from 1.0.41 remain.

Verification: 19 focused Python tests passed. The launcher validated all files
and startup inputs in the staged runtime. LauncherChecks 1.0.42 verified the
signed `1.0.42.mw3update`, installed its matching ZIP against original game
inputs in an isolated store, activated and validated it, then rolled back.
The 1.0.42 metadata, payload, and private download wrapper were uploaded to
R2 and read back by hash. The public update endpoint passed full and Range
reads. The private download pages were updated, and signed catalog sequence
2026102511 was promoted last and read back publicly.

The Dynamic Lighting off profile was launched on the DEV AMD GPU with the
legacy night preset still present in the profile. Its effective flags retained
`MW34_SUN=0` and no preset was applied. An isolated C1M1 image capture did not
reach gameplay because the original opening and mission movies consumed the
frame budget; removing all movies triggered the game's CD check. Visual
comparison of the off state on the Intel test laptop remains open.

Local staged release: `D:\CoreCriticalSkyRegression-20261025-r1\Release-r4`.
Original game media and generated game code were not placed in the update.
No repository commit was made.
