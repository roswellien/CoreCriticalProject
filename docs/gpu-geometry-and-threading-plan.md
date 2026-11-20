# GPU geometry and simulation threading in MW3-RE

## Scope of the measurement

The native-preview launcher defaults to partial geometry. Its Python planner emits the Vulkan WSI presenter. The comparison workload uses a 3440×1440 raster, render worker on, the full owner pack set, draw distances 800 and 3200, seed 72519, and the turn/walk inputs in the local bench-r2 harness. All four cases use the player-facing partial geometry path. Each run starts from a separate copy of the player profile. The renderer reports the selected adapter at startup. Compare rows with the same presenter, adapter and workload. [Launcher defaults](../tools/mw3-remaster-launcher/Core/Mw3ReLaunchRequest.cs) · [Argument construction](../tools/remaster-launcher/mw3_re_launch.py)

The runtime counts non-sharp draw attempts in its geometry handoff summary. The renderer increments it before checking whether replacement geometry suppressed the draw. Several producers can also feed the same deferred queue. Count attempts, suppressions, submitted draws and earlier producer CPU work separately. Existing stage, assembly and worker timers report calling-thread elapsed time and can include waits or nested operations. Attribute on-CPU costs to non-overlapping buckets with sampled callers. [Renderer](../runtime/mw3-re/src/frontend/core_critical/frame_renderer.cpp) · [Timer](../runtime/mw3-re/src/frontend/sdl/cpu_interval.h)

## Geometry already on the GPU

Eligible rigid prepared batches use retained geometry and per-instance matrices, source colour, fog parameters and clip inputs. The early adapter can bypass original vertex and polygon preparation. The shader writes clip coordinates and fog factors. Ineligible batches retain their staged CPU path. The prepared GPU reference fixture compares seven scenarios at a tolerance of two per RGB channel. It also checks that 21 vertices took the GPU path with a single geometry upload and zero CPU-clipped triangles. The stock fixture independently checks a near-plane-crossing triangle. These two completed capabilities leave the implementation queue. Stock model admission has additional conditions, including a separate far-plane safety check. [Prepared adapter](../runtime/mw3-re/src/frontend/core_critical/prepared_gpu_adapter.inc) · [Vertex shader](../runtime/mw3-re/src/frontend/core_critical/renderer/geometry/shaders/native_geometry.vert) · [Prepared checks](../runtime/mw3-re/src/frontend/core_critical/prepared_gpu_checks.inc) · [Stock admission](../runtime/mw3-re/src/gamez/zmodel/gmod_geometry.cpp)

## Measured workload and first geometry candidate

On the November 20, 2026 development build `85d0638430097db305908017d85cb5ea590c92f2`, increasing draw distance from 800 to 3200 increased main-thread stock handoff from 0.89 to 4.07 ms/frame on c2m1 and from 0.81 to 3.83 ms/frame on ia1. The first proposed geometry change is to reduce repeated host-side cache scans during stock submission. The measured scan alone accounted for 1.43 and 1.58 ms/frame at 3200. Prepared CPU vertex staging and assembly both reported zero in all four cases. This candidate changes CPU-side submission bookkeeping. The samples justify testing it independently of a future per-family GPU migration. A later A/B is required to establish a gain.

Each run used a Ryzen 7 9700X on Windows 11 build 26300. The WSI renderer reported AMD Radeon(TM) Graphics with AMD driver 32.0.21045.29003. None of the four profiled runs or the four runs with profiling disabled observed a second game PID. Each trace had zero lost buffers and events. The executable SHA-256 was `f83d517ac2e6a7753cc96650fad72b49024a5e91e8f948be10f89762d9e2b082`. The Release executable and PDB matched on GUID and age. Throughput varies with the host, adapter and camera. The benchmark advances simulation on elapsed time, so identical input frame numbers can produce different trajectories.

## Main-thread CPU time per gameplay frame

Values are milliseconds per frame from 1 ms ETW sample weights. Each column covers 3,600 complete QPC intervals between frame 300 and frame 3,900. Rows are ranked by their mean across the four equally weighted cases. A displayed 0.000 in a sampled row can mean too few samples to resolve at this precision. Each main-thread sample belongs to one row. Navigation includes its geometric queries. Unclassified samples remain in the total. The synchronization row measures CPU executing that path. Time spent descheduled has no CPU sample. The frame-time table includes that elapsed time.

