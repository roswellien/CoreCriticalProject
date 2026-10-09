"""Root closure for the reviewed toolkit, measured transport and static work map."""
import json
import sys
from pathlib import Path
from capture_bundle import sha_file
from manifests import normalized, verify_manifest
from paths import ROOT, publish_bytes, workspace_path
from stages import verify_stage

RECEIPTS = {
    'pipeline_review': ('reports/m4-pipeline-review/review-r4/report.json', '4e0f65fee5075a960a99ead64c7adfc7a95b5e468b9c7aca96f110dc078a37a9'),
    'transport_benchmark': ('reports/m4-pipeline/benchmark-r3/report.json', 'facab85b14e42f2cf324581035fab399e7a87f1bf36ba4f751caa4426d6d1792'),
    'workahead_root_check': ('reports/m4-application-workahead/root-check-r1/report.json', 'ab4ed89537c0d25e109e772c7a322d6a0b0e7cc9a6a831c45c871f95aa874d88'),
}


def main(directory):
    output = workspace_path(directory, reports=True)
    if output.exists() or output.parent != ROOT / 'reports/m4-pipeline':
        raise ValueError('Fresh workflow acceptance directory required')
    files, receipts, documents = {}, {}, {}

    def add(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path) if digest is None else digest
        key = normalized(str(path))
        if key in files and files[key] != actual:
            raise ValueError('Conflicting dependency SHA: ' + key)
        files[key] = actual
        return path

    for label, (relative, expected) in RECEIPTS.items():
        path = add(ROOT / relative, expected)
        if sha_file(path) != expected:
            raise ValueError('Independent receipt SHA changed')
        value = json.loads(path.read_text(encoding='utf-8'))
        if not value['passed']:
            raise ValueError('Independent receipt did not pass')
        documents[label] = value
        receipts[label] = dict(path=str(path), sha256=expected)
        for p, h in value.get('files', {}).items():
            add(p, h)
    review = documents['pipeline_review']
    benchmark = documents['transport_benchmark']
    work = documents['workahead_root_check']
    if len(review['checks']) != 9161 or not all(c['passed'] for c in review['checks']):
        raise ValueError('Independent toolkit checks changed')
    if benchmark['logical_files'] != 2945 or benchmark['repetitions'] != 3 or benchmark['original_executed'] or benchmark['native_executed']:
        raise ValueError('Transport benchmark scope changed')
    for row in benchmark['rows']:
        stage = Path(row['bundle_path']).parent / ('pack-' + row['label'])
        verify_stage(stage, sha_file(stage / 'stage.json'))
    inventory = work['inventory']
    add(inventory['path'], inventory['sha256'])
    if inventory['sha256'] != 'e7a8902f7e51e13244205e7aa137470f53f5544322d9094d3f0f937c0e892dc1':
        raise ValueError('Static work map identity changed')
    pins_path = add(ROOT / 'reports/m4-application-workahead/root-check-r1/pins.json',
        '0d0b26477e3244cdfd4b643fb128000b2e69ea97d4304406f2a1a00b3f01b502')
    if sha_file(pins_path) != files[normalized(str(pins_path))]:
        raise ValueError('Work map bindings changed')
    for value in json.loads(pins_path.read_text(encoding='utf-8'))['bindings']:
        add(value['path'], value['sha256'])
    if work['counts']['batches'] != 13 or work['counts']['selected_bodies'] != 90 or len(work['corruption_denials']) != 14:
        raise ValueError('Work map validation scope changed')
    for path in (Path(__file__), Path(sys.executable), ROOT / 'tools/m4-pipeline/README.md',
        ROOT / 'docs/m4-development-workflow.md', ROOT / 'docs/m4-application-workahead.md'):
        add(path)
    closure = verify_manifest(files)
    output.mkdir()
    publish_bytes(output / 'pins.json', (json.dumps(dict(files=dict(sorted(files.items()))), indent=2) + '\n').encode('utf-8'))
    report = dict(passed=True, scope='Root acceptance of reusable evidence toolkit, bounded transport benchmark and static application work map',
        receipts=receipts, closure=closure, pipeline_checks=9161, frozen_logical_roundtrips=2945,
        warm_read_ratio=benchmark['measured_warm_read_ratio'], work_batches=13, selected_static_bodies=90,
        workahead_corruption_denials=14, actual_junction_fixture_credit=False,
        semantic_equivalence_supplied_by_transport=False, original_executed=False,
        native_executed_by_this_seal=False, game_launched=False, whole_M4_complete=False,
        pins_sha256=sha_file(output / 'pins.json'))
    publish_bytes(output / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(report))


if __name__ == '__main__':
    main(sys.argv[1])
