"""Read-only review receipt for the final filename BEFORE-only root observer.

This validates association and reviewed scope; it does not rerun the observer,
the candidate worker, original provider code, or the game.
"""
import hashlib
import json
import ntpath
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-filename'
PROOF_SHA = 'cca4a274b6082439222b275429b0860ed76bc9e499cc88d79b784725ac3ff570'
EXECUTION_SHA = '96840cb525fa731f703cad016b261b149afd862979d0ad633c04316ed28f3ad9'
OBSERVER_SHA = '405797301b25103cdc27dd0635e93e169a4ef86f415afb7c8a431da23703733e'
STAGE_SHA = '9e1ca18d79df0821d8af72b0cba49c17fe75b09dbb8bc6c3c69e01eefe7457a4'


def need(ok, why):
    if not ok: raise ValueError(why)


def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    out = BASE / 'independent-root-model-audit-r1'
    need(not out.exists(), 'Fresh read-only audit receipt required')
    pins = {}
    def bind(path, expected=None):
        path = Path(path).absolute()
        actual = sha(path)
        key = ntpath.normcase(ntpath.normpath(str(path)))
        need((expected is None or actual == expected) and (key not in pins or pins[key] == actual),
             'Physical association changed/conflicted: ' + str(path))
        pins[key] = actual
        return path
    proof_path = bind(BASE / 'root-observer-r3/report.json', PROOF_SHA)
    execution_path = bind(BASE / 'root-execution-r2/report.json', EXECUTION_SHA)
    proof, execution = read(proof_path), read(execution_path)
    need(proof['passed'] and execution['passed'], 'Both matching root receipts must pass')
    for receipt in (proof, execution):
        for path, digest in receipt['files'].items(): bind(path, digest)
    observer_path = bind(ROOT / 'tools/m4-crt-filename-root/observe.py', OBSERVER_SHA)
    observer = observer_path.read_text()
    stage = read(bind(BASE / 'root-observer-stage-r3/stage.json', STAGE_SHA))
    need(stage['passed'] and stage['format'] == 'mw34.stage.v1' and stage['status'] == 'success',
         'Exact passed root observer stage schema')
    invoked_observer = ntpath.normcase(ntpath.normpath(str(Path(stage['cwd']) / stage['argv'][1])))
    need(invoked_observer == ntpath.normcase(ntpath.normpath(str(observer_path))) and stage['required_outputs'] == [str(proof_path)],
         'Observer invocation/output association')
    for group in ('input_sha256', 'final_input_sha256', 'artifact_sha256'):
        for path, digest in stage[group].items(): bind(path, digest)
    need(stage['inputs_stable'] and stage['elapsed_seconds'] >= 0 and
         not stage['process_file_open_attestation'] and not stage['command_shell_used'], 'Narrow real stage timing/association')
    bind(BASE / 'root-observer-stage-r3/stdout.bin', stage['stdout_sha256'])
    bind(BASE / 'root-observer-stage-r3/stderr.bin', stage['stderr_sha256'])
    expected = dict(checks=107306, selected_semantic_byte_corruption_denials=952,
                    positive_sequences=48, causal_sequences=24, actual_capacity_units=8,
                    ordinary_host_pairs=146, main_initializer_count=27)
    for key, value in expected.items(): need(proof[key] == value, 'Exact successful proof count: ' + key)
    need(proof['full_State3504_FX512_pages16_source1140'] and proof['physical_closure']['passed'] and
         proof['physical_closure']['unique_physical_dependencies'] == 736, 'Whole predicted storage/source and physical scope')
    for key in ('author_expected_model_imported', 'original_executed', 'game_launched', 'guest_TEB_LastError_written',
                'x86_native_API_volatile_equivalence_claimed', 'argument_initialization_complete', 'whole_M4_complete'):
        need(proof[key] is False, 'Explicit unclaimed scope: ' + key)
    need(execution['build_sha256'] == '1868574163cdbce4491afe2217688ef549189f184e20549e31f68e44930fb1d5' and
         execution['positive_cases'] == 48 and execution['causal_controls'] == 24 and execution['API_capacity_units'] == 8,
         'Current immutable candidate and native execution count')
    need(execution['levels']['O0']['adopted_successful_root_stage'] and
         not execution['levels']['O2']['adopted_successful_root_stage'], 'Explicit recovered O0/fresh O2 provenance')
    rows = proof['rows']
    need(len(rows) == 72, 'All real native rows observed')
    for level in ('O0', 'O2'):
        own = [r for r in rows if r['level'] == level]
        need([r['index'] for r in own] == list(range(36)), 'Exact per-level native row order')
        for row in own:
            index = row['index']; mode = 0 if index < 24 else index + 37
            need(row['control'] == mode and not row['required_commandline_read_executed'], 'Exact bounded control/read scope')
            need(row['actual_API'] == (mode not in (61,63,64,65,66,67)) and
                 row['buffer_stored'] == (mode in (0,69,70)) and row['stdcall_returned'] == (mode in (0,70)),
                 'Actual partial API/store/RET ordering for all injected faults')
    for fragment in (
        "writer = types.FunctionType(OLD.writer_result.__code__",
        "dict(OLD.writer_result.__globals__, pin=explicit_reader_pin)",
        "original = M.R.originals(original_path.read_bytes())",
        "payloads = [M.R.project(v) for v in original[:24]]",
        "'Full API scratch seeded from independently predicted guest bytes'",
        'validate_stage_record(actual, expected, tag)',
        'validate_stage_record(corrupted, expected, tag)',
        "fault_pc, fault_address = (expected_pc, expected_address) if mode not in (67, 68, 69, 70) else (expected_pc, 0)",
        "job_record = (row / 'entry-job.bin').read_bytes()",
        'len(job_record) == 40 and job_record[32:] == bytes(8)',
        "unit_module = identities(units, worker, prefix='')",
        "bytes((n * 31 + 17) & 255 for n in range(260))",
        "pin(__file__, SELF_SHA)", 'closure = verify_manifest(PHYSICAL)'):
        need(fragment in observer, 'Reviewed original BEFORE/service/validator schema seam absent')
    need('changed != value' not in observer and 'writer-job.bin' not in observer and
         "tools/m4-crt-filename/observe.py" not in observer, 'No tautological denial, nonexistent writer job, or author oracle import')
    # Count unique tested locations independently from the bundle inventories.
    # The observer additionally invokes the same checks twice for its first two
    # filename phases; its 952 rejections are real, with repeated locations.
    sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
    from capture_bundle import CaptureBundle
    from stages import verify_stage
    unique_positions = set()
    for level, identity in execution['levels'].items():
        for key in ('native_stage', 'pack_stage'):
            directory = Path(identity[key])
            verify_stage(directory, pins[ntpath.normcase(ntpath.normpath(str(directory / 'stage.json')))])
        with CaptureBundle(identity['bundle'], identity['bundle_sha256']) as reader:
            for name in reader.names():
                parts = name.split('/')
                if len(parts) == 3 and parts[0] == 'row-0' and parts[1].startswith('filename-'):
                    value = reader.read_bytes(name)
                    for offset in sorted({0, len(value)-1}):
                        if offset >= 0: unique_positions.add((level, parts[1], parts[2], offset))
    need(len(unique_positions) == 680, 'Exact selected unique stage corruption locations')
    for path in (BASE / 'independent-contract-r2/report.json', BASE / 'independent-contract-r2/pins.json',
                 ROOT / 'tools/m4-crt-filename-contract/root_audit.py',
                 ROOT / 'tools/m4-crt-fdiv-independent/replay_model.py',
                 ROOT / 'tools/m4-crt-entry-control-root/observe.py',
                 ROOT / 'tools/m4-crt-mainargs-root/observe.py', ROOT / 'tools/m4-crt-mainargs-root/model.py',
                 ROOT / 'tools/m4-crt-filename-root/resume.py', ROOT / 'tools/m4-crt-filename-root/run.py',
                 BASE / 'root-observer-r1/report.json', BASE / 'root-observer-r1/failure.txt',
                 BASE / 'root-observer-r2/report.json', BASE / 'root-observer-r2/failure.txt'):
        bind(path)
    for path, digest in list(pins.items()): bind(path, digest)
    out.mkdir()
    report = dict(passed=True, scope='Read-only independent audit of final root BEFORE-only filename service observer and exact recovered execution/source association; no proof/native rerun',
        root_observer_report_sha256=PROOF_SHA, root_execution_report_sha256=EXECUTION_SHA,
        reviewed_observer_sha256=OBSERVER_SHA, observer_stage_sha256=STAGE_SHA,
        whole_State_bytes=3504, whole_FX_bytes=512, whole_pages=16, whole_source_identity_bytes=1140,
        **expected, unique_selected_corruption_locations=680,
        corruption_note='952 rejections pass mutated observations through the same positive stage validator; preliminary filename-before/API-after checks repeat 272 locations from the final complete-stage comparison',
        actual_API_rows=sum(r['actual_API'] for r in rows), checked_guest_store_rows=sum(r['buffer_stored'] for r in rows),
        declared_stdcall_return_rows=sum(r['stdcall_returned'] for r in rows),
        original_BEFORE_only_guest_expectations=True, stopped_mainargs_AFTER_used_as_seed=False,
        frozen_writer_AFTER_validated_against_independent_BEFORE_source_model=True,
        new_API_witness_only_supplies_declared_native_service_effects=True,
        mutable_current_candidate_expected_code_imported=False,
        generic_catch_fault_uses_current_State_PC_and_default_address0=True,
        real_entry_job_40B_fault_schema=True,
        actual_unit_API_module_seed_filename_witness_checked=True,
        full_state_pages_and_ledgers_preserve_fault_partial_order=True,
        explicit_recovered_O0_success_and_fresh_O2_native_stage=True,
        code_and_input_physical_bindings_rehashed=True,
        original_executed_by_auditor=False, native_executed_by_auditor=False, observer_rerun_by_auditor=False,
        game_launched=False, argument_environment_initialized=False, whole_M4_complete=False,
        superseded_attempts='Observer1 generic-catch PC/address and observer2 nonexistent writer-job predictions failed and remain preserved; final source semantics corrected without candidate changes',
        limitations=['Native filename and immediate LastError are actual OS service witnesses for the AMD64 worker, with an explicit representative guest State ABI; no original x86 volatile-callee equality or guest TEB initialization.',
                     'The initialized command-line global load at7800BBD6 remains refused before the load/EAX publication; no parser/argv/environment/full CRT/full M4 execution credit.',
                     'Serial owned capture publication and no concurrent flat writers are assumed; stage receipts are source/artifact associations, not process file-open attestation.'])
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    bind(out / 'report.json')
    (out / 'pins.json').write_text(json.dumps(dict(files=pins), indent=2) + '\n')
    print(json.dumps(dict(passed=True, report_sha256=sha(out/'report.json'), pins_sha256=sha(out/'pins.json'),
                         physical_associations=len(pins), unique_corruption_locations=680)))


if __name__ == '__main__': main()
