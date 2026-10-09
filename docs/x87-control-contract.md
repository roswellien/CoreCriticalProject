# Authored FNSTCW control-word probe

Established 2026-10-07. This is the first bounded M2 feasibility experiment.
It measures control-word storage and preservation; it does not admit x87
arithmetic, extended intermediates, status, tags, or floating-point registers.
Prior integer G1/G2 evidence remains separate.

## Authored code and architectural oracle

The complete authored x86 fixture is `FNSTCW word ptr [ECX]; RET`, encoded
`D9 39 C3`. FNSTCW stores the control word to a two-byte destination without
modifying the control register. Its x87 C0–C3 condition bits are undefined and are excluded
from this experiment. The reference instruction is FNSTCW, with no inserted
FWAIT. See [Intel SDM Volume 2A, FSTCW/FNSTCW, pages 3-389–3-390](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=491).

The twelve requests use `CW = 0x007F | PCbits | RCbits`. All six exception
masks are set. PC encodings are 0, 2 and 3 for 24-, 53- and 64-bit precision;
the reserved encoding 1 is excluded. RC encodings 0 through 3 denote nearest
even, down, up and toward zero. See [Intel SDM Volume 1, sections 8.1.5.1–8.1.5.3 and Table 8-2](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf#page=199).

| Precision | Nearest even | Down | Up | Toward zero |
| --- | --- | --- | --- | --- |
| 24 bits | 0x007F | 0x047F | 0x087F | 0x0C7F |
| 53 bits | 0x027F | 0x067F | 0x0A7F | 0x0E7F |
| 64 bits | 0x037F | 0x077F | 0x0B7F | 0x0F7F |

## Entry and observations

Each request initializes the original hardware CW and native Remill State CW
to the same requested value. The reference reads back before fixture execution,
records the value, and rejects evidence unless it matches the requested entry
CW. Initialize a clean masked x87 environment; save and restore the reference
worker's host floating-point environment around each case. The native control
probe does not alter the host floating-point environment. These harness
operations occur outside the fixture.

ECX points to a writable two-byte destination within the mapped 4096-byte guest
memory region. The destination cannot overlap the return slot. ESP points to
the mapped four-byte return sentinel `0x10000100`. Record and validate the
entry address, complete input state, initial memory and worker identities.

The architectural expected result is the requested CW encoded little endian
at `[ECX]`, and the same post-execution CW. All remaining memory bytes must
match the initial image. EAX, ECX, EDX, EBX, EBP, ESI and EDI, and the admitted
integer flags remain unchanged. ESP advances by four bytes; EIP reaches the
sentinel. Capture post-execution CW outside guest memory so the guest fixture
still writes only its two-byte target.

The only rounding bridge used here returns the request's admitted RC encoding
0–3. Its scope is this control-word experiment; it makes no claim about host
arithmetic rounding, conversions or exception delivery. No precision repair,
CW masking, expected-result substitution or undefined-value policy may be
inserted into the generated semantics.

## Pinned implementation prediction and reporting

Remill commit `0e324aee8c67a63ec759ef379dcfafa0b3cb1448`,
`lib/Arch/X86/Semantics/X87.cpp`, FNSTCW at lines 1328–1335, explicitly assigns
single precision to State CW, replaces RC through the rounding bridge, and
writes the resulting word. The pinned `x86.bc` SHA-256 is
`138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71`.
The earlier exploratory `reports/x87-feasibility/control-status-guest.ll`
contains the corresponding CW load/store at State offset 2768 and an
`and i16` with -769, clearing bits 8–9. That earlier fixture also included
other instructions; bind the final three-byte fixture's own generated IR and
artifacts in its new report.

The predicted generated result is `requestCW & ~0x0300`, both in the target
word and post State CW. If reproduced, each native optimization level should
match four single-precision requests and disagree on eight double/extended
requests. This prediction is not the architectural oracle. Reports must count
those eight as incompatibilities and preserve both expected and observed
values. Every original execution must satisfy the architectural oracle, and
all non-CW observations must match at O0/O2.

Save source/tool/artifact hashes, request/results and independent verification
under a new ignored report directory. A reproduced precision-clamp limitation
completes this research experiment while leaving M2 compatibility open. Any
unexplained mismatch, failed admission, missing execution, or changed integer
state/memory remains a probe failure. This contract does not support claims
about measured numerical precision, SW/TOP/tags, live ST values, MXCSR,
unmasked traps, or game floating-point behavior.
