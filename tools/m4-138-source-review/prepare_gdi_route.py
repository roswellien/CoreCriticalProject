"""Bind the source comparator to its existing exact GDI target tuple."""
from pathlib import Path
import ast, hashlib, json, shutil, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
    parent = ROOT/'reports/m4-joint-startup138-source/preparation-r7'
    out = parent.parent/name
    assert not out.exists()
    pins = {}
    def pin(p,h=None):
        p=Path(p).resolve(); assert p.suffix.lower() not in ('.mwb','.mwi','.zip')
        v=sha(p); assert h is None or h==v; pins[str(p)]=v; return p
    r=json.loads(pin(parent/'report.json').read_bytes())
    assert r['passed']
    for p,h in r['files'].items(): pin(p,h)
    failure=json.loads(pin(parent.parent/'combined-source-provider-r3/report.json').read_bytes())
    assert not failure['passed'] and failure['reader_closed'] and failure['paired_export_readers_closed']
    adapter=pin(ROOT/'tools/m4-widget-growth-review/persistent_gdi.py')
    tree=ast.parse(adapter.read_text())
    values=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TARGETS' for t in n.targets)]
    assert values==[(0x71f00010,0x71f00020,0x71f00030)]
    assert 'target in TARGETS' in adapter.read_text() and 'kind=TARGETS.index(target)' in adapter.read_text()
    text=(parent/'compare_provider138.py').read_text()
    assert text.count('PG.GDI_TARGETS')==1
    current=text.replace('PG.GDI_TARGETS','PG.TARGETS',1)
    assert current.replace('PG.TARGETS','PG.GDI_TARGETS',1)==text
    ast.parse(current)
    out.mkdir()
    for p in parent.iterdir():
        if p.is_file() and p.name!='report.json':
            shutil.copyfile(p,out/p.name)
            pin(out/p.name)
    (out/'compare_provider138.py').write_text(current)
    pin(out/'compare_provider138.py'); pin(__file__); pin(sys.executable)
    result=dict(passed=True,scope='Single exact source GDI route binding correction; no semantic gate changed',entrypoint=str(out/'compare_provider138.py'),parent_preparation_sha256=sha(parent/'report.json'),exact_inverse_restores_parent=True,target_tuple=values[0],all_prior_gates_retained=True,archive_reader_opened=False,source_execution_performed=False,initializer_credit=0,files=pins)
    q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__': main(sys.argv[1])
