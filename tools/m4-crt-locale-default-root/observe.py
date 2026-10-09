"""Independent original-BEFORE/source comparison of the default locale prefix.

Only the previously declared FDIV OS query is an external witness. No candidate
AFTER machine state or author expected-value code supplies expectations.
"""
import json
import struct
import sys
import time
import traceback
from pathlib import Path
sys.dont_write_bytecode = True
from consumer import F, M, OLD
from before import expected, stage
from prefix import predict, source_material, PAGE, ENTRY, SETMBCP, LOCK, CALL, MALLOC, RETURN, SLOT
ROOT = F.ROOT
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import verify_manifest, unique_object
from paths import publish_bytes, workspace_path
from stages import verify_stage

EXECUTION_SHA = '49ef0521fd43eda19b36085865ce3428ae9928d2ef82c8f6399e689eda7426ee'
BASELINE_SHA = 'b78c296b69dc15abf6b88d4901c8742875ca25de417497233e0687ee2704b964'
REASON = 'Required genuine CRT malloc for default locale lock remains unresolved'


def read(path):
    return json.loads(path.read_bytes(), object_pairs_hook=unique_object)


def positive(row, entry, phases, locale_program, index, level):
    result = read(row / 'result.json')
    F.require(result['passed'] and result['scenario'] == index and result['control'] == 0,
              'Ordinary declared row identity')
    F.require(result['writer_complete'] and result['entry_executed'] and result['poisoned_retry']
              and not result['State_reseed_after_writer'] and not result['full_CRT']
              and not result['whole_M4_complete'], 'Bounded carried startup without reseed or full CRT credit')
    F.require(result['source_events'] == len(entry.events) and result['writer_events'] == 97
              and result['data_routes'] == 1, 'Complete earlier source ledgers')
    parsed = predict(entry, locale_program)
    phases.update(parsed['phases'])
    terminal = stage(parsed['state'], parsed['fx'], parsed['cpu'], parsed['memory'])
    phases['entry-after-fault'] = terminal
    phases['retry-after'] = terminal
    tags = {name.split('/')[1] for name in row.inventory
            if name.startswith(row.name + '/') and name.count('/') == 1}
    F.require(tags == set(phases), 'Exact independently derived checkpoint inventory')
    for tag, values in phases.items():
        F.full_stage(row, tag, values, index == 0 and tag.startswith('locale-'))

    evidence = OLD.evidence(entry)
    # The parent has not admitted its argument-provider frame. Only the known
    # parent's first diagnostic is set by the explicit locale bootstrap.
    evidence['mainargs-job.bin'] = struct.pack('<20I', M.SLOT, M.RAW, *([0]*13), 1, 0, 0, CALL, MALLOC)
    evidence['mainargs-events.bin'] = bytes(256)
    evidence['mainargs-accesses.bin'] = bytes(1280)
    for name, value in evidence.items():
        actual = (row / name).read_bytes()
        F.require((json.loads(actual) if name.endswith('.json') else actual) == value,
                  'Complete earlier independent evidence: ' + name)
    F.require((result['fault_reason'], result['fault_site'], result['fault_target']) == (0, CALL, MALLOC),
              'Typed unresolved allocation refusal at actual source CALL')
    for name in ('mainargs-reason.txt', 'locale-reason.txt'):
        F.require((row / name).read_text().strip() == REASON, 'Preserved first locale diagnostic ' + name)
    for name, expected_reason in (('initterm', entry.init_reason), ('control', entry.control_reason),
                                 ('matherr', '')):
        F.require((row / (name+'-reason.txt')).read_text().strip() == expected_reason,
                  'Unchanged earlier service reason ' + name)
    for name in ('writer', 'entry'):
        M.D.host((row / (name+'-host-before.bin')).read_bytes(), (row / (name+'-host-after.bin')).read_bytes())
    entry_job = (row / 'entry-job.bin').read_bytes()
    F.require(len(entry_job) == 40 and entry_job[32:] == bytes(8) and
              struct.unpack_from('<3I', entry_job, 20) == (0, CALL, MALLOC), 'Ordinary boundary job without fixture callback')

    accesses = b''.join(struct.pack('<5I', *v) for v in parsed['accesses'])
    F.require((row / 'locale-accesses.bin').read_bytes() == accesses + bytes(640-len(accesses)),
              'Every ordered PUSH/CALL/argument/lock-slot source access')
    events = [(1, ENTRY, parsed['entry_frame'], 0xfffffff0)]
    events.extend((n+2, *v) for n, v in enumerate(parsed['routes']))
    events_bytes = b''.join(struct.pack('<4I', *v) for v in events)
    F.require((row / 'locale-events.bin').read_bytes() == events_bytes + bytes(128-len(events_bytes)),
              'Separate explicit scheduling event and three actual nested source CALLs')
    initial = phases['locale-before']['state.bin']
    oldpc = struct.unpack_from('<I', initial, 2472)[0]
    scheduler = (1, oldpc, parsed['parent_frame'], ENTRY, parsed['entry_frame'],
                 parsed['entry_frame'], 0xfffffff0, 0, M.SLOT, parsed['parent_frame'])
    F.require(F.words((row / 'locale-scheduler.bin').read_bytes(), 10) == scheduler,
              'Explicit State-only projection and scheduler store; generic Runtime CPU preserved')
    job = F.words((row / 'locale-job.bin').read_bytes(), 24)
    F.require(job[:13] == (0, parsed['entry_frame'], parsed['parent_frame'], 15, 4, 4, 0,
                          CALL, MALLOC, 1, 0, 1, 1) and job[13] == job[14] and
              job[15:] == (ENTRY, SETMBCP, LOCK, CALL, MALLOC, RETURN, SLOT, 17, 269),
              'Exact immutable locale request, terminal lifecycle and LastError closure')

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
        F.require((row / name).read_bytes() == value, 'Constructed but unexecuted later service ' + name)
    for name in ('filename', 'commandline', 'parser'):
        F.require((row / (name+'-reason.txt')).read_text().strip() == '', 'Unused later service has no fault ' + name)
    root_files = set(evidence) | set(unused) | {
        'input.bin', 'writer-record.bin', 'writer-host-before.bin', 'writer-host-after.bin',
        'entry-host-before.bin', 'entry-host-after.bin', 'entry-job.bin', 'result.json',
        'matherr-reason.txt', 'control-reason.txt', 'initterm-reason.txt', 'mainargs-reason.txt',
        'filename-reason.txt', 'commandline-reason.txt', 'parser-reason.txt', 'locale-reason.txt',
        'locale-job.bin', 'locale-events.bin', 'locale-accesses.bin', 'locale-scheduler.bin',
    }
    F.require(row.inventory[row.name] == root_files, 'Exact complete row evidence inventory')
    F.require(len(parsed['PCs']) == 20 and len(parsed['accesses']) == 15 and
              len(parsed['routes']) == 3 and not parsed['allocator_body_executed'] and
              not parsed['locale_initialized'], 'Complete source prefix with allocator body unexecuted')
    F.require(parsed['memory'][0x78037000][0x9e0:0xae1] == entry.mem[0x78037000][0x9e0:0xae1],
              'Whole raw 257-byte lead-byte table preserved without initialized credit')
    return dict(index=index, level=level, source_PCs=20, source_accesses=15, actual_source_CALLs=3,
        distinct_host_scheduler_stores=1, checkpoints=len(phases), full_State_bytes=3504,
        full_FX_bytes=512, full_Runtime_CPU_bytes=40, full_pages=17,
        mainargs_provider_started=False, original_attach_proved=False,
        allocator_body_executed=False, locale_initialized=False)


