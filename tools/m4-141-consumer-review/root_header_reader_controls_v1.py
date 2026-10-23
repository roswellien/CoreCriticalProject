"""Pure production-AST controls and immutable reader-only admission recipe."""
from pathlib import Path
import ast,copy,hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-original141/root-header-reader-controls-r1';out.mkdir();files={};results=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 code=pin(R/'tools/m4-141-consumer-review/validate_original141_v7.py');tree=ast.parse(code.read_text(encoding='utf-8'))
 checks={n.args[1].value:n.args[0]for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and len(n.args)==2 and isinstance(n.args[1],ast.Constant)}
 def evaluate(label,env):return eval(compile(ast.Expression(checks[label]),str(code),'eval'),env)
 def control(name,label,env,want):
  try:got=bool(evaluate(label,env))
  except (KeyError,ValueError,TypeError,struct.error):got=False
  assert got==want,(name,got,want);results.append(dict(name=name,passed=True,production_predicate=label,expected_accept=want))
 h=b'MW4J138O'+struct.pack('<6I',1,6,141,846,43,356992);label='Exact original header'
 control('legacy_magic_current_numeric',label,dict(header=h,struct=struct),True)
 for name,v in [('wrong_current_magic',b'MW4J141O'+h[8:]),('debug_magic',b'MW4J138D'+h[8:]),('extra_byte',h+b'x'),('truncated',h[:-1])]:control(name,label,dict(header=v,struct=struct),False)
 for i in range(6):
  words=[1,6,141,846,43,356992];words[i]+=1;control('numeric_field_'+str(i),label,dict(header=h[:8]+struct.pack('<6I',*words),struct=struct),False)
 writer=pin(R/'reports/m4-original141/root-capture-admission-r2/report.json','2317169a720a88b44b8c14de8f78ffea13974efaca78d4dc88a1a5331c244697');wd=sha(writer)
 execution=R/'reports/m4-original141/root-capture-execution-r2';ep=pin(execution/'report.json','2897d2f5e3a6607e1609ea15a661a0cc76bffd12e2c9017a5b2993c7bb590820')
 admission=dict(capture_preflight_path=str(writer),capture_preflight_sha256=wd,files={str(writer):wd,str(ep):sha(ep),str(code):sha(code)})
 env=dict(Path=Path,ROOT=R,admission=admission,capture_preflight_path=writer,capture_preflight_digest=wd,execution=execution,sha=sha,__file__=str(code),preflight_path=R/'reports/m4-original141/root-strict-reader-admission-r1/report.json')
 bridge='Fresh reader admission physically binds immutable actually used writer admission'
 control('exact_bridge',bridge,env,True)
 for name,mutate in [('wrong_writer_path',lambda a:a.update(capture_preflight_path=str(writer.parent/'other.json'))),('wrong_writer_digest',lambda a:a.update(capture_preflight_sha256='0'*64)),('missing_writer_pin',lambda a:a['files'].pop(str(writer))),('wrong_writer_pin',lambda a:a['files'].update({str(writer):'0'*64}))]:
  e=dict(env);e['admission']=copy.deepcopy(admission);mutate(e['admission']);control(name,bridge,e,False)
 terminal='Fresh reader admission seals exact already-terminal writer execution before reader opens'
 control('exact_terminal_pin',terminal,env,True)
 for name,digest in [('altered_terminal', '0'*64),('missing_terminal',None)]:
  e=dict(env);e['admission']=copy.deepcopy(admission)
  if digest:e['admission']['files'][str(ep)]=digest
  else:e['admission']['files'].pop(str(ep))
  control(name,terminal,e,False)
 own='Actual validator code belongs to exact ROOT admission';control('current_code_pin',own,env,True)
 e=dict(env);e['admission']=copy.deepcopy(admission);e['admission']['files'][str(code)]='0'*64;control('stale_validator',own,e,False)
 writercheck='Actual captured execution bound immutable writer preflight, distinct from current reader-only gate'
 run=json.loads(ep.read_bytes());control('actual_captured_writer_gate',writercheck,dict(env,run=run),True)
 wrong=copy.deepcopy(run);wrong['preflight_sha256']='0'*64;control('reader_digest_not_writer_digest',writercheck,dict(env,run=wrong),False)
 stagepath=pin(execution/'run/stage.json');stage=json.loads(stagepath.read_bytes());assert stage['passed']and stage['exit_code']==0 and stage['inputs_stable']
 for kind in ('stdout','stderr'):pin(execution/'run'/f'{kind}.bin',stage[kind+'_sha256'])
 old=json.loads(writer.read_bytes());assert old['passed']and old['original141_writer_admitted']
 for p,v in old['files'].items():pin(p,v)
 prep=pin(R/'reports/m4-original141/header-reader-preparation-r1/report.json','26ab05ae2933a4052c5d9ee55e58fefb1aee12343c1ea87e1974aaa0e687f49a');j=json.loads(prep.read_bytes())
 for p,v in j['files'].items():pin(p,v)
 pin(__file__);controls=out/'controls.json';controls.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8');pin(controls)
 union=out/'current-reader-input-union.json';union.write_text(json.dumps(dict(files=files),indent=2)+'\n',encoding='utf-8');pin(union)
 report=dict(passed=True,prepared_only=True,controls=len(results),production_AST_only=True,capture_preflight_path=str(writer),capture_preflight_sha256=wd,new_reader_admission_path=str(env['preflight_path']),required_ROOT_fields=dict(passed=True,original141_validator_admitted=True,capture_preflight_path=str(writer),capture_preflight_sha256=wd),actual_execution_path=str(execution),actual_execution_sha256=sha(ep),stage_stdout_stderr_exact=True,retained_writer_inputs=len(old['files']),reader_opened=False,worker_launched=False,accepted_function_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report=str(p),sha256=sha(p),controls=len(results),inputs=len(files),union_sha256=sha(union))))
if __name__=='__main__':main()
