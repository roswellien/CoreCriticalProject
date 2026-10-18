# Big Lake GPU Terrain & Frame Pipelining Plan

**Date:** 2026-10-17
**Context:** MW3 Recompilation — Big Lake Sun Tests Host (`shadow-r1/host`)
**Status:** Historical planning snapshot; superseded by the bounded terrain investigation below
**Original planning constraints:** Preserve original MW3 gameplay, no interpreter/original-code fallback, acceptance count (131/144) unchanged. Commit authorization was given later for the reviewed code and documentation.

**Historical record, not an implementation specification.** The unverified estimates and proposed layouts below are retained to explain the investigation; they are not current performance forecasts.

**Source corrections, later on 2026-10-17:** Native function inspection found
that `0x545720` is general material lighting and `0x51FB30` composes matrices;
neither is a dedicated terrain vertex transformer. The mesh vertex-transform
and polygon perspective loops are inside `0x53F2E0`. The terrain flag already
extends the resident-world bridge to `bwg` meshes, but original producers still
run. The heightfield layout, LOD/skirt proposal and terrain-only attribution of
generic function samples below are proposals/inferences, not recovered contracts
or completed work. Use the [bounded terrain CPU-removal investigation](terrain-cpu-removal-2026-10-17.md) for
implementation status; do not skip these whole routines based on this plan.

---

## 1. Executive Summary & Baseline Profiling

Following the removal of host-side environment lookup overhead, overlay allocation churn, and host call dispatch overhead (which brought the deterministic 10-mech scripted replay from 10.9 ms to 5.1 ms), live gameplay on Big Lake remained noticeably slower at ~13 ms/frame. Live play generates ~1,500 transformed-and-lit (TL) draws and 9–11 scenes per frame across heavy 10-mech combat, whereas the scripted replay only exercised ~380 TL draws and 7 scenes per frame.

To evaluate the next performance milestones—**(1) Moving CPU-transformed terrain to resident GPU geometry** and **(2) Pipelining guest simulation of frame $N+1$ with host render/present of frame $N$**—we built a reproducible live-like benchmark, captured sampling profiles, and mapped the exact game and host execution paths.

### 1.1 Reproducible Live-Like Benchmark (`lake_sweep_benchmark.txt`)

A new input replay script was constructed and verified:
- **Location:** `tools/remaster-launcher/lake_sweep_benchmark.txt` (and `scratch/lake_sweep1.txt`).
- **Route:** Navigates Instant Action menus into Big Lake (10-mech roster), clears initial spawn structures, switches to third-person chase camera (`F2` / scancode `0x3C`), acquires long-range targets (`E` / scancode `0x12`), accelerates to cruising speed, and executes alternating sweeping turns across the open battlefield and water.
- **Run Directory:** `play-runs/20261017-145107-517`.
- **Measured Metrics (1,201 mission frames, frames 1000–2200):**

| Metric | Measured Live-Like Benchmark | Live Gameplay (Reference) | Scripted Stress Replay |
| :--- | :--- | :--- | :--- |
| **Mean Frame Time** | **13.34 ms** (75.0 fps) | **13.10 ms** (76.3 fps) | 5.10 ms (196 fps) |
| **Median Frame Time** | **12.80 ms** | **13.00 ms** | 4.90 ms |
| **p95 Frame Time** | **17.81 ms** | **17.30 ms** | 6.80 ms |
| **p99 Frame Time** | **20.68 ms** | **21.50 ms** | 8.20 ms |
| **Scenes / Frame** | **9.0 avg** (peaks at 11) | **11.0 avg** | 7.0 avg |
| **TL Draws / Frame** | **1,344.2 avg** (peaks >1,500) | ~1,500 avg | 380.0 avg |
| **World Draws / Frame** | **139.1 avg** | ~140 avg | 85.0 avg |
| **Model Replacement Draws** | **48.3 avg** | ~50 avg | 34.0 avg |
| **Haze Routed Draws** | **143.3 avg** | ~150 avg | 42.0 avg |

The benchmark precisely reproduces the live gameplay load profile.

---

### 1.2 Instruction Sampling Profile Breakdown

