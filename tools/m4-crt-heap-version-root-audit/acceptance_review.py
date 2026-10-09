"""Read-only review of the current version-gate admission scripts and sealed inputs."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT/'reports/m4-crt-heap-version-root-audit'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

SCRIPTS = {
    'accept.py': '8fec1ed4a942c892247667cc552d0151bd9dd59fd536fbfade614197142c3c9e',
    'create_config.py': '374fa1bbea4d4b48107ff6d7f9bab9265aa07dd13fc8fef51cb391bf01325e97',
    'final_check.py': 'a1e33721f35f95f2ccc22c3c2a90f817780e9d7192db12dad6ec8f5a759e9191',
}


def need(value, why):
    if not value:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_object)


def main(directory):
    started = time.perf_counter_ns()
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh acceptance-review receipt')
    files = {}

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or actual == digest, 'Exact input digest '+str(path))
        key = normalized(str(path))
        need(key not in files or files[key] == actual, 'Consistent input identity')
        files[key] = actual
        return path

    trees = {}
    for name, digest in SCRIPTS.items():
        path = pin(ROOT/'tools/m4-crt-heap-version-root'/name, digest)
        trees[name] = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    fixed = None
    for node in trees['create_config.py'].body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FIXED' for t in node.targets):
            fixed = ast.literal_eval(node.value)
    need(isinstance(fixed, dict) and len(fixed) == 10, 'Ten fixed available proof domains')
    receipts = {}
    identities = {}
    for name, (path, digest) in fixed.items():
        path = pin(ROOT/path, digest)
        receipts[name] = read(path)
        need(receipts[name]['passed'] is True, 'Successful available proof '+name)
        identities[name] = dict(path=str(path), sha256=digest)

    assertions = 0
    for node in ast.walk(trees['accept.py']):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'equals'):
            continue
        name = ast.literal_eval(node.args[0])
        if name not in receipts:
            continue
        for keyword in node.args[1].keywords:
            wanted = keyword.value
            if isinstance(wanted, ast.Call) and isinstance(wanted.func, ast.Name) and wanted.func.id == 'digest':
                wanted = identities[ast.literal_eval(wanted.args[0])]['sha256']
            else:
                wanted = ast.literal_eval(wanted)
            need(receipts[name].get(keyword.arg) == wanted, 'Current root receipt assertion '+name+'/'+keyword.arg)
            assertions += 1
    need(assertions == 155, 'Exact previously reviewed current-receipt assertions')

    labels = {
        node.args[-1].value for node in ast.walk(trees['accept.py'])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'need'
        and node.args and isinstance(node.args[-1], ast.Constant) and isinstance(node.args[-1].value, str)
    }
    required = {
        'All 38 exact fixture-to-production object paths and hashes',
        'Both exact production FDIV libraries',
        'Exact compiled worker composition',
        'Native worker equals its owning build artifact',
        'Native stage binds exact compiled worker hash',
        'Native closed-output association',
        'Pack stage produces exactly the admitted archive',
        'Exact capture pack request and source tree',
        'Native result and archive exact association',
        'Observer output association',
        'Final independent audit binds actual root proof',
    }
    need(required <= labels, 'All requested association checks implemented')

    build = receipts['build']
    fixture = receipts['compiled_build']
    objects = {}
    for category, entries in fixture.items():
        if category.endswith('_objects'):
            for path, digest in entries.items():
                pin(path, digest)
                key = normalized(path)
                need(key not in objects or objects[key] == digest, 'Consistent fixture object hash')
                objects[key] = digest
    production_objects = {normalized(p): h for p, h in build['entry_objects'].items()}
    need(objects == production_objects and len(objects) == 38, 'Complete exact current 38-object composition')
    libraries = {normalized(p): h for p, h in fixture['libraries'].items()}
    need(libraries == {normalized(p): h for p, h in build['libraries'].items()} and len(libraries) == 2,
         'Both exact current production FDIV libraries')
    for path, digest in fixture['libraries'].items():
        pin(path, digest)
    for domain in (build, fixture):
        need(not any(p.lower().endswith('.md') for p in domain['sources']), 'Current compiled-source scope excludes documentary history')
    pin(build['source_scope_note'], build['source_scope_note_sha256'])

    stage_records = []
    archives = []
    execution = receipts['author_execution']
    need(set(execution['levels']) == {'O0', 'O2'}, 'Both actual author optimization levels')
    for level, info in execution['levels'].items():
        need(normalized(info['worker']) == normalized(build['workers'][level]), 'Exact production worker path')
        worker_hash = {normalized(p): h for p, h in build['artifacts'].items()}[normalized(info['worker'])]
        pin(info['worker'], worker_hash)
        commands = {}
        for role in ('native_stage', 'pack_stage'):
            directory = Path(info[role])
            path = pin(directory/'stage.json')
            verified = verify_stage(directory, files[normalized(str(path))])
            need(verified['recorded_stage_passed'] is True, 'Actual author successful stage')
            command = read(path)
            commands[role] = command
            pin(directory/'stdout.bin')
            pin(directory/'stderr.bin')
            stage_records.append(dict(level=level, role=role, sha256=files[normalized(str(path))], verified=verified))
        native = commands['native_stage']
        packed = commands['pack_stage']
        need([normalized(p) for p in native['argv']] == [normalized(p) for p in info['argv']], 'Exact actual author argv')
        native_inputs = {normalized(p): h for p, h in native['input_sha256'].items()}
        need(native_inputs[normalized(info['worker'])] == worker_hash, 'Native stage current owning worker hash')
        outputs = {normalized(p): h for p, h in native['artifact_sha256'].items()}
        need(outputs[normalized(str(Path(info['argv'][-1])/'COMPLETE'))] == hashlib.sha256(b'COMPLETE').hexdigest(),
             'Native closed output marker association')
        pack_outputs = {normalized(p): h for p, h in packed['artifact_sha256'].items()}
        need(pack_outputs[normalized(info['bundle'])] == info['bundle_sha256'], 'Exact author pack-to-bundle association')
        expected_pack = [str(Path(sys.executable)), str(ROOT/'tools/m4-pipeline/capture_bundle.py'),
                         'pack', info['argv'][-1], info['bundle']]
        need(len(packed['argv']) == 5 and packed['argv'][2] == 'pack'
             and [normalized(packed['argv'][i]) for i in (0, 1, 3, 4)]
             == [normalized(expected_pack[i]) for i in (0, 1, 3, 4)], 'Exact pack argv and source tree')
        pin(info['bundle'], info['bundle_sha256'])
        with CaptureBundle(info['bundle'], info['bundle_sha256']) as capture:
            need(capture.read_bytes('COMPLETE') == b'COMPLETE', 'Closed actual author archive')
            need(len(capture.names()) == info['logical_files'] == 84834, 'Exact author complete archive inventory')
            for row in range(36):
                result = json.loads(capture.read_bytes(f'row-{row}/result.json'), object_pairs_hook=unique_object)
                need(result['passed'] is True and result['scenario'] == row
                     and result['control'] == (0 if row < 24 else row+121), 'Actual author native request sequence')
        archives.append(dict(level=level, path=info['bundle'], sha256=info['bundle_sha256'], logical_files=info['logical_files']))

    proof = receipts['model_audit']['final_root_proof']
    observer_dir = ROOT/'reports/m4-crt-heap-version-root/observe-stage-r2'
    observer_path = pin(observer_dir/'stage.json', 'cbdeac19fd62e215f3137ef3b8639d2186939255f527e90c2a4a254fcef48302')
    verified = verify_stage(observer_dir, files[normalized(str(observer_path))])
    need(verified['recorded_stage_passed'] is True, 'Successful exact final root observer stage')
    observer_outputs = {normalized(p): h for p, h in read(observer_path)['artifact_sha256'].items()}
    need(observer_outputs[normalized(identities['root_model']['path'])] == identities['root_model']['sha256'], 'Root observer artifact association')
    need(proof['execution_sha256'] == identities['author_execution']['sha256']
         and proof['observer_sha256'] == identities['root_model']['sha256']
         and proof['stage_sha256'] == files[normalized(str(observer_path))], 'Independent final audit exact proof linkage')
    pin(observer_dir/'stdout.bin')
    pin(observer_dir/'stderr.bin')
    diagnosis = ROOT/'reports/m4-crt-heap-version-host-review/diagnosis-r1/report.json'
    pin(diagnosis, '231ab4795a86ebda9c33eea33ae78a3aa55ed6bb0120488e6e800928879764f6')
    source = (ROOT/'tools/m4-crt-heap-version-root/create_config.py').read_text()
    need(str(diagnosis.relative_to(ROOT)).replace('\\', '/') in source
         and '231ab4795a86ebda9c33eea33ae78a3aa55ed6bb0120488e6e800928879764f6' in source,
         'Host diagnostic retained by identity-only config history')
    need('Historical receipt identities are retained without reopening their closures.'
         in (ROOT/'tools/m4-crt-heap-version-root/accept.py').read_text(), 'No historical closure expansion')
    refusal = BASE/'acceptance-review-refusal-r1/report.json'
    pin(refusal)
    pin(refusal.with_name('acceptance-review-draft.py'))
    for path in (Path(__file__), Path(sys.executable), ROOT/'tools/m4-pipeline/capture_bundle.py',
                 ROOT/'tools/m4-pipeline/manifests.py', ROOT/'tools/m4-pipeline/paths.py', ROOT/'tools/m4-pipeline/stages.py'):
        pin(path)
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report = dict(
        passed=True, schema='mw34-m4-heap-version-root-acceptance-script-review-v1',
        scope='Read-only current admission-script review and existing available-proof corroboration; independent final corpus comparisons deferred to actual admission',
        script_hashes=SCRIPTS, available_receipt_identities=identities, current_receipt_scalar_assertions=assertions,
        requested_binding_assertions_reviewed=sorted(required), complete_fixture_COFF_entries=38,
        unchanged_FDIV_libraries=2, author_optimization_levels=2, author_native_rows_correlated=72,
        author_strict_archive_records_verified=169668, author_archives=archives,
        successful_author_native_pack_stages_checked=4, verified_stages=stage_records,
        exact_worker_owning_artifact_and_stage_input_binding=True,
        exact_pack_output_and_argv_and_source_tree_binding=True,
        exact_native_COMPLETE_marker_binding=True, independent_controls_archive_association_implemented=True,
        independent_controls_archive_association_executed_by_this_review=False,
        root_observer_and_final_model_audit_association_verified=True,
        historical_receipt_closures_expanded=False, current_compiled_source_documentary_history_excluded=True,
        final_independent_native_hardware_seal_receipt_comparisons_deferred_to_admission=True,
        independent_planned_counts_credited_as_actual_by_this_review=False,
        no_actionable_findings=True, native_or_original_or_API_or_game_executed_by_this_review=False,
        resolved_findings=['Literal pack argv token excluded from absolute path normalization; exact token and argc5 retained'],
        preserved_review_refusal=dict(path=str(refusal), sha256=sha_file(refusal)),
        acceptance_executed_by_this_review=False, root_full_causal_model_claim=False, whole_M4_complete=False,
        documents_final_aggregate_counts_not_reviewed_here=True, files=files, physical_closure=closure,
        pins_sha256=sha_file(out/'pins.json'), seconds=(time.perf_counter_ns()-started)/1e9,
    )
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'available_receipt_identities', 'verified_stages', 'author_archives')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
