"""One finally-closed reader exports only the failed projection ledger."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
    out=ROOT/'reports/m4-joint-startup138-source'/name
    assert not out.exists(); out.mkdir()
    pins={}; reader=None; closed=True
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
    fail=ROOT/'reports/m4-joint-startup138-source/combined-source-provider-r4'
    f=json.loads(pin(fail/'report.json','351e22b907e033f673f843edd1cde193b32d7e58e34c5c1b76966547d63d10af').read_bytes())
    assert not f['passed'] and f['reader_closed'] and f['paired_export_readers_closed']
    rows=json.loads(pin(fail/'Widget-source-derivations.json').read_bytes())
    expected=[tuple(v['borrowed_provider']['borrowed_projection'])for v in rows]
    e=json.loads(pin(ROOT/'reports/m4-joint-startup138-root/execution-r3/report.json','2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6').read_bytes())
    spec=importlib.util.spec_from_file_location('narrow_projection_reader',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try:
        reader=module.DirectSet(Path(e['levels'][0]['capture']),pin);closed=False
        raw=reader.data('sequence-0/selected/registry-research-projections.bin')
        (out/'actual-projections.bin').write_bytes(raw);pin(out/'actual-projections.bin')
        actual=list(struct.iter_unpack('<8I',raw))
    finally:
        if reader is not None:reader.close()
        closed=True
    pin(__file__);pin(sys.executable)
    for p,h in pins.items():assert sha(p)==h
    result=dict(passed=True,scope='Exact actual versus source predicted borrowed projection diagnostic only',reader_closed=closed,canonical_reader_opened=True,source_execution_performed=False,initializer_credit=0,actual=actual,expected_widget=expected,files=pins)
    q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,sha256=sha(q),actual=actual,expected=expected)))
if __name__=='__main__':main(sys.argv[1])
