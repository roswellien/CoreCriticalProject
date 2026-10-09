# Live numeric initializer x64 test

Use **Launch MW3 with Native Numeric.cmd** in the project root. Close any
existing MW3 session first. The launcher builds pinned binaries, checks their
transport and return path, starts the game before its entry point, and connects
initializer `0x4C19F0` to a separate native x64 worker. The research owner stays
alive until the game exits and records its exit code.

The original game is x86. Its CRT initializer table slot `0x5E016C` temporarily
points to the authored x86 bridge. The wrapper, body, provider and on-disk game
remain unchanged. The worker executes the frozen generated x64 objects for
`0x4C19F0`, `0x4C1A00` and MSVCP50 `0x780C10F0`. This preserves gameplay;
there is no intended visual change or performance gain from this initializer.

Each actual call captures CPU/full flags, FXSAVE, separate legacy ENV and the
44 output bytes before dispatch. The worker imports observable state with
explicit virtual stack/return/FS/IAT projections and an authored hidden State
seed. The hook runs the unmodified original on a guarded private stack and
compares CPU, numerical FP state, all 28 ENV bytes and 44 output bytes. Only
after agreement does it publish the worker's output and restore native FP
state to the real caller. It validates 22 memory events and three completed
translated call routes. An input rejection returns the original result with
`native_applied:false`; an execution failure or mismatch stops the owned game.

The measured live input has CW `0x027F`, SW `0x0020`, an empty x87 stack and
MXCSR `0x1FA0`. A separately pinned Session copy adds only admission of that
preserved SSE precision flag alongside `0x1F80`. It does not clear or normalize
the captured game state. The canonical Session, translated objects, IR and
shared runtime remain unchanged. Caller admission currently pins this host's
32-bit Windows CRT and its observed `CALL EDI` route. Different providers,
relocations, CRT versions or unsupported FP inputs require separate review.

Fresh evidence is saved under `reports/mw3-live-native-numeric/`. `game.jsonl`
distinguishes synthetic checks from actual `game_call` records. The latter
contains hashes and paths for `.before.bin`, `.native.bin` and `.original.bin`
captures. The independent `verify_live.py <run-directory>` checks the empty
x87 entry route from BEFORE data and rejects corrupted receipts. Full M4,
arbitrary floating-point inputs and a whole-game x64 executable remain open.

The first successful actual run is
`20261008-060333-738476-c0b14d82`. Its independent verification passed one
applied native callback and 17 corruption checks. Passive process/log monitoring
reported no alerts or dropped events during approximately 95 seconds, then
recorded exit code zero. This is a function test; extended Training/gameplay
stability still needs the user's play session.

Build without launching: `launch.py --prepare-only` through the installed
Python runtime. Existing immutable build receipts can be selected with
`--build-report <build.json>`. Original game bytes and private captures stay
local. The passive monitor does not capture debug exceptions, frame timing or
visual glitches; its logs cannot establish absence of those issues.
