#!/usr/bin/env python3
"""Measure final FSTP C1 on admitted mul/div and masked-special profiles."""
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
FIXTURES = {'mul64': bytes.fromhex('dd01dc4908dd1ac3'),
            'div64': bytes.fromhex('dd01dc7108dd1ac3'),
            'mul-special': bytes.fromhex('dd01dc4908dd1ac3'),
            'div-special': bytes.fromhex('dd01dc7108dd1ac3')}
COUNTS = {'mul64': 1152, 'div64': 1152, 'mul-special': 480, 'div-special': 480}
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
FINITE_MAGNITUDES = (
    (0x3ff0000000000000, 0x3ff0000000000000),
    (0x3ff0000000000000, 0x4000000000000000),
    (0x4000000000000000, 0x3ff0000000000000),
    (0x3ff0000000000000, 0x4008000000000000),
    (0x4008000000000000, 0x3ff0000000000000),
    (0x4000000000000000, 0x4008000000000000),
    (0x4008000000000000, 0x4000000000000000),
    (0x4014000000000000, 0x401c000000000000),
    (0x401c000000000000, 0x4014000000000000),
    (0x3ff0000020000000, 0x3ff0000010000000),
    (0x3ff0000010000000, 0x3ff0000010000000),
    (0x3ff0000000000001, 0x3ff0000000000001),
    (0x3fefffffffffffff, 0x3ff0000000000001),
    (0x3fefffffffffffff, 0x3fefffffffffffff),
    (0x3ff0000002000002, 0x3ff0000004000000),
    (0x3ff0000000000001, 0x4008000000000000),
    (0x4008000000000000, 0x3ff0000000000001),
    (0x3ff8000000000000, 0x3ff8000000000000),
    (0x5f30000000000000, 0x5f30000000000000),
    (0x20b0000000000000, 0x20b0000000000000),
    (0x5f30000000000000, 0x20b0000000000000),
    (0x20b0000000000000, 0x5f30000000000000),
    (0x5f30000000000000, 0x4008000000000000),
    (0x20b0000000000000, 0x4008000000000000))
SPECIAL_MAGNITUDES = ((0, ONE), (ONE, 0), (0, 0), (0, INF),
                      (INF, 0), (INF, ONE), (ONE, INF), (INF, INF))
NANS = (0x7ff8000000001234, 0xfff8000000004321,
        0x7ff0000000001234, 0xfff0000000004321)
REVIEWED_GUEST = {'mul64':'2191a98a7e3c2bf4d547a22591c342b79185e9540ebeb0df5ebd056308906a1a',
                 'div64':'b45250c94d0f2b1028670d676e9e28c07a8ebe3f88874da2108b5c7e2012ddf2'}
REVIEWED_GUEST.update({'mul-special':REVIEWED_GUEST['mul64'], 'div-special':REVIEWED_GUEST['div64']})
BASELINE_SEMANTICS = '138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71'
REMILL_COMMIT = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
INITIAL_FAILURE_SHA256 = 'b2c41d795a7b3daa9fb5e7f7359b731569cc3ccb9aea5db1bb8b6bf75bd2b067'
INITIAL_MANIFEST_SHA256 = '02ab1f40de52cf6897718f517340c90282a2be8ac984c11b9aefb5f0ff08fc5c'
PROMOTION_POLICY = {'memory_operand_promotion': {
    'moves':1,'source_type':'f64','destination_type':'f80','after_exception_clear':True,
    'before_arithmetic':True,'captured_by_existing_test':True}}
C1_BASELINE_SHA256 = '03eba1e074e3770bb42c2c411e876335f0cef556c9e4dd80d027cc960cd2f586'
C1_MANIFEST_SHA256 = 'ce06d189c3d2547b7f050623db2281d139c1e9d896d35059c3fa797bcb5b77cb'
PRIOR_SOURCE_DIGEST = '1171023baadd2e832393314aabb101dd7872ba06195af04556a55e55c2eb84ef'
FINAL_STORE_POLICY = {**PROMOTION_POLICY, 'final_store_c1': {
    'stores':1,'state_byte_offset':2739,'rule':'stored_magnitude_greater_than_input',
    'input_type':'f80','stored_type':'f64','assignment':'unconditional',
    'nonfinite_cleared':True,'comparison':'unsigned_abs_f80_encoding'}}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_identity(root: Path = ROOT) -> dict:
    spec = importlib.util.spec_from_file_location(
        '_mw34_x87_store_c1_identity', Path(__file__).with_name('source_identity.py'))
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


