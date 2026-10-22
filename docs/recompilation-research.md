# Recompilation research

Current strategy, 2026-10-11: [faithful modernization](faithful-modernization-plan.md)
reuses the accepted translation/CPU experiments and evaluates other components
only for concrete execution gaps. The initial proposal below is historical;
it does not call for restarting framework selection or repeating accepted probes.

Research date: **2026-10-06**. This is a source review and experiment proposal,
not a successful MW3 lift. No framework listed below has been built or validated
against an MW3 function by this document's author. Upstream documentation is
evidence of claimed capabilities, not proof of compatibility with this game.

## Provisional decision

Evaluate **Remill as the instruction-semantics library**, with a small
project-owned control-flow and runtime adapter. Use Ghidra for analysis and
reviewed function/control-flow metadata. Keep **SRW/llasm** as a serious second
candidate for a bounded comparison because it addresses existing Windows x86
games. Do not commit to a whole-program translator until an integer function and
an x87 function survive differential testing.

This recommendation is an engineering judgment: explicit guest state and memory
accesses fit the project's 32-bit-address requirement, while the project retains
control of import marshalling, unsupported behavior, and replacements. A native
compiled helper implementing an instruction's semantics is compatible with this
design; a permanent fetch/decode/execute interpreter or runtime JIT fallback is
not part of the proposed game executable.

## Candidate comparison