| Work | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| AI navigation and path queries | 3.534 | 3.573 | 2.258 | 2.218 |
| Stock GPU handoff | 0.887 | 4.070 | 0.806 | 3.835 |
| Prepared selection and submission | 0.993 | 1.311 | 1.530 | 1.694 |
| HUD and 2D | 0.689 | 0.830 | 0.751 | 0.768 |
| Scene culling and traversal | 0.256 | 0.727 | 0.229 | 0.572 |
| Immediate draw assembly and submission | 0.269 | 0.445 | 0.307 | 0.461 |
| Other or unresolved | 0.242 | 0.354 | 0.292 | 0.312 |
| Other texture preparation and upload | 0.000 | 0.000 | 0.591 | 0.599 |
| Shadow geometry and traversal | 0.238 | 0.256 | 0.206 | 0.208 |
| Render synchronization (executing) | 0.176 | 0.279 | 0.156 | 0.147 |
| Geometry admission and materials | 0.076 | 0.317 | 0.064 | 0.261 |
| Other AI and targeting | 0.199 | 0.237 | 0.133 | 0.142 |
| Collision outside navigation | 0.133 | 0.147 | 0.174 | 0.162 |
| Effects and weather | 0.122 | 0.109 | 0.185 | 0.192 |
| Deferred draw assembly and submission | 0.040 | 0.252 | 0.042 | 0.155 |
| Other original model preparation | 0.049 | 0.172 | 0.065 | 0.164 |
| Other entity update | 0.082 | 0.111 | 0.046 | 0.043 |
| Mech movement and physics | 0.053 | 0.054 | 0.068 | 0.069 |
| Other renderer | 0.019 | 0.027 | 0.051 | 0.050 |
| Original clipping | 0.032 | 0.040 | 0.033 | 0.036 |
| Original lighting | 0.011 | 0.047 | 0.009 | 0.039 |
| Original fog | 0.010 | 0.043 | 0.009 | 0.036 |
| Weapons and projectiles | 0.014 | 0.014 | 0.025 | 0.024 |
| Original transform and projection | 0.009 | 0.014 | 0.007 | 0.022 |
| Mech animation | 0.008 | 0.012 | 0.009 | 0.009 |
| Audio commands | 0.003 | 0.004 | 0.007 | 0.007 |
| Network | 0.002 | 0.001 | 0.001 | 0.001 |
| Total main-thread CPU | 8.146 | 13.446 | 8.056 | 12.225 |

## Frame timing with CPU profiling enabled

| Case | Mean ms | Median ms | p95 ms | p99 ms | >33 ms | Host CPU median | Game GPU engine median |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c2m1 800 | 83.27 | 78.43 | 112.96 | 143.20 | 3600 | 9% | 83% |
| c2m1 3200 | 118.63 | 121.54 | 155.61 | 171.00 | 3600 | 22% | 88% |
| ia1 800 | 78.79 | 77.52 | 79.82 | 81.93 | 3600 | 4% | 45% |
| ia1 3200 | 79.12 | 77.50 | 80.09 | 82.88 | 3599 | 4% | 46% |

## Player frame timing with profiling disabled

These runs use the same executable, launcher arguments, scratch profile and input script. Runtime CPU counters and the ETW collector are disabled. QPC frame timestamps and host utilization sampling remain enabled. Each cell is one run. Time-driven trajectories and host load vary between runs, so differences between cohorts cannot isolate profiling overhead.

| Case | Mean ms | Median ms | p95 ms | p99 ms | >33 ms |
| --- | --- | --- | --- | --- | --- |
| c2m1 800 | 87.08 | 79.08 | 127.48 | 161.89 | 3600 |
| c2m1 3200 | 155.98 | 159.20 | 179.81 | 194.42 | 3600 |
| ia1 800 | 78.49 | 77.33 | 79.81 | 81.73 | 3592 |
| ia1 3200 | 79.16 | 77.39 | 79.88 | 82.03 | 3600 |

## Calling-thread elapsed counters

These runtime counters include warmup. Values in milliseconds per presentation divide each complete-run total by the renderer's reported presentations. The counters can overlap and include waits.

