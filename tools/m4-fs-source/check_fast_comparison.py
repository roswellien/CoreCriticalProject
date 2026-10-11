"""Verify failure-only diagnostic derivatives preserve exact byte rejection."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-fs-source'/name;assert not out.exists();out.mkdir(parents=True);pins={};counts={}
 for path,names in((ROOT/'tools/m4-fs-source/compare_connected_v3.py',('first_diff','equal')),(ROOT/'tools/m4-fs-source/compare_paired_policy.py',('delta',))):
  pins[str(path)]=sha(path);tree=ast.parse(path.read_text());functions=[r for r in tree.body if isinstance(r,ast.FunctionDef)and r.name in names];assert len(functions)==len(names);namespace={};exec(compile(ast.Module(body=functions,type_ignores=[]),str(path),'exec'),namespace)
  if 'equal'in namespace:
   equal=namespace['equal'];namespace['first_diff']=lambda *a:(_ for _ in()).throw(RuntimeError('diagnostic called on equal input'));equal(b'\0\x11\xff'*2000,b'\0\x11\xff'*2000,'equal');counts['equal_skips_diagnostics']=1
   namespace['first_diff']=lambda a,b:[(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:16]
   for a,b in((b'abc',b'abd'),(b'abc',b'ab'),(b'ab',b'abc')):
    try:equal(a,b,'must reject')
    except ValueError:pass
    else:raise ValueError('Whole payload difference was admitted')
   counts['unequal_full_bytes_and_length_rejections']=3
  else:
   delta=namespace['delta'];assert delta(b'abc',b'abc')==[]and delta(b'abc',b'abd')==[dict(offset=2,original=99,native=100)];counts['raw_difference_payload_retained']=2
 pins[str(Path(__file__).resolve())]=sha(__file__);report=dict(passed=True,scope='Failure-only diagnostics preserve exact complete comparison and raw unequal observations',counts=counts,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
