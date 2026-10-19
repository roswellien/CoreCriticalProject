# Announcement trailer capture plan

The requested deliverable is a reviewable collection of real in-game screenshots
and footage for the project announcement and website. Capture environments,
combat, replacement mechs, the detailed original Strider, upgraded textures,
normal mapping, sun/sky/ambient lighting and supported sun shadows. Keep feature
claims tied to the actual settings and visible content of each take.

## Capture groups

| Group | Subject | Intended use |
| --- | --- | --- |
| Environment | Campaign shoreline, water, industrial structures and vegetation | Opening vistas and website backgrounds |
| Mech showcase | Mad Cat, Bushwacker and detailed original MW3 Strider | Close detail, silhouette and orbit views |
| Action | Native movement, weapons, impacts and destruction | Main announcement action montage |
| Lighting/materials | Low-angle sun, shadows, surface relief and changing sky palettes | Feature inserts and explanatory captions |

Retain native ultrawide masters and prepare 16:9 editorial crops without
stretching. Preserve capture metadata and camera settings. Gameplay clips keep
their gameplay identity; paused photo-mode orbits must be identified as camera
showcases rather than live combat. The existing video recorder produces silent
footage, suitable for b-roll; sound design and music are a later editing pass.

Use the validated current preview as the source. Private capture automation may
drive existing hotkeys and the host photo camera; it must not alter gameplay,
model geometry or material rendering. Preserve the playable executable/profile.
Recording overhead must not be presented as a performance baseline.

## Selection and quality checks

- Use the clean capture path. Exclude HUD-hidden notifications, recording status,
  legends, menus, loading screens and unrelated desktop content from website
  stills and cinematic selects. Wait for temporary messages before still capture.
- Inspect every selected still and representative beginning/middle/end video
  frames for colors, framing, texture stretching, water composition and overlays.
- Check decoded dimensions, duration, frame count and complete encoding.
- Record actual environment, chassis, preset, shadow settings, source build,
  camera mode and whether the shot is live gameplay or paused photo mode.
- Separate technical proof captures and failed attempts from the editorial
  selects. Do not imply incomplete or planned lighting features already exist.

## Delivery

Store source media and reports locally on the Games-drive archive. Upload only
review selects and a shot list to the user's private Google Drive review folder.
Prepare a suggested shot order for later announcement editing. Do not add original
game assets or generated game code to source control. Website publication and a
finished announcement edit are separate from preparing this capture collection.

Formal acceptance remains 131/144; capture success does not grant game-function
acceptance credit.

## Capture review corrections

The initial technical proof images displayed photo-mode status text, including
HUD-hidden and 60 FPS recording messages. They are excluded from editorial
selects. Selected stills use the native clean PNG path; selected video frames
are read before the photo-mode overlay. Inspect the actual exported media,
not the diagnostic presentation dump, before uploading.

The first Strider framing clipped antennas and is excluded. The first live-action
attempt was rejected before gameplay because scripted events were out of order;
the corrected run reached its presentation budget and recorded movement and
laser fire. Do not describe that short firing pass as a sustained enemy battle.

An Operation 2 saved-pilot probe stopped before gameplay with an invalid guest
file handle. Copying the corresponding configuration files did not resolve it.
It remains a separate investigation, with no later-operation footage claimed.

## First reviewed collection

Prepared five selected PNGs and six H.264 clips: Mad Cat and detailed original
MW3 Strider sunrise orbits, Bushwacker campaign coast orbit, campaign coastal
sunset glide, dockside midday glide, and live cockpit movement/laser firing.
Each clip has 720 frames at 60 FPS, lasts 12 seconds and is silent. All six exports
fully decode without errors. Reviewed opening, middle and closing frames contain
no photo-mode status messages. Original unit selection rings remain in IA model
shots. Environment clips begin with the mech in the foreground before gliding out.

Stills and cinematic clips are centered 2560 by 1440 crops of 3440 by 1440 masters.
The live firing clip instead uses proportional scaling and letterboxing to retain
the entire gameplay HUD. These controlled-clock captures are not benchmarks.
The existing sun-shadow feature is enabled; material strengths and the installed
preview executable/profile are unchanged. Private capture source adds hotkey and
camera automation plus failed-file diagnostics, without changing rendering.

