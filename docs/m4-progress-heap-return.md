# M4: heap initializer return

This gate continues the original heap initializer after its genuine selector return. The source publishes mode **1**, executes its success PUSH and POP, and returns **1** to the original caller at `0x78001843`. Execution stops before the caller's TEST and argument cleanup. The research handle remains live through the return checkpoint and is released afterward.

All **38 existing x64 objects** and both FDIV libraries are reused unchanged. This adds eight executed source instructions and four checked memory accesses. The combined bounded path is 59 instructions, 35 source accesses, five source calls and three source returns. Its 192 executed bytes remain within the existing 2,086-byte source identity.

The independent model and native captures cover **44 complete checkpoints**, carrying the full guest State, floating-point state, runtime CPU and 21 mapped pages. Actual Windows version-query results drive the source branch. The lower stack page remains declared research input; original stack-growth equivalence is unproved.

The author and independent harness passed **316 integrated native scenarios**. The author witnessed 68 genuine mode stores and 52 initializer returns, including controls that fail after those effects commit. The root observer compared all 48 ordinary captures with 304,892 checks and 5,192 selected corruption refusals; a separate complete-capture audit passed 16,944 comparisons.

The selected initializer inventory stays **27 of 144**. This completes the measured mode-1 return path of the heap initializer; remaining allocator modes, persistent application ownership, locale, argument parsing and full CRT startup remain open. Standalone native menus remain an M4 objective, and native Training remains an M5 objective.

The next gate is the original caller at `0x78001843`: verify its return-value test and argument cleanup, then recover and admit its next startup dependency. The complete-game native launch remains pending.

Current evidence is recorded in [the technical review](m4-crt-heap-return-review.md). The previous accepted gate is [the native version query and selector return](m4-progress-heap-version.md).
