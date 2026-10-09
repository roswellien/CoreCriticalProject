"""Focused read-only review of the narrow failed-sample admission revision."""
import ast
import difflib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT/'reports/m4-crt-heap-version-root-audit'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

SCRIPTS = {
    'accept.py': '8fec1ed4a942c892247667cc552d0151bd9dd59fd536fbfade614197142c3c9e',
    'accept_v2.py': '7bef4900a710ed36952c3107ce020c3646dc38ff3b6b221c8502812a498af97b',
    'create_config.py': '374fa1bbea4d4b48107ff6d7f9bab9265aa07dd13fc8fef51cb391bf01325e97',
    'final_check.py': 'a1e33721f35f95f2ccc22c3c2a90f817780e9d7192db12dad6ec8f5a759e9191',
}
FINAL = {
    'compiled_native': ('reports/m4-crt-heap-version-review/native-r2/report.json', '14d243d38367abf3160a65808d32659ee25acbf88bf58c0479442daad10582b9'),
    'hardware_review': ('reports/m4-crt-heap-version-review/check-r2/report.json', 'bc78018542801e696181d4a6a59506758a79673c7535023fdee4b1564e685981'),
    'independent_seal': ('reports/m4-crt-heap-version-review/sealed-r1/report.json', '0bc51c080d3756241fd9f70a4d9ea1ccc38eb7688e2e25e80fa6062e2e0dca51'),
}
HISTORICAL = {
    normalized(str(ROOT/'reports/m4-crt-heap-version-review/native-r1/actual-O0/case-47/writer-host-before.bin')):
        '2249e4ddeee6333aac29b3a60af606241067de4286f21cd873510032d0ce767d',
    normalized(str(ROOT/'reports/m4-crt-heap-version-review/native-r1/actual-O0/case-47/writer-host-after.bin')):
        'c272aeb3a1ea03cb19c14a26d690318410c7e68998426c258f6015185c5c92a4',
}


def need(value, why):
    if not value:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_object)


