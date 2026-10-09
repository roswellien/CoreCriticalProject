"""Measure the actual whole MW3 function; never implements a worker body.

Large result streams are read one record at a time. Proprietary inputs and
generated translations remain in the ignored private report directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from corpus import (Case, ENTRY, SENTINEL, STACK, GLOBAL, PAGE, CWS, IMAGE_SHA,
                    CODE_SHA, HEADER, PREFIX, REQUEST_SIZE, RESULT_SIZE,
                    STATE_SIZE, ENTRY_FLAGS, EXIT_FLAGS, cases, expected,
                    initial_memory, full_tags)

ROOT = Path(__file__).resolve().parents[2]
CPU = struct.Struct('<10I')
OFFSETS = {'cpu_before': 0, 'cpu_after': 40, 'status': 80,
           'observation_mode': 84, 'host_restored': 88,
           'memory_before': 92, 'memory_after': 8284,
           'fx_before': 16476, 'fx_after': 16988,
           'env_before': 17500, 'env_after': 17528,
           'state_before': 17556, 'state_after': 21060}
GUEST_IR_SHA = '60cf4c91d2ed5ff9857768196f06ac0aff40178f6e27f8a80f5cafdda936d62c'
LLVM_SHA = '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'
FLAG_FIELDS = ((0, 1), (2, 3), (4, 5), (6, 7), (7, 9), (10, 11), (11, 13))
SW_FIELDS = ((8, 1), (9, 3), (10, 5), (14, 7), (5, 9), (4, 11),
             (3, 13), (2, 15), (1, 17), (0, 19), (6, 21))


def require(ok: bool, field: str) -> None:
    if not ok:
        raise ValueError(field)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def put_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from('<H', data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from('<I', data, offset)[0]


def check_cpu(actual: tuple[int, ...], goal: tuple[int, ...], mask: int, phase: str) -> None:
    for i, name in enumerate(('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi')):
        require(actual[i] == goal[i], phase + '.' + name)
    require((actual[8] ^ goal[8]) & mask == 0, phase + '.defined_flags')
    require(actual[9] == goal[9], phase + '.eip')


def fp_fields(fx: bytes) -> tuple:
    """Architecturally defined legacy fields; occupied values use TOP/FTW.

    The omitted bytes are capability, selectors/reserved bytes and padding.
    Empty raw80 storage is separately preserved within each worker.
    """
    cw, sw, ftw, fop = u16(fx, 0), u16(fx, 2), fx[4], u16(fx, 6)
    top = sw >> 11 & 7
    slots = tuple(fx[32 + i * 16:42 + i * 16] if ftw & (1 << ((top + i) & 7)) else None
                  for i in range(8))
    return (cw, sw, ftw, fop, u32(fx, 8), u32(fx, 16), u32(fx, 24),
            slots, fx[160:288])


def check_fx(actual: bytes, goal: bytes, phase: str, *, metadata: bool = True) -> None:
    names = ('cw', 'sw', 'physical_ftw', 'fop', 'fip', 'fdp', 'mxcsr', 'occupied_raw80', 'xmm0_7')
    for name, a, b in zip(names, fp_fields(actual), fp_fields(goal)):
        if not metadata and name in ('fop', 'fip', 'fdp'):
            continue
        require(a == b, phase + '.' + name)


def check_env(env: bytes, fx: bytes, phase: str, *, metadata: bytes | None = None) -> None:
    require(u16(env, 0) == u16(fx, 0), phase + '.cw')
    require(u16(env, 4) == u16(fx, 2), phase + '.sw')
    require(u16(env, 8) == full_tags(fx), phase + '.full_physical_tags')
    metadata = fx if metadata is None else metadata
    require(u32(env, 12) == u32(metadata, 8), phase + '.fip')
    require(u16(env, 18) & 0x7ff == u16(metadata, 6), phase + '.fop')
    require(u32(env, 20) == u32(metadata, 16), phase + '.fdp')


def state_cpu(state: bytes, layout: dict) -> tuple[int, ...]:
    structures = layout['struct_layouts']
    x = structures['struct.X86State']['offsets']
    g = structures['struct.GPR']['offsets']
    a = structures['struct.ArithFlags']['offsets']
    registers = tuple(u32(state, x[6] + g[i]) for i in (1, 5, 7, 3, 13, 15, 9, 11))
    flags = 0
    for bit, index in FLAG_FIELDS:
        value = state[x[2] + a[index]]
        require(value in (0, 1), 'state.arithmetic_flag_encoding')
        flags |= value << bit
    return (*registers, flags, u32(state, x[6] + g[33]))


def state_fx(state: bytes, layout: dict) -> bytes:
    """An independent projection from the recorded State, not the request."""
    structures = layout['struct_layouts']
    x = structures['struct.X86State']['offsets']
    s = structures['struct.FPUStatusFlags']['offsets']
    raw = structures['struct.anon.3']['offsets'][1]
    slot_size = structures['struct.anon.3']['size']
    vector_size = structures['union.VectorReg']['size']
    fx = bytearray(state[x[11]:x[11] + 512])
    sw = u16(fx, 2) & 0x3880
    for bit, index in SW_FIELDS:
        value = state[x[9] + s[index]]
        require(value in (0, 1), 'state.status_flag_encoding')
        sw |= value << bit
    struct.pack_into('<H', fx, 2, sw)
    for i in range(8):
        start = x[7] + i * slot_size + raw
        fx[32 + i * 16:42 + i * 16] = state[start:start + 10]
        start = x[1] + i * vector_size
        fx[160 + i * 16:176 + i * 16] = state[start:start + 16]
    return bytes(fx)


def protected_ranges(layout: dict) -> list[tuple[int, int]]:
    ranges = sorted((v['offset'], v['offset'] + v['bytes']) for v in layout['state_write_ranges'])
    out, last = [], 0
    for start, end in ranges:
        require(last <= start < end <= STATE_SIZE, 'layout.state_write_range_overlap')
        if last < start:
            out.append((last, start))
        last = end
    if last < STATE_SIZE:
        out.append((last, STATE_SIZE))
    return out


def validate_layout(layout: dict) -> None:
    require(layout['profile'] == 'm3-whole-function-558290', 'layout.profile')
    require(layout['guest_ir_sha256'] == GUEST_IR_SHA, 'layout.guest_ir')
    require(layout['dll_sha256'] == LLVM_SHA and layout['llvm_version'] == [21, 1, 8], 'layout.llvm')
    require(layout['state_bytes'] == STATE_SIZE and layout['guest_pointer_bits'] == 32 and
            layout['host_pointer_bits'] == 64 and layout['all_struct_layouts_equal'] is True,
            'layout.state_or_pointer_width')
    st = layout['struct_layouts']
    require(st['struct.State']['size'] == STATE_SIZE and
            st['struct.X86State']['offsets'] ==
            [0, 16, 2064, 2080, 2088, 2112, 2208, 2480, 2608, 2736, 2760, 2768, 3280, 3376],
            'layout.reviewed_state_offsets')
    expected_ranges = sorted([(2065, 1), (2067, 1), (2069, 1), (2071, 1), (2073, 1), (2077, 1),
                              (2216, 4), (2264, 4), (2312, 4), (2472, 4)])
    require(sorted((v['offset'], v['bytes']) for v in layout['state_write_ranges']) == expected_ranges,
            'layout.exact_integer_write_ranges')
    require(layout['call_counts'] == {'__remill_read_memory_32': 3, '__remill_write_memory_32': 5,
                                     '__remill_function_return': 1, 'llvm.ctpop.i8': 2,
                                     '__remill_flag_computation_carry': 1,
                                     '__remill_flag_computation_zero': 1,
                                     '__remill_flag_computation_sign': 1,
                                     '__remill_flag_computation_overflow': 1,
                                     '__remill_undefined_8': 1}, 'layout.exact_call_counts')
    require(layout['entry_va'] == ENTRY and layout['end_va'] == 0x5582bb and
            layout['source_length'] == 43 and layout['image_sha256'] == IMAGE_SHA and
            layout['code_sha256'] == CODE_SHA, 'layout.actual_function_binding')
    policy = layout['undefined_flag_policy']
    require(policy['policy'] == 'single-final-SAR-AF-arbitrary-zero' and
            policy['state_offset'] == 2069 and policy['width'] == 1 and
            policy['defined_exit_flags_mask'] == EXIT_FLAGS and
            policy['architectural_AF_compatibility_claim'] is False and
            policy['value_has_only_AF_store_use'] is True and policy['subsequent_AF_reads'] == 0,
            'layout.final_AF_policy')
    require(layout['indirect_host_calls'] == 0 and layout['pointer_integer_conversions'] == 0,
            'layout.unknown_native_target')
    protected_ranges(layout)


def validate_record(row: bytes, case: Case, mode: int, layout: dict,
                    reference: bytes | None = None) -> None:
    require(len(row) == RESULT_SIZE, 'result.record_size')
    require(u32(row, OFFSETS['status']) == 0, 'result.execution_status')
    require(u32(row, OFFSETS['observation_mode']) == mode, 'result.observation_provenance')
    require(u32(row, OFFSETS['host_restored']) == 1, 'result.host_environment_restoration')
    before, after = CPU.unpack_from(row), CPU.unpack_from(row, 40)
    goal_cpu, goal_memory = expected(case)
    check_cpu(before, case.cpu, ENTRY_FLAGS, 'entry_cpu')
    check_cpu(after, goal_cpu, EXIT_FLAGS, 'exit_cpu')
    require(row[92:8284] == initial_memory(case), 'memory.before_full_pages')
    require(row[8284:16476] == goal_memory, 'memory.after_full_pages')
    fx_before, fx_after = row[16476:16988], row[16988:17500]
    check_fx(fx_before, case.fx, 'entry_fp', metadata=bool(mode))
    if mode == 0:
        actual = (u16(fx_before, 6), u32(fx_before, 8), u32(fx_before, 16))
        seeded = (u16(case.fx, 6), u32(case.fx, 8), u32(case.fx, 16))
        require(actual in ((0, 0, 0), seeded), 'original.supported_FXSAVE_metadata_view')
    check_fx(fx_after, fx_before, 'preserved_fp')
    # Empty numerical values are not compared between modes. Actual captured
    # storage is nevertheless untouched by this integer-only operation.
    require(all(fx_before[32+i*16:42+i*16] == fx_after[32+i*16:42+i*16] for i in range(8)),
            'preserved_fp.all_captured_raw_storage')
    check_env(row[17500:17528], fx_before, 'entry_env', metadata=case.fx)
    check_env(row[17528:17556], fx_after, 'exit_env', metadata=case.fx)
    sb, sa = row[17556:21060], row[21060:24564]
    if mode == 0:
        require(sb == bytes(STATE_SIZE) and sa == bytes(STATE_SIZE), 'original.unobserved_state_must_be_zero')
    else:
        check_cpu(state_cpu(sb, layout), before, ENTRY_FLAGS, 'state.before_cpu_projection')
        check_cpu(state_cpu(sa, layout), after, ENTRY_FLAGS, 'state.after_cpu_projection')
        check_fx(state_fx(sb, layout), fx_before, 'state.before_fp_projection')
        check_fx(state_fx(sa, layout), fx_after, 'state.after_fp_projection')
        for start, end in protected_ranges(layout):
            require(sb[start:end] == sa[start:end], f'state.protected_bytes_{start}_{end}')
        if reference is not None:
            for phase, offset in (('before', 16476), ('after', 16988)):
                check_fx(row[offset:offset+512], reference[offset:offset+512], 'original_native_fp.' + phase, metadata=False)


def parse_result_header(stream, count: int, bits: int) -> None:
    require(HEADER.unpack(stream.read(HEADER.size)) == (b'MW34M3RS', 1, count, RESULT_SIZE, bits),
            'result.header')


def result_controls(samples: dict[int, bytes], requests: list[Case], layout: dict) -> list[dict]:
    """Discriminating observer mutations of genuine successful worker records."""
    controls = []
    index = next(i for i in samples if requests[i].fx[4] == 255)
    case = requests[index]
    good = samples[index]
    changes = [(f'entry_gpr{i}', i*4, 1) for i in range(8)]
    changes += [(f'exit_gpr{i}', 40+i*4, 1) for i in range(8)]
    changes += [('entry_eip', 36, 1), ('exit_eip', 76, 1), ('status', 80, 1),
                ('provenance', 84, 1), ('host_restored', 88, 1)]
    for phase, offset, mask in (('entry', 32, ENTRY_FLAGS), ('exit', 72, EXIT_FLAGS)):
        changes += [(f'{phase}_flags_bit{bit}', offset+bit//8, 1 << (bit%8))
                    for bit in range(12) if mask & (1 << bit)]
    for phase, offset in (('before', 92), ('after', 8284)):
        changes += [(f'{phase}_memory_{i}', offset+i, 1)
                    for i in (0, 4095, 4096, 8191, PAGE+0x1e4, PAGE+0x1f7)]
    for phase, fx, env in (('before', 16476, 17500), ('after', 16988, 17528)):
        changes += [(f'{phase}_fx_{i}', fx+i, 1) for i in (0, 2, 4, 6, 8, 16, 24)]
        changes += [(f'{phase}_occupied_slot{i}', fx+32+i*16, 1) for i in range(8)]
        changes += [(f'{phase}_xmm{i}', fx+160+i*16+j, 1) for i in range(8) for j in (0, 15)]
        changes += [(f'{phase}_env_{i}', env+i, 1) for i in (0, 4, 8, 12, 18, 20)]
    for name, offset, xor in changes:
        bad = bytearray(good); bad[offset] ^= xor
        try:
            validate_record(bytes(bad), case, 1, layout)
        except ValueError as error:
            controls.append({'name': name, 'outcome': 'rejected', 'reason': str(error)})
        else:
            raise ValueError('Observer failed corruption control: ' + name)
    # Native state alone must expose corrupted integer/opaque/FP storage.
    for side in (17556, 21060):
        for offset in (16, 31, 1024, 2065, 2216, 2486, 2608, 2737, 2768, 3280, 3503):
            bad = bytearray(good); bad[side+offset] ^= 1
            try:
                validate_record(bytes(bad), case, 1, layout)
            except ValueError as error:
                controls.append({'name': f'actual_state_{side}_{offset}', 'outcome': 'rejected', 'reason': str(error)})
            else:
                raise ValueError('Observer ignored actual State corruption: ' + str((side, offset)))
    # Positive controls: final instruction-undefined AF (including actual State),
    # and report-only reserved/capability padding are outside defined equality.
    for name, mutations in [('undefined_exit_AF', [(72, 16), (21060+2069, 1)]),
                            ('FX_capability_mask', [(16476+28, 1), (16988+28, 1)]),
                            ('FX_reserved_padding', [(16476+47, 1), (16988+47, 1)])]:
        altered = bytearray(good)
        for offset, xor in mutations:
            altered[offset] ^= xor
        validate_record(bytes(altered), case, 1, layout)
        controls.append({'name': name, 'outcome': 'accepted_explicit_exclusion'})
    return controls


def compare_files(paths: dict[str, Path], requests: list[Case], layout: dict) -> dict:
    failures, samples, counts = [], {}, Counter()
    streams = {name: path.open('rb') for name, path in paths.items()}
    try:
        for name, stream in streams.items():
            parse_result_header(stream, len(requests), 32 if name == 'original' else 64)
        for i, case in enumerate(requests):
            rows = {name: stream.read(RESULT_SIZE) for name, stream in streams.items()}
            for name, row in rows.items():
                try:
                    validate_record(row, case, int(name != 'original'), layout,
                                    rows['original'] if name != 'original' else None)
                except ValueError as error:
                    counts[name] += 1
                    if len(failures) < 30:
                        failures.append({'worker': name, 'index': i, 'category': case.category, 'field': str(error)})
            if i in (0, 1, 1484, 1612, 1613, 1680, len(requests)-1):
                samples[i] = rows['native-O2']
        require(all(stream.read(1) == b'' for stream in streams.values()), 'result.trailing_bytes')
    finally:
        for stream in streams.values():
            stream.close()
    controls = result_controls(samples, requests, layout) if not counts else []
    return {'passed': not counts, 'mismatched_records': dict(counts), 'examples': failures,
            'observer_controls': controls, 'observer_controls_count': len(controls)}


def run_worker(worker: Path, request: Path, output: Path, code: Path, image: Path,
               log: Path, *, timeout: int = 180) -> dict:
    require(not output.exists(), 'Refusing to overwrite prior worker evidence')
    cmd = [str(worker), str(request), str(output), str(code), str(image)]
    run = subprocess.run(cmd, capture_output=True, timeout=timeout)
    log.write_bytes(run.stdout + b'\n' + run.stderr)
    return {'command': cmd, 'exit_code': run.returncode, 'log_path': str(log), 'log_sha256': sha(log),
            'output_exists': output.exists(), 'output_bytes': output.stat().st_size if output.exists() else 0}


def admission_controls(workers: dict[str, Path], code: Path, image: Path, out: Path,
                       layout: dict) -> list[dict]:
    out.mkdir()
    q = cases()[0].pack()
    valid = HEADER.pack(b'MW34M3RQ', 1, 1, REQUEST_SIZE, 32) + q
    entries = [('header_truncated', valid[:7]), ('record_truncated', valid[:-1]),
               ('trailing', valid+b'X')]
    for name, offset, value in (('entry', 36, ENTRY+1), ('frame_low', 16, STACK-1),
                                ('frame_high', 16, STACK+PAGE-11), ('frame_wrap', 16, 0xffffffff),
                                ('flags_TF', 32, 0x302), ('flags_IF', 32, 2),
                                ('unmasked_CW', 56, 0x37e), ('reserved_PC', 56, 0x17f),
                                ('full_tags_high', 52, 0x10000), ('wrong_MXCSR', 80, 0),
                                ('wrong_FTW', 60, 0), ('nonzero_guest_FOP', 62, 1),
                                ('nonzero_guest_FIP', 64, 1), ('nonzero_guest_FDP', 72, 1)):
        bad = bytearray(q)
        size = 2 if offset in (56,62) else 1 if offset == 60 else 4
        struct.pack_into({1: '<B', 2: '<H', 4: '<I'}[size], bad, offset, value)
        entries.append((name, HEADER.pack(b'MW34M3RQ', 1, 1, REQUEST_SIZE, 32)+bad))
        entries.append(('late_'+name, HEADER.pack(b'MW34M3RQ', 1, 2, REQUEST_SIZE, 32)+q+bad))
    for offset in (5, 12, 20, 47, 300, 511):
        bad = bytearray(q); bad[56+offset] = 1
        entries.append((f'reserved_FX_{offset}', HEADER.pack(b'MW34M3RQ', 1, 1, REQUEST_SIZE, 32)+bad))
    mutated_code = out/'mutated-private-code.bin'
    body = bytearray(code.read_bytes()); body[0] ^= 1; mutated_code.write_bytes(body)
    results = []
    for worker_name, worker in workers.items():
        for name, data in entries + [('changed_private_code', valid), ('missing_private_image', valid)]:
            inp, result = out/f'{worker_name}-{name}.request.bin', out/f'{worker_name}-{name}.result.bin'
            inp.write_bytes(data)
            run = run_worker(worker, inp, result,
                             mutated_code if name == 'changed_private_code' else code,
                             out/'missing-image.exe' if name == 'missing_private_image' else image,
                             out/f'{worker_name}-{name}.log', timeout=30)
            require(run['exit_code'] != 0 and run['output_bytes'] == 0,
                    'Worker failed zero-output rejection: ' + worker_name + '/' + name)
            results.append({'worker': worker_name, 'name': name, 'outcome': 'rejected_before_output',
                            'request_sha256': sha(inp), **run})
    return results


def load_build(path: Path) -> tuple[dict, dict, dict[str, Path], Path, Path]:
    """Accept only pinned source/tool/artifact identities, then exact layout."""
    build = json.loads(path.read_bytes())
    require(build['schema_version'] == 1, 'build.schema')
    from source_identity import identity
    current = identity(ROOT)
    complete_sources = {str((ROOT/name).resolve()): digest for name, digest in current['source_files'].items()}
    require(build['source_files'] == complete_sources and build['source_digest'] == current['source_digest'],
            'build.complete_current_source_snapshot')
    for identity_group in ('source_files', 'tool_files'):
        require(build.get(identity_group), 'build.missing_' + identity_group)
        for name, digest in build[identity_group].items():
            p = Path(name)
            require(p.is_absolute() and p.is_file() and sha(p) == digest, 'build.identity:' + name)
    pinned_artifact_paths = {}
    for name, digest in build['artifacts'].items():
        p = Path(name)
        if not p.is_absolute():
            p = path.parent / p
        require(p.is_file() and sha(p) == digest, 'build.artifact:' + name)
        pinned_artifact_paths[p.resolve()] = digest
    layout_path = Path(build.get('layout_path', path.parent/'layout.json'))
    layout = json.loads(layout_path.read_bytes())
    validate_layout(layout)
    workers = {name: Path(build['workers'][name]) for name in ('original', 'native-O0', 'native-O2')}
    for name, worker in workers.items():
        require(worker.is_absolute() and worker.is_file(), 'build.worker:' + name)
        require(worker.resolve() in pinned_artifact_paths, 'build.unpinned_worker:' + name)
    require(layout_path.resolve() in pinned_artifact_paths and
            sha(path.parent/'guest.ll') == layout['guest_ir_sha256'] and
            sha(path.parent/'host.ll') == layout['host_ir_sha256'], 'build.actual_IR_layout_binding')
    code, image = Path(build['code_path']), Path(build['image_path'])
    require(sha(code) == CODE_SHA and sha(image) == IMAGE_SHA, 'build.private_image_code')
    return build, layout, workers, code, image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--replay', type=Path, help='Compare saved admitted results without running workers')
    args = parser.parse_args()
    out = args.out.resolve()
    require(out.is_relative_to((ROOT/'reports/m3-slice').resolve()), 'Private output must stay under reports/m3-slice')
    require(not out.exists(), 'Refusing to replace earlier comparison evidence')
    build, layout, workers, code, image = load_build(args.build.resolve())
    out.mkdir(parents=True)
    requests = cases()
    request = out/'requests.bin'
    with request.open('wb') as stream:
        stream.write(HEADER.pack(b'MW34M3RQ', 1, len(requests), REQUEST_SIZE, 32))
        for case in requests:
            stream.write(case.pack())
    paths, executions = {}, {}
    if args.replay:
        saved = args.replay.resolve()
        require(sha(saved/'requests.bin') == sha(request), 'Replay request corpus changed')
        paths = {name: saved/f'{name}.results.bin' for name in workers}
    else:
        for name, worker in workers.items():
            paths[name] = out/f'{name}.results.bin'
            executions[name] = run_worker(worker, request, paths[name], code, image, out/f'{name}.log')
            if executions[name]['exit_code'] != 0 or not paths[name].exists():
                put_json(out/'report.json', {'schema_version': 1, 'passed': False,
                                            'failure': 'worker_execution', 'executions': executions})
                return 1
    comparison = compare_files(paths, requests, layout)
    controls = []
    if comparison['passed'] and not args.replay:
        controls = admission_controls(workers, code, image, out/'admission-controls', layout)
    report = {'schema_version': 1, 'experiment': 'actual_MW3_whole_function_558290',
              'milestone_scope': 'First function gate; connected subsystem remains required',
              'original_cases': len(requests), 'native_comparisons': 2*len(requests),
              'category_counts': dict(Counter(q.category for q in requests)),
              'entry_flag_mask': ENTRY_FLAGS, 'exit_flag_mask': EXIT_FLAGS,
              'guest_metadata_domain': 'zero FOP/FIP/FDP only; nonzero requests reject before execution',
              'request_path': str(request), 'request_sha256': sha(request),
              'build_path': str(args.build.resolve()), 'build_sha256': sha(args.build),
              'contract_sha256': sha(ROOT/'docs/m3-slice-contract.md'),
              'executions': executions, 'results': {name: {'path': str(p), 'sha256': sha(p),
                                                         'bytes': p.stat().st_size} for name, p in paths.items()},
              'comparison': comparison, 'admission_controls': controls,
              'admission_controls_count': len(controls), 'passed': comparison['passed'],
              'replayed_saved_records': bool(args.replay)}
    put_json(out/'report.json', report)
    print(json.dumps({k: report[k] for k in ('passed', 'original_cases', 'native_comparisons', 'admission_controls_count')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print('M3 comparison rejected: ' + str(error), file=sys.stderr)
        sys.exit(1)
