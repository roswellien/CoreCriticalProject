# Native CRT filename service

This additive isolated worker resumes the actual compiled ordinary MSVCRT argument builder through its first Windows filename dependency. It borrows the accepted mainargs Context, runtime, 3504-byte State, distinct 512-byte FX image and sixteen existing guest pages. It reuses every prior translated object unchanged. It launches no ordinary game and executes no complete original CRT.

The actual source route is game CALL `5AC468` → `MSVCRT!__getmainargs` `7800BA5E` → ordinary builder `7800BBBC` → CALL `7800BBD0`, IAT `7802E018`, raw `343B0`. The checked source frame contains return `7800BBD6`, NULL module, guest buffer `7803B3F0` and capacity 260. The bridge records the actual native `GetModuleFileNameA(NULL,...)` result for the research worker executable, its immediate LastError, and physical worker/API owner identities. The admitted guest game identity remains separately recorded.

The entire 260-byte native scratch buffer starts with the actual guest buffer. The witness retains both complete arrays. One checked whole-buffer guest write precedes publication of the API's DWORD EAX result, real stdcall ESP advancement by 16 and source return PC. Immutable witness checks surround observer hooks. All other carried State/FX storage remains unchanged under this declared service contract. Native x64 API execution does not establish original x86 callee volatile ECX/EDX/EFLAGS behavior.

Actual compiled source resumes at `7800BBD6`. Its next `MOV EAX,[78037174]` is refused before the source load: the initialized command-line producer remains unresolved. There is no unsafe zero-pointer dereference, parser execution, argc/argv/environment output, provider RET, main initializer or menu credit. The main initializer count remains 27 of 144; M4 remains active.

The [official Microsoft contract](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulefilenamea) defines NULL as the current process executable, successful return length excluding the NUL, and modern Windows truncation return equal to capacity with `ERROR_INSUFFICIENT_BUFFER`. The separately labelled unit witnesses call the actual API at capacities 0, 1, 8 and 260. They check NUL placement, truncation status and every untouched tail byte. Incoming and resulting LastError are typed service metadata and OS witnesses; this gate writes no guest TEB LastError field. Inner and enclosing host LastError guards restore the caller on success and exceptions.

Current candidate: [preparation-r8](../../reports/m4-crt-filename/preparation-r8/report.json), [build-r7](../../reports/m4-crt-filename/build-r7/build.json), [execution-r4](../../reports/m4-crt-filename/execution-r4/report.json), [author observer-r6](../../reports/m4-crt-filename/author-observer-r6/report.json). Root acceptance and independent filename reviews remain separate. Superseded preparations/builds and the failed observer corruption trial remain preserved.

The batch contains 48 positive sequences, 24 meaningful new causal sequences, eight actual API capacity cases, complete State/FX/page/source snapshots and terminal retry evidence. Twelve author controls cover return/IAT/source corruption, invalid NULL-only or capacity domains, denied guest buffer writes, observer exceptions before API/after API/after store/after RET, and late State corruption. Independent fixtures additionally review stale side bindings, opaque tokens and immutable API outcome corruption. Published and admitted side bindings must agree with the exact current mainargs owner before any stale binding field is inspected.

Run from the project root with fresh output directories:

```powershell
& 'C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe' -NoProfile -ExecutionPolicy Bypass -File tools/m4-crt-filename/build.ps1 -OutputDirectory reports/m4-crt-filename/build-fresh
C:/Python314/python.exe tools/m4-crt-filename/run.py build-fresh execution-fresh
C:/Python314/python.exe tools/m4-crt-filename/observe.py build-fresh execution-fresh author-observer-fresh
C:/Python314/python.exe tools/m4-crt-filename/seal.py build-fresh execution-fresh author-observer-fresh author-submission-fresh
```

The preparation script creates fresh derivatives of the frozen predecessor. The build recipe currently selects preparation-r8. It retains `/EHs`, the accepted enclosing final catch/host FP restoration, compiler-read headers, exact COFF/native object hashes, SDK search environment and source/build association. It does not claim exact linker SDK file-open attestation. FP verification measures ENV28, CW/SW/FTW/MXCSR, physical raw80 values and ABI XMM6–15; volatile XMM0–5 equality is outside the claim.

The next coherent dependency is the reviewed initialized command-line producer, carried into this same State/page ownership without duplicate mapping or reseeding. Parser/locale/allocation/environment contracts must precede successful argument output and the main initializer table.