def vectors(kind: str) -> tuple[tuple[int, int], ...]:
    require(kind in FIXTURES, 'Unsupported authored arithmetic profile')
    magnitudes = SPECIAL_MAGNITUDES if kind.endswith('-special') else FINITE_MAGNITUDES
    signed = tuple((left | (a << 63), right | (b << 63))
                   for left, right in magnitudes for a, b in ((0, 0), (0, 1), (1, 0), (1, 1)))
    return signed + tuple(pair for nan in NANS for pair in ((nan, ONE), (ONE, nan))) if kind.endswith('-special') else signed


def classify(bits: int) -> str:
    magnitude = bits & ~SIGN
    exponent, fraction = (magnitude >> 52) & 0x7FF, magnitude & ((1 << 52) - 1)
    if exponent == 0x7FF:
        return 'infinity' if not fraction else ('quiet_nan' if fraction & QUIET else 'signaling_nan')
    if not exponent:
        return 'zero' if not fraction else 'subnormal'
    return 'normal'


def special_specification(case: tuple[int, ...], kind: str) -> dict:
    left, right = case[12:14]
    a, b = classify(left), classify(right)
    sign = (left ^ right) & SIGN
    flags = 0
    if 'nan' in a or 'nan' in b:
        require(('nan' in a) != ('nan' in b), 'Two-NaN selection is outside this contract')
        source = left if 'nan' in a else right
        flags = int(classify(source) == 'signaling_nan')
        output, rule = source | QUIET, 'single_nan_payload_and_sign_preserved_quieted'
    elif kind.startswith('mul'):
        if {a, b} == {'zero', 'infinity'}:
            output, flags, rule = INDEFINITE, 1, 'masked_invalid_floating_indefinite'
        else:
            output = sign | (INF if 'infinity' in (a, b) else 0)
            rule = 'signed_infinity' if 'infinity' in (a, b) else 'signed_zero'
    else:
        require(kind.startswith('div'), 'Unknown special arithmetic operation')
        if (a == b == 'zero') or (a == b == 'infinity'):
            output, flags, rule = INDEFINITE, 1, 'masked_invalid_floating_indefinite'
        elif b == 'zero':
            output, flags = sign | INF, 4 if a == 'normal' else 0
            rule = 'finite_divide_by_zero' if flags else 'infinity_divide_by_zero'
        elif a == 'infinity':
            output, rule = sign | INF, 'signed_infinity'
        else:
            output, rule = sign, 'signed_zero'
    return {'output_bits': output, 'output_class': classify(output), 'status_word': flags,
            'special_rule': rule, 'left_class': a, 'right_class': b,
            'stage_inexact': [False, False], 'negative_zero': output == SIGN,
            'store_c1': 0, 'full_output_encoding_observed': True}


