# Terrain and sky classification repair

The user confirmed that the sky repair resolved the skyboxes, then reported
severe terrain pop-in. The latest ordinary play session selected C1M1 with
1600-unit scenery distance and 1100-unit fog. No additional game was launched.

The preceding sky correction excluded every opaque TL draw whose vertices
occupied the far reversed-depth band from solid-surface lighting. Distant
terrain can occupy that same band. It consequently lost its lighting binding
and became eligible for the atmosphere pass's sky routing at a depth threshold.
This is a concrete rendering regression; the report's live appearance remains
to be checked after correction.

The successor retains exact-pixel sky registrations and excludes registered
sky surfaces from ordinary lighting without relying on the animation toggle.
Atmosphere sky admission now requires a registered sky role, an untextured
backdrop without depth writes, or an untextured zero-depth horizon. Distance
alone does not identify sky. Ordinary distant solid terrain retains its normal
lighting and fog path. Camera draw distance, terrain submission, gameplay,
texture packs and mission lighting are unchanged.

The actual capture-adapter regression fails on the preceding build and passes
on the successor for solid terrain on both sides of the former cutoff. It also
checks sky registration, cloud toggle handling when registered, horizon cases
and invalid inputs. Native build, launcher checks, and installed HUD/menu
binding checks pass. Evidence and exact publication hashes are under
`local/work-ahead/terrain-popin-repair-20261022-r1/`.

The local native profile and self-contained launcher are updated. Packs were
not reinstalled or removed. No game launch, commit, acceptance increase, or
interruption of other processes occurred. Strict acceptance remains 131/144.
Live visual confirmation is pending the user's playtest.