| Candidate | Evidence from upstream | Fit and unresolved work |
| --- | --- | --- |
| Remill | Lifts x86 instructions to LLVM bitcode; intended as an instruction library. Current README describes Linux support and experimental Windows builds. Apache-2.0. [Repository](https://github.com/lifting-bits/remill), [design documentation](https://github.com/lifting-bits/remill/blob/master/docs/README.md) | Best first semantic experiment. Does not discover a trustworthy whole-program CFG, reproduce Win32, or establish MW3's floating-point behavior. Need memory intrinsics, call routing, target ABI isolation, and pinned build dependencies. |
| McSema | Documents 32-bit Windows PE lifting, control-flow recovery through IDA Pro, and use of Remill. Repository was archived on 2022-08-23. [Repository and limitations links](https://github.com/lifting-bits/mcsema) | Valuable reference for executable lifting and external calls. Archived dependencies, commercial frontend dependency, and historical build instructions make it a poor default for a new reproducible pipeline. Its advertised coverage is not evidence that MW3 or modern cross-architecture output works. |
| rev.ng | Provides binary analysis, a model, C output, and a recompilation artifact. Current setup documentation requires Linux x86-64, with WSL/Docker options. The documented `recompile` artifact is a Linux x86-64 ELF with a runtime. [Overview](https://docs.rev.ng/what-is-revng/), [artifacts](https://docs.rev.ng/references/artifacts/), [setup](https://docs.rev.ng/user-manual/initial-setup/) | Useful analysis and competing lift experiment. PE analysis and a recompilation artifact do not establish a Windows x86-to-native Win32 runtime. Evaluate helper dependencies, address-space handling, Windows ABI, and licensing of selected components before adoption. |
| Ghidra SLEIGH / p-code | SLEIGH describes instruction decoding and p-code semantics. Raw p-code is a register-transfer IR; some instructions can use user-defined operations. [Language specification](https://ghidra.re/ghidra_docs/languages/index.html), [p-code](https://ghidra.re/ghidra_docs/languages/html/pcoderef.html), [pseudo operations](https://ghidra.re/ghidra_docs/languages/html/pseudo-ops.html) | Strong analysis frontend. Decompiler C is not automatically correct, buildable source. An executable backend must lower raw p-code, implement every encountered user operation, preserve flags and floating-point behavior, and resolve calls. Prefer metadata export before attempting a custom p-code compiler. |
| llvm-mctoll | README lists x86-64 and Arm32 Linux/ELF support; Windows and C++ support remain work to add, and SIMD is a stated limitation. [Repository](https://github.com/microsoft/llvm-mctoll) | Wrong initial target for a 32-bit x86 PE C++ game. Revisit only if upstream target coverage changes materially. Running the tool on Windows is different from supporting Windows input. |
| M-HT SR / SRW / llasm | SRW accepts Windows executable plus per-game information and emits assembly or llasm; llasm converts to LLVM IR. Repository lists Windows-game ports including Septerra Core and Battle Isle 3. [Project](https://github.com/M-HT/SR), [SRW](https://github.com/M-HT/SR/blob/master/SRW/README.md) | Relevant practical alternative, though not a general x86-to-C generator. Evaluate required annotations, instruction coverage, host pointer assumptions, x87 treatment, and ease of replacing its runtime boundary. Do not import another game's generated output or proprietary data. |
| Anvill / Rellic path | Anvill uses Remill to produce bitcode intended for further C decompilation. Its current README says the main branch consumes specifications from a closed-source Ghidra plugin; the older open frontend uses Binary Ninja. [Anvill](https://github.com/lifting-bits/anvill) | Interesting for recovered types and eventual maintainable output. The documented frontend availability is a reproducibility obstacle. Readable C does not remove the need to validate ABI, aliasing, and guest memory semantics. |

Console recompilers can inform project layout, patch registration, and local
generation workflows, but are not x86 decoders. For example,
[XenonRecomp](https://github.com/hedge-dev/XenonRecomp) translates Xbox 360
executables to C++ and explicitly requires a separate runtime. Adapting its
overall pattern does not establish x86 or Windows support.

The current rev.ng overview and artifact pages were available through indexed
primary-source text during this review; direct retrieval timed out. Verify those
details against the pinned release before relying on them. No version or commit
is yet approved as a project dependency. Once a candidate builds, record the exact
commit, LLVM/Clang version, dependency revisions, build options, and license notices
in the experiment record. The bootstrap build must remain independent of lifter
installation.

## Smallest useful experiment

First build the adapter against a **project-authored 32-bit x86 fixture**, so
toolchain and memory-model failures can be investigated without game material.
The fixture should contain one arithmetic leaf function, one conditional branch,
and one load/store through a 32-bit argument. Compile a native reference and the
lifted result separately. Do not describe a manually written equivalent C++
function as a generated recompilation.

After admitting an actual user-provided MW3 executable by SHA-256:

1. Record its precise build identity and PE metadata. Confirm that it is the game
   image, rather than a patch installer or launch helper.
2. Select one reviewed integer leaf function with no imports, indirect calls,
   exceptions, TLS, or unknown global dependencies. Keep the address-based name.
3. Record entry RVA, every reachable instruction range, exit convention, inputs,
   outputs, register/flag effects, and required memory. Check all paths terminate
   within the approved graph. Obtain bytes only from the validated local file.
4. Lift the function using a pinned Remill build. Route every memory operation
   through the guest-memory adapter and lower every exit explicitly. Abort on
   unsupported instructions, unresolved successors, or unmodelled helper calls.
5. Compile LLVM output to a native x86-64 object and link the project harness.
   Keep this locally generated game-derived object and IR untracked.
6. In an isolated local 32-bit reference harness, run the original function from
   the user's file with controlled state. A debugger-backed original process may
   be needed if standalone execution depends on loader or initialization state.
   This is an offline oracle, not the shipped runtime architecture.
7. Compare results, modified memory, preserved registers, stack effects, and all
   architecturally defined live flags. Use boundary values and deterministic
   randomized inputs, and compare optimized and unoptimized lifted builds.

Passing the integer test answers only whether this narrow path works. Next add an
x87 fixture with control-word changes, rounding boundaries, NaNs, and spills;
then a direct call; then one marshalled import; then a bounded jump table. Compare
the same fixtures with SRW/llasm before expanding the adapter substantially.

## Acceptance and stop conditions

Accept a candidate only with repeatable build instructions, no interpreter/JIT
fallback in the output, faithful 32-bit memory accesses, diagnosed unsupported
operations, and matching reference results for the selected corpus. Record
translation time, object size, compile time, and execution cost as observations,
not performance promises.

The first MW3 execution remains blocked until all of these exist:

- A reviewed actual game executable hash and version-specific analysis record.
- A trustworthy function boundary and complete control-flow slice.
- A built, pinned lifter and an explicit adapter for its memory/state intrinsics.
- A reference execution method and input-state corpus.

Later feasibility risks include x87 precision, callbacks, virtual calls, SEH/C++
unwinding, FS-relative state, dynamically resolved imports, executable writes,
and initialization spread across libraries. A failure should produce a minimized
fixture and a recorded unsupported feature, never a silent success stub.

For the architecture and validation record format, see
[architecture](architecture.md) and [reverse engineering](reverse-engineering.md).
