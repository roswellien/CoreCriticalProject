---
name: core-critical-add-mech-pack
description: Build an additional mech pack, or a skin pack for an added mech, from a portable project with prepared models and textures. Use when adding a new mech, or a skin for one, as community content.
---

# Add a mech pack

The rules live in `docs/authoring-additional-mechs.md` (how to build a pack) and
`docs/additional-mech-packs.md` (identity and compatibility). Read both first;
this is the order to work in.

1. **Lay out the portable project** as in "Portable project": one folder holding
   the project file, the definition override and every payload, with paths
   relative to the project (no parent paths, absolute paths, links or commands).
   Pick a stable namespaced pack ID and chassis ID, and keep them unchanged when
   updating the same mech.
2. **Match the controller.** The definition template must match the visual
   controller, and the model must fit that controller's skeleton, collision and
   damage topology. Metadata may use another stock template with matching mass,
   class and technology.
3. **Use prepared payloads only** ("Prepared models and textures"): close and
   distance meshes in `BWMESH4`, textures in `BWTEX1`. A GLB or PNG renamed to
   `.bin` is not a payload.
4. **Build** into an output folder that doesn't exist yet (the builder creates it
   and refuses an existing one, even if empty):
   `python tools/remaster-launcher/build_chassis_pack.py --project <project file> --output <new folder>`.
   Install the `<pack_id>-<version>.mw3pack` it writes there; the `pack` folder
   beside it is the builder's staging copy.
5. **Install** it in a compatible launcher (Mods & Packs, Install Pack), enable it
   and check it appears in the Mech Lab ("Installing and adding skins").
6. **For a skin pack,** set its chassis to the full ID (`<pack_id>:<chassis_id>`)
   and follow the same section.
7. **Before calling it release-ready,** run the gameplay and save checks the
   authoring doc lists with the exact installed pack. A successful build or import
   alone is not release qualification.

Never put original MW3 media or generated game code in a project, a pack or the
repository (`docs/legal.md`). Report what was and wasn't checked, as
`docs/project-status-reporting.md` asks.
