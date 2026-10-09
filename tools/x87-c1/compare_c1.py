#!/usr/bin/env python3
"""Measure finite FISTP32 C1 repair and unchanged spilling with exact rational oracles."""
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
SW_MASKS = {'spill64': 0x38FF, 'fistp32': 0x3AFF}
FIXTURES = {'spill64': bytes.fromhex('dd01dc4108dd5a08dd4208dc21dd1ac3'),
            'fistp32': bytes.fromhex('dd01db1ac3')}
COUNTS = {'spill64': 240, 'fistp32': 384}
INPUT_SIZES = {'spill64': 16, 'fistp32': 8}
OUTPUT_SIZES = {'spill64': 16, 'fistp32': 4}
SEED = 0x3434
CW_CASES = tuple(0x007F | (pc << 8) | (rc << 10) for pc in (0, 2, 3) for rc in range(4))
PRECISIONS = {0: 24, 2: 53, 3: 64}
BASE_BITS = (0x3FF0000000000000, 0xBFF0000000000000)
INCREMENT_BITS = tuple(((1023 - exponent) << 52) | (sign << 63)
                       for exponent in (30, 54, 24, 53, 64) for sign in (0, 1))
SPILL_VECTORS = tuple((base, increment) for base in BASE_BITS for increment in INCREMENT_BITS)
CONVERSION_FRACTIONS = tuple(Fraction(n, 4) * sign for n in (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 14, 49382) for sign in (1, -1))
CONVERSION_BOUNDARIES = (Fraction(-2147483648), Fraction(2147483647),
    Fraction(-8589934591, 4), Fraction(8589934587, 4),
    Fraction(-4294967295, 2), Fraction(4294967293, 2),
    Fraction(-8589934589, 4), Fraction(8589934585, 4))
BASELINE_SEMANTICS = '138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71'
REMILL_COMMIT = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
C1_BASELINE_SHA256 = '8eba6d35ec2e1053281610e264c0e27b37316b9e4de60faaf0798659b4956f74'
PREVIOUS_BUILD_SHA256 = 'a74e6b6589f3fe24c7d29a9a8fd3f08e8351f8f4e00296f6094aa82fc325bab9'
PREVIOUS_REPORT_SHA256 = '3a07d33e00baff243dacb348d135ddd1ff412c2917c076a0afa2f883457a2703'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_identity(root: Path = ROOT) -> dict:
    spec = importlib.util.spec_from_file_location(
        '_mw34_x87_c1_identity', Path(__file__).with_name('source_identity.py'))
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
    require(kind in FIXTURES, 'Unsupported authored expansion fixture')
    if kind == 'spill64':
        return SPILL_VECTORS
    return tuple((encode_binary64(value, negative_zero=index == 1), 0)
                 for index, value in enumerate(CONVERSION_FRACTIONS + CONVERSION_BOUNDARIES))


def round_integer(value: Fraction, rc: int) -> tuple[int, bool]:
    magnitude = abs(value)
    integer, remainder = divmod(magnitude.numerator, magnitude.denominator)
    if rc == 0:
        twice = remainder * 2
        up = twice > magnitude.denominator or (twice == magnitude.denominator and bool(integer & 1))
    elif rc == 1:
        up = value < 0 and remainder != 0
    elif rc == 2:
        up = value > 0 and remainder != 0
    else:
        up = False
    result = (integer + int(up)) * (-1 if value < 0 else 1)
    require(-(1 << 31) <= result < (1 << 31), 'Conversion corpus result outside signed32')
    return result, Fraction(result) != value


