# MechWarrior 4: Mercenaries recompilation execution plan

Proposed 2026-10-09, based on the [installed-game assessment](mw4-reconnaissance.md).
Begin with **Mercenaries**, the verified installed title, on **Windows x64**.
Keep original game behavior and user-supplied data, using native static
translation for game logic and authored compatibility services. Carry the
project's selected **Vulkan** backend into the MW4 design after recovering its
actual graphics boundary. Vengeance and Black Knight require separate build
admission and later comparison.

The critical path starts with obtaining an exact, readable game-code image.
The installed SafeDisc launcher and protected ICD are identified, but Ghidra
recovered no usable gameplay function from the ICD. Recompilation cannot start
by treating its current entry pseudocode as source. Archive-directory work can
proceed while this gate is resolved.

The subsequent [normal-launch test](mw4-launch-test.md) failed twice with Disc 2
mounted on this Windows 11 host: `Secdrv` was blocked from loading and the
launcher exited with `0xC0000005`. A third attempt with Disc 1 verified at `H:`
displayed an administrator-privileges error dialog, with another blocked
`Secdrv` event. No attempt reached the game menu. Launcher memory changed during
the passive repeat, but no usable ICD gameplay code was recovered. Phase 0 must
establish a viable reference route before native function work.

[Online compatibility research](mw4-windows-compatibility.md) found an existing
source-based retail conversion in MechWarrior 4 Remastered release
`v0.6.47.5`. Its three declared EXE/ICD/player-DLL hashes exactly match fresh
calculations of our installed inputs. Reviewing and reproducing that pinned
conversion in a separate directory is now the preferred next phase-0 step.
This is an input match; no derived output or playable reference has yet been
qualified locally. PR1 and MekTek remain separate build admissions.

The existing `m4-*` tools mean **MW3 Milestone 4**. Use `mw4mercs-*` tools and
`MW4P-*` phase identifiers for this work. MW3 remains the active implementation
target until the first MW4 native proof earns a separate admission; preserve
its [current accepted work](project-milestones-r3.md).
The MW4 research lane can begin independently of completing MW3 startup.

## Execution order and acceptance gates

| Phase | Work and concrete deliverable | Completion gate |
| --- | --- | --- |
| **MW4P-0: Identity and execution oracle** | Preserve the installed EXE/ICD/DLL/data identities; establish ordinary startup behavior and identify the actual running code module. Obtain a readable game image from the user's own build, with reproducible provenance. | Readable code, mappings, entry and import state are bound to exact original and derived hashes; repeated capture/admission can explain changes. A working original x86 execution route exists for differential tests. Current status: static identity complete; code/oracle gate open. |
| **MW4P-1: First native function** | Select one complete integer leaf from the admitted gameplay image; document ABI/CFG/memory; lift with Remill, compile x64 and compare with original x86. | Zero unexplained mismatches at O0/O2 across boundary/random cases; defined flags, registers, stack cleanup, permitted writes and preserved host state match; rejection controls pass. No function has been selected yet. |
| **MW4P-2: First closed subsystem** | Grow the proof into a small configuration, lookup, archive or state component with every reachable dependency covered. In parallel, implement a bounded `#VBD` directory reader and then one verified payload path. | Complete call closure and state contract; original/native comparisons plus authored malformed-input controls; title-specific receipts can be reproduced. An authored archive reader alone receives asset-tooling credit. |
| **MW4P-3: Native startup and frontend** | Recover initializer scheduling, CRT/provider behavior, allocations, filesystem, timing, threads, callbacks, windows and actual graphics/input/audio interfaces. Compile the necessary code and implement each service boundary. | A project-built x64 process reaches and operates the menu using the supplied data, with checked service traces and orderly shutdown. All executed code is translated or explicitly replaced; unknown calls fail visibly. |
| **MW4P-4: One playable mission** | Resolve one small scenario's terrain/shared/script/mech dependencies; recover update scheduling, rendering, input, audio, AI, weapons and exit paths. Use a single controlled offline scenario. | Load, play, pause, complete/exit and reload through native code; compare controlled state checkpoints and rendering/audio observations with the original; no unexplained state drift or ownership errors. |
| **MW4P-5: Compatibility and release** | Expand to Instant Action, campaign, saves, settings, mission variants, stability and performance; schedule multiplayer as a separate compatibility contract. | A documented supported-scenario matrix, reproducible local build/conversion and asset-free distribution process; regressions against admitted builds pass. |
| **MW4P-6: Other titles and enhancements** | Compare Vengeance/Black Knight artifacts and behaviors, admit their differences and then implement them. Add optional visual/asset improvements against the established baseline. | Each title and enhancement has its own acceptance evidence; engine similarity earns reuse through checked correspondence. |

Dependencies are `0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6`. Asset-directory research,
resource inventory and authored service fixtures may run beside phase 0, but
they cannot satisfy native-function or gameplay gates. Measure engineering time
on completed proof families before assigning a full-game date. A credible
completion estimate is not available while code recovery remains unresolved.