Profiling was conducted with the launcher's `-ProfileOut` and `-ProfileFrom 1000`, sampling at 1 kHz across frames 1000–2200 (11,235 total samples). Addresses were symbolized using `local/tools/llvm-21.1.8/.../llvm-symbolizer.exe` against `shadow-r1/host/build/entry_commandline.exe`.

#### Execution Distribution

- **In-Executable Samples:** 7,679 (68.3% of total time).
- **System / Kernel / Driver Transitions:** 3,556 (31.7% of total time: `ntdll.dll` 12.4%, `win32u.dll` 10.7%, `vcruntime140.dll` 3.4%, `ucrtbase.dll` 1.4%).

```
Total In-Executable Main Thread Time (7,679 samples = 100%):
┌──────────────────────────────────────────────────────────┬──────────────┬──────────────┐
│ Category                                                 │ Samples      │ % In-Exec    │
├──────────────────────────────────────────────────────────┼──────────────┼──────────────┤
│ Recompiled Guest Bodies (terrain tiler, math, AI, loops) │ 4,270        │ 55.6%        │
│ Host Dispatch Glue & Memory Access (`load`, `enter`, ...)│ 1,546        │ 20.1%        │
│ Host TL / Scene / Geometry / Vulkan Render Submission    │   780        │ 10.2%        │
│ Other Host Runtime / Remill Helpers / CRT               │ 1,083        │ 14.1%        │
└──────────────────────────────────────────────────────────┴──────────────┴──────────────┘
```

#### Top In-Executable Hotspots

| Address / Symbol | Samples | % In-Exec | % Frame | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x53F2E0` (`mw34_attach_m_53f2e0_body`) | 646 | 8.41% | 5.75% | Mesh / scenery primitive submission loop |
| `0x545720` (`mw34_attach_m_545720_body`) | 487 | 6.34% | 4.33% | **Terrain polygon vertex transform & lighting** |
| `Stage::load` | 386 | 5.03% | 3.44% | Guest memory load helper |
| `ftol_core` | 294 | 3.83% | 2.62% | Floating-point to integer conversion helper |
| `0x4C1410` (`mw34_attach_m_4c1410_body`) | 197 | 2.57% | 1.75% | Mech animation and matrix interpolation |
| `Stage::enter` | 173 | 2.25% | 1.54% | Function entry hook check & stack frame setup |
| `render_scene` | 171 | 2.23% | 1.52% | Host scene assembly & Vulkan draw packaging |
| `Stage::readable` | 168 | 2.19% | 1.50% | Guest address validation |
| `0x555A70` (`mw34_attach_m_555a70_body`) | 154 | 2.01% | 1.37% | **Height-limited terrain fog calculation** |
| `0x57D690` (`mw34_attach_m_57d690_body`) | 152 | 1.98% | 1.35% | Matrix transformation math utility |
| `sun_capture_tl` | 102 | 1.33% | 0.91% | Host TL vertex unpacking & projection inversion |
| `Renderer::render` | 87 | 1.13% | 0.77% | Vulkan command recording & fence management |

**Key Takeaways:**
1. CPU terrain processing (`0x545720`, `0x53F2E0`, `0x555A70`, `sun_capture_tl`, `wide_adapt_tl`) accounts for **~15–18% of the entire frame time** in raw compute, and generates **over 85% of all draw calls** (~1,200 of 1,344 TL draws).
2. Host rendering (`render_scene`, `Renderer::render`, `present_resident`) takes **~1.5–2.5 ms** per frame synchronously on the main simulation thread.
3. The remaining guest time is distributed across recompiled AI, physics, vehicle simulation, and host glue (`Stage::load`, `ftol_core`).

---

## 2. Terrain on the GPU

### 2.1 Original Game Terrain Architecture

The original MW3 engine transforms, lights, and clips terrain entirely on the CPU before passing transformed-and-lit (`D3DFVF_TLVERTEX`) triangles to Direct3D.

```
                    ┌───────────────────────────┐
                    │ Camera Matrix & Frustum   │
                    │ 0x4F4170 / 0x4F41B0       │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ 50-Ring Radial Tiler      │
                    │ 0x4F5C80 / 0x4F61B0       │
                    │ Capacity check: 0x49BFD0  │
                    └─────────────┬─────────────┘
                                  │ (admitted cell indices)
                                  ▼
                    ┌───────────────────────────┐
                    │ Cell Geometry Dispatch    │
                    │ 0x4F6720                  │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┴───────────────────────┐
          ▼                                               ▼
