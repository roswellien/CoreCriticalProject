"""Final current-source closure; historical failures do not expand stale manifests."""
import json
import sys
import time
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

BASE = ROOT / 'reports/m4-crt-filename'
RECEIPTS = {
    'build': ('build-r7/build.json', '1868574163cdbce4491afe2217688ef549189f184e20549e31f68e44930fb1d5'),
    'author_submission': ('author-submission-r2/report.json', 'bed371ffc9e955939630e1e0d0546e7a4e7051e09db183604cac3126454bbdea'),
    'root_execution': ('root-execution-r2/report.json', '96840cb525fa731f703cad016b261b149afd862979d0ad633c04316ed28f3ad9'),
    'root_source_model': ('root-observer-r3/report.json', 'cca4a274b6082439222b275429b0860ed76bc9e499cc88d79b784725ac3ff570'),
    'independent_source': ('independent-contract-r2/report.json', 'c5aa78625caba28434e5c49a82fc3b31c731e5db0ffe9cd2e9ccdcc3c176e567'),
    'independent_compiled': ('independent-compiled-review-r1/report.json', '00682e887dc0f2675184843f226b001943f6da58873e7374f2cb963867d78c7e'),
    'independent_hardware': ('independent-compiled-observer-r1/report.json', 'c7bc79bb4de48bbced02640dee378466c3c6c4358632571519fe900c2608db11'),
    'independent_root_model': ('independent-root-model-audit-r1/report.json', 'fdefab31cb5eddbcc3aa82b02b09ca2601fc08968347d8660e9f35bf0875a913'),
}
PINS = {
    'independent-contract-r2/pins.json': '2cf4d931ce35412aca6208a605daf8d835d9408155532e6cf3e61c09b20292fb',
    'independent-root-model-audit-r1/pins.json': '760196909e68e5ace8e124061e6b7a142729f70a0688b6202a8f065c3c7c9cec',
}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def main(directory):
    out = workspace_path(directory, reports=True)
    need(not out.exists() and out.parent == BASE, 'Fresh root acceptance directory required')
    started = time.perf_counter_ns()
    files, receipts, values = {}, {}, {}

    def add(path, expected=None):
        path = Path(path).absolute()
        digest = sha_file(path) if expected is None else expected
        key = normalized(str(path))
        need(key not in files or files[key] == digest, 'Conflicting current dependency SHA: ' + key)
        files[key] = digest
        return path

    for name, (relative, digest) in RECEIPTS.items():
        path = add(BASE / relative, digest)
        need(sha_file(path) == digest, 'External final receipt SHA mismatch')
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        need(value['passed'], 'Failed final prerequisite')
        values[name] = value
        receipts[name] = dict(path=str(path), sha256=digest)
        for group in ('files', 'sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts'):
            for p, h in value.get(group, {}).items():
                add(p, h)
    for relative, digest in PINS.items():
        path = add(BASE / relative, digest)
        need(sha_file(path) == digest, 'Independent current manifest SHA mismatch')
        for p, h in json.loads(path.read_text(encoding='utf-8'))['files'].items():
            add(p, h)
    expected_build = RECEIPTS['build'][1]
    need(values['root_execution']['build_sha256'] == values['independent_source']['build_sha256'] == expected_build,
        'Final source and execution build association')
    need(values['author_submission']['receipts']['build']['sha256'] == expected_build, 'Author submission build association')
    need(values['root_source_model']['positive_sequences'] == values['author_submission']['positive_sequences'] == 48 and
        values['root_source_model']['causal_sequences'] == values['author_submission']['causal_sequences'] == 24,
        'Complete normal and causal proof domain')
    need(len(values['root_source_model']['rows']) == 72 and values['root_source_model']['actual_capacity_units'] == 8,
        'All current rows and capacity units')
    need(values['root_source_model']['checks'] == 107306 and values['root_source_model']['selected_semantic_byte_corruption_denials'] == 952,
        'Source model and shared-validator proof identity')
    need(values['independent_compiled']['scenarios'] == 90 and values['independent_compiled']['checks'] == 3012 and
        values['independent_compiled']['direct_host_records'] == 180 and values['independent_compiled']['malformed_token_denials'] == 28,
        'Independent actual compiled/hardware domain')
    need(values['independent_hardware']['meaningful_corruption_denials'] == 548, 'Independent hardware observation controls')
    need(values['independent_source']['unchanged_guest_COFF_objects'] == 12 and
        values['independent_source']['unchanged_FDIV_libraries'] == 2 and values['independent_source']['unchanged_ancestor_components'] == 11,
        'Prior accepted literal bodies and contexts retained')
    for row in values['root_source_model']['rows']:
        need(not row['required_commandline_read_executed'], 'Uninitialized command-line read received no execution credit')
    for name in ('root_source_model', 'author_submission', 'independent_compiled', 'independent_hardware'):
        need(not values[name]['whole_M4_complete'], 'No whole-M4 credit from this gate')
    need(not values['independent_source']['native_worker_executed'] and not values['independent_source']['game_launched'],
        'Source association audit supplies no execution credit')
    stage = BASE / 'root-observer-stage-r3'
    stage_sha = '9e1ca18d79df0821d8af72b0cba49c17fe75b09dbb8bc6c3c69e01eefe7457a4'
    need(verify_stage(stage, stage_sha)['recorded_stage_passed'], 'Successful root observer stage required')
    for p in stage.iterdir():
        if p.is_file():
            add(p)
    bundle_rows = []
    for level, identity in values['root_execution']['levels'].items():
        bundle = add(identity['bundle'], identity['bundle_sha256'])
        with CaptureBundle(bundle, identity['bundle_sha256']) as reader:
            need(len(reader.names()) == identity['logical_files'] == 39090, 'Complete current bundle logical inventory')
        bundle_rows.append(dict(level=level, path=str(bundle), sha256=identity['bundle_sha256'], logical_files=39090,
            native_seconds=identity['native_seconds'], pack_seconds=identity['pack_seconds'],
            adopted_successful_root_stage=identity['adopted_successful_root_stage']))
    # Historical receipts retain failures and superseded source/build work;
    # they do not supply current source bindings from older headers/observers.
    historical = {}
    for relative in ('root-execution-r1/report.json', 'root-observer-r1/report.json', 'root-observer-r2/report.json',
        'independent-contract-r1/report.json', 'independent-compiled-r1/build.json'):
        path = add(BASE / relative)
        historical[relative] = files[normalized(str(path))]
    for p in (Path(__file__), Path(sys.executable), ROOT / 'tools/m4-crt-filename-root/README.md',
        ROOT / 'docs/m4-crt-filename-review.md', ROOT / 'docs/m4-development-workflow-results.md',
        ROOT / 'docs/project-milestones.md', ROOT / 'docs/roadmap.md', ROOT / 'docs/m4-startup-plan.md'):
        add(p)
    merged_seconds = (time.perf_counter_ns() - started) / 1e9
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out / 'pins.json', (json.dumps(dict(files=dict(sorted(files.items()))), indent=2) + '\n').encode('utf-8'))
    report = dict(passed=True, scope='Accepted bounded actual native filename service and real compiled startup continuation to required command-line producer',
        receipts=receipts, preserved_history=historical, bundles=bundle_rows, closure=closure,
        merge_and_admission_seconds=merged_seconds, positive_sequences=48, causal_sequences=24,
        actual_API_capacity_units=8, root_model_checks=107306, root_semantic_validator_rejections=952,
        distinct_semantic_mutation_locations=680, ordinary_host_pairs=146, independent_compiled_scenarios=90,
        independent_compiled_checks=3012, independent_rich_host_pairs=180, strict_token_denials=28,
        independent_hardware_corruption_denials=548, State_bytes=3504, FX_bytes=512, borrowed_pages=16,
        source_identity_bytes=1140, next_required_PC=0x7800bbd6, next_required_address=0x78037174,
        commandline_read_executed=False, actual_native_NULL_module_identity=True,
        guest_original_module_identity_claimed=False, guest_TEB_LastError_written=False,
        State_reseed=False, new_guest_mappings=[], full_x86_API_volatile_equivalence=False,
        argc_argv_environment_outputs=False, mainargs_or_argv_provider_RET=False, main_initializer_count=27,
        original_executed=False, game_launched=False, whole_M4_complete=False,
        pins_sha256=sha_file(out / 'pins.json'))
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: v for k, v in report.items() if k not in ('receipts', 'preserved_history', 'bundles')}))


if __name__ == '__main__':
    main(sys.argv[1])
