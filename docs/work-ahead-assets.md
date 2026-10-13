# Work-ahead assets and visual modernization

Established: 2026-10-07. Scope: MW3 first; other games need separate inventories.

Current status, reviewed 2026-10-13: the optional
[Hi-Res texture pack](hi-res-texture-pack.md) has progressed beyond the early
pilots below into cumulative local archive integration. The latest local audit
records 39 configured archives and 19 complete primary mech sets; the terrain
inventory records 243 of 298 priority families upgraded across their banks.
Runtime visual acceptance and public distribution remain separate open gates.
The following pilot descriptions retain their original scopes and evidence.

The [first installed-tree discovery](work-ahead-discovery.md) is complete;
selected image containers and 19 disc videos have been inventoried. Other
embedded formats remain open. The reusable
[inventory tool](../tools/asset-inventory/README.md) records local metadata.
The [first texture decoding pilot](work-ahead-texture-pilot.md) now has six local
reference previews covering opaque, black-key and full-alpha images. Enhancement
experiments now have [4x comparisons and disc-video metadata](work-ahead-enhancement-experiment.md).
The generated damage candidate fails alpha fidelity; a faithful resize baseline
is available. Original-renderer review and replacement-pack approval remain open.
The [five-second video pilot](work-ahead-video-pilot.md) now compares two AI
models and a conventional 2x upscale with verified timing and original PCM.
The [first prepared texture batch](work-ahead-texture-batch.md) now packages
12 exact 4x exports across mech panels, terrain and effects, with source mapping,
editable documents, hashes and a local review gallery. Preservation checks pass;
mapped in-game approval remains open. Following review, the user selected the
[full AI version](work-ahead-texture-ai-batch.md) as the starting direction.
That new twelve-texture package retains full AI RGB and transparency, native
working artwork, and separate original-mask comparisons. The user has now
visually approved that batch; a [four-material height/normal pilot](work-ahead-material-pilot.md)
has now expanded to the [eight-material normal-map batch](work-ahead-material-batch.md).
The next [effects animation pilot](work-ahead-effects-animation-pilot.md) prepares
six AI dust frames with source-script ordering evidence and transparency review.
User feedback led to a [softer dust revision](work-ahead-effects-transparency-revision.md)
with lower exported alpha and the first AI version retained for comparison.
The user accepted the softer dust appearance; the
[complete sixteen-frame fire pilot](work-ahead-fire-animation-pilot.md) now has
AI exports, editable layers and an animated comparison ready for visual review.
The next [machine-gun impact pilot](work-ahead-weapon-impact-pilot.md) prepares
a complete four-frame white flash and residue sequence with weapon-definition
and frame-order evidence.
The [white-smoke concept](work-ahead-smoke-animation-concept.md) explored four
AI-authored states from one sprite. Follow-up source discovery found a likely
two-texture `jump_smoke` association and prepared a [two-frame AI pilot](work-ahead-smoke-animation-pilot.md);
compiled playback order and timing remain unverified.
The opening movie is first in
the planned full-upscale queue, with processing on hold.
A new [non-effect surface texture batch](work-ahead-surface-texture-batch.md) prepares eight full-AI mech and terrain drafts for visual review; UV assignment and in-game compatibility remain unverified.
The [Training texture proof of concept](work-ahead-training-textures.md) inventories the t1 raster banks and prepares fourteen full-AI terrain/water drafts; the complete four-mission non-effect texture roster is still being traced.

This parallel track prepares optional visual improvements while recompilation
continues. Preparation does not advance CPU/ABI or gameplay compatibility gates.
Assets can become ready for integration before M7; enabling them in a release
still requires the original-behavior baseline and modernization checks.

## Readiness states

Use these states for each item: **queued**, **inventoried**, **prototype**,
**reviewed**, **integration-ready**, **integrated**, **validated**. None of the
whole-game asset categories below are claimed as integration-ready. WA01 has 12 visually reviewed image prototypes and eight additional mech/terrain drafts awaiting review; WA04
has 12 visually reviewed image prototypes; WA03 now covers eight authored-height
material prototypes with sixteen paired normal maps. WA04 also has six visually
reviewed AI dust-animation frames, sixteen AI fire-animation prototypes and
four AI weapon-impact frames
prepared for visual review, plus two source-associated AI smoke frames.
Compiled smoke order, native timing, motion and blending validation remain open.
WA02 has a disc inventory, video prototype
and a held full-upscale plan for the opening movie.
The twelve-texture AI batch is visually reviewed; its source-coordinate
and mask checks do not replace mapped compatibility review.

Integration-ready means the source identity, replacement mapping, editable
source, export recipe, quality review, provenance and rollback behavior are
documented. It does not mean the native game can consume the replacement yet.
Mark unresolved engine assumptions explicitly; do not lock exports to guesses.

## Workstreams and integration gates