Private review folder: https://drive.google.com/drive/folders/1Qf3TuSQHrMKx3oDCNgZ4i8ggtSDaWuly

Local selects, manifest, shot list, QA frame sheet and readme are under
`reports/announcement-captures-20261019/selects` on the Games-drive report junction.
The shot list proposes coast, Mad Cat, Strider, docks, firing pass, Bushwacker.
Audio, sustained combat coverage, later environments and the final trailer edit
remain future work. Nothing has been publicly published or committed.

## Mech gallery: revised framing and lighting direction

The user rejected the first gallery's fixed-world side/rear camera framing.
That Drive folder is labelled superseded. The replacement collection must use
15 degrees off the mech's front, 100 degrees from its front, and a head-on
view looking down from above. These are measured from the actual player's
world orientation, not a common world azimuth across map spawns.

A private capture-only camera addition reads the player's root matrix and
places the Orbit camera relative to its facing. Mad Cat calibration visually
confirms front and side identity; elevated head-on uses 27 degrees downward
viewing elevation. It changes camera state only and fails if the player root,
world matrix or Orbit target is missing. The installed playable build is unchanged.

The replacement queue covers all 15 upgraded chassis, with three images per
chassis across two IA maps. All four IA maps are used across the collection.
Front/side pairs alternate sunrise and sunset between chassis; elevated shots
use midday on the other map. Native sun azimuth 45 and ambient 0.4 are capture
overrides, with unchanged normal strengths and existing sun shadows enabled.
These are selected lighting presets for photography, not evidence of continuous
campaign time progression or new local lights. Shot metadata retains the exact
applied lighting values and native input route.

Replacement review folder: https://drive.google.com/drive/folders/1jwO2_iNAH4mKdKMZ5_5LU0KVnQuLG2zR

Local replacement exports and provenance: `reports/mech-gallery-facing-20261019`.
Do not mix the superseded side/rear set into the final front/side/elevated gallery.

## Completed material-preview gallery and arm corrections

All 15 chassis now have three reviewed PNGs in the replacement Drive folder:
45 images, verified by reading back each chassis folder. Orion and Annihilator
initially exposed real upward-pointing forearm defects. Separate corrected
close/distance assets are registered in both the material-preview and main model
registries. Corrected native front/side views and movement checks retain forward
weapons. Orion's Drive files were replaced in place; both hold labels are removed.
Full combat/damage and exact visual muzzle-origin fitting remain open.

This collection records the material-preview bindings used during capture.
The concurrent Mad Cat/Bushwacker/Vulture joint-fitting lane has newer revisions
and a newer host; refresh those three sets after that lane settles before calling
this gallery a showcase of every latest main-launcher joint correction.
Technical record: `docs/orion-annihilator-arm-alignment-2026-10-19.md`.
Private review metadata and Drive readback are retained with the local exports.

## Walking-and-firing orbit continuation; Mad Cat held

The user subsequently put Mad Cat on hold while its model work continues. No
new Mad Cat capture was made. Its prior folder is clearly labelled HOLD, and
both active indexes exclude its older images.

The review collection now has 42 active screenshots and 14 native walking/
firing orbit clips, with all four IA environments and sunrise/sunset presets.
Thirty images were refreshed, including all three Vulture and Bushwacker views
using the current joint-fit assets; elevated shots retain midday on second maps.
Eleven clips run 12 seconds. Bushwacker, Thor and Black Hawk have eight-second
action selections to avoid closing camera views obscured by nearby building fire.
Selected video totals 156 seconds, silent 2560x1440 at 60 FPS output. These are
controlled-clock capture runs, not real-time benchmarks.

All clips were fully decoded and visually reviewed around orbit/firing windows.
Drive readback checks three PNGs and one MP4 per active chassis, with matching
names and byte sizes. Existing image IDs were preserved. Local source/payload
hashes, input routes, exact lighting and the final indexes remain with the media.
See `docs/mech-orbit-captures-2026-10-19.md` for the private-host boundary and
Mad Cat's newer format requirement before it can be photographed again.
