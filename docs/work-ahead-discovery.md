# MW3 work-ahead discovery

Recorded 2026-10-07 using the project-authored asset inventory tool against the
local installed MW3 tree. Installer and three media directories were excluded.
Local report: `local/work-ahead/inventory.json`, including tool and file hashes.
This is a current-tree inventory, including compatibility files and mutable
configuration/log files; it is not a reconstruction of the original media.

The later [texture decoding pilot](work-ahead-texture-pilot.md) resolves the
initial pixel-layout and alpha hypotheses for this supported subset. The
observations below preserve the earlier structural probe's scope.
Later [disc-video discovery](work-ahead-enhancement-experiment.md) found nineteen
AVI files on the supplied ISO; the installed-tree scan below did not include them.

## Observations

- 139 files, 422,553,909 bytes; 112 `.zbd` and 10 `.wav` files.
- Twelve files have leading RIFF/WAVE signatures: the ten standalone WAVs and
  `zbd/soundsH.zbd` and `zbd/soundsL.zbd`. These two ZBD files need separate
  investigation; the first decoded stream is not a complete container inventory.
- No leading AVI, Bink or Smacker signature was found. Embedded video, other
  formats and disc-only content remain unexamined.
- No whole-file duplicates were found. Equal sizes do not imply identical data.
- Texture dimensions, palettes, alpha, UVs and effect frames are unresolved.
  Filenames are candidate-selection hints, not verified semantic labels.

## Next format probes

| Priority | Candidate | Question and required evidence |
| --- | --- | --- |
| 1 | `zbd/rmechtex.zbd` and `zbd/rmechtex16.zbd` | Recover bounded entries and image descriptors; verify dimensions, pixel/palette format and decoding on representative entries before a texture pilot |
| 2 | `zbd/rimage.zbd` | Establish its entry format and observed usage; determine whether UI/effect imagery is present without assuming from the name |
| 3 | `zbd/soundsH.zbd` and `zbd/soundsL.zbd` | Compare declared RIFF length, physical size and chunk boundaries; establish whether streams, trailing data or an outer index explain the layout |
| 4 | Supplied MW3 disc file inventory | Locate video candidates using signatures and metadata, excluding installers and redistributables; do not equate absence from installation with absence from media |

## First bounded format probes

The project-authored `tools/asset-inventory/probe.py` tested a structural
hypothesis: a 24-byte header, count at byte 12, and 40-byte records containing
a 32-byte name, absolute offset and marker. All records passed name, table,
offset-order and descriptor-bound checks in the following files. The first
entry starts immediately after the table in all three. This is evidence for
these files, not a universal ZBD specification.

| Container | Entries | Exact spans of 16-byte descriptor plus width × height × 2 | Descriptor tags |
| --- | --- | --- | --- |
| `rmechtex.zbd` | 3,360 | 3,350 | 5: 3,350; 11: 10 |
| `rmechtex16.zbd` | 2,286 | 2,285 | 5: 2,285; 11: 1 |
| `rimage.zbd` | 394 | 288 | 5: 90; 3: 198; 11: 106 |

Candidate dimensions are little-endian 16-bit values at descriptor bytes 4
and 6. A two-byte pixel representation fits 5,923 entry spans exactly; channel
layout, alpha/color-key behavior, orientation and tag semantics remain unknown.
Do not interpret tag 11 entries using the simple pixel-span hypothesis.

Both sound containers parse as **999 successive RIFF streams**, followed by
**147,860 unparsed bytes**. Chunk lengths and padding were checked within each
stream's declared bounds. The initial all-RIFF hypothesis failed at offsets
92,677,054 (`soundsH`) and 46,039,734 (`soundsL`); those boundaries are preserved
in the reports. The trailer could contain indexing or other data; its purpose
has not been verified. Equal trailer lengths do not prove equal contents.

Local reports are `local/work-ahead/{rmechtex,rmechtex16,rimage,soundsH,soundsL}-probe.json`.
Each binds source bytes and the actual probe revision by SHA-256. Names and
per-entry metadata remain local. Six authored-fixture tests pass for inventory,
invalid table counts/offsets, dimension/span checks, RIFF sequencing/trailers
and malformed chunk bounds. No proprietary fixtures were added to tests.

First texture-pilot candidate: entry 0 of `rmechtex.zbd`, with candidate
dimensions 128 × 64 and an exact two-byte pixel span. Before production,
verify its channel layout and orientation against loader evidence or an original
reference. Its observed name does not establish its in-game role. Include an
alpha-bearing or keyed image and a tiled surface once those roles are verified.

WA00's installed-tree discovery is complete. WA08 has bounded structural passes;
pixel decoding, special entry types and sound trailers remain open. Disc-video
discovery also remains open. No payloads have been exported, upscaled or remade,
and no replacement loader exists.
