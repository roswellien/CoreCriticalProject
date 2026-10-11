"""Immutable strict-checker4/5 semantics and historical positive/control lineage."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=pin(R/'tools/m4-joint-startup138/check_context_controls_v4.py','5a6b673cad65db1b0c64329c57f5525df0634d70f39165712707dee8151b006e')
 new=pin(R/'tools/m4-joint-startup138/check_context_controls_v5.py')
 a,b=ast.parse(old.read_text()),ast.parse(new.read_text())
 dump=lambda x:ast.dump(x,include_attributes=False)
 ma=next(x for x in a.body if isinstance(x,ast.FunctionDef)and x.name=='main');mb=next(x for x in b.body if isinstance(x,ast.FunctionDef)and x.name=='main')
 fa={x.name:x for x in ma.body if isinstance(x,ast.FunctionDef)};fb={x.name:x for x in mb.body if isinstance(x,ast.FunctionDef)}
 identical=[]
 for n in('raw','read','W','Q','inventory','component','memory','payload','store','hardware'):
  assert dump(fa[n])==dump(fb[n]),n;identical.append(n)
 # All exact refusal, mutation, CPU/State, source operand, cleanup, physical
 # identity and hardware obligations are an identical per-case AST segment.
 def semantic_case(m):
  trial=next(x for x in m.body if isinstance(x,ast.Try));loop=next(x for x in trial.body if isinstance(x,ast.For)and isinstance(x.target,ast.Name)and x.target.id=='run')
  start=next(i for i,x in enumerate(loop.body)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='status'for t in x.targets))
  end=next(i for i,x in enumerate(loop.body)if isinstance(x,ast.Expr)and isinstance(x.value,ast.Call)and isinstance(x.value.func,ast.Attribute)and isinstance(x.value.func.value,ast.Name)and x.value.func.value.id=='proofs')
  return loop.body[start:end+1]
 ca,cb=semantic_case(ma),semantic_case(mb);assert [dump(x)for x in ca]==[dump(x)for x in cb]
 # Exact equal_folder call changed only whole-file materialization to stream.
 foldera=fa['equal_folder'];folderb=fb['equal_folder'];loopa=foldera.body[-1];loopb=folderb.body[-1]
 assert dump(foldera.body[:-1][0])==dump(folderb.body[:-1][0])
 assert [dump(x)for x in foldera.body[:-1]]==[dump(x)for x in folderb.body[:-1]]
 assert dump(loopa.target)==dump(loopb.target)and dump(loopa.iter)==dump(loopb.iter)and dump(loopa.body[-1])==dump(loopb.body[-1])
 assert ast.unparse(loopa.body[0])=="eq(raw(a[n]), raw(b[n]), label + ' whole ' + n)"
 assert ast.unparse(loopb.body[0])=="equal_file(a[n], b[n], label + ' whole ' + n)"
 ef=ast.unparse(fb['equal_file']);assert "eq(a.stat().st_size, b.stat().st_size"in ef and "eq(xb, yb"in ef and 'if not xb:'in ef and 'x.read(1024 * 1024)'in ef and 'y.read(1024 * 1024)'in ef
 # Bytearrays here were constructed only from raw bytes; equality is identical.
 class Bytes(ast.NodeTransformer):
  def visit_Call(self,n):
   self.generic_visit(n)
   if isinstance(n.func,ast.Name)and n.func.id=='bytes'and len(n.args)==1 and isinstance(n.args[0],ast.Subscript):return n.args[0]
   return n
 assert dump(Bytes().visit(fa['equal_memory']))==dump(fb['equal_memory'])
 positive=read(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')
 controls=read(R/'reports/m4-joint-startup138/controls-preparation-r4/report.json','f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e')
 assert positive['selected_order']==controls['selected_order']and len(controls['selected_order'])==138
 common_objects=0
 for level in('O0','O2'):
  assert positive['objects'][level]==controls['objects'][level]and len(controls['objects'][level])==468
  for p in controls['objects'][level]:assert positive['files'][p]==controls['files'][p];pin(p,controls['files'][p]);common_objects+=1
 component=read(controls['widget_component_preparation'],controls['widget_component_preparation_sha256']);shared=[]
 for p,h in component['files'].items():
  if positive['files'].get(p)==controls['files'].get(p)==h:pin(p,h);shared.append(p)
 assert shared
 pin(R/'tools/m4-tree-review/review_mfc131_controls.py');pin(R/'tools/m4-tree-review/review_mfc131_control_equivalence_v3.py');pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Checker4/5 exact per-case semantic predicate equivalence and historical positive138/control138 shared literal objects only; no current native3 linked equivalence',
  counts=dict(exact_identical_per_case_AST_statements=len(ca),identical_helper_ASTs=len(identical),shared_literal_objects=common_objects,shared_component_physical_files=len(shared),identical_declared_schedule_roots=138),
  checker4_sha256=pins[str(old)],checker5_sha256=pins[str(new)],historical_completed_report_binds_checker4=True,checker5_execution_claimed=False,
  performance_changes_reviewed=['Cached pin replaces repeated hashing; stat identity checked each use; every pinned digest is freshly rehashed at completion','Whole-file stream compares1MiB blocks until equal EOF after exact lengths; full folder inventory gate unchanged','Parallel initial hashes and final hashes preserve asserted expected digests and file identity; no GPU path','Bytearray equality retains whole memory bytes; GC clears dictionaries only after proof creation'],
  capture_archives_opened=0,worker_executed=False,verifier_rerun=False,initializer_credit=0,current_native3_link_equivalence_proved=False,full_raw_controls_review=False,
  limitations=['Historical positive/control468object component join cannot substitute current native3 full-link review','Checker5 performance path reviewed but never claimed executed by historical checker4 receipt','Full exported raw/identity/private/provider retry review remains separate'],files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),counts=d['counts'])))
if __name__=='__main__':main(sys.argv[1])
