# CRT entry with complete control wrapper

This additive isolated experiment carries the actual FDIV producer, CRT
services and math-error registration into the game's control wrapper at
`0x5AC5A0`, import thunk at `0x5AC5D6`, and complete staged MSVCRT `_controlfp`
provider. The same admitted Runtime, 3,504-byte State, distinct FX512 and
fourteen checked pages persist throughout execution. Existing provider pages
are borrowed without remapping or resetting. Only the original FDIV BEFORE
records seed execution.

The wrapper returns to real entry PC `0x5AC436`. The compiled entry performs
both subsequent source PUSH instructions and stops at required, unimplemented
CALL `0x5AC440` to `0x5AC598`. This experiment does not execute an initializer
range, argument setup, SEH dispatcher, complete CRT startup, or a native menu.

The accepted control IR has nine reversible symbol name changes: wrapper and
thunk definitions avoid those already present in the frozen entry object, and
seven pure Remill helpers avoid definitions supplied by the FDIV library.
Provider instructions and global bridge declarations remain unchanged. The
paired Context removes its standalone bridges and replaces longjmp with
`BridgeAbort`; C++ catch paths close nesting and active ownership. Current-owner
pointer equality is checked before selecting a typed bridge. `/EHs`, the
existing caller FX/ENV guard and nonthrowing callable boundary remain required.

The final candidate is `preparation-r5` with `build-r6`. The actual author run
`execution-r3` has 24 original BEFORE compositions and 36 causal controls at
each optimization level. Controls include source/IAT corruption, control-word
incoherence, pending/nonempty x87 state, actual stack permission loss, argument
and return changes, and observer exceptions. The hot/cold source mutations
occur before entry and are denied by the earlier shared FDIV source integrity
check; they do not claim entered-control source mutation coverage.

Every checkpoint captures all fourteen pages, State3504, Runtime CPU, projected
State CPU, FX512, CRT globals, guest TIB bytes, and literal entry/matherr/control
source spans. Positive captures include 38 game accesses, 13 control routes,
52 actual compiled memory or typed CW accesses, and eight Runtime call records
(the root remains incomplete). Admission reads are excluded from the compiled
access trace. Fixed-capacity event/status files retain zero unused tails.
Terminal retry checks retain the full failed checkpoint without another access.

`observe.py` supplies author whole-buffer carry checks. Independent instruction
models and compiled rich-host fault controls remain separate acceptance evidence.
Historical preparation/build failures and the partial O0 run remain retained.
Inherited generic build/execution scope strings mention the preceding matherr
gate; this README and the final submission describe the actual control gate.

Run the pinned additive preparation, build, execute and author observer tools
with fresh immediate report directory names. Do not rerun the configuration
materializer against the final tools: it is retained as historical source
construction evidence, while the final literal preparation is authoritative.