## First implementation batch

1. **Create a title-aware admission recipe.** Generalize the strict manifest
   parser in [pe.py](../../tools/analysis/pe.py) for explicitly supported game IDs,
   retaining duplicate-key, full-hash, size and PE checks. Both existing CLIs
   default to MW3, and the parser currently rejects `game != mw3`. Add independent
   MW4 configuration after review, with tests for cross-title rejection and all
   existing MW3 identities. Keep the launcher, protected payload, readable
   derived code and provider DLLs as distinct artifact roles; documenting a
   hash does not make that artifact executable in the native runtime.

2. **Resolve the original execution route and readable image.** Review and
   reproduce the exact-match, release-pinned retail conversion identified in
   the [compatibility research](mw4-windows-compatibility.md), retaining source,
   input/output identities, modified regions and a separate output directory.
   Validate its derived PE/code and original-game behavior before admission.
   Record the normal startup result, loaded module identities and process memory layout.
   If ordinary execution exposes readable code, retain a local capture with
   section coverage, load base, modifications, import resolution and provenance
   linking it to the installed EXE/ICD. Compare stable code over repeated runs;
   record relocated or runtime-generated areas separately. A process dump is
   not automatically a reconstructable PE. If this build cannot supply readable
   code and an original oracle, assess another user-owned build as a separate
   input. Do not spend the first batch compiling the protected entry's
   pseudocode. Normal startup has now been tested and failed as recorded above;
   readable game-image capture remains unresolved.

3. **Create a persistent analysis project for that image.** Verify the imported
   hash and every selected body's original byte ranges. Seed exact entries
   from reviewed callers, tables and callbacks, documenting overlaps and missing
   functions. Export function bodies, assembly, CFG, calls, data references and
   pseudocode in batches. Recovered names/types/calling conventions remain
   hypotheses until checked. Retain one analysis owner and let other workers
   consume frozen exports; repeated cold imports are avoidable overhead.

4. **Implement the small asset-directory proof.** Start with the 58,948-byte
   `coliseum.mw4` and its 28 records. Validate directory extent, counts, names,
   stored sizes and offsets before reading payloads. Use authored archives for
   public tests, including truncated tables, overflowing lengths, overlap and
   invalid paths. Compare the reader with the retained observations for all
   113 installed archives. Then determine one member's codec and output shape
   using original reader behavior when available. Add script source/bytecode
   classification only after inspecting decoded payloads. Codec semantics and
   directory field meanings remain provisional.

5. **Deliver the native leaf proof.** Prefer an integer-only game function with
   no allocation, callbacks, imports, TLS/FS/SEH or indirect branches, a complete
   CFG, a clear caller and a small testable memory contract. Use a separate x86
   original worker and x64 compiled worker, exact body/image hashes, boundary
   values, controlled random cases and malformed-state controls. Compare defined
   outputs and permitted side effects; confirm generated code routes only to
   reviewed destinations. Preserve x87/SIMD state even for an integer proof.

The batch produces an admission specification, an original-execution receipt,
a readable-image/analysis receipt, an archive-directory proof and a native-leaf
comparison receipt. If step 2 remains unresolved, finish the independent asset
and schema work and report that exact gate; do not claim a native recompilation.

## Reuse the existing foundations selectively

| Existing foundation | Reuse | Required MW4 work |
| --- | --- | --- |
| [Guest addresses/memory](../../runtime/memory/guest_memory.hpp) | Explicit 32-bit guest pointers, permissions, checked little-endian reads/writes | Map the admitted MW4 layout and ownership; keep host pointers outside guest fields |
| [Remill adapter](../../tools/lifting/host_adapter.py) and [subsystem adapter](../../tools/m3-subsystem/adapt_subsystem.py) | Pinned lifting/compiler build, state layout checks and differential method | New reviewed entries, CFG, extraction, state/memory contracts and call routing; current adapters reject unreviewed external/indirect calls |
| [Experimental image loader](../../tools/m4-startup/image_loader.cpp) | Bounded PE section/data mapping | Evaluate the readable image against its fixed-base, stripped-relocation and directory subset; add relocations/DLL/TLS only when measured requirements demand them |
| [Experimental runtime](../../tools/m4-runtime/runtime.cpp) | Frozen native/service routes, guest stacks, ABI checks, first-fault handling and execution ledger | Remove MW3-specific admission through explicit profiles; add measured CRT/provider, allocator, thread and exception behavior. Existing SEH-chain storage does not implement exception dispatch |
| [Capture manifests/stages](../../tools/m4-pipeline/stages.py) and [direct capture](../../tools/m4-capture-direct/capture_direct_v3.hpp) | Strict artifact manifests, receipts and tested transport patterns | Separate acceptance recipe: current seal and several capture paths pin MW3 inventories/addresses |
| [Game monitor](../../tools/game-monitor/monitor.py) | Windows lifecycle and diagnostic mechanisms | Separate executable/code-module identities and log paths; current admission and hooks are MW3-specific |
| [Graphics instrumentation](../../tools/graphics-trace/trace.cpp) and [Vulkan replay](../../tools/vulkan-probe/replay.cpp) | Capture/replay methodology, format/state contracts and image comparisons | Recover MW4 COM interfaces and GameOS ABI, resource lifetime and full presentation boundaries; current D3D3/offscreen subset is not an integrated MW4 renderer |
| [Asset discovery](../../tools/asset-inventory/inventory.py) | File/signature inventories | New `.mw4` container and payload readers; existing MW3 ZBD/ZRD/RGB565 decoders do not establish MW4 support |

