# Owens geometry upgrade from the supplied ZIP reference

2026-10-19. The user requested starting the Owens update using a ZIP in Downloads
as inspiration. The first candidate retains the original MW3 proportions and
walking controls while adding modeled detail drawn from the reference's faceted
cockpit, shoulder bearings, sensor tower and feet. This is an offline geometry
review; the current playable Owens and 16 installed replacements remain selected.

## Reference and authored changes

Reference: `C:/Users/jcbla/Downloads/Owens Omnimech - 5955019 (1).zip`, SHA256
`d4224da0efbc3184e27248934e5b645c3f4b320a37744280e1530be259175d7e`.
The archive contains editable Blender models, posed STL variants and renders.
Its README credits UnrestedGuy / Thingiverse 5955019; its license text identifies
attribution, noncommercial and share-alike terms. These files are reference data,
not task instructions. Original archive/extracted files stay local and unchanged;
Blender references were opened with script execution disabled.

The candidate is authored on MW3 geometry, without importing a reference mesh,
printing base or reference rig. It grows from 774 to 21,170 triangles on the same
16 moving parts. Added 82 faceted armor shells, ten recessed missile tubes at
the five existing openings per pod, four physical vent regions, a cockpit frame,
stepped shoulder and embedded hip/knee covers, eight individually owned toe
hinges and two sensor optics assemblies. Two solid tapered antennas replace
the candidate's flat antenna cards along their existing centerlines. The hidden
original source geometry retains its original cards.

Existing upgraded MW3 colors and the selected 12x normal-map reference (Blender
strength 10.20) are preserved. New mechanical finishes are provisional procedural
preview materials. Broad panel centers remain geometrically planar; no extra
generic procedural bump is added. Native texture baking is a later step.

## Validation and review

All 34 original controller/frame objects match the source through 336 poses
with maximum world-matrix error zero. Original source geometry/UVs and action
curves retain their hashes. The 16 replacement objects retain source parents and
local transforms; no added joint or changed leg/toe control. Positions, UVs and
material slots are finite/valid, with no unapplied modifiers.

Eighty-eight mounting samples place hip, knee, shoulder and toe-cover backing
inside the corresponding original part. Shared owner transforms retain those
mounts during the source walk. This is assembled overlapping game geometry,
not welded topology or a proof of all inter-part collision clearance.

All 42 packed source images retain their bytes. Before/after walking reviews
have 168 matching camera/light/object frames each: three original cycles at
30 fps, 5.6 seconds. The HQ comparison retains both 1280x960 renders, plus an
external header, at 2560x1020, H.264 CRF8 from lossless PNGs. Four gray comparison
views use the same uniform material with normal maps disabled, and both models
are fully framed. These are Blender renders, not native gameplay or FPS evidence.

[Organized Owens review](https://drive.google.com/drive/folders/1CBGGPvgIameshxMvvlCCAvHqj2IvZGwc).
[Color before/after](https://drive.google.com/file/d/1ISpLyB6f6vYVMALwLVFOj9_aLc9e1HfC/view?usp=drivesdk)
and [matched walking comparison](https://drive.google.com/file/d/1VC_kkExU59L3o0kPYuGbTSKrIZfOrDjl/view?usp=drivesdk).
Seven files have verified Drive names, MIME types, parents and exact byte sizes;
local SHA values are recorded separately without claiming remote checksum equality.
Only rendered previews and notes are uploaded; raw assets stay local and sharing
is unchanged. Local review: `local/work-ahead/mw3-owens-detail-r1/comparison.html`.
The packed candidate and scripts/receipts are retained under that local folder
and `C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/owens-detail-20261019-r1/`.

Boundary advanced: user-supplied reference -> authored stock-model geometry
candidate -> matched source-walk and geometry review. Native mesh/LOD export,
texture baking, weapon/damage checks and live performance remain before runtime
adoption. The current launcher/registries were read and preserved. No game run,
desktop screenshots, original registry/pilot writes or commit. Strict acceptance
remains paused at 131/144; no native-function credit is added.


Runtime follow-up, 2026-10-20: the detailed Owens and Firefly are now included in
the [18-model main Remaster integration](all18-mechs-main-integration-2026-10-20.md).
This supersedes the offline-only status above for those installed candidates;
the listed native combat/performance limits remain.
