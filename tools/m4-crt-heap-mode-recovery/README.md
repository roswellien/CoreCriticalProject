# Heap mode selector: first OS-query boundary

This static recovery freshly decodes the staged, pinned x86 MSVCRT provider. It does not execute the original provider, the game, translated native functions, or any Windows API.

Run `C:/Python314/python.exe tools/m4-crt-heap-mode-recovery/recover.py recovery-r1` once into a fresh report directory. Every selected instruction is checked against the exact original PE bytes; the receipt pins its tooling, original bytes, decode outputs, import metadata, baseline acceptance, and prior static contract. Existing receipts are never overwritten.

The proposed next executable cut is `selector-prefix.bin` (37 bytes, `78003A0C..78003A31`) and the complete `stack-probe.bin` helper (49 bytes, `780058B5..780058E6`). The selector performs its actual helper CALL, the helper's real relocated RET, and the genuine GetVersionExA indirect CALL. Stop at the unresolved raw import target `00034600`, before an API invocation or return. The full selector's hot and cold CFG and module fallback are separate, unexecuted static evidence.

Starting from the previously accepted selector entry at ESP `20001854`, the new source performs 26 instructions and 14 memory accesses. With the carried HeapCreate chain this is 39 instructions, 24 source accesses, five source CALLs, and one separate earlier API-return read. The query frame is `20000618`, its source return is `78003A31`, and its pointer argument is `200017B8`. Only the first DWORD of the 148-byte OSVERSIONINFOA is initialized by this prefix.

Two new maps are required: exact original RX page `78005000`, and owned research RW page `20000000`. The new lower stack page is declared input, initially zero for admission, rather than an original capture. Directed nonzero inputs must determine terminal TEST flags. All prior 18 mappings, TIB/StackLimit metadata, and generic RuntimeCPU/call records remain carried. This does not establish original Windows guard-stack growth. No host source-store shortcut, OS-version output, heap mode, selector return, initialized allocator, original attach, or full causal replay is claimed.

API references are Microsoft [GetVersionExA](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getversionexa), [OSVERSIONINFOA](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-osversioninfoa), and [x86 stdcall](https://learn.microsoft.com/en-us/cpp/cpp/stdcall?view=msvc-170). They describe future API admission; no API is run by this tool.