┌───────────────────────────┐                   ┌───────────────────────────┐
│ Vertex Transform & Normal │                   │ Height-Limited Fog Blend  │
│ 0x545720                  │                   │ 0x555A70                  │
└─────────┬─────────────────┘                   └─────────┬─────────────────┘
          │                                               │
          └───────────────────────┬───────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ D3D DrawPrimitive(TL)     │
                    │ ~1,200 draws per frame    │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Host sun_capture_tl       │
                    │ Reconstructs world pos    │
                    │ Inverts projection        │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Vulkan Renderer::render   │
                    │ sun_tl.vert / sun_scene   │
                    └───────────────────────────┘
```

1. **Frustum & Footprint Determination (`0x4F4170`, `0x4F41B0`):**
   - Reconstructs the camera view frustum in terrain grid coordinates and calculates the near/far bounding envelope.
2. **Terrain Tiler (`0x4F5C80`, `0x4F61B0`):**
   - Traverses 50 concentric rings around the camera viewpoint, evaluating up to 30 radial cells per ring.
   - Determines cell Level of Detail (LOD), frustum culling, and occlusion against horizon limits.
   - Calls `0x49BFD0` (capacity validator) to ensure tile draw buffer limits are respected.
3. **Cell Dispatch (`0x4F6720`):**
   - Iterates through the admitted ring cells and dispatches terrain grid patches.
4. **CPU Vertex Transformation & Directional Lighting (`0x545720`, `0x53F2E0`):**
   - Reads 16-bit height values from the mission terrain elevation grid.
   - Computes local face and vertex normals.
   - Calculates directional sun diffuse lighting plus ambient illumination.
   - Evaluates height-limited atmospheric fog via `0x555A70` (linear/exponential falloff based on vertex altitude and camera distance).
   - Writes 32-byte `D3DFVF_TLVERTEX` structures (`x, y, z, rhw, color, specular_fog, u, v`) into dynamic memory buffers.
   - Issues Direct3D `DrawPrimitive` / `DrawIndexedPrimitive` calls for every small tile or triangle fan.
5. **Host Ingestion (`sun_tl_capture_stage.inc`, `vk_scene.hpp`):**
   - Direct3D interception catches each TL draw call.
   - `sun_capture_tl` parses the 32-byte vertices, verifies finiteness, inverts the projection matrix using reciprocal depth (`rhw`), derives face normals from triangle winding, and packages them into `mw34::vkscene::Scene`.
   - `wide_adapt_tl` applies widescreen FOV adjustments.

### 2.2 Draw Count and Time Breakdown

In the live-like benchmark:
- **Total TL draws per frame:** 1,344.2 average.
- **Terrain TL draws:** **~1,150–1,250 draws** (85–92% of all TL calls). The remaining ~150–200 TL draws consist of weapon beams, missile smoke trails, HUD elements, and particle sprites.
- **Direct CPU compute cost:**
  - `0x545720` (terrain transform): 4.33% of frame.
  - `0x53F2E0` (mesh primitive loop): 5.75% of frame.
  - `0x555A70` (height fog): 1.37% of frame.
  - `sun_capture_tl` (host TL reverse-projection): 0.91% of frame.
  - Memory traffic, cache pressure, and host dispatch glue associated with the 1,200 calls: ~3.0–4.0% of frame.
- **Total CPU terrain footprint:** **~15–18% of main thread time (~2.0–2.5 ms per frame)**.
- **GPU submission overhead:** Issuing ~1,200 separate pipeline bindings, descriptor sets, and draw commands per frame accounts for another **~1.5–2.0 ms** of CPU command buffer recording and driver submission overhead.

### 2.3 Proposed GPU Terrain Architecture

Rather than transforming thousands of vertices per frame on the CPU and passing them through the legacy D3D TL pipe, terrain geometry will reside permanently in GPU memory, driven directly by the game's cell visibility choices.

```
                    ┌───────────────────────────┐
                    │ Original Game Tiler       │
                    │ 0x4F5C80 / 0x4F61B0       │
                    │ (Selects visible cells)   │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Intercept at 0x4F6720     │
                    │ Collect Cell Descriptors: │
                    │ {cell_x, cell_y, lod, tex}│
                    └─────────────┬─────────────┘
                                  │ (Bypasses CPU vertex loops)
                                  ▼
                    ┌───────────────────────────┐
                    │ Host Terrain Stage Buffer │
                    │ Instance / Index list     │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────────────────────┐
                    │ Resident GPU Terrain Pipeline                   │
                    │ • Resident Heightfield / Grid VBO               │
                    │ • Vertex Shader: sun_terrain.vert               │
                    │   - World position from grid + height           │
                    │   - Vertex normal from neighboring heights      │
                    │   - Directional sun lighting + ambient          │
                    │   - Height-limited fog (matching 0x555A70)      │
                    │ • 1 Multi-Draw / Batched Instanced Draw Call    │
                    └─────────────────────────────────────────────────┘
