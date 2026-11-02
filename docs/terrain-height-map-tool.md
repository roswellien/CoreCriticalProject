# Terrain height-map derivation tool

`tools/remaster-launcher/terrain_height_maps.py` is an offline deterministic tool
that derives metric scalar height maps from tangent-space normal maps via 2D
Frankot-Chellappa Poisson integration with optional high-pass colour luminance
refinement. It serializes validated `BWSFM1` environment surface-material sidecars
consumed by the runtime Vulkan POM renderer (`MW34_POM=1`).

Original textures, extracted media, and generated height-map images remain local
per `docs/legal.md`; only the tool implementation, test suite, and schema
definitions are committed.

## Architecture

1. **Slope integration**: tangent-space normals $(n_x, n_y, n_z)$ are converted to
   surface gradients $p = -n_x/n_z$ and $q = -n_y/n_z$. A 2D Fourier transform
   solves the least-squares Poisson equation $\nabla^2 z = \nabla \cdot (p, q)$
   with periodic boundary conditions matching texture wrap modes (`ADDRESS_WRAP`).
2. **Colour-guided refinement**: extracts high-frequency luminance detail
   via frequency-domain Gaussian high-pass filtering ($1 - \text{lowpass}$),
   suppressing macro lighting/shadows painted on legacy textures while retaining
   fine grain.
3. **Robust normalization**: percentiles $p_{0.5}$ and $p_{99.5}$ anchor $[0, 1]$
   scalar height to avoid single-texel gradient spikes, and the median value
   supplies the material's `height_reference`.
4. **Self-check quality audit**: finite central-difference gradients re-estimate
   normals $N_{\text{est}}$ to measure angular error and slope correlation against
   the input normal map.
5. **Contract serialisation**: records and RGBA8 scalar height images are packaged
   into `BWSFM1` sidecars via `surface_materials.pack_surface_materials` (up to
   512 images and 256 MiB per sidecar).

## Usage

### 1. Inventory candidate normals in a region

```powershell
python tools/remaster-launcher/terrain_height_maps.py inventory `
    --region training `
    --normals-manifest local/remaster/environment/authored.txt
```

### 2. Generate BWSFM1 terrain sidecar

```powershell
python tools/remaster-launcher/terrain_height_maps.py generate `
    --region training `
    --normals-manifest local/remaster/environment/authored.txt `
    --output local/remaster/environment/ground_surface_materials.bin `
    --report local/remaster/environment/height_quality_report.json
```

## Material families & parameters

| Family | Pattern keywords | Height amplitude | Max displacement | Colour weight |
| :--- | :--- | :--- | :--- | :--- |
| **cliff** | `txwall`, `cliff`, `bluff` | 0.50 | 0.50 | 0.10 |
| **rock** | `rock`, `boulder`, `stone` | 0.45 | 0.45 | 0.09 |
| **road** | `road`, `hwy`, `pave`, `path` | 0.20 | 0.20 | 0.05 |
| **asphalt**| `asphalt`, `tarmac`, `runway` | 0.18 | 0.18 | 0.04 |
| **sand** | `sand`, `dune` | 0.25 | 0.25 | 0.08 |
| **beach** | `beach`, `shore` | 0.22 | 0.22 | 0.07 |
| **terrain**| `txgter`, `ter`, `dirt`, `grass`| 0.35 | 0.35 | 0.08 |
| **default**| (fallback) | 0.30 | 0.30 | 0.06 |
