# Full-AI texture starting batch

Recorded 2026-10-07. After reviewing the detailed AI artwork against the first
preserved exports, the user selected **the AI version at 100% as the starting
point**. This is now the active art direction for the twelve-texture work-ahead
batch. The [earlier preserved batch](work-ahead-texture-batch.md) remains a
comparison and records the same source-entry mapping.

All twelve use complete generated RGB and generated transparency, without
original RGB restoration, marking/border locks or source-anchored detail. Eleven
reuse the existing AI artwork; white smoke now has its own newly generated draft.
This selection accepts the generated look for preparation. Mapped UV, marking,
tiling and effect behavior review remain open before integration.

## Local working package

The ignored `local/work-ahead/texture-ai-v2/` contains native AI PNG artwork,
source PNGs, prompts and provenance, source/container/entry hashes, actual export
commands, outputs, layered OpenRaster files, review previews and independent
checks. `texture-ai-v2.zip` and its SHA-256 sidecar sit alongside the directory.
No source containers are bundled.

Native working artwork is retained unchanged: 1254 x 1254 for eleven textures,
and 1774 x 887 for the annihilator panel. Exports are resized once to 1024 x 1024
for mech/terrain surfaces, 1024 x 512 for the annihilator, and 512 x 512 for the
four effects. These sizes retain more detail than the previous 4x exports; they
do not imply recovered source detail or a settled engine texture contract.

`final.png` is byte-identical to `ai-sized.png`: AI color and AI alpha, with only
bicubic size conversion. The three-layer editable document opens with this final
visible; original-mask and source-grid comparisons remain hidden.

The gallery defaults to the full-AI export, with native working art and the
original-mask comparison available separately. Fit, 100% and 200% views report
actual pixel dimensions. Background and terrain repeat controls aid review.
Rendered browser automation remains unavailable for local file URLs; gallery
JavaScript and resources receive static checks.

## Alpha and compatibility

Original masks are retained separately. `source-alpha-preview.png` transfers each
original alpha byte exactly onto an integer-sized AI RGB grid, with black RGB at
zero alpha and no RGB locks. Its report is explicitly scoped to that comparison.
These are not the selected starting images.

The generated effects have different footprints from the originals. Restoring
original alpha can expose dark pixels where the AI image was transparent, or
clip AI features. The starting images therefore keep AI transparency. The
independent report records those footprint differences separately from main
export identity. Final engine compatibility will require mapped effect and
animation review rather than assuming the original-mask comparison is suitable.

All twelve main exports pass exact AI file/RGBA identity checks. Source/native
generation hashes match; optional original-mask previews pass exact alpha,
visible AI RGB, transparent RGB, source-grid and report-identity checks. Source
RGB locks are empty and anchoring is disabled. Editable stacks, merged images,
thumbnails and archive identities are checked during packaging. The existing
export tool is unchanged; its 27 authored asset tests previously passed.

The user subsequently approved the displayed batch and requested the next step.
Visual status is now **reviewed**, while actual mapped compatibility remains
pending. That approval is recorded separately under ignored local storage to
preserve the sealed texture ZIP and its hashes.

The [four-material height/normal pilot](work-ahead-material-pilot.md) has expanded
to the [eight-material batch](work-ahead-material-batch.md). A
[six-frame dust animation pilot](work-ahead-effects-animation-pilot.md) now
prepares a configured effect sequence with the same full-AI starting direction.
Replacement lookup, renderer validation and release approval remain subsequent work. INTRO
remains the first planned full video upscale, with processing on hold.
