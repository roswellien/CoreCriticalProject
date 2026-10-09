"""Read-only association/source audit; never executes either oracle or worker."""
import ast
import hashlib
import json
import ntpath
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-parser-prefix'
PROOF = '7fdae94b6a7c8b0ac612776edb89145731f10c1f5dd4350c282889af34959801'
EXECUTION = '80d7a4766aeffd6242148213559a91cdf5113c3f1004e2243e879b602c72a91c'
STAGE = 'a8b78cdad19c3ab61debcf4971f9439b8cddd5adc6e411bb197a1fedc111b8d6'
BUILD = '215cdc4fc04cbc2163250a1746f1a5d20411bc3f0a57f3680212682c1596654a'
OBSERVER = 'df6400fe5c543f3ca8fc52132f14aa8ae743755f6c6820ce8e7005c0543f49f0'
PARSER = 'eb306a193d8ad078858f9a20afa47d3a5b5bbe2c1ba218c3db4cee378ecb34c8'


def need(value, why):
    if not value:
        raise ValueError(why)


def unique(pairs):
    values = {}
    for k, v in pairs:
        need(k not in values, 'Duplicate JSON key')
        values[k] = v
    return values


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def key(path):
    return ntpath.normcase(ntpath.normpath(str(Path(path).absolute())))


