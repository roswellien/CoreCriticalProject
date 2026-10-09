#!/usr/bin/env python3
"""Execute original x86 and compiled lifted x64 workers on the same authored corpus.

The expected-result specification validates the reference measurement first.
It is never presented as the generated/lifted implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
from fixture_catalog import FIXTURES

HEADER = struct.Struct('<8s4I')
REQUEST = struct.Struct('<13I')
STATE = struct.Struct('<11I')
CODE_BASE = 0x10000000
SENTINEL = CODE_BASE + 0x100
MEMORY_BASE = 0x20001000
MEMORY_SIZE = 4096
RESULT_SIZE = STATE.size + MEMORY_SIZE
FLAG_MASK = 0xCD5
FIXTURE = FIXTURES['add']


class WorkerStartError(ValueError):
    def __init__(self, command: list[str], error: OSError):
        super().__init__(f'Worker could not start: {command[0]}: {error}')
        self.command = command
        self.winerror = getattr(error, 'winerror', None)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def corpus(seed: int, random_count: int, kind: str = 'add') -> list[tuple[int, ...]]:
    rng = random.Random(seed)
    edges = (0, 1, 15, 16, 127, 128, 255, 256, 0x7fffffff, 0x80000000,
             0xfffffffe, 0xffffffff)
    pairs = [(a, b) for a in edges for b in edges]
    pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(random_count)]
    cases = []
    for index, (a, b) in enumerate(pairs):
        registers = [rng.getrandbits(32) for _ in range(8)]
        # Vary alignment too: x86's stack loads permit unaligned addresses.
        registers[4] = MEMORY_BASE + 0x800 + (index % 16)
        flags = 0x202 | (rng.getrandbits(12) & FLAG_MASK)
        if kind == 'memory':
            # Exercise page boundaries and all 32-bit alignments, away from the
            # return frame. EDX is the independently specified first input word.
            offsets = (0, 1, 2, 3, 16, 17, 31, 32, 511, 512, 1023, 1024,
                       3072, 3073, 4081, 4082, 4083, 4084)
            registers[2] = a
            a = MEMORY_BASE + offsets[index % len(offsets)]
        cases.append((*registers, flags, CODE_BASE, a, b, rng.getrandbits(32)))
    return cases


def signed(value: int) -> int:
    return value if value < 0x80000000 else value - 0x100000000


def expected(case: tuple[int, ...], kind: str = 'add') -> bytes:
    registers = list(case[:8])
    entry_flags, _, a, b, memory_seed = case[8:]
    left = case[2] if kind == 'memory' else ((a << 5) & 0xffffffff if kind == 'shift' else a)
    subtraction = kind in ('branch', 'shift')
    result = ((left - b) if subtraction else (left + b)) & 0xffffffff
    flags = entry_flags & 0x400
    flags |= int(left < b if subtraction else left + b > 0xffffffff)
    flags |= int((result & 255).bit_count() % 2 == 0) << 2
    flags |= int(bool((left ^ b ^ result) & 16)) << 4
    flags |= int(result == 0) << 6
    flags |= int(bool(result & 0x80000000)) << 7
    overflow = ((left ^ b) & (left ^ result) if subtraction
                else ~(left ^ b) & (left ^ result))
    flags |= int(bool(overflow & 0x80000000)) << 11
    memory = bytearray((i * 37 + memory_seed) & 255 for i in range(MEMORY_SIZE))
    struct.pack_into('<3I', memory, registers[4] - MEMORY_BASE, SENTINEL, a, b)
    if kind == 'branch':
        below = signed(a) < signed(b)
        registers[0] = b if below else a
        mask, marker = (0xffffff00, 0x11) if below else (0xffff0000, 0x2233)
        registers[1] = (registers[1] & mask) | marker
    elif kind == 'memory':
        offset = a - MEMORY_BASE
        struct.pack_into('<2I', memory, offset, case[2], case[6])
        struct.pack_into('<I', memory, offset, result)
        struct.pack_into('<I', memory, offset + 8, case[6])
        registers[0] = registers[1] = result
        registers[2] = case[6]
    else:
        registers[0] = result
    registers[4] += 12 if kind == 'memory' else 4
    return STATE.pack(*registers, flags, SENTINEL, 0) + memory


def parse_results(data: bytes, count: int, pointer_bits: int) -> list[bytes]:
    if len(data) < HEADER.size:
        raise ValueError('Worker returned a truncated header')
    header = HEADER.unpack_from(data)
    if header != (b'MW34RES1', 1, count, RESULT_SIZE, pointer_bits):
        raise ValueError(f'Invalid worker header: {header!r}')
    if len(data) != HEADER.size + count * RESULT_SIZE:
        raise ValueError('Worker returned truncated or trailing result bytes')
    return [data[offset:offset + RESULT_SIZE]
            for offset in range(HEADER.size, len(data), RESULT_SIZE)]


def difference(actual: bytes, wanted: bytes) -> dict | None:
    if actual == wanted:
        return None
    names = ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi',
             'flags', 'eip', 'status')
    left, right = STATE.unpack_from(actual), STATE.unpack_from(wanted)
    changed = {name: {'actual': hex(a), 'expected': hex(b)}
               for name, a, b in zip(names, left, right) if a != b}
    offsets = [i for i, (a, b) in enumerate(zip(actual[STATE.size:], wanted[STATE.size:]))
               if a != b]
    if offsets:
        changed['memory'] = {'changed_byte_count': len(offsets), 'first_offsets': offsets[:16]}
    return changed


def validate_records(records: list[bytes], cases: list[tuple[int, ...]], role: str,
                     kind: str = 'add') -> None:
    for index, (actual, case) in enumerate(zip(records, cases, strict=True)):
        delta = difference(actual, expected(case, kind))
        if delta:
            raise ValueError(json.dumps({'role': role, 'case': index, 'input': case,
                                         'difference': delta}))


def comparator_controls(record: bytes) -> list[str]:
    detected = []
    for name, offset in (('preserved_register', 12), ('carry_flag', 32),
                         ('memory_inside_mapping', STATE.size + 100)):
        corrupted = bytearray(record)
        corrupted[offset] ^= 1
        if difference(bytes(corrupted), record) is None:
            raise ValueError(f'Comparator missed {name} negative control')
        detected.append(name)
    return detected


def run_worker(worker: Path, corpus_file: Path, output: Path, fixture: Path,
               timeout: int) -> dict:
    command = [str(worker.resolve()), str(corpus_file.resolve()), str(output.resolve()),
               str(fixture.resolve())]
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except OSError as error:
        raise WorkerStartError(command, error) from error
    if run.returncode:
        raise ValueError(f'Worker failed ({run.returncode}): {run.stdout}\n{run.stderr}')
    return {'command': command, 'exit_code': run.returncode, 'stdout': run.stdout.strip(),
            'stderr': run.stderr.strip(), 'worker_sha256': digest(worker.read_bytes()),
            'output_sha256': digest(output.read_bytes())}


def source_digest(root: Path) -> str:
    source = []
    for folder in ('tools/lifting', 'tests/fixtures', 'runtime'):
        source.extend(path for path in (root / folder).rglob('*') if path.is_file()
                      and path.suffix in ('.py', '.hpp', '.cpp', '.asm', '.s', '.txt', '.ps1', '.json', '.patch'))
    state = hashlib.sha256()
    for path in sorted(source):
        state.update(path.relative_to(root).as_posix().encode() + b'\0')
        state.update(path.read_bytes())
    return state.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--lifted', type=Path, action='append', default=[])
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--fixture-name', choices=FIXTURES, default='add')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--random-cases', type=int, default=10000)
    parser.add_argument('--seed', type=lambda v: int(v, 0), default=0x3434)
    parser.add_argument('--timeout', type=int, default=60)
    parser.add_argument('--metadata', type=Path, help='Build provenance JSON to embed in report')
    args = parser.parse_args()
    if not 0 <= args.random_cases <= 99000 or not 1 <= args.timeout <= 60:
        parser.error('Case count or timeout out of bounds')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {'schema_version': 1, 'fixture': 'fixture_' + args.fixture_name, 'outcome': 'failed',
              'scope': 'reviewed authored leaf only; no MW3 execution proof',
              'lifted_runs': []}
    try:
        if args.metadata:
            report['build_provenance'] = json.loads(args.metadata.read_text(encoding='utf-8-sig'))
        data = args.fixture.read_bytes()
        if data != FIXTURES[args.fixture_name]:
            raise ValueError('Fixture bytes do not match reviewed authored fixture identity')
        cases = corpus(args.seed, args.random_cases, args.fixture_name)
        input_bytes = HEADER.pack(b'MW34REQ1', 1, len(cases), REQUEST.size, 32)
        input_bytes += b''.join(REQUEST.pack(*case) for case in cases)
        corpus_file = args.output_dir / 'corpus.bin'
        corpus_file.write_bytes(input_bytes)
        report.update({'fixture_sha256': digest(data), 'seed': args.seed,
                       'directed_cases': 144, 'random_cases': args.random_cases,
                       'total_cases': len(cases), 'corpus_sha256': digest(input_bytes),
                       'source_digest': source_digest(Path(__file__).resolve().parents[2]),
                       'python_version': sys.version.split()[0]})
        if args.fixture_name == 'branch':
            below = sum(signed(case[10]) < signed(case[11]) for case in cases)
            report['branch_coverage'] = {'signed_less': below, 'signed_greater_equal': len(cases) - below,
                                         'equal_operands': sum(case[10] == case[11] for case in cases),
                                         'evidence': 'both path-specific partial-register markers compared'}
            if not 0 < below < len(cases):
                raise ValueError('Corpus did not cover both branch outcomes')
        if args.fixture_name == 'memory':
            report['memory_coverage'] = {
                'unaligned_buffer_cases': sum(case[10] % 4 != 0 for case in cases),
                'buffer_offsets': sorted({case[10] - MEMORY_BASE for case in cases}),
                'permitted_write_ranges': ['[buffer,buffer+4)', '[buffer+8,buffer+12)'],
                'comparison_bytes_per_case': MEMORY_SIZE,
                'callee_stack_cleanup_bytes': 8,
            }
        if args.fixture_name == 'shift':
            report['undefined_flag_policy_coverage'] = {
                'shift_count': 5, 'final_flags': 'all six arithmetic flags from following subtraction',
                'shift_wrap_cases': sum(case[10] >= 0x08000000 for case in cases),
                'final_borrow_cases': sum(((case[10] << 5) & 0xffffffff) < case[11] for case in cases),
            }
        original_file = args.output_dir / 'reference.bin'
        report['reference_run'] = run_worker(args.reference, corpus_file, original_file,
                                               args.fixture, args.timeout)
        original = parse_results(original_file.read_bytes(), len(cases), 32)
        validate_records(original, cases, 'reference_self_test', args.fixture_name)
        report['reference_self_test'] = 'passed independent result/register/flag/stack/memory specification'
        report['comparator_negative_controls'] = comparator_controls(original[0])
        for index, worker in enumerate(args.lifted):
            result_file = args.output_dir / f'lifted-{index}.bin'
            run = run_worker(worker, corpus_file, result_file, args.fixture, args.timeout)
            native = parse_results(result_file.read_bytes(), len(cases), 64)
            validate_records(native, cases, 'lifted', args.fixture_name)
            for case_id, (left, right) in enumerate(zip(native, original, strict=True)):
                if left != right:
                    raise ValueError(f'Differential mismatch at case {case_id}')
            run['differential_result'] = 'zero mismatches'
            report['lifted_runs'].append(run)
        report['outcome'] = (('arithmetic_lift_passed' if args.fixture_name == 'add' else 'fixture_lift_passed')
                             if args.lifted else 'reference_only_passed')
        print(f"{report['outcome']}: {len(cases)} cases; {len(args.lifted)} x64 worker(s)")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
        if isinstance(error, WorkerStartError):
            report['worker_start_failure'] = {'command': error.command, 'winerror': error.winerror}
            if error.winerror == 4551:
                report['outcome'] = 'execution_blocked'
        print(str(error), file=sys.stderr)
        return 1
    finally:
        (args.output_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
