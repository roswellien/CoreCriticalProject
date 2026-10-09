"""BEFORE-only source composition, then declared filename ABI; reads bundles directly.

Native API output is an actual OS witness, not a claimed x86 API oracle. Guest
machine expectations originate in the frozen original BEFORE capture and the
independent literal source model. No candidate expected-value code is imported.
"""
import copy
import hashlib
import json
import ntpath
import struct
import sys
import time
import traceback
import types
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import verify_manifest
from paths import publish_bytes, workspace_path

SELF_SHA = sha_file(__file__)
PIPELINE_SHAS = {
    'paths.py': 'c17b154b5dc86074d4df85f64108fe2cc587dbe8dacc3f303bf1b4f4d865ef66',
    'capture_bundle.py': '486ec0074d1a7e5171f7744dc23cd5b0acb5b1e104242e58749ae77ccb79f4e1',
    'manifests.py': '67b56e5622a1d3dd1b0cbf4d6eb5de5a71a773f01ac2cf584ea5f97a03a4dd9b',
    'stages.py': '4a6bf3503db40959ff5e1ecd69d971c4e8f1866d706576423fc53a1560b79cd4',
}

MODEL_SHA = '2d1abb299279e6788a4d65483ef67b249d26e51465153604f3b34b621d5e4c59'
OBSERVER_SHA = 'a7e791622a3e21a04970f53695d4403dccbb3856bc72ab8fd75b0b1487f18029'
ORIGINAL_SHA = 'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2'


