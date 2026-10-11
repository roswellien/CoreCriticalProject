"""Physical original144-table frontier after complete selected125 acceptance."""
from pathlib import Path
import collections, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def main(acceptance_path, acceptance_sha256, name):
    out = ROOT / 'reports/m4-joint-startup125-root' / name
    assert not out.exists(); out.mkdir(parents=True); pins = {}
    def pin(path, expected=None):
        path = Path(path).resolve(); actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert expected is None or expected == actual
        assert str(path) not in pins or pins[str(path)] == actual
        pins[str(path)] = actual; return path
    acceptance = json.loads(pin(acceptance_path, acceptance_sha256).read_bytes())
    assert acceptance['passed'] and acceptance['connected_roots'] == 125 and not acceptance['whole_M4_complete']
    item = acceptance['gates']['preparation']; preparation = json.loads(pin(ROOT / item['path'], item['sha256']).read_bytes())
    spec = importlib.util.spec_from_file_location('frontier_PE', pin(ROOT / 'tools/analysis/pe.py'))
    PE = importlib.util.module_from_spec(spec); spec.loader.exec_module(PE)
    pe = PE.PEImage(pin(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    table = [dict(slot=address, entry=pe.rva_u32(address-pe.image_base)) for address in range(0x5e0000, 0x5e0244, 4)]
    table = [row for row in table if row['entry']]; assert len(table) == 144
    selected = preparation['selected_order']; entries = {row['entry'] for row in selected}
    assert len(entries) == len(selected) == 125 and all(row in table for row in selected)
    classification = json.loads(pin(ROOT / 'reports/m4-service-initializers/static-r1/root-classification.json').read_bytes())
    inventory = {row['entry']:row for row in classification['roots']}; assert len(inventory) == 144
    remaining = [inventory[row['entry']] for row in table if row['entry'] not in entries]; assert len(remaining) == 19
    graphs = json.loads(pin(ROOT / 'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json', 'da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
    physical = {}; zero_instruction_entries = set()
    for root in remaining:
        assert dict(slot=root['slot'], entry=root['entry']) in table
        for entry in root['local_entries']:
            instructions = graphs[str(entry)]['instructions']
            if not instructions: zero_instruction_entries.add(entry)
            for row in instructions:
                pc = row['pc']; raw = bytes.fromhex(row['bytes']); offset,_ = pe.rva_range(pc-pe.image_base, len(raw))
                assert pe.data[offset:offset+len(raw)] == raw
                assert pc not in physical or physical[pc] == raw; physical[pc] = raw
    groups = collections.defaultdict(list)
    for root in remaining: groups[tuple(root['imports'])].append(root['entry'])
    counts = dict(remaining_roots=19, roots_with_FS_sites=sum(bool(r['FS_sites']) for r in remaining), roots_with_unresolved_controls=sum(bool(r['unresolved_controls']) for r in remaining), roots_with_FP_sites=sum(bool(r['FP_sites']) for r in remaining), unique_recovered_physical_instruction_rows=len(physical), unique_recovered_physical_instruction_bytes=sum(map(len,physical.values())))
    (out / 'remaining-roots.json').write_text(json.dumps(remaining, indent=2)+'\n'); pin(out / 'remaining-roots.json'); pin(__file__)
    result = dict(passed=True, scope='Exact original144 table minus accepted125; every previously recovered frontier byte physically checked, without treating incomplete/empty static graphs as complete functions', counts=counts, service_groups=[dict(imports=list(key),count=len(value),roots=value) for key,value in sorted(groups.items(),key=lambda r:(-len(r[1]),r[0]))], zero_instruction_entries_requiring_focused_recovery=sorted(zero_instruction_entries), priority='Close the three genuinely observed filename formatting roots4DF610/4E0710/4E0810 with bounded normal narrow CRT source and native contracts; then the three-FCOS initializer4B64F0 and remaining constructor/service families. Retain full original table order and final connected144 acceptance.', static_graph_completeness_claimed=False, native_executed=False, original_executed=False, initializer_credit=0, whole_M4_complete=False, files=pins)
    path = out / 'report.json'; path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True, report=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), counts=counts)))

if __name__ == '__main__': main(*sys.argv[1:])