Use Ghidra/REA for recovery and artifact-bound observations, Remill/LLVM for
instruction translation, and original/native workers for correctness. Remill's
upstream description emphasizes instruction lifting into LLVM bitcode; it does
not supply whole-program reconstruction or a Windows compatibility runtime.
[Remill documentation](https://github.com/lifting-bits/remill)

The installed REA Windows bridge admits native PE applications, while DLL
analysis and persistent project work require the direct Ghidra route already
tested in this repository. Keep provider/import caches from being mistaken for
the admitted DLL's ABI. A neutral REA evidence snapshot does not eliminate the
measured cold provider initialization.
[REA Windows boundary](https://github.com/morluto/rea/blob/main/docs/windows-ghidra-p0.md),
[local tooling evaluation](m4-tooling-evaluation.md)

## Requirements to recover before native startup

Track requirements against reachable code and actual runtime observations:

- **CPU/ABI:** x87 precision/control/status and float-to-integer paths; observed
  MMX/SSE/MXCSR requirements; flags, calling conventions, jump tables, callbacks,
  C++ object layouts, thread-local state and exceptions. Extend the bounded MW3
  tests when MW4 uses a new case; existing acceptance is not universal coverage.
- **CRT and providers:** verify this installation's DLL identities and actual
  loader choices. The included `msvcrt.dll` is version `6.00.8397.0`; its behavior
  cannot be substituted by the host CRT or an MW3 provider assumption. Recover
  initialization, allocation/reallocation, locale, I/O, math and termination
  only as the executable closure needs them.
- **GameOS/platform:** determine initialization order, registries/files,
  handle ownership, windows, timers, update threads, synchronization, input and
  audio formats. Resource-only language DLLs and executable providers need
  separate treatment based on their actual roles.
- **Graphics:** confirm DirectDraw/Direct3D interface versions and calls,
  vertex/pixel formats, states, surfaces, texture locks and presentation. The
  readable ICD metadata suggests legacy DirectDraw/Direct3D work, but does not
  establish a complete API. Keep a captured baseline, then implement the
  accepted boundary with Vulkan; validate the whole presented frame.
- **Data and scripts:** establish archive lookup/override order, member
  codecs, mission/map references and whether `.abl`/`.script` payloads are
  interpreted, compiled or data. Include campaign state and save layouts later.
- **Network boundaries:** isolate offline behavior first. The installed batch
  documents `-win32dedicated`, a useful headless experiment candidate once its
  actual startup dependencies are recovered; it does not prove a network-free
  or working dedicated mode. Multiplayer and obsolete online-service behavior
  need a separate scope after the local mission works.

## Work layout and progress accounting

Proposed locations, to create as their phases begin:

| Location | Content |
| --- | --- |
| `games/mw4mercs/config/` | Title/build admission and provider identities |
| `games/mw4mercs/docs/` | Image map, API ledger, function/subsystem contracts and unresolved questions |
| `games/mw4mercs/symbols/` | Reviewed hash/RVA annotations, with confidence and sources |
| `tools/mw4mercs-analysis/` | Readable-image verification and persistent Ghidra exports |
| `tools/mw4mercs-assets/` | Authored bounded container/payload readers |
| `tools/mw4mercs-leaf/` | Exact extraction, original/native workers and comparisons |
| `reports/mw4mercs-*/`, `local/mw4mercs-*/` | Ignored proprietary evidence, projects, captures and generated translations |

Record separate counts for recovered entries, byte-checked bodies, contracted
interfaces, native-tested functions, closed subsystems and playable scenarios.
Record unresolved indirect targets, unsupported instructions and required
services explicitly. Successful decompilation, archive enumeration or capture
transport adds no gameplay credit. Time the full recovery/build/comparison/
integration cycle and retain failures as well as passes.

The first useful success is a **verified native MW4 gameplay function**. The
first user-facing success is **one mission playable through the project-built
x64 runtime**. Keep original binaries, assets, dumps, full pseudocode and
generated translations in ignored local storage under the existing
[distribution policy](../legal.md); public tests use authored fixtures.
