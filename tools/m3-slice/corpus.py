"""Authored inputs and independent integer oracle for the private MW3 slice.

No original instructions or executable implementation are embedded here.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
import struct

ENTRY, SENTINEL = 0x558290, 0x10000100
STACK, GLOBAL, PAGE = 0x20001000, 0x72C000, 4096
IMAGE_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"
CODE_SHA = "fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa"
U32, ENTRY_FLAGS, EXIT_FLAGS = 0xFFFFFFFF, 0xCD5, 0xCC5
HEADER = struct.Struct("<8s4I")
PREFIX = struct.Struct("<14I")
REQUEST_SIZE, RESULT_SIZE, STATE_SIZE = 568, 24564, 3504
CWS = tuple(0x7F | pc << 8 | rc << 10 for pc in (0, 2, 3) for rc in range(4))
SEED = 0x3400558290
STACK_OFFSETS = (0, 1, 2, 3, 15, 16, 17, 31, 127, 255, 256, 1023,
                 2047, 2048, 4077, 4078, 4079, 4080, 4081, 4082, 4083, 4084)


def raw80(sig: int, exponent: int) -> bytes:
    return struct.pack("<QH", sig, exponent)


PATTERNS = (
    tuple(raw80(0x8000000000000001 + i * 0x1000000000000002,
                (0xBFFF if i & 1 else 0x3FFF) + (i // 2)) for i in range(8)),
    (raw80(0, 0), raw80(0, 0x8000), raw80(1 << 63, 0x7FFF), raw80(1 << 63, 0xFFFF),
     raw80(0xC000000000001234, 0x7FFF), raw80(0xC000000000004321, 0xFFFF),
     raw80(0xD000000000005678, 0x7FFF), raw80(0xE00000000000ABCD, 0xFFFF)),
)


def full_tags(fx: bytes) -> int:
    if len(fx) != 512:
        raise ValueError("FX seed length")
    top, ftw = (struct.unpack_from("<H", fx, 2)[0] >> 11) & 7, fx[4]
    tags = 0
    for logical in range(8):
        physical = (top + logical) & 7
        sig, exp = struct.unpack_from("<QH", fx, 32 + logical * 16)
        exp &= 0x7FFF
        tag = 3 if not ftw & (1 << physical) else 1 if not sig and not exp else 2 if exp == 0x7FFF else 0
        tags |= tag << (physical * 2)
    return tags


def fx_seed(cw: int, top: int, ftw: int, sw: int, pattern: int, seed: int) -> bytes:
    if cw not in CWS or not 0 <= top < 8 or not 0 <= ftw < 256 or sw & ~0x477F:
        raise ValueError("Invalid authored FP seed")
    fx = bytearray(512)
    struct.pack_into("<HH", fx, 0, cw, sw | top << 11)
    fx[4] = ftw
    # This host loses seeded nonzero pointer/opcode metadata across scheduling.
    # Admit zero metadata explicitly; its actual before/after bytes still match.
    struct.pack_into("<I", fx, 24, 0x1F80)
    for i, value in enumerate(PATTERNS[pattern]):
        fx[32 + i * 16:42 + i * 16] = value
    fx[160:288] = bytes((seed + i * 73 + 0x5B) & 255 for i in range(128))
    return bytes(fx)


@dataclass(frozen=True)
class Case:
    cpu: tuple[int, ...]
    arg_a: int
    arg_b: int
    seed: int
    tags: int
    fx: bytes
    category: str

    def pack(self) -> bytes:
        return PREFIX.pack(*self.cpu, self.arg_a, self.arg_b, self.seed, self.tags) + self.fx


def directed_values() -> tuple[int, ...]:
    values = set(range(256)) | set(range(0xFFFFFF00, 0x100000000))
    for bit in range(32):
        for delta in (-2, -1, 0, 1, 2):
            values.add(((1 << bit) + delta) & U32)
            values.add((-(1 << bit) + delta) & U32)
    return tuple(sorted(values))


def cases() -> list[Case]:
    rng = random.Random(SEED)
    output: list[Case] = []

    def add(a, b, df, category, *, top=0, ftw=255, cw=0x37F, sw=0, pattern=0, flags=None):
        i = len(output)
        seed = rng.getrandbits(32)
        regs = [rng.getrandbits(32) for _ in range(8)]
        regs[0] = 0xA5A5F00D if i % 3 == 0 else regs[0]
        regs[4] = STACK + STACK_OFFSETS[i % len(STACK_OFFSETS)]
        arithmetic = ((i & 1) | ((i >> 1 & 1) << 2) | ((i >> 2 & 1) << 4) |
                      ((i >> 3 & 1) << 6) | ((i >> 4 & 1) << 7) | ((i >> 5 & 1) << 11))
        flags = 0x202 | df << 10 | arithmetic if flags is None else flags
        fx = fx_seed(cw, top, ftw, sw, pattern, seed)
        output.append(Case(tuple(regs + [flags, ENTRY]), a & U32, b & U32,
                           seed, full_tags(fx), fx, category))

    for b in directed_values():
        for df in (0, 1):
            add(rng.getrandbits(32), b, df, "directed_integer", pattern=df)
    for bits in range(128):
        flags = (0x202 | (bits & 1) | ((bits >> 1 & 1) << 2) | ((bits >> 2 & 1) << 4) |
                 ((bits >> 3 & 1) << 6) | ((bits >> 4 & 1) << 7) | ((bits >> 5 & 1) << 11) |
                 ((bits >> 6 & 1) << 10))
        add(0x12345678, (0xFFFFFFFD, 0x80000000, 0, 3)[bits % 4], bits >> 6,
            "entry_flag_matrix", flags=flags)
    for top in range(8):
        for ftw in range(256):
            for pattern in (0, 1):
                add(rng.getrandbits(32), rng.getrandbits(32), pattern, "TOP_FTW_storage",
                    top=top, ftw=ftw, cw=CWS[(top * 256 + ftw) % 12],
                    sw=(0, 0x22, 0x241, 0x457F)[ftw % 4], pattern=pattern)
    for cw in CWS:
        for df in (0, 1):
            for ftw in (0, 2, 255):
                add(0x89ABCDEF, 0x80000001, df, "control_DF_preservation", cw=cw,
                    top=(cw >> 10) + df, ftw=ftw, sw=0x457F, pattern=df)
    for _ in range(10000):
        add(rng.getrandbits(32), rng.getrandbits(32), rng.randrange(2), "seeded_integer",
            top=rng.randrange(8), ftw=rng.randrange(256), cw=rng.choice(CWS),
            sw=rng.choice((0, 0x22, 0x241, 0x457F)), pattern=rng.randrange(2))
    return output


def initial_memory(case: Case) -> bytes:
    stack = bytearray((i * 37 + case.seed) & 255 for i in range(PAGE))
    struct.pack_into("<3I", stack, case.cpu[4] - STACK, SENTINEL, case.arg_a, case.arg_b)
    return bytes(stack) + bytes(PAGE)


def expected(case: Case) -> tuple[tuple[int, ...], bytes]:
    """An exact arithmetic specification, used only to measure both real workers."""
    signed = case.arg_b if case.arg_b < 0x80000000 else case.arg_b - (1 << 32)
    quotient = signed // 2 if signed >= 0 else -((-signed) // 2)
    sign = U32 if signed < 0 else 0
    adjusted = (case.arg_b - sign) & U32
    result = quotient & U32
    # CF observes the actual value shifted by the final SAR, after SUB.
    flags = ((adjusted & 1) | (int((result & 255).bit_count() % 2 == 0) << 2) |
             (int(result == 0) << 6) | ((result >> 31) << 7) | (case.cpu[8] & 0x400))
    regs = list(case.cpu[:8])
    regs[0], regs[2], regs[4] = result, sign, regs[4] + 12
    memory = bytearray(initial_memory(case))
    struct.pack_into("<5I", memory, PAGE + 0x1E4,
                     case.cpu[1], case.cpu[2], case.arg_a, case.arg_b, result)
    return tuple(regs + [flags, SENTINEL]), bytes(memory)