def main(execution_directory, output_directory):
    started = time.perf_counter_ns()
    out = workspace_path(output_directory, reports=True)
    if out.exists() or out.parent != ROOT / 'reports/m4-crt-locale-default-root':
        raise ValueError('Fresh root observer output required')
    out.mkdir()
    passed, rows, stage_checks = False, [], []
    try:
        for path in Path(__file__).parent.glob('*.py'):
            F.pin(path)
        F.pin(sys.executable)
        for name, digest in F.PIPELINE_SHAS.items():
            F.pin(ROOT / 'tools/m4-pipeline' / name, digest)
        F.pin(ROOT / 'reports/m4-crt-parser-prefix/root-acceptance-r1/report.json', BASELINE_SHA)
        execution_path = F.pin(Path(execution_directory) / 'report.json', EXECUTION_SHA)
        execution = read(execution_path)
        F.require(execution['passed'] and execution['native_stages_completed'] == 2,
                  'Fresh delegated author native execution with both worker levels complete')
        for p, h in execution['files'].items():
            F.pin(p, h)
        for level in ('O0', 'O2'):
            identity = execution['levels'][level]
            for key in ('native_stage', 'pack_stage'):
                path = F.pin(Path(identity[key]) / 'stage.json')
                checked = verify_stage(path.parent, sha_file(path))
                F.require(checked['recorded_stage_passed'], 'Actual current zero-exit native/pack stage '+level+'/'+key)
                stage_checks.append(checked)
        program, providers, maths, ctrl, init, args, argv, source, commands = M.source_material(out)
        locale_program, raw, locale_commands = source_material(out)
        source[PAGE] = raw
        wp, pp, gp = M.R.source_material()
        original_path = F.pin(ROOT / 'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin', F.ORIGINAL_SHA)
        payloads = [M.R.project(v) for v in M.R.originals(original_path.read_bytes())[:24]]
        for level in ('O0', 'O2'):
            identity = execution['levels'][level]
            bundle = F.pin(identity['bundle'], identity['bundle_sha256'])
            with CaptureBundle(bundle, identity['bundle_sha256']) as reader:
                F.require(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Strict bundled completion')
                F.require(len(reader.names()) == identity['logical_files'], 'Externally bound full logical inventory')
                F.require({n.split('/')[0] for n in reader.names()} == {'COMPLETE', 'units'} | {f'row-{n}' for n in range(36)},
                          'Exact complete capture top-level inventory')
                root = F.LogicalPath(reader, 'root')
                units = F.LogicalPath(reader, 'units', root.inventory)
                F.require(root.inventory['units'] == {'api-before.bin', 'api-after.bin',
                    'module-before.bin', 'module-after.bin', 'caller-error.bin',
                    'units-host-before.bin', 'units-host-after.bin'} |
                    {f'capacity-{n}.bin' for n in (0, 1, 8, 260)}, 'Exact ancillary API-unit evidence inventory')
                unit_module = F.identities(units, F.pin(identity['worker']), prefix='')
                M.D.host((units/'units-host-before.bin').read_bytes(), (units/'units-host-after.bin').read_bytes())
                errors = F.words((units/'caller-error.bin').read_bytes(), 2)
                F.require(errors[0] == errors[1], 'Ancillary unit restores caller LastError')
                for size in (0, 1, 8, 260):
                    data = (units/f'capacity-{size}.bin').read_bytes()
                    F.require(len(data) == 536, 'Whole ancillary API-unit witness')
                    request, incoming, length, error = F.words(data[:16], 4)
                    before, after = data[16:276], data[276:]
                    F.require(before == bytes((n*31+17)&255 for n in range(260)), 'Declared ancillary scratch seed')
                    F.require((request, incoming) == (size, 0xface0123) and after[size:] == before[size:],
                              'Ancillary API capacity and untouched tail')
                    if size < 260:
                        F.require((length, error) == (size, 122), 'Actual ancillary truncation/zero-capacity result')
                        if size:
                            F.require(after[size-1] == 0, 'Actual ancillary truncation NUL')
                    else:
                        F.require(0 < length < size and after[length] == 0 and
                                  after[length+1:] == before[length+1:] and
                                  after[:length].decode('mbcs') == str(unit_module), 'Actual ancillary filename/NUL/tail')
                for index in range(36):
                    value = read(F.LogicalPath(reader, f'row-{index}/result.json', root.inventory))
                    F.require(value['passed'] and value['scenario'] == index and
                              value['control'] == (0 if index < 24 else index+73), 'Bound native row request identity')
                for index in range(24):
                    row = F.LogicalPath(reader, f'row-{index}', root.inventory)
                    entry, phases = expected(row, payloads[index], wp, pp, gp, program,
                        providers, maths, ctrl, init, args, argv, source, level)
                    rows.append(positive(row, entry, phases, locale_program, index, level))
        for module in (M, M.M, M.M.M, M.M.M.M, M.D, M.R, M.N, M.D.E, M.F, M.C):
            for p, h in module.PINS.items():
                F.pin(p, h)
        for p in out.iterdir():
            if p.is_file():
                F.pin(p)
        closure = verify_manifest(F.PHYSICAL)
        passed = True
    except Exception:
        publish_bytes(out / 'failure.txt', traceback.format_exc().encode('utf-8'))
        raise
    finally:
        report = dict(passed=passed, rows=rows, checks=F.CHECKS,
            independently_modeled_ordinary_sequences=48 if passed else 0,
            standard_causal_sequences_independently_modeled_by_root=0,
            selected_semantic_byte_corruption_denials=F.SEMANTIC_DENIALS,
            scope='Independent original BEFORE/source derivation; frozen FDIV OS query witness only',
            native_executor='Delegated locale_native_author; root verifies actual stages and independently models ordinary rows',
            inherited_execution_root_label_grants_independent_root_execution_credit=False,
            native_stages=stage_checks, State_bytes=3504, FX_bytes=512, borrowed_pages=17,
            ancillary_real_API_capacity_units=8, legacy_host_pairs_compared=98 if passed else 0,
            prior_pages_preserved=16, new_raw_RX_page=PAGE, source_identity_bytes=1856,
            new_compiled_source_bytes=221, new_guarded_source_bytes=269,
            actual_source_PCs=20, actual_source_DWORD_accesses=15, actual_nested_source_CALLs=3,
            explicit_host_scheduler_store_separate=True, generic_Runtime_CPU_preserved=True,
            locale_RET_executed=False, allocator_body_executed=False, initialized_lock_proved=False,
            locale_initialized=False, codepage_API_executed=False, parser_executed_in_this_gate=False,
            DllMain_or_original_scheduling_recovered=False, State_reseed=False,
            argument_initialization_complete=False, main_initializer_count=27,
            whole_M4_complete=False, game_launched=False, original_executed=False,
            author_expected_model_imported=False, AFTER_machine_state_used_as_seed=False,
            source_commands=commands+locale_commands, files=F.PHYSICAL,
            physical_closure=closure if passed else None,
            seconds=(time.perf_counter_ns()-started)/1e9)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2)+'\n').encode('utf-8'))
        if passed:
            F.pin(out / 'report.json')
            publish_bytes(out / 'pins.json', (json.dumps(dict(files=F.PHYSICAL), indent=2)+'\n').encode('utf-8'))
        print(json.dumps({k:v for k,v in report.items() if k not in ('files','rows','source_commands','native_stages')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
