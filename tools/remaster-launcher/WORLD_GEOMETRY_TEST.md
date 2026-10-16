# Original-world geometry development test

This is a bounded original static-mesh projection bridge, not a production
renderer setting. Read the [contract/results](../../docs/gpu-world-geometry-prototype-2026-10-15.md)
and [development plan](../../docs/gpu-geometry-development-plan.md).

Prerequisites: a fresh frozen host snapshot based on the stage1 geometry-profile
build, the existing native build toolchain and locally supplied game inputs.
Keep all translated code, media, snapshots and captures local. The published
Play profile must remain unchanged.

Compile the authored shader with the existing local compiler, then apply the
checked patch to the fresh snapshot and use its existing build procedure:

```powershell
python tools/remaster-launcher/compile_world_shader.py `
  --compiler local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe `
  --binary local/gpu-world-geometry-r1/world.vert.spv
python tools/remaster-launcher/apply_world_geometry.py <fresh-host-source>
```

The prototype requires `MW34_GPU_MODELS=1`, `MW34_GPU_WORLD=1`, and an explicit
`MW34_WORLD_LOG` JSONL output path. Missing/invalid configuration or unknown
required geometry contracts fail visibly. Names `ter`, `wall`, `healthy` select
only the initial known experiment; other meshes keep their existing drawing.
This is not a name-based building/terrain classifier. Do not add a production
settings toggle or enable by default from this evidence.

The existing private-save harness was copied to
`local/gpu-world-geometry-r1/run-world.ps1`; its new `-GpuWorld` switch sets those
two world variables. It protects user save/registry hashes and refuses another
active game. The retained test command is:

```powershell
& local/gpu-world-geometry-r1/run-world.ps1 `
  -Scenario IA -Build play -Name world-r2-walk `
  -Executable D:/Projects/MW34Recomp/local/remaster/gpu-native-world-geometry-r2/build/entry_commandline.exe `
  -DrawDistance 1600 -Frames 1400 -Visible `
  -RemasterAssets OriginalModels -RemasterWidth 3440 `
  -GpuHud -GpuModels -GpuWorld -AA fxaa -AF 16 `
  -FrameDump 1000 -HiresDumps '600,900,1100,1300' `
  -CandidateEnvironment local/terrain-distance-investigation-r1/current-model-environment.json `
  -InputScript local/terrain-distance-investigation-r1/ia-distance-yaw.txt
```

Use fresh names for new runs. Omit `-GpuWorld` for the disabled control. Compare
original draw hashes, scene/clock sequences, screenshots and logical readback;
require real executed-world counts, not just queued geometry. Budget exceptions
are deliberate test termination and do not establish normal quit.

The authored C++ fixture includes `vk_scene.hpp` from the patched private host.
It needs the project's existing Vulkan headers, Windows C++20 toolchain and
Vulkan driver, but no original game/media. Compile with the patched host directory
and Vulkan include directory on the include path; link `user32.lib`.
The retained local compiler invocation and output are in
`local/gpu-world-geometry-r1/check-world.ps1` and `fixture.log`.

It tests raw-position GPU projection, nonzero original-attribute offsets,
switching back to TL geometry, and static cache reuse. It does not test malformed
original mesh inputs, normal-map orientation, off-camera casters or gameplay.
The current live prototype bounds/validates mesh arrays and indices before use;
broader decoder and lifetime adverse tests remain required before production.

## Direct polygon binding follow-up

`apply_world_direct.py <fresh-host-source>` applies to a fresh copy of the patched
world-r2 snapshot. It adds `world_direct_stage.inc` and `world_binding.hpp`,
reuses the existing shader/resources, and replaces the polygon search with the
original frame's current-polygon pointer. Source byte snapshots guard cached
metadata; the linear projection audit and original producers remain active.
No additional production setting is introduced.

The portable fixture has no Windows, Vulkan or game dependency:

```text
c++ -std=c++20 tools/remaster-launcher/test_world_binding.cpp -o test_world_binding
```

Run the resulting executable. It checks actual cache mutation/reuse, capacity
accounting/rejection integrity and source polygon bounds. The GPU fixture above
also passes against the direct-binding snapshot. Local Windows invocations are
retained in `local/gpu-world-direct-r1/check-binding.ps1` and `check-world.ps1`.

The same private game harness now lives in `local/gpu-world-direct-r1/run-review.ps1`;
use fresh run names and the direct-r2 executable for new runs. `benchmark.ps1`
retains four alternating search/direct runs; `validation.json` records the results
and the first divergent disabled control rather than silently discarding it.
See [direct-binding results and limits](../../docs/gpu-world-direct-binding-2026-10-15.md).

## Cached triangles and fast binding

`apply_world_fast.py <fresh-host-source>` applies to a fresh copy of direct-r2.
It caches triangulated geometry per exact source revision. Add
`MW34_WORLD_FAST_BINDING=1` to omit the bridge's projection audit only for its
explicit unchanged textured-polygon contract. Unsupported paths keep the audit.
Original CPU projection and callbacks still execute. Do not enable this in Play.

`test_world_fast_binding.cpp` is an asset-free C++20 admission fixture; compile
and run as for the portable binding test. The GPU fixture also runs against the
new snapshot. Retained private-save runs use
`local/gpu-world-fast-r1/run-review.ps1 -GpuWorld -FastBinding` and fresh names.
Omit `-FastBinding` to exercise the cached-triangle audited control; omit
`-GpuWorld` for the disabled control. Use separate capture and timing runs.
See [contract and results](../../docs/gpu-world-fast-binding-2026-10-15.md).