| ID | Workstream | Preparation that can start now | Engine gate for integration | Acceptance criteria |
| --- | --- | --- | --- | --- |
| WA01 | Texture upscales and authored remakes | Inventory dimensions, palettes, alpha and likely usage; define a faithful art direction; choose a small representative pilot | Verified texture decoding, stable asset identities and optional replacement lookup; renderer preserves original sampling and transparency | Compare at original and target resolution; retain markings, silhouette cues and material identity; check tiling, mipmaps, alpha edges and memory cost |
| WA02 | Video upscales and authored rerenders | Inventory containers/codecs, dimensions, frame rate, duration, audio and subtitles; define restoration versus rerender goals | Verified playback and replacement routing with timing, audio sync, aspect ratio, skipping and fallback | Preserve sequence duration and cue timing unless explicitly changed; review flicker, invented detail, motion artifacts, cropping and audio sync |
| WA03 | Normal maps and material detail | Classify materials; define authored surface depth separately from painted shading; prepare a small material test scene | Recovered geometry/UVs, normal orientation, tangent convention, lighting and shader support | Check seams, handedness, inverted depth and moving-light behavior; avoid turning text, shadows or painted highlights into relief |
| WA04 | Effects upscales and remakes | Inventory sprites, animation frames, transparency and intended appearance; cover smoke, fire, explosions, muzzle flashes and weapon impacts if observed | Verified effect sequencing, blending, depth behavior, billboards and rendering hooks | Preserve gameplay cues, visibility, frame timing and apparent size; check atlas bleeding, sorting and overdraw |
| WA05 | HUD, menus, fonts and cockpit artwork | Inventory UI elements and coordinate assumptions; prepare scalable layouts and readable artwork | Native menus/HUD render correctly; scaling, clipping, hit regions and aspect behavior are understood | Check text readability, alignment, input targets and cockpit/HUD visibility across supported resolutions |
| WA06 | Models, terrain and geometry detail | Inventory formats, UVs, LODs, animation and attachments; separate visual geometry from collision | Verified model loading, animation, attachments, LOD selection and collision separation | Preserve silhouettes, weapon origins, animations and gameplay collision; measure frame cost |
| WA07 | Audio restoration | Inventory sample format, looping and event roles; define noise cleanup and loudness goals | Verified audio loading, mixing, spatialization and optional replacement routing | Preserve event duration, loop boundaries and recognizable cues; check clipping and positional behavior |

WA01, WA02 and WA04 are the initial priorities. WA03 follows a reviewed texture
pilot and material research. WA05-WA07 are queued extensions, not commitments
to replace every asset. Video rerenders may require scenes, models and animation
that a simple upscale does not; track those dependencies per clip.

## First work package

1. **WA00: Asset discovery.** Produce a local, read-only file/container inventory
   from the admitted installation, excluding installer/media directories.
   Record hashes, sizes, signatures and metadata; extensions alone do not prove
   a format. Identify existing decoder support and document unknown formats.
   The installed files include `.zbd` containers, but their contents and
   replacement granularity have not been established by this plan.
2. **WA08: Format probes.** Select one container per observed format. Document
   bounds, indexing, compression, palettes and checksums where evidenced.
   Validate tooling with authored fixtures before relying on extracted metadata.
3. **WA09: Visual baseline and style guide.** Capture approved local reference
   scenes when feasible. Define fidelity goals, acceptable detail changes,
   color treatment and naming. Keep upscales and authored remakes identifiable.
4. **WA10: Representative pilot.** After formats and content policy are resolved,
   choose a small batch: a tiled surface, marked mech panel, transparent sprite,
   UI element and short video segment where available. Review these before
   scaling production. Record effort and storage to estimate the full backlog.
5. **WA11: Replacement contract.** Once loading behavior is recovered, implement
   stable lookup, source-version checks, optional packs, original fallback,
   settings and cache behavior. Avoid changing original installation files.

Discovery and format research can run alongside M2. Loader evidence in M3/M4
may permit replacement prototypes. In-game scene review depends on the relevant
native rendering/playback path, often M4/M5. Final regression and configurable
release acceptance remain M6/M7 work. Milestone numbers are dependencies, not
delivery dates; a particular subsystem may become available earlier or later.

## Per-asset record

Keep local records in `local/work-ahead/manifest.json` once discovery starts.
The proposed record fields are a planning contract, not an implemented loader:

| Field | Purpose |
| --- | --- |
| `id`, `workstream`, `status` | Stable task identity and readiness |
| `game_profile`, `source_container_sha256`, `source_entry` | Bind to the observed installation and container entry |
| `source_metadata` | Dimensions, format, palette/alpha, frames, timing or audio properties as applicable |
| `method`, `tool_version`, `parameters` | Reproducible processing or authored export recipe |
| `editable_source`, `output`, `output_sha256` | Locate the working source and verified export |
| `provenance`, `distribution_status` | Record authorship, dependencies and release eligibility |
| `integration_dependencies`, `unresolved_assumptions` | State what the engine must provide |
| `review_evidence`, `known_issues`, `owner` | Track quality review and follow-up |

Store working assets, derived previews and original references under ignored
`local/work-ahead/`; keep repository documentation and tooling asset-free.
An upscale from a game asset is still derived content. Authored remakes also
need provenance and distribution review; authorship alone does not settle it.
The [distribution policy](legal.md) permits user-authorized decoded research
previews in ignored local storage. Production of derived replacement packs
needs a defined content/provenance policy before release; local decoding does
not establish distribution rights. Discovery, specifications and authored
tooling remain asset-free in the repository.

## Review and integration

Review against original references at the scale seen in-game, not just enlarged
previews. Use stable comparison scenes and note intentional departures. Normal
maps require moving-light checks; effects require motion and combat visibility
checks; videos require full-speed playback and synchronized audio checks.

Preserve an original-assets mode. Missing or incompatible optional replacements
must fall back predictably, and one pack must be removable without rebuilding
the game. Measure load time, memory, frame cost and playback behavior once the
native path exists. Choose budgets from measured baselines instead of invented
thresholds. Visual approval alone does not satisfy runtime validation.
