# Current features, readability cleanup and installed support

The user requested finishing setup using the new native compile, clarified that
alternate textures belong in packs, and explicitly requested merging the builds.
The alternate images remain in `.mw3pack` files. Native code supplies per-instance
skin selection and the pack readers; it does not embed those images.

The completed readability compile at
`local/remaster/readability-full-compilation-20261021/build/entry_commandline.exe`
has SHA256 `470096a7b12eed44082d1a6057b1d3ec04d21fbc1c5a2fb41f36cc8c18f0009f`.
It used the older detached-cockpit base and links existing translated objects.
It was not substituted wholesale for the selected feature host.

## Merged build

`local/remaster/gpu-native-installer-merged-r1/build/entry_commandline.exe`
has SHA256 `8194028a835c85e46b0963864ea04acfe400749671b1eb7f28ae63a51a2f5532`.
It starts from the current all-skin feature host
`a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c`, adds explicit
installed original-provider bindings, and merges all 21 audited readability files.
Each of those 21 files was byte-identical between the feature branch and the
readability branch's common pre-cleanup base. Each compiled donor file was checked
against `reports/readability-20261021/full-compilation/host-compiled-inputs.json`.
No newer feature conflict was overwritten. All 120 initial source pins were
verified; changes are confined to these 21 files and `main_v2.inc`. The list of
37,201 translated object inputs is unchanged.

`prepare_install_host.py` maintains this private build preparation. It rejects
source/executable drift, changed common-base files, changed compiled donors and
existing output directories. It is not the missing end-user native generator.
An initial provider-only successor was built separately and retained as
`gpu-native-installer-all-skins-r1`; the final selected build includes readability.

The execution boundary advanced is the current feature host plus installed user
support paths reaching an actual external installed menu and normal shutdown.
Gameplay/renderer fidelity acceptance remains 131/144; no new formal credit.

## Integration checks

Private installed trials are under `D:/MW3MergedInstallerTrial-20261021-r1` / `r2`.
The first content launch rejected the rebuilt mech packs because their new
reference host is `a99afd...`, rather than the historical earlier host. Exact
compatibility admissions were added for the reviewed successor; no wildcard
admission was introduced. UI/movie readers remain byte-identical, and environment
and mech compatibility preserve the current feature behavior.

The r2 actual C# installed launch used all five existing enabled packs, fresh
per-trial generated support resources, original data from the prior fresh ISO
installation, and an external Runtime. The live menu displayed 53 HD sprites and
the enhanced background. Normal Alt+F4 completed `ExitProcess(0)` after **2,304**
presentations, including provider DLL detach; both native and coordinator exits
are zero. A preceding automated menu click did not select Quit; that click alone
is not counted as a successful shutdown. No owned native process needed stopping.

The native import table still requires MSVCP140/VCRUNTIME140/VCRUNTIME140_1.
`stage_native_dependencies.ps1` copies these three app-local prerequisites from
the existing VS 14.51.36231 redistributable directory after validating Microsoft's
Authenticode signatures, then registers their hashes/sizes in the private runtime
manifest. It performs no system installation or download. The source identities
are retained in each trial's `native-dependencies.json`. This is same-machine
testing, not a clean-OS proof or a new distribution clearance.

The complete C# launcher checks and 29 targeted Python pack/runtime checks pass.
One initial test command used the wrong working directory and was corrected;
the subsequent actual suite completed successfully. Native builds used two
parallel compiler jobs sequentially; no other long job was duplicated or stopped.

## Deployment and remaining installer gate

Launcher **1.0.14-preview** is deployed at `tools/remaster-launcher`, and the
ordinary native profile selects the merged build. The original selected profile
is retained in `reports/merged-installer-20261021-r1/selected-before.json`.
Deployment preserved the user settings hash, existing pack choices and graphics.
The ordinary GUI Play path was then tested at the retained 3440×1440 settings.
It played the original movie, reached the enhanced live menu and returned via
normal Alt+F4 with native exit zero after **1,297** presentations. Its session is
`%LOCALAPPDATA%/MW3Remaster/sessions/aaa1f6b94d604e32bb606fd5a80a9968`.
This is separate from the installed r2 trial's 2,304 presentations. The native
processes were allowed to shut down normally; no force termination was used.

The rebuilt EXE is
`reports/merged-installer-20261021-r1/installer/MW3Remaster-Launcher-Preview-Setup.exe`,
70,030,929 bytes, SHA256
`6ad741ffbe74fd6dfa39ccde7c910620e9f96e29a0b602fb44ce89ef08a5a6e5`.
It remains launcher-only, deliberately excluding private generated Runtime.

The new compilation does not resolve the central end-user dependency: the host
and startup object still link previously generated translation outputs from
development `reports/` and `build/`. The current lifters also depend on private
recovery/closure graphs, hardcoded workspace paths and a developer toolchain.
Those need a source-only, portable recipe that extracts from verified player
images, produces all selected translated objects and startup inputs, and links
the host without developer caches. Existing generated LLVM IR/object files cannot
be shipped as a substitute under `docs/legal.md`.

The signed update/preparation protocol is ready to invoke that producer, but the
actual whole-game producer, release feed/trust provisioning, and clean-Windows
installation/update tests remain open. No feed, signing identity, original game
file or generated game binary was uploaded or publicly released. The external
Runtime is a private integration trial, not an end-user distribution.

The subsequent [original-input generation work](native-generation-preparation-2026-10-21.md)
now reproduces the startup and heap objects from verified player inputs and
starts the complete 37,201-body run outside the checkout. Full generation,
fresh-object linking and standalone installer integration remain pending.