def numeric_specification(case: tuple[int, ...], kind: str) -> dict:
    cw = case[10]
    precision, rc = PRECISIONS[(cw >> 8) & 3], (cw >> 10) & 3
    if kind.endswith('-special'):
        return {'precision': precision, 'rounding': rc, **special_specification(case, kind)}
    require(kind in ('mul64', 'div64') and all(classify(c) == 'normal' for c in case[12:14]),
            'Finite oracle only admits nonzero normal inputs')
    left, right = (decode_binary64(c) for c in case[12:14])
    exact_value = left * right if kind == 'mul64' else left / right
    arithmetic = round_precision(exact_value, precision, rc)
    stored = round_precision(arithmetic.value, 53, rc)
    require(-1022 <= floor_log_two(abs(arithmetic.value)) <= 1023 and
            -1022 <= floor_log_two(abs(stored.value)) <= 1023,
            'Finite arithmetic/store escaped reviewed normal exponent range')
    bits = encode_binary64(stored.value)
    return {'precision': precision, 'rounding': rc, 'output_bits': bits,
            'output_class': classify(bits),
            'status_word': (0x20 if arithmetic.inexact or stored.inexact else 0) | (int(abs(stored.value) > abs(arithmetic.value)) << 9),
            'store_c1': int(abs(stored.value) > abs(arithmetic.value)),
            'rounded_store': [stored.value.numerator, stored.value.denominator],
            'stage_inexact': [arithmetic.inexact, stored.inexact], 'negative_zero': False,
            'exact_arithmetic': [exact_value.numerator, exact_value.denominator],
            'rounded_arithmetic': [arithmetic.value.numerator, arithmetic.value.denominator],
            'full_output_encoding_observed': True}

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
    regressions = []
    if kind.endswith('-special'):
        chosen = next(c for c in cases if numeric_specification(c, kind)['negative_zero'])
        changed = bytearray(expected(chosen, kind)); changed[STATE.size+chosen[2]-MEMORY_BASE+7] ^= 0x80
        regressions.append(('special_zero_sign_lost', chosen, bytes(changed)))
        for name, needle, output_xor, status_xor in (
                ('quiet_nan_payload_changed', 'quiet_nan', 1, 0),
                ('quiet_nan_sign_changed', 'quiet_nan', SIGN, 0),
                ('nan_quiet_bit_missing', 'quiet_nan', QUIET, 0),
                ('spurious_precision_on_nan', 'quiet_nan', 0, 0x20)):
            chosen = next(c for c in cases if classify(c[12]) == needle or classify(c[13]) == needle)
            spec = numeric_specification(chosen, kind); changed = bytearray(expected(chosen, kind))
            struct.pack_into('<Q', changed, STATE.size+chosen[2]-MEMORY_BASE, spec['output_bits'] ^ output_xor)
            struct.pack_into('<H', changed, 4146, spec['status_word'] ^ status_xor)
            regressions.append((name, chosen, bytes(changed)))
        for position in (12, 13):
            chosen = next(c for c in cases if classify(c[position]) == 'signaling_nan')
            changed = bytearray(expected(chosen, kind)); changed[4146] ^= 1
            regressions.append(('missing_snan_invalid_position_'+str(position), chosen, bytes(changed)))
        chosen = next(c for c in cases if numeric_specification(c, kind)['output_bits'] == INDEFINITE)
        changed = bytearray(expected(chosen, kind)); changed[4146] ^= 1
        regressions.append(('missing_masked_invalid', chosen, bytes(changed)))
        if kind.startswith('div'):
            chosen = next(c for c in cases if numeric_specification(c, kind)['status_word'] == 4)
            changed = bytearray(expected(chosen, kind)); changed[4146] ^= 4
            regressions.append(('missing_finite_zero_divide', chosen, bytes(changed)))
            chosen = next(c for c in cases if classify(c[12]) == 'infinity' and classify(c[13]) == 'zero')
            changed = bytearray(expected(chosen, kind)); changed[4146] ^= 4
            regressions.append(('spurious_infinity_zero_divide', chosen, bytes(changed)))
    else:
        pair = FINITE_MAGNITUDES[14 if kind == 'mul64' else 16]
        chosen = next(c for c in cases if c[10] == 0x037F and c[12:14] == pair)
        altered = list(chosen); altered[10] = 0x027F
        wrong = numeric_specification(tuple(altered), kind)
        changed = bytearray(expected(chosen, kind))
        struct.pack_into('<Q', changed, STATE.size+chosen[2]-MEMORY_BASE, wrong['output_bits'])
        regressions.append(('ignored_two_stage_precision', chosen, bytes(changed)))
        for name, source_cw, wrong_cw in (('ignored_rounding',0x0B7F,0x037F),
                                        ('ignored_pc24',0x007F,0x037F)):
            chosen = next(c for c in cases if c[10] == source_cw and
                          numeric_specification(c,kind)['output_bits'] != numeric_specification(
                              (*c[:10],wrong_cw,*c[11:]),kind)['output_bits'])
            altered = (*chosen[:10],wrong_cw,*chosen[11:]); wrong = numeric_specification(altered,kind)
            changed = bytearray(expected(chosen,kind))
            struct.pack_into('<Q', changed, STATE.size+chosen[2]-MEMORY_BASE, wrong['output_bits'])
            regressions.append((name,chosen,bytes(changed)))
        chosen = next(c for c in cases if numeric_specification(c,kind)['status_word'] & 0x20)
        changed = bytearray(expected(chosen,kind)); changed[4146] ^= 0x20
        regressions.append(('dropped_sticky_precision',chosen,bytes(changed)))
        if kind == 'div64':
            chosen = next(c for c in cases if decode_binary64(c[12]) == 1 and decode_binary64(c[13]) == 3)
            changed = bytearray(expected(chosen,kind))
            struct.pack_into('<Q',changed,STATE.size+chosen[2]-MEMORY_BASE,encode_binary64(Fraction(3)))
            regressions.append(('reversed_division',chosen,bytes(changed)))
    # Mutate only observed C1, keeping output bits and every other field exact.
    for cw in CW_CASES:
        chosen = next(c for c in cases if c[10] == cw and
                      numeric_specification(c,kind)['store_c1'] == 0)
        changed = bytearray(expected(chosen,kind)); changed[4147] ^= 2
        regressions.append(('spurious_c1_mode_'+hex(cw),chosen,bytes(changed)))
    if not kind.endswith('-special'):
        predicates = [
            ('lost_final_store_c1', lambda c,s: bool(s['store_c1'])),
            ('sticky_arithmetic_pe_as_store_c1', lambda c,s: s['stage_inexact'] == [True,False]),
            ('negative_round_down_magnitude', lambda c,s: c[12] & SIGN and s['rounding']==1 and s['stage_inexact'][1]),
            ('negative_round_up_magnitude', lambda c,s: c[12] & SIGN and s['rounding']==2 and s['stage_inexact'][1]),
            ('used_pre_pc_arithmetic_for_c1', lambda c,s:
             int(abs(Fraction(*s['rounded_store'])) > abs(Fraction(*s['exact_arithmetic']))) != s['store_c1']),
            ('nearest_halfway_c1', lambda c,s: s['rounding']==0 and s['stage_inexact'][1] and
             (abs(Fraction(*s['rounded_arithmetic'])) / power_two(
                 floor_log_two(abs(Fraction(*s['rounded_arithmetic'])))-52)).denominator==2),
        ]
        for name,predicate in predicates:
            chosen = next(c for c in cases if predicate(c,numeric_specification(c,kind)))
            changed = bytearray(expected(chosen,kind)); changed[4147] ^= 2
            regressions.append((name,chosen,bytes(changed)))
    else:
        for result_class in ('zero','infinity','quiet_nan'):
            chosen = next(c for c in cases if numeric_specification(c,kind)['output_class']==result_class)
            changed = bytearray(expected(chosen,kind)); changed[4147] ^= 2
            regressions.append(('special_c1_'+result_class,chosen,bytes(changed)))
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
               ('unreviewed_subnormal', 12, 1, 'exact input vectors'),
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
                ('unreviewed_maximum_finite',12,0x7fefffffffffffff,'exact input vectors')]
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