| Counter | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| Renderer presentations | 3903 | 3903 | 3903 | 3903 |
| Original CPU 3D draw attempts | 936635 | 3722524 | 1008816 | 3088873 |
| All models handed off (includes early prepared) | 541523 | 2178199 | 561896 | 2123162 |
| Models reported unsupported | 160975 | 596113 | 170391 | 588708 |
| Prepared GPU vertices | 663504033 | 875216478 | 1113058851 | 1098100266 |
| Prepared CPU reference vertices | 0 | 0 | 0 | 0 |
| Early prepared models | 162028 | 210911 | 213740 | 218446 |
| Prepared CPU fallback batches | 0 | 0 | 0 | 0 |
| Prepared vertex staging | 0.000 | 0.000 | 0.000 | 0.000 |
| Prepared vertex assembly | 0.000 | 0.000 | 0.000 | 0.000 |
| Prepared model selection | 0.477 | 0.645 | 0.914 | 0.939 |
| Prepared pose retargeting | 0.000 | 0.000 | 0.294 | 0.284 |
| Prepared deformation | 0.000 | 0.000 | 0.000 | 0.000 |
| Prepared emission | 0.000 | 0.000 | 0.000 | 0.000 |
| Transformed/lit vertex append | 0.270 | 0.435 | 0.305 | 0.445 |
| Producer render | 0.073 | 0.264 | 0.070 | 0.163 |
| Producer transport | 0.607 | 0.598 | 0.601 | 0.602 |
| Worker render | 62.321 | 93.312 | 31.243 | 36.430 |
| Worker presentation | 15.134 | 10.001 | 45.248 | 39.944 |

## Wrapped terrain traversal

The extended wrapped-cell path at camera.cpp line 1405 selects roots with the terrain flag. Counts cover that traversal and any descendants. Other terrain in mixed cells remains unattributed. These values are subsets of the work table.

| Work | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| Stock GPU handoff | 0.012 | 1.421 | 0.003 | 1.157 |
| Prepared selection and submission | 0.000 | 0.026 | 0.000 | 0.013 |
| Scene culling and traversal | 0.001 | 0.031 | 0.000 | 0.020 |
| Immediate draw assembly and submission | 0.001 | 0.046 | 0.000 | 0.004 |
| Geometry admission and materials | 0.001 | 0.089 | 0.000 | 0.061 |
| Other original model preparation | 0.001 | 0.063 | 0.000 | 0.009 |
| Original clipping | 0.001 | 0.019 | 0.000 | 0.004 |
| Original lighting | 0.001 | 0.021 | 0.000 | 0.003 |
| Original fog | 0.000 | 0.016 | 0.000 | 0.002 |
| Original transform and projection | 0.000 | 0.003 | 0.000 | 0.001 |

## Geometry CPU by observed caller

| Caller context | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| Mixed world-cell traversal | 1.819 | 4.343 | 2.371 | 4.961 |
| Wrapped terrain traversal | 0.018 | 1.734 | 0.003 | 1.274 |
| Other or unresolved geometry caller | 0.430 | 0.762 | 0.352 | 0.548 |
| HUD or 2D producer | 0.324 | 0.346 | 0.334 | 0.334 |
| Shadow draw | 0.238 | 0.256 | 0.206 | 0.208 |
| Shared deferred queue | 0.040 | 0.252 | 0.042 | 0.155 |
| Particle and weather draw | 0.000 | 0.000 | 0.001 | 0.001 |

## Original CPU model work after geometry handoff declined

PDB callsites below the failed handoff in draw_model, or inside the separate point-model branch, identify work on the residual CPU route. The table counts sampled transform, clip, light, fog, immediate assembly and remaining original model preparation inside that route. Shared deferred flushes and scene traversal take place outside this boundary. These subsets overlap the ranked table. Wrapped roots have the terrain flag. Mixed cells contain multiple families, including additional terrain. A dash marks a caller for which the trace produced no attributable sample in that case.

| Residual model caller | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| Wrapped terrain subtree | 0.004 | 0.160 | — | 0.019 |
| Mixed world-cell subtree | 0.113 | 0.302 | 0.168 | 0.469 |
| Point-model branch | — | — | — | — |
| Other residual model callers | 0.060 | 0.059 | 0.040 | 0.040 |