def numeric_specification(case: tuple[int, ...], kind: str) -> dict:
    cw = case[10]
    precision, rc = PRECISIONS[(cw >> 8) & 3], (cw >> 10) & 3
    base = decode_binary64(case[12])
    if kind == 'fistp32':
        integer, inexact = round_integer(base, rc)
        c1 = abs(Fraction(integer)) > abs(base)
        return {'precision': precision, 'rounding': rc, 'integer_result': integer,
                'output_bits': integer & 0xFFFFFFFF,
                'status_word': (0x20 if inexact else 0) | (0x200 if c1 else 0), 'c1': int(c1),
                'stage_inexact': [inexact], 'negative_zero': False}
    require(kind == 'spill64', 'Unknown expansion oracle kind')
    increment = decode_binary64(case[13])
    added = round_precision(base + increment, precision, rc)
    spilled = round_precision(added.value, 53, rc)
    exact_difference = spilled.value - base
    subtracted = round_precision(exact_difference, precision, rc,
                                 negative_zero=(exact_difference == 0 and rc == 1))
    stored = round_precision(subtracted.value, 53, rc, negative_zero=subtracted.negative_zero)
    inexact = added.inexact or spilled.inexact or subtracted.inexact or stored.inexact
    return {'precision': precision, 'rounding': rc,
            'output_bits': encode_binary64(stored.value, stored.negative_zero),
            'spill_bits': encode_binary64(spilled.value),
            'status_word': 0x20 if inexact else 0,
            'stage_inexact': [added.inexact, spilled.inexact, subtracted.inexact, stored.inexact],
            'negative_zero': stored.value == 0 and stored.negative_zero,
            'exact_intermediate_add': [added.value.numerator, added.value.denominator],
            'exact_reloaded_spill': [spilled.value.numerator, spilled.value.denominator],
            'exact_intermediate_sub': [subtracted.value.numerator, subtracted.value.denominator]}

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
    if kind == 'spill64':
        struct.pack_into('<2Q', memory, case[1] - MEMORY_BASE, case[12], case[13])
    else:
        struct.pack_into('<Q', memory, case[1] - MEMORY_BASE, case[12])
    return bytes(memory)

def expected(case: tuple[int, ...], kind: str) -> bytes:
    expansional = numeric_specification(case, kind)
    registers = list(case[:8]); registers[4] += 4
    memory = bytearray(initial_memory(case, kind))
    if kind == 'spill64':
        struct.pack_into('<2Q', memory, case[2] - MEMORY_BASE, expansional['output_bits'], expansional['spill_bits'])
    else:
        struct.pack_into('<I', memory, case[2] - MEMORY_BASE, expansional['output_bits'])
    return (STATE.pack(*registers, case[8] & FLAG_MASK, SENTINEL, 0) + memory +
            FPU.pack(case[10], case[10], 0, expansional['status_word'], 0, 0, 0))

def parse_results(data: bytes, count: int, pointer_bits: int) -> list[bytes]:
    require(len(data) >= HEADER.size, 'Worker returned a truncated header')
    require(HEADER.unpack_from(data) == (b'MW34RES1', 1, count, RESULT_SIZE, pointer_bits),
            'Invalid worker result header')
    require(len(data) == HEADER.size + count * RESULT_SIZE, 'Truncated or trailing result bytes')
    return [data[HEADER.size + i * RESULT_SIZE:HEADER.size + (i + 1) * RESULT_SIZE] for i in range(count)]


def difference(actual: bytes, wanted: bytes, kind: str) -> dict | None:
    require(kind in SW_MASKS, 'Unsupported comparator status boundary')
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
        mask = SW_MASKS[kind] if name.startswith('sw_') else 0xFFFF
        if left & mask != right & mask:
            delta[name] = {'actual': hex(left), 'expected': hex(right), 'observed_mask': hex(mask)}
    return delta or None