def main(directory):
    started = time.perf_counter_ns()
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh focused revision receipt')
    files = {}

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or actual == digest, 'Fixed revision input '+str(path))
        key = normalized(str(path))
        need(key not in files or files[key] == actual, 'Consistent current physical identity')
        files[key] = actual
        return path

    text = {}
    trees = {}
    for name, digest in SCRIPTS.items():
        path = pin(ROOT/'tools/m4-crt-heap-version-root'/name, digest)
        text[name] = path.read_text(encoding='utf-8')
        trees[name] = ast.parse(text[name], filename=str(path))
    previous_path = pin(BASE/'acceptance-review-r1/report.json', '1c2781d03d27b32a3bebf68018a568af31bff1c3870ec403d25235e4a19c4efd')
    previous = read(previous_path)
    need(previous['passed'] is True and previous['current_receipt_scalar_assertions'] == 155,
         'Previous sealed script review retained')
    for name in ('accept.py', 'create_config.py', 'final_check.py'):
        need(previous['script_hashes'][name] == SCRIPTS[name], 'Previously reviewed root script unchanged')

    fixed = None
    for node in trees['create_config.py'].body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FIXED' for t in node.targets):
            fixed = ast.literal_eval(node.value)
    need(isinstance(fixed, dict) and len(fixed) == 10, 'Unchanged ten fixed current receipt domains')
    identities = {}
    values = {}
    for name, (rel, digest) in {**fixed, **FINAL}.items():
        path = pin(ROOT/rel, digest)
        values[name] = read(path)
        need(values[name]['passed'] is True, 'Successful actual current receipt '+name)
        identities[name] = dict(path=str(path), sha256=digest)

    assertions = 0
    for node in ast.walk(trees['accept_v2.py']):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'equals'):
            continue
        name = ast.literal_eval(node.args[0])
        for keyword in node.args[1].keywords:
            wanted = keyword.value
            if isinstance(wanted, ast.Call) and isinstance(wanted.func, ast.Name) and wanted.func.id == 'digest':
                wanted = identities[ast.literal_eval(wanted.args[0])]['sha256']
            else:
                wanted = ast.literal_eval(wanted)
            need(values[name].get(keyword.arg) == wanted, 'Actual v2 current receipt assertion '+name+'/'+keyword.arg)
            assertions += 1

    seal = values['independent_seal']
    hardware = values['hardware_review']
    native = values['compiled_native']
    expected = dict(native_scenarios=196, actual_hardware_pairs=396, malformed_token_denials=40,
        new_guest_objects=8, reused_guest_objects=30, declared_initial_lower_stack_patterns=6,
        author_controls_per_optimization=12, independent_controls_per_optimization=80,
        counterfactual_direct_host_failure_queries=4, actual_HeapCreate_calls=148,
        actual_successful_HeapDestroy_calls=148, actual_integrated_GetVersionExA_calls=82,
        actual_output_DWORD_commits=1934, actual_selector_RETs=20, synthetic_API_results=False,
        alternate_query_branch_live_coverage=False, full_causal_source_model_oracle=False,
        original_executed=False, ordinary_game_launched=False, whole_M4_complete=False)
    for key, value in expected.items():
        need(seal[key] == value, 'Actual independent aggregate/'+key)
    for key in ('actual_HeapCreate_calls', 'actual_successful_HeapDestroy_calls',
                'actual_integrated_GetVersionExA_calls', 'actual_output_DWORD_commits', 'actual_selector_RETs',
                'hardware_semantic_denials', 'inventory_request_denials'):
        need(seal[key] == hardware[key], 'Exact actual hardware/aggregate count '+key)
    need(seal['native_assertions'] == hardware['native_checks'] == native['native_checks'] == 11042,
         'All actual final assertion totals agree')
    need(native['compiled_sha256'] == identities['compiled_build']['sha256']
         and hardware['native_sha256'] == identities['compiled_native']['sha256'], 'Exact final fixture/native/hardware linkage')
    for role, name in (('source', 'source_contract'), ('audit', 'source_audit'), ('compiled', 'compiled_build'),
                       ('native', 'compiled_native'), ('hardware', 'hardware_review')):
        item = seal['evidence'][role]
        need(normalized(item['path']) == normalized(identities[name]['path'])
             and item['sha256'] == identities[name]['sha256'], 'All five exact final seal evidence domains')

    failure_path = pin(ROOT/'reports/m4-crt-heap-version-review/failed-native-r1/report.json',
                       '33b04d1f74afbbccb3cec2b33fb2f85119e7f1e29ba5837f9a3cef912a701811')
    failure = read(failure_path)
    need(failure['passed'] is False and failure['current_proof_credit'] is False
         and failure['validator_weakened'] is False and failure['current_candidate_entered_at_failure'] is False,
         'Original failed samples retain refusal and receive no current proof credit')
    flat = {normalized(p): h for p, h in seal['files'].items()
            if '/actual-o' in p.replace('\\', '/').lower() and '/case-' in p.replace('\\', '/').lower()}
    need(flat == HISTORICAL, 'Exactly two actual final seal flat files; current proof remains archived')
    failure_files = {normalized(p): h for p, h in failure['files'].items()}
    for path, digest in HISTORICAL.items():
        need(failure_files[path] == digest, 'Exact failed-sample refusal linkage')
        pin(path, digest)
    declared = None
    for node in ast.walk(trees['accept_v2.py']):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'historical_samples' for t in node.targets):
            declared = node.value
    need(isinstance(declared, ast.Dict) and len(declared.keys) == 2, 'Narrow two-file literal admission allowlist')
    need([ast.literal_eval(v) for v in declared.values] == list(HISTORICAL.values()), 'Allowlisted exact two failed byte hashes')
    need('flat_samples == historical_samples' in text['accept_v2.py']
         and "failure['current_proof_credit'] is False" in text['accept_v2.py']
         and "failure['validator_weakened'] is False" in text['accept_v2.py']
         and 'historical_hardware_sample_success_credit=False' in text['accept_v2.py'],
         'Narrow equality and explicit no-success-credit admission assertions')

    for domain in (native, hardware, seal):
        need(domain['full_causal_source_model_oracle'] is False and domain['original_executed'] is False,
             'Actual final source/native proof stays bounded')
    need(hardware['guest_heap_mode_global_published'] is False and seal['guest_heap_mode_global_published'] is False
         and hardware['heap_initialized'] is False and seal['heap_initialized'] is False,
         'Genuine selector return remains before heap publication and completion')
    levels = native['levels']
    need(set(levels) == {'O0', 'O2'} and native['native_checks'] == sum(info['result']['checks'] for info in levels.values()),
         'Exact two-level native assertion aggregate')
    for info in levels.values():
        need(info['result']['passed'] is True and info['result']['scenarios'] == 98
             and info['result']['checks'] == 5521 and info['result']['malformed_token_denials'] == 20
             and info['result']['direct_host_failure_queries'] == 2 and info['logical_files'] == 167696,
             'Actual closed receipt level counts, without archive re-expansion')

    delta = ''.join(difflib.unified_diff(text['accept.py'].splitlines(True), text['accept_v2.py'].splitlines(True),
                                       fromfile='accept.py', tofile='accept_v2.py'))
    for path in (Path(__file__), Path(sys.executable), ROOT/'tools/m4-pipeline/capture_bundle.py',
                 ROOT/'tools/m4-pipeline/manifests.py', ROOT/'tools/m4-pipeline/paths.py'):
        pin(path)
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out/'reviewed.patch', delta.encode())
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report = dict(passed=True, schema='mw34-m4-heap-version-root-focused-acceptance-script-review-v1',
        scope='Focused new admission revision and final receipt counts; unchanged strict archives/full models are not reread',
        script_hashes=SCRIPTS, prior_acceptance_review_sha256='1c2781d03d27b32a3bebf68018a568af31bff1c3870ec403d25235e4a19c4efd',
        current_receipt_scalar_assertions=assertions, unchanged_previously_reviewed_receipt_assertions=155,
        final_independent_receipt_identities={n: identities[n] for n in FINAL},
        exact_failed_hardware_sample_files=HISTORICAL, failed_hardware_samples=2,
        failed_hardware_sample_success_credit=False, failed_hardware_sample_validator_weakened=False,
        fixed_refusal_sha256='33b04d1f74afbbccb3cec2b33fb2f85119e7f1e29ba5837f9a3cef912a701811',
        actual_independent_native_scenarios=196, actual_separate_direct_host_failure_diagnostics=4,
        actual_independent_native_assertions=11042, actual_independent_hardware_pairs=396,
        actual_independent_created_heaps=148, actual_independent_successful_heap_releases=148,
        actual_integrated_GetVersionExA_calls=82, actual_API_output_DWORD_commits=1934,
        actual_source_selector_RETs=20, malformed_token_denials=40, hardware_semantic_denials=548,
        inventory_request_denials=56, final_seal_domains_bound=5,
        actual_final_receipt_counts_now_correlated=True, planned_counts_credited_without_actual_receipts=False,
        strict_current_corpus_remains_archive_only=True, unchanged_archive_records_reread=0,
        full_machine_models_reread=0, no_actionable_findings=True,
        native_original_API_game_or_acceptance_executed_by_this_review=False,
        original_API_or_lower_stack_or_full_causal_equivalence_claimed=False,
        heap_mode_global_published=False, heap_initialized=False, whole_M4_complete=False,
        reviewed_patch_sha256=sha_file(out/'reviewed.patch'), files=files, physical_closure=closure,
        pins_sha256=sha_file(out/'pins.json'), seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'final_independent_receipt_identities')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