| Residual stage and caller | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| Wrapped terrain subtree / Original transform and projection | 0.000 | 0.003 | 0.000 | 0.001 |
| Wrapped terrain subtree / Original clipping | 0.001 | 0.019 | 0.000 | 0.004 |
| Wrapped terrain subtree / Original lighting | 0.001 | 0.021 | 0.000 | 0.003 |
| Wrapped terrain subtree / Original fog | 0.000 | 0.016 | 0.000 | 0.002 |
| Wrapped terrain subtree / Immediate draw assembly and submission | 0.001 | 0.046 | 0.000 | 0.004 |
| Wrapped terrain subtree / Other original model preparation | 0.001 | 0.056 | 0.000 | 0.005 |
| Mixed world-cell subtree / Original transform and projection | 0.007 | 0.009 | 0.006 | 0.020 |
| Mixed world-cell subtree / Original clipping | 0.012 | 0.008 | 0.017 | 0.014 |
| Mixed world-cell subtree / Original lighting | 0.009 | 0.023 | 0.009 | 0.037 |
| Mixed world-cell subtree / Original fog | 0.008 | 0.025 | 0.009 | 0.034 |
| Mixed world-cell subtree / Immediate draw assembly and submission | 0.050 | 0.168 | 0.085 | 0.249 |
| Mixed world-cell subtree / Other original model preparation | 0.026 | 0.069 | 0.042 | 0.115 |

## Thread accounting

Worker and audio rows are concurrent with the main thread. They cannot be added to elapsed frame time. A role is identified by samples in the worker loop or the SDL callback. The total row includes other sampled activity on that OS thread.

| Job | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| Render thread, all samples | 2.709 | 6.447 | 2.519 | 5.508 |
| Audio device thread, all samples | 0.351 | 0.679 | 0.294 | 0.302 |
| Inside the SDL mixer or callback | 0.190 | 0.376 | 0.162 | 0.158 |

## Stock geometry cache scan

| Work | c2m1 800 | c2m1 3200 | ia1 800 | ia1 3200 |
| --- | --- | --- | --- | --- |
| CPU sampled directly in the stock cache scan | 0.183 | 1.434 | 0.163 | 1.577 |

## Reproducing and interpreting the measurements

Copy the native-preview write directory before each launch and supply the full pack arguments from the launcher. Pin Vulkan WSI, FXAA, 16x AF, 3440 by 1440, render thread 1 and partial geometry. Use bench-r2's seed 72519, frame limit 3900 and scripted left, right and walk/turn inputs. Pass --tap 0x1e@300:900, --tap 0x20@900:1500, --tap 0x11@1500:3900 and --tap 0x1e@1500:3900. Record every frame with MW3_BENCHMARK_TIMESTAMPS. Enable MW3_CC_CPU_PROFILE=1 for the diagnostic cohort. The slot guard checks the system process list before launch and records any second game PID it observes during the run. Host CPU is the Windows total-processor counter. GPU is the median of the busiest WDDM engine attributed to the game PID in each roughly five-second host sample, across gameplay. It describes one engine and may show transient readings above 100 percent. A compiler-process count is also sampled. It can count waiting build processes, so use it as host context.

Attach the Visual Studio Standard Collector CPU agent to the benchmark PID after the native Core state appears. Read its ETW trace with the Windows Performance Toolkit. Verify its active sample period, process ID, main-thread ID, symbol identities, event-loss totals and coverage of the analysis window. The local traces used 1 ms samples. Convert ETW relative times to the runtime's performance counter with the UTC/QPC anchor and check it against the end anchor. Take only samples between the frame 300 and frame 3900 marks. Count each sample once per thread. One sample in 3,600 intervals is about 0.00028 ms/frame of measured CPU time. Short-lived functions can receive no samples. Counts are sampling estimates, especially for small rows.

Transform, clipping, lighting and fog include recognized helpers and inlined callsites identified by the current PDB. Charge child work to a single category. Navigation owns its collision calls. HUD reticle aiming owns its hit tests when no higher-priority named category applies. Recognized model preparation and draw work precede the residual traversal bucket. Report the render-worker and device-thread samples separately. The producer and worker counters in the runtime measure elapsed time including waits. They cover warmup and use the reported presentation count. Throughput uses QPC frame differences. Classify CPU executing a synchronization call separately from time when the operating system has descheduled the thread.

