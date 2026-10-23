# Strider stock cockpit in detached views

Strider's stock evolution footage exposed part of the attached first-person
cockpit through the top of the exterior. The exterior stock mesh is unchanged.
The current visual adapter now omits the authenticated attached Strider interior
only in detached photo/replay views, including when replacement models are off.
The exterior roof, head glass and antennae remain original.

The filter requires the full original close or distance chassis roster and the
complete ten-mesh cockpit roster. It checks names, vertex counts, bounded tree
traversal and readable mesh metadata. Extra, duplicate, missing or unknown meshes
do not qualify. The existing Avatar filter is retained. Normal first-person and
status-preview views do not use this filter.

The reproducible source transformation is
`tools/remaster-launcher/apply_strider_detached_interior.py`, applied after the
Avatar detached-interior transformation. Future host rebuilds must retain both.
Only `mesh_override_stage.inc` differs from the selected local play runtime;
the capture derivative adds this same one-file change to the current exact-frame
capture host. The translated module is byte-identical to the parent runtime.

## Checks and installation

- Compiled helper checks pass for both original LOD rosters, first-person bypass,
  exterior-head bypass and eight malformed/unknown-tree controls.
- Native stock views at 0, 30 and 60 degrees show the protrusion removed, with
  the exterior windshield, roof and antennae retained. The runtime logs the
  authenticated Strider interior omission.
- The ordinary play runtime completes a 1,300-frame original-stock first-person
  run; its cockpit structure is visible and no detached suppression is logged.
- The local launcher plan validates with the new source snapshot and executable.
  All asset bindings, graphics preferences and the preceding Avatar, Black Hawk
  and Champion fixes are retained.

Selected local runtime: `D:/MW3StriderRepair-20261023-r1/`.
Current capture derivative: `D:/MW3StriderCapture-20261023-r1/`.
Private checks and backups: `reports/strider-cockpit-repair-20261023/` and
`C:/Users/jcbla/MW34SunTests/strider-cockpit-repair-20261023/`.

All three replacement recordings pass their exact source frame counts:
1,680 / 1,680 / 3,120. Each logs the authenticated Strider interior omission.
Current menu/world resource bindings match across all three stages, global
normal mapping stays enabled, and diagnostic frame dumping is disabled. The
stock Strider texture identities have no authored relief bindings in the current
surface catalog. The approved opening, original MW3 music and matched Big Lake
sunset camera sequence are retained.

Both the 1440p60 master and 1080p60 posting copy contain 6,361 frames over
106.016667 seconds and pass full decoding. Reviewed the opening, transitions,
front/rear views and endpoint. The corrected video, thumbnail files and metadata
replace the six existing [Strider Drive files](https://drive.google.com/drive/folders/17nxAAx0oHmTmgE0pWQb4eV_baF0YvpOX)
in place; metadata readback verifies sizes and folder placement. The full master
is retained under `reports/strider-evolution-repair-20261023/strider/`. No ZIP
or YouTube publication was performed.

This advances detached-view presentation only. It changes no guest service,
simulation, collision, weapon or initialization contract and earns no native
acceptance credit. Strict acceptance remains 131/144. No commit or public
runtime/content-pack release is performed.
