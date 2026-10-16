# Pirate's Moon native host work

This target reuses the MW3 native host, guest memory, services and Remill/LLVM
pipeline with a separate exact input profile, dispatch and executable. It is
experimental. A successful build does not establish a live menu.

The current validated slice is live Vulkan menu -> Options -> menu -> Quit/OK,
with normal native dependency detach and exit code zero after frame 210.
All 210 scene fingerprints match the original comparison reference. This is
experimental evidence, not M4 admission; missions and cinematics remain open.

With the current local build and PM CD mounted at `H:`, physical input is the
default:

```powershell
./tools/pirates-moon/play.ps1 -MediaDrive H: -NoFmv
```

For the verified scripted sequence:

```powershell
./tools/pirates-moon/play.ps1 -MediaDrive H: -NoFmv -Frames 300 -Dump 30 -Script tools/pirates-moon/input-menu-options-quit.txt -Clock 50
```

Read `docs/pirates-moon-native-startup.md` for recovered boundaries, executed
results and remaining blockers. Do not copy MW3 addresses or apply its
game-specific `--x87-noexc` optimization to PM.

The default launcher selects hardware rendering through the original PM registry
settings in `games/mw3-pirates-moon/config/native-registry.txt`. It validates the
five pinned 8 MB hardware texture banks before declaring that component installed
in its private overlay. The source installation lacks the installer's registry
keys; leaving those absent makes PM fall back to its uninstalled software renderer.
`-Registry PATH` selects an explicit alternate overlay for a run; `-Registry ''`
leaves the copied installation's configuration untouched.

## Inputs and translation

The default installation is `MW3-PiratesMoon/`. `target.py` verifies its game,
MSVCRT, MFC42, MSVCP60 and Mech3Msg before analysis. Optional `--installation`
selects an exact copied installation. No files are downloaded.

```powershell
python -B tools/pirates-moon/target.py MW3-PiratesMoon
python -B tools/pirates-moon/translate.py closure reports/pirates-moon/startup-r1/closure.json --initializers
$sha=(Get-FileHash reports/pirates-moon/startup-r1/closure.json).Hash.ToLower()
python -B tools/pirates-moon/translate.py lift reports/pirates-moon/startup-r1/closure.json $sha reports/pirates-moon/startup-r1/lifts-r1
```

Closures are static candidates, not completeness evidence. Add `--root 0xADDRESS`
for an observed missing entry and its direct closure. Lift results retain failures;
unlifted or unsupported instructions stop visibly if reached. Outputs must use
fresh names under ignored `reports/pirates-moon/`. Never regenerate base MW3's
dispatch includes for PM. Heavy runs should not overlap existing jobs.
Supplemental lifts can pass `--skip PREVIOUS_LIFT_DIRECTORY` repeatedly to avoid
retranslating entries already in matching closed PM reports. Dispatch generation
still verifies every linked object's identity and source bytes.
For a large recovered closure, `lift --root 0xADDRESS --max-depth N` selects
only that root and N levels of recorded direct/callback edges. The closed report
records the selection. Missing continuations/targets still stop explicitly;
this is incremental compilation, not completeness or accepted-game evidence.

`closure --root 0xADDRESS --max-depth N` also bounds the initial scan itself.
It visits the shortest recorded call depth first and records that depth limit
in the closure. Use a small limit for an observed missing callback, then grow
from actual faults. This avoids scanning unrelated deep descendants before
compiling a small repair; omitted targets continue to fail explicitly.

## Build and run

After closed lift reports exist, generate an isolated host profile and dispatch.
Pass one `--lift DIRECTORY REPORT_SHA256` pair per report, ordered oldest first;
later reports replace entries at the same address, including failed repairs.

```powershell
$sha=(Get-FileHash reports/pirates-moon/startup-r1/lifts-r1/report.json).Hash.ToLower()
python -B tools/pirates-moon/generate.py reports/pirates-moon/startup-r1/host-r1 --lift reports/pirates-moon/startup-r1/lifts-r1 $sha
./tools/pirates-moon/build.ps1 -Generated reports/pirates-moon/startup-r1/host-r1
./tools/pirates-moon/play.ps1 -Frames 120 -Dump 30 -Hidden
```

The build reuses prepared shared CRT/bridge object settings from the existing
MW3 native build cache (`-Baseline`), and links PM's own verified dispatch objects.
It produces `shared-host/pirates_moon_native.exe` in its separate build directory.
The PM driver uses a distinct `research_game` runtime domain. It does not register
or credit MW3's accepted game translations.

The launcher copies root files to a fresh writable local installation and links
asset directories. Logs and frames go into a fresh PM report directory. It
does not launch the original x86 executable. Frame-budget termination is a smoke
test, not normal shutdown acceptance. Real input is the default.

PM performs its original disc-file/content check. With both game CDs mounted,
the earlier base-MW3 CD can be selected first. Pass `-MediaDrive H:` (using the
actual PM CD letter) to expose that same Windows CD device through a temporary
user-level `B:` alias. The launcher requires `B:` to be unused, waits for PM to
exit, and removes only its exact alias in `finally`. It does not unmount other
media or synthesize drive/file results. If the original disc check fails, the
game's dialog path remains an explicit unsupported boundary.

For menu-focused validation, `-NoFmv` appends the original PM `-nofmv` option
to its guest command line. The retail CRT and PM's own argument parser still
run; no guest code or state is patched to skip the movie. The default keeps
the original opening-movie choice. Cinematics remain separately unverified.

## Original-side comparison preparation

`prepare_original.py local/pirates-moon-comparison/NAME` prepares a fresh local
comparison installation and an adapted copy of the existing Win32 comparison
hook sources. It verifies the PM inputs and hardware banks, renames only CRT
import strings to select the supplied CRT, and selects the recovered PM entry
and three timestamp instructions. Original instruction bytes stay unchanged.
Local dgVoodoo files come from `MW3/`; no files are downloaded or published.
The output includes derivation hashes. Build its `hook-source/` with a Win32
Visual Studio CMake generator into a separate comparison build directory.

This is a research reference for the original game. The native PM target and
launcher never load it. Comparisons must select the same registry, input,
clock, media and `-nofmv` choice on both sides. Budget termination is not a
normal-quit pass. The original visual reference and current native boundaries
are recorded in `docs/pirates-moon-native-startup.md`.

## Narrow checks

```powershell
python -B -m unittest discover -s tests -p test_pirates_moon.py -v
python -B -m unittest discover -s tests -p test_binary_tools.py -v
```

The shared `tools/m4-runtime` CMake tests also exercise research-image identity,
translation-domain isolation and source binding on a project-authored PE.