The wrapped-cell branch in zcls::render_cells selects terrain-flagged roots. Cost attributed to that callsite is the cost of traversing those roots and their descendants. Normal cells can contain additional terrain, buildings, and other world objects. Both the CPU and GPU handoff paths run below the same zmod::draw_model symbol. A separate building CPU cost remains unresolved in this mixed row. A family counter can read the terrain flag and existing owner-kind binding at model dispatch. Mission-target ownership can cover structures and other scored objects, and should retain that label. Deferred queue flushes may contain work from multiple producers.

Draw attempts at the FrameRenderer::draw entry precede suppression and other handling. Submitted model counts include successful early prepared replacements. Prepared early bindings, vertices and original draw attempts measure different events. Early model submission can bypass the original loops entirely. A draw that reaches FrameRenderer::draw is counted before the later replacement suppression check. Work attributed to the stock GPU handoff is still CPU time. This baseline doesn't measure an optimization gain.

## Producer identity still needed

The timing evidence establishes an exclusive geometry-stage ranking and a wrapped-terrain subset. Ordinary mixed cells share a draw routine for terrain, structures, vehicles and props. The caller table combines the CPU cost of GPU-bound submission with residual original draws. A residual CPU-only building or prop cost cannot be recovered from that sum. Separate building and prop timings require carrying the current producer identity through the measurement boundary. A small opt-in diagnostic can use the terrain flag, existing entity owner-kind bindings and a distinct unclassified bucket. Keep unattributable deferred work visible. Check each family against isolated fixtures and require the per-family totals to reconcile with the overall measurement before using them to choose a family-wide rewrite. [Entity ownership](../runtime/mw3-re/src/mech3/entity_bind.cpp) · [Scene traversal](../runtime/mw3-re/src/gamez/zclass/camera.cpp) · [Original model dispatch](../runtime/mw3-re/src/gamez/zmodel/gmod_draw.cpp)

## Simulation ownership and candidate jobs

The application pumps messages, updates its timer and polls networking before it dispatches the state. A mission frame polls input, executes the six action lists in order, purges removable nodes after each nonempty list and calls its frame-update hook. Sound commands follow. Within the hardware draw path the order includes sensors, mission, pilot and camera updates, then weather, 3D submission and HUD. A render call can therefore encompass gameplay. Roots in a call graph cannot be added to their descendants. [Application loop](../runtime/mw3-re/src/gamez/zgame/zgameapp.cpp) · [Mission frame](../runtime/mw3-re/src/mech3/app_states.cpp) · [Action lists](../runtime/mw3-re/src/gamez/zclass/list.cpp)

| System | Live data and ordering | Candidate boundary and equality test |
| --- | --- | --- |
| AI and navigation | The brain borrows contacts and can select a live target. Navigation grid construction queries wall and ground geometry. Graph search mutates shared visit bits and preserves first-best traversal order. Brain waits consume the shared random stream. | The live query APIs temporarily override shared zone visibility, reuse static hit buffers and mutate the global traversal contexts. Wall filtering reads entity ownership. Keep those APIs on main. A future query kernel would need owned traversal and hit storage plus the zone and owner flags from the same world snapshot. Apply results in original query order and preserve the per-tick work budget. Compare paths, tie breaks, controls, contacts and RNG state at each tick. A whole-brain worker requires a proven input snapshot and commit point. |
| Movement and collision | Mech movement, foot contacts, hit selection and responses update authoritative state in entity order. Mech::collide_query reuses a function-static array of twelve SegmentHits. Terrain and object queries also serve AI callers. | A query worker needs owned scratch, the same world revision, ordered candidates and exact FP operations. Apply responses, touched-object callbacks and position changes on main. Compare ordered hit IDs and bitwise hit distances, velocities and positions after each tick. |
| Weapons and projectiles | Weapon spread and bursts advance the same RNG as AI and HUD. Salvo marks, expiry, hit callbacks and damage depend on earlier events. | Retain fire, ammunition, spawn, damage, RNG advancement and callbacks in original order. A future read-only broad-phase query must reproduce the same candidate set and first hit. Compare ordered spawn/hit events and damage after every shot. |
| Animation | Clip time and blend phase are per instance, but blend objects borrow clips and parts. Hip and ski frame methods write matrices. Motion samples can affect locomotion as well as appearance. | The blend sampler temporarily reassigns both borrowed part script pointers. A parallel interpolation kernel would need owned or immutable inputs and must bypass that mutable borrowing. Commit matrices in original order before collision, attachment or rendering consumers. Compare sampled matrices bitwise, foot contacts, muzzle positions and damage/LOD transitions. |
| Effects and weather | Animation events can invoke callbacks, change nodes and produce sounds. The effects scheduler shares staggering and accumulated time across definitions. | Keep scheduling, RNG and callbacks serial. A possible render job expands already-selected particles from an immutable packet. Compare event and RNG order, particle attributes, transparent ordering and pixels. |
| Audio | The SDL device callback already mixes voices under a mutex. Main-thread sound commands update queue state, timing and voice operations after action lists. | Profile main-thread command processing and lock contention separately from device-thread mixing. Preserve ordered play/stop/gain decisions. Compare a scripted command stream and PCM from identical voice inputs. |
| Network | The app polls before the state update. Dispatch may add handlers while iterating and defers removal during active dispatch. A packet can therefore change the mission on the same iteration. | Only reception of owned bytes is a candidate for a queue. Keep packet delivery, registration, callbacks, replies and state changes at the original poll point. Replay explicit arrival order/tick and compare dispatch, replies and state. These two single-player missions provide no multiplayer load measurement. |

