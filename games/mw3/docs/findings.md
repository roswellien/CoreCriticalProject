# MW3 reconnaissance ledger

Status: the exact installed U.S. version 1.2 executable is admitted as research
input `mw3-us-1-2-retail`. This is identity verification, not runtime or
recompilation validation. See [media and installation provenance](../../../docs/media-inventory.md).

| Topic | Status | Next evidence |
| --- | --- | --- |
| Executable/version/hash | Observed: installed 1.2; file/product resources 1.2.22.0; exact SHA-256 in manifest | Preserve identity when selecting a real function |
| Memory map, imports, relocations | PE32 headers and import/relocation metadata captured in local analysis report | Correlate metadata with disassembly and runtime behavior |
| Function boundaries and globals | Unknown | Correlate disassembly, xrefs, dynamic observations |
| x87, MMX, SSE | Unknown | Decode reachable code and classify instructions |
| RTTI, vtables, exceptions, TLS | Unknown | Validate structures and references |
| Indirect calls, jump tables, callbacks | Unknown | Recover targets and ABI evidence |
| Subsystems, structures, enums, formats | Unknown | Record narrow experiments with SHA and addresses |
| Renderer and audio behavior | Main menu observed with app-local dgVoodoo2; playable training reported by user; audio coverage unknown | API and COM-method inventory followed by traces and broader session testing |
| Simulation timing | Terrain/view glitch reportedly resolved with a 30 FPS ceiling; exact cause and timing model unknown | Identify updates, timer units, delta calculation and coupling |

The 30 FPS comparison is a user-reported behavioral result, not a measurement of
the engine's timestep or proof of the glitch's cause. No timestep correction is
enabled; only a presentation frame-rate ceiling is configured.

## Original-game compatibility observations — 2026-10-06

- Input: `mw3-us-1-2-retail`, SHA-256
  `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
  The original executable remains unchanged.
- Without a wrapper, `mech3.out` accepted Direct3D HAL but ended with
  `Error opening video... ABORTING RUN`; the displayed error was
  `Failed to initialize video device`.
- With [dgVoodoo2 2.87.5](https://github.com/dege-diosg/dgVoodoo2/releases/tag/v2.87.5)
  x86 `DDraw.dll` and `D3DImm.dll` beside the executable, the main menu was
  observed. Loaded-module inspection confirmed the local wrappers and system
  D3D11. Output API is `d3d11_fl11_0`; resolution, filtering and antialiasing
  remain application controlled; FastVideoMemoryAccess is disabled.
- The user reported playable training, then abnormal geometry near a cliff.
  A paused-screen inspection showed cockpit/HUD rendering and an abnormal
  outside view. The process remained responsive; no crash was recorded.
- The sole configuration change for the next trial was `GeneralExt/FPSLimit`
  from `0` to `30`. The user subsequently reported the issue appeared resolved
  but gameplay was less smooth. Duration, exact route and repeatability were
  not measured. Timing involvement is a hypothesis; clipping, collision or a
  renderer issue remain possible explanations.
- Local evidence: `local/diagnostics/mw3-video-20261006/`, including original
  failure logs, settings backup, graphics-glitch evidence and the FPS trial.
  Wrapper ZIP SHA-256:
  `5ffde6927f7355ca3fdd5d785b581256a8e6539fa13e395a891ade6ba1040850`.
- Next compatibility experiment: repeat the same training route with recorded
  frame timing and conditions before changing another variable. Review the
  [ZipperFixup timing implementation](https://github.com/TerranMechworks/ZipperFixup)
  in a separate experiment if warranted; no timing patch is installed.

These observations concern the original game's reference environment. The
authored x86/native x64 comparison gate (G1) has since passed; the first MW3
execution comparison (G2) passed on 2026-10-07 for one isolated integer leaf.
Retain the 30 FPS environment as the current provisional gameplay
baseline while researching smoother simulation and rendering later.

## Hash-bound reconnaissance and first-function review (2026-10-06)

- **Observed:** the installed image still matches `mw3-us-1-2-retail`. Python and
  LLVM 21.1.8 metadata views agree on the reviewed headers and all 474 ordinary
  imports across 18 libraries. See the [memory map](memory-map.md) and
  [API inventory / research backlog](api-dependencies.md).
- **Observed:** real executable-section disassembly now works through the PE
  adapter after removing an option terminator unsupported by LLVM 21.1.8. All
  27 synthetic tooling tests passed with the corrected invocation.
- **Observed:** `sub_00409ED0`, RVA `0x9ED0`, is a reviewed 22-byte straight-line
  integer leaf. LLVM and Remill/XED agree on its six instructions. It computes
  an address from ECX and one stack argument, clobbers EAX/EDX, reads only its
  stack frame, writes no memory, and cleans one argument. See its
  [identity, complete contract and comparison requirements](first-function.md).
- **Observed:** exact-image and exact-slice admission produced a private slice
  and guest IR. Six changed-input/metadata/output-location controls were rejected;
  the independent binary validator also rejected changed code with exit 2.
  The installed executable was preserved. Evidence is under
  `reports/mw3-recon/`, including source and artifact hashes.
- **Inferred:** its address calculation resembles a member-array helper. The
  object type and gameplay role remain **unknown**.
- **Unknown / next:** no original/native MW3 comparison has executed. Adapter
  work must explicitly handle undefined intermediate shift flags that are
  overwritten before return, select the original guest entry, and provide an
  x86 reference host whose own image does not overlap the guest code page.
  Reconnaissance review and static slice recovery do not establish G2.

## First native MW3 leaf comparison (2026-10-07)

- **Observed:** G2 passes for the admitted `sub_00409ED0` slice: 16,609 original
  x86 inputs match Remill-generated native x64 at O0 and O2, with zero mismatches
  and all 49 admission/comparator/worker rejection controls passing.
- **Observed:** independent offline verification regenerated the corpus and
  rechecked complete register/flag/return/4,096-byte payload results, source and
  worker hashes, nine generated artifacts and the exact overwritten AF/OF proof.
- **Observed:** the expanded authored G1 suite passes 40,576 inputs and
  81,152 native comparisons, with 135 rejection/bridge checks on the same source
  digest. Both native game-function workers are AMD64 PE32+ executables statically
  linked to generated COFF objects; reviewed output has no interpreter/JIT path.
- **Observed:** the separate authored x86 replacement logged one verified call
  in original MW3, and the user confirmed Training loaded. Its index/base pair
  appears in G2; other replay state is authored. The installed game hash is unchanged.
- **Unknown / next:** x87 fidelity, calls/imports, whole-game native integration,
  extended gameplay stability and the helper's precise object type remain open.
  This integer result does not establish physics or renderer compatibility.

See the [G2 experiment and replay record](../../../docs/mw3-leaf-experiment.md)
and [function dossier](first-function.md). The pending comparison noted in the
2026-10-06 static review above records the earlier state; this result closes it.

Use this record format for new findings:

```text
ID / date:
Binary SHA-256:
RVA and preferred VA:
Observation:
Evidence and reproduction:
Tool version / configuration:
Evidence status (observed / inferred / hypothesis / unknown):
Alternative explanations:
Next discriminating experiment:
```
