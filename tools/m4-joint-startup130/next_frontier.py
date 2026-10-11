"""Derive the full remaining144-table scope from an actually accepted130 gate."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def main(acceptance_path, acceptance_sha256, name):
    out = ROOT / 'reports/m4-joint-startup130-root' / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        assert path.suffix.lower() not in ('.mwb', '.zip')
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert expected is None or actual == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == actual
        pins[str(path)] = actual
        return path

    accepted = json.loads(pin(acceptance_path, acceptance_sha256).read_bytes())
    assert accepted['passed'] is True and accepted['connected_roots'] == 130
    assert accepted['remaining_inventory_roots'] == 14
    assert accepted['whole_M4_complete'] is False
    gate = accepted['gates']['preparation']
    prepared = json.loads(pin(ROOT / gate['path'], gate['sha256']).read_bytes())
    module = importlib.util.spec_from_file_location('frontier130_pe', pin(ROOT / 'tools/analysis/pe.py'))
    loader = importlib.util.module_from_spec(module)
    module.loader.exec_module(loader)
    pe = loader.PEImage(pin(ROOT / 'MW3/Mech3.exe',
        '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    table = [dict(slot=slot, entry=pe.rva_u32(slot - pe.image_base))
             for slot in range(0x5e0000, 0x5e0244, 4)]
    table = [row for row in table if row['entry']]
    assert len(table) == 144
    selected = prepared['selected_order']
    entries = {row['entry'] for row in selected}
    assert len(selected) == len(entries) == 130 and all(row in table for row in selected)
    classification = json.loads(pin(ROOT / 'reports/m4-service-initializers/static-r1/root-classification.json').read_bytes())
    inventory = {row['entry']:row for row in classification['roots']}
    assert len(inventory) == 144
    remaining = [inventory[row['entry']] for row in table if row['entry'] not in entries]
    assert len(remaining) == 14
    graphs = json.loads(pin(ROOT / 'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json',
        'da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
    physical = {}
    empty = set()
    for root in remaining:
        assert dict(slot=root['slot'], entry=root['entry']) in table
        for entry in root['local_entries']:
            rows = graphs[str(entry)]['instructions']
            if not rows:
                empty.add(entry)
            for row in rows:
                raw = bytes.fromhex(row['bytes'])
                offset, _ = pe.rva_range(row['pc'] - pe.image_base, len(raw))
                assert pe.data[offset:offset + len(raw)] == raw
                assert row['pc'] not in physical or physical[row['pc']] == raw
                physical[row['pc']] = raw
    groups = collections.defaultdict(list)
    for root in remaining:
        groups[tuple(root['imports'])].append(root['entry'])
    path = out / 'remaining-roots.json'
    path.write_text(json.dumps(remaining, indent=2) + '\n')
    pin(path)
    pin(__file__)
    counts = dict(remaining_roots=14,
        roots_with_FS_sites=sum(bool(r['FS_sites']) for r in remaining),
        roots_with_FP_sites=sum(bool(r['FP_sites']) for r in remaining),
        roots_with_unresolved_controls=sum(bool(r['unresolved_controls']) for r in remaining),
        unique_recovered_physical_instruction_rows=len(physical),
        unique_recovered_physical_instruction_bytes=sum(map(len, physical.values())))
    report = dict(passed=True, scope='Exact physical144 initializer table minus accepted130',
        acceptance_sha256=acceptance_sha256, counts=counts,
        service_groups=[dict(imports=list(k), count=len(v), roots=v)
                        for k,v in sorted(groups.items(), key=lambda r:(-len(r[1]), r[0]))],
        zero_instruction_entries_requiring_focused_recovery=sorted(empty),
        next_scopes=['MFC1168 genuine TLS/current-thread provider and _setmbcp(-3)',
                     'Two actual _hypot cdecl boundaries and literal x87 game source',
                     'Shared object constructors, vector construction and exact vtable dispatch',
                     'Font, file-version, registry and loader dependencies'],
        static_graph_completeness_claimed=False, original_executed=False,
        native_executed=False, initializer_credit=0, whole_M4_complete=False, files=pins)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    pin(path)
    print(json.dumps(dict(passed=True, report=str(path), sha256=pins[str(path)], counts=counts)))


if __name__ == '__main__':
    main(*sys.argv[1:])
