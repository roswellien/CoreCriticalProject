"""Read-only ordinary-file review; never opens capture archives or indexes."""
from pathlib import Path
import ast, hashlib, json, re, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/m4-138-validation-review/ordinary-audit-r1'
files = {}
def pin(path, expected=None):
    path = Path(path).resolve()
    assert path.name not in ('index.json', 'payload.bin', 'transport.json')
    assert path.suffix.lower() not in ('.mwb', '.zip')
    assert path.stat().st_size <= 32 * 1024 * 1024
    with path.open('rb') as stream:
        value = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert expected is None or value == expected, str(path)
    assert str(path) not in files or files[str(path)] == value
    files[str(path)] = value
    return path
def read(relative):
    return json.loads(pin(ROOT / relative).read_text(encoding='utf-8-sig'))
prep = read('reports/m4-startup138-original/validation-preparation-r1/report.json')
admission = read('reports/m4-startup138-original/admitted-controller-r1/report.json')
execution = read('reports/m4-startup138-original/original-execution-r1/report.json')
skipped = []
for report in (prep, admission, execution):
    assert report['passed'] and report['initializer_credit'] == 0
    for path, value in report['files'].items():
        p = Path(path)
        if p.name in ('index.json', 'payload.bin', 'transport.json') or p.suffix.lower() in ('.mwb', '.zip'):
            skipped.append(str(p))
            continue
        pin(p, value)
parent = pin(prep['parent_validator_path'], prep['parent_validator_sha256']).read_text()
validator = pin(prep['validator_path'], prep['validator_sha256']).read_text()
helper = pin(prep['helper_path'], prep['helper_sha256']).read_text()
ast.parse(parent); ast.parse(validator); ast.parse(helper)
deltas = read('reports/m4-startup138-original/validation-preparation-r1/validator-deltas.json')
rebuilt = parent
for delta in deltas:
    assert rebuilt.count(delta['before']) == delta['occurrences']
    rebuilt = rebuilt.replace(delta['before'], delta['after'])
assert rebuilt == validator and len(deltas) == 32
contract = read('reports/m4-startup138-original/preparation-r7/contracts.json')
order = read('reports/m4-startup138-original/preparation-r7/selected-order.json')
normal = read('reports/m4-fps-original/preparation-r1/normal-contracts.json')
bindings = read('reports/m4-startup138-original/preparation-r7/fs-hook-bindings.json')
assert contract['selected_order'] == order and len(order) == 138
assert len(set(row['entry'] for row in order)) == 138
assert [order[i]['entry'] for i in contract['widget_phases']] == contract['widget_roots']
assert set(row['root'] for row in normal['roots']) == set(contract['widget_roots'])
assert len(normal['roots']) == 7 and len({row['PC'] for row in bindings}) == 93
assert (contract['sequences'], contract['phases'], contract['callbacks']) == (6, 828, 108)
assert (138 * 6 * 69 * 2, 138 * 6 * 64 * 2, 137 * 6 * 68) == (114264, 105984, 55896)
observers = read('reports/m4-tree-review/original138-prelaunch-r5/compiled-observers.json')
resolutions = {}
for row in observers:
    for rel in row['relocations']:
        if rel['symbol_section'] == 0 and rel['resolution_kind'] == 'virtual address':
            key, value = rel['symbol'], rel['actual_symbol_address']
            assert key not in resolutions or resolutions[key] == value
            resolutions[key] = value
for symbol in ('_format_entry_strrchr', '_format_entry_malloc', '_format_entry_sprintf', '_fps_entry'):
    assert symbol in resolutions
assert execution['validation_pending'] and execution['original_executed'] and not execution['native_executed']
assert execution['build_sha256'] == prep['build_sha256']
assert execution['preflight_sha256'] == prep['prelaunch_sha256']
pin(__file__)
assert not OUT.exists()
OUT.mkdir(parents=True)
report = dict(
    passed=True, scope='Independent ordinary-file hash/schema/additive-delta review only',
    recommend_running_current_validator=False,
    reason='Repair definite incomplete GDI pair acceptance before fresh validator admission',
    findings=[dict(id='GDI-pair-extent', severity='blocking-review',
        file=str(ROOT/'tools/m4-startup138-original/widget_phase.py'),
        detail='Even count does not force alternating sides: side=h[3]%2, and only side1 requires preceding side0. Consecutive side0 records and a trailing side0 are permitted. Final count gate does not require GDI boundary sides==2*stdcall returns.',
        remedy='Fresh helper/validator version: require side==i%2 for every GDI record and complete per-phase/final pair cardinality.')],
    exact_additive_delta_reconstruction=True, additive_hunks=len(deltas),
    inherited_checks_preserved_by_exact_reconstruction=True,
    schedule_roots=138, phases=828, callbacks=108,
    source_page_endpoints=114264, CRT_page_endpoints=105984, nonstack_carry_relations=55896,
    capture_opened=False, archive_index_opened=False, skipped_capture_paths=sorted(set(skipped)),
    validation_executed=False, original_executed=False, native_executed=False,
    acceptance_credit=0, semantic_source_proof_reviewed=False, files=files)
target = OUT/'report.json'
target.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(path=str(target), sha256=hashlib.sha256(target.read_bytes()).hexdigest(), pins=len(files), skipped=len(set(skipped)), recommendation=report['reason'])))