def assess_result(actual: bytes, case: tuple[int, ...], kind: str) -> dict:
    delta = difference(actual, expected(case, kind), kind)
    require(delta is None, 'Expansion result violates exact bounded specification: ' + json.dumps(delta))
    fpu = FPU.unpack_from(actual, 4140)
    specification = numeric_specification(case, kind)
    width = 16 if kind == 'spill64' else 8
    result = {'classification': 'architectural_match', 'entry_cw': hex(case[10]),
            'base_bits': f'0x{case[12]:016x}', 'increment_bits': f'0x{case[13]:016x}',
            'output_bits': f'0x{specification["output_bits"]:0{width}x}',
            'cw_before': hex(fpu[0]), 'cw_after': hex(fpu[1]),
            'raw_sw_before': hex(fpu[2]), 'raw_sw_after': hex(fpu[3]),
            'defined_sw_before': hex(fpu[2] & SW_MASKS[kind]), 'defined_sw_after': hex(fpu[3] & SW_MASKS[kind]),
            'tags_before': fpu[4], 'tags_after': fpu[5], 'reserved': fpu[6],
            'oracle': {**specification, 'output_bits': f'0x{specification["output_bits"]:0{width}x}'}}
    if kind == 'spill64': result['spill_bits'] = f'0x{specification["spill_bits"]:016x}'
    return result

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
                      for bit in range(16) if SW_MASKS[kind] & (1 << bit)]
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
    if kind == 'spill64':
        chosen = next(c for c in cases if numeric_specification(c, kind)['negative_zero'])
        changed = bytearray(expected(chosen, kind))
        changed[STATE.size + chosen[2] - MEMORY_BASE + 7] ^= 0x80
        regressions.append(('signed_zero_lost', chosen, bytes(changed)))
        chosen = next(c for c in cases if c[10] == 0x037F and c[12] == BASE_BITS[0]
                      and c[13] == (1023-54)<<52)
        changed = bytearray(expected(chosen, kind))
        struct.pack_into('<Q', changed, STATE.size+chosen[2]-MEMORY_BASE, chosen[13])
        regressions.append(('binary64_spill_bypassed', chosen, bytes(changed)))
        chosen = next(c for c in cases if c[10] == 0x0B7F and c[12] == BASE_BITS[0]
                      and c[13] == (1023-64)<<52)
        altered = list(chosen); altered[10] = 0x037F
        wrong = numeric_specification(tuple(altered), kind)
        changed = bytearray(expected(chosen, kind))
        struct.pack_into('<2Q', changed, STATE.size+chosen[2]-MEMORY_BASE, wrong['output_bits'],wrong['spill_bits'])
        struct.pack_into('<H', changed, 4146, wrong['status_word'])
        regressions.append(('spill_ignored_rounding', chosen, bytes(changed)))
    else:
        for name, value, cw, wrong_integer in (
                ('integer_ties_away_from_even', Fraction(5,2), 0x037F, 3),
                ('integer_forced_truncation', Fraction(-3,2), 0x077F, -1),
                ('integer_pc_clamped_input', Fraction(2147483647), 0x007F, 2147483648)):
            chosen = next(c for c in cases if c[10] == cw and decode_binary64(c[12]) == value)
            changed = bytearray(expected(chosen, kind))
            struct.pack_into('<I', changed, STATE.size+chosen[2]-MEMORY_BASE, wrong_integer & 0xFFFFFFFF)
            regressions.append((name, chosen, bytes(changed)))
        # Change only C1: the integer, PE, memory and every other observation
        # remain correct. Cover every PC/RC mode and explicit semantic traps.
        c1_cases = [('c1_pc_' + str((cw >> 8) & 3) + '_rc_' + str((cw >> 10) & 3),
                     next(c for c in cases if c[10] == cw and
                          decode_binary64(c[12]) == Fraction(-3, 4))) for cw in CW_CASES]
        c1_cases += [(name, next(c for c in cases if c[10] == cw and decode_binary64(c[12]) == value))
                     for name, value, cw in (
                         ('missing_increment_c1', Fraction(3, 4), 0x037F),
                         ('wrong_signed_direction_c1', Fraction(-3, 4), 0x037F),
                         ('sticky_c1_on_exact', Fraction(1), 0x037F),
                         ('sticky_c1_toward_zero', Fraction(-3, 4), 0x0F7F),
                         ('nearest_odd_tie_increment_c1', Fraction(3, 2), 0x037F),
                         ('nearest_even_tie_clear_c1', Fraction(5, 2), 0x037F),
                         ('nearest_negative_odd_tie_c1', Fraction(-3, 2), 0x037F),
                         ('nearest_negative_even_tie_c1', Fraction(-5, 2), 0x037F),
                         ('negative_endpoint_increment_c1', Fraction(-8589934591, 4), 0x077F),
                         ('positive_endpoint_increment_c1', Fraction(8589934587, 4), 0x0B7F),
                         ('negative_exact_endpoint_clear_c1', Fraction(-2147483648), 0x037F),
                         ('positive_exact_endpoint_clear_c1', Fraction(2147483647), 0x037F))]
        for name, chosen in c1_cases:
            changed = bytearray(expected(chosen, kind)); changed[4147] ^= 2
            require(set(difference(bytes(changed), expected(chosen, kind), kind)) == {'sw_after'},
                    'C1 regression changed unrelated observations: ' + name)
            regressions.append((name, chosen, bytes(changed)))
    for name, chosen, wrong in regressions:
        require(difference(wrong, expected(chosen,kind), kind) is not None,'Regression unchanged: '+name)
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
            if SW_MASKS[kind] & (1 << bit):
                continue
            changed = bytearray(record); changed[offset + bit // 8] ^= 1 << (bit % 8)
            require(difference(bytes(changed), record, kind) is None, 'SW excluded-bit mask differs')
            controls.append({'name': f'excluded_sw_{slot}_{bit}', 'outcome': 'excluded_by_contract',
                             'bit': bit, 'observation_mask': hex(SW_MASKS[kind])})
    return controls


def worker_mutations(cases: list[tuple[int, ...]], kind: str) -> list[tuple[str, bytes, bytes, str]]:
    valid, fixture, count = encode_corpus(cases,kind),FIXTURES[kind],COUNTS[kind]
    other = 'fistp32' if kind == 'spill64' else 'spill64'
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
               ('duplicate_vector',13 if kind=='spill64' else 12,
                cases[1][13 if kind=='spill64' else 12], 'Duplicate reviewed expansion'),
               ('invalid_base_infinity', 12, 0x7FF0000000000000, 'exact input vectors'),
               ('invalid_base_nan', 12, 0x7FF8000000000000, 'exact input vectors'),
               ('invalid_increment', 13, 0x7FF8000000000000, 'exact input vectors'),
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
    if kind=='fistp32':
        changes += [('conversion_nonzero_increment',13,0x3FF0000000000000,'exact input vectors'),
                    ('positive_integer_overflow',12,encode_binary64(Fraction(2147483648)),'exact input vectors'),
                    ('negative_integer_overflow',12,encode_binary64(Fraction(-2147483649)),'exact input vectors'),
                    ('denormal_input',12,1,'exact input vectors')]
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


def validate_baseline(path: Path, expected_sha256: str) -> dict:
    """Recheck the preserved failure; never run or rewrite a frozen worker."""
    require(path.is_absolute() and path.resolve() ==
            (ROOT / 'reports/x87-c1/baseline-failure/report.json').resolve(),
            'C1 baseline must be the preserved new-experiment failure record')
    data = path.read_bytes()
    require(digest(data) == expected_sha256 == C1_BASELINE_SHA256,
            'C1 baseline identity differs from the reviewed archived failure')
    baseline = json.loads(data)
    require(baseline.get('schema_version') == 1 and
            baseline.get('status') == 'reproduced_missing_conversion_c1' and
            baseline.get('observed_status_mask') == '0x3aff' and
            baseline.get('cases') == 384 and baseline.get('native_comparisons') == 768 and
            baseline.get('native_c1_only_mismatches') == 222 and
            baseline.get('original_architectural_matches') == 384 and
            baseline.get('old_sources_binaries_reports_edited') is False,
            'Archived C1 failure scope/counts differ')
    old_metadata = Path(baseline.get('baseline_metadata_path', ''))
    old_report = Path(baseline.get('baseline_comparison_report_path', ''))
    require(old_metadata.resolve() == (ROOT / 'reports/x87-expand/fistp32/build.json').resolve() and
            digest(old_metadata.read_bytes()) == baseline.get('baseline_metadata_sha256') == PREVIOUS_BUILD_SHA256,
            'Frozen prior conversion build identity differs')
    require(old_report.resolve() == (ROOT / 'reports/x87-expand/fistp32/comparison/report.json').resolve() and
            digest(old_report.read_bytes()) == baseline.get('baseline_comparison_report_sha256') == PREVIOUS_REPORT_SHA256,
            'Frozen prior conversion report identity differs')
    previous_build = json.loads(old_metadata.read_bytes())
    previous_report = json.loads(old_report.read_bytes())
    require(previous_build.get('kind') == previous_report.get('kind') == 'fistp32' and
            previous_report.get('bounded_contract_passed') is True and
            previous_report.get('observed_status_word_mask') == '0x38ff',
            'Prior conversion proof had a different observation boundary')
    sources = previous_build.get('source_files', {})
    require(sources and digest(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode()) ==
            previous_build.get('source_digest'), 'Frozen prior source map digest differs')
    for name, sha256 in sources.items():
        source = (ROOT / name).resolve()
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and
                source.is_relative_to(ROOT.resolve()) and digest(source.read_bytes()) == sha256,
                'Frozen prior source changed: ' + name)
    for name, sha256 in previous_build['artifacts'].items():
        artifact = (old_metadata.parent / name).resolve()
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and
                artifact.is_relative_to(old_metadata.parent.resolve()) and
                digest(artifact.read_bytes()) == sha256, 'Frozen prior artifact changed: ' + name)
    for name, sha256 in previous_build['tool_files'].items():
        require(Path(name).is_absolute() and digest(Path(name).read_bytes()) == sha256,
                'Frozen prior compile tool changed: ' + name)
    require(digest((path.parent / 'reference-worker.exe').read_bytes()) ==
            baseline.get('reference_worker_sha256'), 'Archived original reference worker differs')
    corpus_bytes = (path.parent / 'corpus.bin').read_bytes()
    fixture = (path.parent / 'fixture.bin').read_bytes()
    reference_bytes = (path.parent / 'reference.bin').read_bytes()
    require(digest(corpus_bytes) == baseline.get('corpus_sha256') == previous_report.get('corpus_sha256') and
            fixture == FIXTURES['fistp32'] and digest(fixture) == baseline.get('fixture_sha256') and
            digest(reference_bytes) == baseline.get('reference_sha256'),
            'Archived baseline fixture, corpus or original records changed')
    cases = parse_corpus(corpus_bytes, 'fistp32')
    original = parse_results(reference_bytes, len(cases), 32)
    for record, case in zip(original, cases, strict=True):
        assess_result(record, case, 'fistp32')
    original_run = baseline.get('original_run', {})
    command = original_run.get('command', [])
    require(original_run.get('exit_code') == 0 and len(command) == 4 and
            all(Path(p).is_absolute() for p in command) and
            digest(Path(command[1]).read_bytes()) == digest(corpus_bytes) and
            digest(Path(command[2]).read_bytes()) == digest(reference_bytes) and
            Path(command[3]).read_bytes() == fixture,
            'Archived original execution command/records differ')
    c1_per_pc = {str(pc): 0 for pc in PRECISIONS}
    c1_per_rc = {str(rc): 0 for rc in range(4)}
    signed_direction_errors = 0
    for case in cases:
        specification = numeric_specification(case, 'fistp32')
        c1 = specification['c1']
        c1_per_pc[str((case[10] >> 8) & 3)] += c1
        c1_per_rc[str((case[10] >> 10) & 3)] += c1
        signed_direction_errors += ((specification['integer_result'] > decode_binary64(case[12])) != bool(c1))
    require(c1_per_pc == {'0': 37, '2': 37, '3': 37} and
            c1_per_rc == {'0': 39, '1': 36, '2': 36, '3': 0} and signed_direction_errors == 144,
            'Independent baseline C1 oracle coverage differs')
    runs = baseline.get('native_runs', [])
    require(len(runs) == 2 and [r.get('optimization') for r in runs] == ['O0', 'O2'],
            'Archived native optimization levels differ')
    reviewed_runs = []
    for run in runs:
        level = run['optimization']
        output = path.parent / ('native-' + level + '.bin')
        output_bytes = output.read_bytes()
        native = parse_results(output_bytes, len(cases), 64)
        require(digest(output_bytes) == run.get('output_sha256'), 'Archived native result identity differs: ' + level)
        native_command = run.get('run', {}).get('command', [])
        require(len(native_command) == 4 and run['run'].get('exit_code') == 0 and
                Path(native_command[0]).resolve() ==
                (ROOT / ('build/x87-expand-fistp32-' + level + '/mw34_x87_native.exe')).resolve() and
                digest(Path(native_command[0]).read_bytes()) == run.get('worker_sha256') ==
                previous_build.get('native_' + level + '_sha256') and
                Path(native_command[1]).resolve() == (path.parent / 'corpus.bin').resolve() and
                Path(native_command[2]).resolve() == output.resolve() and
                Path(native_command[3]).resolve() == (path.parent / 'fixture.bin').resolve(),
                'Frozen prior native execution/worker identity differs: ' + level)
        failures = []
        for index, (record, hardware, case) in enumerate(zip(native, original, cases, strict=True)):
            wanted = expected(case, 'fistp32')
            delta = difference(record, wanted, 'fistp32')
            if delta is None:
                require(difference(record, hardware, 'fistp32') is None,
                        'Baseline oracle/original equality differs')
                continue
            actual_sw, expected_sw = struct.unpack_from('<H', record, 4146)[0], struct.unpack_from('<H', wanted, 4146)[0]
            repaired = bytearray(record); struct.pack_into('<H', repaired, 4146, actual_sw | 0x200)
            require(set(delta) == {'sw_after'} and actual_sw & 0x200 == 0 and expected_sw & 0x200 and
                    difference(bytes(repaired), wanted, 'fistp32') is None and
                    difference(bytes(repaired), hardware, 'fistp32') is None,
                    'Baseline has a difference beyond missing C1: ' + level + '/' + str(index))
            failures.append({'case_index': index, 'control_word': hex(case[10]),
                             'base_bits': f'0x{case[12]:016x}', 'actual_sw': hex(actual_sw),
                             'expected_sw': hex(expected_sw), 'difference': '0x0200',
                             'all_other_observations_match': True})
        require(len(failures) == run.get('architectural_mismatches') == 111 and
                len(cases) - len(failures) == run.get('architectural_matches') == 273 and
                failures == run.get('mismatches') and run.get('expected_c1_sets') == 111 and
                run.get('c1_sets_per_pc') == c1_per_pc and run.get('c1_sets_per_rc') == c1_per_rc and
                run.get('wrong_signed_direction_predictions') == signed_direction_errors,
                'Archived C1-only failure classification/counts differ: ' + level)
        reviewed_runs.append({'optimization': level, 'worker_sha256': run['worker_sha256'],
                              'output_sha256': digest(output_bytes), 'architectural_matches': 273,
                              'c1_only_mismatches': 111, 'unrelated_differences': 0})
    return {'path': str(path.resolve()), 'sha256': digest(data),
            'classification': 'independently_reproduced_missing_conversion_c1',
            'original_oracle_matches': 384, 'prior_native_observations': 768,
            'prior_native_c1_only_mismatches': 222, 'unrelated_differences': 0,
            'c1_sets_per_pc': c1_per_pc, 'c1_sets_per_rc': c1_per_rc,
            'wrong_signed_direction_predictions': signed_direction_errors,
            'prior_build_sha256': PREVIOUS_BUILD_SHA256, 'prior_report_sha256': PREVIOUS_REPORT_SHA256,
            'archived_original_worker_sha256': baseline['reference_worker_sha256'],
            'native_runs': reviewed_runs}


