"""Authored inputs and independent integer oracle for the private MW3 slice.

No original instructions or executable implementation are embedded here.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
import struct

ENTRY, SENTINEL = 0x43aec0, 0x10000100
ENTRIES=(0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4b5b20,0x4c7940,0x4cfef0)
STACK, GLOBAL, PAGE = 0x20001000, 0x605000, 4096
IMAGE_SHA = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"
CODE_SHA = "8091fc698f5d5fc75afc1fc3f4926c9f98f2cbce614b5a667889320be799bd31"
U32, ENTRY_FLAGS, EXIT_FLAGS = 0xFFFFFFFF, 0xCD5, 0xCD5
HEADER = struct.Struct("<8s4I")
PREFIX = struct.Struct("<14I")
REQUEST_SIZE, RESULT_SIZE, STATE_SIZE = 568, 32988, 3504
MEMORY_SIZE, MAX_EVENTS = 12288, 8
CWS = tuple(0x7F | pc << 8 | rc << 10 for pc in (0, 2, 3) for rc in range(4))
SEED = 0x3400410910
STACK_OFFSETS = (0, 1, 2, 3, 43, 44, 45, 59, 127, 255, 256, 1023,
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

DESTINATIONS=(0x605928,0x605908,0x605888,0x6058e8,0x605948,0x6058c8,0x6058a8,0x605968)

def cases():
    rng=random.Random(SEED);result=[]
    def make(root,category,cw=0x37f,top=0,ftw=255,pattern=0,flags=0x202,sw=0,persistent=0):
        seed=rng.getrandbits(32);regs=[rng.getrandbits(32) for _ in range(8)];regs[4]=STACK+STACK_OFFSETS[len(result)%len(STACK_OFFSETS)]
        fx=fx_seed(cw,top,ftw,sw,pattern,seed);return Case(tuple(regs+[flags,ENTRIES[root]]),root,persistent,seed,full_tags(fx),fx,category)
    for root in range(14):
        for bits in range(128):
            flags=0x202|sum(((bits>>i)&1)<<j for i,j in enumerate((0,2,4,6,7,11,10)))
            result.append(make(root,'all_entry_flags',flags=flags,pattern=bits&1))
        for cw in CWS:
            for top in range(8):
                for ftw in (0,2,255):result.append(make(root,'CW_TOP_FTW',cw=cw,top=top,ftw=ftw,pattern=top&1,flags=0x202|((top&1)<<10),sw=(0,0x22,0x241,0x457f)[top%4]))
        for i in range(128):result.append(make(root,'seeded_register_padding',cw=CWS[i%12],top=i%8,ftw=i*13&255,pattern=i&1,flags=0x202|((i&1)<<10)))
    for i in range(64):
        base=make(0,'persistent_all_fourteen',cw=CWS[i%12],top=i%8,ftw=i*17&255,pattern=i&1,flags=0x202|((i&1)<<10),persistent=1)
        for root in range(14):result.append(Case((*base.cpu[:9],ENTRIES[root]),root,1,base.seed,base.tags,base.fx,base.category))
    return result

def request_bytes(rows):return HEADER.pack(b'MW34I4RQ',1,len(rows),REQUEST_SIZE,32)+b''.join(q.pack() for q in rows)

def initial_memory(q):
    result=bytearray((i*37+q.seed)&255 for i in range(PAGE))
    for p in (1,2):result.extend((i*73+(q.seed>>8)+(i>>8)*19+0x5b+p*11)&255 for i in range(PAGE))
    struct.pack_into('<I',result,q.cpu[4]-STACK,SENTINEL);return bytes(result)

def expected(q,incoming=None,memory=None):
    before=q.cpu if incoming is None else (*incoming[:4],q.cpu[4],*incoming[5:9],q.cpu[9])
    after=list(before);data=bytearray(initial_memory(q) if memory is None else memory);events=[];idx=q.arg_a
    def write(address,value,width=4):
        off=PAGE+(address-GLOBAL) if address<0x606000 else PAGE*2+(address-0x60b000)
        data[off:off+width]=value.to_bytes(width,'little');events.append((address,value,width,1))
    if idx<8:
        for i in range(7):write(DESTINATIONS[idx]+i*4,0)
        after[0]=DESTINATIONS[idx];after[1]=0;after[8]=0x246|(before[8]&0x400)
    elif idx==11:
        after[0]&=0xffffff00;after[8]=0x246|(before[8]&0x400)
        write(0x60b2b8,0x60b2f4);write(0x60b2bc,0);write(0x60b2c0,0,1);write(0x60b2c1,0,1)
    elif idx==12:write(0x60b44c,0xfffff)
    elif idx==13:
        after[0]=0;after[8]=0x246|(before[8]&0x400);write(0x60b4a8,0);write(0x60b4ac,0)
    events.append((before[4],SENTINEL,4,0));after[4]+=4;after[9]=SENTINEL
    routes=[]
    if idx<8:
        tail=list(before);tail[1]=DESTINATIONS[idx];tail[9]=0x43ae30
        routes=[(tuple(tail),tuple(after),0x43ae30,SENTINEL,0,1)]
    mask=0xcc5 if q.arg_b or idx<8 or idx in (11,13) else 0xcd5
    return {'before':tuple(before),'after':tuple(after),'memory_before':initial_memory(q) if memory is None else memory,'memory_after':bytes(data),'events':tuple(events),'routes':routes,'mask':mask}


