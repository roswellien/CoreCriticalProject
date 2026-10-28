# MW3 texture staging performance

The dev launcher now selects a native host with faster 16-bit texture staging.
It reduces the remaining first-use Training hitches without changing textures,
lighting, shadows, geometry or gameplay. Average throughput remains about the
same. Formal acceptance remains **131/144**.

## Before and after

Two matched on/off pairs, 4,600 measured intervals per setting, frames 400-2699:

| Metric | Before | After |
| --- | ---: | ---: |
| Average equivalent FPS | 77.06 | 77.54 |
| 1% low equivalent FPS | 32.12 | 34.31 |
| Mean frame interval | 12.98 ms | 12.90 ms |
| Worst frame interval | 62.54 ms | 51.14 ms |
| Intervals above 50 ms | 6 / 4,600 | 2 / 4,600 |
| Frame 1051, pair mean | 61.86 ms | 47.41 ms |
| Frame 1055, pair mean | 60.74 ms | 50.73 ms |
| Frame 1160, pair mean | 53.74 ms | 41.15 ms |

This is about **6.8% better 1% lows** and **18.2% less worst-frame time** on this
route. The less-than-1% average change is small relative to run variation and
does not establish a substantial sustained FPS increase. Hitches remain.

These are hidden-window equivalent render-throughput measurements, not displayed
gameplay FPS. Both conditions use the same executable, independent copied pilot
and configuration data, fixed 16.666667 ms diagnostic guest clock and real host
timestamps. Order: on/off/off/on. Settings: 3440x1440, FXAA, AF16, draw distance
1600, fog 1100, full lighting and fixture shadows, monitor on, replay off.
Existing normal, pipeline and world-texture warmups stay enabled.

## Cause and selected change

A private resource trace identifies the frame-1051 uploads as large cockpit
textures, including a 2048x2048 panel. Frames 1055 and 1160 also upload large
16-bit guest textures. CPU conversion takes approximately 10-17 ms at these
frames; completed GPU upload/mipmap intervals are approximately 1.0-1.6 ms.
CPU allocation, game work and shadow preparation also contribute. Inclusive
scene-construction timing must not be added to its measured subphases.

The existing renderer writes converted pixels individually into mapped GPU
upload memory, which may be write-combined. The selected helper expands the
same RGB565, ARGB1555 and ARGB4444 values through exact integer lookup tables,
converts into a small CPU buffer and copies contiguous blocks into staging.
It never reads mapped upload memory. Existing image allocation, resource
identity/version checks, GPU uploads and mip generation remain unchanged.

The lookup tables retain 0.75 MiB of CPU data; each conversion chunk holds
16 KiB. This change prepares no additional GPU textures. Initial mission-load
intervals, separate from launcher pack preparation, average 5.83 seconds off versus 5.95 seconds on in this cohort.
The 0.12-second difference is small relative to load variation; these runs do
not establish how much of it is caused by this change. Total peak process
RAM/VRAM was not profiled.

The launcher enables `MW34_TEXTURE_STAGING=1`; setting it to 0 restores the
prior conversion for diagnosis. The execution boundary improved is the live
native scene-to-Vulkan texture upload handoff. Original CPU render producers,
simulation and timing contracts are retained.

## Validation and retained trial

All 196,608 possible source color/alpha combinations across the three formats
match the old integer expansion. Chunk boundaries, zero length, unaligned output,
source preservation, output guards and an invalid format are checked with
asset-free fixtures. The installer reproduces the selected source exactly,
is idempotent and rejects a malformed anchor before writes.

Separate monitor-off on/off runs match all **2,800 complete draw-diagnostic rows**
and **seven full-resolution captures**, including frames 1051, 1055 and 1160.
The off control matches the prior world-texture-warmup host's draw records;
four captures from that host also match. All 2,800 non-timing per-present world-counter rows match
across all four timing runs. Diagnostic runs end at the expected 2,800-frame
budget, exit 1; this is not evidence of normal shutdown or mission completion.
The full launcher checks and 12 prepared-pack tests pass.

An earlier broad resident-texture warmup is rejected and retained privately.
Its 128 MiB extra nominal mip budget fills with earlier textures, leaving the
target hitches largely unchanged. It prepares 180 textures and skips 227; it is
not installed. The selected staging change avoids that additional residency.

Selected host: `gpu-native-texture-staging-controller-r1`, SHA-256
`6c45fc1c104c0c497de0465af42a70376576a678606deac3b7357afbc7a822fe`.
Only `vk_scene.hpp` changes from controller predecessor `d4395d19...`, plus the new authored
helper. Other host sources, shaders and the translated object list match.
Exact successor admissions preserve pack readers without adding a wildcard.
The selected base is the controller host. All controller input sources and its
pinned runtime are retained. The initial candidate used the earlier host; a normal
startup check rejected its stale source-snapshot reference before game launch.
That candidate was withdrawn, the controller profile restored, and this optimization
rebuilt and fully remeasured on the controller host. Both trials and the rejected
startup session are retained locally.
No commit or signed update package is made.

Private evidence: `local/work-ahead/performance-resources-20261022/`, including
matched timing results, resource diagnosis, all retained trials, fidelity hashes,
adapter/source checks, launcher checks and deployment backups.

## Next target

Fixture-shadow CPU preparation and Vulkan command recording remain candidates
for improving sustained throughput. The GPU already shades lighting and draws
shadow maps; the CPU selects lights/casters, computes bounds/transforms and
records commands. Some legacy vertex-lighting calculations also remain because
original clipping and material callbacks consume their outputs. Removing their
redundant work requires a validated earlier handoff. No geometry bypass or
shadow-quality reduction is introduced here. Broad campaign, combat, mission
reload and sustained gameplay validation remain open.

Normal-launch verification: session `fd10353638f545818012b13746876ec9`
prepares all 11 packs in 122 seconds, starts the exact selected host, renders
the intro and live enhanced menu, then exits normally with `ExitProcess(0)`
and coordinator exit 0. Controller input version 1 is retained. Saved settings
are byte-identical, including performance monitor off and replay off. The
updated launcher is left open and ready.