def validate_layout(layout: dict, build: dict, kind: str) -> None:
    reviewed_guest = {'spill64':'21e7331b94cf78dd30f4323f068da0e069611f657514936150a3f7409d3b2747',
                      'fistp32':'bc7e0f03047c9310470d75ce4baa048a1af07987619f986ff43cea3cc29e24a5'}
    require(layout.get('schema_version') == 1 and layout.get('profile') == 'x87_c1_'+kind and
            layout.get('entry_va') == CODE_BASE and layout.get('authored_bytes') == FIXTURES[kind].hex(),
            'Wrong authored expansion adapter profile/entry')
    require(layout.get('llvm_version') == [21, 1, 8] and
            layout.get('dll_sha256') == build.get('llvm_dll_sha256') and
            layout.get('guest_ir_sha256') == reviewed_guest[kind] and
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
    bridges = {'__remill_read_memory_f64':1,'__remill_write_memory_32':1,
               '__remill_read_memory_32':1,'__remill_function_return':1,
               '__remill_fpu_exception_clear':1,'__remill_fpu_exception_test':1,'__mw34_x87_nearbyint80':1}
    operations={'fptosi':1,'sitofp':1,'fpext':1}
    lowerings={'llvm.nearbyint.f80': {'bridge':'__mw34_x87_nearbyint80','calls':1,
                                   'storage_bytes':10,'host_exceptions_preserved':True}}
    undefined={}
    if kind=='spill64':
        bridges={'__remill_read_memory_f64':4,'__remill_write_memory_f64':2,
                 '__remill_read_memory_32':1,'__remill_function_return':1,
                 '__remill_fpu_exception_clear':4,'__remill_fpu_exception_test':4,'__remill_undefined_8':3}
        operations={'fadd':1,'fsub':1,'fptrunc':2,'fpext':4}
        lowerings={}
        undefined={'__remill_undefined_8':{'calls':3,'only_store_offsets':[2737,2741,2743],'observed':False}}
    require(layout.get('bridge_calls') == bridges, 'Adapter admitted other expansion bridges/call counts')
    require(layout.get('constrained_operations') == operations and layout.get('rounding') == 'dynamic'
            and layout.get('exceptions') == 'strict','Missing reviewed strict dynamic expansion operations')
    require(layout.get('undefined_helpers') == undefined,
            'Undefined expansion values escape excluded condition-code slots')
    require(layout.get('bridge_lowerings') == lowerings,
            'Unsafe or unreviewed 80-bit rounding bridge lowering')
    status_lowerings = {} if kind == 'spill64' else {'C1': {
        'state_byte_offset': 2739, 'operation': 'rounded_magnitude_greater_than_input',
        'writes': 1, 'valid_signed32_only': True}}
    require(layout.get('status_lowerings') == status_lowerings,
            'Missing or unreviewed conversion C1 lowering')


def validate_build(build: dict, metadata: Path, reference: Path, native: list[Path], fixture: Path, kind: str) -> dict:
    require(fixture.read_bytes() == FIXTURES[kind], 'Authored fixture identity differs')
    require(build.get('schema_version') == 1 and build.get('llvm_version') == '21.1.8' and
            build.get('remill_commit') == REMILL_COMMIT and
            build.get('llvm_dll_sha256') == '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb',
            'Build lacks pinned LLVM/Remill provenance')
    require(build.get('kind') == kind and build.get('entry_va') == CODE_BASE and
            build.get('scope') == 'authored valid signed32 C1 repair with explicit-spill regression only' and
            build.get('target_triples') == ['i686-pc-windows-msvc', 'x86_64-pc-windows-msvc'] and
            build.get('optimization_levels') == ['llc -O0', 'opt default<O2>; llc -O2'],
            'Build entry, architecture or optimization recipe differs')
    require(build.get('fixture_sha256') == digest(FIXTURES[kind]), 'Build fixture identity differs')
    require(build.get('contract_sha256') == digest((ROOT / 'docs/x87-c1-contract.md').read_bytes()),
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
    require(build.get('memory_bridge_checks_per_native') == 12 and
            build.get('fp_environment_checks_per_native') == 15 and
            build.get('adapter_mutation_controls') == 8 and
            adapter.get('accepted_original_profile') == layout['guest_ir_sha256'] and
            adapter.get('mutation_controls') == 8 and len(adapter.get('controls', [])) == 8 and
            all(c.get('status') == 'rejected' for c in adapter['controls']),
            'Expansion build omitted reviewed worker/adapter checks')
    require(build.get('object_symbol_rejection_checks_per_native') == 3 and
            build.get('rounding_bridge_checks_per_native') == (24 if kind == 'fistp32' else 0),
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
    baseline_proof = validate_baseline(Path(build.get('c1_baseline_path', '')),
                                       build.get('c1_baseline_sha256', ''))
    return {'metadata_path': str(metadata.resolve()), 'metadata_sha256': digest(metadata.read_bytes()),
            'build_provenance': build, **identity, 'fixture_path': str(fixture.resolve()),
            'fixture_sha256': digest(FIXTURES[kind]), 'adapter_layout': layout,
            'repair_provenance': provenance, 'adapter_controls': adapter, 'native_symbol_checks': symbol_reports,
            'prior_c1_failure_proof': baseline_proof}


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
            ('changed_c1_baseline', 'c1_baseline_sha256', '0' * 64, 'C1 baseline identity')):
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
            ('wrong_c1_slot', 'status_lowerings', {'C1': {'state_byte_offset':2737,
                'operation':'rounded_magnitude_greater_than_input','writes':1,'valid_signed32_only':True}}),
            ('signed_direction_c1', 'status_lowerings', {'C1': {'state_byte_offset':2739,
                'operation':'rounded_greater_than_input','writes':1,'valid_signed32_only':True}}),
            ('sticky_c1', 'status_lowerings', {'C1': {'state_byte_offset':2739,
                'operation':'rounded_magnitude_greater_than_input','writes':0,'valid_signed32_only':True}}),
            ('unbounded_c1', 'status_lowerings', {'C1': {'state_byte_offset':2739,
                'operation':'rounded_magnitude_greater_than_input','writes':1,'valid_signed32_only':False}})):
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
    require(args.baseline_report.resolve() == Path(build['c1_baseline_path']).resolve(),
            'CLI C1 baseline differs from build binding')
    cases = corpus(kind)
    count, encoded = len(cases), encode_corpus(cases, kind)
    require(parse_corpus(encoded,kind) == cases, 'Independent corpus parse differs')
    corpus_file = args.output_dir / 'corpus.bin'; corpus_file.write_bytes(encoded)
    if report is None: report = {}
    specifications = [numeric_specification(case,kind) for case in cases]
    report.update({'schema_version': 1, 'experiment': 'bounded_x87_conversion_c1_repair', 'kind':kind,
              'outcome': 'failed', 'bounded_contract_passed': False, 'compatibility_gate': False,
              'scope': 'exact authored valid signed32 C1 repair with explicit-spill regression only',
              'seed': SEED, 'total_cases': count, 'request_record_bytes': REQUEST.size,
              'result_record_bytes': RESULT_SIZE, 'corpus_path': str(corpus_file.resolve()),
              'corpus_sha256': digest(encoded), 'observed_integer_flag_mask': hex(FLAG_MASK),
              'observed_status_word_mask': hex(SW_MASKS[kind]), 'input_span_bytes':INPUT_SIZES[kind],
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
                           'unaligned_output_cases': sum(bool(c[2] & (7 if kind=='spill64' else 3)) for c in cases),
                           'unaligned_stack_cases': sum(bool(c[4] & 3) for c in cases),
                           'input_offsets': sorted({c[1] - MEMORY_BASE for c in cases}),
                           'output_offsets': sorted({c[2] - MEMORY_BASE for c in cases}),
                           'stack_offsets': sorted({c[4] - MEMORY_BASE for c in cases}),
                           'negative_zero_results': sum(s['negative_zero'] for s in specifications),
                           'zero_results': sum(s['output_bits'] & ((1<<63)-1)==0 for s in specifications),
                           'inexact_results': sum(bool(s['status_word'] & 0x20) for s in specifications),
                           'exact_results': sum(not (s['status_word'] & 0x20) for s in specifications),
                           'observed_c1': kind == 'fistp32',
                           'c1_set_results': sum(s.get('c1', 0) for s in specifications) if kind == 'fistp32' else None,
                           'c1_clear_results': sum(not s['c1'] for s in specifications) if kind == 'fistp32' else None},
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
    report['reference_cases'] = [dict(case_index=index, **assess_result(record, case,kind))
                                for index, (record, case) in enumerate(zip(original, cases, strict=True))]
    report['reference_architectural_matches'] = count
    for level, worker in workers[1:]:
        output = args.output_dir / ('native-' + level + '.bin')
        measured = run_worker(worker, corpus_file, output, args.fixture, args.timeout)
        records = parse_results(output.read_bytes(), count, 64)
        observations = []
        for index, (record, baseline, case) in enumerate(zip(records, original, cases, strict=True)):
            observations.append(dict(case_index=index, **assess_result(record, case,kind)))
            delta = difference(record, baseline, kind)
            require(delta is None, 'Native differs from original on defined observations: ' + json.dumps(delta))
        report['native_runs'].append({'optimization': level, **measured, 'cases': observations,
                                     'architectural_matches': count, 'architectural_mismatches': 0,
                                     'unexpected_differences': 0,
                                     'raw_status_word_difference_cases': sum(
                                         FPU.unpack_from(a, 4140)[2:4] != FPU.unpack_from(b, 4140)[2:4]
                                         for a, b in zip(records, original, strict=True))})
    report['controls_total'] = sum(len(report[key]) for key in ('comparator_negative_controls',
                                'metadata_negative_controls', 'worker_admission_negative_controls'))
    report['excluded_status_bit_controls_total'] = len(report['excluded_status_bit_controls'])
    report['native_comparisons'] = count * 2
    report['native_architectural_matches'] = count * 2
    report['native_architectural_mismatches'] = 0
    report['unexpected_differences'] = 0
    report['bounded_contract_passed'] = True
    report['outcome'] = 'passed_bounded_c1_contract'
    report['not_proven'] = ['arbitrary x87 inputs or other instructions',
                           'live 80-bit register contents or nonempty entry stacks',
                           'C0/C2/C3/busy equivalence; spill C1 equivalence', 'denormals, NaNs and infinities',
                           'invalid/out-of-range integer conversions', 'unmasked trap delivery',
                           'exceptional-exit FIP/FDP restoration', 'game native integration']
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=tuple(FIXTURES),required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--native', type=Path, action='append', required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--baseline-report', type=Path,
                        default=ROOT / 'reports/x87-c1/baseline-failure/report.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=60)
    args = parser.parse_args()
    if len(args.native) != 2 or not 1 <= args.timeout <= 60:
        parser.error('Require O0/O2 workers and timeout 1-60 seconds')
    report = {'schema_version': 1, 'experiment': 'bounded_x87_conversion_c1_repair', 'kind':args.kind,
              'outcome': 'failed', 'bounded_contract_passed': False, 'compatibility_gate': False}
    destination = None
    try:
        private_root = (ROOT / 'reports/x87-c1' / args.kind).resolve()
        args.output_dir = args.output_dir.resolve()
        require(args.output_dir.is_relative_to(private_root) and args.output_dir != private_root,
                'C1 output must be a private subdirectory of reports/x87-c1/' + args.kind)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        destination = args.output_dir / 'report.json'
        compare(args, report)
        print(f'{args.kind} bounded x87 C1 contract passed: {report["total_cases"]} original cases, '
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
