# C1 road artwork and softer world normals — 2026-10-18

The C1 roads were loading replacement banks, but several replacements retained
the soft appearance of the original 32×64 or 64×128 artwork. Increasing file
size had not supplied equivalent visual detail. The earlier terrain export
receipts identify `source_anchored_detail` for these variants, while the primary
`c1-rtexture` export uses the detailed AI-assisted road candidate. This confirms
a quality problem in the selected variants, rather than an exact original-file
fallback. Other campaign road families have not all been checked yet.

## Changes installed in the previews

- Reused the existing detailed `road01` and `road03` primary exports from
  `campaign1-terrain-batch-v1/v2` across the six C1 bank variants: 12 entries.
  The existing normalized UV layout and each entry's dimensions are retained;
  lower-resolution bank entries receive a filtered import of the same artwork.
- Compared every byte outside the selected road color planes against each source
  bank. All other bytes are identical, preserving the shoreline revision, other
  textures, descriptors, entry counts and offsets. Original banks are untouched.
- Preserved all 3,998 previous world-normal identities and pages. Added two new
  exact full-pixel identities for the 512×1024 road imports, with 256×512
  material-specific color-derived normal drafts. Two 1024×2048 donor identities
  were already registered; their existing normals remain. No physical-height or
  final hand-authored normal-map claim is made.
- Reduced terrain/original-world-object normal strength **2 → 1.5** in Normal
  Mapping Preview, Sky and Water Preview, and Material Normal Preview. This
  follows the user's numeric example **4 → 3**, a 25% reduction. Separately
  tuned replacement-mech, dedicated water and cloud strengths are unchanged.
- Installed the verified road bank map and extended world manifests in all
  three preview profiles. Regular Play and standalone Big Lake remain separate.
  No native executable or gameplay source change was needed.

## Native verification and screenshots

Two fresh bounded C1M1 runs use the same original input route and resolved midday
preset: azimuth225°, elevation35°, sun0.85, ambient0.2. They differ in road
artwork/registrations and world strength. Replay video buffering is off. Both
complete the intended 2,000-presentation budget and preserve all 2,000 original
frame/draw-count/hash triples. Runtime logs confirm the new normal page is loaded.
The full diagnostic counter lines differ as expected; equality refers only to
the original three fields. This is not a performance benchmark or full-mission
fidelity result. A further 2,600-presentation run supplies the village view.
Budget stops are intentional test exits, not crashes or normal mission quits.

- [Before: road approach, strength2](https://drive.google.com/file/d/1_2Y4X1-Z6zwBv5EqOxp7ZQ3lW6riHtiC/view)
- [After: road approach, strength1.5](https://drive.google.com/file/d/1Z_tuBrATzo0GlDACDzb8ON_MG_FpLMdQ/view)
- [Updated village roads, strength1.5](https://drive.google.com/file/d/12Mbj37p_XoQqSH1f-L-tkcAH9vfs5cmD/view)

Screenshots are native 3440×1440 captures. The before/after pair changes both
road assets and world strength; it does not isolate their individual visual
contributions. Earlier orange screenshots used raw profile lighting rather than
the resolved midday preset, so they are not a matched comparison to this set.
The road still becomes less distinct with distance and grazing viewing angles.

## Evidence and next scope

Local evidence: `C:/Users/jcbla/MW34SunTests/road-audit-20261018/`.
`candidate-r2/receipt.json` pins donor artwork, six source/output banks and full
road identities. `verification.json` records the native comparison. Failed
preparation `candidate-r1` and the pre-launch execution-policy failure are
retained, excluded from successful verification. Source bank hashes stayed
unchanged. Private screenshot uploads do not change Drive sharing permissions.

The campaign-first100 encounter queue remains the work order. Its recorded
source identities describe the earlier capture; the new road keys are linked
by this revision's receipt rather than silently rewriting historical evidence.
Road variants need actual artwork checks as their missions are reached; a larger
image or an upgraded-bank label alone does not count as approved visual quality.
This patch repairs the two C1 road families, not every road throughout the game.

Execution boundary advanced: detailed existing road artwork now reaches the live
C1 native-rendered preview across bank variants, with matching normal bindings
and softer world relief. Acceptance remains **131/144**. No commit is made.
