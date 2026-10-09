# CRT math-error registration review

The isolated `__setusermatherr` leaf is accepted on 2026-10-07. Its complete
17-byte provider body reads the cdecl argument, clears one provider global,
stores the callback DWORD in another and returns. The actual game import is
bound by name and exact image identity. Callback addresses remain guest data;
this gate does not invoke them or run the complete game CRT caller.

The independent [original model](../reports/m4-crt-matherr/independent-original-safe-r1/report.json)
checks 1,536 actual original observations. The independent
[native model](../reports/m4-crt-matherr/independent-native-safe-r1/report.json)
checks 3,072 O0/O2 observations, complete 3,504-byte State, three whole pages,
15,360 ordered access events and 3,072 complete named routes. Defined CPU and
memory effects match the four source instructions. Original AND-AF is
undefined; the native IR's AF=0 representative is independently checked.
The raw reviewers reject 144 original and 648 native corruptions, with separate
coherent original undefined-AF positive controls.

The [independent static review](../reports/m4-crt-matherr/independent-static-review-r3/report.json)
checks the complete unchanged guest body, all 34 named ABI layouts and an
explicitly derived typed exception boundary. Independent compiled tests pass
462 assertions across 48 scenarios. Real argument/global/return faults check
partial progress and first diagnostics; entered failures poison retries,
while unentered IAT/return denials can be corrected before execution.

The [final independent closure](../reports/m4-crt-matherr/independent-final-closure-r5/report.json)
checks ten fresh production COFF objects and the actual Context catch handlers
at both optimization levels. It verifies 3,622 compiler-read header and 1,552
source-map associations, preserves prior failed attempts and confirms unchanged
Runtime r9. All 1,437 physical bindings were rehashed before acceptance.
An additive public-source repair replaces embedded original instruction bytes
with private hashes and exact decode/operand checks; the original checker is
preserved privately and excluded from source control. Fresh safe models produce
the same successful review reports.

The bounded fixtures use twelve masked CWs, all eight TOP values, coherent
depths 0/1/7/8, sticky status and eight callback DWORDs. The entire actual
RuntimeFX and software State are checked. Native legacy ENV-after is serialized
from input; its metadata preservation is proven by State, rather than an extra
hardware capture. Host FX/ENV captures establish restoration of architectural
fields; zero-filled reserved FX padding is serialized storage.

Original software State and access events are unobserved. The three provider
pages start from explicit fixtures; their layout does not prove complete
initialized process state. Source/tool/header hashes associate recorded builds
with exact files and do not establish full execution-time dependency provenance.
Full CRT/SEH, callback execution, remaining startup routing and native menus
remain open. This isolated service does not change the 26/118 initializer count.
