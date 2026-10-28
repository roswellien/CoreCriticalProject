# Current M4 progress: real heap creation and source publication

The startup experiment now bridges the original `HeapCreate(0, 4096, 0)` call
to Windows. The full host handle stays in a private owner. The guest receives
opaque token `48450001`, and the translated source stores that token in its
heap global before making the genuine call to the heap-mode selector.

This gate ends at selector entry `78003A0C`. Each experiment releases its owned
host heap afterward. The captured guest global retains the diagnostic token;
it does not represent a live resource after cleanup. No heap mode, complete
initializer return or allocator result is claimed.

The [heap creation review](m4-crt-heap-create-review.md) records the source
boundary, API model, ownership proof and test receipts. All 26 earlier guest
objects are reused unchanged. This step extends verified execution of the
existing translated initializer; it adds no new guest object or initializer
root.

Both production builds passed all **72 scenarios**, including 70 actual heap
creations paired with successful destruction of the same full handles. The
independent compiled corpus passed **132 cases and 6,198 assertions**. It also
checked actual live heap membership, validation before release, membership
after release and duplicate cleanup. The root independently compared 48
ordinary sequences across all 31 checkpoints, with 116,986 checks and 1,620
selected corruption denials.

Twelve additional independent cases verified nonzero Windows error preservation.
Together, production and independent workers created and released **150 real
heaps**. The [accepted evidence](../../reports/m4-crt-heap-create-root/root-acceptance-r1/report.json)
keeps source modeling, compiled fixtures and actual API ownership proof separate.

M4 remains active, with selected initializer coverage **27 of 144**. The next
gate is the genuine heap-mode selector, including its stack-probe and OS-query
dependencies. Mode-specific initialization and allocation, locale ownership,
complete parser sizing, argument outputs and environment ownership follow.
Application initialization, a standalone x64 window and menus remain unfinished.

Only isolated x64 research workers run for this boundary. A game test is not
required yet. Earlier accepted reports and status documents remain frozen.
