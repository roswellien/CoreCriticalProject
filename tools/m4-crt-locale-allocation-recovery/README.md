# Malloc and heap prerequisites

This static recovery reads the exact staged CRT bytes. It executes no provider, game, native component or API. It continues the source `malloc(24)` dependency at `780012B3`, distinguishing the wrapper, size check and real heap-worker prologue.

The next bounded native gate can execute twelve more source instructions and thirteen DWORD accesses, with two actual nested CALLs, then refuse before the first `FS:[0]` read at `780012F2`. This is a provider SEH prerequisite. It establishes no exception registration, allocation return, heap initialization or locale initialization.

The subsequent worker selects a heap path using `78035004`. Both that mode and the heap handle at `78035000` are zero in the source file; those zeros provide identity rather than initialized heap evidence. Modes two and three use distinct small-block allocators and lock nine. Other modes reach `HeapAlloc` with a rounded nonzero request. The authentic preceding attach path calls the heap initializer at `780039BF`, which invokes `HeapCreate`, stores the measured handle, and selects its heap mode. Current default-locale experiments have not run that initialization.

Run `recover.py` with a fresh `recovery-rN` name after the separate whole-provider static inspection used for direct-reference discovery exists. Selected spans are freshly decoded again and checked byte for byte against the original PE. Direct global references are bounded evidence, not an exhaustive alias analysis.