def load(name, path, digest):
    import importlib.util
    if sha_file(path) != digest:
        raise ValueError('Frozen independent source model changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = load('filename_frozen_mainargs_model', ROOT / 'tools/m4-crt-mainargs-root/model.py', MODEL_SHA)
previous = sys.modules.get('model')
sys.modules['model'] = M
try:
    OLD = load('filename_frozen_mainargs_observer', ROOT / 'tools/m4-crt-mainargs-root/observe.py', OBSERVER_SHA)
finally:
    if previous is None:
        del sys.modules['model']
    else:
        sys.modules['model'] = previous


class LogicalPath:
    """Explicit reader adapter, without creating fictitious physical file pins."""
    def __init__(self, reader, name, inventory=None):
        self.reader, self.name = reader, name
        if inventory is None:
            inventory = {}
            for entry in reader.names():
                if '/' in entry:
                    parent, child = entry.rsplit('/', 1)
                    inventory.setdefault(parent, set()).add(child)
        self.inventory = inventory

    def __truediv__(self, other):
        return LogicalPath(self.reader, self.name + '/' + str(other), self.inventory)

    def read_bytes(self):
        return self.reader.read_bytes(self.name)

    def read_text(self, encoding='utf-8'):
        return self.read_bytes().decode(encoding)

    def __str__(self):
        return 'bundle-entry:' + self.name


def explicit_reader_pin(path, digest=None):
    if not isinstance(path, LogicalPath):
        return M.pin(path, digest)
    if digest is not None and hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('Logical entry hash changed')
    return path


# Only two reads in this frozen function consume current worker data: the
# original-derived input and FDIV writer's actual native OS query record.
# Remaining guest effects are independently interpreted from source bytes.
writer = types.FunctionType(OLD.writer_result.__code__,
    dict(OLD.writer_result.__globals__, pin=explicit_reader_pin))
predict = types.FunctionType(OLD.expected.__code__,
    dict(OLD.expected.__globals__, writer_result=writer))

CHECKS = 0
SEMANTIC_DENIALS = 0
PHYSICAL = {}


def require(ok, why):
    global CHECKS
    CHECKS += 1
    if not ok:
        raise AssertionError(why)


def pin(path, digest=None):
    path = Path(path).absolute()
    actual = sha_file(path)
    require(digest is None or actual == digest, 'Physical input SHA: ' + str(path))
    key = ntpath.normcase(ntpath.normpath(str(path)))
    require(key not in PHYSICAL or PHYSICAL[key] == actual, 'Unambiguous physical binding')
    PHYSICAL[key] = actual
    return path


def words(data, count):
    require(len(data) == count * 4, 'Exact DWORD capture extent')
    return struct.unpack('<' + 'I' * count, data)


def put(data, offset, value):
    struct.pack_into('<I', data, offset, value)


def validate_stage_record(actual, expected, tag):
    require(set(actual) == set(expected), 'Exact complete storage inventory: ' + tag)
    for name, value in expected.items():
        require(actual[name] == value, tag + '/' + name + ' independently predicted complete storage')


def full_stage(row, tag, expected, attack=False):
    global SEMANTIC_DENIALS
    names = row.inventory.get(row.name + '/' + tag, set())
    require(names == set(expected), 'Exact complete storage inventory: ' + tag)
    actual = {name: (row / tag / name).read_bytes() for name in names}
    validate_stage_record(actual, expected, tag)
    if attack:
        for name, value in expected.items():
            for offset in sorted({0, len(value) - 1}):
                if offset < 0:
                    continue
                changed = bytearray(actual[name])
                changed[offset] ^= 1
                corrupted = dict(actual, **{name: bytes(changed)})
                try:
                    validate_stage_record(corrupted, expected, tag)
                except AssertionError:
                    SEMANTIC_DENIALS += 1
                else:
                    raise AssertionError('Corrupted complete stage passed the shared semantic validator')


def identities(row, worker, prefix='filename-'):
    module_path = None
    for kind, digest_offset, extent in (('api', 72, 2184), ('module', 48, 2160)):
        before = (row / f'{prefix}{kind}-before.bin').read_bytes()
        after = (row / f'{prefix}{kind}-after.bin').read_bytes()
        require(before == after and len(before) == extent, 'Actual API/module identity capture closure')
        digest = before[digest_offset:digest_offset + 64].decode('ascii')
        path = Path(before[digest_offset + 64:].decode('utf-16-le').split('\0')[0])
        pin(path, digest)
        region = struct.unpack_from('<3Q4I', before, 32 if kind == 'api' else 8)
        base, size, allocation, state, image_type, protection, _ = region
        require(state == 0x1000 and image_type == 0x1000000, 'Committed actual native image')
        if kind == 'api':
            address, named, owner, owner_named = struct.unpack_from('<4Q', before)
            require(address == named == owner_named and owner == allocation and base <= address < base + size,
                'Named/forwarded actual native executable API owner')
            require(protection & 0xf0 and not protection & 0x101, 'Executable API protection')
        else:
            module_path = path
            require(struct.unpack_from('<Q', before)[0] == base == allocation and
                ntpath.normcase(str(path)) == ntpath.normcase(str(worker)),
                'NULL module denotes this actual AMD64 worker')
    return module_path


def filename_case(row, entry, phases, index, worker, attack=False):
    mode = 0 if index < 24 else index + 37
    base = phases['mainargs-builder-after']
    state, memory, fx, cpu = bytearray(entry.state), copy.deepcopy(entry.mem), bytearray(entry.fx), bytes(entry.runtime_cpu)
    result = json.loads((row / 'result.json').read_bytes())
    require(result['passed'] and result['scenario'] == index and result['control'] == mode,
        'Exact native row request identity')
    require(result['writer_complete'] and result['entry_executed'] and result['poisoned_retry'] and
        not result['State_reseed_after_writer'] and not result['full_CRT'] and not result['whole_M4_complete'],
        'Bounded native execution and cleanup scope')
    require(result['source_events'] == len(entry.events) and result['writer_events'] == 97 and result['data_routes'] == 1,
        'Complete existing game/writer ledger')
    full_stage(row, 'filename-before', base, attack)
    job = words((row / 'filename-job.bin').read_bytes(), 22)
    require(job[0:3] == (mode, 0xa11c0000 + index, 0x20001834) and
        job[20:] == (0x78037174, 0x7800bbd6), 'Exact declared filename frame and producer dependency')
    require(job[5] == job[6] and job[18] == job[19], 'Inner and outer host LastError preserved')
    witness = (row / 'filename-witness.bin').read_bytes()
    require(len(witness) == 536, 'Exact full-capacity API witness')
    called = mode not in (61, 63, 64, 65, 66, 67)
    stored = mode in (0, 69, 70)
    returned = mode in (0, 70)
    point = {0: 5, 61: 1, 62: 2, 63: 1, 64: 1, 65: 1, 66: 1,
        67: 1, 68: 2, 69: 3, 70: 4, 71: 2, 72: 2}[mode]
    require(job[7:9] == (point, point) and job[11:18] ==
        (1, 0, int(called), int(stored), int(returned), int(mode == 0), int(mode != 0)),
        'Causal admission/API/store/RET/stop ordering and terminal lifecycle')
    if called:
        capacity, incoming, length, error = words(witness[:16], 4)
        old, new = witness[16:276], witness[276:]
        require((capacity, incoming, length, error) == (260, job[1], job[3], job[4]),
            'Immediate actual OS return and LastError witness')
        require(old == bytes(memory[0x7803b000][0x3f0:0x4f4]),
            'Full API scratch seeded from independently predicted guest bytes')
        require(0 < length < 260 and new[length] == 0 and new[length + 1:] == old[length + 1:],
            'Actual success byte count, NUL and untouched tail')
        module_path = identities(row, worker)
        require(new[:length].decode('mbcs') == str(module_path), 'Actual ANSI filename agrees with witnessed native worker module')
        full_stage(row, 'filename-api-after', base, attack)
    else:
        require(witness == bytes(536) and job[3:5] == (0, 0), 'No fabricated native OS outcome')
        new = bytes(260)

    mutations = {61: (0x20001834, 0x7800bbd7), 63: (0x7802e018, 0x343b1),
        64: (0x7800bbbc, 0), 65: (0x20001838, 1), 66: (0x20001840, 259),
        71: (0x20001834, 0x7800bbd7)}
    if mode in mutations:
        address, value = mutations[mode]
        put(memory[address & ~4095], address & 4095, value)
    if mode == 72:
        put(state, 2280, struct.unpack_from('<I', state, 2280)[0] ^ 1)
    if stored:
        memory[0x7803b000][0x3f0:0x4f4] = new
        phases['filename-buffer-after'] = OLD.stage(state, fx, cpu, memory)
    if returned:
        put(state, 2216, job[3])
        put(state, 2312, 0x20001844)
        put(state, 2472, 0x7800bbd6)
        phases['filename-return-after'] = OLD.stage(state, fx, cpu, memory)
    if mode == 0:
        phases['filename-commandline-before'] = OLD.stage(state, fx, cpu, memory)
        require(job[9:11] == (0, 0), 'Successful service has no filename first fault')
        require((result['fault_reason'], result['fault_site'], result['fault_target']) ==
            (0, 0x7800bbd6, 0x78037174), 'Refusal BEFORE initialized command-line load')
        reason = 'Required initialized CRT command-line producer remains unresolved'
        expected_filename_reason = ''
        fault_pc, fault_address = 0x7800bbd6, 0x78037174
    else:
        require((result['fault_reason'], result['fault_site'], result['fault_target']) == (4, M.SLOT, M.SLOT),
            'Causal required-service refusal and outer fault attribution')
        failures = {
            61: ('Actual filename NULL/module/buffer/capacity/return closure rejected', 0x7800bbd0, 0x20001834),
            62: ('Checked atomic full filename guest buffer write rejected', 0x7800bbd0, 0x7803b3f0),
            63: ('Actual filename NULL/module/buffer/capacity/return closure rejected', 0x7800bbd0, 0x20001834),
            64: ('Exact mainargs/provider source and game IAT identity', 0x343b0, 0),
            65: ('Actual filename NULL/module/buffer/capacity/return closure rejected', 0x7800bbd0, 0x20001834),
            66: ('Actual filename NULL/module/buffer/capacity/return closure rejected', 0x7800bbd0, 0x20001834),
            67: ('Filename observer or host exception', 0x343b0, 0x7803b3f0),
            68: ('Filename observer or host exception', 0x343b0, 0x7803b3f0),
            69: ('Filename observer or host exception', 0x343b0, 0x7803b3f0),
            70: ('Filename observer or host exception', 0x7800bbd6, 0x7803b3f0),
            71: ('Actual filename NULL/module/buffer/capacity/return closure rejected', 0x7800bbd0, 0x20001834),
            72: ('Filename service carried State/FX changed before publication', 0x7800bbd0, 0x7803b3f0)}
        expected_filename_reason, expected_pc, expected_address = failures[mode]
        require(job[9:11] == (expected_pc, expected_address), 'Exact typed first filename fault')
        reason = expected_filename_reason if mode not in (67, 68, 69, 70) else 'Required mainargs observer or host fault'
        # The generic encompassing catch calls Context.first without an
        # explicit PC/address: it retains current State PC and default address0.
        fault_pc, fault_address = (expected_pc, expected_address) if mode not in (67, 68, 69, 70) else (expected_pc, 0)
    require((row / 'filename-reason.txt').read_text().strip() == expected_filename_reason,
        'First filename reason is retained')
    require((row / 'mainargs-reason.txt').read_text().strip() == reason, 'Outer first refusal reason')
    for name in ('mainargs-builder-after', 'mainargs-after', 'entry-after-fault', 'retry-after'):
        phases[name] = OLD.stage(state, fx, cpu, memory)
    phases['filename-before'] = base
    if called:
        phases['filename-api-after'] = base
    actual_tags = {name.split('/')[1] for name in row.inventory
        if name.startswith(row.name + '/') and name.count('/') == 1}
    require(actual_tags == set(phases), 'Exact checkpoint inventory with no invented continuation')
    for tag, values in phases.items():
        full_stage(row, tag, values, attack and tag.startswith('filename-'))
    evidence = OLD.evidence(entry)
    routes = list(entry.args_events[:3])
    if called:
        routes.append(entry.args_events[3])
    if returned:
        routes.append((5, 0x7800bbd6, 0x20001844, job[3]))
    if mode == 0:
        routes.append((6, 0x7800bbd6, 0x78037174, 0))
    evidence['mainargs-events.bin'] = b''.join(struct.pack('<4I', *v) for v in routes) + bytes(256 - len(routes) * 16)
    old_job = list(entry.args_job)
    old_job[11], old_job[16], old_job[18], old_job[19] = len(routes), int(called), fault_pc, fault_address
    evidence['mainargs-job.bin'] = struct.pack('<20I', *old_job)
    for name, value in evidence.items():
        actual = (row / name).read_bytes()
        require((json.loads(actual) if name.endswith('.json') else actual) == value,
            'Complete source/call/access ledger: ' + name)
    job_record = (row / 'entry-job.bin').read_bytes()
    require(len(job_record) == 40 and job_record[32:] == bytes(8), 'No unit callback in ordinary native entry job')
    require(struct.unpack_from('<3I', job_record, 20) ==
        (result['fault_reason'], result['fault_site'], result['fault_target']), 'Direct outer job first-fault metadata')
    for name in ('writer', 'entry'):
        M.D.host((row / f'{name}-host-before.bin').read_bytes(), (row / f'{name}-host-after.bin').read_bytes())
    return dict(index=index, control=mode, actual_API=called, buffer_stored=stored,
        stdcall_returned=returned, required_commandline_read_executed=False,
        checkpoints=len(phases), storage_files=sum(map(len, phases.values())))


def main(execution_directory, output_directory):
    started = time.perf_counter_ns()
    out = workspace_path(output_directory, reports=True)
    if out.exists() or out.parent != ROOT / 'reports/m4-crt-filename':
        raise ValueError('Fresh root observer output required')
    out.mkdir()
    passed = False
    rows = []
    try:
        pin(__file__, SELF_SHA)
        for name, digest in PIPELINE_SHAS.items():
            pin(ROOT / 'tools/m4-pipeline' / name, digest)
        execution_path = pin(Path(execution_directory) / 'report.json')
        execution = json.loads(execution_path.read_text(encoding='utf-8'))
        require(execution['passed'] and execution['native_executed_by_root'], 'Root-owned native execution required')
        for p, h in execution['files'].items():
            pin(p, h)
        material = M.source_material(out)
        program, providers, maths, ctrl, init, args, argv, source, commands = material
        require(argv[0x7800bbd6] == (5, 'mov', ['eax', 'dword ptr [0x78037174]']),
            'Exact literal source read that remains refused')
        wp, pp, gp = M.R.source_material()
        original_path = pin(ROOT / 'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin', ORIGINAL_SHA)
        original = M.R.originals(original_path.read_bytes())
        payloads = [M.R.project(v) for v in original[:24]]
        for level in ('O0', 'O2'):
            identity = execution['levels'][level]
            bundle = pin(identity['bundle'], identity['bundle_sha256'])
            worker = pin(identity['worker'])
            with CaptureBundle(bundle, identity['bundle_sha256']) as reader:
                require(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Strict bundled completion')
                logical_root = LogicalPath(reader, 'root')
                for index in range(36):
                    row = LogicalPath(reader, 'row-' + str(index), logical_root.inventory)
                    entry, phases = predict(row, payloads[index if index < 24 else 0],
                        wp, pp, gp, program, providers, maths, ctrl, init, args, argv, source, 0, level)
                    value = filename_case(row, entry, phases, index, worker, attack=index == 0)
                    rows.append(dict(level=level, **value))
                units = LogicalPath(reader, 'units', logical_root.inventory)
                unit_module = identities(units, worker, prefix='')
                M.D.host((units / 'units-host-before.bin').read_bytes(), (units / 'units-host-after.bin').read_bytes())
                errors = words((units / 'caller-error.bin').read_bytes(), 2)
                require(errors[0] == errors[1], 'Units restore enclosing caller error')
                for size in (0, 1, 8, 260):
                    data = (units / f'capacity-{size}.bin').read_bytes()
                    require(len(data) == 536, 'Exact unit witness')
                    request, incoming, result, error = words(data[:16], 4)
                    before, after = data[16:276], data[276:]
                    require(before == bytes((n * 31 + 17) & 255 for n in range(260)), 'Exact authored unit scratch seed')
                    require((request, incoming) == (size, 0xface0123) and after[size:] == before[size:], 'Bounded real unit capacity/tail')
                    if size < 260:
                        require((result, error) == (size, 122), 'Actual Windows truncation/zero-capacity result')
                        if size:
                            require(after[size - 1] == 0, 'Actual truncation NUL')
                    else:
                        require(0 < result < size and after[result] == 0 and after[result + 1:] == before[result + 1:], 'Success length/NUL/tail')
                        require(after[:result].decode('mbcs') == str(unit_module), 'Actual unit filename matches native module witness')
        for module in (M, M.M, M.M.M, M.M.M.M, M.D, M.R, M.N, M.D.E, M.F, M.C):
            for p, h in module.PINS.items():
                pin(p, h)
        pin(ROOT / 'tools/m4-crt-mainargs-root/model.py', MODEL_SHA)
        pin(ROOT / 'tools/m4-crt-mainargs-root/observe.py', OBSERVER_SHA)
        pin(__file__, SELF_SHA)
        pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():
                pin(p)
        closure = verify_manifest(PHYSICAL)
        passed = True
    except Exception:
        publish_bytes(out / 'failure.txt', traceback.format_exc().encode('utf-8'))
        raise
    finally:
        report = dict(passed=passed, scope='Independent original BEFORE/source derivation plus declared native filename ABI, strict bundle reader',
            rows=rows, checks=CHECKS, selected_semantic_byte_corruption_denials=SEMANTIC_DENIALS,
            positive_sequences=48 if passed else 0, causal_sequences=24 if passed else 0,
            actual_capacity_units=8 if passed else 0, ordinary_host_pairs=146 if passed else 0,
            full_State3504_FX512_pages16_source1140=True, author_expected_model_imported=False,
            original_executed=False, game_launched=False, guest_TEB_LastError_written=False,
            x86_native_API_volatile_equivalence_claimed=False, argument_initialization_complete=False,
            main_initializer_count=27, whole_M4_complete=False, files=PHYSICAL,
            physical_closure=closure if passed else None,
            seconds=(time.perf_counter_ns() - started) / 1e9)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
        print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'rows')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
