# Full-size texture storage repair

The cause and controlled failing baseline are recorded in
[the dev/fresh texture investigation](c1m1-fresh-versus-dev-texture-selection-2026-10-23.md).
The original renderer creates a system-memory texture and a rendering texture.
The native provider previously kept both sets permanently in its approximately
2 GiB guest surface arena. A saved dev setting selected a smaller bank and
concealed the full-bank failure. This is a provider allocation defect, not a
different arena limit imposed by the remote computer.

## Implementation

Unlocked texture pixels now live in host-owned storage. `Texture2::Load` shares
identical backing with copy-on-write isolation: subsequent changes to either
surface preserve the other's pixels. A texture Lock maps a checked guest view;
the last Unlock copies its resulting pixels back and unmaps/recycles that view.
Render targets, flip chains, z-buffers and ordinary offscreen surfaces retain
their existing guest allocation and lazy GPU synchronization behavior.

Provider blits/fills, renderer uploads, normal/effect image hashes and texture
warmup all read the same authoritative backing. Guest addresses remain 32-bit;
host pointers never enter guest descriptors. Surface identity, pixel format,
pitch, dimensions and content versions remain independent of backing ownership.
Released surfaces are periodically collected while honoring COM identities,
attached surfaces, device bindings and queued draw references.

This removes the fixed arena ceiling on the aggregate of unlocked textures.
It does not make physical RAM or Vulkan memory unlimited. Simultaneously locked
views must still fit safe guest ranges. No texture dimensions or pixels were
reduced, and no original game logic, bank-selection logic or simulation timing
was replaced.

The maintained implementation is in `tools/remaster-launcher/native-overrides/`.
`apply_host_texture_storage.py` applies narrow edits to an older frozen host
after its surface-page-pool prerequisite, preserving newer renderer work. A
future native build must retain this integration; rebuilding from an older
private source snapshot without it reintroduces the crash.

## Executed checks

The private candidate starts from the published performance r6 source: eight
existing host files change and one backing header is added. The translated game
module is unchanged. Native compilation and linking succeed.

* C1M1 with the absent/fresh texture-memory setting now reaches 1,500 Vulkan
  frames, 454,175 logical draws and 211,185 GPU draws. The prior exact public
  host failed before 3D submission at arena cursor `0xef93c000` on this same PC.
* C1M1 with the old saved setting also reaches 1,500 Vulkan frames. Both candidate
  and r6 baseline emit 456,648 logical draws and 210,388 GPU draws. Four of six
  frame captures match exactly, including frame 1,500. Frame 1,200 differs in
  484/786,432 pixels, mean RGB error below 0.002/255; the menu animation capture
  also differs. This is not a claim of complete pixel determinism.
* Authored C++ checks cover zero initialization, independent writes after shared
  texture Load, lifetime after source release, checked transfer bounds and
  recycling one guest view across 4 GiB of cumulative lock allocations.
* All five prepared-environment pack tests pass, including enabling effect
  lights when a selected pack supplies their verified catalog.
* The full installed selection exposed a second defect: the shared bank's
  `stump_damage02` record is at unsigned offset `0x94293c88`. The known MW3
  table-loader return is present, but the original adapter also required a CRT
  internal return absent from that call chain. Its normal negative-seek failure
  left the reader at an incorrect record. The adapter now identifies this
  operation by replacement-handle ownership, exact MW3 loader return, absolute
  origin, no explicit high word and a high-bit offset. Other signed/relative
  seeks retain their original behavior. All 36 authored seek/sparse-file checks
  pass, including the caller without that incidental CRT frame.
* With that correction, the complete selected pack map (38 banks including
  shared mechs), installed mech/HUD/menu assets and enabled effect-light
  catalog reach 1,500 C1M1 Vulkan frames: 456,648 logical draws and 211,437 GPU
  draws. Offsets `0x94293c88`, `0x94291c78` and `0xba590208` seek successfully;
  the effect catalog registers 1,067 full-content material keys. An intermediate
  hidden-window attempt paused during startup and was terminated by its owner;
  it is retained separately and does not count as a successful test.

## Dev selection

The dev shortcut still starts `Core Critical Launcher.exe`. Its next launch
reads the updated `local/remaster/launcher.json`, selecting the repaired,
timestamp-signed native host and the same installed pack roots selected under
Mods & Packs: six environment packs, two mech packs, HUD, menu and soundtrack.
The composed environment uses pack/cache paths rather than legacy development
asset directories. Existing player registry state was copied to
`local/remaster/player-settings/mw3-full-texture-registry.txt`, with only the
old texture-memory selection removed through the registry overlay's normal
absent-value marker. The original seed, saves and user pack selection remain.

The dev deployment compares the current profile against its saved parent before
atomic replacement; other graphics work and native builds are preserved. The
matching native source snapshot and executable/module pins remain enforced.
The signed host SHA-256 is
`db728475f51f63e34b20b9cb43a338872054d4f8301d8e7d7111fec85df21ba2`.
This task changes the dev selection; the hosted installer and update downloads
have not been republished with this repair.

Private source, build inputs, logs, original-menu input scripts, images and
metadata are in `local/work-ahead/c1m1-surface-investigation-20261023-r1`.
The frame budget deliberately terminates these tests with a typed diagnostic;
it is distinguished from an arena or gameplay crash. Normal mission exit,
long sessions and the remote PC remain separate validation scopes. No replay,
original-code execution fallback or injected mission state was used. Strict
acceptance remains 131/144.
