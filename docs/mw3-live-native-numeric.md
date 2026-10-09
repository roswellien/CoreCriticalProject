# First live numeric initializer x64 publication

On 2026-10-08, one real MW3 startup invocation of `0x4C19F0` used the
unchanged translated x64 wrapper, complete body and MSVCP50 provider in a
separate native worker. The original x86 game consumed its verified global
output and returned FP state through an authored x86 bridge. The game remains
x86; this does not complete M4 or promote the accepted joint startup count.

Evidence:

- [Independent live verification](../reports/mw3-live-native-numeric/20261008-060333-738476-c0b14d82/independent-live-verification.json)
- [Actual hook trace](../reports/mw3-live-native-numeric/20261008-060333-738476-c0b14d82/game.jsonl)
- [Immutable build](../reports/mw3-live-native-numeric/20261008-060203-337-2f1c691f/build.json)
- [Narrow MXCSR carry preparation](../reports/mw3-live-native-numeric/session-mxcsr-r1/preparation.json)
- [Worker idle validation](../reports/mw3-live-native-numeric/session-mxcsr-r1/worker-idle-validation.json)
- [Monitor sharing regression](../reports/mw3-live-native-numeric/monitor-sharing-81a227c7/regression.json)

The actual callback compared full CPU/flags, defined numerical FX fields,
separate ENV28 and 44 output bytes against the unmodified original. The
independent BEFORE-only observer checked all 22 source memory events and
three completed routes and rejected 17 corrupted receipts. Observed input was
CW `0x027F`, SW `0x0020`, empty TOP-zero x87 and MXCSR `0x1FA0`. SSE precision
status carried unchanged. The exact current CRT `CALL EDI` route and owning
table slot were recovered and pinned from the real callback.

The first restricted launch failed before process creation with Win32 error
623. A subsequent real callback honestly rejected MXCSR/caller admission;
its captures remain preserved. The final run applied native output, monitored
the responsive process for about 95 seconds without alerts or event loss and
observed normal exit code zero. Exit cause and visible menu/gameplay behavior
are not inferred from a zero code or responsive windows.

Scope remains narrow: hidden Remill State starts from an authored zero seed;
stack/return/FS/raw IAT are explicit transport projections; independent live
credit covers empty x87 entry only. The original comparison holds its
initializer thread; other game threads are not suspended. The private Session
copy changes only its MXCSR guard to admit `0x1F80` or `0x1FA0`; prior canonical
acceptance remains an ancestor proof, not blanket acceptance of broader state.

The [launcher and protocol documentation](../tools/in-game-native-numeric/README.md)
describes replay and failure behavior. On 2026-10-08 the user confirmed launch,
Training gameplay and manual quit without issues through this launcher. The
[fresh Training receipt](../reports/mw3-live-native-numeric/20261008-061318-042559-807ce824/user-training-confirmation.json)
links a second independently verified actual native callback, original comparison,
exit code zero and an exited monitor with no alerts or lost segments. This is a
session stability check; frame timing, visual defects and extended play remain
outside the passive monitor's coverage. Further live function replacement needs
its own ABI, dependencies, input admission and original comparison.