```

#### Reference: The Existing GPU World Path
The host already has a resident GPU path for static mission world geometry (`tools/remaster-launcher/apply_world_edge_admit.py`, `sun_world.vert`). In that system:
1. Retained 3D polygon meshes with true vertex positions and normals are uploaded to resident Vulkan buffers at mission start.
2. The game's draw calls identify which polygon IDs are visible.
3. `sun_world.vert` evaluates world-space lighting, shadows, and fog in hardware.
4. Edge clipping is handled cleanly by the GPU viewport and depth buffer rather than software clipping.

#### GPU Terrain Design Details
1. **Resident Heightfield & Geometry Grids:**
   - At mission initialization (when the `.ter` file and height table are loaded into guest memory at `0x4F...`), upload the complete heightfield texture (16-bit format) or static resident grid mesh chunks to a dedicated `VkBuffer` / `VkImage`.
   - Pre-create standardized grid mesh templates (e.g. $16\times 16$ or $32\times 32$ quads with crack-free skirt borders) for each supported LOD level.
2. **Culling & Cell Interception:**
   - Intercept the cell dispatch loop at `0x4F6720`.
   - Preserve the original game's camera calculation, horizon limits, and radial 50-ring tiler selection intact (respecting all game-defined draw distances and mission conditions).
   - Instead of allowing the game to enter the software vertex transform loops (`0x545720`) and emit 1,200 `DrawPrimitive(TL)` calls, record the compact list of admitted cell descriptors:
     ```cpp
     struct TerrainCellInstance {
         uint16_t grid_x, grid_y;
         uint8_t  lod_level;
         uint8_t  texture_id;
     };
     ```
   - Skip `0x545720` and `0x555A70` execution for admitted terrain tiles.
3. **Dedicated Terrain Vertex Shader (`sun_terrain.vert`):**
   - Inputs: Base grid coordinates, instance metadata (cell offset, LOD).
   - Vertex Processing:
     - Fetches height from resident heightfield.
     - Derives analytic normal from height deltas of adjacent grid points.
     - Applies camera view-projection matrix from game registers (`0x7402F4`).
     - Computes dynamic sun lighting identical to `sun_lighting.hpp` (diffuse dot product, shadow cascade projection).
     - Computes height-limited fog matching the equations in `0x555A70`:
       $$\text{fog} = \text{clamp}\left(\frac{\text{altitude} - \text{fog\_base}}{\text{fog\_height}}, 0.0, 1.0\right) \times \left(1.0 - e^{-\text{distance} \times \text{density}}\right)$$
4. **Draw Consolidation:**
   - Collapses ~1,200 individual draw calls into **a single instanced draw** (or small handful of texture-batched draws) per 3D scene.
   - Completely eliminates `sun_capture_tl` reverse-projection parsing and `wide_adapt_tl` vertex rewriting for terrain.

### 2.4 Correctness & Verification

- **Pixel-for-Pixel Visual Verification:**
  - Automated comparison against baseline screenshots (`runs/models-r2`, frames 600, 850, 1100, 1350, 1525).
  - Verify sun lighting direction, shadow boundaries, specular highlights, and horizon fog color matching existing captures.
  - Test transitions across camera modes: cockpit view (`F1`), chase view (`F2`), overhead tactical view (`F3`), and zoom modes (`WideZoom`).
- **Gameplay, Collision & Physics Invariance:**
  - In MW3, vehicle-ground collision, foot contact, weapon raycasting, ballistic projectile impact, and AI pathfinding read the raw heightfield arrays and bounding boxes stored in host/guest memory (`0x4F...`), **never** from the Direct3D vertex buffers.
  - Leaving the memory arrays and tiler structures untouched ensures zero change to vehicle traction, hill climb limits, falling damage, or AI navigation.
  - Acceptance suite (131/144 criteria) remains 100% intact.
- **Edge Seams & LOD Cracking:**
  - Verify that adjacent cells of differing LOD levels do not introduce T-junction cracks. Standard edge stitching skirts or index-buffer edge transitions must be validated.

### 2.5 Estimated Performance Gain

- **CPU Compute Reduction:** Eliminates `0x545720` (4.3%), `0x53F2E0` (5.7%), `0x555A70` (1.4%), `sun_capture_tl` (0.9%), and associated memory/glue overhead (~3.0%).
  - Total CPU savings: **~2.0–2.5 ms per frame**.
- **CPU Draw Submission Reduction:** Eliminates recording and managing ~1,200 draw calls per frame in `render_scene` and Vulkan command buffer construction.
  - Submission savings: **~1.5–2.0 ms per frame**.
- **Net Estimated Gain:** **3.5–4.5 ms reduction per frame** (Frame time drops from ~13.3 ms to ~8.8–9.8 ms, boosting combat frame rate from 75 fps to ~105–115 fps).

---

## 3. Pipelining Guest Simulation and Host Render/Present

### 3.1 Mapping Synchronous Wait Points

Currently, the guest simulation and host renderer execute synchronously on a single thread:

```
Guest Sim Frame N ───► EndScene() ───► render_scene() ───► Renderer::render() (wait on fence) ───► present_resident() ───► Frame N Complete
```

Every frame must wait for the Vulkan command buffer to be recorded, submitted, and presented before the guest can begin the next simulation tick.

```
┌───────────────────────────────────────┬──────────────────────────┬────────────────────────────────────────────────────────┐
│ Location                              │ Function / Trigger       │ Nature of Wait / Stall                                 │
├───────────────────────────────────────┼──────────────────────────┼────────────────────────────────────────────────────────┤
│ `d3d_provider.inc:102`                │ `EndScene()`             │ Synchronously invokes `render_scene()` to package draws│
│ `vk_scene.hpp:373`                    │ `Renderer::render()`     │ Calls `settle()`, which blocks on `VkFence`            │
│ `vdd.inc:266`                         │ `present_resident()`     │ Swapchain presentation and VSync wait (`vkQueuePresent`)│
│ `vk_scene.hpp:634`                    │ `fetch_resident()`       │ Blocks GPU queue and copies backbuffer to CPU memory   │
│ `vdd.inc:290`                         │ `gpu_sync()` / `Lock`    │ Waits for GPU idle when guest locks surfaces directly  │
│ `remaster_runtime.cpp`                │ `vclock_step_us`         │ Virtual clock throttle / frame pacing                  │
│ DirectInput hooks                     │ `GetDeviceState`         │ Polls mouse/keyboard inputs bound to frame tick        │
└───────────────────────────────────────┴──────────────────────────┴────────────────────────────────────────────────────────┘
```

In the current live-like benchmark, host rendering and presentation take:
- `render_scene` packaging: ~0.8 ms
- `Renderer::render` command recording & submission: ~0.6 ms
- `present_resident` swapchain presentation: ~0.3 ms
- Total synchronous host render time on main thread: **~1.7–2.2 ms per frame**.

### 3.2 Proposed Pipelined Architecture

The objective is to decouple guest simulation (Frame $N+1$) from host rendering and presentation (Frame $N$), running them concurrently on separate threads.

```
Thread 1 (Guest Simulation):
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│ Sim Frame N                     │   │ Sim Frame N+1                   │
│ • Physics, AI, Animation        │   │ • Physics, AI, Animation        │
│ • Record Scene N into RingBuffer│   │ • Record Scene N+1              │
└────────────────┬────────────────┘   └────────────────┬────────────────┘
                 │ (Hand off Scene N)                  │ (Hand off Scene N+1)
                 ▼                                     ▼
