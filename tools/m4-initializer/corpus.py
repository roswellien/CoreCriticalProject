"""Authored inputs and independent integer oracle for the private MW3 slice.

No original instructions or executable implementation are embedded here.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
import struct

ENTRY, SENTINEL = 0x410910, 0x10000100
STACK, GLOBAL, PAGE = 0x20001000, 0x604000, 4096
IMAGE_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"
CODE_SHA = "f5a91456f4eb0ecab7e5cd689b1d1465dc4e2610bc879397e500b02d00946af7"
U32, ENTRY_FLAGS, EXIT_FLAGS = 0xFFFFFFFF, 0xCD5, 0xCD5
HEADER = struct.Struct("<8s4I")
PREFIX = struct.Struct("<14I")
REQUEST_SIZE, RESULT_SIZE, STATE_SIZE = 568, 27256, 3504
CWS = tuple(0x7F | pc << 8 | rc << 10 for pc in (0, 2, 3) for rc in range(4))
SEED = 0x3400410910
STACK_OFFSETS = (0, 1, 2, 3, 15, 16, 17, 31, 127, 255, 256, 1023,
                 2047, 2048, 4085, 4086, 4087, 4088, 4089, 4090, 4091, 4092)


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


def cases() -> list[Case]:
    rng=random.Random(SEED)
    result=[]
    def add(category, *, cw=0x37f,top=0,ftw=255,sw=0,pattern=0,flags=0x202):
        seed=rng.getrandbits(32)
        regs=[rng.getrandbits(32) for _ in range(8)]
        regs[4]=STACK+STACK_OFFSETS[len(result)%len(STACK_OFFSETS)]
        fx=fx_seed(cw,top,ftw,sw,pattern,seed)
        result.append(Case(tuple(regs+[flags,ENTRY]),0,0,seed,full_tags(fx),fx,category))
    for bits in range(128):
        flags=0x202|sum(((bits>>i)&1)<<j for i,j in enumerate((0,2,4,6,7,11,10)))
        add('all_entry_flags',flags=flags,pattern=bits&1)
    for top in range(8):
        for ftw in range(256):
            for pattern in (0,1):
                add('TOP_FTW_storage',top=top,ftw=ftw,cw=CWS[(top*256+ftw)%12],
                    sw=(0,0x22,0x241,0x457f)[ftw%4],pattern=pattern,flags=0x202|pattern<<10)
    for cw in CWS:
        for df in (0,1):
            for ftw in (0,2,255):
                add('CW_DF_preservation',cw=cw,top=((cw>>10)+df)&7,ftw=ftw,
                    sw=0x457f,pattern=df,flags=0x202|df<<10)
    for _ in range(1024):
        bits=rng.randrange(128)
        flags=0x202|sum(((bits>>i)&1)<<j for i,j in enumerate((0,2,4,6,7,11,10)))
        add('seeded_register_padding',cw=rng.choice(CWS),top=rng.randrange(8),ftw=rng.randrange(256),
            sw=rng.choice((0,0x22,0x241,0x457f)),pattern=rng.randrange(2),flags=flags)
    return result


def initial_memory(q: Case) -> bytes:
    stack=bytearray((i*37+q.seed)&255 for i in range(PAGE))
    struct.pack_into('<I',stack,q.cpu[4]-STACK,SENTINEL)
    data=bytes((i*73+(q.seed>>8)+(i>>8)*19+0x5b)&255 for i in range(PAGE))
    return bytes(stack)+data


def expected(q: Case):
    regs=list(q.cpu[:8]);regs[0]=0x604e3c;regs[1]=0;regs[4]+=4
    cpu=tuple(regs+[0x202|(q.cpu[8]&0x400)|0x44,SENTINEL])
    memory=bytearray(initial_memory(q))
    for i in range(167):memory[PAGE+0x130+i*20]=0
    events=tuple((GLOBAL+0x130+i*20,0,1,1) for i in range(167))+((q.cpu[4],SENTINEL,4,0),)
    return cpu,bytes(memory),events


def request_bytes(rows: list[Case]) -> bytes:
    return HEADER.pack(b'MW34I4RQ',1,len(rows),REQUEST_SIZE,32)+b''.join(q.pack() for q in rows)


