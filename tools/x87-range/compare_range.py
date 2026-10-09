#!/usr/bin/env python3
"""Measure masked binary64 operand and result range semantics on admitted mul/div."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[2]
HEADER = struct.Struct('<8s4I')
REQUEST = struct.Struct('<10I2I2Q')
STATE = struct.Struct('<11I')
FPU = struct.Struct('<4H2BH')
CODE_BASE = 0x10000000
SENTINEL = 0x10000100
MEMORY_BASE = 0x20001000
MEMORY_SIZE = 4096
RESULT_SIZE = STATE.size + MEMORY_SIZE + FPU.size
FLAG_MASK = 0xCD5
SW_MASK = 0x3AFF
HISTORICAL_SW_MASK = 0x38FF
FIXTURES = {'mul64':bytes.fromhex('dd01dc4908dd1ac3'),'div64':bytes.fromhex('dd01dc7108dd1ac3')}
COUNTS = dict.fromkeys(FIXTURES,1920)
INPUT_SIZES = dict.fromkeys(FIXTURES, 16)
OUTPUT_SIZES = dict.fromkeys(FIXTURES, 8)
SEED = 0x3434
CW_CASES = tuple(0x007F | (pc << 8) | (rc << 10) for pc in (0, 2, 3) for rc in range(4))
PRECISIONS = {0: 24, 2: 53, 3: 64}
SIGN = 1 << 63
ONE = 0x3FF0000000000000
INF = 0x7FF0000000000000
QUIET = 1 << 51
INDEFINITE = 0xFFF8000000000000
S,L,N,M,H = 0x1,0x000fffffffffffff,0x0010000000000000,0x7fefffffffffffff,0x7fe0000000000000
O,T,R,F,A,U,D = ONE,0x4000000000000000,0x4008000000000000,0x3fe0000000000000,0x3ff8000000000000,0x3ff0000000000001,0x3fefffffffffffff
RANGE_MAGNITUDES = ((S,O),(O,S),(L,O),(O,L),(N,O),(O,N),(S,T),(T,S),(S,R),(R,S),
    (S,F),(F,S),(S,A),(A,S),(L,F),(F,L),(N,F),(F,N),(N,R),(R,N),(N,D),(L,U),
    (S,S),(N,N),(M,O),(O,M),(M,T),(T,M),(M,F),(F,M),(M,U),(M,D),(H,T),(H,F),
    (N,H),(H,N),(0x5f30000000000000,0x5f30000000000000),
    (0x0018000000000000,0x3fe5555555555555),
    (0x3ff0000002000002,0x3ff0000004000000),(R,U))
REVIEWED_GUEST = {'mul64':'2191a98a7e3c2bf4d547a22591c342b79185e9540ebeb0df5ebd056308906a1a',
                 'div64':'b45250c94d0f2b1028670d676e9e28c07a8ebe3f88874da2108b5c7e2012ddf2'}
BASELINE_SEMANTICS = '138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71'
REMILL_COMMIT = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
INITIAL_FAILURE_SHA256 = 'b2c41d795a7b3daa9fb5e7f7359b731569cc3ccb9aea5db1bb8b6bf75bd2b067'
INITIAL_MANIFEST_SHA256 = '02ab1f40de52cf6897718f517340c90282a2be8ac984c11b9aefb5f0ff08fc5c'
PROMOTION_POLICY = {'memory_operand_promotion': {
    'moves':1,'source_type':'f64','destination_type':'f80','after_exception_clear':True,
    'before_arithmetic':True,'captured_by_existing_test':True}}
OLD_VALIDATOR_SHA256 = 'c14f133c70f0a42055bedb06bfc855e5ea5094b1e31106d4cf1552b5ac8c8a8a'
PREVIOUS_GATE_SHA256 = 'f9beeeb7f81e2e7f4a648e1a7ae727a7da1abb79f4dbbf4684649874ffcb10a3'
FINAL_STORE_POLICY = {**PROMOTION_POLICY, 'final_store_c1': {
    'stores':1,'state_byte_offset':2739,'rule':'stored_magnitude_greater_than_input',
    'input_type':'f80','stored_type':'f64','assignment':'unconditional',
    'nonfinite_cleared':True,'comparison':'unsigned_abs_f80_encoding'}}
RANGE_BASELINE_SHA256 = 'f52847eb4f286ae7e6af20835898981a4ef0f8e7823d3eb46e6b803c6a7320fd'
RANGE_MANIFEST_SHA256 = '3c81e9b0f2d2dae1028b0382fde785235041c4e56bdcf64503151f1ccd4fb7c6'
INITIAL_RANGE_SOURCE_DIGEST = '999f0fe50125fbf8b658afbf85714e2fc288d7b9bfdbf1804dbe8906be45606f'
RANGE_POLICY = {**FINAL_STORE_POLICY, 'sticky_denormal': {
    'sites':2,'state_byte_offset':2753,'operation':'or_previous_shadow_and_new_classification',
    'arithmetic':True,'final_store':True}}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_identity(root: Path = ROOT) -> dict:
    spec = importlib.util.spec_from_file_location(
        '_mw34_x87_range_identity', Path(__file__).with_name('source_identity.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.identity(root)


def power_two(exponent: int) -> Fraction:
    return Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)


def decode_binary64(bits: int) -> Fraction:
    exponent, fraction = (bits >> 52) & 0x7FF, bits & ((1 << 52) - 1)
    require(exponent != 0x7FF, 'Oracle does not admit infinity or NaN')
    significand = fraction if exponent == 0 else (1 << 52) | fraction
    shift = (-1022 if exponent == 0 else exponent - 1023) - 52
    return (-1 if bits >> 63 else 1) * significand * power_two(shift)


def floor_log_two(value: Fraction) -> int:
    require(value > 0, 'Logarithm requires a positive exact value')
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    if value < power_two(exponent):
        exponent -= 1
    require(power_two(exponent) <= value < power_two(exponent + 1), 'Exact binade calculation failed')
    return exponent


class Rounded(NamedTuple):
    value: Fraction
    negative_zero: bool
    inexact: bool


def round_precision(value: Fraction, precision: int, rc: int, *, negative_zero: bool = False) -> Rounded:
    require(precision in (24, 53, 64) and rc in range(4), 'Unsupported oracle precision/rounding mode')
    if value == 0:
        return Rounded(value, negative_zero, False)
    quantum = power_two(floor_log_two(abs(value)) - precision + 1)
    scaled = abs(value) / quantum
    integer, remainder = divmod(scaled.numerator, scaled.denominator)
    increment = False
    if rc == 0:
        twice = remainder * 2
        increment = twice > scaled.denominator or (twice == scaled.denominator and bool(integer & 1))
    elif rc == 1:
        increment = value < 0 and remainder != 0
    elif rc == 2:
        increment = value > 0 and remainder != 0
    rounded = (integer + int(increment)) * quantum * (-1 if value < 0 else 1)
    return Rounded(rounded, False, rounded != value)


def encode_binary64(value: Fraction, negative_zero: bool = False) -> int:
    if value == 0:
        return int(negative_zero) << 63
    exponent = floor_log_two(abs(value))
    require(-1022 <= exponent <= 1023, 'Corpus result outside finite normal binary64')
    scaled = abs(value) / power_two(exponent - 52)
    require(scaled.denominator == 1 and (1 << 52) <= scaled.numerator < (1 << 53),
            'Binary64 result was not rounded before encoding')
    return ((int(value < 0) << 63) | ((exponent + 1023) << 52) |
            (scaled.numerator - (1 << 52)))


def vectors(kind: str) -> tuple[tuple[int,int], ...]:
    require(kind in FIXTURES,'Unsupported authored range profile')
    return tuple((left|(a<<63),right|(b<<63)) for left,right in RANGE_MAGNITUDES
                 for a,b in ((0,0),(0,1),(1,0),(1,1)))


def classify(bits: int) -> str:
    magnitude = bits & ~SIGN
    exponent, fraction = (magnitude >> 52) & 0x7FF, magnitude & ((1 << 52) - 1)
    if exponent == 0x7FF:
        return 'infinity' if not fraction else ('quiet_nan' if fraction & QUIET else 'signaling_nan')
    if not exponent:
        return 'zero' if not fraction else 'subnormal'
    return 'normal'


def round_quantum(value: Fraction, quantum: Fraction, rc: int) -> Rounded:
    require(value != 0 and quantum > 0 and rc in range(4),'Unsupported range-grid rounding')
    scaled=abs(value)/quantum
    integer,remainder=divmod(scaled.numerator,scaled.denominator)
    increment=(2*remainder>scaled.denominator or
               (2*remainder==scaled.denominator and bool(integer&1))) if rc==0 else (
               remainder!=0 and ((rc==1 and value<0) or (rc==2 and value>0)))
    rounded=(integer+int(increment))*quantum*(-1 if value<0 else 1)
    return Rounded(rounded,value<0 and rounded==0,rounded!=value)


def range_binary64_store(value: Fraction, rc: int) -> dict:
    """Round the full finite f80 value onto the binary64 destination grid."""
    unbounded=round_precision(value,53,rc)
    overflow=abs(unbounded.value)>=power_two(1024)
    if overflow:
        infinity=rc==0 or (rc==1 and value<0) or (rc==2 and value>0)
        bits=(SIGN if value<0 else 0) | (INF if infinity else M)
        finite_value=None if infinity else decode_binary64(bits)
        c1=int(infinity)
        stored_inexact=True
        tiny=False
    else:
        rounded=(round_quantum(value,power_two(-1074),rc) if abs(value)<power_two(-1022)
                 else unbounded)
        bits=encode_binary64_range(rounded.value,rounded.negative_zero)
        finite_value=rounded.value
        c1=int(abs(rounded.value)>abs(value))
        stored_inexact=rounded.inexact
        tiny=0<abs(unbounded.value)<power_two(-1022)
    underflow=tiny and stored_inexact
    return {'output_bits':bits,'output_class':classify(bits),'store_c1':c1,
            'store_inexact':stored_inexact,'overflow':overflow,'underflow':underflow,
            'tiny_input':abs(value)<power_two(-1022),'tiny_unbounded53':tiny,
            'rounded_store':None if finite_value is None else [finite_value.numerator,finite_value.denominator],
            'unbounded53':[unbounded.value.numerator,unbounded.value.denominator],
            'negative_zero':bits==SIGN}


def encode_binary64_range(value: Fraction, negative_zero: bool=False) -> int:
    if value==0:return int(negative_zero)<<63
    if abs(value)<power_two(-1022):
        scaled=abs(value)/power_two(-1074)
        require(scaled.denominator==1 and 0<scaled.numerator<(1<<52),'Invalid binary64 subnormal grid')
        return (int(value<0)<<63)|scaled.numerator
    return encode_binary64(value)


def numeric_specification(case: tuple[int,...],kind: str) -> dict:
    cw=case[10];precision,rc=PRECISIONS[(cw>>8)&3],(cw>>10)&3
    require(kind in FIXTURES and all(classify(c) in ('normal','subnormal') for c in case[12:14]),
            'Range oracle admits only listed nonzero finite inputs')
    left,right=(decode_binary64(c) for c in case[12:14])
    exact=left*right if kind=='mul64' else left/right
    arithmetic=round_precision(exact,precision,rc)
    require(-16382<=floor_log_two(abs(arithmetic.value))<=16383,'Arithmetic escaped normal f80 exponent range')
    store=range_binary64_store(arithmetic.value,rc)
    denormal=any(classify(c)=='subnormal' for c in case[12:14])
    status=(int(denormal)<<1)|(int(store['overflow'])<<3)|(int(store['underflow'])<<4)|(
            int(arithmetic.inexact or store['store_inexact'])<<5)|(store['store_c1']<<9)
    return {'precision':precision,'rounding':rc,**store,'status_word':status,
            'denormal_operand':denormal,'stage_inexact':[arithmetic.inexact,store['store_inexact']],
            'exact_arithmetic':[exact.numerator,exact.denominator],
            'rounded_arithmetic':[arithmetic.value.numerator,arithmetic.value.denominator],
            'full_output_encoding_observed':True}


def overlap(left: int, left_size: int, right: int, right_size: int) -> bool:
    return left < right + right_size and right < left + left_size


def validate_case(case: tuple[int, ...], kind: str) -> None:
    require(kind in FIXTURES, 'Unsupported authored expansion fixture')
    require(len(case) == 14 and all(type(value) is int and 0 <= value <=
            (0xFFFFFFFF if index < 12 else 0xFFFFFFFFFFFFFFFF)
            for index, value in enumerate(case)), 'Invalid request scalar fields')
    esp, source, target = case[4], case[1], case[2]
    input_size, output_size = INPUT_SIZES[kind], OUTPUT_SIZES[kind]
    require(case[9] == CODE_BASE and MEMORY_BASE + 16 <= esp <= MEMORY_BASE + MEMORY_SIZE - 16 and
            case[8] & ~(FLAG_MASK | 0x202) == 0 and case[8] & 0x202 == 0x202,
            'Invalid entry state or unsafe integer flags')
    require(MEMORY_BASE <= source and source + input_size <= MEMORY_BASE + MEMORY_SIZE and
            not overlap(source, input_size, esp, 12), 'Invalid expansion input span or overlap with return frame')
    require(MEMORY_BASE <= target and target + output_size <= MEMORY_BASE + MEMORY_SIZE and
            not overlap(target, output_size, esp, 12), 'Invalid expansion output span or overlap with return frame')
    require(not overlap(source, input_size, target, output_size), 'Expansion input and output spans overlap')
    require(case[10] in CW_CASES, 'Control word is outside reviewed masked PC/RC modes')
    require((case[12], case[13]) in vectors(kind), 'Bits are outside reviewed expansion input vectors')

def corpus(kind: str) -> list[tuple[int, ...]]:
    rng = random.Random(SEED)
    input_size, output_size = INPUT_SIZES[kind], OUTPUT_SIZES[kind]
    sources = (0, 1, 7, 8, 15, 16, 127, 511, 1023, 2047, 3073, MEMORY_SIZE-input_size)
    targets = (MEMORY_SIZE-output_size, MEMORY_SIZE-output_size-1, 4063, 0, 1, 7, 31, 126, 510, 1022, 2047, 3073)
    stacks = (16, 17, 31, 511, 1023, 1537, 2048, 2051, 3001, 4079, 100, 200)
    cases = []
    for index, (cw, base, increment) in enumerate((cw, base, inc)
            for cw in CW_CASES for base, inc in vectors(kind)):
        registers = [rng.getrandbits(32) for _ in range(8)]
        registers[1] = MEMORY_BASE + sources[index % 12]
        candidates = targets[index % 12:] + targets[:index % 12]
        registers[2] = next(MEMORY_BASE + value for value in candidates
                            if not overlap(MEMORY_BASE + value, output_size, registers[1], input_size))
        candidates = stacks[index % 12:] + stacks[:index % 12]
        registers[4] = next(MEMORY_BASE + value for value in candidates
                            if not overlap(MEMORY_BASE + value, 12, registers[1], input_size) and
                            not overlap(MEMORY_BASE + value, 12, registers[2], output_size))
        flags = 0x202 | (rng.getrandbits(12) & (FLAG_MASK & ~0x400)) | ((index & 1) << 10)
        case = (*registers, flags, CODE_BASE, cw, rng.getrandbits(32), base, increment)
        validate_case(case, kind)
        cases.append(case)
    return cases

def encode_corpus(cases: list[tuple[int, ...]], kind: str) -> bytes:
    require(len(cases) == COUNTS[kind] and {(c[10], c[12], c[13]) for c in cases} ==
            {(cw, base, inc) for cw in CW_CASES for base, inc in vectors(kind)},
            'Corpus requires every unique control mode and exact expansion vector')
    for case in cases: validate_case(case, kind)
    return HEADER.pack(b'MW34REQ1', 1, len(cases), REQUEST.size, 32) + b''.join(
        REQUEST.pack(*case) for case in cases)

def parse_corpus(data: bytes, kind: str) -> list[tuple[int, ...]]:
    count = COUNTS[kind]
    require(len(data) >= HEADER.size, 'Truncated request header')
    require(HEADER.unpack_from(data) == (b'MW34REQ1', 1, count, REQUEST.size, 32), 'Invalid request header')
    require(len(data) == HEADER.size + count * REQUEST.size, 'Truncated or trailing requests')
    cases = [REQUEST.unpack_from(data, HEADER.size + index * REQUEST.size) for index in range(count)]
    encode_corpus(cases, kind)
    return cases

def initial_memory(case: tuple[int, ...], kind: str) -> bytes:
    validate_case(case, kind)
    memory = bytearray((index * 37 + case[11]) & 255 for index in range(MEMORY_SIZE))
    struct.pack_into('<3I', memory, case[4] - MEMORY_BASE, SENTINEL, case[10], case[11])
    struct.pack_into('<2Q', memory, case[1] - MEMORY_BASE, case[12], case[13])
    return bytes(memory)

def expected(case: tuple[int, ...], kind: str) -> bytes:
    expansional = numeric_specification(case, kind)
    registers = list(case[:8]); registers[4] += 4
    memory = bytearray(initial_memory(case, kind))
    struct.pack_into('<Q', memory, case[2] - MEMORY_BASE, expansional['output_bits'])
    return (STATE.pack(*registers, case[8] & FLAG_MASK, SENTINEL, 0) + memory +
            FPU.pack(case[10], case[10], 0, expansional['status_word'], 0, 0, 0))

def parse_results(data: bytes, count: int, pointer_bits: int) -> list[bytes]:
    require(len(data) >= HEADER.size, 'Worker returned a truncated header')
    require(HEADER.unpack_from(data) == (b'MW34RES1', 1, count, RESULT_SIZE, pointer_bits),
            'Invalid worker result header')
    require(len(data) == HEADER.size + count * RESULT_SIZE, 'Truncated or trailing result bytes')
    return [data[HEADER.size + i * RESULT_SIZE:HEADER.size + (i + 1) * RESULT_SIZE] for i in range(count)]


def difference(actual: bytes, wanted: bytes, *, sw_mask: int = SW_MASK) -> dict | None:
    require(len(actual) == len(wanted) == RESULT_SIZE, 'Invalid comparator record extent')
    delta = {}
    names = ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi', 'flags', 'eip', 'status')
    for name, left, right in zip(names, STATE.unpack_from(actual), STATE.unpack_from(wanted)):
        if left != right:
            delta[name] = {'actual': hex(left), 'expected': hex(right)}
    memory_a, memory_b = actual[STATE.size:4140], wanted[STATE.size:4140]
    offsets = [i for i, (a, b) in enumerate(zip(memory_a, memory_b)) if a != b]
    if offsets:
        delta['memory'] = {'changed_byte_count': len(offsets), 'first_offsets': offsets[:16]}
    for name, left, right in zip(('cw_before', 'cw_after', 'sw_before', 'sw_after',
                                  'tags_before', 'tags_after', 'reserved'),
                                 FPU.unpack_from(actual, 4140), FPU.unpack_from(wanted, 4140)):
        mask = sw_mask if name.startswith('sw_') else 0xFFFF
        if left & mask != right & mask:
            delta[name] = {'actual': hex(left), 'expected': hex(right), 'observed_mask': hex(mask)}
    return delta or None


def observe_result(actual: bytes, case: tuple[int, ...], kind: str) -> dict:
    delta = difference(actual, expected(case, kind))
    fpu = FPU.unpack_from(actual, 4140)
    specification = numeric_specification(case, kind)
    width = 16
    result = {'classification': 'architectural_match' if delta is None else 'architectural_mismatch',
            'difference': delta, 'entry_cw': hex(case[10]),
            'base_bits': f'0x{case[12]:016x}', 'increment_bits': f'0x{case[13]:016x}',
            'output_bits': f'0x{specification["output_bits"]:0{width}x}',
            'cw_before': hex(fpu[0]), 'cw_after': hex(fpu[1]),
            'raw_sw_before': hex(fpu[2]), 'raw_sw_after': hex(fpu[3]),
            'defined_sw_before': hex(fpu[2] & SW_MASK), 'defined_sw_after': hex(fpu[3] & SW_MASK),
            'tags_before': fpu[4], 'tags_after': fpu[5], 'reserved': fpu[6],
            'oracle': {**specification, 'output_bits': f'0x{specification["output_bits"]:0{width}x}'}}
    result['output_class'] = classify(struct.unpack_from('<Q', actual, STATE.size+case[2]-MEMORY_BASE)[0])
    result['raw_output_bits'] = f'0x{struct.unpack_from("<Q", actual, STATE.size+case[2]-MEMORY_BASE)[0]:016x}'
    return result


def assess_result(actual: bytes, case: tuple[int, ...], kind: str) -> dict:
    observation = observe_result(actual, case, kind)
    require(observation['difference'] is None,
            'Arithmetic result violates bounded specification: ' + json.dumps(observation['difference']))
    return observation

def comparator_controls(cases: list[tuple[int, ...]], kind: str) -> list[dict]:
    case, controls = cases[0], []
    record = expected(case, kind)
    mutations = [(name, i * 4, 1) for i, name in enumerate(
        ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'))]
    mutations += [('flag_' + name, 32 + bit // 8, 1 << (bit % 8)) for name, bit in
                  (('cf', 0), ('pf', 2), ('af', 4), ('zf', 6), ('sf', 7), ('df', 10), ('of', 11))]
    mutations += [('eip', 36, 1), ('status', 40, 1), ('cw_before', 4140, 1), ('cw_after', 4142, 1),
                  ('tags_before', 4148, 1), ('tags_after', 4149, 1), ('reserved', 4150, 1)]
    for slot, offset in (('before', 4144), ('after', 4146)):
        mutations += [('sw_' + slot + '_' + str(bit), offset + bit // 8, 1 << (bit % 8))
                      for bit in range(16) if SW_MASK & (1 << bit)]
    mutations += [('memory_' + str(offset), STATE.size + offset, 1) for offset in (0, 2048, 4095)]
    mutations += [('output_'+str(offset), STATE.size + case[2]-MEMORY_BASE+offset, 1)
                  for offset in range(OUTPUT_SIZES[kind])]
    for name, offset, bit in mutations:
        corrupted = bytearray(record); corrupted[offset] ^= bit
        try:
            assess_result(bytes(corrupted), case, kind)
        except ValueError as error:
            controls.append({'name': name, 'outcome': 'rejected', 'reason': str(error)})
        else:
            raise ValueError('Comparator missed corruption: ' + name)
    count = COUNTS[kind]
    encoded = HEADER.pack(b'MW34RES1', 1, count, RESULT_SIZE, 64) + record * count
    invalid_headers = []
    for name, field, value in (('wrong_result_version',1,2), ('wrong_result_count',2,count-1),
                               ('wrong_result_extent',3,RESULT_SIZE-1)):
        header = list(HEADER.unpack_from(encoded)); header[field] = value
        invalid_headers.append((name, HEADER.pack(*header)+encoded[HEADER.size:], 64))
    for name, data, bits in [('truncated_header', encoded[:7], 64), ('wrong_result_bits', encoded, 32),
                             ('truncated_result', encoded[:-1], 64), ('trailing_result', encoded + b'X', 64),
                             ('wrong_result_magic', b'FAILRES1' + encoded[8:], 64)] + invalid_headers:
        try:
            parse_results(data, count, bits)
        except ValueError as error:
            controls.append({'name': name, 'outcome': 'rejected', 'reason': str(error)})
        else:
            raise ValueError('Result parser accepted ' + name)
    regressions=[]
    predicates=[('missing_loaded_denormal',lambda c,x:classify(c[12])=='subnormal' and classify(c[13])=='normal',2),
        ('missing_memory_denormal',lambda c,x:classify(c[12])=='normal' and classify(c[13])=='subnormal',2),
        ('spurious_denormal',lambda c,x:not x['denormal_operand'],2),
        ('missing_masked_underflow',lambda c,x:x['underflow'],16),
        ('spurious_underflow_exact_subnormal',lambda c,x:x['output_class']=='subnormal' and not x['store_inexact'],16),
        ('arithmetic_precision_is_not_store_underflow',lambda c,x:x['stage_inexact']==[True,False] and x['output_class']=='subnormal',16),
        ('missing_overflow',lambda c,x:x['overflow'],8),
        ('missing_sticky_precision',lambda c,x:bool(x['status_word']&32),32),
        ('lost_final_store_c1',lambda c,x:bool(x['store_c1']),512),
        ('signed_negative_rounding_c1',lambda c,x:bool(x['output_bits']&SIGN) and x['rounding']==1 and x['store_inexact'],512)]
    if kind == 'mul64':
        predicates.append(('tininess_boundary_flag',lambda c,x:x['tiny_input']!=x['tiny_unbounded53'],16))
    for name,predicate,status_xor in predicates:
        chosen=next(c for c in cases if predicate(c,numeric_specification(c,kind)))
        changed=bytearray(expected(chosen,kind));struct.pack_into('<H',changed,4146,
            struct.unpack_from('<H',changed,4146)[0]^status_xor)
        regressions.append((name,chosen,bytes(changed)))
    for cw in CW_CASES:
        chosen=next(c for c in cases if c[10]==cw and numeric_specification(c,kind)['store_c1']==0)
        changed=bytearray(expected(chosen,kind));changed[4147]^=2
        regressions.append(('spurious_c1_mode_'+hex(cw),chosen,bytes(changed)))
    for name,predicate,replace in [
        ('underflow_zero_sign_lost',lambda c,x:x['negative_zero'],lambda x:x['output_bits']^SIGN),
        ('subnormal_flushed_to_zero',lambda c,x:x['output_class']=='subnormal',lambda x:x['output_bits']&SIGN),
        ('overflow_saturated_instead_of_infinity',lambda c,x:x['output_class']=='infinity',lambda x:(x['output_bits']&SIGN)|M),
        ('overflow_infinity_instead_of_saturation',lambda c,x:x['overflow'] and x['output_class']=='normal',lambda x:(x['output_bits']&SIGN)|INF)]:
        chosen=next(c for c in cases if predicate(c,numeric_specification(c,kind)))
        x=numeric_specification(chosen,kind);changed=bytearray(expected(chosen,kind))
        struct.pack_into('<Q',changed,STATE.size+chosen[2]-MEMORY_BASE,replace(x))
        regressions.append((name,chosen,bytes(changed)))
    for name,cw,wrong_cw in [('ignored_pc24',0x7f,0x37f),('ignored_rounding',0xb7f,0x37f),
                             ('ignored_two_stage_precision',0x37f,0x27f)]:
        chosen=next(c for c in cases if c[10]==cw and numeric_specification(c,kind)['output_bits']!=
                    numeric_specification((*c[:10],wrong_cw,*c[11:]),kind)['output_bits'])
        wrong=numeric_specification((*chosen[:10],wrong_cw,*chosen[11:]),kind)
        changed=bytearray(expected(chosen,kind));struct.pack_into('<Q',changed,STATE.size+chosen[2]-MEMORY_BASE,wrong['output_bits'])
        regressions.append((name,chosen,bytes(changed)))
    for name, chosen, wrong in regressions:
        require(difference(wrong, expected(chosen,kind)) is not None,'Regression unchanged: '+name)
        try:
            assess_result(wrong, chosen, kind)
        except ValueError as error:
            controls.append({'name': name, 'outcome': 'rejected', 'reason': str(error)})
        else:
            raise ValueError('Comparator missed expansional regression: ' + name)
    return controls


def excluded_sw_controls(case: tuple[int, ...], kind: str) -> list[dict]:
    record, controls = expected(case, kind), []
    for slot, offset in (('before', 4144), ('after', 4146)):
        for bit in range(16):
            if SW_MASK & (1 << bit):
                continue
            changed = bytearray(record); changed[offset + bit // 8] ^= 1 << (bit % 8)
            require(difference(bytes(changed), record) is None, 'SW excluded-bit mask differs')
            controls.append({'name': f'excluded_sw_{slot}_{bit}', 'outcome': 'excluded_by_contract',
                             'bit': bit, 'observation_mask': hex(SW_MASK)})
    return controls


def worker_mutations(cases: list[tuple[int, ...]], kind: str) -> list[tuple[str, bytes, bytes, str]]:
    valid, fixture, count = encode_corpus(cases,kind),FIXTURES[kind],COUNTS[kind]
    other = 'div64' if kind.startswith('mul') else 'mul64'
    mutations = [('truncated_header', b'MW34', fixture, 'Truncated expansion probe input'),
                 ('truncated_request', valid[:-1], fixture, 'Truncated expansion probe input'),
                 ('trailing_input', valid + b'X', fixture, 'trailing expansion probe input'),
                 ('changed_code', valid, fixture[:-1] + b'\xC2', 'identity'),
                 ('truncated_code', valid, fixture[:-1], 'identity'),
                 ('cross_fixture_code',valid,FIXTURES[other],'identity')]
    for name, field, value in (('bad_header_version', 1, 2), ('bad_header_count', 2, count-1),
                               ('bad_record_extent', 3, REQUEST.size + 4), ('bad_pointer_bits', 4, 64)):
        header = list(HEADER.unpack_from(valid)); header[field] = value
        mutations.append((name, HEADER.pack(*header) + valid[HEADER.size:], fixture, str(count)+' v1 x86 requests'))
    input_size,output_size=INPUT_SIZES[kind],OUTPUT_SIZES[kind]
    changes = [('bad_entry', 9, CODE_BASE + 1, 'entry state'),
               ('unsafe_flags', 8, cases[0][8] | 0x100, 'integer flags'),
               ('missing_required_flags', 8, cases[0][8] & ~0x200, 'integer flags'),
               ('reserved_precision', 10, 0x017F, 'masked PC/RC modes'),
               ('unmasked_exception', 10, 0x007E, 'masked PC/RC modes'),
               ('invalid_control_extent', 10, 0x1007F, 'masked PC/RC modes'),
               ('duplicate_vector',13,cases[1][13], 'Duplicate reviewed expansion'),
               ('unreviewed_left', 12, 0x4000000000000001, 'exact input vectors'),
               ('unreviewed_right', 13, 0x4000000000000001, 'exact input vectors'),
               ('unreviewed_subnormal', 12, 2, 'exact input vectors'),
               ('low_stack', 4, MEMORY_BASE + 15, 'entry state'),
               ('high_stack', 4, MEMORY_BASE + MEMORY_SIZE - 15, 'entry state'),
               ('low_input_extent', 1, MEMORY_BASE - 1, 'expansion input span'),
               ('high_input_extent', 1, MEMORY_BASE + MEMORY_SIZE - input_size+1, 'expansion input span'),
               ('wrapped_input_extent', 1, 0xFFFFFFFF, 'expansion input span'),
               ('input_frame_overlap', 1, cases[0][4] + 4, 'overlap with return frame'),
               ('low_output_extent', 2, MEMORY_BASE - 1, 'expansion output span'),
               ('high_output_extent', 2, MEMORY_BASE + MEMORY_SIZE - output_size+1, 'expansion output span'),
               ('wrapped_output_extent', 2, 0xFFFFFFFF, 'expansion output span'),
               ('output_frame_overlap', 2, cases[0][4] + 4, 'overlap with return frame'),
               ('frame_straddling', 2, cases[0][4] - 1, 'overlap with return frame'),
               ('input_output_overlap', 2, cases[0][1], 'input and output spans overlap')]
    changes += [('unreviewed_nan_payload',12,0x7ff8000000001235,'exact input vectors'),
                ('unreviewed_maximum_finite',12,0x7feffffffffffffe,'exact input vectors')]
    if kind.endswith('-special'):
        changed = list(cases[0]); changed[12], changed[13] = NANS[0], NANS[1]
        mutations.append(('two_nan_inputs',valid[:HEADER.size] + REQUEST.pack(*changed) +
                          valid[HEADER.size+REQUEST.size:],fixture,'exact input vectors'))
    else:
        changes += [('unreviewed_infinity',12,INF,'exact input vectors'),
                    ('unreviewed_zero',12,0,'exact input vectors')]
    for name, field, value, reason in changes:
        changed = list(cases[0]); changed[field] = value
        data = valid[:HEADER.size] + REQUEST.pack(*changed) + valid[HEADER.size + REQUEST.size:]
        mutations.append((name, data, fixture, reason))
    return mutations


def worker_controls(workers: list[tuple[str, Path]], cases: list[tuple[int, ...]],
                    output: Path, timeout: int, kind: str) -> list[dict]:
    controls, folder = [], output / 'admission-controls'
    folder.mkdir(exist_ok=True)
    for role, worker in workers:
        for name, data, code, reason in worker_mutations(cases, kind):
            prefix = folder / (role + '-' + name)
            input_file, result_file, code_file = (prefix.with_suffix(s)
                                                 for s in ('.input.bin', '.result.bin', '.code.bin'))
            input_file.write_bytes(data); code_file.write_bytes(code)
            if result_file.exists(): result_file.unlink()
            command = [str(worker.resolve()), str(input_file.resolve()), str(result_file.resolve()),
                       str(code_file.resolve())]
            run = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            require(run.returncode == 1 and reason.lower() in run.stderr.lower(),
                    f'{role}/{name}: intended rejection missing: {run.returncode} {run.stderr}')
            require(not result_file.exists() or result_file.stat().st_size == 0,
                    f'{role}/{name}: rejection emitted result bytes')
            controls.append({'role': role, 'name': name, 'outcome': 'rejected_before_execution',
                             'command': command, 'exit_code': run.returncode, 'stdout': run.stdout.strip(),
                             'reason': run.stderr.strip(), 'input_sha256': digest(data),
                             'fixture_sha256': digest(code), 'result_bytes': 0})
    return controls


def run_worker(worker: Path, corpus_file: Path, output: Path, fixture: Path, timeout: int) -> dict:
    if output.exists(): output.unlink()
    command = [str(worker.resolve()), str(corpus_file.resolve()), str(output.resolve()), str(fixture.resolve())]
    run = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    require(run.returncode == 0, f'Worker failed ({run.returncode}): {run.stdout}\n{run.stderr}')
    return {'command': command, 'exit_code': run.returncode, 'stdout': run.stdout.strip(),
            'stderr': run.stderr.strip(), 'worker_sha256': digest(worker.read_bytes()),
            'output_path': str(output.resolve()), 'output_sha256': digest(output.read_bytes())}


def historical_validator():
    path=ROOT/'tools/x87-store-c1/compare_store_c1.py'
    require(digest(path.read_bytes())==OLD_VALIDATOR_SHA256,'Historical authored validator identity differs')
    spec=importlib.util.spec_from_file_location('_mw34_frozen_store_c1_archive_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def validate_previous_gate(path: Path, sha256: str) -> dict:
    require(path.is_absolute() and path.resolve()==(ROOT/'reports/x87-store-c1/independent-review/final-pins.json').resolve(),
            'Range build must bind the frozen previous store-C1 gate')
    require(digest(path.read_bytes())==sha256==PREVIOUS_GATE_SHA256,'Previous gate provenance identity differs')
    pins=json.loads(path.read_bytes());profiles=[]
    require(set(pins)=={'mul64','div64','mul-special','div-special'},'Previous gate omitted a profile')
    for kind,pin in pins.items():
        folder=ROOT/'reports/x87-store-c1'/kind
        metadata=folder/'build.json';report_path=folder/'comparison/report.json'
        require(digest(metadata.read_bytes())==pin['build_sha256'] and digest(report_path.read_bytes())==pin['report_sha256'],
                'Previous gate build/report changed')
        build=json.loads(metadata.read_bytes());report=json.loads(report_path.read_bytes())
        source_files=build.get('source_files',{})
        require(build.get('source_digest')==report.get('source_digest')==pin.get('source_digest')==
                '7249d0c4324fb89177e870e2a391549e06a48e94a5bce8a5d1206ebad07e3c93' and
                digest(json.dumps(source_files,sort_keys=True,separators=(',',':')).encode())==pin['source_digest'],
                'Previous gate source recording differs')
        for name,value in source_files.items():
            source=(ROOT/name).resolve()
            require(not Path(name).is_absolute() and source.is_relative_to(ROOT.resolve()) and digest(source.read_bytes())==value,
                    'Previous gate authored source changed: '+name)
        for name,value in build.get('artifacts',{}).items():
            artifact=(folder/name).resolve()
            require(not Path(name).is_absolute() and artifact.is_relative_to(folder.resolve()) and digest(artifact.read_bytes())==value,
                    'Previous gate artifact changed: '+name)
        for name,value in build.get('tool_files',{}).items():
            require(Path(name).is_absolute() and digest(Path(name).read_bytes())==value,'Previous gate tool changed')
        require(report.get('bounded_contract_passed') is True and report.get('observed_status_word_mask')=='0x3aff' and
                report.get('reference_architectural_mismatches')==0 and report.get('native_architectural_mismatches')==0 and
                report.get('native_original_differences')==0 and report.get('controls_total')==pin.get('controls'),
                'Previous gate is not the completed bounded contract')
        corpus_path=folder/'comparison/corpus.bin'
        require(digest(corpus_path.read_bytes())==pin['corpus_sha256']==report.get('corpus_sha256'),
                'Previous gate corpus changed')
        for run in [report['reference_run'],*report['native_runs']]:
            worker=Path(run['command'][0]);result=Path(run['output_path'])
            require(worker.is_absolute() and result.is_absolute() and digest(worker.read_bytes())==run['worker_sha256'] and
                    digest(result.read_bytes())==run['output_sha256'] and run['exit_code']==0,
                    'Previous gate worker/result changed')
        profiles.append({'kind':kind,'build_sha256':pin['build_sha256'],'report_sha256':pin['report_sha256'],
                         'corpus_sha256':pin['corpus_sha256']})
    return {'path':str(path),'sha256':sha256,'profiles':profiles,'classification':'frozen_previous_store_c1_gate_verified'}


def validate_range_baseline(path: Path, sha256: str) -> dict:
    require(path.is_absolute() and path.resolve()==(ROOT/'reports/x87-range/baseline-failure/report.json').resolve(),
            'Range baseline must use the preserved canonical failure archive')
    require(digest(path.read_bytes())==sha256==RANGE_BASELINE_SHA256,'Range baseline provenance identity differs')
    record=json.loads(path.read_bytes());manifest_path=path.with_name('manifest.json')
    require(digest(manifest_path.read_bytes())==record.get('manifest_sha256')==RANGE_MANIFEST_SHA256,
            'Range baseline manifest identity differs')
    manifest=json.loads(manifest_path.read_bytes());files=manifest.get('files')
    require(manifest.get('schema_version')==1 and manifest.get('source_digest')==INITIAL_RANGE_SOURCE_DIGEST and
            manifest.get('purpose')=='Immutable actual pre-DE-repair authored range experiment' and
            isinstance(files,dict) and len(files)==record.get('archived_files')==91,
            'Range archive omitted initial source/artifact identities')
    for name,sha in files.items():
        artifact=(path.parent/name).resolve()
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and
                Path(name).parts[0]=='snapshot' and artifact.is_relative_to(path.parent.resolve()) and
                digest(artifact.read_bytes())==sha,'Range archived file changed: '+name)
    def archived(name: str, sha: str | None=None) -> Path:
        require(name in files,'Range baseline refers to an unarchived file')
        if sha is not None:require(files[name]==sha,'Range baseline measurement identity differs')
        return path.parent/name
    require(record.get('schema_version')==1 and record.get('status')=='reproduced_lost_denormal_operand' and
            record.get('observed_status_mask')==hex(SW_MASK) and record.get('original_cases')==3840 and
            record.get('original_mismatches')==0 and record.get('native_comparisons')==7680 and
            record.get('native_mismatches')==record.get('lost_denormal_operand')==3072 and
            record.get('prior_source_digest')==INITIAL_RANGE_SOURCE_DIGEST and
            record.get('only_defined_difference')=='Sticky denormal-operand flag DE cleared despite a binary64 subnormal operand' and
            record.get('all_other_full_cpu_page_cw_tags_result_observations_match') is True,
            'Range baseline scope/counts differ')
    originals=record.get('originals',[]);experiments=record.get('experiments',[])
    require(len(originals)==2 and {r.get('kind') for r in originals}==set(FIXTURES) and
            len(experiments)==4 and {(r.get('kind'),r.get('optimization')) for r in experiments}==
            {(k,l) for k in FIXTURES for l in ('O0','O2')},'Range baseline omitted a measured profile')
    prerequisites=record.get('previous_provenance_bindings',[])
    require(len(prerequisites)==8,'Range baseline omitted prerequisite provenance')
    for entry in prerequisites:
        archived(entry.get('snapshot_path',''),entry.get('sha256'))
    observations=[]
    for kind in FIXTURES:
        original=next(r for r in originals if r['kind']==kind)
        corpus_path=archived(original.get('corpus_snapshot_path',''),original.get('corpus_sha256'))
        original_path=archived(original.get('reference_snapshot_path',''),original.get('result_sha256'))
        reference_path=archived(original.get('worker_snapshot_path',''),original.get('worker_sha256'))
        fixture_path=archived(original.get('fixture_snapshot_path',''))
        require(fixture_path.read_bytes()==FIXTURES[kind],'Range baseline authored fixture differs')
        cases=parse_corpus(corpus_path.read_bytes(),kind);hardware=parse_results(original_path.read_bytes(),len(cases),32)
        wanted=[expected(c,kind) for c in cases]
        require(all(difference(a,b) is None for a,b in zip(hardware,wanted,strict=True)) and
                original.get('cases')==original.get('matches')==1920 and original.get('mismatches')==0 and
                original.get('failures')==[],'Range baseline originals violate full exact oracle')
        original_histogram={}
        for actual in hardware:
            key=hex(struct.unpack_from('<H',actual,4146)[0]&SW_MASK)
            original_histogram[key]=original_histogram.get(key,0)+1
        require(original.get('defined_status_histogram')==original_histogram,'Range baseline original status histogram differs')
        for level in ('O0','O2'):
            saved=next(r for r in experiments if r['kind']==kind and r['optimization']==level)
            paths={field:archived(saved.get(field+'_snapshot_path',''),saved.get(field+'_sha256'))
                   for field in ('worker','result','corpus','reference','fixture','build','comparison_report')}
            require(paths['corpus']==corpus_path and paths['reference']==original_path and paths['fixture']==fixture_path,
                    'Range baseline profiles used different original records')
            build=json.loads(paths['build'].read_bytes());comparison=json.loads(paths['comparison_report'].read_bytes())
            require(build.get('source_digest')==comparison.get('source_digest')==INITIAL_RANGE_SOURCE_DIGEST and
                    digest(json.dumps(build.get('source_files',{}),sort_keys=True,separators=(',',':')).encode())==INITIAL_RANGE_SOURCE_DIGEST and
                    build.get('reference_sha256')==original['worker_sha256'] and
                    build.get('native_'+level+'_sha256')==saved.get('worker_sha256') and
                    comparison.get('bounded_contract_passed') is False and
                    comparison.get('reference_architectural_mismatches')==0 and
                    comparison.get('native_architectural_mismatches')==1536 and
                    comparison.get('native_original_differences')==1536,
                    'Range baseline source/build/failed report differs')
            for name,sha in build.get('source_files',{}).items():archived('snapshot/'+name,sha)
            archived_layout=json.loads(archived('snapshot/reports/x87-range/'+kind+'/layout.json',
                                                build['artifacts']['layout.json']).read_bytes())
            require(archived_layout.get('status_lowerings')==FINAL_STORE_POLICY and
                    archived_layout.get('profile')=='x87_range_'+kind and
                    archived_layout.get('guest_ir_sha256')==REVIEWED_GUEST[kind],
                    'Range baseline is not the admitted pre-DE repair lowering')
            native=parse_results(paths['result'].read_bytes(),len(cases),64);failures=[];histogram={}
            for index,(actual,original_record,target,case) in enumerate(zip(native,hardware,wanted,cases,strict=True)):
                sw_before,sw_after=struct.unpack_from('<2H',actual,4144)
                expected_sw=struct.unpack_from('<H',target,4146)[0]
                key=hex(sw_after);histogram[key]=histogram.get(key,0)+1
                delta=difference(actual,target)
                if delta is None:
                    require(difference(actual,original_record) is None,'Range baseline original/oracle disagreement')
                    continue
                classified=bytearray(actual);classified[4146]|=2
                require(set(delta)=={'sw_after'} and expected_sw&2 and sw_after&2==0 and
                        difference(bytes(classified),target) is None and difference(bytes(classified),original_record) is None,
                        'Range baseline includes an unrelated observation: '+kind+'/'+level+'/'+str(index))
                spec=numeric_specification(case,kind)
                failures.append({'case_index':index,'cw':hex(case[10]),'left_bits':hex(case[12]),'right_bits':hex(case[13]),
                                 'actual_result_bits':hex(spec['output_bits']),'expected_result_bits':hex(spec['output_bits']),
                                 'raw_status':hex(sw_after),'expected_status':hex(expected_sw),
                                 'arithmetic_inexact':spec['stage_inexact'][0],'store_inexact':spec['stage_inexact'][1],
                                 'denormal':spec['denormal_operand'],'overflow':spec['overflow'],'underflow':spec['underflow'],
                                 'c1':bool(spec['store_c1']),'intermediate':str(Fraction(*spec['rounded_arithmetic'])),
                                 'differences':{'status':{'before':hex(sw_before),'after':hex(sw_after),
                                                        'expected':hex(expected_sw),'xor':'0x2'}}})
            require(len(failures)==saved.get('lost_denormal_operand')==saved.get('mismatches')==768 and
                    saved.get('unrelated_differences')==0 and saved.get('matches')==1152 and
                    saved.get('failures')==failures and saved.get('raw_status_histogram')==histogram and
                    saved.get('defined_status_histogram')==original_histogram,
                    'Range baseline measured failure classification differs: '+kind+'/'+level)
            observations.append({'kind':kind,'optimization':level,'cases':len(cases),'matches':1152,
                                 'missing_denormal_operand':768,'unrelated_differences':0,
                                 'worker_sha256':saved['worker_sha256'],'output_sha256':saved['result_sha256']})
    return {'path':str(path),'sha256':sha256,'manifest_sha256':RANGE_MANIFEST_SHA256,'archived_files':91,
            'original_oracle_matches':3840,'native_observations':7680,'missing_denormal_operand':3072,
            'unrelated_differences':0,'profiles':observations,'classification':'independently_reproduced_lost_sticky_denormal_operand'}


def validate_layout(layout: dict, build: dict, kind: str) -> None:
    require(layout.get('schema_version') == 1 and layout.get('profile') == 'x87_range_'+kind and
            layout.get('entry_va') == CODE_BASE and layout.get('authored_bytes') == FIXTURES[kind].hex(),
            'Wrong authored expansion adapter profile/entry')
    require(layout.get('llvm_version') == [21, 1, 8] and
            layout.get('dll_sha256') == build.get('llvm_dll_sha256') and
            layout.get('guest_ir_sha256') == REVIEWED_GUEST[kind] and
            layout.get('guest_ir_sha256') == build['artifacts'].get('guest.ll') and
            layout.get('host_ir_sha256') == build['artifacts'].get('host.ll'),
            'Adapter tool or reviewed IR identity differs')
    require(layout.get('guest_pointer_bits') == 32 and layout.get('host_pointer_bits') == 64 and
            layout.get('state_bytes') == 3504 and layout.get('all_struct_layouts_equal') is True,
            'Missing checked State/host ABI boundary')
    structures = layout.get('struct_layouts', {})
    require(structures.get('struct.State', {}).get('size') == 3504 and
            structures.get('struct.State', {}).get('offsets') == [0] and
            structures.get('struct.X86State', {}).get('size') == 3504 and
            structures.get('struct.X86State', {}).get('offsets', [])[9:12] == [2736, 2760, 2768],
            'Reviewed State FPU storage differs')
    bridges = {'__remill_read_memory_f64':2,'__remill_write_memory_f64':1,
               '__remill_read_memory_32':1,'__remill_function_return':1,
               '__remill_fpu_exception_clear':2,'__remill_fpu_exception_test':2}
    operations={'fmul' if kind.startswith('mul') else 'fdiv':1,'fptrunc':1,'fpext':3,
                'fcmp_f64':3,'fcmp_f80':6}
    require(layout.get('bridge_calls') == bridges, 'Adapter admitted other expansion bridges/call counts')
    require(layout.get('constrained_operations') == operations and layout.get('rounding') == 'dynamic'
            and layout.get('exceptions') == 'strict','Missing reviewed strict dynamic expansion operations')
    require(layout.get('undefined_helpers') == {},
            'Undefined expansion values escape excluded condition-code slots')
    require(layout.get('bridge_lowerings') == {} and layout.get('status_lowerings') == RANGE_POLICY,
            'Missing reviewed promotion/final-store C1/sticky-DE boundary')


def validate_build(build: dict, metadata: Path, reference: Path, native: list[Path], fixture: Path, kind: str) -> dict:
    require(fixture.read_bytes() == FIXTURES[kind], 'Authored fixture identity differs')
    require(build.get('schema_version') == 1 and build.get('llvm_version') == '21.1.8' and
            build.get('remill_commit') == REMILL_COMMIT and
            build.get('llvm_dll_sha256') == '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb',
            'Build lacks pinned LLVM/Remill provenance')
    require(build.get('kind') == kind and build.get('entry_va') == CODE_BASE and
            build.get('target_triples') == ['i686-pc-windows-msvc', 'x86_64-pc-windows-msvc'] and
            build.get('optimization_levels') == ['llc -O0', 'opt default<O2>; llc -O2'],
            'Build entry, architecture or optimization recipe differs')
    require(build.get('fixture_sha256') == digest(FIXTURES[kind]), 'Build fixture identity differs')
    require(build.get('contract_sha256') == digest((ROOT / 'docs/x87-range-contract.md').read_bytes()),
            'Build contract identity differs')
    identity = source_identity()
    require(build.get('source_digest') == identity['source_digest'], 'Expansion sources changed after build recording')
    require(build.get('source_files') == identity['source_files'], 'Build source-file identities differ')
    require(build.get('reference_sha256') == digest(reference.read_bytes()),
            'Reference worker differs from build provenance')
    require(len(native) == 2, 'Expansion probe requires native O0 and O2 workers in that order')
    for level, worker in zip(('O0', 'O2'), native, strict=True):
        require(build.get('native_' + level + '_sha256') == digest(worker.read_bytes()),
                level + ' worker differs from build provenance')
    artifacts = build.get('artifacts')
    require(isinstance(artifacts, dict) and {'fixture.bin', 'fixture-authored.obj',
            'original-disassembly.txt', 'guest.ll', 'guest.bc', 'host.strict-input.ll',
            'host.ll', 'host-O2.ll', 'native-O0.obj', 'native-O2.obj', 'layout.json',
            'native-O0-disassembly.txt', 'native-O2-disassembly.txt', 'adapter-controls/report.json',
            'native-O0-symbols.json', 'native-O2-symbols.json'} <= set(artifacts),
            'Build omitted required expansion artifacts')
    for name, sha256 in artifacts.items():
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and
                (metadata.parent / name).resolve().is_relative_to(metadata.parent.resolve()) and
                type(sha256) is str and len(sha256) == 64 and all(c in '0123456789abcdef' for c in sha256),
                'Invalid build artifact identity/path')
        require(digest((metadata.parent / name).read_bytes()) == sha256, 'Generated build artifact changed: ' + name)
    tools = build.get('tool_files')
    require(isinstance(tools, dict) and tools, 'Build omitted expansion compile tool identities')
    for path, sha256 in tools.items():
        require(Path(path).is_absolute() and digest(Path(path).read_bytes()) == sha256,
                'Expansion compile tool changed: ' + path)
    required_tools = {'llvm-mc.exe', 'llvm-objcopy.exe', 'llvm-objdump.exe', 'llvm-nm.exe', 'llvm-as.exe',
                      'opt.exe', 'llc.exe', 'clang-cl.exe', 'cmake.exe', 'python.exe', 'llvm-c.dll'}
    require(required_tools <= {Path(path).name.lower() for path in tools},
            'Build omitted required expansion compiler/tool identities')
    dlls = [path for path in tools if Path(path).name.lower() == 'llvm-c.dll']
    require(len(dlls) == 1 and tools[dlls[0]] == build['llvm_dll_sha256'], 'Expansion LLVM DLL identity differs')
    require(isinstance(build.get('commands'), list) and build['commands'], 'Build omitted expansion command recipe')
    tool_paths = {Path(path).resolve() for path in tools}
    for command in build['commands']:
        require(isinstance(command, list) and command and isinstance(command[0], str),
                'Invalid expansion build command')
        program = Path(command[0]).resolve()
        # Built workers are independently admitted above; every compile tool is bound here.
        require(program in tool_paths or program in {p.resolve() for p in native},
                'Unbound expansion build command executable: ' + command[0])
    provenance_path = Path(build.get('repair_provenance_path', ''))
    require(provenance_path.is_absolute() and provenance_path.resolve() ==
            (ROOT / 'reports/x87-repair/toolchain/repair.json').resolve(),
            'Expansion build must bind the unchanged isolated repair record')
    provenance_bytes = provenance_path.read_bytes()
    require(digest(provenance_bytes) == build.get('repair_provenance_sha256'),
            'Repair provenance changed after expansion compilation')
    provenance = json.loads(provenance_bytes)
    require(provenance.get('schema_version') == 1 and provenance.get('remill_commit') == REMILL_COMMIT and
            provenance.get('llvm_version') == '21.1.8' and provenance.get('llvm_dll_sha256') ==
            build['llvm_dll_sha256'], 'Repair toolchain identities differ from expansion build')
    pinned = {'baseline_semantics_sha256': BASELINE_SEMANTICS,
              'repaired_semantics_sha256': '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca',
              'baseline_remill_lifter_sha256': 'd0973f5f42df6b37b2badbf4f698ad74a3e55e0dd080cd0554b5fe144cf8902f',
              'remill_lifter_sha256': 'b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38',
              'patch_sha256': '58bbf4a3497dbc6f0cc0e76c1a04828821bb19565d8d5d4009d7c630d56b37e5'}
    for path_key, hash_key in (('baseline_semantics_path', 'baseline_semantics_sha256'),
                               ('repaired_semantics_path', 'repaired_semantics_sha256'),
                               ('baseline_remill_lifter_path', 'baseline_remill_lifter_sha256'),
                               ('remill_lifter_path', 'remill_lifter_sha256'), ('patch_path', 'patch_sha256')):
        path = Path(provenance.get(path_key, ''))
        require(path.is_absolute() and digest(path.read_bytes()) == provenance.get(hash_key) ==
                build.get(hash_key) == pinned[hash_key], 'Reused repair identity differs: ' + hash_key)
    require(provenance.get('changed_source_files') == ['bin/lift/Lift.cpp', 'lib/Arch/X86/Semantics/X87.cpp'],
            'Expansion experiment changed the reviewed repair overlay scope')
    for field in ('semantics_component_hashes', 'link_libraries'):
        values = provenance.get(field)
        require(isinstance(values, dict) and values, 'Repair omitted pinned components: ' + field)
        for path, sha256 in values.items():
            require(Path(path).is_absolute() and digest(Path(path).read_bytes()) == sha256,
                    'Repair component changed: ' + path)
    layout = json.loads((metadata.parent / 'layout.json').read_bytes())
    validate_layout(layout, build, kind)
    adapter = json.loads((metadata.parent / 'adapter-controls/report.json').read_bytes())
    require(build.get('memory_bridge_checks_per_native') == 8 and
            build.get('fp_environment_checks_per_native') == 15 and
            build.get('adapter_mutation_controls') == 8 and
            adapter.get('accepted_original_profile') == layout['guest_ir_sha256'] and
            adapter.get('mutation_controls') == 8 and len(adapter.get('controls', [])) == 8 and
            all(c.get('status') == 'rejected' for c in adapter['controls']),
            'Expansion build omitted reviewed worker/adapter checks')
    require(build.get('object_symbol_rejection_checks_per_native') == 3 and
            build.get('rounding_bridge_checks_per_native') == 0,
            'Expansion build omitted object-symbol or 80-bit rounding checks')
    require(build.get('guest_mxcsr') == 0x1F80 and build.get('mxcsr_isolation_checks_per_native') == 384,
            'Missing normalized guest MXCSR and reviewed isolation checks')
    nm_paths = [p for p in tools if Path(p).name.lower() == 'llvm-nm.exe']
    require(len(nm_paths) == 1, 'Symbol gate omitted an unambiguous LLVM nm identity')
    symbol_reports = []
    bridge_names = set(layout['bridge_calls'])
    for level in ('O0', 'O2'):
        symbols = json.loads((metadata.parent / ('native-' + level + '-symbols.json')).read_bytes())
        names = symbols.get('undefined_symbols')
        require(isinstance(names, list) and all(type(n) is str for n in names) and
                len(names) == len(set(names)) and bridge_names <= set(names) <=
                bridge_names | {'_fltused', '__chkstk'} and symbols.get('status') == 'passed' and
                symbols.get('kind') == kind and symbols.get('negative_controls') == 3 and
                symbols.get('object_sha256') == artifacts['native-' + level + '.obj'] and
                symbols.get('nm_sha256') == tools[nm_paths[0]],
                'Native object has unreviewed dependencies or symbol evidence differs: ' + level)
        symbol_reports.append(dict(optimization=level, **symbols))
    previous_gate=validate_previous_gate(Path(build.get('previous_gate_provenance_path','')),build.get('previous_gate_provenance_sha256',''))
    frozen=historical_validator()
    initial_failure = frozen.validate_initial_failure(Path(build.get('initial_failure_provenance_path','')),
                                               build.get('initial_failure_provenance_sha256',''))
    c1_baseline = frozen.validate_c1_baseline(Path(build.get('c1_baseline_path','')),
                                     build.get('c1_baseline_sha256',''))
    range_baseline = validate_range_baseline(Path(build.get('range_baseline_path','')),
                                             build.get('range_baseline_sha256',''))
    return {'metadata_path': str(metadata.resolve()), 'metadata_sha256': digest(metadata.read_bytes()),
            'build_provenance': build, **identity, 'fixture_path': str(fixture.resolve()),
            'fixture_sha256': digest(FIXTURES[kind]), 'adapter_layout': layout,
            'repair_provenance': provenance, 'adapter_controls': adapter, 'native_symbol_checks': symbol_reports,
            'initial_failure_proof':initial_failure,'c1_baseline_proof':c1_baseline,'previous_gate_proof':previous_gate,
            'range_baseline_proof':range_baseline}


def metadata_controls(build: dict, metadata: Path, reference: Path, native: list[Path], fixture: Path,
                      layout: dict, kind: str) -> list[dict]:
    controls = []
    for name, field, value, reason in (
            ('wrong_fixture_digest', 'fixture_sha256', '0' * 64, 'fixture identity'),
            ('changed_source_digest', 'source_digest', '0' * 64, 'sources changed'),
            ('changed_source_map', 'source_files', {}, 'source-file identities'),
            ('wrong_reference_digest', 'reference_sha256', '0' * 64, 'Reference worker'),
            ('wrong_native_O0_digest', 'native_O0_sha256', '0' * 64, 'O0 worker'),
            ('wrong_native_O2_digest', 'native_O2_sha256', '0' * 64, 'O2 worker'),
            ('changed_repair_record', 'repair_provenance_sha256', '0' * 64, 'Repair provenance changed'),
            ('changed_semantics', 'repaired_semantics_sha256', '0' * 64, 'Reused repair identity'),
            ('missing_tool_identities', 'tool_files', {}, 'compile tool identities'),
            ('changed_initial_failure', 'initial_failure_provenance_sha256', '0'*64, 'failure provenance identity'),
            ('changed_c1_baseline', 'c1_baseline_sha256', '0'*64, 'C1 baseline provenance identity'),
            ('missing_c1_baseline', 'c1_baseline_path', '', 'C1 baseline must use'),
            ('changed_previous_gate','previous_gate_provenance_sha256','0'*64,'Previous gate provenance identity'),
            ('changed_range_baseline','range_baseline_sha256','0'*64,'Range baseline provenance identity'),
            ('missing_range_baseline','range_baseline_path','','Range baseline must use'),
            ('inherited_guest_mxcsr','guest_mxcsr',0xDFC0,'normalized guest MXCSR'),
            ('missing_mxcsr_isolation_checks','mxcsr_isolation_checks_per_native',0,'normalized guest MXCSR')):
        changed = dict(build); changed[field] = value
        try:
            validate_build(changed, metadata, reference, native, fixture, kind)
        except ValueError as error:
            require(reason.lower() in str(error).lower(), 'Metadata rejected for unintended reason: ' + name)
            controls.append({'name': name, 'outcome': 'rejected_before_execution', 'reason': str(error)})
        else:
            raise ValueError('Build gate missed changed identity: ' + name)
    for name, field, value in (
            ('wrong_expansion_profile', 'profile', 'fixture'),
            ('different_state_extent', 'state_bytes', 3505),
            ('plain_rounding_policy', 'rounding', 'nearest'),
            ('missing_strict_effects', 'exceptions', 'ignore'),
            ('extra_arithmetic', 'constrained_operations', {'fadd': 2, 'fsub': 1, 'fptrunc': 1, 'fpext': 3}),
            ('unsafe_rounding_bridge', 'bridge_lowerings', {'llvm.nearbyint.f80': {
                'bridge':'__mw34_x87_nearbyint80','calls':1,'storage_bytes':8,'host_exceptions_preserved':False}}),
            ('observable_undefined_flags', 'undefined_helpers', {'__remill_undefined_8': {
                'calls': 3, 'only_store_offsets': [2737, 2741, 2743], 'observed': True}}),
            ('missing_promotion_exception_boundary','status_lowerings',{}),
            ('promotion_before_clear','status_lowerings',{'memory_operand_promotion':{
                'moves':1,'source_type':'f64','destination_type':'f80','after_exception_clear':False,
                'before_arithmetic':True,'captured_by_existing_test':True}}),
            ('uncaptured_promotion','status_lowerings',{'memory_operand_promotion':{
                'moves':1,'source_type':'f64','destination_type':'f80','after_exception_clear':True,
                'before_arithmetic':True,'captured_by_existing_test':False}}),
            ('unconstrained_comparison','constrained_operations',{
                'fmul' if kind.startswith('mul') else 'fdiv':1,'fptrunc':1,'fpext':3,'fcmp_f64':3,'fcmp_f80':5}),
            ('missing_final_store_c1','status_lowerings',PROMOTION_POLICY),
            ('wrong_c1_source_precision','status_lowerings',{**RANGE_POLICY,'final_store_c1':{
                **RANGE_POLICY['final_store_c1'],'input_type':'f64'}}),
            ('sticky_c1_assignment','status_lowerings',{**RANGE_POLICY,'final_store_c1':{
                **RANGE_POLICY['final_store_c1'],'assignment':'sticky_or'}}),
            ('signed_c1_comparison','status_lowerings',{**RANGE_POLICY,'final_store_c1':{
                **RANGE_POLICY['final_store_c1'],'comparison':'signed_value_greater_than'}}),
            ('nonfinite_c1_leak','status_lowerings',{**RANGE_POLICY,'final_store_c1':{
                **RANGE_POLICY['final_store_c1'],'nonfinite_cleared':False}}),
            ('missing_sticky_de','status_lowerings',FINAL_STORE_POLICY),
            ('missing_sticky_de_site','status_lowerings',{**RANGE_POLICY,'sticky_denormal':{
                **RANGE_POLICY['sticky_denormal'],'sites':1}}),
            ('replaced_sticky_de','status_lowerings',{**RANGE_POLICY,'sticky_denormal':{
                **RANGE_POLICY['sticky_denormal'],'operation':'replace_previous_with_new_classification'}}),
            ('wrong_de_slot','status_lowerings',{**RANGE_POLICY,'sticky_denormal':{
                **RANGE_POLICY['sticky_denormal'],'state_byte_offset':2755}}),
            ('missing_arithmetic_sticky_de','status_lowerings',{**RANGE_POLICY,'sticky_denormal':{
                **RANGE_POLICY['sticky_denormal'],'arithmetic':False}}),
            ('missing_store_sticky_de','status_lowerings',{**RANGE_POLICY,'sticky_denormal':{
                **RANGE_POLICY['sticky_denormal'],'final_store':False}})):
        changed = dict(layout); changed[field] = value
        try:
            validate_layout(changed, build, kind)
        except ValueError as error:
            controls.append({'name': name, 'outcome': 'rejected_before_execution', 'reason': str(error)})
        else:
            raise ValueError('Layout gate missed altered expansion policy: ' + name)
    return controls


def compare(args, report: dict | None = None) -> dict:
    kind = args.kind
    build = json.loads(args.metadata.read_bytes())
    admission = validate_build(build, args.metadata, args.reference, args.native, args.fixture, kind)
    cases = corpus(kind)
    count, encoded = len(cases), encode_corpus(cases, kind)
    require(parse_corpus(encoded,kind) == cases, 'Independent corpus parse differs')
    corpus_file = args.output_dir / 'corpus.bin'; corpus_file.write_bytes(encoded)
    if report is None: report = {}
    specifications = [numeric_specification(case,kind) for case in cases]
    report.update({'schema_version': 1, 'experiment': 'bounded_x87_binary64_range', 'kind':kind,
              'outcome': 'failed', 'bounded_contract_passed': False, 'compatibility_gate': False,
               'scope': 'listed finite nonzero binary64 range vectors; full CPU/page/CW/status/C1/tag observations only',
              'seed': SEED, 'total_cases': count, 'request_record_bytes': REQUEST.size,
              'result_record_bytes': RESULT_SIZE, 'corpus_path': str(corpus_file.resolve()),
              'corpus_sha256': digest(encoded), 'observed_integer_flag_mask': hex(FLAG_MASK),
              'observed_status_word_mask': hex(SW_MASK), 'input_span_bytes':INPUT_SIZES[kind],
              'output_span_bytes':OUTPUT_SIZES[kind],
              'input_control_words': [hex(value) for value in CW_CASES],
              'input_vectors': [{'base_bits':f'0x{b:016x}','increment_bits':f'0x{i:016x}'}
                               for b,i in vectors(kind)],
              'coverage': {'precision_controls': [0, 2, 3], 'significand_precisions': [24, 53, 64],
                           'rounding_controls': [0, 1, 2, 3], 'vectors_per_control_word': len(vectors(kind)),
                           'unique_control_vector_triples': len({(c[10], c[12], c[13]) for c in cases}),
                           'masked_exception_modes_only': True,
                           'df_set_cases': sum(bool(c[8] & 0x400) for c in cases),
                           'unaligned_input_cases': sum(bool(c[1] & 7) for c in cases),
                           'unaligned_output_cases': sum(bool(c[2] & 7) for c in cases),
                           'unaligned_stack_cases': sum(bool(c[4] & 3) for c in cases),
                           'input_offsets': sorted({c[1] - MEMORY_BASE for c in cases}),
                           'output_offsets': sorted({c[2] - MEMORY_BASE for c in cases}),
                           'stack_offsets': sorted({c[4] - MEMORY_BASE for c in cases}),
                           'negative_zero_results': sum(s['negative_zero'] for s in specifications),
                           'zero_results': sum(s['output_bits'] & ((1<<63)-1)==0 for s in specifications),
                           'inexact_results': sum(bool(s['status_word'] & 0x20) for s in specifications),
                           'store_c1_set_results': sum(s['store_c1'] for s in specifications),
                           'exact_results': sum(not (s['status_word'] & 0x20) for s in specifications) if not kind.endswith('-special') else None,
                           'invalid_results': sum(bool(s['status_word'] & 1) for s in specifications),
                           'zero_divide_results': sum(bool(s['status_word'] & 4) for s in specifications),
                           'output_classes': {name:sum(s['output_class']==name for s in specifications)
                                              for name in sorted({s['output_class'] for s in specifications})},
                           'denormal_operand_results':sum(s['denormal_operand'] for s in specifications),
                           'store_underflow_results':sum(s['underflow'] for s in specifications),
                           'store_overflow_results':sum(s['overflow'] for s in specifications),
                           'tininess_discrimination_results':sum(s['tiny_input']!=s['tiny_unbounded53'] for s in specifications)},
              'python_version': sys.version.split()[0], **admission, 'native_runs': []})
    workers = [('reference', args.reference), ('O0', args.native[0]), ('O2', args.native[1])]
    report['comparator_negative_controls'] = comparator_controls(cases,kind)
    report['excluded_status_bit_controls'] = excluded_sw_controls(cases[0],kind)
    report['metadata_negative_controls'] = metadata_controls(
        build, args.metadata, args.reference, args.native, args.fixture, admission['adapter_layout'],kind)
    report['worker_admission_negative_controls'] = worker_controls(
        workers, cases, args.output_dir, min(args.timeout, 10),kind)
    reference_file = args.output_dir / 'reference.bin'
    report['reference_run'] = run_worker(args.reference, corpus_file, reference_file, args.fixture, args.timeout)
    original = parse_results(reference_file.read_bytes(), count, 32)
    report['reference_cases'] = [dict(case_index=index, **observe_result(record, case,kind))
                                for index, (record, case) in enumerate(zip(original, cases, strict=True))]
    report['reference_architectural_matches'] = sum(r['difference'] is None for r in report['reference_cases'])
    report['reference_architectural_mismatches'] = count - report['reference_architectural_matches']
    for level, worker in workers[1:]:
        output = args.output_dir / ('native-' + level + '.bin')
        measured = run_worker(worker, corpus_file, output, args.fixture, args.timeout)
        records = parse_results(output.read_bytes(), count, 64)
        observations = []
        for index, (record, baseline, case) in enumerate(zip(records, original, cases, strict=True)):
            observations.append(dict(case_index=index, **observe_result(record, case,kind)))
            delta = difference(record, baseline)
            observations[-1]['original_difference'] = delta
        matches = sum(r['difference'] is None for r in observations)
        report['native_runs'].append({'optimization': level, **measured, 'cases': observations,
                                     'architectural_matches': matches, 'architectural_mismatches': count-matches,
                                     'original_differences': sum(r['original_difference'] is not None for r in observations),
                                     'raw_status_word_difference_cases': sum(
                                         FPU.unpack_from(a, 4140)[2:4] != FPU.unpack_from(b, 4140)[2:4]
                                         for a, b in zip(records, original, strict=True))})
    report['controls_total'] = sum(len(report[key]) for key in ('comparator_negative_controls',
                                'metadata_negative_controls', 'worker_admission_negative_controls'))
    report['excluded_status_bit_controls_total'] = len(report['excluded_status_bit_controls'])
    report['native_comparisons'] = count * 2
    report['native_architectural_matches'] = sum(r['architectural_matches'] for r in report['native_runs'])
    report['native_architectural_mismatches'] = sum(r['architectural_mismatches'] for r in report['native_runs'])
    report['native_original_differences'] = sum(r['original_differences'] for r in report['native_runs'])
    report['bounded_contract_passed'] = (report['reference_architectural_mismatches'] == 0 and
                                        report['native_architectural_mismatches'] == 0 and
                                        report['native_original_differences'] == 0)
    report['outcome'] = ('passed_bounded_binary64_range_contract' if report['bounded_contract_passed'] else
                         'failed_bounded_binary64_range_contract')
    report['not_proven'] = ['arbitrary x87 inputs or other instructions',
                           'live 80-bit register contents or nonempty entry stacks',
                           'C0/C2/C3/busy equivalence', 'arbitrary range inputs or other destination formats',
                           'unlisted NaNs or two-NaN selection', 'unmasked trap delivery',
                           'exceptional-exit FIP/FDP restoration', 'game native integration']
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=tuple(FIXTURES),required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--native', type=Path, action='append', required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=60)
    args = parser.parse_args()
    if len(args.native) != 2 or not 1 <= args.timeout <= 60:
        parser.error('Require O0/O2 workers and timeout 1-60 seconds')
    report = {'schema_version': 1, 'experiment': 'bounded_x87_binary64_range', 'kind':args.kind,
              'outcome': 'failed', 'bounded_contract_passed': False, 'compatibility_gate': False}
    destination = None
    try:
        private_root = (ROOT / 'reports/x87-range' / args.kind).resolve()
        args.output_dir = args.output_dir.resolve()
        require(args.output_dir.is_relative_to(private_root) and args.output_dir != private_root,
                'Arithmetic output must be a private subdirectory of reports/x87-range/' + args.kind)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        destination = args.output_dir / 'report.json'
        compare(args, report)
        require(report['bounded_contract_passed'], f'{args.kind} bounded binary64 range gate failed: '
                f'{report["reference_architectural_mismatches"]} original / '
                f'{report["native_architectural_mismatches"]} native oracle mismatches, '
                f'{report["native_original_differences"]} native/original differences')
        print(f'{args.kind} bounded binary64 range contract passed: {report["total_cases"]} original cases, '
              f'{report["native_comparisons"]} native O0/O2 comparisons, zero mismatches; '
              'broader compatibility remains open')
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
        print(str(error), file=sys.stderr)
        return 1
    finally:
        if destination is not None:
            destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