def validate_initial_failure(path: Path, sha256: str) -> dict:
    """Reparse all pre-repair measurements and admit their immutable archive."""
    require(path.is_absolute() and path.resolve() ==
            (ROOT / 'reports/x87-arithmetic/baseline-failure/report.json').resolve(),
            'Arithmetic initial failure must use the preserved new-experiment archive')
    require(digest(path.read_bytes()) == sha256 == INITIAL_FAILURE_SHA256,
            'Initial arithmetic failure provenance identity differs')
    record = json.loads(path.read_bytes())
    manifest_path = path.with_name('manifest.json')
    require(digest(manifest_path.read_bytes()) == record.get('manifest_sha256') == INITIAL_MANIFEST_SHA256,
            'Initial arithmetic source/artifact manifest differs')
    manifest = json.loads(manifest_path.read_bytes())
    files, bindings = manifest.get('files'), manifest.get('original_bindings')
    require(manifest.get('schema_version') == 1 and manifest.get('status') == 'initial_native_baseline_snapshot' and
            isinstance(files,dict) and len(files) == manifest.get('file_count') == 151 and
            isinstance(bindings,list) and len(bindings) == len(files), 'Initial archive omitted source/artifact identities')
    for name, expected_hash in files.items():
        artifact = (path.parent / name).resolve()
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and
                Path(name).parts[0] == 'snapshot' and artifact.is_relative_to(path.parent.resolve()) and
                digest(artifact.read_bytes()) == expected_hash, 'Initial archive changed: '+name)
    require({b.get('snapshot_path') for b in bindings} == set(files), 'Initial archive origin mapping differs')
    for binding in bindings:
        original = Path(binding.get('original_path',''))
        require(original.is_absolute() and original.resolve().is_relative_to(ROOT.resolve()) and
                binding.get('snapshot_path') == 'snapshot/' + original.relative_to(ROOT).as_posix() and
                binding.get('sha256') == files[binding['snapshot_path']], 'Invalid initial archive origin identity')
    require(record.get('schema_version') == 1 and
            record.get('status') == 'reproduced_missing_right_snan_invalid_flag' and
            record.get('original_cases') == 3264 and record.get('original_mismatches') == 0 and
            record.get('native_comparisons') == 6528 and record.get('native_mismatches') == 96 and
            record.get('only_defined_difference') == 'IE missing for right-hand sNaN' and
            record.get('all_other_full_cpu_page_cw_tags_result_observations_match') is True and
            record.get('original_sources_binaries_reports_edited') is False,
            'Initial arithmetic failure scope/counts differ')
    experiments = record.get('experiments',[])
    require(len(experiments) == 8 and {(r.get('kind'),r.get('optimization')) for r in experiments} ==
            {(k,l) for k in FIXTURES for l in ('O0','O2')}, 'Initial archive omitted a native profile')
    observations = []
    for kind in FIXTURES:
        folder = path.parent / 'snapshot/reports/x87-arithmetic/reference-check' / kind
        code, corpus_bytes, original_bytes = ((folder / n).read_bytes() for n in
                                              ('fixture.bin','corpus.bin','reference.bin'))
        require(code == FIXTURES[kind], 'Initial authored fixture differs')
        cases = parse_corpus(corpus_bytes,kind)
        originals = parse_results(original_bytes,len(cases),32)
        wanted = [expected(c,kind) for c in cases]
        require(all(difference(a,b,sw_mask=HISTORICAL_SW_MASK) is None for a,b in zip(originals,wanted,strict=True)),
                'Initial original records violate the exact oracle')
        initial_layout = json.loads((path.parent / 'snapshot/reports/x87-arithmetic' / kind / 'layout.json').read_bytes())
        require(initial_layout.get('status_lowerings') == {} and initial_layout.get('bridge_lowerings') == {} and
                initial_layout.get('guest_ir_sha256') == REVIEWED_GUEST[kind],
                'Archived initial lowering is not the admitted pre-repair profile')
        for level in ('O0','O2'):
            saved = next(r for r in experiments if r['kind'] == kind and r['optimization'] == level)
            result_path = folder / ('baseline-native-'+level+'.bin')
            result_bytes = result_path.read_bytes()
            worker_path = path.parent / ('snapshot/build/x87-arithmetic-'+kind+'-'+level+'/mw34_x87_native.exe')
            require(digest(worker_path.read_bytes()) == saved.get('worker_sha256') and
                    digest(result_bytes) == saved.get('result_sha256') and
                    digest(corpus_bytes) == saved.get('corpus_sha256') and
                    digest(original_bytes) == saved.get('reference_sha256') and
                    digest(code) == saved.get('fixture_sha256'), 'Initial native measurement identities differ')
            native = parse_results(result_bytes,len(cases),64)
            failures, histogram = [], {}
            for index,(actual,hardware,target,case) in enumerate(zip(native,originals,wanted,cases,strict=True)):
                actual_sw = struct.unpack_from('<H',actual,4146)[0]
                key = hex(actual_sw & HISTORICAL_SW_MASK); histogram[key] = histogram.get(key,0)+1
                delta = difference(actual,target,sw_mask=HISTORICAL_SW_MASK)
                if delta is None:
                    require(difference(actual,hardware,sw_mask=HISTORICAL_SW_MASK) is None, 'Initial original/oracle observations differ')
                    continue
                repaired = bytearray(actual); repaired[4146] |= 1
                expected_sw = struct.unpack_from('<H',target,4146)[0]
                require(kind.endswith('-special') and classify(case[13]) == 'signaling_nan' and
                        set(delta) == {'sw_after'} and actual_sw & 1 == 0 and expected_sw & 1 and
                        difference(bytes(repaired),target,sw_mask=HISTORICAL_SW_MASK) is None and difference(bytes(repaired),hardware,sw_mask=HISTORICAL_SW_MASK) is None,
                        'Initial failure includes an unrelated observation: '+kind+'/'+level+'/'+str(index))
                failures.append({'case_index':index,'left_bits':f'0x{case[12]:016x}',
                                 'right_bits':f'0x{case[13]:016x}','cw':hex(case[10]),
                                 'pc':(case[10]>>8)&3,'rc':(case[10]>>10)&3,
                                 'result_bits':f'0x{struct.unpack_from("<Q",actual,STATE.size+case[2]-MEMORY_BASE)[0]:016x}',
                                 'actual_status':hex(actual_sw),'expected_defined_status':hex(expected_sw & HISTORICAL_SW_MASK),
                                 'record_offset':4146,'defined_difference':'0x0001',
                                 'all_other_cpu_page_cw_tags_observations_match':True})
            failures_expected = 24 if kind.endswith('-special') else 0
            require(len(failures) == failures_expected and saved.get('cases') == len(cases) and
                    saved.get('matches') == len(cases)-failures_expected and saved.get('mismatches') == failures and
                    saved.get('defined_status_histogram') == histogram,
                    'Initial native failure classification differs: '+kind+'/'+level)
            observations.append({'kind':kind,'optimization':level,'cases':len(cases),
                                 'matches':len(cases)-len(failures),'missing_right_snan_ie':len(failures),
                                 'unrelated_differences':0,'worker_sha256':digest(worker_path.read_bytes()),
                                 'output_sha256':digest(result_bytes)})
    return {'path':str(path),'sha256':sha256,'manifest_sha256':INITIAL_MANIFEST_SHA256,
            'archived_files':len(files),'original_oracle_matches':3264,'native_observations':6528,
            'missing_right_snan_ie':96,'unrelated_differences':0,'profiles':observations,
            'classification':'independently_reproduced_pre_repair_exception_capture_failure'}


