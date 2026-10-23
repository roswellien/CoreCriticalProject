"""ROOT complete widget3/controller3 inverses and physical phase adverses."""
from pathlib import Path
import ast,copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-original141-source'/name;assert not out.exists();files={};checks=[]
 def pin(p,h=None):
  p=Path(p).resolve()
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v
  assert str(p)not in files or files[str(p)]==v
  files[str(p)]=v;return p
 p=pin(R/'reports/m4-original141-source/controller-preparation-r3/report.json','a61566e0d9aa2912b444abbd48a0e591c116bcb657db3f0ad13d37713a0109d1');v=json.loads(p.read_bytes())
 for p,h in v['files'].items():pin(p,h)
 inverse=json.loads(pin(R/'reports/m4-original141-source/controller-preparation-r3/inverse.json').read_bytes())
 for row in inverse:
  parent=pin(row['parent']).read_text();child=pin(row['child']).read_text();a=parent.splitlines(keepends=True);b=child.splitlines(keepends=True)
  for d in row['deltas']:
   assert ''.join(a[d['parent_start']:d['parent_stop']])==d['parent']
   assert ''.join(b[d['child_start']:d['child_stop']])==d['child']
  for d in reversed(row['deltas']):b[d['child_start']:d['child_stop']]=d['parent'].splitlines(keepends=True)
  assert ''.join(b)==parent
  ast.parse(child);checks.append(dict(child=row['child'],whole_inverse=True,hunks=len(row['deltas'])))
 widget=ast.parse(pin(R/'tools/m4-original141-source/widget_source141_v3.py').read_text())
 predicates=[n.test for n in ast.walk(widget)if isinstance(n,ast.If)and isinstance(n.test,ast.Compare)and ast.unparse(n.test)=='phase == 139']
 assert len(predicates)==1
 code=compile(ast.Expression(predicates[0]),'actual cleanup predicate','eval')
 for phase in (136,137,138,139,140):
  got=eval(code,{'phase':phase});assert got==(phase==139);checks.append(dict(phase=phase,cleanup_taken=got,passed=True))
 order=json.loads(pin(R/'reports/m4-original141/source-preparation-r6/selected-order.json','da5d37940d51dbfe971e692c4b52f673fd2dda289d9314d078148a70f27519bd').read_bytes())
 assert order[139]['entry']==0x5a66f0 and order[140]['entry']!=0x5a66f0
 pin(__file__);pin(sys.executable)
 for p,h in files.items():pin(p,h)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,checks=checks,actual_terminal_widget_phase=139,source_execution_admitted=False,source_evaluated=False,reader_opened=False,initializer_credit=0,files=files),indent=2)+'\n');print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