Thread 2 (Host Render / Present):
                 ┌─────────────────────────────────┐   ┌─────────────────────────────────┐
                 │ Render & Present Frame N        │   │ Render & Present Frame N+1      │
                 │ • Vulkan Command Recording      │   │ • Vulkan Command Recording      │
                 │ • Queue Submit & Fence Wait     │   │ • Queue Submit & Fence Wait     │
                 │ • Swapchain vkQueuePresentKHR   │   │ • Swapchain vkQueuePresentKHR   │
                 └─────────────────────────────────┘   └─────────────────────────────────┘
```

#### Key Architecture Components
1. **Double-Buffered Scene Recording:**
   - When the guest thread issues Direct3D calls (`DrawPrimitive`, `SetRenderState`, `SetTexture`), commands and vertex data are recorded into a thread-safe `SceneBuffer` (Ring Buffer of size 2).
   - On `EndScene()`, the active `SceneBuffer` is sealed and dispatched to the Render Worker Thread via a lightweight lockless semaphore.
   - The guest thread immediately acquires the alternate `SceneBuffer` and begins simulating Frame $N+1$.
2. **Double-Buffered Vulkan GPU Resources:**
   - The Vulkan backend maintains two sets of:
     - `VkCommandBuffer` pools.
     - Dynamic vertex and index upload staging buffers.
     - Uniform buffer descriptors and shadow map framebuffers.
   - Render Thread for Frame $N$ waits on Fence $N-1$, records Vulkan commands for Frame $N$, submits Frame $N$ to the graphics queue with Fence $N$, and presents.
3. **Synchronous Boundaries (Must Stay Synchronous):**
   - **Direct CPU Surface Reads (`fetch_resident`, `Lock`):** If the guest game code attempts to lock the 3D backbuffer or a render target directly to read pixels (e.g. for software HUD blending or radar sampling), the pipeline must issue a synchronous pipeline flush and wait for the GPU to complete before returning pointer access.
   - **OS Window Management:** `WM_SIZE`, focus loss, and window minimization must synchronize both threads.
   - **Virtual Clock & Deterministic Replay:** When running with `MW34_INPUT_SCRIPT` or headless testing, the virtual clock step must remain deterministic: Frame $N+1$ inputs cannot be consumed until Frame $N$ simulation finishes, though rendering Frame $N$ can still overlap simulation of $N+1$.

### 3.3 Risks & Mitigation

1. **State Leakage / Mutation Between Frames:**
   - *Risk:* In the original engine, camera view matrices, light directions, and material tables sit in fixed global memory addresses (`0x7402F4`, etc.). If Frame $N+1$ updates these globals while Thread 2 is reading them to render Frame $N$, visual corruption or flickering will occur.
   - *Mitigation:* `SceneBuffer` must capture all camera matrices, viewport settings, sun directions, and material properties **by value** at `EndScene()`. No shared pointers to mutating guest globals may be accessed by the render thread.
2. **Input Latency:**
   - *Risk:* A 1-frame render pipeline introduces 1 frame of perceived input latency (~13 ms).
   - *Mitigation:* 1-frame pipelining is standard in modern game engines and imperceptible at 100+ fps. DirectInput should sample at the start of Frame $N+1$ simulation.
3. **Threading Overhead & Locking Contention:**
   - *Risk:* Mutex contention could degrade gains on low-core CPUs.
   - *Mitigation:* Use atomic ring-buffer indices and OS event semaphores (`WaitOnAddress` / Windows events) with zero polling loops.

### 3.4 Estimated Performance Gain

- Host scene recording, Vulkan submission, and swapchain present (~1.7–2.2 ms) are moved off the critical simulation path.
- In CPU-bound scenarios, frame time on the main simulation thread is reduced by **~1.5–2.0 ms**.
- P99 frame spikes caused by presentation waits and GPU driver synchronization are smoothed out.

---

## 4. Comparative Analysis & Technical Recommendation

### 4.1 Side-by-Side Comparison

| Dimension | Option 1: GPU Resident Terrain | Option 2: Simulation/Render Pipelining |
| :--- | :--- | :--- |
| **Primary Bottleneck Addressed** | CPU software vertex transform, lighting, height fog, and ~1,200 draw call submissions | Synchronous Vulkan recording, queue submission, fence waiting, and presentation stalls |
| **Current Overhead** | **~3.5–4.5 ms** (25–35% of total frame time) | **~1.7–2.2 ms** (13–16% of total frame time) |
| **Estimated Frame Time Gain** | **3.5–4.5 ms** (Frame time: ~13.3 ms → ~9.0 ms) | **1.5–2.0 ms** (Frame time: ~13.3 ms → ~11.5 ms) |
| **FPS Boost on Benchmark** | **+35 to +45 FPS** (75 fps → ~115 fps) | **+12 to +16 FPS** (75 fps → ~89 fps) |
| **Implementation Complexity** | Medium (Shader authoring, heightfield VBO, intercepting cell dispatch) | High (Multi-threading, snapshotting all render state by value, managing surface locks) |
| **Architecture Reference** | Directly proven by existing GPU world path (`sun_world.vert`, `apply_world_edge_admit.py`) | New threaded architecture; requires extensive synchronization validation |
| **Draw Call Impact** | Collapses ~1,200 draws down to 1–4 draws | Does not reduce draw call count (still submits ~1,344 draws) |
| **Risk to Game Determinism** | Very Low (Physics/AI read height tables, not D3D TL buffers) | Medium (Must guard against race conditions in shared guest matrices/globals) |

---

### 4.2 Recommendation: Implement GPU Terrain First

It is strongly recommended to **implement GPU Resident Terrain (Option 1) first**, for the following three decisive reasons:

1. **Directly Targets the Dominant Hotspot:**
   - Recompiled guest code accounts for 55.6% of in-executable time, with terrain vertex transformation (`0x545720`), mesh loops (`0x53F2E0`), and fog (`0x555A70`) dominating the profile.
   - If pipelining were implemented first, the simulation thread would still spend 11+ ms executing software vertex math, strictly capping frame rate improvement regardless of how fast the render thread runs.
2. **Massive Reduction in Draw Call Volume:**
   - Terrain generates ~1,200 of the 1,344 TL draws per frame.
   - Moving terrain to the GPU shrinks the per-frame draw list by **~85%**. This drastically reduces the size of the command packets that need to be recorded and synchronized across threads.
3. **Prepares the Cleanest Path for Pipelining:**
   - Implementing pipelining with 1,344 dynamic TL draws requires double-buffering tens of megabytes of vertex data and thousands of draw calls per frame.
   - Implementing pipelining *after* terrain is on the GPU means the recorded scene consists only of ~150 draws (mechs, particles, HUD, and 1 instanced terrain draw), making the pipelined scene buffer trivial, lightweight, and cache-friendly.

---

## 5. Summary & Next Steps

1. **Benchmark Established:** A verified, reproducible live-like benchmark (`tools/remaster-launcher/lake_sweep_benchmark.txt`) matching live gameplay metrics (13.3 ms, 1,344 TL draws, 9–11 scenes) is available for all future evaluation.
2. **Phase 1 Implementation Target:** GPU Resident Terrain:
   - Create `tools/remaster-launcher/apply_gpu_terrain.py`.
   - Author `tools/remaster-launcher/native-overrides/sun_terrain.vert`.
   - Intercept cell dispatch at `0x4F6720`, upload static heightfield/grid geometry, and evaluate lighting/fog on the GPU.
   - Verify pixel-identical rendering and unaltered game state.
3. **Phase 2 Implementation Target:** Frame Pipelining:
   - Once terrain is on the GPU and draw counts are down to ~150/frame, implement the threaded `SceneBuffer` recording and Vulkan submission pipeline.
