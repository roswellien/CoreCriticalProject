# Verified live native address-helper test

On 2026-10-08 the address helper at `0x409ED0` was connected to a persistent
native x64 worker using the unchanged accepted generated G2 objects. This
additive launcher passes its offline and hardware bridge gates. A subsequent
real original-game call returned verified compiled x64 output, and the user
confirmed launch, entry into Training and quit through this launcher.

Run `Launch MW3 with Native Helper.cmd` in the project root, load Training,
play briefly and quit. No visible gameplay change is intended. This test is
separate from the native numeric launcher whose Training session the user
already confirmed.

Live evidence:

- [Independent actual-call verification](../../reports/mw3-live-native-helper/20261008-065208-629532-8918caf7/independent-live-verification.json)
- [User Training confirmation and exit/monitor receipt](../../reports/mw3-live-native-helper/20261008-065208-629532-8918caf7/user-training-confirmation.json)
- [Actual game trace](../../reports/mw3-live-native-helper/20261008-065208-629532-8918caf7/game.jsonl)
- [Actual-session immutable build](../../reports/mw3-live-native-helper/20261008-065206-622-53b089a5/build.json)

The actual invocation used stack argument zero from caller `0x405173`, returned
EAX `0x13B189E8`, EDX zero and flags `0x246`, and matched the original CPU,
full seeded FX512, ENV28 and unchanged original 4096-byte shadow page. It
performed exactly two generated reads and one completed `RET 4`. Input CW
`0x027F`, SW `0x0120`, empty x87 tags and MXCSR `0x1FBD` carried unchanged;
FP remained opaque integer-source transport. The independent observer rejected
25 deliberately corrupted records. All 33 fresh source pins, both frozen objects
and the saved worker/hook/launcher binaries match their build and launch receipts.

The game exited with code zero. Its passive monitor ended cleanly with no alerts,
errors or lost segments. The user's report confirms Training entry and quit;
the trace does not associate the helper invocation with a specific Training
action. Extended gameplay stability, visual defects and frame timing remain
outside this session's evidence.

Preparation evidence:

- [Immutable build](../../reports/mw3-live-native-helper/20261008-063252-213-dc1ad94b/build.json)
- [O0 compiled worker preflight](../../reports/mw3-live-native-helper/20261008-063316-141101-ee7da4e9/O0-preflight/report.json)
- [O2 compiled worker preflight](../../reports/mw3-live-native-helper/20261008-063316-141101-ee7da4e9/O2-preflight/report.json)
- [Independent hardware thunk verification](../../reports/mw3-live-native-helper/20261008-063316-141101-ee7da4e9/independent-selftest-verification.json)
- [Exact saved O2 worker idle check](../../reports/mw3-live-native-helper/20261008-063316-141101-ee7da4e9/O2-idle-preflight/report.json)
- [Launch preparation](../../reports/mw3-live-native-helper/20261008-063316-141101-ee7da4e9/launch.json)
- [Independent saved-build audit](../../reports/mw3-live-native-helper/contract-review/20261008-063616-155023-7e5307f3/report.json)

Each worker variant completed 2,435 generated executions, 13 request/transport
denials, 66 corrupted-output denials and two startup identity denials, with a
clean EOF exit. Tests cover 598 directed stack arguments, base-address wrapping,
512 random cases, all 128 arithmetic/DF combinations and full remaining flag
preservation. CPU results, both generated reads, a completed return and all
4096 owned page bytes are checked from BEFORE-only predictions. FP/ENV variation
in worker tests is opaque transport and never loaded into host FP hardware.
The exact saved O2 executable also remained alive across 65 seconds without a
request, completed the next generated call and exited cleanly when its server
closed. This covers menu idle time before the Training load triggers the helper.

The returning x86 thunk also passed 64 actual hardware cases against the original
copied leaf. It preserved full admitted flags, opaque seeded FX512, separate
ENV28, the caller's page and exact `RET 4` cleanup. Those cases cover x87 depths
0/1/3/7, CW `0x027F`/`0x037F`/`0x0A7F`, MXCSR `0x1F80`/`0x1FA0`, eight varied
XMM banks and DF/OF combinations. A separate source model independently checked
every captured BEFORE/native/original/page record and rejected 1,600 deliberate
receipt corruptions.

The bridge redirects only the admitted five-byte CALL at `0x40516E`, returning
to `0x405173`. It retains all 22 original helper bytes and verifies the loaded
source and caller route. The actual original comparison executes that unmodified
function on a guarded private stack. After matching, EAX, EDX and arithmetic
flags from the actual generated x64 execution are returned to the game. All other
admitted CPU/FP state carries unchanged. The hardware flag domain is `0x202`
plus arithmetic/DF bits; the actual SS selector must prove base zero. Unsupported
inputs receive explicit rejection and no live native credit.

Only observed CPU/flags are imported into an authored zero-seeded hidden Remill
State. ESP/EIP and two read-only argument/return slots are explicit owned-stack
projections. The source is integer-only, so FP is preserved separately as opaque
transport rather than numerically reinterpreted. C++ scratch runs under a clean
host FP environment after guest capture, with literal guest state restored on
return. Actual native publication, user-confirmed Training entry/quit and a clean
monitored exit now pass this bounded live test. The numeric initializer's separate
live test also passes; further work returns to shared native startup integration,
including initialized CRT data consumption and numeric-max carry from the preceding
26 initializers.

See the [protocol and replay documentation](../../tools/in-game-native-helper/README.md).
M4 remains active with 26 connected initializers; this component test does not
establish native startup, menus or a fully native game executable.