def main():
    out = BASE / 'independent-root-model-audit-r1'
    need(not out.exists(), 'Fresh owned audit output required')
    pins = {}

    def bind(path, expected=None):
        path = Path(path).absolute()
        value = sha(path)
        need(expected is None or expected == value, 'Physical digest changed: ' + str(path))
        need(key(path) not in pins or pins[key(path)] == value, 'Conflicting path digest')
        pins[key(path)] = value
        return path

    proof_path = bind(BASE / 'root-observer-r1/report.json', PROOF)
    execution_path = bind(BASE / 'root-execution-r1/report.json', EXECUTION)
    proof, execution = read(proof_path), read(execution_path)
    need(proof['passed'] and execution['passed'], 'Actual matching successful proof and capture')
    for receipt in (proof, execution):
        for path, digest in receipt['files'].items():
            bind(path, digest)
    sources = {}
    for name, digest in {
        'observe.py': OBSERVER, 'parser.py': PARSER,
        'model.py': '3614f7b417afd56f40a4f79122c15cd3e1d19508886a5b6172e85b0119750696',
        'consumer.py': '01c0c248f00785acb73b5c1ce96f2ddda1b675db6c60a0602bf04c175b1b48a8',
    }.items():
        sources[name] = bind(ROOT / 'tools/m4-crt-parser-prefix-root' / name, digest).read_text()
        ast.parse(sources[name])
    observer, parser, model, consumer = (sources[n] for n in ('observe.py', 'parser.py', 'model.py', 'consumer.py'))
    bind(ROOT / 'tools/m4-crt-parser-prefix-root/run.py')
    stage_path = bind(BASE / 'root-observer-stage-r1/stage.json', STAGE)
    stage = read(stage_path)
    need(stage['passed'] and stage['format'] == 'mw34.stage.v1' and stage['status'] == 'success' and
         stage['inputs_stable'] and not stage['command_shell_used'] and not stage['process_file_open_attestation'],
         'Successful stable-input direct observer stage, with no process-file-open claim')
    need(key(Path(stage['cwd']) / stage['argv'][1]) == key(ROOT / 'tools/m4-crt-parser-prefix-root/observe.py') and
         stage['required_outputs'] == [str(proof_path)] and stage['elapsed_seconds'] >= 0,
         'Exact final observer request/output/timing association')
    for group in ('input_sha256', 'final_input_sha256', 'artifact_sha256'):
        for path, digest in stage[group].items():
            bind(path, digest)
    bind(stage_path.with_name('stdout.bin'), stage['stdout_sha256'])
    bind(stage_path.with_name('stderr.bin'), stage['stderr_sha256'])
    counts = dict(checks=146113, selected_semantic_byte_corruption_denials=2648,
        independently_modeled_ordinary_sequences=48, standard_causal_sequences_independently_modeled_by_root=0,
        State_bytes=3504, FX_bytes=512, borrowed_pages=16, new_owned_buffer=0x33000000,
        parser_source_bytes=436, source_identity_bytes=1587, main_initializer_count=27)
    for name, value in counts.items():
        need(proof[name] == value, 'Exact successful proof count: ' + name)
    for name in ('locale_read_completed', 'parser_RET_executed', 'parser_sizing_complete',
                 'DllMain_or_original_scheduling_recovered', 'State_reseed', 'argument_initialization_complete',
                 'whole_M4_complete', 'game_launched', 'original_executed', 'author_expected_model_imported'):
        need(proof[name] is False, 'Bounded unclaimed scope: ' + name)
    need(proof['source_writer_and_consumer_executed'] and proof['parser_body_executed'] and
         proof['physical_closure']['passed'] and proof['physical_closure']['unique_physical_dependencies'] == 730 and
         not proof['physical_closure']['metadata_only_cache_used'], 'Actual source phases and full current byte/hash closure')
    need(execution['build_sha256'] == BUILD and execution['native_executed_by_root'] and
         execution['native_stages_completed'] == 2 and execution['positive_sequences'] == 48 and
         execution['causal_sequences'] == 24 and not execution['original_executed'] and not execution['game_launched'],
         'Fresh O0/O2 actual candidate capture; root scalar proof remains ordinary-only')
    need(len(proof['rows']) == 48, 'Exactly48 ordinary scalar proof rows')
    for level in ('O0', 'O2'):
        rows = [r for r in proof['rows'] if r['level'] == level]
        need([r['index'] for r in rows] == list(range(24)), 'Exact original per-level input order')
        for row in rows:
            need(row['control'] == 0 and row['producer_source_bytes'] == 11 and
                 row['consumer_source_instructions'] == 14 and row['consumer_memory_accesses'] == 9 and
                 row['parser_source_instructions'] == 23 and row['parser_memory_accesses'] == 16 and
                 row['borrowed_pages'] == 16 and row['owned_bytes'] > 1 and row['parser_CALL_executed'] and
                 row['parser_body_executed'] and not row['locale_read_completed'] and not row['parser_RET_executed'] and
                 row['State3504_FX512'] and row['checkpoints'] == 45, 'Complete bounded actual nonquoted parser row')
    for fragment in (
        'originals = M.R.originals(original_path.read_bytes())',
        'payloads = [M.R.project(v) for v in originals[:24]]',
        "host_bytes == subprocess.list2cmdline(argv).encode('mbcs') + b'\\0'",
        'host_bytes[0] == 0x44', 'before == bytes(memory[0x7803b000][0x3f0:0x4f4])',
        'after[length + 1:] == before[length + 1:]',
        'consumed = consumer_predict(holder, program, host_bytes)',
        'parsed = parser_predict(parser_holder, parser_program, host_bytes)',
        "F.full_stage(row, tag, values, attack and tag.startswith(('commandline-', 'filename-', 'parser-')))",
        "tags == set(phases)", "job[11], job[18], job[19] = len(routes), parsed['stop_PC'], parsed['stop_address']",
        "(row / 'parser-job.bin').read_bytes(), 20", "(row / 'parser-undefined.bin').read_bytes(), 8",
        "(row / 'filename-job.bin').read_bytes(), 22", "(row / 'commandline-job.bin').read_bytes(), 28",
        "(row / 'filename-reason.txt').read_text().strip()", "(row / 'commandline-reason.txt').read_text().strip()",
        "(row / 'mainargs-reason.txt').read_text().strip()", "(row / 'parser-reason.txt').read_text().strip()",
        'closure = verify_manifest(F.PHYSICAL)'):
        need(fragment in observer, 'Reviewed source/witness/whole-stage/metadata seam missing: ' + fragment)
    need('memory = copy.deepcopy(entry.mem)' in consumer and 'cpu = bytes(entry.fx), bytes(entry.runtime_cpu)' in consumer,
         'Consumer starts from independent predicted State/pages/FX and separate stale RuntimeCPU')
    need(model.index('self.raw_store(frame - 4, RETURN)') < model.index("self.r['esp'] = frame - 4") and
         model.index("self.cmd_snapshot('commandline-api-after')") < model.index('self.cmd_owned = True') <
         model.index("self.cmd_snapshot('commandline-buffer-after')") < model.index("self.r['eax'], self.r['esp'] = BUFFER, frame"),
         'Actual producer checked CALL and declared API/allocation/result partial ordering')
    need("struct.pack_into('<I', self.state, 2472, saved_pc)" in model and "struct.pack_into('<I', runtime, 0, BUFFER)" in model,
         'Explicit continuation seam changes savedPC and representative RuntimeEAX only')
    need(consumer.index('write32(address, value)') < consumer.index("r['esp'] = address") and
         consumer.index('write32(address, END)') < consumer.index("r['esp'], pc = address, PARSER"),
         'Consumer PUSH and actual parser CALL write before ESP/PC publication')
    need('state, memory = bytearray(entry.state), copy.deepcopy(entry.mem)' in parser and
         'fx, cpu = bytes(entry.fx), bytes(entry.runtime_cpu)' in parser, 'Parser expectation derives only from independent consumer machine')
    need(parser.index('write(address, r[operands[0]])') < parser.index("r['esp'] = address") and
         parser.index("read(r['ecx'], 4)\n            write(r['ecx'], 0)") < parser.index('flags = logical(0)'),
         'Parser PUSH store-beforeESP and checked AND read/store-beforeflags')
    need('flags & ~0x8d4' in parser and 'r[\'edx\'] = (r[\'edx\'] & 0xffffff00) | value' in parser and
         "r['ebx'] = r['edx'] & 255" in parser and "address = TABLE + r['ebx']" in parser,
         'Original INC CF preservation, DL merge, MOVZX lead byte and first typed table address')
    need(parser.index('if pc == 0x7800bce6:') < parser.index("if op == 'push':") and
         "snapshot('parser-locale-before')" in parser and "snapshot('parser-after')" in parser and
         'stop_PC=pc, stop_address=address, locale_read_completed=False' in parser,
         'Stop before locale load, flags, guestRET or sizing completion')
    need('do not assert' in parser and 'original x86 values for architecturally undefined flags' in parser,
         'Concrete translated AF representative scope remains explicit')
    need('tools/m4-crt-parser-prefix/observe.py' not in observer + parser + model + consumer and
         'changed != value' not in observer, 'No candidate expected-model import or tautological corruption count')
    frozen = bind(ROOT / 'tools/m4-crt-filename-root/observe.py',
                  '405797301b25103cdc27dd0635e93e169a4ef86f415afb7c8a431da23703733e')
    text = frozen.read_text()
    need('validate_stage_record(actual, expected, tag)' in text and
         'validate_stage_record(corrupted, expected, tag)' in text and 'except AssertionError:' in text,
         'Positive and altered dictionary stages use the identical frozen semantic validator')
    bind(ROOT / 'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',
         'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2')
    bind(BASE / 'source-contract-r2/report.json', '5cecb09b9f02aeddfb9a5488a144b8f1ba8e28a9ab7d1cfd413505bb1b41e40e')
    bind(BASE / 'source-contract-r2/pins.json', '3ce0d6c3c60d04a03ae21eba50189b528ab13a14964f11ab09cffc5199587781')
    bind(ROOT / 'reports/m4-crt-commandline-carry/independent-root-model-audit-r1/report.json',
         'c1bd08f5775bd0f9a9e9b55b76d8a8afd270bf912b46aa445e07eb0b3e601cfc')
    # Only reader/stage validation runs. No source interpreter, observer or
    # worker is imported or executed. All bundle bytes are verified by the
    # same strict frozen reader; count the selected existing locations only.
    sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
    from capture_bundle import CaptureBundle
    from stages import verify_stage
    positions = set()
    verify_stage(stage_path.parent, STAGE)
    for level, identity in execution['levels'].items():
        for kind in ('native_stage', 'pack_stage'):
            directory = Path(identity[kind])
            verify_stage(directory, pins[key(directory / 'stage.json')])
        with CaptureBundle(identity['bundle'], identity['bundle_sha256']) as reader:
            need(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Fully bound completed archive')
            for name in reader.names():
                parts = name.split('/')
                if len(parts) == 3 and parts[0] == 'row-0' and parts[1].startswith(('commandline-', 'filename-', 'parser-')):
                    value = reader.read_bytes(name)
                    for offset in sorted({0, len(value) - 1}):
                        if offset >= 0:
                            positions.add((level, parts[1], parts[2], offset))
    need(len(positions) == 2648, '2648 distinct actual selected stage-byte corruption locations')
    bind(Path(__file__))
    for path, digest in list(pins.items()):
        need(sha(path) == digest, 'Final stable current physical association: ' + path)
    out.mkdir()
    (out / 'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))), indent=2) + '\n')
    report = dict(passed=True, scope='Independent read-only audit of final original-BEFORE ordinary parser source model and current execution/observer association; no model or native rerun',
        root_proof_sha256=PROOF, root_execution_sha256=EXECUTION, root_observer_stage_sha256=STAGE,
        observer_sha256=OBSERVER, parser_model_sha256=PARSER, candidate_build_sha256=BUILD,
        pins_sha256=sha(out / 'pins.json'), physical_associations=len(pins), **counts,
        original_BEFORE_only_machine_expectation=True, native_AFTER_used_as_machine_seed=False,
        actual_OS_witnesses_only_supply_declared_service_inputs_or_results=True,
        current_model_and_consumer_exact_frozen_carry_identity=True,
        whole3504State_512FX_16pages_1587source_and_ownedbytes_checked=True,
        separate_stale_generic_RuntimeCPU_predicted=True, exact45checkpoints_per_ordinary_row=True,
        parser_completed_accesses=16, parser_PC_count_including_unperformed_table_test=23,
        parser_route_events=3, explicit_TEST_undefined_AF_representative_sites=2,
        checked_PUSH_CALL_store_beforeESP=True, checked_AND_read_store_beforeflags=True,
        source_read_beforeMOV_CMP_result_publication=True, INC_preserves_CF=True,
        normal_filename22word_commandline28word_parser20word_and_firstreasons_checked=True,
        mainargs_required_fault_site=0x7800bce6, mainargs_required_fault_address=0x78037a25,
        commandline_completed_without_synthetic_fault=True,
        unique_shared_validator_stage_byte_corruption_locations=len(positions),
        oracle_rerun_by_auditor=False, native_executed_by_auditor=False, original_executed=False,
        game_launched=False, locale_read_completed=False, parser_RET_executed=False,
        parser_sizing_complete=False, argument_environment_initialized=False, whole_M4_complete=False,
        limitations=[
            'Root source equality covers48ordinary rows.24actual standard injected native causal rows require the separate compiled-review gate; no full causal source model is claimed.',
            'The measured native command lines are nonempty, unquoted and D-leading; no quoted or empty native execution credit.',
            'AF at architecturally undefined sites follows the declared concrete translation policy; originalx86 undefined AF equality is not claimed.',
            'Two actual OS witnesses and representative guest API State effects do not recover originalx86 volatile registers or DLL process-attach scheduling.',
            'Real local count stores and a real parser frame precede the unperformed locale-table load; no completed sizing, RET, argv/env, fullCRT, window/menu or fullM4 credit.',
            'Serial immutable published captures/source are assumed; stage associations are not process-file-open attestation.'])
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, report_sha256=sha(out / 'report.json'), pins_sha256=report['pins_sha256'],
                         current_physical_associations=len(pins), selected_stage_corruption_locations=len(positions))))


if __name__ == '__main__':
    main()
