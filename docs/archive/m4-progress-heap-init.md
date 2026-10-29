# Current M4 progress: first heap creation boundary

The translated x64 startup experiment now executes the original caller's
`PUSH 1 / CALL` fragment and the beginning of the CRT heap initializer. It
reaches the real `HeapCreate` import with the authentic flags, size arguments
and return address. The Windows API remains unresolved at this gate.

The production corpus passed 72 sequences at O0/O2. Root independently compared
48 ordinary sequences against the original captured BEFORE state, including the
complete State, FX, Runtime CPU and all 17 mapped pages. The independent compiled
corpus passed 132 fault and cleanup scenarios. The
[heap initializer review](m4-crt-heap-init-review.md) records the source boundary,
proof receipts and limits.

This advances a startup prerequisite. Selected initializer coverage remains
**27 of 144**; 117 roots remain outside that accepted sequence. M4 is active.
Complete CRT startup, application initialization, a standalone x64 window and
menus remain unfinished.

The next gate is a real `HeapCreate` bridge with an opaque guest handle that owns
the full host handle, validates its lifetime and supports `HeapDestroy` cleanup.
Then the original source can publish the heap handle, select its allocation
mode and reach the allocator prerequisites. Locale completion still needs
allocation, critical-section ownership and source codepage/table updates.
Complete parser sizing, argument outputs and environment ownership follow.

Only isolated x64 research workers ran in this batch. No game run is needed for
this boundary. Earlier accepted milestone reports remain frozen.
