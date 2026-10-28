# Texture light audit and launcher verification - 2026-10-20

The user requested a review of missed light-bearing artwork before enabling more
lights, highlighting the red indicators inside Training's opening mechbays.
This audit changes no textures, light registrations, gameplay or light budget.
Acceptance remains **131/144**.

## Current Play launcher

`Play MW3Remaster.cmd` calls the maintained Python launcher and defaults to
`local/remaster/launcher.json`. That profile now selects
`local/remaster/launcher-f12-r1/build/entry_commandline.exe`, SHA-256
`cd230d892bf84312c7a008d1833da0d95003f0c73b1bfe88d93cfb8013943cbd`.
The GUI launcher reads the same published profile and creates a per-launch copy.

The source chain is repaired lighting R7 (`f250b300...`), then display/material
repairs (`a80468e4...`), then F12 pass-through (`cd230d89...`). The selected
executable matches its profile and source snapshot; every recorded host source
pin matches. Maintained campaign, fixture, sun/settings and compiled lighting
shader headers match the selected host. Display and material-catalog changes
remain included. This verifies the current published build, not arbitrary
unfinished experiments elsewhere in the workspace.

The actual CMD wrapper passes `--check` and asset preparation. A retained native
Campaign 1 check of this build reached its intentional 1,800-frame budget; its
exit 1 is a bounded test stop, not a crash. An existing live process uses the
same host and was left untouched. No older host was republished over concurrent
launcher work. Evidence: `reports/texture-light-audit-20261020/launcher-verified.json`
and the wrapper check/preparation logs.

## Audit scope and findings

All **39 active upgraded bank files** match their published source hashes.
Their **24,685 entries** decode into **8,743 distinct pixel variants**, with all
bank/name occurrences retained and **zero skipped entries**. Registered native
replacement models and the alternate Bushwacker skin contribute **92 distinct
atlas images from 146 material-source occurrences**. The complete review contains
**8,835 entries**. Normal maps are not treated as light artwork.

| Coverage label | Variants | Meaning |
| --- | ---: | --- |
| Registered fixture | 37 | Exact converted runtime pixel key matches the permanent fixture catalog |
| Unmatched fixture variant | 32 | A name is already represented in that catalog, but these pixels do not match |
| Effect catalog only | 78 | Matches a weapon/effect light identity, not a permanent world fixture |
| Not registered | 8,596 | No permanent fixture match; this includes many ordinary non-light textures |
| Model material - not registered | 92 | Replacement-model atlases bypass the source-world fixture observer |

These counts describe texture variants, not physical lamps or simultaneously
active lights. Registration does not establish correct bulb/UV placement,
direction, visible illumination or complete coverage of an atlas. Alpha-packed
and zero-coverage runtime identities are considered separately. Generic colored
patches and bright regions generate review candidates; painted markings,
reflections, skies and effects remain explicit false positives.

`C5STRT18` and `C5STRT23` contain clear red indicators and are unregistered in
the current fixture catalog. Their appearance is consistent with the reported
Training bay walls; exact live polygon/UV correspondence has not been traced.
They lead the focused PDF as **T0065-T0070**. Other visible candidates include
vehicle warning lamps, cockpit instruments and previously unregistered lamp
textures. A texture containing a glowing panel must not turn its entire polygon
into a lamp without the appropriate mask and placement review.

## Review package

[Google Drive review folder](https://drive.google.com/drive/folders/1Fh3m0SjBrc1IC5pKVgQ_Ynz8xTakycUZ)
contains:

- A **40-page focused PDF**, with 239 variants: registered fixtures, unmatched
  variants, named lamp candidates, selected visual examples and all replacement
  model atlases. The Training red panels appear first.
- A **247-page broad PDF**, with 5,920 heuristic/replacement candidates. This
  deliberately includes false positives and is not a list of 5,920 missing lights.
- An offline interactive ZIP containing all 8,835 entries, embedded previews,
  search/filter controls, decision export, CSV and instructions.
- A first-page Training example PNG for quick remote viewing.

After downloading and extracting the ZIP, open `all-textures-review.html`.
Review choices are **add/correct light**, **glow only**, **not a light** and
**keep current light**. Export decisions as JSON, edit `review.csv`, or supply IDs
and notes in chat. No decisions are automatically imported into the game.
T IDs identify active-bank variants; M IDs identify replacement model atlases.

Local outputs reside under
`reports/texture-light-audit-20261020/gallery-r2`, through the existing Games-drive
reports junction. Source identities and occurrences are in `audit.json`; Drive
identities/readbacks are in `drive-files.json`. Earlier scan outputs are retained
as superseded diagnostics. RGB565 artwork is unchanged; JPEG previews are review
images, not new runtime textures.

PDFs were reopened for page counts/text and visually rendered for layout checks.
The standalone gallery payload contains every unique ID and embedded preview;
its JavaScript passes Node syntax checking. Browser rendering was not verified:
the browser policy blocks local file URLs, and no workaround was attempted.
Drive uploads were verified by metadata readback without changing sharing.

## Light budget

The configured limit remains **16 combined selected lights per rendered scene**,
with eight slots reserved for weapons. It is not a 16-light limit on an entire
map. The current uniform/shader supports up to 32 entries, but increasing the
selected budget was deferred by the user. A later change should measure the
actual renderer and scenes; another game's light cost does not establish this
shader's cost. No limit or performance defaults changed in this audit.
