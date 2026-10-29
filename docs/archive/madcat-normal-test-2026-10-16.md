# Mad Cat normal mapping test (Big Lake directional sun)

Authorized 2026-10-16. Tangent-space normal mapping has been implemented and validated on ONE GPU replacement mech (**Mad Cat**, `MW34_MADCAT_MESH` / `MW34_MADCAT_TEXTURES`) in the isolated Big Lake test instance (`Play MW3 - Big Lake Sun Tests`).

## Summary of Results

1. **Flat-Normal Equivalence Proven**:
   - `normal-flat` (normal map bound, normal strength 0.0, sun 225°) was compared against `final-sun` (sun 225°, unperturbed baseline without normal maps).
   - Frame 600 capture (`target-600.ppm`, SHA256: `349fde567924ad0bd3f422e54d9541e40e8c4f40995c5a6fe14e93cd5b3edb95`) matches byte-for-byte.
   - Frame 900 capture (`target-900.ppm`, SHA256: `70864a3117e167f97cfe0befafee6f4e8c93725bf261d807c2ae2a17e9aa4b61`) matches byte-for-byte.

2. **Directional Surface Detail on Mad Cat Geometry**:
   - In `normal-calibrated` (strength 1.0, sun 225°), exactly 9,555 pixels (0.19% of the scene) differ from flat baseline, localized entirely to the Mad Cat replacement mesh panels (bounding box X: [1044, 2340], Y: [598, 1439]).
   - Terrain, hills, sky, and water remain completely unchanged.
   - Canopy glass exception is preserved: material 3 (`Window`) is authored flat `(128, 128, 255, 255)` in the normal binary sidecar and receives no perturbation.

3. **Opposite Sun Angle and Diagnostics**:
   - `normal-opposite` (sun 45°, strength 1.0) alters 2,584,396 pixels across the scene and reverses the illumination of the Mad Cat's angled torso and missile pods.
   - `normal-diag` (SunNormals diagnostic) renders world-space normals directly, verifying that screen-space derivative $TBN$ vectors remain invariant under camera rotation.

4. **Simulation Fidelity and Performance**:
   - All 4 test cases (`normal-flat`, `normal-calibrated`, `normal-opposite`, `normal-diag`) reached their 1,000-frame presentation budget.
   - Draw records (draw calls and hashes) match baseline across all 1,000 frames identically (`recs == base_recs: True`).
   - Cumulative draw calls at frame 1,000: 109,850 retained-world, 326,095 TL receiver, and 21,877 replacement-model draws across all runs.
   - Average 3D frame time on AMD Radeon RX 9070 is ~9.88 ms (calibrated) vs ~10.20 ms (flat) (~100 FPS), demonstrating negligible GPU overhead.

## Test Artifacts and Location

- Packaged sidecar: `C:\Users\jcbla\MW34SunTests\big-lake-r1\assets\madcat-normals.bin` (50,364,824 bytes, binary tag `BWNRM1\0\0`).
- Comparison images:
  - 2x2 crop grid (cockpit & torso): `C:\Users\jcbla\MW34SunTests\big-lake-r1\comparisons-madcat-normals\madcat-normals-crop-comparison.png`
  - 3440x1440 full frame comparison: `C:\Users\jcbla\MW34SunTests\big-lake-r1\comparisons-madcat-normals\madcat-normals-full-comparison.png`
  - Individual frame captures: `C:\Users\jcbla\MW34SunTests\big-lake-r1\captures-madcat-normals\normal-*-600.png` and `normal-*-900.png`
- Host binary: `C:\Users\jcbla\MW34SunTests\big-lake-r1\host\build\entry_commandline.exe` (SHA256: `19e28686bed63f70ec0bfaa9dd963d86735e0dcc430b31b02f73b85b1f8f5b11`).
- Launcher profile: `local/remaster/big-lake-sun-tests.json` updated with executable hash and `MW34_MADCAT_NORMALS`.

## Operational Boundaries

All changes remain strictly confined to `C:\Users\jcbla\MW34SunTests\big-lake-r1\`. Existing Remaster and Alpha profiles, campaign saves, and user pilots remain untouched. No git commits were made; uncommitted work is preserved. Formal acceptance remains **131/144**.
