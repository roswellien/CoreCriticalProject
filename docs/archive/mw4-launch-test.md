# MW4 Mercenaries normal-launch test

Tested 2026-10-09 following the user's requests to launch the installed game
and then mount Disc 1 and retry. **None of the three attempts reached the game
menu.** The first two crashed with Disc 2 mounted. The Disc 1 retry displayed an
administrator-privileges error dialog. Windows explicitly reported a blocked
`Secdrv` driver during all three attempts. No usable gameplay image was recovered.

## Inputs and environment

- Installed target: `D:\Projects\MW34Recomp\MW4\MW4Mercs.exe`, launched with
  no arguments and the installation directory as its working directory.
- Launcher SHA-256:
  `fa317099c1336acabd1c1a3e9736d05533c6e19fb6603fa16e31a87d362bf8cf`.
- Protected ICD SHA-256:
  `37cdc4025c5dc2e8c48f22b2e02a2ef296878e5114453de40bcfaa835f0cc39c`.
- OS: Windows 11 Pro, version `10.0.26200`, x64.
- Disc 2 was mounted at `H:` with volume label `MW4MERCS_02` for the first two
  attempts. For the third attempt, it was replaced with the original
  `MW4MERCS_01.iso`, verified at `H:` as `MW4MERCS_01`. Disc 1 remains mounted.
- The repeat used a plain process launch and passive process/memory reads,
  without debugger attachment or target-memory writes. Both input-file hashes
  still matched after that attempt.

## Observed results

| Attempt | Launcher PID | Exit | Application Error record | Fault RVA | Service Control Manager record |
| --- | ---: | --- | ---: | --- | ---: |
| First normal launch | 32432 | `0xC0000005` | 14617 | `0x0000E416` | 16735 |
| Passive repeat | 1860 | `0xC0000005` | 14619 | `0x0000E41F` | 16737 |
| Normal retry with Disc 1 | 10900 | Waiting at error dialog | None at observation | — | 16739 |

The three System events report that `Secdrv` failed to start because its driver
was blocked from loading. The two crash Application events identify the launcher
itself as the faulting module. These are current-machine observations, rather
than conclusions drawn from historical SafeDisc compatibility reports.

The Disc 1 retry started at `2026-10-09T19:49:51.6627524Z` and stayed open at an
**Access Denied** dialog reading “Please login with administrator privileges and
try again.” Computer Use confirmed the exact dialog text. No matching crash
Application event appeared during this observation, and the launcher was still
running. Its administrator wording does not establish that elevation would
resolve the blocked driver. The installed EXE and ICD hashes remained unchanged.

Both retained WER reports list the launcher, system modules and `drvmgt.dll`;
neither module list contains `MW4MERCS.ICD`. Computer Use window inventories
found no game or autoconfiguration window after either crashed attempt. Their
final process inventory found no remaining Mercenaries/ICD/autoconfiguration
process. The later Disc 1 retry exposed only the launcher error dialog.

Nine bounded 4-KiB memory samples were obtained from the repeat's launcher at
roughly 10 ms, 510 ms and 1,006 ms after launch. The `.txt` samples changed from
their on-disk bytes while the sampled `.text` wrapper page stayed identical.
The changed `.txt` samples remained high entropy. This establishes runtime
modification of launcher memory; it does not establish a readable gameplay
payload or identify the transformation.

One additional matching PID returned access denied during memory-capable
process opening. Its name/path was not retained by that error branch, so its
identity and role remain unresolved. Passive polling can miss short-lived
processes, and WER's module list describes the crashed launcher rather than an
exhaustive process tree. Accordingly, the result is **no usable gameplay image
recovered**, rather than proof that no payload process could ever have existed.

## Interpretation and execution-plan effect

**Inferred:** the failure is in the protection/startup portion of this retail
installation. The blocked driver is an observed startup obstacle; a complete
causal explanation of the subsequent access violation has not been proven.
Gameplay, rendering and mission behavior were never reached. Mounting Disc 1
changed the visible result but did not establish a working execution route.

The [MW4P-0 gate](mw4-execution-plan.md) remains open. This exact installation
has not provided a working ordinary-launch oracle or readable game-code image
on the current Windows host. The next code-recovery work must establish another
viable reference route, such as a separately admitted user-owned readable build
or a compatible reference environment. Archive and authored tooling work can
continue independently.

Subsequent [online compatibility research](mw4-windows-compatibility.md) found
a source-based conversion matching all three installed protection inputs.
It is now a concrete reference-route candidate; the research itself has not
produced a derived image or successful launch.

## Retained evidence

Private inputs and detailed diagnostics remain in ignored
[`reports/mw4-launch-test-2026-10-09/`](../../reports/mw4-launch-test-2026-10-09/):

- `preflight.json`, `os.json`, `launch-first.json`, `secdrv-status.json`.
- `application-events-first.json`, `system-events-first.json`,
  `application-events-repeat.json`, `system-events-repeat.json`.
- `report-first.wer`, `report-repeat.wer`, `final-state.json`.
- `passive_launch_probe.py`, `passive-repeat.json` and the nine local byte samples.

The Disc 1 retry is retained separately in ignored
[`reports/mw4-disc1-launch-test-2026-10-09/`](../../reports/mw4-disc1-launch-test-2026-10-09/):
`media-before.json`, `media-after.json`, `launch-disc1.json`,
`dialog-observation.json`, `application-events.json`, `system-events.json`,
and the before/after input hashes. The media receipts verify the Disc 2-to-Disc 1
swap and the unchanged MW3 mount at `F:`.

REA's `capture_process_scenario` rejected native Windows PTY capture before
execution because its adapter does not verify descendant cleanup. The repeat
therefore ran through the ordinary local command tool; it is not an REA runtime
Evidence record. Static REA evidence remains in the
[earlier reconnaissance](mw4-reconnaissance.md).
