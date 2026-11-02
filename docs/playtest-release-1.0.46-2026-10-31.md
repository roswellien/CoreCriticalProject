# Launcher and native runtime 1.0.46 playtest release

Release preparation for issue #153. This records intended scope, not completed
publication. Build only from the exact merged main SHA after the version
preparation and develop-to-main release PRs pass their checks and merge.

## Changes

- Native HD menu frames retain text textures while render workers use them,
  including when the recipe cache evicts entries. The regression passes under
  AddressSanitizer and fails when ownership is deliberately removed.
- Remove the redundant headlight member declaration that blocked native builds.
- Include reviewed integrations already in develop: bounded normal catalogs,
  optional pack-authored mech headlights and bindings, Training time-of-day
  support, legacy chassis skin handling, and clearer crash-upload error responses.
- Include the experimental Vulkan-to-DXGI presentation bridge. It remains an
  explicit developer environment option, not an automatically enabled launcher
  feature. Its documented restrictions and separate validation still apply.
- Asset authoring and C3M3 sky metadata changes are included in source. Code
  updates do not silently replace installed content packs; newly authored assets
  require their own reviewed pack publication.

## Delivery

Publish Core Critical Launcher 1.0.46-preview and MW3 native runtime 1.0.46.
Rebuild the canonical host; keep the translated game DLL unchanged. The full
installer includes the same validated runtime shipped by the native update.

- corecriticalinstaller-1.0.46-preview.exe
- 1.0.46.ccupdate with its matching launcher 1.0.46.zip
- 1.0.46.mw3update with its separate native 1.0.46.zip
- Optional offline wrappers 1.0.46-cc-update.zip and 1.0.46-mw3-update.zip

Existing players install the launcher first, restart it, then install the native
update with the game closed. Fresh setup includes both. Original supported game
files remain required; players do not need a compiler or Windows SDK. Automatic
update checking and crash reporting remain optional.

## Validation and remaining limits

Run the committed release checklist: source/dependency fingerprint checks,
asset-free tests, focused graphics/content/headlight tests and launcher checks;
timestamped Windows signatures and signed metadata; isolated full installation,
launcher upgrade, native activation/rollback and data preservation; immutable R2
readbacks and resumed downloads; protected Setup listings; and signed feed
promotion last with a concurrent-change guard. Preserve historical objects and
all unrelated content rows.

The exact reported C3M3 crash sequence has not been replayed. Issue #149 tracks
extended HD-menu playtesting. Baseline Vulkan presentation is blocked by surface
error -13 in the remote build session; any explicit DXGI bridge run must be
identified separately. Broad campaign, physical-PC and new content validation
remain open. Native MP4 playback and unmerged changes are excluded.
