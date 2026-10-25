# Performance monitor and update delivery

The Graphics & Display tab gains a saved **Show performance monitor in game**
checkbox for the native engine. It defaults off and takes effect on the next
launch. The explicit saved choice overrides old profile/environment defaults.
Rolling video replay remains a separate option and is not enabled by monitoring.

The host overlay measures real time between presentation-path calls, independent
of the original simulation clock. It refreshes four times per second over a
rolling ten-second window. AVG FPS is frame count divided by elapsed time;
AVG Frame Time is the arithmetic mean interval in milliseconds. 1% Low FPS is
the reciprocal of the mean of the slowest `ceil(samples / 100)` intervals.
High FPS is the reciprocal of the shortest interval. Values initially show
dashes. A suspension exceeding ten seconds clears the old window. At extreme
rates, storage is capped at 65,536 intervals. This measures host presentation
cadence, not GPU-only timing or externally measured monitor scanout.

The monitor draws only in the existing host overlay path and changes no guest
memory, simulation timing, gameplay or lighting settings. When off, it performs
no sampling, sorting or drawing. Statistics sorting occurs at the four-Hz display
refresh, not on every frame. The current single line uses a small transparent
text tile on the direct GPU path; the CPU fallback paints only glyph pixels.

The native candidate derives from the tested display-cache host, preserving that
performance fix. `apply_performance_monitor.py` installs the authored header and
the two reviewed adapter changes into a private host snapshot. It rejects an
unexpected old overlay/buffer rather than silently editing different code.
The maintained renderer template is older than the current host, so the current
host is patched in isolation rather than replaced with that template.

## October 23 compact layout

The monitor now occupies one line immediately right of the normal radar and
below the compass. The font changes from 10x14 glyphs to 6x8, approximately a
40% reduction. Labels retain average FPS, 1% low FPS, high FPS and average frame
time. Both presentation paths leave the scene visible between glyphs; the GPU
tile uses zero alpha for its background. Its left-edge aspect correction follows
the radar, and the GPU scene retains the existing no-readback/no-full-frame
host-allocation optimization. Measurement formulas, refresh cadence and saved
on/off preference are unchanged.

The authored monitor checks cover the rolling statistics, disabled behavior,
clipped small targets, the compact HUD bounds and preservation of scene pixels
between glyphs. Native placement validation and selected-host identity are
recorded privately under `local/work-ahead/performance-monitor-20261023-r1`.
No formal acceptance credit is added; the count remains 131/144.

## Delivering to an existing installation

### Required naming for future releases — October 24, 2026

The owner's naming rule is recorded in the root `AGENTS.md` and supersedes
historical descriptive update filenames in earlier release examples:

| Update target | Required filename | Example |
| --- | --- | --- |
| Game runtime | `<version>.<game-abbreviation>update` | `1.0.34.mw3update` |
| Core Critical Launcher | `<version>.ccupdate` | `1.0.34.ccupdate` |

The stem is the public release version, without prefixes such as `corecritical-`
or descriptive runtime/task labels. The game abbreviation is its registered
file stem, such as `mw3`, `mw3pm` or `mw4`; naming does not establish runtime
support for an otherwise unimplemented title.

The current signed-metadata-plus-payload contract remains in force: keep the
matching payload beside the update as `<version>.zip`, preserving signatures,
hashes and references. Keep launcher and game pairs in separate directories
when their version numbers match, so their payloads cannot overwrite each other.
If an extra download wrapper is offered for browser compatibility, identify the
version and target in its name (for example `1.0.34-mw3-update.zip` or
`1.0.34-cc-update.zip`) and include the correctly named metadata/payload pair.
Never disguise an ordinary ZIP as `.mw3update` or `.ccupdate`.

Packaging scripts and release checks must produce these names before the next
publication. Existing signed releases remain historical evidence; do not rename
or replace them merely to apply this prospective rule.

The existing `.mw3update` format is signed metadata, accompanied by a matching
ZIP (or a signed HTTPS download URL). The current updater prepares and selects
a versioned runtime/coordinator and retains the previous version for rollback.
It does **not** replace the launcher executable. A runtime package alone therefore
cannot add this checkbox to an older installed launcher.

For this release, use the supported two-part delivery:

1. Upgrade the launcher to 1.0.18 with the normal setup upgrade. Preserve the
   existing trust key, user settings, packs and original inputs. This adds the
   checkbox and its profile binding; it does not require reinstalling content.
2. Build the release **split host** from the display-cache + monitor sources,
   retaining the exact existing translated-module contract. Review the resulting
   exact host identity for existing resource-pack readers. The developer's
   monolithic native test EXE is not a distributable update payload.
