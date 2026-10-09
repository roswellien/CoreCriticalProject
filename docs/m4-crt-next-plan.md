# Next CRT startup contracts

The read-only dossier in [recovery-r2](../reports/m4-crt-next/recovery-r2/report.json)
binds the exact staged provider, raw RX source spans, matching LLVM instruction
bytes and a closed direct control-flow graph. `_controlfp` reaches 148
instructions, `_control87` reaches 140, and the CW conversion helpers reach 60
and 55 respectively. Hot/cold tails at `0x7801129B..0x78011318` are included;
the adjacent unrelated allocator and thread routines are excluded. Six
authored graph corruptions reject missing helpers/tails, an instruction-middle
CALL and an unreviewed indirect CALL. This is static preparation, with no
execution or native equivalence credit. The first extraction attempt used a
parser range ending inside an instruction; its source and partial outputs are
preserved in `recovery-r1` and the corrected run uses a fresh directory.

`_controlfp` at `0x780042E1` removes the denormal-mask bit `0x80000` from its mask
argument, then calls `_control87` at `0x780042F7`. `_control87` stores the actual
x87 CW to a two-byte guest stack operand, converts it to CRT control flags,
merges `(old & ~mask) | (new & mask)`, converts that logical result back to a
hardware CW and loads it. Its EAX return is the logical CRT result; it is not
the hardware CW. Guest stack scratch and volatile ECX/EDX are observable.
Unsupported mask bits and the two conversion directions therefore require
source-faithful behavior rather than a host rounding-mode call.

The conversion maps hardware exception masks to CRT bits in a different order:

| Hardware CW mask bit | CRT control bit |
| --- | --- |
| `0x01` invalid | `0x10` |
| `0x04` divide by zero | `0x08` |
| `0x08` overflow | `0x04` |
| `0x10` underflow | `0x02` |
| `0x20` precision | `0x01` |
| `0x02` denormal | `0x80000` |

Rounding bits `0xC00` become CRT `0x300`. Hardware PC `0`, `0x200`, `0x300`
maps to CRT `0x20000`, `0x10000`, `0`; the reserved encodings follow explicit
fallback branches in the recovered helpers. Hardware infinity-control bit
`0x1000` maps to CRT `0x40000`. These are static instruction-derived mappings.
Hardware reserved-bit normalization still requires actual FLDCW/FNSTCW
measurements; no normalized guest-CW implementation is admitted here.

The pinned Remill6 implementation cannot be used unchanged for this gate.
FNSTCW overwrites guest PC with single precision and obtains RC from host
rounding. FLDCW loads the guest word and then forces PC to single precision.
Both defects are bound to the exact semantics source in the dossier. The
proposed normal ABI bridge takes a checked context, persistent State and guest
operand address. FNSTCW writes exactly two bytes from the measured guest CW
without mutating it or consulting host rounding. FLDCW reads exactly two guest
bytes and updates CW using only the independently measured normalization
policy. It preserves legacy FOP/FIP/FDP/selectors, status, physical tags/raw
80-bit storage, XMM and MXCSR. Full host FP capture/restoration surrounds any
host operation; host state never supplies guest CW authority.

The next directed gate should measure all 65,536 FLDCW input words twice in an
empty, zero-exception x87 environment, then test the exact provider CFG with the
twelve masked CW states, all TOPs and concrete masked PC/RC request pairs. It
must capture actual two-byte scratch writes, surrounding untouched bytes,
final defined flags, volatile results, physical/legacy FP state and host
restoration. Unmasked pending exception behavior remains a required separate
contract. No Windows `long double` numerical ABI is involved.

`__setusermatherr` is a complete 17-byte leaf at `0x7800B38F`. It loads its
argument into EAX, ANDs DWORD `0x780392B8` with zero, stores the callback guest
pointer to `0x7803B0C4` and returns. It invokes no callback. AND defines
CF/PF/ZF/SF/OF with result `0x44`; AF is undefined. A future differential gate
must retain that distinction.

The actual CRT entry dereferences data imports `_adjust_fdiv` and `_acmdln`.
Their staged file-backed RW DWORDs at `0x78037C2C` and `0x78037174` are both
zero, which does not prove their initialized host-provider values. Runtime r9
has typed function imports and preserves original raw IAT bytes; it has no
admitted data-import route. A new preserved runtime extension must explicitly
bind named IAT ownership, provider global address/span/source identity and
lifetime, and route translated data accesses without rewriting the original
IAT. Command-line/argv/environment buffers require owned guest addresses and
measured initialization contracts before their dereferences can succeed.

`__getmainargs` at `0x7800BA5E` has separate wildcard and ordinary parser paths.
The ordinary path reaches `GetModuleFileNameA`, a two-pass parser, `malloc`,
allocation-failure `_amsg_exit` and a multibyte classification table. Its outer
body and ordinary parser spans are recorded, but their complete dependency
closure is absent. Constant argc/argv/environment results would hide required
work and are not implemented.

The real helper `0x5AC5C0` is a one-byte RET. It is separate from the
`_controlfp` thunk at `0x5AC5D6`. Full CRT initialization, data imports, SEH,
connected initializer ordering, MFC/frontend and native menus remain open.
