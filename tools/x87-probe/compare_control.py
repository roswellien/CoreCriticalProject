#!/usr/bin/env python3
"""Measure a bounded FNSTCW incompatibility; incompatible cases are not passes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_identity import identity

ROOT = Path(__file__).resolve().parents[2]
HEADER = struct.Struct('<8s4I')
REQUEST = struct.Struct('<13I')
STATE = struct.Struct('<11I')
CONTROL_WORDS = struct.Struct('<2H')
CODE_BASE = 0x10000000
SENTINEL = 0x10000100
MEMORY_BASE = 0x20001000
MEMORY_SIZE = 4096
RESULT_SIZE = STATE.size + MEMORY_SIZE + CONTROL_WORDS.size
FLAG_MASK = 0xCD5
FIXTURE = bytes.fromhex('D9 39 C3')
SEED = 0x3434
REMILL_COMMIT = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
SEMANTICS_SHA256 = '138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71'
CW_CASES = tuple(0x007F | (pc << 8) | (rc << 10)
                 for pc in (0, 2, 3) for rc in range(4))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_hashes(root: Path = ROOT) -> dict[str, str]:
    return identity(root)['source_files']


def source_digest(root: Path = ROOT) -> str:
    return identity(root)['source_digest']


def validate_case(case: tuple[int, ...]) -> None:
    require(len(case) == 13 and all(type(value) is int and 0 <= value <= 0xFFFFFFFF
                                   for value in case), 'Invalid request scalar fields')
    esp, target = case[4], case[1]
    require(case[9] == CODE_BASE and MEMORY_BASE + 16 <= esp <= MEMORY_BASE + MEMORY_SIZE - 16,
            'Invalid entry state or unsafe integer flags')
    require(case[8] & ~(FLAG_MASK | 0x202) == 0 and case[8] & 0x202 == 0x202,
            'Invalid entry state or unsafe integer flags')
    require(MEMORY_BASE <= target and target + 2 <= MEMORY_BASE + MEMORY_SIZE and
            not (target < esp + 12 and target + 2 > esp),
            'Invalid output word or overlap with return frame')
    require(case[10] in CW_CASES, 'Control word is outside reviewed masked PC/RC modes')


def corpus() -> list[tuple[int, ...]]:
    rng = random.Random(SEED)
    targets = (0, 1, 2, 4094, 15, 127, 511, 1023, 3073, 4093, 2046, 2047)
    stacks = (16, 17, 31, 511, 1023, 1537, 2048, 2051, 3001, 4079, 100, 200)
    cases = []
    for index, cw in enumerate(CW_CASES):
        registers = [rng.getrandbits(32) for _ in range(8)]
        registers[1] = MEMORY_BASE + targets[index]
        registers[4] = MEMORY_BASE + stacks[index]
        flags = 0x202 | (rng.getrandbits(12) & (FLAG_MASK & ~0x400)) | ((index & 1) << 10)
        case = (*registers, flags, CODE_BASE, cw, rng.getrandbits(32), rng.getrandbits(32))
        validate_case(case)
        cases.append(case)
    return cases


def encode_corpus(cases: list[tuple[int, ...]]) -> bytes:
    require(len(cases) == 12 and {case[10] for case in cases} == set(CW_CASES),
            'Corpus must contain all twelve unique reviewed PC/RC modes')
    for case in cases:
        validate_case(case)
    return HEADER.pack(b'MW34REQ1', 1, len(cases), REQUEST.size, 32) + b''.join(
        REQUEST.pack(*case) for case in cases)


def parse_corpus(data: bytes) -> list[tuple[int, ...]]:
    require(len(data) >= HEADER.size, 'Truncated request header')
    require(HEADER.unpack_from(data) == (b'MW34REQ1', 1, 12, REQUEST.size, 32),
            'Invalid request header')
    require(len(data) == HEADER.size + 12 * REQUEST.size, 'Truncated or trailing requests')
    cases = [REQUEST.unpack_from(data, HEADER.size + index * REQUEST.size) for index in range(12)]
    encode_corpus(cases)
    return cases


def initial_memory(case: tuple[int, ...]) -> bytes:
    validate_case(case)
    memory = bytearray((index * 37 + case[12]) & 255 for index in range(MEMORY_SIZE))
    struct.pack_into('<3I', memory, case[4] - MEMORY_BASE, SENTINEL, case[10], case[11])
    return bytes(memory)


def expected(case: tuple[int, ...], *, clamped: bool = False) -> bytes:
    registers = list(case[:8])
    registers[4] += 4
    memory = bytearray(initial_memory(case))
    stored = case[10] & ~0x0300 if clamped else case[10]
    struct.pack_into('<H', memory, case[1] - MEMORY_BASE, stored)
    return (STATE.pack(*registers, case[8] & FLAG_MASK, SENTINEL, 0) + memory +
            CONTROL_WORDS.pack(case[10], stored))


def parse_results(data: bytes, count: int, pointer_bits: int) -> list[bytes]:
    require(len(data) >= HEADER.size, 'Worker returned a truncated header')
    require(HEADER.unpack_from(data) == (b'MW34RES1', 1, count, RESULT_SIZE, pointer_bits),
            'Invalid worker result header')
    require(len(data) == HEADER.size + count * RESULT_SIZE,
            'Worker returned truncated or trailing result bytes')
    return [data[HEADER.size + index * RESULT_SIZE:HEADER.size + (index + 1) * RESULT_SIZE]
            for index in range(count)]


def difference(actual: bytes, wanted: bytes) -> dict | None:
    require(len(actual) == len(wanted) == RESULT_SIZE, 'Invalid comparator record extent')
    if actual == wanted:
        return None
    names = ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi', 'flags', 'eip', 'status')
    delta = {name: {'actual': hex(left), 'expected': hex(right)}
             for name, left, right in zip(names, STATE.unpack_from(actual), STATE.unpack_from(wanted))
             if left != right}
    memory_a = actual[STATE.size:STATE.size + MEMORY_SIZE]
    memory_b = wanted[STATE.size:STATE.size + MEMORY_SIZE]
    offsets = [index for index, (left, right) in enumerate(zip(memory_a, memory_b)) if left != right]
    if offsets:
        delta['memory'] = {'changed_byte_count': len(offsets), 'offsets': offsets,
                           'bytes': [{'offset': offset, 'actual': memory_a[offset],
                                      'expected': memory_b[offset]} for offset in offsets]}
    for name, left, right in zip(('cw_before', 'cw_after'), CONTROL_WORDS.unpack_from(actual, 4140),
                                CONTROL_WORDS.unpack_from(wanted, 4140)):
        if left != right:
            delta[name] = {'actual': hex(left), 'expected': hex(right)}
    return delta


def assess_result(actual: bytes, case: tuple[int, ...], *, native: bool) -> dict:
    wanted = expected(case)
    delta = difference(actual, wanted)
    if not native:
        require(delta is None, 'Original x86 violated architectural specification: ' + json.dumps(delta))
        classification = 'architectural_match'
    elif (case[10] & 0x0300) == 0:
        require(delta is None, 'Native single-precision case differs unexpectedly: ' + json.dumps(delta))
        classification = 'architectural_match'
    else:
        predicted = expected(case, clamped=True)
        require(actual == predicted, 'Native result is not the isolated predicted precision clamp: ' +
                json.dumps(difference(actual, predicted)))
        require(delta is not None, 'Required precision incompatibility was absent')
        classification = 'precision_control_incompatibility'
    before, after = CONTROL_WORDS.unpack_from(actual, STATE.size + MEMORY_SIZE)
    stored = struct.unpack_from('<H', actual, STATE.size + case[1] - MEMORY_BASE)[0]
    return {'classification': classification, 'input_cw': hex(case[10]),
            'precision_bits': (case[10] >> 8) & 3, 'rounding_bits': (case[10] >> 10) & 3,
            'cw_before': hex(before), 'cw_after': hex(after), 'stored_cw': hex(stored),
            'architectural_difference': delta,
            'non_cw_observations': 'all GPR, observed integer flags, return, status and full memory checked'}


def comparator_controls(cases: list[tuple[int, ...]]) -> list[dict]:
    case = cases[4]
    record = expected(case, clamped=True)
    mutations = [(name, index * 4, 1) for index, name in enumerate(
        ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'))]
    mutations += [('flag_' + name, 32 + bit // 8, 1 << (bit % 8))
                  for name, bit in (('cf', 0), ('pf', 2), ('af', 4), ('zf', 6),
                                    ('sf', 7), ('df', 10), ('of', 11))]
    mutations += [('eip', 36, 1), ('status', 40, 1), ('cw_before', 4140, 1), ('cw_after', 4142, 1)]
    mutations += [('memory_' + str(offset), STATE.size + offset, 1) for offset in (0, 2048, 4095)]
    controls = []
    for name, offset, mask in mutations:
        corrupted = bytearray(record)
        corrupted[offset] ^= mask
        require(difference(bytes(corrupted), record) is not None, f'Comparator missed {name}')
        try:
            assess_result(bytes(corrupted), case, native=True)
        except ValueError as error:
            controls.append({'name': name, 'outcome': 'rejected', 'reason': str(error)})
        else:
            raise ValueError(f'Precision classification accepted corrupt {name}')
    encoded = HEADER.pack(b'MW34RES1', 1, 12, RESULT_SIZE, 64) + record * 12
    for name, data, bits in (('truncated_header', encoded[:7], 64),
                             ('wrong_result_bits', encoded, 32),
                             ('truncated_result', encoded[:-1], 64),
                             ('trailing_result', encoded + b'X', 64),
                             ('wrong_result_magic', b'FAILRES1' + encoded[8:], 64)):
        try:
            parse_results(data, 12, bits)
        except ValueError as error:
            controls.append({'name': name, 'outcome': 'rejected', 'reason': str(error)})
        else:
            raise ValueError(f'Result parser accepted {name}')
    return controls


def worker_mutations(cases: list[tuple[int, ...]]) -> list[tuple[str, bytes, bytes, str]]:
    valid = encode_corpus(cases)
    mutations = [
        ('truncated_header', b'MW34', FIXTURE, 'Truncated control probe input'),
        ('truncated_request', valid[:-1], FIXTURE, 'Truncated control probe input'),
        ('trailing_input', valid + b'X', FIXTURE, 'trailing control probe input'),
        ('changed_code', valid, FIXTURE[:-1] + b'\xC2', 'identity'),
        ('truncated_code', valid, FIXTURE[:-1], 'identity')]
    for name, field, value in (('bad_header_version', 1, 2), ('bad_header_count', 2, 11),
                               ('bad_record_extent', 3, REQUEST.size + 4), ('bad_pointer_bits', 4, 64)):
        header = list(HEADER.unpack_from(valid))
        header[field] = value
        mutations.append((name, HEADER.pack(*header) + valid[HEADER.size:], FIXTURE,
                          'twelve v1 x86 requests'))
    changes = [('bad_entry', 9, CODE_BASE + 1, 'entry state'),
               ('unsafe_flags', 8, cases[0][8] | 0x100, 'integer flags'),
               ('missing_required_flags', 8, cases[0][8] & ~0x200, 'integer flags'),
               ('reserved_precision', 10, 0x017F, 'masked PC/RC modes'),
               ('unmasked_exception', 10, 0x007E, 'masked PC/RC modes'),
               ('invalid_control_extent', 10, 0x1007F, 'masked PC/RC modes'),
               ('duplicate_mode', 10, cases[1][10], 'Duplicate reviewed control word'),
               ('low_stack', 4, MEMORY_BASE + 15, 'entry state'),
               ('high_stack', 4, MEMORY_BASE + MEMORY_SIZE - 15, 'entry state'),
               ('low_output_extent', 1, MEMORY_BASE - 1, 'output word'),
               ('high_output_extent', 1, MEMORY_BASE + MEMORY_SIZE - 1, 'output word'),
               ('wrapped_output_extent', 1, 0xFFFFFFFF, 'output word'),
               ('frame_overlap', 1, cases[0][4] + 4, 'overlap with return frame'),
               ('frame_straddling', 1, cases[0][4] - 1, 'overlap with return frame')]
    for name, field, value, reason in changes:
        changed = list(cases[0])
        changed[field] = value
        encoded = valid[:HEADER.size] + REQUEST.pack(*changed) + valid[HEADER.size + REQUEST.size:]
        mutations.append((name, encoded, FIXTURE, reason))
    return mutations


def worker_controls(workers: list[tuple[str, Path]], fixture: Path,
                    cases: list[tuple[int, ...]], output: Path, timeout: int) -> list[dict]:
    controls = []
    folder = output / 'admission-controls'
    folder.mkdir(exist_ok=True)
    require(fixture.read_bytes() == FIXTURE, 'Authored fixture identity differs')
    for role, worker in workers:
        for name, data, code, intended_reason in worker_mutations(cases):
            prefix = folder / (role + '-' + name)
            input_file, result_file, code_file = (prefix.with_suffix(suffix)
                                                  for suffix in ('.input.bin', '.result.bin', '.code.bin'))
            input_file.write_bytes(data)
            code_file.write_bytes(code)
            if result_file.exists():
                result_file.unlink()
            command = [str(worker.resolve()), str(input_file.resolve()), str(result_file.resolve()),
                       str(code_file.resolve())]
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            require(result.returncode == 1 and intended_reason.lower() in result.stderr.lower(),
                    f'{role}/{name}: intended admission rejection missing: {result.returncode} {result.stderr}')
            require(not result_file.exists() or result_file.stat().st_size == 0,
                    f'{role}/{name}: rejection emitted result bytes before validation')
            controls.append({'role': role, 'name': name, 'outcome': 'rejected_before_execution',
                             'command': command, 'exit_code': result.returncode,
                             'stdout': result.stdout.strip(), 'reason': result.stderr.strip(),
                             'input_sha256': digest(data), 'fixture_sha256': digest(code),
                             'result_bytes': result_file.stat().st_size if result_file.exists() else 0})
    return controls


def validate_build(build: dict, metadata: Path, reference: Path, native: list[Path],
                   fixture: Path) -> dict:
    require(fixture.read_bytes() == FIXTURE, 'Authored fixture identity differs')
    require(build.get('schema_version') == 1 and build.get('llvm_version') == '21.1.8' and
            build.get('remill_commit') == REMILL_COMMIT and
            build.get('remill_semantics_sha256') == SEMANTICS_SHA256,
            'Build lacks pinned LLVM/Remill/semantics provenance')
    require(build.get('entry_va') == CODE_BASE and
            build.get('target_triples') == ['i686-pc-windows-msvc', 'x86_64-pc-windows-msvc'] and
            build.get('optimization_levels') == ['llc -O0', 'opt default<O2>; llc -O2'],
            'Build entry, architecture or optimization recipe differs')
    require(build.get('fixture_sha256') == digest(FIXTURE), 'Build fixture identity differs')
    require(build.get('source_digest') == source_digest(), 'Probe sources changed after build recording')
    require(build.get('source_files') == source_hashes(), 'Build source-file identities differ')
    require(build.get('reference_sha256') == digest(reference.read_bytes()),
            'Reference worker differs from build provenance')
    require(len(native) == 2, 'Probe requires native O0 and O2 workers in that order')
    for level, worker in zip(('O0', 'O2'), native, strict=True):
        require(build.get('native_' + level + '_sha256') == digest(worker.read_bytes()),
                level + ' worker differs from build provenance')
    artifacts = build.get('artifacts')
    require(isinstance(artifacts, dict) and len(artifacts) >= 4,
            'Build must identify generated input, IR/layout and objects')
    for name, expected_hash in artifacts.items():
        require(type(name) is str and Path(name).name == name and
                type(expected_hash) is str and len(expected_hash) == 64,
                'Invalid build artifact identity/path')
        require(digest((metadata.parent / name).read_bytes()) == expected_hash,
                'Generated build artifact changed: ' + name)
    require({'control.bin', 'control-guest.ll', 'control-host.ll', 'control-host-O2.ll',
             'control-O0.obj', 'control-O2.obj', 'layout.json'} <= set(artifacts),
            'Build omitted required generated artifacts')
    layout = json.loads((metadata.parent / 'layout.json').read_bytes())
    validate_layout(layout, build)
    return {'metadata_path': str(metadata.resolve()), 'metadata_sha256': digest(metadata.read_bytes()),
            'build_provenance': build, 'source_hashes': source_hashes(),
            'source_digest': source_digest(), 'fixture_path': str(fixture.resolve()),
            'fixture_sha256': digest(FIXTURE), 'adapter_layout': layout}


def validate_layout(layout: dict, build: dict) -> None:
    require(layout.get('schema_version') == 1 and layout.get('profile') == 'authored_fnstcw_ret' and
            layout.get('entry_va') == CODE_BASE and layout.get('authored_bytes') == FIXTURE.hex(),
            'Wrong authored control adapter profile/entry')
    require(layout.get('llvm_version') == [21, 1, 8] and
            layout.get('dll_sha256') == build.get('llvm_dll_sha256') and
            layout.get('guest_ir_sha256') == build['artifacts'].get('control-guest.ll') and
            layout.get('host_ir_sha256') == build['artifacts'].get('control-host.ll'),
            'Adapter tool or IR identity differs')
    require(layout.get('guest_pointer_bits') == 32 and layout.get('host_pointer_bits') == 64 and
            layout.get('state_bytes') == 3504 and layout.get('all_struct_layouts_equal') is True,
            'Missing checked State/host ABI boundary')
    structures = layout.get('struct_layouts', {})
    require(structures.get('struct.State', {}).get('size') == 3504 and
            structures.get('struct.State', {}).get('offsets') == [0] and
            structures.get('struct.X86State', {}).get('offsets', [])[11:12] == [2768],
            'Reviewed State CW storage differs')
    require(layout.get('bridge_calls') == {'__remill_fpu_get_rounding': 1,
                                         '__remill_write_memory_16': 1,
                                         '__remill_read_memory_32': 1,
                                         '__remill_function_return': 1} and
            layout.get('semantic_repairs') == [] and layout.get('undefined_helpers') == [],
            'Adapter changed semantics or admitted other bridges/undefined helpers')


def run_worker(worker: Path, corpus_file: Path, output: Path, fixture: Path, timeout: int) -> dict:
    if output.exists():
        output.unlink()
    command = [str(worker.resolve()), str(corpus_file.resolve()), str(output.resolve()), str(fixture.resolve())]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, f'Worker failed ({result.returncode}): {result.stdout}\n{result.stderr}')
    return {'command': command, 'exit_code': result.returncode, 'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(), 'worker_sha256': digest(worker.read_bytes()),
            'output_path': str(output.resolve()), 'output_sha256': digest(output.read_bytes())}


def compare(args, report: dict | None = None) -> dict:
    build = json.loads(args.metadata.read_bytes())
    admission = validate_build(build, args.metadata, args.reference, args.native, args.fixture)
    cases = corpus()
    encoded = encode_corpus(cases)
    require(parse_corpus(encoded) == cases, 'Independent corpus parse differs')
    corpus_file = args.output_dir / 'corpus.bin'
    corpus_file.write_bytes(encoded)
    if report is None:
        report = {}
    report.update({'schema_version': 1, 'experiment': 'authored_fnstcw_control_word', 'outcome': 'failed',
              'compatibility_gate': False, 'scope': 'control-word store/preservation only; no x87 arithmetic',
              'seed': SEED, 'total_cases': 12, 'request_record_bytes': REQUEST.size,
              'result_record_bytes': RESULT_SIZE, 'corpus_path': str(corpus_file.resolve()),
              'corpus_sha256': digest(encoded), 'input_control_words': [hex(value) for value in CW_CASES],
              'coverage': {'precision_controls': [0, 2, 3], 'rounding_controls': [0, 1, 2, 3],
                           'masked_exception_modes_only': True,
                           'df_set_cases': sum(bool(case[8] & 0x400) for case in cases),
                           'unaligned_word_cases': sum(bool(case[1] & 1) for case in cases),
                           'unaligned_stack_cases': sum(bool(case[4] & 3) for case in cases),
                           'destination_offsets': [case[1] - MEMORY_BASE for case in cases],
                           'stack_offsets': [case[4] - MEMORY_BASE for case in cases]},
              'python_version': sys.version.split()[0], **admission, 'native_runs': []})
    workers = [('reference', args.reference), ('O0', args.native[0]), ('O2', args.native[1])]
    report['comparator_negative_controls'] = comparator_controls(cases)
    report['worker_admission_negative_controls'] = worker_controls(
        workers, args.fixture, cases, args.output_dir, min(args.timeout, 10))
    reference_file = args.output_dir / 'reference.bin'
    report['reference_run'] = run_worker(args.reference, corpus_file, reference_file, args.fixture, args.timeout)
    original = parse_results(reference_file.read_bytes(), 12, 32)
    report['reference_cases'] = [dict(case_index=index, **assess_result(record, case, native=False))
                                 for index, (record, case) in enumerate(zip(original, cases, strict=True))]
    report['reference_architectural_matches'] = 12
    for level, worker in workers[1:]:
        output = args.output_dir / ('native-' + level + '.bin')
        measured = run_worker(worker, corpus_file, output, args.fixture, args.timeout)
        records = parse_results(output.read_bytes(), 12, 64)
        observations = [dict(case_index=index, **assess_result(record, case, native=True))
                        for index, (record, case) in enumerate(zip(records, cases, strict=True))]
        matches = sum(case['classification'] == 'architectural_match' for case in observations)
        incompatibilities = sum(case['classification'] == 'precision_control_incompatibility'
                                for case in observations)
        require((matches, incompatibilities) == (4, 8), 'Unexpected incompatibility counts')
        report['native_runs'].append({'optimization': level, **measured, 'cases': observations,
                                     'architectural_matches': matches, 'architectural_mismatches': incompatibilities,
                                     'precision_control_incompatibilities': incompatibilities,
                                     'unexpected_differences': 0})
    report['controls_total'] = (len(report['comparator_negative_controls']) +
                                len(report['worker_admission_negative_controls']))
    report['native_comparisons'] = 24
    report['native_architectural_matches'] = 8
    report['native_architectural_mismatches'] = 16
    report['unexpected_differences'] = 0
    report['outcome'] = 'reproduced_x87_control_incompatibility'
    report['not_proven'] = ['x87 arithmetic/precision fidelity', 'SW/TOP/tags/ST register equivalence',
                            'host rounding arithmetic and exception delivery', 'game floating-point behavior']
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--native', type=Path, action='append', required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=60)
    args = parser.parse_args()
    if len(args.native) != 2 or not 1 <= args.timeout <= 60:
        parser.error('Require O0/O2 workers and timeout 1–60 seconds')
    report = {'schema_version': 1, 'experiment': 'authored_fnstcw_control_word',
              'outcome': 'failed', 'compatibility_gate': False}
    destination = None
    try:
        private_root = (ROOT / 'reports').resolve()
        args.output_dir = args.output_dir.resolve()
        require(args.output_dir.is_relative_to(private_root) and args.output_dir != private_root,
                'Probe output must be a private subdirectory of reports')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        destination = args.output_dir / 'report.json'
        report = compare(args, report)
        print('FNSTCW incompatibility reproduced: 12 original matches; each native O0/O2 '
              'has 4 matches, 8 precision-control mismatches; compatibility gate remains open')
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
