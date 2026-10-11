"""Independent bounded review of the successful masked CW unit evidence.

This is a source/receipt/input review. It deliberately does not manufacture
historical compiler dependency output or per-case hardware observation dumps.
"""
from pathlib import Path
import hashlib, json, struct, sys

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PINS, ARCHIVES = {}, {}
EXECUTION = '2632058a2b8d42834d81cdb47185dbc261c407fd95c045c03de799cd0f6cce9d'

def need(condition, message):
    if not condition:
        raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def pin(path, expected=None):
    path = Path(path).resolve()
    need(path.suffix.lower() not in ('.mwb', '.zip'), 'No archive payload reader')
    digest = sha(path)
    need(expected is None or digest == expected, 'Physical identity: ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == digest, 'Stable physical identity')
    PINS[str(path)] = digest
    return path

def load(path, expected=None):
    return json.loads(pin(path, expected).read_text(encoding='utf-8-sig'))

def mapped(report):
    for path, digest in report['files'].items():
        if Path(path).suffix.lower() in ('.mwb', '.zip'):
            need(path not in ARCHIVES or ARCHIVES[path] == digest, 'Stable retained archive declaration')
            ARCHIVES[path] = digest
        else:
            pin(path, digest)

def main(name):
    out = R / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Additive output')
    epath = R / 'reports/m4-hypot-native/control-execution-r1/report.json'
    e = load(epath, EXECUTION)
    need(e['passed'] and e['total_hardware_cases'] == 1536, 'Actual successful two-level unit execution')
    need(e['levels'] == [dict(level=level, passed=True, hardware_cases=768,
         masked_only=True, original_AFTER_seed=False, initializer_credit=0) for level in ('O0', 'O2')],
         'Both actual finite matrix summaries')
    need(e['whole_State_bytes'] == 3504 and e['whole_guest_operand_backing_bytes'] == 12
         and e['hardware_x87_header_bytes'] == 24 and e['hardware_raw80_backings'] == 8
         and e['complete_legacy_ENV_bytes'] == 28, 'Exact asserted unit byte domains')
    for field in ('SIMD_or_whole_caller_FX_claim', 'source_dynamic_path_proven',
                  'full_native_helper_executed', 'original_AFTER_seed'):
        need(e[field] is False, 'Bounded successful unit scope ' + field)
    need(type(e['initializer_credit']) is int and e['initializer_credit'] == 0, 'No initializer credit')
    mapped(e)
    bpath = R / 'reports/m4-hypot-native/control-build-r2/report.json'
    b = load(bpath, e['build_sha256']); mapped(b)
    pdir = Path(b['preparation']); p = load(pdir / 'report.json', b['preparation_sha256']); mapped(p)
    need(b['passed'] and p['passed'] and not b['native_executed'] and not p['native_executed'],
         'Actual frozen preparation and successful compilation are separate from execution')
    runtime = pin(pdir / 'control_runtime.cpp').read_text()
    probe = pin(pdir / 'control_probe.cpp').read_text()
    need(runtime == pin(R / 'tools/m4-hypot-native/control_runtime.cpp').read_text()
         and probe == pin(R / 'tools/m4-hypot-native/control_probe.cpp').read_text(), 'Exact frozen source copies')
    need('(word & 0x1f3fU) | 0x40U' in runtime and '(word & 63U) != 63U' in runtime
         and 'actual != word' in runtime and 'mw34_hypot_control_admit(state, context);' in runtime,
         'State-owned normalized fully masked CW and actual hardware/current-context guard')
    for instruction in ('fnstcw %0', 'fldcw %0', 'fwait'):
        need(instruction in runtime, 'Actual declared hardware operation ' + instruction)
    need(runtime.index('admit(state, context);', runtime.index('mw34_hypot_load_cw'))
         < runtime.index('mw34_hypot_read_memory_16(context, address)')
         < runtime.index('fldcw %0') < runtime.index('state->x87.fxsave.cwd.flat = word;'),
         'Load admission, bounded source operand, actual transfer and State publication chronology')
    for phrase in ('context->state == state', 'context->thread == GetCurrentThreadId()',
                   'std::uint64_t{address} + 2 <= 0x2000100c',
                   'std::memcmp(&state, &saved, sizeof(state)) == 0',
                   'std::memcmp(&state, &expected_state, sizeof(state)) == 0',
                   'context.memory == expected_memory', 'expected.env == after.env',
                   'std::memcmp(expected.fx.data(), after.fx.data(), 24) == 0',
                   'after.fx.data() + 32 + i * 16, 10',
                   'context.reads == 1 && context.writes == 1 && context.admissions == 3'):
        need(phrase in probe, 'Exact asserted conservation/admission domain ' + phrase)
    need('constexpr unsigned occupied_counts[]{0, 1, 4, 8};' in probe
         and 'sequence < 6' in probe and 'sticky < 2' in probe
         and 'precision < 4' in probe and 'rounding < 4' in probe,
         'Explicit 6*4*2*4*4 hardware matrix')
    need(6*4*2*4*4 == 768 and 'sw |= 0x20;' in probe, 'Masked sticky PE is an authored unit input')
    endpoints_path = R / 'reports/m4-hypot-original/prefix-validation-r2/actual-hypot-endpoints.json'
    original = load(R / 'reports/m4-hypot-original/prefix-validation-r2/report.json',
                    '80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313')
    endpoints = load(endpoints_path, original['files'][str(endpoints_path.resolve())])
    seeds = pin(p['source_state_input']).read_bytes()
    need(len(seeds) == 6*580 and len(endpoints) == 6, 'Whole bounded genuine BEFORE input extent')
    inputs = []
    for index, row in enumerate(endpoints):
        seed = struct.pack('<10I', *row['BEFORE_CPU']) + bytes.fromhex(row['BEFORE_FX512_hex']) + bytes.fromhex(row['BEFORE_ENV28_hex'])
        need(row['sequence'] == index and len(seed) == 580 and seed == seeds[index*580:(index+1)*580],
             'Every complete seed is the bound original BEFORE endpoint')
        raw = pin(row['raw_record'], row['raw_record_sha256']).read_bytes()
        need(len(raw) == 356992 and raw[36:76]+raw[116:628]+raw[2164:2192] == seed,
             'Raw observed BEFORE CPU/FX/ENV fields, fixed immutable ABI')
        cw = struct.unpack_from('<H', seed, 40)[0]
        need(cw == row['CW'] and cw & 63 == 63, 'Genuine finite fully masked starting CW')
        inputs.append(dict(sequence=index, CW=cw, whole_BEFORE_seed_sha256=hashlib.sha256(seed).hexdigest()))
    for level, command in zip(('O0', 'O2'), b['commands']):
        args = command['arguments']
        need(command['exit_code'] == 0 and args[0] == '-'+level and '-frounding-math' in args
             and '-DADDRESS_SIZE_BITS=32' in args and '-DHAS_FEATURE_AVX=0' in args
             and '-DHAS_FEATURE_AVX512=0' in args and str(pdir / 'control_runtime.cpp') in args
             and str(pdir / 'control_probe.cpp') in args, 'Exact actual compile command/source association')
        observed = load(epath.parent / (level+'.stdout'))
        need(observed == dict(passed=True,
             hardware_cases=768, masked_only=True, original_AFTER_seed=False, initializer_credit=0),
             'Actual sealed successful worker summary')
        need(pin(epath.parent / (level+'.stderr')).read_bytes() == b'', 'No actual successful worker stderr')
    pin(R / 'tools/m4-hypot-native/prepare_inputs.py')
    pin(R / 'tools/m4-hypot-native/prepare_inputs_v3.py')
    pin(__file__); pin(sys.executable)
    out.mkdir()
    report = dict(passed=True, execution_sha256=EXECUTION, build_sha256=e['build_sha256'],
        preparation_sha256=b['preparation_sha256'], levels_reviewed=2,
        actual_successful_hardware_cases=1536, complete_genuine_BEFORE_seed_joins=6,
        State_bytes=3504, guest_operand_bytes=12, hardware_x87_header_bytes=24,
        raw80_backings=8, complete_legacy_ENV_bytes=28, inputs=inputs,
        successful_source_and_receipt_review=True, historical_compiler_consumed_header_closure_proven=False,
        per_case_raw_hardware_artifacts_retained=False, initializer_credit=0,
        negative_control_credit=0, literal_helper_equivalence_credit=0,
        arbitrary_host_or_whole_caller_FX_credit=0, archive_payload_opened=False,
        scope='Independent source/actual-command/receipt/whole-BEFORE-input review of the successful masked control-transfer unit. '
              'Per-case full State, operand and declared hardware assertions are present in the frozen worker; actual O0/O2 summaries attest their successful execution. '
              'Raw per-case hardware witnesses and historical compiler-consumed include identities are not supplied by this unit chain. '
              'The failed separate denial path, outside-caller restoration, unmasked exception dispatch and literal hypot helper equivalence remain separate obligations.',
        files=PINS, retained_archive_identities_not_rehashed=ARCHIVES)
    target = out / 'report.json'; target.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=True, path=str(target), sha256=sha(target), physically_pinned_files=len(PINS))))

if __name__ == '__main__':
    main(sys.argv[1])
