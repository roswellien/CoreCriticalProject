# Reverse-engineering workflow

Status: bootstrap procedure, 2026-10-06. Treat the checked-in supported-binary
manifest and [supported binaries](supported-binaries.md) as the current identity
record. A filename, archive label, patch version, or valid PE header alone does
not identify a supported MechWarrior 3 game executable.

## Evidence rules

Keep originals and detailed tool output in local ignored storage. Do not execute
an installer merely to identify it. Record SHA-256, byte size, source description,
analysis date, tool version/options, and the investigator's conclusion separately.
Hash the actual input image, not just its surrounding archive. Hash matching
identifies bytes; it does not itself establish provenance or functionality.

Use these labels on every conclusion:

- **Observed:** directly read metadata or reproducible trace, with source location.
- **Inferred:** an interpretation supported by stated observations.
- **Hypothesis:** an experiment is still required.
- **Unknown:** not inspected or not determined.

Name unknown functions `sub_00412340` using the actual verified VA; the example is
a naming convention, not a discovered function. Keep stable `(image SHA-256,
RVA)` identifiers even when assigning a descriptive alias. Do not infer function
purpose from a single nearby string or import name.

## First pass

1. **Identity:** validate a user-provided installed game image against the
   manifest. Keep unknown images in inspection mode and out of execution/lifting.
   If no reviewed game-image hash exists, this is the first blocked milestone.
2. **PE structure:** record machine, optional-header kind, image base, entry RVA,
   sizes/alignments, section file/virtual ranges and permissions, imports,
   exports, relocation directory, TLS, resources, and debug/load-config presence.
   Distinguish file offsets, RVAs, and VAs throughout. Flag malformed or truncated
   tables and ambiguous mappings.
3. **Import report:** group imports by likely subsystem. Record whether a claim
   is based on a DLL name, function name, ordinal, or observed call. A listed DLL
   does not prove which interface versions or features are used.
4. **Code discovery:** seed analysis from the entry point and reviewed targets in
   executable sections. An executable section can contain data; a linear sweep
   is neither a complete CFG nor proof of function boundaries.
5. **Function slice:** review every reachable block and exit for one small leaf
   candidate. Record undecoded bytes, indirect flows, global reads/writes, and
   ABI assumptions. Reject a candidate whose dependencies are not understood.

Use [Microsoft's PE format reference](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)
to interpret PE metadata. The bootstrap analyzer reports structural observations
and dependency hints; a future Ghidra project provides deeper cross-reference,
type, and control-flow review. Keep that project local because it embeds input
content. Tool-specific heuristics remain hypotheses until checked.

## Reconnaissance checklist

This is a work queue, not a claim that each capability already exists in the
bootstrap analyzer. Record `not yet inspected` for unfinished work.

| Area | Evidence to collect |
| --- | --- |
| Loader / memory | Preferred base; section map; relocation types and targets; IAT; TLS; writable code; globals; zero-initialized storage; allocators and heap assumptions. |
| Win32 / CRT | Named and ordinal imports; GetProcAddress/LoadLibrary call sites if present; static CRT routines; filesystem paths; registry; shell integration; last-error use. |
| Graphics | DirectDraw/Direct3D entry points; requested interface GUIDs; COM vtables; render-state calls; pixel and vertex layouts; locks and resource ownership. |
| Input / audio | DirectInput/DirectSound entry points and interface versions; device enumeration; buffer formats; callbacks; notification and cursor behavior. |
| Timing / threading | Timer APIs; timestamp units; float/integer conversion; update loops; sleeps; threads; waits; synchronization; frame-dependent effects. |
| Networking | Winsock, DirectPlay, or other imported/dynamically resolved APIs if present; packet structures only after evidence. |
| CPU semantics | x87 control/status words and extended intermediates; MMX/SSE if present; flags across blocks; atomics; alignment assumptions; FS-relative accesses. |
| C++ / exceptions | Vtable candidates, constructors/destructors, RTTI, exception registrations, unwind handlers, nonlocal jumps, thread-local state. |
| Control flow | Function entries and shared tails; jump tables; indirect calls; callbacks; tail calls; return-address manipulation; unresolved destinations. |
| Data / subsystems | Global and structure layouts; strings and references; file-format candidates; ownership; proposed subsystem boundaries and evidence. |

## Analysis record template

```text
Record ID: mw3/<binary-id>/<subject>
Image SHA-256: <64 lowercase hexadecimal characters>
Location: RVA 0x........; VA 0x........; file offset 0x........
Tool/version/options: <exact environment>
Status: observed | inferred | hypothesis | unknown
Observation: <minimal structural fact; no bulk bytes or strings>
Evidence: <reproducible command, cross-reference, or local trace identifier>
Interpretation: <what the observation suggests>
Alternatives: <other plausible interpretations>
Dependencies: <globals, imports, state, functions>
Validation: <experiment, inputs, outputs, comparison result>
Unresolved: <precise next question>
```

For a function add entry/exit ABI, block ranges, live registers/flags, stack delta,
memory read/write ranges, call destinations, floating-point state, and failure
paths. For a structure add offsets, widths, signedness, alignment evidence, and
pointer fields. For an API add argument/output layouts, ownership, calling
convention, side effects, and observed error behavior. Keep exact strings and
disassembly in the local evidence store; commit concise independent descriptions.

## First translated function

Follow the [bounded experiment](recompilation-research.md#smallest-useful-experiment).
Do not select a simulation, renderer, or complex constructor first. Prefer an
integer leaf with a clear caller and testable inputs. If no such slice is yet
known, the next task is function recovery, not writing a speculative translator.

Public CI uses project-authored fixtures. Game-dependent differential tests run
only when the developer explicitly supplies the admitted executable; absence is
reported as skipped, never passed. Store image hash, slice identity, lifter/build
revisions, input seed, observations compared, and mismatch details in a local
record. An import inventory, a memory unit test, or a hand-authored arithmetic
function does not constitute successful execution of recompiled MW3 code.

## Timing investigation before changes

Trace timer reads and values entering update functions. Determine units, precision,
wraparound, clamps, pause/resume behavior, and whether simulation depends on
rendering or input polling. Compare controlled runs at different presentation
rates while leaving simulation code unchanged. Record save/replay state only
locally and prefer numeric summaries in public notes. Treat proposed fixed ticks
or interpolation as hypotheses until compatibility can be measured.
