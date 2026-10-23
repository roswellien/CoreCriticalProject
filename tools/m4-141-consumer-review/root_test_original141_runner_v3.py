"""Exercise actual runner admission IF predicates only; no main/stage execution."""
from pathlib import Path
import ast,copy,hashlib,json,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141/root-runner-controls-r2';out.mkdir();p=Path(__file__).with_name('run_original141_v4.py');tree=ast.parse(p.read_bytes());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main')
 start=next(i for i,x in enumerate(fn.body)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='b'for t in x.targets));end=next(i for i,x in enumerate(fn.body)if isinstance(x,ast.For)and ast.unparse(x.iter)=="q['files'].items()")
 nodes=[x for x in fn.body[start+1:end]if isinstance(x,ast.If)or(isinstance(x,ast.Assign)and ast.unparse(x.targets[0])=='validator')]
 assert len(nodes)==8,len(nodes)
 code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual runner admission predicates','exec');build=R/'reports/m4-original141/build-r2/build.json';b=json.loads(build.read_bytes());sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
 q=dict(passed=True,original141_writer_admitted=True,original141_validator_admitted=True,files={str(build.resolve()):sha(build),str(Path(b['worker']).resolve()):b['worker_sha256'],str(p.resolve()):sha(p),str(R/'tools/m4-141-consumer-review/validate_original141_v6.py'):'d189534d56046153aeaafbcbdf699d72b51fed0da6969a832e5fc5be01159c7b'})
 controls=[]
 def test(name,bb,qq,reject):
  try:exec(code,dict(R=R,b=bb,q=qq,Path=Path,build=build,digest=sha(build),sha=sha,__file__=str(p.resolve())))
  except (ValueError,KeyError):assert reject,name
  else:assert not reject,name
  controls.append(dict(name=name,rejected=reject))
 test('real current compiled build, synthetic full explicit admission shape',b,q,False)
 for k in ['passed','original141_writer_admitted','original141_validator_admitted']:
  x=copy.deepcopy(q);x[k]=False;test('reject false '+k,b,x,True)
  x=copy.deepcopy(q);del x[k];test('reject missing '+k,b,x,True)
 for k in list(q['files']):
  x=copy.deepcopy(q);x['files'][k]='0'*64;test('reject altered pin '+Path(k).name,b,x,True)
 for k in ['roots','phases','record_bytes','sequences','pages','external_pages','combined_pages','constructor_global_extra_page_bytes']:
  x=copy.deepcopy(b);x[k]+=1;test('reject wrong '+k,x,q,True)
 x=copy.deepcopy(b);x['preparation_sha256']='0'*64;test('reject unrelated source preparation',x,q,True)
 x=copy.deepcopy(b);x['passed']=False;test('reject failed build',x,q,True)
 files={str(x.resolve()):sha(x)for x in[p,Path(__file__),build,R/'reports/m4-original141/rebase-controller-preparation-r1/report.json']}
 report=dict(passed=True,controls=controls,production_predicate_count=len(nodes),actual_runner_imported=False,actual_runner_main_called=False,synthetic_admission_only=True,worker_launched=False,reader_opened=False,initializer_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(sha(p))
if __name__=='__main__':main()
