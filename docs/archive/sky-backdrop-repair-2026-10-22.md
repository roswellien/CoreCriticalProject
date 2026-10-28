# Training and Operation 1 sky backdrop correction

The reported symptoms were visible seams, stretching or broken sky shapes in
Training and Operation 1 Mission 1. No new game launch was performed.

Two concrete defects were identified in the selected host and content:

* Opaque TL draws with a positive depth inside the existing far-backdrop band
  could receive ordinary geometric surface lighting before the atmosphere pass.
  That pass already identifies the same depths as sky/horizon. Reconstructing a
  solid surface from the sky's far-depth values is inappropriate for the dome.
* The cloud catalog recognized only the two C1 sky colour identities. None of
  Training's six bank variants matched, and other operation sky identities were
  absent. The actual latest user-session bank map and cloud catalog reproduced
  the missing Training bindings; C1's two identities were already present.

`tools/remaster-launcher/native-overrides/sky_backdrop.hpp` supplies one bounded
depth predicate shared by TL lighting admission and atmosphere classification.
It accepts a nonempty, complete 32-byte TL vertex array only when every depth
is finite and within [0, 0.00025]. Ordinary and mixed-depth geometry retains
ordinary lighting. The capture check executes inside the existing preserved
host floating-point scope. Sky classification no longer depends on enabling
optional cloud relief. No shaders, UV coordinates or texture pixels changed.

An authored regression includes the actual capture adapter from the old and
corrected host. Positive far-depth backdrop vertices incorrectly receive solid
lighting before the fix; the same check passes afterward. Controls cover the
ordinary surface path, mixed depths, cloud detail off, backdrop camera capture,
empty/truncated arrays and invalid depths. These are authored fixtures, not
native gameplay acceptance evidence.

Cloud registration now covers 12 unique exact-pixel identities across all 36
environment-bank sky variants (Training, C1, C2, C3, C4 and C4b). Existing C1
cloud images are retained byte for byte. Added maps use the existing bounded
cloud-normal preparation method. The catalog is 2,360,572 bytes, below the
unchanged 16 MiB limit. It has no collisions with authored, water or surf roles.

Five environment packs are rebuilt as version **1.1.1** in
`local/asset-packs/environments-sky-repair-20261022-r1/`. Their only changed
payload is `environment/detail/cloud.bin`; archive readback verifies that all
other declared member hashes match the previous 1.1.0 packs. Original archives,
upgraded colour banks, mech resources, mission lighting, Training's selected
night preset, ambient levels and underground weather settings are retained.

Installed environment selections now refresh the coordinator's detail metadata
from their verified file table. A development cloud hash must not reject a
different independently verified pack revision. The regression verifies that
the selected resource path, size and digest agree. Empty selections retain the
existing disabled-content behavior.

The host is rebased on `gpu-native-installer-merged-r1`; only the translation-unit
helper include, TL capture adapter and shared atmosphere depth check changed,
with one added helper header. Other existing host sources, resource readers and
generated gameplay objects were retained. Reviewed exact successor admissions
allow existing mech, UI and environment content to use this correction.

The matching launcher, native profile and five installed environment packs are
updated. The existing open frontend retains its already loaded code and must
be restarted. User pack preferences, settings and original data are preserved.

Local evidence is under `local/work-ahead/skybox-repair-20261022-r1/`:
`stage.json`, `capture-check.log`, `cloud-registration.json`, `packs.log`,
`launcher-check.log`, `publication.json`, `preparation-check.log` and
`final-check.json`. The publication receipt records the exact final host hash;
an additional build places classification inside the existing host FP guard.
The pack reference host is retained through an explicit reviewed successor
admission; the original reference build and snapshot are preserved locally.

Native build, authored capture regression, coordinator/pack checks and ordinary
installed prepare-only routing pass. The prepare-only check forbids a game
process invocation. **Live visual confirmation of the reported sky seams is
still pending the user's playtest.** Strict acceptance remains **131/144**.
No commit, upload, active SQLite access or forced frontend termination occurred.
