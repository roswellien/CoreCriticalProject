# Exact numeric-max startup prerequisite

This standalone gate executes the recovered game wrapper `4C19F0`, complete body `4C1A00`, and actual two-instruction MSVCP50 provider leaf `780C10F0`. The source name identifies the import; it never supplies a floating-point result. The checked native import route calls the compiled provider translation using the same guest State and memory. The original worker executes the actual isolated bytes without loading or initializing the game or provider DLL.

The admitted provider is `local/mw3-staged/Shared_DLLs/MSVCP50.DLL`, 565760 bytes, SHA256 `91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a`, preferred base `780C0000`. Owning IAT `5BB4FC` resolves to export ordinal1545/RVA10F0; import hint1544 remains distinct. Only that IAT cell is resolved. Provider read-only data `78115004` begins with bytes `ffff7f7f`. Directed cases alter this declared data word before restoring read-only protection.

The live-stack corpus uses contiguous logical depth0/1/7, TOP0/7, 12 masked PC/RC control words, clean/DE/DE+PE incoming status, and two repeats. All eight initial raw80 slots contain explicitly authored canonical finite values, including empty storage. Sixteen binary32 input words include signed zero, subnormal, finite, infinity and quiet/signaling NaN cases. Depth8, unmasked control, gapped tags, wrong entry/frame/import/code/data/segment/owner and altered raw80 inputs fail before guest entry. Native whole State starts from a declared 3504-byte pattern and preserves every byte outside exact observed updates.

Game RX `4C1000`, provider RX `780C1000`, authored broker RX `10000000`, game IAT RO `5BB000`, provider data RO `78115000`, game globals RW `60B000`, and authored A5 stack RW `20001000` are separate mappings. The caller frame is `20001800`, return PC `10000100`, returned ESP `20001804`. Forty-four output bytes begin with authored A5 bytes to verify the store and ten clears. The remaining game page bytes retain their exact admitted image/zero-fill origins.

The original connected checkpoint replaces only byteD9 at `4C1A09` with INT3, after its admission. The isolated parent debugger recognizes the exact child breakpoint/address and owner, captures a literal 716-byte x86 Windows CONTEXT, restores the original D9 byte, and resumes EIP `4C1A09` using `CONTEXT_CONTROL`. The original FSTP then executes at its real PC. Every selected instruction is checked against the exact images after each invocation. This is narrowly scoped instrumentation, with no generic live-game debugging claim.

The debugger's literal CONTEXT reports EIP `4C1A0A` and has measured zero metadata in both FloatSave and ExtendedRegisters. It is retained separately from the direct assembly FXSAVE/FNSTENV snapshots. The observer never restores that zero FP metadata. The native checkpoint's legacy metadata is an explicitly labelled inference from the paired actual provider-leaf FNSTENV plus the recovered integer call/return route, which contains no other FP instruction before the checkpoint. It is not claimed as a direct checkpoint FNSTENV capture.

Three failed in-process observer attempts, their successful first leaf records, the first successful full-context debugger capture, and all strict native baseline failures remain immutable. The measured native defects were the omitted physical occupied-tag push/pop bookkeeping and an unconditional overwrite of incoming DE in the FSTP classification. Repairs add two checked typed tag commits and sticky DE accumulation. Numeric operations, original guest code, and C1 production are unchanged.

The final comparison checks actual CPU/flags, four entire pages, physical/logical tags, raw80 values, distinct hardware FX/legacy metadata, host restoration, exact native 3504-byte State, 22 ordered wrapper memory accesses, actual nested CALL/RET0 frames, and the connected ST0 return. Original opaque State and bus events are unobserved. Finite binary32 loads/stores are exact; finite C1=0 cases receive limited credit. C0/C2/C3, special-value C1 and empty-storage equality remain observations, without broader architectural claims.

Reproduce with entirely new report directories:

```powershell
& 'C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe' -NoProfile -ExecutionPolicy Bypass -File tools/m4-fp-numeric-max/build.ps1 -OutputDirectory reports/m4-fp-numeric-max/fresh-example -Repair
& C:/Python314/python.exe tools/m4-fp-numeric-max/capture.py reports/m4-fp-numeric-max/fresh-example reports/m4-fp-numeric-max/fresh-original-example
& C:/Python314/python.exe tools/m4-fp-numeric-max/verify.py reports/m4-fp-numeric-max/fresh-original-example reports/m4-fp-numeric-max/fresh-example reports/m4-fp-numeric-max/fresh-comparison-example
```

Actual original capture requires the authorized normal Windows execution scope because sandbox CRT reservations can collide with guest addresses. Compiler-time literal source copies, commands, failures, objects, tool identities and additive actual SDK/STL read-dependency copies accompany the private reports. Publishers use exclusive CREATE_NEW staging and no-replace publication in fresh sequential private ordinary directories. Production concurrent/reparse publication is outside this gate.

No frozen shared Runtime source or provider admission has changed. Integration will require a separately reviewed MSVCP50 provider identity/continuation admission and fresh adapters compiled against the accepted shared Runtime; its current provider helper remains MSVCRT-only. Full initializer-table, CRT entry/SEH, MFC application/menu and complete M4 remain open.
