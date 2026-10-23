# Published runtime update and artwork compatibility repair

The remote report `MW3-Playtest-20261023-043528.zip` confirms launcher
1.0.24 and selected native host `dee5e15e…`. Launch stops in `UiPack.Apply`
before starting native execution: HUD reference `9fd17ba2…` rejects that
published performance host. This report contains only report.json and
launcher.log, with no new native crash. The earlier c1m1 memory fault must
still be retested after this separate blocker is removed.

The C# launcher compatibility list omitted three signed successors already
admitted by the Python environment/mech pack readers: archive repair
`879408f4…`, service history `dee5e15e…`, and call routing `3aae1c6e…`.
The repaired list inherits the existing `d52fbf63…` artwork/movie admissions
for these exact hashes only. Unknown hosts and unrelated pack references
remain rejected; no integrity or signature validation is bypassed.

Read-only comparison of the frozen archive-repair, service-history-r2 and
body-dispatch source snapshots finds identical resource readers:

| File | SHA-256 |
| --- | --- |
| gpu_hud.inc | 0917a516c9c6dbea1b203eefc48261c82c59ead9ebc3483ec663bcc674d8645b |
| vdd.inc | 4f63d7bbdeb9b652b7a4123fe586767bd93b887875889840b670a16d8fceadfe |
| cinematic_paths.inc | 3aec9ebfc0a44684aedb52b917a3482686fa64dd709bea3e0eaccb2d409f83d9 |

The execution boundary repaired is launcher admission of verified UI packs
before native launch. No native code or content is rebuilt. Launcher 1.0.25
includes the correction; the full installer retains the existing signed
archive-repair runtime. An active game update remains selected after upgrade.

The complete launcher fixture suite passes after the implementation change.
Additional fixtures apply an authored HUD pack carrying the actual released
reference to a profile carrying the reported performance-runtime identity,
and check exact successors, case handling, unknown hosts and unrelated
references. These artwork checks pass independently. The actual signed
publication also successfully activates the installed HUD and menu packs
against the exact reported `dee5e15e…` host identity, retaining both sprite
paths and the enhanced menu background. This uses the real pack readers and
does not start a game. A subsequent full-suite
attempt correctly refused update mutation while another worker's game was
running; that process was left untouched. A real-pack profile trial stopped
at missing isolated original-support inputs before reaching UI admission;
it is not gameplay evidence. Formal acceptance stays 131/144.

Private build, signing and delivery evidence is under
`D:/MW3PackCompatibilityRepair-20261023-r1`. The first signing attempt lacked
the portable Azure CLI in PATH; the retry uses the existing authenticated
CLI and produces a valid timestamped Windows signature. The original attempt
and logs are retained. No commit is made.

The signed full installer is published under
`installers/2026-10-23-r1/corecriticalinstaller.exe`, 92,602,144 bytes,
SHA-256 `781abffdbc1b5942eb7643f6d0bb74f304438096738915439fd88b210375fc8d`.
A complete remote readback is identical and retains a valid Windows signature.
The two Setup catalogs now link 1.0.25; performance-update notes direct users
with HUD/menu packs to upgrade the launcher first. Existing performance-update,
asset, ISO and patch links remain. A new installer-upgrade trial and remote
mission retest are not claimed.
