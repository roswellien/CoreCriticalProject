"""Independently constrain the exact adjacent-TIB pure-model repair."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
def main(name):
    out = R / 'reports/m4-tree-review' / name
    assert not out.exists(); out.mkdir(parents=True)
    files = {}
    def pin(p, h=None):
        p = Path(p).resolve(); actual = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h is None or h == actual
        assert str(p) not in files or files[str(p)] == actual
        files[str(p)] = actual; return p
    def receipt(p, h):
        r = json.loads(pin(p, h).read_bytes()); assert r['passed']
        for p, h in r['files'].items(): pin(p, h)
        return r
    receipt(R/'reports/m4-tree-review/joint131-source-preflight-r3/report.json', '52b85902f4d61731ea434ab1c7d479b2458b7190c4367acc9bd419be29b2c0cd')
    p = receipt(R/'reports/m4-joint-startup131-source/preparation-r6/report.json', 'fb90b0dc1d47b9fc89878049100a957d10ad6638bc718e8eff32b04ad861b6f8')
    t = receipt(R/'reports/m4-joint-startup131-source/preflight-r5/report.json', '89ede6938625ccd5c28bbf69f44cb16a2814f94cf9aaa0c70f72564a0dd57297')
    base = R/'tools/m4-joint-startup131'
    for old, new, changes in [('mfc_source.py', 'mfc_source_layout.py', p['layout_changes']), ('mfc_source_v3.py', 'mfc_source_v4.py', p['snapshot_changes']), ('compare_provider_v5.py', 'compare_provider_v6.py', p['reader_changes'])]:
        s = pin(base/old).read_text()
        for change in changes:
            assert s.count(change['before']) == 1
            s = s.replace(change['before'], change['after'])
        assert s == pin(base/new).read_text()
    layout = (base/'mfc_source_layout.py').read_text()
    # Two four-byte computed inputs join exactly once; source invocation and
    # every capture comparison remain those of the frozen base extension.
    assert p['normalized_span'] == [0x7ffde004, 8]
    assert p['original_spans'] == [[0x7ffde004, 4], [0x7ffde008, 4]]
    assert len(p['layout_changes']) == 2 and len(p['snapshot_changes']) == 4
    assert len(p['reader_changes']) == 1
    assert p['reader_changes'][0] == dict(before='import mfc_source_v3 as MF', after='import mfc_source_v4 as MF')
    assert 'original_layout={a:len(b)for a,b in machine.memory.items()}' in layout
    assert 'first=machine.bytes(0x7ffde004,4);second=machine.bytes(0x7ffde008,4);joined=first+second' in layout
    assert 'eq(joined,machine.bytes(0x7ffde004,8)' in layout
    assert 'del literal_memory[0x7ffde008]' in layout
    assert 'for address,size in original_layout.items():machine.store_bytes(address,computed.bytes(address,size))' in layout
    assert "eq({a:len(b)for a,b in machine.memory.items()},original_layout" in layout
    assert not p['nonTIB_memory_change'] and p['persistent_original_layout_restored']
    assert not p['candidate_AFTER_machine_seed'] and not p['per_phase_BEFORE_machine_seed']
    wrapper = (base/'mfc_source_v4.py').read_text()
    assert not any(isinstance(n, ast.Name) and n.id in ('archive', 'DirectSet') for n in ast.walk(ast.parse(wrapper)))
    assert wrapper.index('memory={a:bytes(b)') < wrapper.index('result=L.Extension.phase')
    assert "machine._source_undefined_flags=dict(result['final_undefined_flags'])" in wrapper
    assert not t['capture_reader_opened'] and not t['worker_executed']
    pure = json.loads(pin(Path(R/'reports/m4-joint-startup131-source/preflight-r5/pure-TIB-layout-equivalence.json')).read_bytes())
    assert pure['synthetic_transport'] and not pure['native_API_lifecycle_or_phase_claim']
    w = pure['witness']; assert len(w) == 1
    assert w[0]['address'] == 0x7ffde004 and w[0]['literal_extent'] == 8
    assert [(r['address'], r['bytes']) for r in w[0]['original_parts']] == [(0x7ffde004,4),(0x7ffde008,4)]
    assert ''.join(r['BEFORE_hex'] for r in w[0]['original_parts']) == w[0]['joined_BEFORE_hex']
    assert ''.join(r['source_AFTER_hex'] for r in w[0]['source_AFTER_parts']) == w[0]['source_AFTER_joined_hex']
    assert w[0]['persistent_original_layout_restored'] and not w[0]['candidate_BEFORE_seed']
    assert pure['original_region_inventory'][str(0x7ffde004)] == pure['original_region_inventory'][str(0x7ffde008)] == 4
    assert [r['PC'] for r in pure['source_normal_boundaries']] == [0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca]
    pin(__file__)
    for q,h in files.items(): assert hashlib.sha256(Path(q).read_bytes()).hexdigest() == h
    r = dict(passed=True, scope='Exact reader6 pure-model adjacent TIB join and inverse region projection; unchanged full source/capture comparisons, proof-only exports retain original split BEFORE', files=files, counts=dict(physical_dependencies=len(files), joined_DWORDs=2, persistent_region_extents_unchanged=True, unchanged_reader_predicates=True), source_preparation_sha256='fb90b0dc1d47b9fc89878049100a957d10ad6638bc718e8eff32b04ad861b6f8', capture_reader_opened=False, worker_executed=False, initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__ == '__main__': main(sys.argv[1])
