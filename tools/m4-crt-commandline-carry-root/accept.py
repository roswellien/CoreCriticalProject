"""Final current dependency union; historical receipts do not expand stale pins."""
import json
import sys
import time
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, verify_manifest, unique_object
from paths import publish_bytes, workspace_path
from stages import verify_stage
BASE = ROOT / 'reports/m4-crt-commandline-carry'
RECEIPTS = {
    'build': ('build-r6/build.json', '10969868ff59f5bd1c37b60065b2329d0649785ab3a5d48763696fe846759ce9'),
    'author_submission': ('author-submission-r1/report.json', '00b5f4a5dcdd1ed0b3305093c79a0ddc7c26a5c75c69e138fd65214a821e3f5c'),
    'author_execution': ('execution-r3/report.json', '940fc08016124ca13a21eb105eacea605f7f6b312707707f44064bdfe0ab9574'),
    'root_execution': ('root-execution-r1/report.json', '930355cc98ecb11eb7f9d57621b69fd9fa9c0ac1df8a14deee363738efa32bf9'),
    'root_source_model': ('root-observer-r2/report.json', '7aa5faba4b659d03dfa2b86c289876e64ae4af6c4ff417bd2711accc417410d0'),
    'independent_source': ('source-contract-r2/report.json', 'be9fb846df9d78448298310274af19fd43463fcbadf1787df680626adb362cf0'),
    'independent_root_model': ('independent-root-model-audit-r1/report.json', 'c1bd08f5775bd0f9a9e9b55b76d8a8afd270bf912b46aa445e07eb0b3e601cfc'),
}
PINS = {
    'source-contract-r2/pins.json': '126647e98358f580104709ac33128db1ece2b76424420fbb856837ecf4841c9b',
    'independent-root-model-audit-r1/pins.json': '8f95f636c75f6c2a25dccab8416804c10210d0cffdb0e148dcebdbed23c5771f',
}

def need(ok, why):
    if not ok:
        raise ValueError(why)

