# Instant Action environment baselines — 2026-10-19

The current Material Normal Preview was tested on all four environments exposed
by the copied pilot's Instant Action menu: Big Lake, Grasslands, Rolling Hills
and Gorge. This expands live native map coverage; no renderer implementation,
lighting layout, material asset, playable profile or executable was changed.
Formal acceptance remains 131/144.

## Settings and method

Ryzen 7 9700X, Radeon RX 9070, driver 32.0.31035.1003. The installed host is
SHA-256 7fa3ef53000c11df73a6d98e48e73a98f45f3b4a4bfb0a58e2f0f26a0ffb8610.
Use 3440×1440, FXAA, AF16, scenery distance 1200, fog distance 1100 and the
launcher's resolved sunset preset: sun elevation 9°, strength 1.6. World normal
strength remains 1.5. Sun shadows and replay video are off. The existing
game-state snapshot recorder remains on. This is a baseline of the current
global lighting configuration, before per-map point/spot lighting work.

Each run starts with a fresh private game/pilot/registry copy and uses the
original Instant Action menus. The setup is Battle, Mad Cat commander, one
Bushwacker enemy, no MFB and no lancemates. Timed views remain at spawn; original
AI, weather and fire effects continue. Real simulation time and visible Vulkan
IMMEDIATE presentation are used, with VSync off. These are application frame
rates, not monitor refresh rates or GPU-only timings.

Eight runs use forward/reverse map order: Big Lake, Grasslands, Rolling Hills,
Gorge, Gorge, Rolling Hills, Grasslands, Big Lake. Each presents 5000 frames.
Frames 2001–4800 supply 2800 wall-clock frame intervals per run, 5600 per map,
22400 total. The preceding menus/loading/warmup are excluded. Screenshot runs
are separate; final proof captures at frame 5000 are outside the measurement
window. Original frame-time/world/model logging remains enabled.

## Results

Average FPS is total measured frames divided by their total wall time. The
1% low is 1000 divided by the mean of the slowest 1% of frame times. Percentiles
and 1% lows below pool both runs; the range shows the two individual average FPS
values. Hitches are retained rather than trimmed.

| Map | Average FPS | Repeat FPS range | 1% low FPS | p99 frame ms | Frames >33.33 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Big Lake | 143.0 | 140.3–145.8 | 60.1 | 12.85 | 1 |
| Grasslands | 98.1 | 96.4–99.7 | 47.8 | 16.67 | 2 |
| Rolling Hills | 170.7 | 160.7–182.0 | 81.6 | 11.42 | 0 |
| Gorge | 115.4 | 114.2–116.6 | 65.7 | 14.79 | 0 |

Big Lake's first pass includes a 199 ms frame; Grasslands' first pass includes
a 182 ms frame and another frame above 33 ms. Neither repeats a >33 ms frame
in its second pass. Their causes were not profiled in this baseline. Rolling
Hills varies more between repeats, and its first final capture contains much
more foreground flame than its second. Do not attribute that spread to lighting
cost. Original AI and effect activity are not deterministic across these runs.
Replacement-model logs also show that enemy visibility differs between passes;
the player Mad Cat replacement is queued in every case. These are repeat ranges
for live scenarios, not identical fixed-scene microbenchmarks.

Every measured frame submits six scenes on the first three maps; Gorge submits
seven and visibly renders rain. Peak process working sets span approximately
2981–3642 MiB across the eight runs; this measures process RAM, not VRAM.
All eight reach the expected presentation-budget stop with gameplay still
visible in the final image. This is neither normal quit nor mission completion.

## Visual record and limits

Grasslands shows the industrial compound and vegetation. Rolling Hills shows
the burning wreck and strong close-ground relief. Gorge shows rain, open terrain,
settlement structures and distant cliffs. Separate capture runs add alternate
native camera views. The shared sunset preset is intentionally held fixed for
this record; these are not completed per-map weather/time-of-day treatments.

The [remote review folder](https://drive.google.com/drive/folders/1ltssE6TQopFJTRgen8yWJe9lk2Tkieg0)
contains seven full-resolution screenshots, a readable results file and CSV.
Its contents were verified after upload. Local evidence is under
reports/ia-environment-baselines-20261019 on the Games-drive report archive:
raw frame intervals, actual input routes, run settings, source/profile snapshots,
per-run and aggregate results, hardware identities and proof images. Discovery
and camera-capture runs do not contribute performance samples.

These are short spawn-area baselines, not whole-map traversal, heavy combat,
multiplayer or campaign acceptance tests. Future lighting comparisons should
retain the same host/settings/routes, repeat the baseline alongside the change,
and account for AI/fire variability. No new performance-impact attribution or
full-map visual acceptance is claimed. No commit or push was made.