3. Stage that authored host, current coordinators, pinned recipes and source
   preparation tools with `stage_preparer.py`. Set the release profile's
   `native.performance_monitor_version` to 1; older runtimes are explicitly
   rejected when monitoring is requested, including after rollback. Reuse the already generated game
   module only if its pinned identity matches, otherwise generate locally from
   the player's verified original inputs. Package no original media, translated
   machine code or local player files.
4. Build a signed `mw3-source-runtime-v2` update using
   `build_source_update.py`, with a unique version, a strictly increasing sequence
   and **minimum_launcher_version 1.0.18**. Set that field before signing; the
   existing builder's default is still 1.0.17. Use the already trusted update key,
   and retain Windows publisher signing as a separate release step.
5. Verify signature/hash, prepare and activate on an isolated copy of the current
   installed release, confirm the cache fix and all four monitor values, then
   exercise rollback and interrupted preparation. Confirm settings, packs and
   saves remain intact. Deliver matching `version.mw3update` and `version.zip`.

No signed release package or upload is claimed by this implementation. The native
developer build and local launcher deployment are separate from player delivery.

## A future single-file or single-action update

To deliver launcher UI and runtime together through `.mw3update`, add an explicit
signed launcher-update contract and a small external updater. Stage and verify
the new launcher first; after the launcher exits, the helper atomically replaces
its allowlisted application files, starts the new version and restores the old
files if replacement fails. The runtime then uses the existing version selection
and rollback path. Never overwrite user storage or a running executable. Older
launchers need a one-time setup upgrade to understand this new contract.

If one downloadable file is desired, add a bounded bundle container carrying the
signed metadata and ZIP. Current `.mw3update` imports expect JSON metadata; naming
a ZIP `.mw3update` does not make it compatible. Both extensions require dedicated
signature, path containment, interrupted replacement and recovery tests before
being advertised as supported.

This advances the launcher setting -> native presentation overlay boundary.
Formal gameplay acceptance remains 131/144.

## Validation and local installation

Launcher 1.0.18 and the isolated monitor host are installed in the developer's
normal launcher. The selected executable SHA-256 is
`bcdc770655f150423a8df3b2fad3446a8e1f7f81ceff7a82a21a6ad8770fb921`.
Relative to the display-cache host, only `vk_scene.hpp`, `gpu_hud.inc` and the
new authored `performance_monitor.hpp` differ. Reader compatibility adds this
exact identity to previously reviewed admissions; no wildcard is added.
Prior launcher binaries, profile and settings remain in the private evidence
directory `local/work-ahead/performance-monitor-20261022/` for rollback.

Authored C++ checks cover unequal frame intervals, the slowest-one-percent mean,
the 101-sample rounding boundary, fastest frame, startup, invalid clock samples,
window expiry, suspension, disabled drawing and small-target pixel bounds.
The complete launcher checks pass, including saved monitor state, explicit
on/off profile bindings and rejection of an old profile's stale enabled value.
All 12 prepared mech/environment pack checks pass. The source installer is
idempotent and rejects an unrecognized GPU overlay buffer before renderer writes.

A 2,800-frame Training comparison with monitoring off matches every original
draw-log row and all four 3440×1440 captures from the display-cache predecessor
byte-for-byte. The fixed diagnostic-clock budget exit is expected and is not a
normal shutdown check. See private `fidelity.json`, `source-pins.json`, native
build logs and `launcher-checks-final-r2.log`. An earlier concurrent fixture
attempt correctly hit the save-backup guard while this isolated Training process
was running; rerunning after the game stopped passed the full suite.

Normal session `58656094502e4e858f5bfb4d1e5eb8ec` prepared all 11 packs, displayed
the four monitor rows during native presentation and reached the enhanced menu;
normal Alt+F4 shutdown returned exit 0. The existing 32-bit enhanced menu
composition does not draw this gameplay overlay. Monitoring was restored off
after the check; all preexisting saved settings, including replay off, were
preserved. The final capability guard also passes the full launcher suite in
`launcher-checks-capability.log`.

Monitoring-on Training also completes 1,600 diagnostic frames. All original
frame/draw-count/hash triples match the monitoring-off run. Two captures differ
only inside the top-left overlay rectangle (within 555×157 pixels at this
resolution); gameplay pixels outside it match exactly. The four values are
readable in the Training capture. Extra host HUD submissions and overlay mip
uploads are expected when on; complete diagnostic rows consequently differ.
See `monitor-on-verification.json` and the two retained full-resolution captures.
These capture-enabled runs do not measure monitoring overhead.
