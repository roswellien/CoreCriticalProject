# Firefly: Firebug-inspired geometry prototype

2026-10-19. The user requested the same offline geometry development performed
for Owens, using two supplied Firebug STL archives as visual inspiration.
This is an authored original-MW3 geometry candidate, not an installed STL port.

## Reference and changes

Both archives are in `C:/Users/jcbla/Downloads/`:

| Archive | SHA-256 |
| --- | --- |
| `63f5461347cff_firebug-pose2-by-punykaiju.zip` | `2aab51305c3b0dc6976fe0cd12d11fe87771c42e5d7baf334df314946333c0a4` |
| `firebug-minature-with-1-25-base20230221-60-f9e4v7.zip` | `67a5a2d31ef2e891465eee792451bf0622267c820b7efb3f20a3ef7dd4752ebd` |

Filenames credit PunyKaiju; neither supplied archive includes a README or license
notice. Together they contain two 119,428-triangle posed mech designs and a
separate display base, with pose 2 duplicated across archives. Both poses were
rendered from multiple angles for local inspection. No reference triangles,
STL pose, print base or rig were imported into the candidate. Original inputs
and extracted references remain local and unchanged; reference contents are data.

The candidate retains MW3 proportions, weapon layout and all 21 source-owned
moving meshes. Geometry grows from 622 to 23,688 triangles. It adds 103 chamfered
armor panels, circular side housings and fasteners, four cooling grilles with
30 louvers, cockpit framing, four recessed leg rails, embedded hip/knee covers
and physical missile wells on the original seven-by-two repeating launcher face.
The side canopy frame follows its painted contour across source facets rather
than adding bars at arbitrary polygon boundaries.

Ten toe hinges use the eight original toe controls. Each source toe02 mesh has
two separated front prongs: an initial single center hinge failed the mounting
check and was replaced by two hinges, each embedded in its corresponding prong.
No joint, limb or toe controller was moved. Source geometry and UVs are retained
hidden for comparison. New geometry is joined by the original moving owner.

Existing worn MW3 colors and the selected 12x reference (Blender Strength 10.20)
are retained. Added mechanisms use provisional procedural preview finishes;
source-textured side glazing and the framed roof pane have smooth normals.
Broad armor centers remain planar with no added generic bump. New native texture
baking remains separate work.

## Validation and execution boundary

All 35 original controller/frame objects retain exact source world matrices
through 336 poses, maximum error zero. Reopened scenes match the original
geometry/UV and action hashes. Candidate parents/local matrices match source,
positions/UVs are finite, material indices valid and modifiers applied. Eighty-two
mounting samples pass: 72 bearing backing samples and ten toe hinge centers lie
inside their corresponding source parts. This is overlapping game geometry,
not welded topology or full inter-part collision clearance validation.

All 48 packed source images retain their bytes. Original walk curves, source
proportions and controller ownership remain intact. Offline interpolation and
in-place presentation retain the existing preview limits; they do not reproduce
all native ground adjustment, animation decisions, damage or visibility behavior.

Boundary advanced: user-supplied STL references -> authored MW3 Firefly geometry
candidate -> matched offline walking and geometry review. Native mesh/LOD export,
texture baking, weapon/damage checks and live performance remain before runtime
adoption. Current 16 installed replacements and launchers are preserved. No game
launch, desktop screenshot, original registry/pilot write or commit. Strict
acceptance remains paused at 131/144; no native-function credit is added.

Workspace and retained authoring scripts:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/firefly-detail-20261019-r1/`.
Local review and packed scene: `local/work-ahead/mw3-firefly-detail-r1/`.

## Delivered review

[Organized Firefly review](https://drive.google.com/drive/folders/1KVGnm-B55x1T3fd9Q9cXX5XalfFVBLQG).
[Color before/after](https://drive.google.com/file/d/1GnOWhjQ1nha9sSlHb77Fs6Nhg6wrjuLS/view?usp=drivesdk) and
[walking comparison](https://drive.google.com/file/d/1WqUXKvwpFu1PD5XJvShLC5ryz5in6jGM/view?usp=drivesdk).
Four gray before/after views disable all normal maps and use one uniform material.
The walking video has 168 matched camera/light/object frames per version, three
source cycles at 30fps/5.6 seconds. Each 1280x960 image is retained without
downscale in a 2560x1020 H.264 CRF8 comparison encoded from lossless PNGs.
These are Blender reviews, not native gameplay or FPS evidence.

All seven uploaded previews/notes have verified names, MIME types, parent folders
and exact remote/local byte sizes. Local SHA-256 values are recorded separately;
no remote checksum equality is claimed. Raw models, references and textures stay
local, and sharing permissions were not changed. The five initial live launcher/
registry identities are unchanged. The local HTML, packed editable scene and
checks are retained in the delivery folder above.


Runtime follow-up, 2026-10-20: the detailed Owens and Firefly are now included in
the [18-model main Remaster integration](all18-mechs-main-integration-2026-10-20.md).
This supersedes the offline-only status above for those installed candidates;
the listed native combat/performance limits remain.