Sources for the audit include [AI contacts](../runtime/mw3-re/src/mech3/zai_brain.cpp), [navigation grid](../runtime/mw3-re/src/mech3/zai_nav.cpp), [path search](../runtime/mw3-re/src/mech3/zai_path.cpp), [movement](../runtime/mw3-re/src/mech3/mech_move.cpp), [collision](../runtime/mw3-re/src/mech3/mech_collide.cpp), [weapons](../runtime/mw3-re/src/mech3/weapon.cpp), [pose sampling](../runtime/mw3-re/src/mech3/mech_anim.cpp), [effect events](../runtime/mw3-re/src/gamez/zeffect/zeff_anim_run.cpp), [sound commands](../runtime/mw3-re/src/gamez/zsound/zsnd_play.cpp), [SDL mixer](../runtime/mw3-re/src/frontend/sdl/sdl_sound.cpp) and [network dispatch](../runtime/mw3-re/src/gamez/znetwork/znet_session.cpp).

The process has one MSVCRT seed. A visual HUD effect can advance the same sequence that later decides weapon spread. Fixed seed alone cannot make a race deterministic. Preserve the exact sequence and conditional consumption of random draws, floating-point control state, resource lifetimes and list mutation order. A future threading experiment must replay identical input and simulation time with jobs enabled and disabled, compare state after every tick, and report the first divergent tick. Compare positions, damage, AI decisions, pending events and RNG state over a long run. [RNG implementation](../runtime/mw3-re/src/crt/msvc_rand.cpp) · [HUD consumers](../runtime/mw3-re/src/mech3/hud.cpp)

## Interpreting the geometry results

The first geometry candidate is the stock model submission cache in FrameRenderer::submit_model_geometry. When a stock model is accepted, the main thread scans native_geometry_ for expired weak references before looking up that model by identity. The loop runs again for the next accepted model in the same frame. Each additional accepted model triggers another scan. The four samples quantify its cost under the scripted workload. The table reports samples whose instruction pointer lands in the loop. The larger handoff row also includes material lookup, instance construction, allocations and other work. [Stock adapter](../runtime/mw3-re/src/frontend/core_critical/geometry_frame_adapter.inc) · [Resource identity](../runtime/mw3-re/src/frontend/core_critical/renderer/geometry/resource.cpp)

For the first slice, investigate retiring expired host cache entries at a bounded frame or ownership boundary. Keep submission order, monotonic resource identity and per-instance matrices. In-flight model instances own their geometry resources. Vulkan buffer retirement also has its own completion boundary. A host cache sweep must preserve both lifetimes, including the last frame of a mission, resource churn and teardown. Test the existing retirement fixture with the render thread on, compare per-frame output and verify bounded residency after repeated mission replacement. The sampled leaf time estimates the CPU cost of instructions attributed directly to the sweep. Out-of-line callees may add cost. A replacement sweep consumes CPU time of its own. Frame-time improvement requires that this work was on the critical path. [Packet ownership](../runtime/mw3-re/src/frontend/core_critical/renderer/vk_scene.hpp) · [Retirement fixture](../runtime/mw3-re/src/frontend/core_critical/geometry_checks.inc)

