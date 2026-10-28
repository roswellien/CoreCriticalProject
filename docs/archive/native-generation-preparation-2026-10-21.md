# Original-input native generation preparation

October 21, 2026, following the merged native installer trial. This work advances
the execution boundary from developer-cache startup/body objects to actual
regeneration from verified player PE images. It does not advance native gameplay
acceptance: **131/144 remains unchanged**. No commits, uploads or publication.

## Implemented

October 22 continuation: [source installer integration](source-installer-integration-2026-10-22.md)
records successful full generation/link/menu launch, SDK-free split linking,
the bundled preparation EXE, signed update activation and the built private
installer. A separate fresh packaged first-install compile is running. The
running/pending notes below describe the historical October 21 state.

`tools/native-preparation/` exports metadata-only recipes, stages the existing
LLVM 21.1.8/Remill tools and authored ABI/FP lowering, and regenerates native
objects using explicit original-input and derived-codec paths. Player-side code
does not read checkout reports, disassembly ledgers, saved LLVM IR, old object
files or captured state. Original executables and DLLs are never executed.

The normal recipe covers all **37,201** objects selected by the merged host.
Every successful result must match the selected object's SHA256 exactly. This
includes its optimizer profile, required strict x87 behavior, codec timing
preservation, symbol mappings and restored non-executable COFF timestamp.
`merge-r7` uses its reviewed strict/flat-memory passes; `merge-r8-codec` does not
inherit those flags. Unknown profiles and failed ABI/CFG checks reject.

Fresh startup/control generation reproduces **all ten additional startup
objects** and **137 heap/attach objects**, covering all non-body native inputs in
the selected link. The portable tool payload contains pure authored adapters;
historical capture/report readers are excluded. Recipes store spans/hashes, not
game bytes. Generation takes place entirely in private output directories.

The current COFF O2 control object is
`9c2658a322afbe78d5a499c94ae35a2d0d0e0a41d4197f57c1a5e4c19690bf03`.
The old `MW34_CONTROL_OBJECT_SHA=885197...` compile definition identifies the
historical **O0** input; `reports/m4-crt-entry-control/build-r6/build.json` records
both. The O2 regeneration matches the actual selected linker input; no old
evidence or compile definition was rewritten.

## Meaningful checks completed

- Ninety-five broad ordinary-body samples match exactly, spanning all six input
  images, selected plain overrides, large spans and the codec timing loop.
- All 137 heap/attach objects match exactly (`local/...-r9/Heap/generation.json`).
- Three argument/parser objects, `_initterm`, math-error registration, retail
  entry, command-line writer, authored ABI shim, control and FDIV writer match
  exactly in the r8, r10, r11-v2, r12, r13 and r14 outputs.
- Five authored-only checks pass: PE slicing, malformed sections/headers,
  ambiguous/executable bounds, path escape, streaming JSON handling, and
  exclusion of historical dependencies from extracted adapters.
- Actual one-component generation/resume checks pass: verified resume, corrupt
  object regeneration, and changed-recipe refusal (`local/...-r15/checks.json`).
- The private link plan accounts for **37,348 generated objects** and **seven
  existing authored host objects**. No game-code input lacks a generator.
  Invoking the link before body completion rejects the first missing object and
  creates no output directory. It does not fall back to old objects.

All abbreviated local paths above begin `native-preparation-20261021` after
`local/`. The latest 340 MB tool staging is `local/native-preparation-20261021-r14/tools`.
It includes compiler/lifter binaries, pure authored translators and upstream
LLVM/Remill notices. LLVM's exact-version notice was obtained from its official
`llvmorg-21.1.8` source tree; no game content was downloaded.

## Running full regeneration

The sole full-body job is outside the checkout:

`D:/MW3NativePreparationTrial-20261022-r1`

It started October 21 at 20:54 local time. Wrapper Python PID **70300**, producer
PID **80384**, two workers, original exec session **75542**. Inspect live process
identity before interacting; PID values alone are not permanent identities.
The protected controls Python processes 6536/5196 and unrelated server 4164
were preserved. No SQLite access or duplicate body job was started.

`generation.log` holds progress. `Bodies/generation.json` is written only upon
successful full completion; its absence means completion is unproven. The job
has already passed 7,000 exact objects, but **37,201/37,201 is still pending**.
This initial prototype is slow; installation time needs improvement before
offering it as the easy playtester setup.

Its frozen `translate.py`, `Tools/`, recipe and `Bodies/session.json` belong
together. Do not replace that producer with the subsequently extended checkout
version: resume identity deliberately includes producer SHA256. To resume an
interrupted job, first verify no matching producer is alive, then use that
outside copy with the identical arguments and `--resume`. Do not duplicate it.

Verified original inputs are the fresh trial installation at
`D:/MW3InstallerProvidersTrial-20261021-r2/OriginalGame`. The explicit codec is
`D:/MW3MergedInstallerTrial-20261021-r2/UserData/original-inputs/9d066dbdb0b9903c2afb07284d609c7d3ed3278245040490e9805d4cd717958f/Ir50_32.base11000000.dll`.

The local-only candidate list and complete link plan are
`local/native-preparation-20261021-r14/link-candidates.json` and
`local/native-preparation-20261021-r14/local-link-plan.json`.
`local_link.py` rehashes every input before linking and requires a fresh output.
It still needs the developer's existing authored object compilation and Windows
SDK. A successful private link is not evidence of a portable installer.

A sequential background continuation was started at 21:26 local time, initial
PowerShell PID **77460**. Its frozen scripts, input pins and plan are under the
outside trial's `FinishTrial/`. It checks the original producer's PID **and
creation time**, waits for that existing process to finish, requires a complete
matching 37,201-body receipt, verifies its helper/linker pins, and then invokes
the private link in the Visual Studio SDK environment. It never starts another
body producer and never deploys, packages or launches the result. The wait has
an eight-hour bound; timeout stops only the continuation, not the producer.

Read `FinishTrial/status.txt`, `failure.txt` if present, and link logs before
resuming work. Success produces `LinkedRuntime/entry_commandline.exe` plus its
`generation.json`. Until that exists and is checked, final linking is pending.
Do not duplicate the continuation while its matching process is alive. The
last observed body progress exceeded 7,800/37,201 with no producer failure.

## Remaining installer work

Finish full regeneration, link with the fresh objects, and test actual native
startup/normal close in an isolated installed Runtime. Keep the working launcher
1.0.14 and normal profile unchanged until that succeeds. Then finish the reviewed
authored-host/tool bootstrap and connect the whole producer to the signed
launcher protocol (`--game --output --version --previous`). The current Python
prototypes are not a complete standalone preparer EXE.

The launcher still needs the real release trust/feed configuration and
clean-Windows install/update/rollback tests. No release signing key or feed was
created. The public preview remains launcher-only. Existing ISO/existing-game
import, source-derived support resources, pack installation and signed update
engine are retained. Texture choices remain pack content; native code supplies
their selection support.