def validate_c1_baseline(path: Path, sha256: str) -> dict:
    """Reparse the immutable previous arithmetic results under the stronger mask."""
    require(path.is_absolute() and path.resolve() ==
            (ROOT / 'reports/x87-store-c1/baseline-failure/report.json').resolve(),
            'C1 baseline must use the preserved store-C1 archive')
    require(digest(path.read_bytes()) == sha256 == C1_BASELINE_SHA256,
            'C1 baseline provenance identity differs')
    record = json.loads(path.read_bytes())
    manifest_path = path.with_name('manifest.json')
    require(digest(manifest_path.read_bytes()) == record.get('manifest_sha256') == C1_MANIFEST_SHA256,
            'C1 baseline archive manifest differs')
    manifest = json.loads(manifest_path.read_bytes())
    files,bindings = manifest.get('files'),manifest.get('original_bindings')
    require(manifest.get('schema_version') == 1 and
            manifest.get('status') == 'frozen_previous_arithmetic_store_c1_baseline' and
            manifest.get('prior_source_digest') == PRIOR_SOURCE_DIGEST and
            isinstance(files,dict) and len(files) == manifest.get('file_count') == 123 and
            isinstance(bindings,list) and len(bindings) == len(files),
            'C1 archive omitted prior source/artifact identities')
    for name,sha in files.items():
        artifact = (path.parent / name).resolve()
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and
                Path(name).parts[0] == 'snapshot' and artifact.is_relative_to(path.parent.resolve()) and
                digest(artifact.read_bytes()) == sha,'C1 archived file changed: '+name)
    require({b.get('snapshot_path') for b in bindings} == set(files),'C1 archive origin mapping differs')
    for binding in bindings:
        original = Path(binding.get('original_path',''))
        require(original.is_absolute() and original.resolve().is_relative_to(ROOT.resolve()) and
                binding.get('snapshot_path') == 'snapshot/' + original.relative_to(ROOT).as_posix() and
                binding.get('sha256') == files[binding['snapshot_path']], 'Invalid C1 archive origin identity')
    require(record.get('schema_version') == 1 and record.get('status') == 'reproduced_missing_final_store_c1' and
            record.get('observed_status_mask') == hex(SW_MASK) and record.get('original_cases') == 3264 and
            record.get('original_mismatches') == 0 and record.get('native_comparisons') == 6528 and
            record.get('native_mismatches') == 160 and record.get('prior_source_digest') == PRIOR_SOURCE_DIGEST and
            record.get('only_defined_difference') == 'Final FSTP C1 missing for finite significand increments' and
            record.get('all_other_full_cpu_page_cw_tags_result_observations_match') is True and
            record.get('old_files_modified') is False,'C1 baseline scope/counts differ')
    def archived(name: str, sha: str | None = None) -> Path:
        require(name in files,'C1 baseline refers to an unarchived file')
        if sha is not None: require(files[name] == sha,'C1 baseline measurement identity differs')
        return path.parent / name
    pins = json.loads(archived(record.get('prior_final_pins_snapshot_path',''),
                              record.get('prior_final_pins_sha256')).read_bytes())
    originals = record.get('originals',[]); experiments = record.get('experiments',[])
    require(len(originals) == 4 and {r.get('kind') for r in originals} == set(FIXTURES) and
            len(experiments) == 8 and {(r.get('kind'),r.get('optimization')) for r in experiments} ==
            {(k,l) for k in FIXTURES for l in ('O0','O2')},'C1 archive omitted a measured profile')
    observations = []
    for kind in FIXTURES:
        original_record = next(r for r in originals if r['kind'] == kind)
        corpus_path = archived(original_record.get('corpus_snapshot_path',''))
        original_path = archived(original_record.get('reference_snapshot_path',''),
                                 original_record.get('result_sha256'))
        fixture_path = archived(original_record.get('fixture_snapshot_path',''))
        reference_path = archived(original_record.get('worker_snapshot_path',''))
        cases = parse_corpus(corpus_path.read_bytes(),kind)
        require(fixture_path.read_bytes() == FIXTURES[kind],'C1 baseline authored fixture differs')
        hardware = parse_results(original_path.read_bytes(),len(cases),32)
        wanted = [expected(c,kind) for c in cases]
        require(all(difference(a,b) is None for a,b in zip(hardware,wanted,strict=True)) and
                original_record.get('cases') == len(cases) and original_record.get('mismatches') == 0,
                'C1 baseline originals violate full strong-mask oracle')
        hardware_histogram = {}
        for entry in hardware:
            key = hex(struct.unpack_from('<H',entry,4146)[0] & SW_MASK)
            hardware_histogram[key] = hardware_histogram.get(key,0)+1
        require(original_record.get('defined_status_histogram') == hardware_histogram,
                'C1 baseline original status histogram differs')
        for level in ('O0','O2'):
            saved = next(r for r in experiments if r['kind'] == kind and r['optimization'] == level)
            fields = (('worker','worker'),('corpus','corpus'),('reference','reference'),('result','result'),
                      ('fixture','fixture'),('prior_build','prior_build'),('prior_report','prior_report'))
            paths = {name:archived(saved.get(name+'_snapshot_path',''),saved.get(sha+'_sha256'))
                     for name,sha in fields}
            require(paths['corpus'] == corpus_path and paths['reference'] == original_path and
                    paths['fixture'] == fixture_path,'C1 baseline profiles used different original records')
            build = json.loads(paths['prior_build'].read_bytes())
            previous_report = json.loads(paths['prior_report'].read_bytes())
            require(build.get('source_digest') == pins[kind].get('source_digest') == PRIOR_SOURCE_DIGEST and
                    files[saved['prior_build_snapshot_path']] == pins[kind].get('build_sha256') and
                    files[saved['prior_report_snapshot_path']] == pins[kind].get('report_sha256') and
                    digest(reference_path.read_bytes()) == build.get('reference_sha256') and
                    saved.get('worker_sha256') == build.get('native_'+level+'_sha256') and
                    previous_report.get('bounded_contract_passed') is True and
                    previous_report.get('observed_status_word_mask') == hex(HISTORICAL_SW_MASK) and
                    previous_report.get('native_architectural_mismatches') == 0,
                    'C1 baseline prior passing provenance differs')
            native = parse_results(paths['result'].read_bytes(),len(cases),64)
            failures,histogram = [],{}
            for index,(actual,original,target,case) in enumerate(zip(native,hardware,wanted,cases,strict=True)):
                actual_sw = struct.unpack_from('<H',actual,4146)[0]
                expected_sw = struct.unpack_from('<H',target,4146)[0]
                key = hex(actual_sw & SW_MASK); histogram[key] = histogram.get(key,0)+1
                delta = difference(actual,target)
                if delta is None:
                    require(difference(actual,original) is None,'C1 baseline original/oracle disagreement')
                    continue
                classified = bytearray(actual); classified[4147] |= 2
                require(not kind.endswith('-special') and set(delta) == {'sw_after'} and
                        actual_sw & 0x200 == 0 and expected_sw & 0x200 and
                        difference(bytes(classified),target) is None and
                        difference(bytes(classified),original) is None,
                        'C1 baseline includes an unrelated difference: '+kind+'/'+level+'/'+str(index))
                failures.append({'case_index':index,'cw':hex(case[10]),'pc':(case[10]>>8)&3,
                                 'rc':(case[10]>>10)&3,'left_bits':f'0x{case[12]:016x}',
                                 'right_bits':f'0x{case[13]:016x}',
                                 'result_bits':f'0x{struct.unpack_from("<Q",actual,STATE.size+case[2]-MEMORY_BASE)[0]:016x}',
                                 'actual_status':hex(actual_sw),'expected_defined_status':hex(expected_sw & SW_MASK),
                                 'record_offset':4146,'defined_difference':'0x0200',
                                 'all_other_cpu_page_cw_tags_observations_match':True})
            count = {'mul64':32,'div64':48,'mul-special':0,'div-special':0}[kind]
            require(len(failures) == count and saved.get('cases') == len(cases) and
                    saved.get('matches') == len(cases)-count and saved.get('mismatches') == failures and
                    saved.get('defined_status_histogram') == histogram,
                    'C1 baseline measured failure classification differs: '+kind+'/'+level)
            observations.append({'kind':kind,'optimization':level,'cases':len(cases),
                                 'matches':len(cases)-count,'missing_final_store_c1':count,
                                 'unrelated_differences':0,'worker_sha256':saved['worker_sha256'],
                                 'output_sha256':saved['result_sha256']})
    return {'path':str(path),'sha256':sha256,'manifest_sha256':C1_MANIFEST_SHA256,
            'archived_files':len(files),'original_oracle_matches':3264,'native_observations':6528,
            'missing_final_store_c1':160,'unrelated_differences':0,'profiles':observations,
            'classification':'independently_reproduced_missing_final_store_c1'}


