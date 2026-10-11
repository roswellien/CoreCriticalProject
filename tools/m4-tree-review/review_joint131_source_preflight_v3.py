"""Bind proof-only source snapshot exports on the admitted complete131 reader."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
def main(name):
    out = R / 'reports/m4-tree-review' / name
    assert not out.exists()
    out.mkdir(parents=True)
    files = {}
    def pin(p, h=None):
        p = Path(p).resolve(); actual = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h is None or h == actual
        assert str(p) not in files or files[str(p)] == actual
        files[str(p)] = actual
        return p
    def receipt(p, h):
        r = json.loads(pin(p, h).read_bytes()); assert r['passed']
        for p, h in r['files'].items(): pin(p, h)
        return r
    receipt(R / 'reports/m4-tree-review/joint131-source-preflight-r2/report.json', 'e41ee004866699d40f67481d78affa8541bf060d060b69fd818698f1a782b0eb')
    prep = receipt(R / 'reports/m4-joint-startup131-source/preparation-r5/report.json', '03ad498607cf1d7285a0738275f61d5df7ef355b092f993c30a49779c83a7e73')
    legacy = receipt(R / 'reports/m4-joint-startup131-source/legacy-flags-r4/report.json', '7cc979cff71ae061dc81a425339960a14557e66a7b150d6ad7dcde00f1031c9a')
    base = R / 'tools/m4-joint-startup131'
    old = pin(base / 'compare_provider_v4.py').read_text()
    assert old.count('import mfc_source_v2 as MF') == 1
    assert old.replace('import mfc_source_v2 as MF', 'import mfc_source_v3 as MF') == pin(base / 'compare_provider_v5.py').read_text()
    source = pin(base / 'mfc_source_v3.py').read_text(); tree = ast.parse(source)
    assert "result=super().phase(machine,*args,**kwargs)" in source
    assert 'state=bytes(machine.state)' in source and 'memory={a:bytes(b)for a,b in machine.memory.items()}' in source
    assert source.index('memory={a:bytes(b)') < source.index('result=super().phase')
    assert 'return super().step()' in source and 'self.literal.Literal=SnapshotLiteral' in source
    assert not any(isinstance(n, ast.Name) and n.id in ('archive','DirectSet') for n in ast.walk(tree))
    assert 'source_AFTER_seed' not in source and 'store_bytes(' not in source
    assert prep['literal_normal_boundary_PCs'] == [0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca]
    assert legacy['conditional_PCs'] == 2 and legacy['source_consumers_per_sequence'] == 171
    pin(__file__)
    for p, h in files.items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
    r = dict(passed=True, scope='Independent exact reader4 to reader5 proof-output-only delta; source BEFORE copied before parent mutation, seven literal snapshots, same source comparisons and canonical closure', counts=dict(physical_dependencies=len(files), unchanged_reader_predicates=True, literal_boundary_snapshots_per_phase=7, legacy_conditional_PCs=2), files=files, capture_reader_opened=False, worker_executed=False, initializer_credit=0)
    f = out / 'report.json'; f.write_text(json.dumps(r, indent=2)+'\n')
    print(json.dumps(dict(passed=True, sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__ == '__main__': main(sys.argv[1])
