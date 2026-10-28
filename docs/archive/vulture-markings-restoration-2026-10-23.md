# Vulture default texture restoration — 2026-10-23

The local dev mech pack now uses revised default Vulture/Mad Dog Body and
Variant color atlases at both detail levels. All five prior source color maps
first matched the installed BWTEX1 records exactly. Seven original vult05–11
maps supplied the paint and marking references.

Tan primary armor becomes subdued gray while off-white secondary armor and
existing blue zones remain. Blue contour trim, small yellow service details,
tiny red weapon-housing service tabs and lighter exposed edge wear restore
original visual cues. These are adaptations to donor UVs, not exact original
texture projection. Scratches retain neutral metal wear; the initial generated
blue-painted scratch lines were corrected. No unit numbers or faction emblems
were invented. Built-in image_gen produced the edits; prompts are saved locally.

Execution boundary: replacement-model default albedo resources. Current BWMESH6
geometry, live shoulder/arm attachments, model size, original simulation and
controllers, normal payloads and alternate skins are unchanged. No executable
rebuild or acceptance credit; 131/144 retained. No commit, installer build,
Google Drive upload or R2 publication is included in this local art change.

Checks:

- Both current native mesh payloads match their authoring sources byte for byte.
  Only the two default Vulture texture environment bindings changed.
- The close/distance BWTEX1 tables retain 34/22 batches. Weapons, Window and
  MissileHead records remain byte-identical; only Body and Variant change.
- Matched front/rear/close/unlit color reviews retain geometry/UV/pose and
  animation digests at both detail levels. Those older fitted source scenes
  contain 32/20 parts, predating the two native clavicle attachment additions;
  their images review color placement, not the current attachment correction.
- The current native host completed an 1800-frame presentation budget with
  the confirmed saved Vulture loadout, all 38 environment banks and candidate
  colors. Model logs contain 107 non-preview Vulture LOD0 replacement records.
  Third-person rear screenshots were inspected. Runtime identity and complete
  inputs are recorded in the private native-review/run.json.
- Installed model registry/manifest and new payload hashes pass. Other model
  entries compare equal. Both local authoring registries reference the updated
  Body/Variant PNGs. Launcher `--check` completed successfully.

Private files: `local/work-ahead/vulture-markings-20261023-r1/`, including
generation-prompts.json, comparison-front.png, textures/, packing-receipt.json,
installation-report.json, installation-backup/ and native-review/.

Installed color identities:

- Close: `5a972d0d6267744fb02248f6e078c7e149e976f2e91a15edbfc6c800b9321886`
- Distance: `1bd057f530c05d1416196ca36fa550fcc19a36d83b0e511dcffa3a6c93d36f54`

Limits: native front paint placement, live lower-detail transitions, extended
motion, destruction and firing alignment are not established by the stationary
rear review. Front placement and lower-detail paint were reviewed offline.
