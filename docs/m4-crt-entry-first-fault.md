# Native CRT entry: first required service

The complete translated CRT entry now links to a private x64 research worker
and runs at O0/O2. Sixteen original instruction PCs install the guest exception
frame and reach `0x5AC3CF`, the call through `0x5BB5A4` to
`MSVCRT.dll!__set_app_type`. This worker deliberately leaves the service
unregistered. It records an explicit unresolved-import failure and refuses
reuse of the poisoned context without changing State or source events.

The bounded native result passes the root's separately authored input/source
observer: complete 3,504-byte guest State, the distinct dispatcher CPU, two
4,096-byte stack/IAT pages, all three implemented NT_TIB regions, and all fifteen
source memory events match at both optimization levels. Thirty-six observer
corruptions reject. The code's installation of one FS exception frame is
observed; exception dispatch and unwinding through that guest frame remain
unimplemented.

The [private observation](../reports/m4-crt-entry/first-fault-observation-r2/report.json)
has SHA-256 `880f25fffaea5f527d8935aa6f420f5d7f914e1084f5d163eac6b0fd987acba5`;
its [bindings](../reports/m4-crt-entry/first-fault-observation-r2/pins.json)
have SHA-256 `09bd235d445aa61568cae03ba578037e6d174f7a96ea73cde59e183494f56c8e`.
The full 148-instruction object preparation retains its separate static scope;
the unexecuted instruction paths do not receive runtime coverage.

These inputs are an authored startup policy, not observations of the original
process. No original game or provider instructions execute in this worker.
Guest floating-point storage remains opaque to the reached integer operations;
this probe makes no numerical coherence or actual caller floating-point
preservation claim. Independent compiled/ABI review and an original startup
comparison remain open. Full CRT startup, service returns, termination and
menus remain open, and the connected initializer gate stays at 26 roots.

Three failed build/run attempts remain preserved with literal sources and logs:
an omitted admission header, implicit nonthrowing C-linkage declarations, and
a pre-run snapshot that exceeded the implemented NT_TIB mappings. The final
derivative declares throwing bridge boundaries explicitly and captures only
the actual mapped thread regions. Required unimplemented bridge operations
still reject.

To reproduce the build and bounded research probe in a fresh directory:

```powershell
& 'C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe' -NoProfile -ExecutionPolicy Bypass -File tools/m4-crt-entry/build-first-fault.ps1 -OutputDirectory reports/m4-crt-entry/fresh-first-fault-build
& 'C:/Python314/python.exe' tools/m4-crt-entry/observe_first_fault.py reports/m4-crt-entry/fresh-first-fault-build reports/m4-crt-entry/fresh-first-fault-observation
```

The next integration is to connect the reviewed CRT services at their actual
entry call sites, then provide the initialized FDIV data import and continue
the measured startup sequence. The [entry preparation](m4-crt-entry-preparation.md)
lists the remaining CRT and application dependencies.
