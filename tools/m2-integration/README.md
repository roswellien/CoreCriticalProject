# M2 call integration probe

This isolated authored experiment adds native call routing, guest globals, a
deterministic zero-argument WINMM `timeGetTime` boundary, and two admitted indirect
destinations. Original x86 instructions execute in a separate Win32 worker.
Remill-generated blocks execute as compiled Windows x64 code at O0 and O2.
The ordinary game and earlier experiment gates remain independent.

`build.py` creates all local artifacts under ignored `reports/m2-integration/`.
`compare.py` saves full stack/global memory, register/defined-flag and call-frame
observations. Unknown code targets and malformed frames are rejected. No runtime
instruction interpreter or integer-to-host-function-pointer cast is used.
