#!/usr/bin/env python3
"""Compare live raw80 stack transitions with an independent integer-byte oracle."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import re
import struct
import subprocess
import sys
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[2]
HEADER = struct.Struct('<8s4I')
PREFIX = struct.Struct('<16I')
CPU = struct.Struct('<11I')
META = struct.Struct('<8I')
REQUEST_SIZE, RESULT_SIZE, COUNT = 156, 5416, 3456
ENTRY, SENTINEL, PAGE, PAGE_SIZE = 0x10000000, 0x10000100, 0x20001000, 4096
FLAGS, SEED = 0xCD5, 0x3434
FIXTURES = {'push': bytes.fromhex('db29c3'), 'pop': bytes.fromhex('db3ac3'),
            'exchange': bytes.fromhex('d9c9c3'), 'free': bytes.fromhex('ddc1c3')}
CWS = tuple(0x7F | p << 8 | r << 10 for p in (0, 2, 3) for r in range(4))
SEEDS = tuple(((1 << depth) - 1, 0) for depth in range(9)) + ((2, 0), (2, 0x22), (2, 0x241)) + tuple(
    (mask, sw) for mask in (0, 1, 255) for sw in (0x22, 0x241))


def raw80(significand: int, exponent: int) -> bytes:
    return struct.pack('<QH', significand, exponent)


PATTERNS = (
    tuple(raw80(sig, exp) for sig, exp in zip(
        (0x8000000000000001, 0x9000000000000003, 0xA000000000000005, 0xB000000000000007,
         0xC000000000000009, 0xD00000000000000B, 0xE00000000000000D, 0xF00000000000000F),
        (0x3FFF, 0xBFFF, 0x4000, 0xC000, 0x4001, 0xC001, 0x3FFE, 0xBFFE), strict=True)),
    (raw80(0, 0), raw80(0, 0x8000), raw80(0x8000000000000000, 0x7FFF),
     raw80(0x8000000000000000, 0xFFFF), raw80(0xC000000000001234, 0x7FFF),
     raw80(0xC000000000004321, 0xFFFF), raw80(0xD000000000005678, 0x7FFF),
     raw80(0xE00000000000ABCD, 0xFFFF)))
INPUTS = (raw80(0x8000000000000055, 0x4002), raw80(0xC00000000000BEEF, 0x7FFF))
INDEFINITE = raw80(0xC000000000000000, 0xFFFF)
GUEST_HASHES = {'push': '56b12be96118153238b85193b7719b6c1f4df5131234b4fe99a0749b7bbd640a',
    'pop': 'c7684b10c5f7bf067bc71a0b968fe99d763c24073d4a651b5de1ad624fe886cf',
    'exchange': '1b033d0b32f687ca42f0f874685711173c8215b90e3270652f5428d060927336',
    'free': 'cd81f402016bda27609a9bd7a9d64d76d47a0299297b6c58bded71499f976095'}
RANGE_COMPARATOR_HASH = 'b0c1b74f9baec045b7f69e2caf8ceaab52cf723dd7e040a57be1135335023989'
RANGE_FINAL_PINS_HASH = '11c50568126933468e32ef061c0adf450aa0d61e1e0d01861d6f2d77fe5306d2'
STATE_BASELINE_HASH = '7b0c935743991ecef15174d7c3d343852a772d63e0fc6d52a2cecf3198c88f11'
STATE_BASELINE_MANIFEST_HASH = '21d69c5a0539ba6166a8e49e3101b906dc9b66d5776371437a5b54073991c048'
STATE_INITIAL_PINS_HASH = '91d2208824bd41377a4930ddac0f6dece23860e3f48e7796b0a001dfe195757a'
HELPER_DESIGN_HASH = '77fbd3b2f13fa25f0401c48c39551a776f771670666b8a43964bb4868b71804e'
HELPER_BODY_HASHES = {
    'mw34_x87_fault_flags':'0ddfc0dbfa5880352a073c85c32f68c5601cefa8355fa96561a2a1e49258f064',
    'mw34_x87_push_prepare':'9216c33f1974f7e271de9f4eb9f1d43dad4550c6d177e63f5f24d1cf092b8b88',
    'mw34_x87_pop_prepare':'936f2f58917e0d0a7d8e1c0eaa9be4cfe34703b685a71a5432e62f7577e920c8',
    'mw34_x87_exchange_prepare':'2d00078a051fd5507aaae83325b67f2d6c50420313bf4140ba96249b582a86f5',
    'mw34_x87_free_prepare':'61fb2db9b4096a7a578cef143b2bcbe49bd214180d2ca1d93947b10b339adcd2'}
HELPER_SITES = {'push':('before_loaded_raw80_unpack','  %20 = load i64, ptr %1, align 8\n'),
    'pop':('before_actual_ST0_load','  %19 = load x86_fp80, ptr %ST0, align 1\n'),
    'exchange':('before_actual_exchange_moves','  call void @llvm.lifetime.start.p0(i64 10, ptr nonnull %1)\n'),
    'free':('after_opcode_pointer_before_return','  store ptr %5, ptr %MEMORY, align 4\n')}
REMILL_COMMIT = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
LLVM_HASH = '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'


class Case(NamedTuple):
    cpu: tuple[int, ...]
    cw: int
    seed: int
    top: int
    ftw: int
    sw: int
    pattern: int
    slots: tuple[bytes, ...]
    source: bytes


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def status_mask(kind: str) -> int:
    return 0x38FF if kind == 'free' else 0x3AFF


def phase_mask(kind: str, side: int) -> int:
    return 0x3AFF if side == 0 else status_mask(kind)


def physical(mask: int, top: int) -> int:
    return sum((1 << ((top + i) & 7)) for i in range(8) if mask & (1 << i))


def logical(ftw: int, top: int) -> int:
    return sum((1 << i) for i in range(8) if ftw & (1 << ((top + i) & 7)))


def canonical(value: bytes) -> bool:
    sig, se = struct.unpack('<QH', value)
    exp = se & 0x7FFF
    return sig == 0 if exp == 0 else bool(sig >> 63) and (
        exp != 0x7FFF or sig == 0x8000000000000000 or bool(sig & (1 << 62)))


def full_tags(slots: tuple[bytes, ...], top: int, ftw: int) -> int:
    tags = 0
    for i, value in enumerate(slots):
        p = (top + i) & 7
        if not ftw & (1 << p):
            tag = 3
        else:
            sig, se = struct.unpack('<QH', value)
            exp = se & 0x7FFF
            tag = 1 if sig == 0 and exp == 0 else 2 if exp in (0, 0x7FFF) or not sig >> 63 else 0
        tags |= tag << (2 * p)
    return tags


def overlaps(a: int, n: int, b: int, m: int) -> bool:
    return a < b + m and b < a + n


def validate_case(case: Case) -> None:
    cpu = case.cpu
    require(len(cpu) == 10 and cpu[9] == ENTRY and PAGE + 16 <= cpu[4] <= PAGE + PAGE_SIZE - 16 and
            cpu[8] & 0x202 == 0x202 and cpu[8] & ~(0x202 | FLAGS) == 0,
            'Invalid x87 state entry/register flags')
    spans = ((cpu[1], 10), (cpu[2], 10), (cpu[4], 12))
    require(all(PAGE <= a and a + n <= PAGE + PAGE_SIZE for a, n in spans) and
            all(not overlaps(a, n, b, m) for i, (a, n) in enumerate(spans) for b, m in spans[i+1:]),
            'Invalid raw80 input/output span or overlap')
    require(case.cw in CWS, 'Unmasked or unsupported x87 control word')
    require(0 <= case.top <= 7 and 0 <= case.ftw <= 255 and 0 <= case.pattern <= 1 and
            (logical(case.ftw, case.top), case.sw) in SEEDS, 'Unadmitted TOP/physical occupancy/sticky seed')
    require(len(case.slots) == 8 and all(len(v) == 10 and canonical(v) for v in case.slots) and
            len(case.source) == 10 and canonical(case.source), 'Unadmitted raw80 encoding')
    require(case.slots == PATTERNS[case.pattern] and case.source == INPUTS[case.pattern],
            'Raw80 values differ from authored admitted patterns')


def corpus() -> list[Case]:
    rng, cases = random.Random(SEED), []
    input_offsets = (0, 1, 3, 127, 1023, 2049, 4086)
    output_offsets = (32, 65, 100, 1537, 3001, 4076)
    stack_offsets = (160, 512, 1024, 2307, 3061, 4064)
    for cw in CWS:
        for top in range(8):
            for occupancy, sw in SEEDS:
                for pattern in range(2):
                    index = len(cases)
                    inp = input_offsets[index % len(input_offsets)]
                    out = output_offsets[(index // len(input_offsets)) % len(output_offsets)]
                    stack = next(s for s in stack_offsets[index % len(stack_offsets):] + stack_offsets[:index % len(stack_offsets)]
                                 if not overlaps(s, 12, inp, 10) and not overlaps(s, 12, out, 10))
                    require(not overlaps(inp, 10, out, 10), 'Authored corpus spans overlap')
                    regs = [rng.getrandbits(32) for _ in range(8)]
                    regs[1], regs[2], regs[4] = PAGE + inp, PAGE + out, PAGE + stack
                    case = Case((*regs, 0x202 | (index * 37 & FLAGS), ENTRY), cw, rng.getrandbits(32),
                                top, physical(occupancy, top), sw, pattern, PATTERNS[pattern], INPUTS[pattern])
                    validate_case(case)
                    cases.append(case)
    require(len(cases) == COUNT, 'Authored state count differs')
    return cases


def encode_case(case: Case) -> bytes:
    return PREFIX.pack(*case.cpu, case.cw, case.seed, case.top, case.ftw, case.sw, case.pattern) + b''.join(
        case.slots) + case.source + b'\0\0'


def encode_corpus(cases: list[Case]) -> bytes:
    return HEADER.pack(b'MW34REQ1', 1, COUNT, REQUEST_SIZE, 32) + b''.join(map(encode_case, cases))


def parse_corpus(data: bytes) -> list[Case]:
    require(len(data) >= HEADER.size, 'Truncated x87 state request')
    require(HEADER.unpack_from(data) == (b'MW34REQ1', 1, COUNT, REQUEST_SIZE, 32),
            'State probe requires3456 admitted v1 x86 requests')
    require(len(data) >= HEADER.size + COUNT * REQUEST_SIZE, 'Truncated x87 state request')
    require(len(data) == HEADER.size + COUNT * REQUEST_SIZE, 'Trailing x87 state request bytes')
    cases, seen = [], set()
    for i in range(COUNT):
        row = data[24+i*REQUEST_SIZE:24+(i+1)*REQUEST_SIZE]
        q = PREFIX.unpack_from(row)
        require(row[154:] == b'\0\0', 'Unadmitted TOP/physical occupancy/sticky seed')
        case = Case(tuple(q[:10]), *q[10:], tuple(row[64+j*10:74+j*10] for j in range(8)), row[144:154])
        validate_case(case)
        key = (case.cw, case.top, case.ftw, case.sw, case.pattern)
        require(key not in seen, 'Duplicate x87 state semantic request')
        seen.add(key)
        cases.append(case)
    require(seen == {(cw, top, physical(mask, top), sw, pattern) for cw in CWS for top in range(8)
                     for mask, sw in SEEDS for pattern in range(2)}, 'Incomplete authored state Cartesian matrix')
    return cases


def initial_memory(case: Case) -> bytes:
    page = bytearray((37*i + case.seed) & 255 for i in range(PAGE_SIZE))
    struct.pack_into('<3I', page, case.cpu[4]-PAGE, SENTINEL, case.cw, case.seed)
    page[case.cpu[1]-PAGE:case.cpu[1]-PAGE+10] = case.source
    return bytes(page)


def transition(case: Case, kind: str) -> dict:
    top, ftw, sw = case.top, case.ftw, case.sw
    values = [b'' for _ in range(8)]
    for i, value in enumerate(case.slots):
        values[(top+i) & 7] = value
    output, fault = None, False
    if kind == 'push':
        top = (top-1) & 7
        fault = bool(ftw & (1 << top))
        values[top] = INDEFINITE if fault else case.source
        ftw |= 1 << top
        sw = (sw & ~0x200) | (0x241 if fault else 0)
    elif kind == 'pop':
        fault = not bool(ftw & (1 << top))
        output = INDEFINITE if fault else values[top]
        ftw &= ~(1 << top)
        top = (top+1) & 7
        sw = (sw & ~0x200) | (0x41 if fault else 0)
    elif kind == 'exchange':
        p0, p1 = top, (top+1) & 7
        fault = not (ftw & (1 << p0) and ftw & (1 << p1))
        if not ftw & (1 << p0):
            values[p0] = INDEFINITE
        if not ftw & (1 << p1):
            values[p1] = INDEFINITE
        values[p0], values[p1] = values[p1], values[p0]
        ftw |= (1 << p0) | (1 << p1)
        sw = (sw & ~0x200) | (0x41 if fault else 0)
    elif kind == 'free':
        ftw &= ~(1 << ((top+1) & 7))
    else:
        raise ValueError('Unadmitted state profile')
    slots = tuple(values[(top+i) & 7] for i in range(8))
    memory = bytearray(initial_memory(case))
    if output is not None:
        memory[case.cpu[2]-PAGE:case.cpu[2]-PAGE+10] = output
    return {'top': top, 'ftw': ftw, 'sw': sw | top << 11, 'slots': slots,
            'full_tags': full_tags(slots, top, ftw), 'memory': bytes(memory), 'stack_fault': fault}


def parse_results(data: bytes, bits: int) -> list[bytes]:
    require(len(data) >= HEADER.size and HEADER.unpack_from(data) == (b'MW34RES1', 1, COUNT, RESULT_SIZE, bits),
            'Wrong state result header/count/width/extent')
    require(len(data) == HEADER.size + COUNT * RESULT_SIZE, 'Wrong complete state result byte extent')
    return [data[24+i*RESULT_SIZE:24+(i+1)*RESULT_SIZE] for i in range(COUNT)]


def observation(raw: bytes, kind: str) -> tuple:
    meta = META.unpack_from(raw, 4140)
    views = []
    for side in range(2):
        top = meta[2+side] >> 11 & 7
        ftw = meta[4+side]
        views.append(tuple(raw[4172+80*side+10*i:4182+80*side+10*i] if ftw & (1 << ((top+i) & 7))
                           else None for i in range(8)))
    return (raw[:4140], meta[:2], tuple(x & phase_mask(kind, i) for i, x in enumerate(meta[2:4])),
            meta[4:], tuple(views), raw[5412:5416])


def assess(raw: bytes, case: Case, kind: str) -> dict:
    require(len(raw) == RESULT_SIZE, 'State record extent differs')
    goal = transition(case, kind)
    cpu = list(case.cpu[:8]); cpu[4] += 4
    require(raw[:44] == CPU.pack(*cpu, case.cpu[8] & FLAGS, SENTINEL, 0), 'Complete CPU/worker status differs')
    require(raw[44:4140] == goal['memory'], 'Full guest page differs')
    meta = META.unpack_from(raw, 4140)
    wanted = (case.cw, case.cw, case.sw | case.top << 11, goal['sw'], case.ftw, goal['ftw'],
              full_tags(case.slots, case.top, case.ftw), goal['full_tags'])
    require(meta[:2] == wanted[:2] and meta[4:] == wanted[4:] and
            all(v <= 0xFFFF for v in meta[:4]) and
            tuple(v & phase_mask(kind, i) for i, v in enumerate(meta[2:4])) ==
            tuple(v & phase_mask(kind, i) for i, v in enumerate(wanted[2:4])),
            'CW/status/TOP/physical occupancy/full tags differ')
    for side, (top, ftw, slots) in enumerate(((case.top, case.ftw, case.slots), (goal['top'], goal['ftw'], goal['slots']))):
        scalar_sw, scalar_tag = meta[2+side], meta[6+side]
        fx = raw[4332+512*side:4844+512*side]
        env = raw[5356+28*side:5384+28*side]
        require(struct.unpack_from('<H', fx)[0] == meta[side] and
                struct.unpack_from('<H', fx, 2)[0] & phase_mask(kind, side) == scalar_sw & phase_mask(kind, side) and
                fx[4] == ftw and struct.unpack_from('<H', env)[0] == meta[side] and
                struct.unpack_from('<H', env, 4)[0] & phase_mask(kind, side) == scalar_sw & phase_mask(kind, side) and
                struct.unpack_from('<H', env, 8)[0] == scalar_tag, 'Raw FXSAVE/FNSTENV scalar views disagree')
        for i, value in enumerate(slots):
            if ftw & (1 << ((top+i) & 7)):
                require(raw[4172+80*side+10*i:4182+80*side+10*i] == value and fx[32+16*i:42+16*i] == value,
                        f'Occupied raw80 payload differs: side{side}/ST{i}')
    require(struct.unpack_from('<I', raw, 5412)[0] == 1, 'Host environment was not restored')
    return {'stack_fault': goal['stack_fault'], 'top_before': case.top, 'top_after': goal['top'],
            'ftw_before': case.ftw, 'ftw_after': goal['ftw'], 'sw_before': meta[2], 'sw_after': meta[3]}


def observe(raw: bytes, case: Case, kind: str) -> dict:
    try:
        return {'difference': None, **assess(raw, case, kind)}
    except ValueError as error:
        return {'difference': str(error), 'raw_meta': list(META.unpack_from(raw, 4140))}


def expected(case: Case, kind: str) -> bytes:
    """Authored comparison-control record, never used as a measured result."""
    goal = transition(case, kind)
    raw = bytearray(RESULT_SIZE)
    cpu = list(case.cpu[:8]); cpu[4] += 4
    raw[:44] = CPU.pack(*cpu, case.cpu[8] & FLAGS, SENTINEL, 0)
    raw[44:4140] = goal['memory']
    META.pack_into(raw, 4140, case.cw, case.cw, case.sw | case.top << 11, goal['sw'], case.ftw,
                   goal['ftw'], full_tags(case.slots, case.top, case.ftw), goal['full_tags'])
    for side, (top, ftw, sw, slots) in enumerate(((case.top, case.ftw, case.sw | case.top << 11, case.slots),
                                                (goal['top'], goal['ftw'], goal['sw'], goal['slots']))):
        fx, env = bytearray(512), bytearray(28)
        struct.pack_into('<HHB', fx, 0, case.cw, sw, ftw)
        struct.pack_into('<H', env, 0, case.cw)
        struct.pack_into('<H', env, 4, sw)
        struct.pack_into('<H', env, 8, full_tags(slots, top, ftw))
        for i, value in enumerate(slots):
            raw[4172+80*side+10*i:4182+80*side+10*i] = value
            fx[32+16*i:42+16*i] = value
        raw[4332+512*side:4844+512*side] = fx
        raw[5356+28*side:5384+28*side] = env
    struct.pack_into('<I', raw, 5412, 1)
    return bytes(raw)


def comparator_controls(cases: list[Case], kind: str) -> list[dict]:
    controls = []
    case = next(c for c in cases if c.ftw == 255 and c.pattern == 0)
    good = expected(case, kind)
    assess(good, case, kind)
    changes = [(f'cpu_{i}', 4*i, 1) for i in range(11)]
    changes += [(f'flags_{b}', 32+b//8, 1 << (b%8)) for b in (0, 2, 4, 6, 7, 10, 11)]
    changes += [(f'page_{i}', 44+i, 1) for i in (0, 1024, 2048, 4095)]
    changes += [(f'meta_{i}', 4140+4*i, 1) for i in range(8)] + [('host_restore', 5412, 1)]
    for side in range(2):
        goal = transition(case, kind)
        ftw, top = (case.ftw, case.top) if side == 0 else (goal['ftw'], goal['top'])
        for i in range(8):
            if ftw & (1 << ((top+i) & 7)):
                for byte in (0, 7, 8, 9):
                    changes.append((f'occupied_side{side}_st{i}_byte{byte}', 4172+80*side+10*i+byte, 1))
                changes.append((f'fx_payload_side{side}_st{i}', 4332+512*side+32+16*i, 1))
        for name, offset in (('fx_cw', 0), ('fx_sw', 2), ('fx_ftw', 4)):
            changes.append((f'{name}_side{side}', 4332+512*side+offset, 1))
        for name, offset in (('env_cw', 0), ('env_sw', 4), ('env_tag', 8)):
            changes.append((f'{name}_side{side}', 5356+28*side+offset, 1))
    for name, offset, xor in changes:
        bad = bytearray(good); bad[offset] ^= xor
        require(observe(bytes(bad), case, kind)['difference'] is not None, 'Comparator missed corruption: '+name)
        controls.append({'name': name, 'outcome': 'rejected'})
    for top in range(8):
        sparse = next(c for c in cases if c.top == top and logical(c.ftw, top) == 2 and c.sw == 0 and c.pattern == 0)
        raw = bytearray(expected(sparse, kind))
        # Corrupt defined exit occupancy, preserving a noncontiguous entry state.
        raw[4160] ^= 1 << top
        require(observe(bytes(raw), sparse, kind)['difference'] is not None, 'Sparse occupancy missed')
        controls.append({'name': 'sparse_mask02_top'+str(top), 'outcome': 'rejected'})
    for sw, bit, label in ((0x22, 2, 'DE'), (0x22, 32, 'PE'), (0x241, 1, 'IE'), (0x241, 64, 'SF')):
        sticky = next(c for c in cases if c.sw == sw and c.top == 7 and c.pattern == 1 and c.ftw == 255)
        raw = bytearray(expected(sticky, kind))
        for offset in (4152, 4844+2, 5384+4):
            raw[offset] ^= bit
        require(observe(bytes(raw), sticky, kind)['difference'] is not None, 'Sticky status missed')
        controls.append({'name': 'lost_sticky_'+label, 'outcome': 'rejected'})
    seeded = next(c for c in cases if c.sw == 0x241)
    raw = bytearray(expected(seeded, kind))
    for offset in (4148, 4332+2, 5356+4):
        raw[offset+1] ^= 2
    require(observe(bytes(raw), seeded, kind)['difference'] is not None, 'Controlled entry C1 missed')
    controls.append({'name': 'lost_controlled_entry_c1', 'outcome': 'rejected'})
    for bit, label in ((1, 'IE'), (64, 'SF')):
        clean = next(c for c in cases if c.sw == 0 and not transition(c, kind)['stack_fault'])
        raw = bytearray(expected(clean, kind))
        for offset in (4152, 4844+2, 5384+4):
            raw[offset] ^= bit
        require(observe(bytes(raw), clean, kind)['difference'] is not None, 'Spurious stack status missed')
        controls.append({'name': 'spurious_stack_'+label, 'outcome': 'rejected'})
    if kind != 'free':
        clean = next(c for c in cases if c.sw == 0x241 and not transition(c, kind)['stack_fault'])
        raw = bytearray(expected(clean, kind))
        for offset in (4152, 4844+2, 5384+4):
            raw[offset+1] ^= 2
        require(observe(bytes(raw), clean, kind)['difference'] is not None, 'Unconditionally cleared exit C1 missed')
        controls.append({'name': 'sticky_exit_c1_on_success', 'outcome': 'rejected'})
    if kind == 'exchange':
        sparse = next(c for c in cases if c.top == 0 and logical(c.ftw, 0) == 2 and c.pattern == 0 and c.sw == 0)
        wrong_slots = (INDEFINITE, sparse.slots[1], *sparse.slots[2:])
        raw = bytearray(expected(sparse, kind))
        for i in range(2):
            raw[4252+10*i:4262+10*i] = wrong_slots[i]
            raw[4844+32+16*i:4854+32+16*i] = wrong_slots[i]
        tag = full_tags(wrong_slots, 0, 3)
        struct.pack_into('<I', raw, 4168, tag)
        struct.pack_into('<H', raw, 5384+8, tag)
        require(observe(bytes(raw), sparse, kind)['difference'] is not None, 'Sparse FXCH direction missed')
        controls.append({'name': 'mask02_wrong_exchange_direction_with_consistent_tags', 'outcome': 'rejected'})
    packed = HEADER.pack(b'MW34RES1', 1, COUNT, RESULT_SIZE, 64) + good*COUNT
    for name, raw in (('short_header', packed[:7]), ('truncated', packed[:-1]), ('trailing', packed+b'X'),
                      ('magic', b'FAILRES1'+packed[8:])):
        try:
            parse_results(raw, 64)
        except ValueError:
            controls.append({'name': 'result_'+name, 'outcome': 'rejected'})
        else:
            raise ValueError('Result parser missed '+name)
    for field, value in ((1, 2), (2, COUNT-1), (3, RESULT_SIZE-1), (4, 32)):
        head = list(HEADER.unpack_from(packed)); head[field] = value
        try:
            parse_results(HEADER.pack(*head)+packed[24:], 64)
        except ValueError:
            controls.append({'name': 'result_header_field'+str(field), 'outcome': 'rejected'})
        else:
            raise ValueError('Result header parser missed '+str(field))
    return controls


def excluded_controls(case: Case, kind: str) -> list[dict]:
    controls = []
    raw = expected(case, kind)
    for side in range(2):
        for bit in range(16):
            if phase_mask(kind, side) & (1 << bit):
                continue
            altered = bytearray(raw)
            for offset in (4148+4*side, 4332+512*side+2, 5356+28*side+4):
                altered[offset+bit//8] ^= 1 << (bit%8)
            assess(bytes(altered), case, kind)
            require(observation(bytes(altered), kind) == observation(raw, kind), 'Excluded status leaked')
            controls.append({'name': f'excluded_sw_side{side}_bit{bit}', 'outcome': 'excluded_by_contract'})
    empty = next(c for c in corpus() if c.ftw == 0)
    raw = expected(empty, kind)
    altered = bytearray(raw)
    altered[4172] ^= 1
    altered[4332+32] ^= 1
    assess(bytes(altered), empty, kind)
    require(observation(bytes(altered), kind) == observation(raw, kind), 'Empty payload leaked')
    controls.append({'name': 'empty_entry_raw_payload', 'outcome': 'excluded_by_contract'})
    return controls


def worker_mutations(cases: list[Case], kind: str) -> list[tuple[str, bytes, bytes, str]]:
    valid, code = encode_corpus(cases), FIXTURES[kind]
    controls = []
    for field, value in ((1, 2), (2, COUNT-1), (3, REQUEST_SIZE-1), (4, 64)):
        head = list(HEADER.unpack_from(valid)); head[field] = value
        controls.append(('header_'+str(field), HEADER.pack(*head)+valid[24:], code, 'State probe requires3456'))
    controls += [('truncated_header', valid[:7], code, 'Truncated x87 state request'),
                 ('truncated_record', valid[:-1], code, 'Truncated x87 state request'),
                 ('trailing_record', valid+b'X', code, 'Trailing x87 state request bytes'),
                 ('wrong_magic', b'FAILREQ1'+valid[8:], code, 'State probe requires3456')]
    for name, field, value, message in (
        ('entry', 9, ENTRY+1, 'Invalid x87 state entry'), ('stack_low', 4, PAGE+15, 'Invalid x87 state entry'),
        ('stack_high', 4, PAGE+PAGE_SIZE-15, 'Invalid x87 state entry'), ('unsafe_tf', 8, 0x302, 'Invalid x87 state entry'),
        ('unsafe_if', 8, 2, 'Invalid x87 state entry'), ('input_low', 1, PAGE-1, 'Invalid raw80'),
        ('input_high', 1, PAGE+4087, 'Invalid raw80'), ('output_high', 2, PAGE+4087, 'Invalid raw80'),
        ('output_wrap', 2, 0xfffffff9, 'Invalid raw80'), ('input_frame', 1, cases[0].cpu[4], 'Invalid raw80'),
        ('output_frame', 2, cases[0].cpu[4]+11, 'Invalid raw80'),
        ('input_output_overlap', 2, cases[0].cpu[1]+9, 'Invalid raw80'),
        ('unmasked', 10, 0x37e, 'Unmasked or unsupported'), ('reserved_pc', 10, 0x17f, 'Unmasked or unsupported'),
        ('unsupported_cw', 10, 0x1037f, 'Unmasked or unsupported'), ('top', 12, 8, 'Unadmitted TOP'),
        ('physical_ftw', 13, 256, 'Unadmitted TOP'), ('sticky_es', 14, 0x80, 'Unadmitted TOP'),
        ('pattern', 15, 2, 'Unadmitted TOP')):
        data = bytearray(valid); struct.pack_into('<I', data, 24+field*4, value)
        controls.append((name, bytes(data), code, message))
    for name, value in (('snan', raw80(0x8000000000000001, 0x7fff)),
                        ('subnormal', raw80(1, 0)), ('unnormal', raw80(1, 0x3fff)),
                        ('pseudo_denormal', raw80(0x8000000000000000, 0)),
                        ('changed_normal', raw80(0x8000000000000002, 0x3fff))):
        for place in (64, 144):
            data = bytearray(valid); data[24+place:24+place+10] = value
            controls.append((name+'_'+str(place), bytes(data), code,
                             'Raw80 values differ' if name == 'changed_normal' else
                             'Raw80 values differ' if place == 144 else 'Unadmitted raw80 encoding'))
    data = bytearray(valid); data[24+154] = 1
    controls.append(('reserved', bytes(data), code, 'Unadmitted TOP'))
    data = bytearray(valid); data[24+REQUEST_SIZE:24+2*REQUEST_SIZE] = data[24:24+REQUEST_SIZE]
    controls.append(('duplicate', bytes(data), code, 'Duplicate x87 state semantic'))
    other = next(value for name, value in FIXTURES.items() if name != kind)
    controls += [('changed_code', valid, code[:-1]+b'\x90', 'fixture_identity'),
                 ('other_code', valid, other, 'fixture_identity'), ('truncated_code', valid, code[:-1], 'fixture_identity')]
    return controls


def run_worker(worker: Path, requests: Path, output: Path, fixture: Path, timeout: int) -> dict:
    command = [str(p.resolve()) for p in (worker, requests, output, fixture)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    require(completed.returncode == 0 and output.is_file(), 'State worker failed: '+completed.stdout+completed.stderr)
    return {'command': command, 'exit_code': completed.returncode, 'stdout': completed.stdout.strip(),
            'stderr': completed.stderr.strip(), 'worker_sha256': digest(worker.read_bytes()),
            'output_path': str(output.resolve()), 'output_sha256': digest(output.read_bytes())}


def worker_controls(workers: list[tuple[str, Path]], cases: list[Case], directory: Path, timeout: int, kind: str) -> list[dict]:
    folder = directory/'admission-controls'; folder.mkdir(exist_ok=True)
    controls = []
    for level, worker in workers:
        for name, requests, fixture, message in worker_mutations(cases, kind):
            if message == 'fixture_identity':
                message = 'Unknown authored state profile/fixture identity' if level == 'reference' else 'Unadmitted state fixture bytes'
            request_path, fixture_path = folder/(level+'-'+name+'.req'), folder/(level+'-'+name+'.code')
            output_path = folder/(level+'-'+name+'.out')
            request_path.write_bytes(requests); fixture_path.write_bytes(fixture)
            require(not output_path.exists(), 'Admission-control output already exists')
            command = [str(p.resolve()) for p in (worker, request_path, output_path, fixture_path)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            require(result.returncode != 0 and message.lower() in (result.stdout+result.stderr).lower() and
                    not output_path.exists(), 'Worker missed admission control: '+level+'/'+name)
            controls.append({'worker': level, 'name': name, 'outcome': 'rejected_before_execution', 'command': command,
                             'exit_code': result.returncode, 'stdout': result.stdout.strip(), 'stderr': result.stderr.strip(),
                             'request_sha256': digest(requests), 'fixture_sha256': digest(fixture)})
    return controls


def native_self_checks(workers: list[tuple[str,Path]], timeout: int) -> list[dict]:
    checks = (('memory_bridges','--check-memory-bridges',12,'State memory bridges: 12 checks passed'),
              ('fp_environment','--check-fp-environment',15,'State FP environment: 15 checks passed'),
              ('mxcsr_isolation','--check-mxcsr-isolation',384,'State MXCSR isolation: 384 checks passed'))
    rows = []
    for level,worker in workers:
        for name,flag,count,message in checks:
            command = [str(worker.resolve()),flag]
            before = digest(worker.read_bytes())
            result = subprocess.run(command,capture_output=True,text=True,timeout=timeout)
            require(result.returncode == 0 and result.stdout.strip() == message and
                    digest(worker.read_bytes()) == before, 'Native live-state selfcheck failed: '+level+'/'+name)
            rows.append({'optimization':level,'name':name,'checks':count,'outcome':'passed','command':command,
                         'exit_code':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip(),
                         'worker_sha256':before})
    return rows


def source_identity() -> dict:
    spec = importlib.util.spec_from_file_location('_state_source_identity', Path(__file__).with_name('source_identity.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.identity(ROOT)


def historical_range():
    path = ROOT/'tools/x87-range/compare_range.py'
    require(digest(path.read_bytes()) == RANGE_COMPARATOR_HASH, 'Historical range validator identity differs')
    spec = importlib.util.spec_from_file_location('_frozen_range_archives', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_previous_range(path: Path, sha256: str) -> dict:
    require(path.is_absolute() and path.resolve() == (ROOT/'reports/x87-range/independent-review/final-pins.json').resolve(),
            'Previous range gate must use preserved final pins')
    require(digest(path.read_bytes()) == sha256 == RANGE_FINAL_PINS_HASH, 'Previous range gate provenance identity differs')
    pins = json.loads(path.read_bytes())
    profiles = []
    for kind in ('mul64', 'div64'):
        folder = ROOT/'reports/x87-range'/kind
        build_path, report_path = folder/'build.json', folder/'comparison/report.json'
        pin = pins[kind]
        require(digest(build_path.read_bytes()) == pin['build_sha256'] and
                digest(report_path.read_bytes()) == pin['report_sha256'], 'Previous range report/build changed')
        build, report = json.loads(build_path.read_bytes()), json.loads(report_path.read_bytes())
        require(build['source_files'] == report['source_files'] and
                digest(json.dumps(build['source_files'],sort_keys=True,separators=(',',':')).encode()) ==
                build['source_digest'] == report['source_digest'] == pin['source_digest'], 'Previous range source binding differs')
        for name, value in build['source_files'].items():
            require(digest((ROOT/name).read_bytes()) == value, 'Previous range authored file changed: '+name)
        for name, value in build['artifacts'].items():
            require(digest((folder/name).read_bytes()) == value, 'Previous range artifact changed: '+name)
        for name, value in build['tool_files'].items():
            require(digest(Path(name).read_bytes()) == value, 'Previous range tool changed: '+name)
        require(report['bounded_contract_passed'] is True and report['total_cases'] == 1920 and
                report['reference_architectural_mismatches'] == report['native_architectural_mismatches'] ==
                report['native_original_differences'] == 0 and report['native_comparisons'] == 3840 and
                report['controls_total'] == pin['controls'], 'Previous range gate lacks complete passing evidence')
        corpus_path = Path(report['corpus_path'])
        require(digest(corpus_path.read_bytes()) == report['corpus_sha256'] == pin['corpus_sha256'], 'Previous range corpus changed')
        for run in [report['reference_run'], *report['native_runs']]:
            require(run['exit_code'] == 0 and digest(Path(run['command'][0]).read_bytes()) == run['worker_sha256'] and
                    digest(Path(run['output_path']).read_bytes()) == run['output_sha256'], 'Previous range worker/result changed')
        profiles.append({'kind': kind, 'build_sha256': pin['build_sha256'], 'report_sha256': pin['report_sha256'],
                         'source_digest': pin['source_digest'], 'original_cases': 1920, 'native_comparisons': 3840})
    return {'path': str(path), 'sha256': sha256, 'profiles': profiles, 'classification': 'immutable_previous_range_gate'}


def baseline_fields(raw: bytes, case: Case, kind: str) -> list[str]:
    """Enumerate frozen pre-repair differences while checking actual raw views."""
    goal = transition(case, kind)
    fields = []
    cpu = list(case.cpu[:8]); cpu[4] += 4
    if raw[:44] != CPU.pack(*cpu, case.cpu[8] & FLAGS, SENTINEL, 0):
        fields.append('CPU_status')
    if raw[44:4140] != goal['memory']:
        fields.append('full_page')
    meta = META.unpack_from(raw, 4140)
    wanted = (case.cw, case.cw, case.sw | case.top << 11, goal['sw'], case.ftw, goal['ftw'],
              full_tags(case.slots, case.top, case.ftw), goal['full_tags'])
    names = ('cw_before','cw_after','sw_before','sw_after','ftw_before','ftw_after','full_tag_before','full_tag_after')
    require(all(v <= 0xFFFF for v in meta[:4]) and all(v <= 255 for v in meta[4:6]) and
            all(v <= 0xFFFF for v in meta[6:]), 'State baseline scalar extent differs')
    for index, (actual, value) in enumerate(zip(meta, wanted, strict=True)):
        mask = phase_mask(kind, index-2) if index in (2,3) else 0xffffffff
        if actual & mask != value & mask:
            fields.append(names[index])
    for side, (top, ftw, slots) in enumerate(((case.top, case.ftw, case.slots),
                                             (goal['top'],goal['ftw'],goal['slots']))):
        fx = raw[4332+512*side:4844+512*side]
        env = raw[5356+28*side:5384+28*side]
        actual_top = meta[2+side] >> 11 & 7
        actual_ftw = meta[4+side]
        actual_slots = tuple(raw[4172+80*side+10*i:4182+80*side+10*i] for i in range(8))
        require(struct.unpack_from('<H',fx)[0] == meta[side] and fx[4] == actual_ftw and
                struct.unpack_from('<H',fx,2)[0] & phase_mask(kind,side) == meta[2+side] & phase_mask(kind,side) and
                struct.unpack_from('<H',env)[0] == meta[side] and
                struct.unpack_from('<H',env,4)[0] & phase_mask(kind,side) == meta[2+side] & phase_mask(kind,side) and
                struct.unpack_from('<H',env,8)[0] == meta[6+side] == full_tags(actual_slots,actual_top,actual_ftw),
                'State baseline actual raw scalar/tag views disagree')
        for index, actual in enumerate(actual_slots):
            if actual_ftw & (1 << ((actual_top+index) & 7)):
                require(fx[32+16*index:42+16*index] == actual, 'State baseline actual occupied FX payload differs')
            if ftw & (1 << ((top+index) & 7)) and actual != slots[index]:
                fields.append(f'occupied_{"before" if side == 0 else "after"}_ST{index}')
    require(struct.unpack_from('<I',raw,5412)[0] == 1, 'State baseline host restoration differs')
    return fields


def validate_state_baseline(path: Path, sha256: str) -> dict:
    require(path.is_absolute() and path.resolve() == (ROOT/'reports/x87-state/baseline-failure/report.json').resolve(),
            'State baseline must use preserved canonical archive')
    require(digest(path.read_bytes()) == sha256 == STATE_BASELINE_HASH, 'State baseline provenance identity differs')
    root = path.parent.resolve()
    manifest_path = root/'manifest.json'
    require(digest(manifest_path.read_bytes()) == STATE_BASELINE_MANIFEST_HASH,
            'State baseline manifest identity differs')
    report, manifest = json.loads(path.read_bytes()), json.loads(manifest_path.read_bytes())
    files = manifest.get('files')
    require(isinstance(files,dict) and len(files) == report.get('archived_files') == 1137 and
            report.get('manifest_sha256') == STATE_BASELINE_MANIFEST_HASH and
            report.get('semantic_stage') == 'unrepaired' and report.get('original_cases') == 13824 and
            report.get('original_mismatches') == report.get('native_before_mismatches') == 0 and
            report.get('native_comparisons') == 27648 and report.get('native_mismatches') == 22272 and
            report.get('entry_status_mask') == '0x3aff' and report.get('exit_status_masks') ==
            {kind: '0x38ff' if kind == 'free' else '0x3aff' for kind in FIXTURES},
            'State baseline archive scope/count/mask differs')

    def bound(name: str, value: str | None = None) -> Path:
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and
                (root/name).resolve().is_relative_to(root) and name in files,
                'State baseline snapshot path is unbound or unsafe')
        target = root/name
        actual = digest(target.read_bytes())
        require(actual == files[name] and (value is None or actual == value), 'State baseline snapshot identity differs: '+name)
        return target

    for name in files:
        bound(name)
    source_files = report.get('source_files')
    require(isinstance(source_files,dict) and digest(json.dumps(source_files,sort_keys=True,separators=(',',':')).encode()) ==
            report.get('source_digest') == manifest.get('source_digest'), 'State baseline archived source binding differs')
    for name, value in source_files.items():
        bound('source/'+name,value)
    pins_path = bound('bindings/initial-canonical-pins.json',STATE_INITIAL_PINS_HASH)
    pins = json.loads(pins_path.read_bytes())
    require(report.get('initial_canonical_pins_sha256') == STATE_INITIAL_PINS_HASH and
            len(report.get('originals',[])) == 4 and len(report.get('experiments',[])) == 8,
            'State baseline initial pin/profile count differs')
    original_by_kind = {row['kind']:row for row in report['originals']}
    experiments = {(row['kind'],row['optimization']):row for row in report['experiments']}
    require(set(original_by_kind) == set(FIXTURES) and
            set(experiments) == {(kind,level) for kind in FIXTURES for level in ('O0','O2')},
            'State baseline profile or optimization coverage differs')
    summaries = []
    gaps = {'push':3456,'pop':3456,'exchange':1920,'free':2304}
    for kind in FIXTURES:
        original, pin = original_by_kind[kind], pins[kind]
        build_path = bound(original['build_snapshot_path'],original['build_sha256'])
        comparison_path = bound(original['comparison_report_snapshot_path'],original['comparison_report_sha256'])
        build, comparison = json.loads(build_path.read_bytes()), json.loads(comparison_path.read_bytes())
        require(original['build_sha256'] == pin['build_sha256'] and original['comparison_report_sha256'] == pin['report_sha256'] and
                build['source_digest'] == comparison['source_digest'] == pin['source_digest'] == report['source_digest'] and
                build['source_files'] == comparison['source_files'] == source_files and
                build['semantic_stage'] == 'unrepaired' and comparison['controls_total'] == pin['controls'] and
                comparison['native_architectural_mismatches'] == pin['native_mismatches'] == 2*gaps[kind],
                'State baseline original build/comparison pins differ')
        for name,value in build['artifacts'].items():
            bound('artifacts/'+kind+'/'+name,value)
        fixture_path = bound(original['fixture_snapshot_path'],original['fixture_sha256'])
        require(fixture_path.read_bytes() == FIXTURES[kind] and build['fixture_sha256'] == original['fixture_sha256'],
                'State baseline fixture differs')
        corpus_path = bound(original['corpus_snapshot_path'],original['corpus_sha256'])
        require(original['corpus_sha256'] == comparison['corpus_sha256'] == pin['corpus_sha256'], 'State baseline corpus pins differ')
        cases = parse_corpus(corpus_path.read_bytes())
        reference_path = bound(original['reference_snapshot_path'],original['reference_sha256'])
        bound(original['worker_snapshot_path'],original['worker_sha256'])
        reference_run = comparison['reference_run']
        require(reference_run['exit_code'] == 0 and reference_run['output_sha256'] == original['reference_sha256'] and
                reference_run['worker_sha256'] == build['reference_sha256'] == original['worker_sha256'],
                'State baseline original worker/result binding differs')
        require(original['cases'] == COUNT and original['mismatches'] == 0 and
                all(not baseline_fields(raw,case,kind) for raw,case in
                    zip(parse_results(reference_path.read_bytes(),32),cases,strict=True)),
                'State baseline original records differ from contract')
        for level in ('O0','O2'):
            row = experiments[kind,level]
            for name in ('corpus','reference','fixture','build','comparison_report'):
                require(row[name+'_snapshot_path'] == original[name+'_snapshot_path'] and
                        row[name+'_sha256'] == original[name+'_sha256'], 'State baseline experiment shared binding differs')
            bound(row['worker_snapshot_path'],row['worker_sha256'])
            native_path = bound(row['result_snapshot_path'],row['result_sha256'])
            run = next(run for run in comparison['native_runs'] if run['optimization'] == level)
            require(run['exit_code'] == 0 and run['worker_sha256'] == row['worker_sha256'] == build['native_'+level+'_sha256'] and
                    run['output_sha256'] == row['result_sha256'], 'State baseline native worker/result binding differs')
            failures, counts = [], {}
            for index,(raw,case) in enumerate(zip(parse_results(native_path.read_bytes(),64),cases,strict=True)):
                fields = baseline_fields(raw,case,kind)
                require(not any('before' in field for field in fields), 'State baseline native entry state differs')
                if fields:
                    failures.append({'case_index':index,'fields':fields})
                    for field in fields: counts[field] = counts.get(field,0)+1
            require(len(failures) == gaps[kind] == row['mismatches'] == run['architectural_mismatches'] and
                    row['cases'] == COUNT and row['native_before_mismatches'] == 0 and
                    failures == row['failures'] and counts == row['defined_difference_counts'],
                    'State baseline failure indices/fields/counts differ')
            summaries.append({'kind':kind,'optimization':level,'cases':COUNT,'mismatches':len(failures),
                              'defined_difference_counts':counts})
    return {'path':str(path),'sha256':sha256,'manifest_sha256':STATE_BASELINE_MANIFEST_HASH,'archived_files':len(files),
            'source_digest':report['source_digest'],'original_cases':13824,'original_mismatches':0,
            'native_comparisons':27648,'native_mismatches':22272,'native_before_mismatches':0,
            'experiments':summaries,'classification':'immutable_canonical_pre_repair_state_gate'}


def stack_policy(kind: str) -> dict:
    name = 'mw34_x87_'+kind+'_prepare'
    helpers = [name] if kind == 'free' else ['mw34_x87_fault_flags',name]
    return {'schema_version':1,'policy':'raw80_physical_tags_masked_stack_faults_sticky_de',
            'design_sha256':HELPER_DESIGN_HASH,'helper_body_sha256':{key:HELPER_BODY_HASHES[key] for key in helpers},
            'entry_helper_calls':{name:1},'insertion_sites':{HELPER_SITES[kind][0]:1},'sticky_DE_sites':int(kind == 'pop')}


def validate_stack_ir(host: str, kind: str) -> None:
    """Check actual generated helper bytes and call placement independently."""
    helper_source = ROOT/'tools/x87-state/semantic_helpers.ll'
    require(digest(helper_source.read_bytes()) == HELPER_DESIGN_HASH, 'Reviewed live-state helper source differs')
    definitions = {}
    for match in re.finditer(r'^define internal void @(mw34_x87_\w+)\([^\n]+\) [^\n]*\{\n(.*?)^\}',host,re.M|re.S):
        require(match[1] not in definitions, 'Duplicate generated live-state helper')
        body = re.sub(r'\bi80 (\d+)\b', lambda m:'i80 '+str(int(m[1])-(1<<80) if int(m[1]) >= 1<<79 else int(m[1])),match[2])
        definitions[match[1]] = digest('\n'.join(' '.join(line.split()) for line in body.splitlines() if line.strip()).encode())
    require(definitions == stack_policy(kind)['helper_body_sha256'], 'Generated live-state helper body identity differs')
    entry = re.search(r'^define .* @sub_10000000\([^\n]+\).*?\{\n(.*?)^\}',host,re.M|re.S)
    require(entry is not None, 'Generated live-state entry missing')
    call = 'call void @mw34_x87_'+kind+'_prepare(ptr %state'+(', ptr %1' if kind == 'push' else '')+')'
    require(entry[1].count(call) == entry[1].count('call void @mw34_x87_') == 1 and
            '  '+call+'\n'+HELPER_SITES[kind][1] in entry[1], 'Generated live-state helper call count/order differs')
    if kind == 'pop':
        sticky = ('  %mw34_old_de = load i8, ptr %28, align 1\n'
                  '  %mw34_sticky_de = or i8 %mw34_old_de, %27\n'
                  '  store i8 %mw34_sticky_de, ptr %28, align 1\n')
        require(entry[1].count(sticky) == 1, 'Generated live-state pop sticky-DE sequence differs')


def validate_layout(layout: dict, build: dict, kind: str) -> None:
    require(layout.get('schema_version') == 1 and layout.get('profile') == 'x87_state_'+kind and
            layout.get('entry_va') == ENTRY and layout.get('authored_bytes') == FIXTURES[kind].hex(),
            'Wrong live-state profile/entry/code')
    require(layout.get('llvm_version') == [21, 1, 8] and layout.get('dll_sha256') == LLVM_HASH and
            layout.get('guest_ir_sha256') == build['artifacts']['guest.ll'] == GUEST_HASHES[kind] and
            layout.get('host_ir_sha256') == build['artifacts']['host.ll'], 'Live-state reviewed IR/tool identity differs')
    require(layout.get('guest_pointer_bits') == 32 and layout.get('host_pointer_bits') == 64 and
            layout.get('state_bytes') == 3504 and layout.get('all_struct_layouts_equal') is True,
            'Missing live-state ABI preservation')
    structures = layout.get('struct_layouts', {})
    require(structures.get('struct.State',{}).get('size') == 3504 and
            structures.get('struct.X86State',{}).get('offsets',[])[9:12] == [2736,2760,2768],
            'Reviewed live-state FPU layout differs')
    bridges = {'__remill_read_memory_f80': int(kind == 'push'), '__remill_write_memory_f80': int(kind == 'pop'),
        '__remill_read_memory_32': 1, '__remill_function_return': 1,
        '__remill_fpu_exception_clear': int(kind == 'pop'), '__remill_fpu_exception_test': int(kind == 'pop')}
    require(layout.get('bridge_calls') == bridges and layout.get('bridge_lowerings') == {},
            'Live-state bridge count or lowering differs')
    require(layout.get('constrained_operations') == {'fcmp_f80': 3 if kind in ('push','pop') else 0} and
            layout.get('rounding') == 'dynamic' and layout.get('exceptions') == 'strict' and
            layout.get('undefined_helpers') == {}, 'Live-state strict operation/undefined policy differs')
    require(build.get('semantic_stage') == 'repaired' and layout.get('status_lowerings') == stack_policy(kind),
            'Unreviewed live-state semantic stage/policy')


def validate_build(build: dict, metadata: Path, reference: Path, native: list[Path], fixture: Path, kind: str) -> dict:
    require(fixture.read_bytes() == FIXTURES[kind] and build.get('fixture_sha256') == digest(FIXTURES[kind]),
            'Live-state authored fixture identity differs')
    require(build.get('schema_version') == 1 and build.get('kind') == kind and build.get('entry_va') == ENTRY and
            build.get('remill_commit') == REMILL_COMMIT and build.get('llvm_version') == '21.1.8' and
            build.get('llvm_dll_sha256') == LLVM_HASH and
            build.get('target_triples') == ['i686-pc-windows-msvc','x86_64-pc-windows-msvc'] and
            build.get('optimization_levels') == ['llc -O0','opt default<O2>; llc -O2'], 'Live-state pinned build recipe differs')
    require(build.get('contract_sha256') == digest((ROOT/'docs/x87-state-contract.md').read_bytes()),
            'Live-state contract identity differs')
    identity = source_identity()
    require(build.get('source_digest') == identity['source_digest'], 'Live-state sources changed after build recording')
    require(build.get('source_files') == identity['source_files'], 'Live-state source-file identities differ')
    require(build.get('reference_sha256') == digest(reference.read_bytes()) and len(native) == 2,
            'Live-state reference worker identity differs')
    for level, worker in zip(('O0','O2'),native,strict=True):
        require(build.get('native_'+level+'_sha256') == digest(worker.read_bytes()), level+' live-state worker identity differs')
    artifacts = build.get('artifacts')
    names = {'fixture.bin','fixture-authored.obj','original-disassembly.txt','guest.ll','guest.bc','host.strict-input.ll',
             'host.ll','host-O2.ll','native-O0.obj','native-O2.obj','layout.json','native-O0-disassembly.txt',
             'native-O2-disassembly.txt','native-O0-symbols.json','native-O2-symbols.json','adapter-controls.json'}
    require(isinstance(artifacts,dict) and names <= set(artifacts), 'Live-state build omitted required artifacts')
    for name, sha256 in artifacts.items():
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and
                (metadata.parent/name).resolve().is_relative_to(metadata.parent.resolve()) and
                type(sha256) is str and len(sha256) == 64 and all(c in '0123456789abcdef' for c in sha256),
                'Invalid live-state artifact identity/path')
        require(digest((metadata.parent/name).read_bytes()) == sha256, 'Live-state build artifact changed: '+name)
    tools = build.get('tool_files')
    require(isinstance(tools,dict) and tools, 'Live-state build omitted tool identities')
    for path, value in tools.items():
        require(Path(path).is_absolute() and digest(Path(path).read_bytes()) == value, 'Live-state compile tool changed: '+path)
    required = {'llvm-mc.exe','llvm-objcopy.exe','llvm-objdump.exe','llvm-nm.exe','llvm-as.exe','opt.exe',
                'llc.exe','clang-cl.exe','llvm-c.dll','python.exe','cmake.exe'}
    require(required <= {Path(path).name.lower() for path in tools}, 'Live-state required tool identities omitted')
    require(build.get('compiler') in tools and Path(build['compiler']).name.lower() == 'clang-cl.exe', 'Live-state compiler binding differs')
    commands = build.get('commands')
    require(isinstance(commands,list) and commands, 'Live-state build omitted commands')
    admitted_programs = {Path(path).resolve() for path in tools} | {p.resolve() for p in native}
    for command in commands:
        require(isinstance(command,list) and command and type(command[0]) is str and
                Path(command[0]).resolve() in admitted_programs, 'Unbound live-state build executable')
    provenance_path = Path(build.get('repair_provenance_path',''))
    require(provenance_path.is_absolute() and provenance_path.resolve() ==
            (ROOT/'reports/x87-repair/toolchain/repair.json').resolve() and
            digest(provenance_path.read_bytes()) == build.get('repair_provenance_sha256') ==
            'e632b0e6f9d4987fb63849331805dc1edb3f011c9ce0f00861780bfe3f58f8db', 'Live-state reused repair provenance differs')
    provenance = json.loads(provenance_path.read_bytes())
    require(provenance.get('remill_lifter_path') in tools and
            tools[provenance['remill_lifter_path']] == build.get('remill_lifter_sha256'),
            'Live-state isolated lifter tool binding differs')
    pinned = {'baseline_semantics_sha256':'138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71',
        'repaired_semantics_sha256':'618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca',
        'baseline_remill_lifter_sha256':'d0973f5f42df6b37b2badbf4f698ad74a3e55e0dd080cd0554b5fe144cf8902f',
        'remill_lifter_sha256':'b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38',
        'patch_sha256':'58bbf4a3497dbc6f0cc0e76c1a04828821bb19565d8d5d4009d7c630d56b37e5'}
    for path_key, hash_key in (('baseline_semantics_path','baseline_semantics_sha256'),
            ('repaired_semantics_path','repaired_semantics_sha256'), ('baseline_remill_lifter_path','baseline_remill_lifter_sha256'),
            ('remill_lifter_path','remill_lifter_sha256'), ('patch_path','patch_sha256')):
        path = Path(provenance.get(path_key,''))
        require(path.is_absolute() and digest(path.read_bytes()) == provenance.get(hash_key) == build.get(hash_key) == pinned[hash_key],
                'Live-state reused repair component identity differs')
    for field in ('semantics_component_hashes','link_libraries'):
        require(isinstance(provenance.get(field),dict) and provenance[field], 'Missing live-state repair components')
        for path, value in provenance[field].items():
            require(digest(Path(path).read_bytes()) == value, 'Live-state repair component changed')
    require(provenance.get('changed_source_files') == ['bin/lift/Lift.cpp','lib/Arch/X86/Semantics/X87.cpp'],
            'Live-state repaired toolchain scope differs')
    layout = json.loads((metadata.parent/'layout.json').read_bytes())
    validate_layout(layout,build,kind)
    validate_stack_ir((metadata.parent/'host.ll').read_text(encoding='utf-8'),kind)
    require(build.get('guest_mxcsr') == 8064 and build.get('object_symbol_rejection_checks_per_native') == 3 and
            build.get('memory_bridge_checks_per_native') == 12 and build.get('fp_environment_checks_per_native') == 15 and
            build.get('mxcsr_isolation_checks_per_native') == 384 and build.get('adapter_mutation_controls') ==
            (13 if kind == 'pop' else 12) and build.get('rounding_bridge_checks_per_native') == 0,
            'Repaired live-state check declarations differ')
    for worker in native:
        for flag in ('--check-memory-bridges','--check-fp-environment','--check-mxcsr-isolation'):
            require(sum(Path(command[0]).resolve() == worker.resolve() and command[1:] == [flag] for command in commands) == 1,
                    'Missing exact live-state native check invocation: '+flag)
    adapter = json.loads((metadata.parent/'adapter-controls.json').read_bytes())
    require(adapter.get('schema_version') == 1 and adapter.get('status') == 'passed' and adapter.get('kind') == kind and
            adapter.get('negative_controls') == build['adapter_mutation_controls'] and adapter.get('positive_controls') == 2 and
            adapter.get('guest_ir_sha256') == artifacts['guest.ll'] and adapter.get('host_ir_sha256') == artifacts['host.ll'],
            'Live-state adapter control artifact differs')
    expected_adapter_files = {str((ROOT/'tools/x87-state'/name).resolve()) for name in
        ('run_adapter_controls.py','adapt_state.py','semantic_lowerings.py','semantic_helpers.ll')}
    require(set(adapter.get('source_sha256',{})) == expected_adapter_files and
            all(digest(Path(path).read_bytes()) == value for path,value in adapter['source_sha256'].items()),
            'Live-state adapter control source binding differs')
    rows = adapter.get('controls',[])
    labels = {'wrong_profile','missing_insertion_site','duplicate_insertion_site','already_lowered_input',
        'removed_helper_call','duplicate_helper_call','wrong_helper_state_pointer','helper_after_observed_operand',
        'wrong_physical_tag_offset','unreviewed_helper_body','changed_exact_guest_IR','cross_profile_IR'}
    if kind == 'pop': labels.add('lost_sticky_DE')
    require(len(rows) == len(labels) and {row.get('name') for row in rows} == labels and
            all(row.get('outcome') == 'rejected_before_compilation' and row.get('diagnostic') for row in rows),
            'Live-state adapter controls lack reviewed rejection coverage')
    nonzero_bridges = {name for name,count in layout['bridge_calls'].items() if count}
    nm = [path for path in tools if Path(path).name.lower() == 'llvm-nm.exe']
    require(len(nm) == 1, 'Live-state LLVM nm identity ambiguous')
    symbol_checks = []
    for level in ('O0','O2'):
        symbols = json.loads((metadata.parent/('native-'+level+'-symbols.json')).read_bytes())
        values = symbols.get('undefined_symbols')
        require(isinstance(values,list) and len(values) == len(set(values)) and nonzero_bridges <= set(values) <=
                nonzero_bridges | {'_fltused','__chkstk','memcpy','memmove'} and symbols.get('kind') == kind and
                symbols.get('status') == 'passed' and symbols.get('negative_controls') == 3 and
                symbols.get('object_sha256') == artifacts['native-'+level+'.obj'] and
                symbols.get('nm_sha256') == tools[nm[0]], 'Live-state object symbols/evidence differ')
        symbol_checks.append(dict(optimization=level,**symbols))
    previous = validate_previous_range(Path(build.get('previous_gate_provenance_path','')),build.get('previous_gate_provenance_sha256',''))
    frozen = historical_range()
    old = frozen.historical_validator()
    initial = old.validate_initial_failure(Path(build.get('initial_failure_provenance_path','')),build.get('initial_failure_provenance_sha256',''))
    c1 = old.validate_c1_baseline(Path(build.get('c1_baseline_path','')),build.get('c1_baseline_sha256',''))
    denormal = frozen.validate_range_baseline(Path(build.get('range_baseline_path','')),build.get('range_baseline_sha256',''))
    state = validate_state_baseline(Path(build.get('state_baseline_path','')),build.get('state_baseline_sha256',''))
    return {'metadata_path': str(metadata.resolve()), 'metadata_sha256': digest(metadata.read_bytes()),
        'build_provenance': build, **identity, 'fixture_path': str(fixture.resolve()), 'fixture_sha256': digest(FIXTURES[kind]),
        'adapter_layout': layout, 'adapter_controls':adapter, 'native_symbol_checks': symbol_checks, 'repair_provenance': provenance,
        'previous_gate_proof': previous, 'initial_failure_proof': initial, 'c1_baseline_proof': c1,
        'range_baseline_proof': denormal, 'state_baseline_proof':state}


def metadata_controls(build: dict, metadata: Path, reference: Path, native: list[Path], fixture: Path,
                      layout: dict, kind: str) -> list[dict]:
    controls = []
    for name, field, value, message in (
        ('fixture','fixture_sha256','0'*64,'fixture identity'), ('contract','contract_sha256','0'*64,'contract identity'),
        ('source_digest','source_digest','0'*64,'sources changed'), ('source_map','source_files',{},'source-file identities'),
        ('reference','reference_sha256','0'*64,'reference worker'), ('native_O0','native_O0_sha256','0'*64,'O0 live-state'),
        ('native_O2','native_O2_sha256','0'*64,'O2 live-state'), ('tool_map','tool_files',{},'tool identities'),
        ('repair','repair_provenance_sha256','0'*64,'repair provenance'),
        ('previous_range','previous_gate_provenance_sha256','0'*64,'range gate provenance'),
        ('missing_previous_range','previous_gate_provenance_path','','range gate must use'),
        ('IE_archive','initial_failure_provenance_sha256','0'*64,'failure provenance'),
        ('C1_archive','c1_baseline_sha256','0'*64,'C1 baseline provenance'),
        ('DE_archive','range_baseline_sha256','0'*64,'Range baseline provenance'),
        ('state_archive','state_baseline_sha256','0'*64,'State baseline provenance'),
        ('missing_state_archive','state_baseline_path','','State baseline must use'),
        ('semantic_stage','semantic_stage','unrepaired','semantic stage'),
        ('missing_memory_checks','memory_bridge_checks_per_native',0,'check declarations'),
        ('missing_FP_checks','fp_environment_checks_per_native',0,'check declarations'),
        ('missing_MXCSR_checks','mxcsr_isolation_checks_per_native',0,'check declarations'),
        ('missing_native_check_command','commands',
         [command for command in build['commands'] if command[1:] != ['--check-fp-environment']],'native check invocation'),
        ('mxcsr','guest_mxcsr',0xDFC0,'check declarations'),
        ('false_adapter_checks','adapter_mutation_controls',8,'check declarations')):
        altered = dict(build); altered[field] = value
        try:
            validate_build(altered,metadata,reference,native,fixture,kind)
        except ValueError as error:
            require(message.lower() in str(error).lower(), 'Unintended metadata rejection: '+name+'/'+str(error))
            controls.append({'name':name,'outcome':'rejected_before_execution','reason':str(error)})
        else:
            raise ValueError('Metadata corruption admitted: '+name)
    for name, field, value in (
        ('profile','profile','fixture'), ('state_extent','state_bytes',3505), ('abi','host_pointer_bits',32),
        ('guest_ir','guest_ir_sha256','0'*64), ('bridges','bridge_calls',{}),
        ('host_nearbyint','bridge_lowerings',{'nearbyintl':1}), ('strict_ops','constrained_operations',{}),
        ('rounding','rounding','nearest'), ('exceptions','exceptions','ignore'),
        ('undefined_helpers','undefined_helpers',{'__remill_undefined_8':1}), ('unreviewed_status','status_lowerings',{'C1':1})):
        altered = dict(layout); altered[field] = value
        try:
            validate_layout(altered,build,kind)
        except ValueError as error:
            controls.append({'name':name,'outcome':'rejected_before_execution','reason':str(error)})
        else:
            raise ValueError('Layout corruption admitted: '+name)
    policy = layout['status_lowerings']
    changes = (
        ('helper_design','design_sha256','0'*64), ('helper_bodies','helper_body_sha256',{}),
        ('helper_call_count','entry_helper_calls',{next(iter(policy['entry_helper_calls'])):0}),
        ('helper_insertion','insertion_sites',{}), ('sticky_DE_site','sticky_DE_sites',int(kind != 'pop')),
        ('helper_policy','policy','unreviewed'))
    for name, field, value in changes:
        altered = dict(layout); altered['status_lowerings'] = dict(policy); altered['status_lowerings'][field] = value
        try:
            validate_layout(altered,build,kind)
        except ValueError as error:
            controls.append({'name':name,'outcome':'rejected_before_execution','reason':str(error)})
        else:
            raise ValueError('Helper policy corruption admitted: '+name)
    return controls


def generated_ir_controls(host: str, kind: str) -> list[dict]:
    validate_stack_ir(host,kind)
    name = 'mw34_x87_'+kind+'_prepare'
    call = '  call void @'+name+'(ptr %state'+(', ptr %1' if kind == 'push' else '')+')\n'
    site = HELPER_SITES[kind][1]
    require(host.count(call) == 1, 'IR control helper call identity differs')
    helper_start = host.index('define internal void @'+name+'(')
    helper_body = host[helper_start:host.index('\n}',helper_start)+2]
    changed_body = helper_body.replace('i32 2772','i32 2773',1)
    require(changed_body != helper_body, 'IR control helper tag location differs')
    variations = [('missing_call',host.replace(call,'',1)),
        ('duplicate_call',host.replace(call,call+call,1)),
        ('reordered_call',host.replace(call+site,site+call,1)),
        ('altered_helper_body',host.replace(helper_body,changed_body,1)),
        ('unexpected_helper_call',host.replace(call,call+'  call void @mw34_x87_unreviewed(ptr %state)\n',1))]
    if kind == 'pop':
        variations.append(('lost_sticky_DE',host.replace('  %mw34_sticky_de = or i8 %mw34_old_de, %27\n',
                                                       '  %mw34_sticky_de = add i8 %mw34_old_de, %27\n',1)))
    controls = []
    for label, altered in variations:
        require(altered != host, 'Generated IR corruption did not alter '+label)
        try:
            validate_stack_ir(altered,kind)
        except ValueError as error:
            controls.append({'name':label,'outcome':'rejected_before_execution','reason':str(error),
                             'altered_host_ir_sha256':digest(altered.encode())})
        else:
            raise ValueError('Generated IR corruption admitted: '+label)
    return controls


def compare(args, report: dict) -> None:
    build = json.loads(args.metadata.read_bytes())
    admission = validate_build(build, args.metadata, args.reference, args.native, args.fixture, args.kind)
    cases = corpus(); encoded = encode_corpus(cases)
    require(parse_corpus(encoded) == cases, 'Independent state corpus parse differs')
    corpus_path = args.output_dir/'corpus.bin'; corpus_path.write_bytes(encoded)
    report.update({'seed': SEED, 'total_cases': COUNT, 'native_comparisons': COUNT*2,
        'request_record_bytes': REQUEST_SIZE, 'result_record_bytes': RESULT_SIZE,
        'corpus_path': str(corpus_path.resolve()), 'corpus_sha256': digest(encoded),
        'observed_integer_flag_mask': hex(FLAGS), 'observed_status_word_masks':
            {'before': '0x3aff', 'after': hex(status_mask(args.kind))},
        **admission, 'native_runs': []})
    report['comparator_negative_controls'] = comparator_controls(cases, args.kind)
    report['metadata_negative_controls'] = metadata_controls(build,args.metadata,args.reference,args.native,args.fixture,
                                                             admission['adapter_layout'],args.kind)
    report['generated_ir_negative_controls'] = generated_ir_controls((args.metadata.parent/'host.ll').read_text(encoding='utf-8'),args.kind)
    report['excluded_observation_controls'] = excluded_controls(cases[0], args.kind)
    workers = [('reference', args.reference), ('O0', args.native[0]), ('O2', args.native[1])]
    report['worker_admission_negative_controls'] = worker_controls(workers, cases, args.output_dir, min(args.timeout, 10), args.kind)
    report['native_self_checks'] = native_self_checks(workers[1:],args.timeout)
    report['native_self_checks_total'] = sum(row['checks'] for row in report['native_self_checks'])
    original_path = args.output_dir/'reference.bin'
    report['reference_run'] = run_worker(args.reference, corpus_path, original_path, args.fixture, args.timeout)
    original = parse_results(original_path.read_bytes(), 32)
    report['reference_cases'] = [dict(case_index=i, **observe(raw, c, args.kind))
                                 for i, (raw, c) in enumerate(zip(original, cases, strict=True))]
    report['reference_architectural_mismatches'] = sum(r['difference'] is not None for r in report['reference_cases'])
    report['reference_architectural_matches'] = COUNT-report['reference_architectural_mismatches']
    for level, worker in workers[1:]:
        output = args.output_dir/('native-'+level+'.bin')
        run = run_worker(worker, corpus_path, output, args.fixture, args.timeout)
        records = parse_results(output.read_bytes(), 64)
        observations = [dict(case_index=i, original_difference=observation(raw, args.kind) != observation(old, args.kind),
                             **observe(raw, c, args.kind))
                        for i, (raw, old, c) in enumerate(zip(records, original, cases, strict=True))]
        mismatches = sum(row['difference'] is not None for row in observations)
        report['native_runs'].append({'optimization': level, **run, 'cases': observations,
            'architectural_matches': COUNT-mismatches, 'architectural_mismatches': mismatches,
            'original_differences': sum(row['original_difference'] for row in observations)})
    report['native_architectural_mismatches'] = sum(r['architectural_mismatches'] for r in report['native_runs'])
    report['native_architectural_matches'] = COUNT*2-report['native_architectural_mismatches']
    report['native_original_differences'] = sum(r['original_differences'] for r in report['native_runs'])
    report['bounded_contract_passed'] = report['reference_architectural_mismatches'] == report['native_architectural_mismatches'] == report['native_original_differences'] == 0
    report['outcome'] = 'passed_bounded_live_x87_stack_contract' if report['bounded_contract_passed'] else 'failed_bounded_live_x87_stack_contract'
    report['controls_total'] = sum(len(report[key]) for key in ('comparator_negative_controls','metadata_negative_controls',
                                                              'generated_ir_negative_controls','worker_admission_negative_controls'))
    report['excluded_observation_controls_total'] = len(report['excluded_observation_controls'])
    report['not_proven'] = ['arbitrary raw80 states or other stack instructions',
        'extended signaling NaN/subnormal/noncanonical policy', 'unmasked x87 trap delivery',
        'cross-mode FIP/FDP/opcode/XMM or reserved raw-image equivalence', 'native game integration',
        'complete CPU/ABI Milestone 2']


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=tuple(FIXTURES), required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--native', type=Path, action='append', required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=60)
    args = parser.parse_args()
    if len(args.native) != 2 or not 1 <= args.timeout <= 60:
        parser.error('Require native O0/O2 and timeout1..60')
    report = {'schema_version': 1, 'experiment': 'bounded_live_x87_stack', 'kind': args.kind,
              'outcome': 'failed', 'bounded_contract_passed': False, 'compatibility_gate': False}
    destination = None
    try:
        private = (ROOT/'reports/x87-state'/args.kind).resolve()
        args.output_dir = args.output_dir.resolve()
        require(args.output_dir.is_relative_to(private) and args.output_dir != private, 'State output must be private profile subdirectory')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        destination = args.output_dir/'report.json'
        compare(args, report)
        require(report['bounded_contract_passed'], 'Bounded live-state gate failed')
        print(args.kind, COUNT, COUNT*2, 'bounded stack cases passed; broader CPU/ABI remains open')
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        report['error'] = str(error); print(error, file=sys.stderr)
        return 1
    finally:
        if destination is not None:
            destination.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
