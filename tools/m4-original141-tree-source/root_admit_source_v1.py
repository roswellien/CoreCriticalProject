"""ROOT whole tree inverses, production audit adverses and fresh input closure."""
from pathlib import Path
import ast,hashlib,json,sys,time
R=Path(__file__).resolve().parents[2]
def main():
 started=time.monotonic();base=R/'reports/m4-original141-tree-source';out=base/'root-source-admission-r1';assert not out.exists();files={};reviews=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  if p.drive.upper()=='G:':assert p.parent==Path('G:/Projects/MW34Recomp-Captures/reports/m4-original141/root-capture-validation-r3/paired-exports/original')and p.name in('index.json','payload.bin')
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def inverse(parent,child,deltas):
  original=pin(parent).read_text();text=pin(child).read_text()
  for d in reversed(deltas):assert text.count(d['new'])==1;text=text.replace(d['new'],d['old'])
  assert text==original,'Whole source inverse';ast.parse(pin(child).read_text());reviews.append(dict(child=str(child),inverse_hunks=len(deltas),passed=True))
 recipe=read(base/'admission-recipe-r3/report.json','9d00de7a8fa968e7479b2060eb4eba5f17784ce170a8cd3cef5213172a92dabf')
 for p,h in recipe['files'].items():pin(p,h)
 union=read(base/'admission-recipe-r3/current-ordinary-input-union.json','38614651c6c64bb99cd649a4952dfb211cc535619e62afe148c8e8653e2d7e9d')
 assert len(union)==9467
 for p,h in union.items():pin(p,h)
 t=R/'tools/m4-original141-tree-source'
 d=read(base/'ordinary-boundary-preparation-r1/deltas.json')
 inverse(R/'tools/m4-startup138-original/tree_source_r5.py',t/'tree_source_v3.py',d['tree_composed'])
 inverse(t/'run_ordinary_v1.py',t/'run_ordinary_v2.py',d['runner'])
 inverse(t/'run_ordinary_v2.py',t/'run_ordinary_v3.py',read(base/'authorized-io-preparation-r1/deltas.json'))
 inverse(t/'run_ordinary_v3.py',t/'run_ordinary_v4.py',read(base/'authorized-io-preparation-r2/deltas.json'))
 order=read(R/'reports/m4-original141/source-preparation-r6/selected-order.json');prior=read(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161')['selected_order']
 assert [r for r in order if r['entry']not in(0x4103f0,0x410440,0x459b40)]==prior and order[86]['entry']==0x4b7f70
 # Reexecute inspected pure production-predicate/audit tests in fresh ROOT
 # namespaces. No Machine, module model, export reader or native code enters.
 for tool,name,count in [('ordinary_boundary_controls_v1.py','root-boundary-controls-r1',13),('authorized_io_controls_v1.py','root-io-controls-r1',24)]:
  p=pin(t/tool);tree=ast.parse(p.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');assign=next(n for n in function.body if isinstance(n,ast.Assign)and any(isinstance(v,ast.Name)and v.id=='out'for v in n.targets));assign.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(str(base/name))],keywords=[])
  ns={'__file__':str(p),'__name__':'ROOT_pure_controls'};exec(compile(ast.fix_missing_locations(tree),str(p),'exec'),ns);ns['main']();receipt=read(base/name/'report.json');assert receipt['passed']is True and len(receipt['controls'])==count;reviews.append(dict(production_controls=count,receipt=str(base/name/'report.json')))
 pin(__file__);pin(sys.executable)
 for p,h in files.items():pin(p,h)
 out.mkdir();result=dict(passed=True,independent_review=True,original141_tree_source_admitted=True,validation_sha256='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c',preparation_sha256='c12647c250cc491c42e31dc52b425c2194f096ba70337c1da2ce070fcf628952',scope='ROOT exact15 tree inverse,8 runner inverse hunks,37 production boundary/audit controls and whole current ordinary physical source/input closure before source execution',reviews=reviews,source_model_executed=False,reader_opened=False,worker_executed=False,initializer_credit=0,elapsed_seconds=time.monotonic()-started,files=files)
 q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main()
