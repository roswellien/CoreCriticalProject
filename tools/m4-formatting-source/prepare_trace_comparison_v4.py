"""Preserve v3 and add scalar mismatch provenance for write BEFORE joins."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    base=R/'tools/m4-formatting-source/compare_trace_v3.py';source=base.read_text()
    a="eq(ambient,cell['before'],'Entire write operand BEFORE bytes from literal preceding source state')"
    b="need(ambient==cell['before'],'Entire write operand BEFORE bytes from literal preceding source state '+str((phase,index,hex(derived['PC']),hex(cell['address']),cell['width'],ambient,cell['before'])))"
    assert source.count(a)==1;source=source.replace(a,b)
    a="pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v3.py')";assert source.count(a)==1
    source=source.replace(a,a+";pin(R/'tools/m4-formatting-source/compare_trace_v3.py');pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v4.py')")
    generated=base.with_name('compare_trace_v4.py');assert not generated.exists();generated.write_text(source)
    out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
    report=dict(passed=True,scope='Additive diagnostic exact scalar/source-PC write BEFORE mismatch provenance',files={str(p.resolve()):sha(p)for p in(base,generated,Path(__file__))})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