## Threading priorities

1. Investigate independent geometry queries used by navigation grid edge construction. Both c2m1 distances spent about 3.0 ms per gameplay frame in Grid::build_edges including its descendants. The same subtree accounted for 1.91 and 1.84 ms/frame on ia1 at 800 and 3200. The cell build has a per-tick step budget. The existing ground and wall calls change the shared zone mode, use static hit buffers, write global traversal state and inspect live entity ownership. Keep those calls on main. A separate query kernel would need the same world revision, ordered candidates, zone and owner flags, private traversal and hit storage, and identical reductions and tie rules. Apply results at the original step, then compare the grid, selected path and controls tick by tick. This is the largest measured simulation opportunity and carries significant determinism risk.
2. Consider per-instance pose interpolation or purely visual effect expansion once snapshots and commit points have correctness fixtures. The animation and effects rows quantify their directly assigned work. A future job may also include descendants charged to other categories. The CPU collision, attachment and weapon consumers determine when pose data must be visible.
3. Keep the current audio device callback. The measured main-thread audio command cost in these runs is small. Queueing the sound commands introduces ordering and latency changes that would need separate evidence. Keep same-tick network dispatch, weapon/damage callbacks and the shared RNG sequence in their original order.

## Dependencies for future slices

| Candidate | What moves and why it can preserve behavior | Proof, risks and performance bound |
| --- | --- | --- |
| Residual stock geometry and submission | Select a measured expensive family. Reuse immutable source or batch invariant data while retaining per-instance pose, material identity and original submission order. WP07A and WP07C govern baked lighting and material order. | Match CPU-reference attributes, clip results, original alpha/depth order, fixed camera/frame captures and culling decisions. Independently validate resource retirement. The measured critical-path time for the chosen family bounds the removable work. |
| Deformed geometry, WP07B | The four runs reported zero in the prepared CPU deformation timer. IA1 spent time retargeting, which is a different operation. Qualify a workload with measured CPU deformation before budgeting a gain. GPU evaluation would consume authoritative CPU pose inputs after influence, damage and LOD semantics are verified. | Compare per-vertex positions/normals and silhouette over movement and damage. Preserve CPU consumers of the pose. Qualify shadow casters separately under WP06B. |
| Visual effects, WP07D | Move render expansion of a measured effect after simulation has selected its state. | Retain ordering, billboarding, fog and cutout coverage. Compare attributes and pixels across overlapping effects. |
| GPU culling and indirect submission, WP07E | Consider when a measured submission or traversal cost remains after earlier work. Keep stable visibility and order for material-sensitive passes. | Compare visible IDs and ordered draws for camera changes, occlusion, alpha and near/far edges. GPU readback on the main path can erase any benefit. |
| Performance qualification, WP09 | Test each selected change independently against its CPU reference and measure the same four mission/distance cases before promotion. | Use separate screenshot and throughput cohorts. The roadmap's final two-card ABBA Training target is at least 5% higher mean FPS with p95 within 5% of the slower control. Phase 0 grants no qualification credit. |

[Renderer package definitions and qualification](renderer-feature-parity.md)

## Validation

The unmodified pinned Release build passed mw3geometry_checks, mw3prepared_staging_checks, mw3ccvulkan_prepared_wsi, mw3ccvulkan_geometry_wsi and mw3ccvulkan_thread_geometry. The WSI fixtures ran in a free game slot. The four timing runs with profiling disabled are reported above. Each capture used the same Release executable, a fresh player profile, seed 72519 and a fixed 33 ms simulation tick. The pair compared the CPU profile switch off and on at gameplay frame 360 and 3440 by 1440. Each image was decoded to RGB24. The existing prepared GPU reference fixture allows an absolute difference of two per color channel. Positive image content and full dimensions were checked in each capture.

| Case | Largest channel difference | Channels outside fixture tolerance | Decoded RGB SHA-256 when identical |
| --- | --- | --- | --- |
| c2m1 3200 | 0 | 0 | 00a73fc57c7388fca9546189be83fcf7a3355cba0e8ea0af2717035dc877c656 |
| ia1 800 | 0 | 0 | 23b90670298a0a0891091bd9be46c34e9267c998ad4cd4ec11b3d1c7c4f2d6b4 |