def main(config_path, config_sha, directory):
    out = workspace_path(directory, reports=True)
    need(not out.exists() and out.parent == BASE, 'Fresh root acceptance output required')
    started = time.perf_counter_ns()
    files, receipts, values = {}, {}, {}

    def add(path, expected=None):
        path = Path(path).absolute()
        digest = sha_file(path) if expected is None else expected
        key = normalized(str(path))
        need(key not in files or files[key] == digest, 'Conflicting current dependency: ' + key)
        files[key] = digest
        return path

    config_path = add(config_path, config_sha)
    need(sha_file(config_path) == config_sha, 'External compiled evidence admission SHA')
    config = json.loads(config_path.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    need(set(config) == {'receipts', 'pins', 'compiled_assertions'}, 'Exact final compiled evidence admission schema')
    need(set(config['compiled_assertions']) == {'independent_compiled', 'independent_hardware'},
         'Both meaningful independent compiled admission domains required')
    combined = dict(RECEIPTS)
    for name, binding in config['receipts'].items():
        need(name not in combined, 'Unambiguous independent receipt name')
        combined[name] = tuple(binding)
    need({'independent_compiled', 'independent_hardware'} <= combined.keys(), 'Actual compiled and hardware proof required')
    for name, (relative, digest) in combined.items():
        path = add(BASE / relative, digest)
        need(sha_file(path) == digest, 'External receipt SHA: ' + name)
        value = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
        need(value['passed'], 'Successful current prerequisite: ' + name)
        values[name], receipts[name] = value, dict(path=str(path), sha256=digest)
        for category in ('files', 'sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts', 'input_files'):
            for p, h in value.get(category, {}).items():
                add(p, h)
    combined_pins = dict(PINS)
    for relative, digest in config['pins'].items():
        need(relative not in combined_pins or combined_pins[relative] == digest,
             'Unambiguous fixed and configured independent pins')
        combined_pins[relative] = digest
    for relative, digest in combined_pins.items():
        path = add(BASE / relative, digest)
        need(sha_file(path) == digest, 'External independent pins SHA')
        bindings = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object)['files']
        if isinstance(bindings, dict):
            for p, h in bindings.items():
                add(p, h)
        else:
            need(isinstance(bindings, list) and bindings, 'Explicit record-list manifest schema')
            seen = set()
            for record in bindings:
                need(isinstance(record, dict) and set(record) == {'path', 'size_bytes', 'sha256'},
                     'Exact record-list binding schema')
                p, size, h = record['path'], record['size_bytes'], record['sha256']
                need(isinstance(p, str) and Path(p).is_absolute() and
                     type(size) is int and size >= 0 and isinstance(h, str) and
                     len(h) == 64 and all(c in '0123456789abcdef' for c in h),
                     'Typed absolute record-list binding')
                key = normalized(p)
                need(key not in seen, 'Unique record-list physical binding')
                seen.add(key)
                need(Path(p).stat().st_size == size, 'Record-list file size association')
                add(p, h)
    build_sha = RECEIPTS['build'][1]
    need(values['root_execution']['build_sha256'] == values['author_execution']['build_sha256'] ==
         values['independent_source']['build_sha256'] == build_sha, 'Actual current build association')
    need(values['author_submission']['anchors']['build']['sha256'] == build_sha, 'Submission current build association')
    need(values['independent_source']['preparation_pins_sha256'] ==
         'c4520c939b5cd886180720116cbc6c034719d03d1dc5a565890aca97dbc20105',
         'Final immutable preparation source association')
    need(values['independent_root_model']['root_proof_sha256'] == RECEIPTS['root_source_model'][1] and
         values['independent_root_model']['root_execution_sha256'] == RECEIPTS['root_execution'][1],
         'Final root model audit is associated with this exact source proof and execution')
    model = values['root_source_model']
    need(model['independently_modeled_ordinary_sequences'] == 48 and len(model['rows']) == 48 and
         model['checks'] == 118807 and model['selected_semantic_byte_corruption_denials'] == 2000,
         'Complete strengthened original BEFORE/source model domain')
    need(model['standard_causal_sequences_independently_modeled_by_root'] == 0,
         'No root full-causal-model overclaim')
    need(values['root_execution']['positive_sequences'] == 48 and values['root_execution']['causal_sequences'] == 24 and
         values['author_execution']['positive_sequences'] == 48 and values['author_execution']['causal_negative_sequences'] == 24,
         'Complete declared normal and standard fault execution domain')
    need(values['independent_source']['unchanged_guest_COFF_objects'] == 12 and
         values['independent_source']['unchanged_FDIV_libraries'] == 2 and
         values['independent_source']['new_literal_producer_COFF_objects'] == 2,
         'Prior literal bodies retained; actual new source writer objects')
    for receipt, assertions in config['compiled_assertions'].items():
        need(receipt in ('independent_compiled', 'independent_hardware') and assertions,
             'Explicit meaningful compiled/hardware admission assertions')
        for key, value in assertions.items():
            need(values[receipt].get(key) == value, 'Independent compiled domain: ' + receipt + '/' + key)
    fixture_build = receipts['independent_compiled_build']
    need(Path(values['independent_compiled']['build_path']).absolute() == Path(fixture_build['path']) and
         Path(values['independent_hardware']['compiled_build_path']).absolute() == Path(fixture_build['path']),
         'Both independent reviews bind the admitted actual compiled fixture build')
    for name in ('mfc_recovery', 'mfc_edges', 'mfc_root_check'):
        need(not values[name]['native_execution_credit'], 'MFC workahead remains static')
    locale = values['locale_recovery']
    need(not locale['original_executed'] and not locale['native_executed'] and
         not locale['parser_executed'] and not locale['whole_M4_complete'],
         'Locale workahead remains static')
    for name in ('root_source_model', 'independent_compiled', 'independent_hardware'):
        need(not values[name]['whole_M4_complete'], 'No complete M4 credit')
    source_audit = values['independent_source']
    need(not source_audit['consumer']['parser_body_executed'] and
         not source_audit['original_executed'] and not source_audit['native_worker_executed'] and
         not source_audit['game_launched'], 'Static source association gives no execution credit')
    stage = BASE / 'root-observer-stage-r2'
    need(verify_stage(stage, '658bce741486e612da967797a12c6369cc3a67de0023a5fb3837d5869709b984')['recorded_stage_passed'],
         'Successful complete current oracle stage')
    for p in stage.iterdir():
        if p.is_file():
            add(p)
    bundles = []
    for level, identity in values['root_execution']['levels'].items():
        bundle = add(identity['bundle'], identity['bundle_sha256'])
        with CaptureBundle(bundle, identity['bundle_sha256']) as reader:
            need(len(reader.names()) == identity['logical_files'] == 49266, 'Complete current root archive')
        bundles.append(dict(level=level, path=str(bundle), sha256=identity['bundle_sha256'],
                            logical_files=49266, native_seconds=identity['native_seconds'], pack_seconds=identity['pack_seconds']))
    history = {}
    for relative in ('preparation-r1/report.json', 'preparation-r2/report.json', 'preparation-r3/report.json',
                     'preparation-r4/report.json', 'build-r1/build.json', 'build-r2/build.json', 'build-r3/build.json',
                     'build-r4/build.json', 'build-r5/build.json', 'execution-r1/report.json', 'execution-r2/report.json',
                     'root-observer-r1/report.json', 'root-observer-r1-source-snapshot/observe.py',
                     'root-model-preview-r1/report.json', 'independent-compiled-r1/build.json',
                     'independent-compiled-r2/build.json', 'independent-compiled-r3/build.json'):
        path = add(BASE / relative)
        history[relative] = files[normalized(str(path))]
    for p in Path(__file__).parent.iterdir():
        if p.is_file():
            add(p)
    for relative in ('docs/m4-crt-commandline-carry-review.md', 'docs/m4-mfc-provider-state-workahead.md',
                     'docs/m4-progress-commandline-carry.md'):
        add(ROOT / relative)
    add(sys.executable)
    merge_seconds = (time.perf_counter_ns() - started) / 1e9
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out / 'pins.json', (json.dumps(dict(files=dict(sorted(files.items()))), indent=2) + '\n').encode('utf-8'))
    report = dict(passed=True, scope='Accepted bounded native command-line producer carry and real source continuation to actual parser CALL',
        receipts=receipts, preserved_history=history, bundles=bundles, closure=closure,
        merge_and_admission_seconds=merge_seconds, native_ordinary_sequences=48, standard_fault_sequences=24,
        independent_root_model_checks=118807, independent_root_corruption_rejections=2000,
        independent_compiled_domain=config['compiled_assertions'], root_modeled_standard_causal_sequences=0,
        State_bytes=3504, FX_bytes=512, borrowed_pages=16, source_identity_bytes=1151,
        new_owned_buffer=0x33000000, producer_source_bytes=11, producer_accesses=3,
        consumer_source_bytes=38, consumer_source_instructions=14, consumer_accesses=9,
        real_parser_CALL=0x7800bbf7, next_required_target=0x7800bc48, real_parser_return=0x7800bbfc,
        nonempty_actual_native_commandline_domain=True, native_empty_branch_credit=False,
        authored_late_scheduling_seam=True, original_DllMain_attach_order=False, fragment_guest_RET=False,
        original_IAT_rewrite=False, State_reseed=False, guest_TEB_LastError_initialized=False,
        full_original_x86_API_volatile_equivalence=False, parser_body_or_argv_outputs=False,
        main_initializer_count=27, game_launched=False, original_executed=False, whole_M4_complete=False,
        pins_sha256=sha_file(out / 'pins.json'))
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: v for k, v in report.items() if k not in ('receipts', 'preserved_history', 'bundles', 'independent_compiled_domain')}))

if __name__ == '__main__':
    main(*sys.argv[1:])
