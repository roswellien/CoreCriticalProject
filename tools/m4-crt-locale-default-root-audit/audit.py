"""Independent source ledger audit of the BEFORE-derived locale prefix model."""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT / 'reports/m4-crt-locale-default-root-audit'
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage
from capture_bundle import CaptureBundle

SOURCE = ROOT / 'reports/m4-crt-locale-default-recovery/recovery-r2/report.json'
SOURCE_SHA = '500e515b769e674d63503bf8572212221c7af8ae9519b712d4ee712c512c37c3'
CONTRACT = ROOT / 'reports/m4-crt-locale-default-contract/review/source-r2/report.json'
CONSUMER_SHA = '01c0c248f00785acb73b5c1ce96f2ddda1b675db6c60a0602bf04c175b1b48a8'
EXECUTION_SHA = '49ef0521fd43eda19b36085865ce3428ae9928d2ef82c8f6399e689eda7426ee'
OBSERVER_SHA = '646bd96a0578688a569b3b80f3c1a702a15f0f93dfab05991d43b6c8da9666e3'
ORIGINAL_SHA = 'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2'
PRIOR_EXECUTION = ROOT / 'reports/m4-crt-commandline-carry/root-execution-r1'
PAGE = 0x78003000
STATE_FLAGS = ((2065, 0), (2067, 2), (2069, 4), (2071, 6), (2073, 7), (2075, 10), (2077, 11))
FULL_FLAGS = tuple(pair for pair in STATE_FLAGS if pair[1] != 10)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(args):
    started = time.perf_counter_ns()
    out = workspace_path(args.output, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh immediate independent audit output')
    files = {}

    def add(path, expected=None):
        path = Path(path).absolute()
        digest = sha(path) if expected is None else expected
        key = normalized(str(path))
        need(key not in files or files[key] == digest, 'Stable current dependency ' + str(path))
        files[key] = digest
        need(sha(path) == digest, 'Current physical byte identity ' + str(path))
        return path

    add(SOURCE, SOURCE_SHA)
    source = read(SOURCE)
    add(CONTRACT)
    contract = read(CONTRACT)
    need(source['passed'] and contract['passed'], 'Successful independent source contracts')
    for path in (Path(__file__), Path(__file__).with_name('README.md'), Path(sys.executable),
                 ROOT / 'tools/m4-pipeline/manifests.py', ROOT / 'tools/m4-pipeline/paths.py',
                 ROOT / 'tools/m4-pipeline/stages.py'):
        add(path)
    for pins in (SOURCE.parent / 'pins.json', CONTRACT.parent / 'pins.json'):
        add(pins)
        for path, digest in read(pins)['files'].items():
            add(path, digest)
    core = ROOT / 'tools/m4-crt-locale-default-root'
    for path in (core / 'before.py', core / 'prefix.py'):
        add(path)
    add(core / 'consumer.py', CONSUMER_SHA)
    if args.observer:
        add(core / 'observe.py')
    original_path = add(ROOT / 'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin', ORIGINAL_SHA)
    initial_check = verify_manifest(files)
    out.mkdir(parents=True)
    previous_consumer = sys.modules.get('consumer')
    previous_before = sys.modules.get('before')
    consumer = load('consumer', core / 'consumer.py')
    sys.modules['consumer'] = consumer
    try:
        before = load('independent_audit_root_before', core / 'before.py')
        sys.modules['before'] = before
        prefix = load('independent_audit_root_prefix', core / 'prefix.py')
    finally:
        if previous_consumer is None:
            del sys.modules['consumer']
        else:
            sys.modules['consumer'] = previous_consumer
        if previous_before is None:
            sys.modules.pop('before', None)
        else:
            sys.modules['before'] = previous_before
    F, M, OLD = consumer.F, consumer.M, consumer.OLD
    need(tuple(M.F.FLAGS) == STATE_FLAGS, 'Independently fixed arithmetic/direction flag byte offsets')
    need(prefix.PCS == tuple(row['pc'] for row in source['default_path']['source_instructions']),
         'Root prefix order equals freshly decoded exact original source')
    need(list(prefix.PCS) == contract['executed_prefix_PC_order'], 'Independent source contract order')
    program, providers, maths, ctrl, init, mainargs, argv, pages, prior_commands = M.source_material(out)
    wp, pp, gp = M.R.source_material()
    locale_program, raw_page, commands = prefix.source_material(out)
    provider = M.N.PE.PEImage((ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
    # Independently map literal source material; it has no producer/initialization credit.
    expected_page = M.D.mapped(provider, PAGE)
    need(raw_page == expected_page and len(raw_page) == 4096, 'Exact additional raw source page')
    pages[PAGE] = expected_page
    for label, start, end in (('default-stub', 0x78003dd2, 0x78003ddb),
                              ('setmbcp-hot', 0x78003ddb, 0x78003e84),
                              ('lock', 0x78001055, 0x780010b0)):
        raw = SOURCE.parent / (label + '.bin')
        expected_rows = source['spans'][label]['instructions']
        need(hashlib.sha256(raw.read_bytes()).hexdigest() == source['spans'][label]['sha256'],
             'Original literal body ' + label)
        for row in expected_rows:
            size, op, operands = locale_program[row['pc']]
            need(size == len(bytes.fromhex(row['bytes_hex'])) and op == row['mnemonic']
                 and ' '.join(', '.join(operands).split()) == ' '.join(row['operands'].split()),
                 'Independently decoded source instruction '+hex(row['pc'])+': '+repr((op, operands, row)))
    original = M.R.originals(original_path.read_bytes())
    payloads = [M.R.project(row) for row in original[:24]]
    ledgers, checks, states = [], 0, []
    supplied = (args.execution, args.observer, args.stage)
    need(all(supplied) or not any(supplied), 'Complete final execution/model/stage binding or draft-only audit')
    readers, native_rows_compared, unused_jobs_compared = {}, 0, 0
    archive_stack = contextlib.ExitStack()
    if all(supplied):
        add(args.execution, EXECUTION_SHA)
        add(args.observer, OBSERVER_SHA)
        execution = read(args.execution)
        observer = read(args.observer)
        need(execution['passed'] and observer['passed'], 'Successful fixed final native/root-model reports')
        need(observer['independently_modeled_ordinary_sequences'] == 48
             and observer['standard_causal_sequences_independently_modeled_by_root'] == 0
             and observer['AFTER_machine_state_used_as_seed'] is False
             and observer['author_expected_model_imported'] is False,
             'Actual ordinary-source scope; no AFTER seed or full causal claim')
        need(observer['native_executor'].startswith('Delegated locale_native_author;')
             and observer['inherited_execution_root_label_grants_independent_root_execution_credit'] is False,
             'Delegated author executor is explicit despite historical root label')
        for level in ('O0', 'O2'):
            identity = execution['levels'][level]
            add(identity['bundle'], identity['bundle_sha256'])
            readers[level] = archive_stack.enter_context(CaptureBundle(identity['bundle'], identity['bundle_sha256']))
            need(len(readers[level].names()) == identity['logical_files'] == 41268
                 and readers[level].read_bytes('COMPLETE') == b'COMPLETE', 'Strict complete current archive')

    def eq(actual, expected, why):
        nonlocal checks
        checks += 1
        need(actual == expected, why)

    def literal_stage(state, fx, cpu, memory):
        result = OLD.stage(state, fx, cpu, memory)
        result['page-'+str(PAGE)+'.bin'] = bytes(memory[PAGE])
        result['commandline-source.bin'] = bytes(memory[0x78001000][0x88c:0x897])
        result['parser-source.bin'] = bytes(memory[0x7800b000][0xc48:0xdfc])
        result['locale-stub.bin'] = bytes(memory[PAGE][0xdd2:0xddb])
        result['locale-setmbcp.bin'] = bytes(memory[PAGE][0xddb:0xe84])
        result['locale-lock.bin'] = bytes(memory[0x78001000][0x55:0xb0])
        return result

    def frozen_memory(*values):
        value = OLD.base_memory(*values)
        value[PAGE] = bytearray(expected_page)
        return value

    # Re-run the full frozen model, taking its pre-provider snapshot. This
    # does not use the root's stopping subclass to derive the seam expectation.
    frozen_writer = types.FunctionType(F.writer.__code__,
        dict(F.writer.__globals__, base_memory=frozen_memory, stage=literal_stage))
    frozen_predict = types.FunctionType(OLD.expected.__code__,
        dict(OLD.expected.__globals__, writer_result=frozen_writer, stage=literal_stage))
    for level in ('O0', 'O2'):
        for index, payload in enumerate(payloads):
            if readers:
                row = F.LogicalPath(readers[level], 'row-' + str(index))
            else:
                row = PRIOR_EXECUTION / ('native-' + level) / ('row-' + str(index))
                for name in ('input.bin', 'writer-record.bin'):
                    add(row / name)
            base, phases = before.expected(row, payload, wp, pp, gp, program, providers,
                maths, ctrl, init, mainargs, argv, pages, level)
            frozen_entry, frozen_phases = frozen_predict(row, payload, wp, pp, gp, program,
                providers, maths, ctrl, init, mainargs, argv, pages, 0, level)
            seam = frozen_entry.args_phases['mainargs-before']
            eq(bytes(base.state), seam[0], 'Whole BEFORE-derived3504 State at healthy seam')
            eq(bytes(base.fx), seam[3], 'Whole inherited512 FX at healthy seam')
            eq(bytes(base.runtime_cpu), seam[1], 'Whole inherited RuntimeCPU at actual mainargs seam')
            eq(base.mem, seam[2], 'All17 inherited/raw page bytes at healthy seam')
            eq(set(base.mem), set(seam[2]), 'Exact carried mapping set')
            need(base.init_complete and not base.init_failed and not base.args_failed
                 and not base.args_used and base.args_accesses == [],
                 'Root halts before argument-provider admission and all argument-provider effects')
            need('entry-after-fault' not in phases and 'retry-after' not in phases,
                 'Removed unobserved pre-locale terminal labels')
            for tag, values in phases.items():
                eq(values, frozen_phases[tag], 'Unchanged independently recomputed prior phase ' + tag)
            result = prefix.predict(base, locale_program)
            initial = bytes(base.state)
            final = bytearray(initial)
            memory = copy.deepcopy(base.mem)
            regs = {name: struct.unpack_from('<I', initial, off)[0]
                    for name, off in consumer.STATE_REG.items()}
            parent = regs['esp']
            need(parent == 0x20001860 and struct.unpack_from('<I', base.runtime_cpu, 16)[0] == parent,
                 'Actual inherited parent frame')
            S = parent - 4
            struct.pack_into('<I', memory[0x20001000], S & 4095, 0xfffffff0)
            projected = bytearray(initial)
            struct.pack_into('<I', projected, consumer.STATE_REG['esp'], S)
            struct.pack_into('<I', projected, 2472, 0x78003dd2)
            eq(result['phases']['locale-projected'], literal_stage(projected, base.fx, base.runtime_cpu, memory),
               'Scheduler changes only StateEIP/ESP and one separately declared sentinel stack word')
            eq(result['phases']['locale-before'], literal_stage(initial, base.fx, base.runtime_cpu, base.mem),
               'Whole healthy locale BEFORE is carried without projection or new seed')
            ledger = []
            sub_a, sub_b = S-12, 24
            sub_v = sub_a-sub_b
            sub_bits = {0: int(sub_a < sub_b), 2: int((sub_v & 255).bit_count() % 2 == 0),
                        4: int(bool((sub_a ^ sub_b ^ sub_v) & 16)), 6: int(sub_v == 0),
                        7: (sub_v >> 31) & 1,
                        11: int(bool(((sub_a ^ sub_b) & (sub_a ^ sub_v)) & 0x80000000))}
            for access in source['default_path']['accesses']:
                expr = access['address_expression']
                address = S - int(expr[2:]) if expr.startswith('S-') else int(expr, 0)
                expr = access['value_expression']
                if expr.startswith('entry.'):
                    value = regs[expr[6:].lower()]
                elif expr.startswith('S-'):
                    value = S - int(expr[2:])
                else:
                    value = int(expr, 0)
                if access['write']:
                    need(0x20001000 <= address <= 0x20001ffc, 'Literal source write domain')
                    struct.pack_into('<I', memory[0x20001000], address & 4095, value)
                else:
                    eq(struct.unpack_from('<I', memory[address & ~4095], address & 4095)[0], value,
                       'Source argument/zero-slot read value from independent source ordering')
                ledger.append((access['pc'], address, value, 4, int(access['write'])))
                if len(ledger) in (2, 8):
                    intermediate = bytearray(initial)
                    tag = 'locale-setmbcp-before' if len(ledger) == 2 else 'locale-lock-before'
                    call_regs = dict(regs, esp=S-8 if len(ledger) == 2 else S-56)
                    if len(ledger) == 8:
                        call_regs['ebp'] = S-12
                        for off, bit in FULL_FLAGS:
                            intermediate[off] = sub_bits[bit]
                    for name, regvalue in call_regs.items():
                        struct.pack_into('<I', intermediate, consumer.STATE_REG[name], regvalue)
                    struct.pack_into('<I', intermediate, 2472, 0x78003ddb if len(ledger) == 2 else 0x78001055)
                    eq(result['phases'][tag], literal_stage(intermediate, base.fx, base.runtime_cpu, memory),
                       'Whole nested source CALL phase from affine ledger and independent SUB flags ' + tag)
            terminal_regs = dict(regs, eax=25, esi=0x7803708c, ebp=S-60, esp=S-76)
            for name, value in terminal_regs.items():
                struct.pack_into('<I', final, consumer.STATE_REG[name], value)
            struct.pack_into('<I', final, 2472, 0x780012b3)
            for off, bit in FULL_FLAGS:
                final[off] = int(bit in (2, 6))
            eq(bytes(result['state']), bytes(final), 'Whole final3504 State from independent affine source ledger')
            eq(result['memory'], memory, 'All17 page bytes; every partial source store and untouched byte retained')
            eq(result['cpu'], bytes(base.runtime_cpu), 'Generic RuntimeCPU remains at real mainargs boundary')
            eq(result['fx'], bytes(base.fx), 'Whole512 FX remains carried')
            eq(result['accesses'], ledger, 'Every ordered source PC/address/value/width/read-write access')
            eq(result['routes'], [(0x78003dd4, 0x78003ddb, 0x78003dd9),
                                 (0x78003de6, 0x78001055, 0x78003deb),
                                 (0x7800107b, 0x780012b3, 0x78001080)], 'Actual nested source CALL records')
            eq(result['scheduler'], [(struct.unpack_from('<I', initial, 2472)[0], S, 0xfffffff0, 4, 1)],
               'Scheduler is a distinct single store and has no invented source CALL')
            eq(result['PCs'], list(prefix.PCS), 'All20 decoded source PCs')
            for tag in ('locale-malloc-before', 'locale-after'):
                eq(result['phases'][tag], literal_stage(final, base.fx, base.runtime_cpu, memory),
                   'Whole actual malloc frontier phase ' + tag)
            need(result['allocator_body_executed'] is False and result['locale_initialized'] is False,
                 'No allocator/result/locale credit')
            need(struct.unpack_from('<I', final, 2120)[0] == 0,
                 'Source PUSH/CALL addresses use independently established flat SS base')
            if readers:
                expected_native = dict(phases, **result['phases'])
                terminal = literal_stage(final, base.fx, base.runtime_cpu, memory)
                expected_native['entry-after-fault'] = terminal
                expected_native['retry-after'] = terminal
                actual_tags = {name.split('/')[1] for name in row.inventory
                               if name.startswith(row.name+'/') and name.count('/') == 1}
                eq(actual_tags, set(expected_native), 'Exact complete current native checkpoint inventory')
                for tag, values in expected_native.items():
                    eq(row.inventory[row.name+'/'+tag], set(values), 'Exact whole current native phase inventory '+tag)
                    actual = {name: (row/tag/name).read_bytes() for name in values}
                    eq(actual, values, 'Actual current native whole State/FX/RuntimeCPU/pages/source phase '+tag)
                unused = {
                    'filename-job.bin': struct.pack('<22I', 0, 0xa11c0000+index, *([0]*18), 0x78037174, 0x7800bbd6),
                    'filename-witness.bin': bytes(536),
                    'commandline-job.bin': struct.pack('<28I', *([0]*4), 0x3442e, *([0]*20), 0x33000000, 0x78037174, 0x78001897),
                    'commandline-accesses.bin': bytes(320),
                    'commandline-consumer-accesses.bin': bytes(320),
                    'commandline-events.bin': bytes(256),
                    'parser-job.bin': struct.pack('<20I', *([0]*14), 0x7800bc48, 0x7800bbf7, 0x7800bbfc, 0x7800bce6, 0x780379e1, 436),
                    'parser-accesses.bin': bytes(640),
                    'parser-events.bin': bytes(128),
                    'parser-undefined.bin': bytes(32),
                }
                for name, value in unused.items():
                    eq((row/name).read_bytes(), value, 'Exact inactive later-service native record '+name)
                    unused_jobs_compared += 1
                for name in ('filename', 'commandline', 'parser'):
                    eq((row/(name+'-reason.txt')).read_text().strip(), '', 'Inactive later service has no native reason')
                eq((row/'locale-accesses.bin').read_bytes(), b''.join(struct.pack('<5I',*item) for item in ledger)+bytes(340),
                   'Actual current native source15access ledger and zero unused tail')
                current_result = json.loads((row/'result.json').read_bytes(), object_pairs_hook=unique_object)
                need(current_result['passed'] and current_result['scenario'] == index
                     and current_result['control'] == 0 and current_result['poisoned_retry']
                     and not current_result['State_reseed_after_writer']
                     and (current_result['fault_reason'], current_result['fault_site'], current_result['fault_target'])
                     == (0, 0x7800107b, 0x780012b3), 'Actual ordinary native request/refusal/retry scope')
                native_rows_compared += 1
            ledgers.append(dict(level=level, id=index, source_accesses=len(ledger), source_PCs=len(prefix.PCS),
                                parent_frame=parent, initializer_frame=S, malloc_frame=S-76,
                                whole_State=3504, whole_FX=512, whole_Runtime_CPU=40, whole_pages=17))
            states.append(hashlib.sha256(final).hexdigest())

    for module in (M, M.M, M.M.M, M.M.M.M, M.D, M.R, M.N, M.D.E, M.F, M.C):
        add(module.__file__)
        for path, digest in getattr(module, 'PINS', {}).items():
            add(path, digest)
    add(F.__file__)
    for path in out.iterdir():
        if path.is_file():
            add(path)
    proof = None
    if all(supplied):
        for path in supplied:
            add(path)
        execution, observer = read(args.execution), read(args.observer)
        need(execution['passed'] and observer['passed'], 'Successful final root native/model receipts')
        categories = ('files', 'sources', 'source_files', 'tools', 'tool_files',
                      'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts', 'input_files')
        for receipt in (execution, observer):
            for category in categories:
                for dependency, digest in receipt.get(category, {}).items():
                    add(dependency, digest)
        for path in (Path(args.execution).parent / 'pins.json', Path(args.observer).parent / 'pins.json'):
            if path.exists():
                add(path)
                for dependency, digest in read(path)['files'].items():
                    add(dependency, digest)
        stage_path = Path(args.stage)
        stage = verify_stage(stage_path.parent, sha(stage_path))
        need(stage['recorded_stage_passed'], 'Successful final root observer stage')
        proof = dict(execution_sha256=sha(args.execution), observer_sha256=sha(args.observer),
                     stage_sha256=sha(args.stage), stage_verification=stage,
                     observer_source_sha256=sha(core/'observe.py'),
                     ordinary_native_rows_compared=native_rows_compared,
                     exact_unused_later_native_records_compared=unused_jobs_compared,
                     actual_native_executor='Delegated locale_native_author',
                     independent_root_execution_credit=False)
    archive_stack.close()
    final_check = verify_manifest(files)
    report = dict(passed=True, scope='Independent BEFORE/source-ledger audit of root locale prefix model',
        original_source_recovery_sha256=SOURCE_SHA, independent_source_contract_sha256=sha(CONTRACT),
        whole_BEFORE_source_rows=48, model_comparison_checks=checks, rows=ledgers,
        independent_affine_source_ledger=True, full_frozen_model_mainargs_before_crosscheck=True,
        stopping_subclass_used_as_seam_expected_seed=False, root_consumer_equals_accepted_bytes=True,
        scheduler_store_separate_from_source=True, source_accesses_per_row=15, source_PCs_per_row=20,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_Runtime_CPU_bytes=40, whole_mappings=17,
        additional_raw_RX_mapping=PAGE, full_prior_mapping_preservation=True,
        State_projection_only_EIP_ESP=True, generic_Runtime_CPU_preserved=True,
        terminal_flag_producer=0x7800105c, source_SUB_flags_formula_reviewed=True,
        source_PUSH_CALL_checked_store_precedes_ESP_publication=True,
        source_flat_SS_base_independently_checked=True,
        AFTER_machine_state_used_as_seed=False, permitted_native_API_witness='Frozen FDIV API identity/feature query record only',
        candidate_expected_value_code_imported=False, root_model_full_causal_audit=False,
        current_native_proof_bound=proof is not None, final_root_proof=proof,
        native_executed_by_this_audit=False, original_or_game_executed_by_this_audit=False,
        allocator_body_or_result_proved=False, locale_initialized=False, original_attach_proved=False,
        full_parser_sizing_proved=False, whole_M4_complete=False,
        source_commands=prior_commands+commands,
        permitted_native_witness_transport=('Current strict native archives; only declared input and FDIV API query record seed expectations'
            if readers else 'Two already accepted flat witness files per row; no flat capture enumeration'),
        initial_dependency_check=initial_check, final_dependency_check=final_check,
        elapsed_seconds=(time.perf_counter_ns()-started)/1e9, files=dict(sorted(files.items())))
    path = out / 'report.json'
    publish_bytes(path, (json.dumps(report, indent=2) + '\n').encode())
    add(path)
    publish_bytes(out / 'pins.json', (json.dumps(dict(files=dict(sorted(files.items()))), indent=2) + '\n').encode())
    print(json.dumps(dict(passed=True, report_sha256=sha(path), pins_sha256=sha(out/'pins.json'),
                         rows=48, comparisons=checks, current_native_proof_bound=proof is not None)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--execution', type=Path)
    parser.add_argument('--observer', type=Path)
    parser.add_argument('--stage', type=Path)
    main(parser.parse_args())