def validate_layout(layout: dict, build: dict, kind: str) -> None:
    require(layout.get('schema_version') == 1 and layout.get('profile') == 'x87_store_c1_'+kind and
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
    require(layout.get('bridge_lowerings') == {} and layout.get('status_lowerings') == FINAL_STORE_POLICY,
            'Missing reviewed promotion/final-store C1 boundary')


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
    require(build.get('contract_sha256') == digest((ROOT / 'docs/x87-store-c1-contract.md').read_bytes()),
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
    initial_failure = validate_initial_failure(Path(build.get('initial_failure_provenance_path','')),
                                               build.get('initial_failure_provenance_sha256',''))
    c1_baseline = validate_c1_baseline(Path(build.get('c1_baseline_path','')),
                                     build.get('c1_baseline_sha256',''))
    return {'metadata_path': str(metadata.resolve()), 'metadata_sha256': digest(metadata.read_bytes()),
            'build_provenance': build, **identity, 'fixture_path': str(fixture.resolve()),
            'fixture_sha256': digest(FIXTURES[kind]), 'adapter_layout': layout,
            'repair_provenance': provenance, 'adapter_controls': adapter, 'native_symbol_checks': symbol_reports,
            'initial_failure_proof':initial_failure,'c1_baseline_proof':c1_baseline}


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
            ('missing_c1_baseline', 'c1_baseline_path', '', 'C1 baseline must use')):
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
            ('wrong_c1_source_precision','status_lowerings',{**FINAL_STORE_POLICY,'final_store_c1':{
                **FINAL_STORE_POLICY['final_store_c1'],'input_type':'f64'}}),
            ('sticky_c1_assignment','status_lowerings',{**FINAL_STORE_POLICY,'final_store_c1':{
                **FINAL_STORE_POLICY['final_store_c1'],'assignment':'sticky_or'}}),
            ('signed_c1_comparison','status_lowerings',{**FINAL_STORE_POLICY,'final_store_c1':{
                **FINAL_STORE_POLICY['final_store_c1'],'comparison':'signed_value_greater_than'}}),
            ('nonfinite_c1_leak','status_lowerings',{**FINAL_STORE_POLICY,'final_store_c1':{
                **FINAL_STORE_POLICY['final_store_c1'],'nonfinite_cleared':False}})):
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
    report.update({'schema_version': 1, 'experiment': 'bounded_x87_final_store_c1', 'kind':kind,
              'outcome': 'failed', 'bounded_contract_passed': False, 'compatibility_gate': False,
              'scope': 'final FSTP C1 and full admitted finite normal mul/div or listed masked-special observations only',
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
                           'full_nan_payload_and_sign_observed': True},
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
    report['outcome'] = ('passed_bounded_final_store_c1_contract' if report['bounded_contract_passed'] else
                         'failed_bounded_final_store_c1_contract')
    report['not_proven'] = ['arbitrary x87 inputs or other instructions',
                           'live 80-bit register contents or nonempty entry stacks',
                           'C0/C2/C3/busy equivalence', 'subnormals and range overflow/underflow',
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
    report = {'schema_version': 1, 'experiment': 'bounded_x87_final_store_c1', 'kind':args.kind,
              'outcome': 'failed', 'bounded_contract_passed': False, 'compatibility_gate': False}
    destination = None
    try:
        private_root = (ROOT / 'reports/x87-store-c1' / args.kind).resolve()
        args.output_dir = args.output_dir.resolve()
        require(args.output_dir.is_relative_to(private_root) and args.output_dir != private_root,
                'Arithmetic output must be a private subdirectory of reports/x87-store-c1/' + args.kind)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        destination = args.output_dir / 'report.json'
        compare(args, report)
        require(report['bounded_contract_passed'], f'{args.kind} bounded final-store C1 gate failed: '
                f'{report["reference_architectural_mismatches"]} original / '
                f'{report["native_architectural_mismatches"]} native oracle mismatches, '
                f'{report["native_original_differences"]} native/original differences')
        print(f'{args.kind} bounded final-store C1 contract passed: {report["total_cases"]} original cases, '
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
