"""Execute actual production audit function with mock hash I/O only."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/authorized-io-controls-r1';out.mkdir();q=R/'tools/m4-original141-tree-source/run_ordinary_v4.py';tree=ast.parse(q.read_text(encoding='utf-8'));audit=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='audit');wrapper=ast.parse('def make(authorized,produced,out,name,sha):\n audit_inside=False\n return None\n').body[0];wrapper.body[-1:]=[copy.deepcopy(audit),ast.Return(value=ast.Name(id='audit',ctx=ast.Load()))];module=ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]));namespace=dict(Path=Path);exec(compile(module,str(q),'exec'),namespace);results=[];output=R/'reports/m4-original141-tree-source/future-source-r1';source=R/'tools/m4-tree-source/game_model_v4.py';identity='a'*64
 def control(name,path,mode,want,allowed=None,actual=identity,produced=None):
  calls=[];allow={str(source):identity}if allowed is None else allowed
  def fake_sha(p):calls.append(str(p));return actual
  hook=namespace['make'](allow,set()if produced is None else produced,output,'future-source-r1',fake_sha)
  try:hook('open',(str(path),'w'if mode=='write'else 'r',1 if mode=='write'else 0));got=True
  except (AssertionError,FileNotFoundError):got=False
  assert got==want,name
  if name.startswith('unadmitted'):assert not calls,'Denied BEFORE any hash/open'
  results.append(dict(name=name,passed=True,expected_accept=want,mock_hash_calls=len(calls)))
 control('admitted_current_source',source,'read',True);control('unadmitted_source_before_open',source.with_name('unadmitted.py'),'read',False);control('changed_admitted_digest',source,'read',False,actual='b'*64)
 for suffix in ('.mwb','.mwi','.zip'):
  p=R/('canonical'+suffix);control('reject_even_admitted_'+suffix,p,'read',False,allowed={str(p):identity})
 p=R/'transport.json';control('reject_even_admitted_transport',p,'read',False,allowed={str(p):identity})
 p=R/'tools/m4-tree-source/__pycache__/game_model_v4.cpython-314.pyc';control('reject_cached_bytecode',p,'read',False,allowed={str(p):identity})
 p=Path('G:/Projects/MW34Recomp-Captures/reports/m4-original141/root-capture-validation-r3/paired-exports/original/payload.bin').resolve();control('exact_admitted_ordinary_payload',p,'read',True,allowed={str(p):identity});control('unadmitted_other_G_payload',p.with_name('other.bin'),'read',False,allowed={str(p):identity})
 control('new_aggregate_output',output/'report.json','write',True)
 for i in range(6):control('exact_case_output_'+str(i),output.parent/('future-source-r1-case-'+str(i))/'report.json','write',True)
 for label in ('00','6','x','-1'):control('reject_other_child_'+label,output.parent/('future-source-r1-case-'+label)/'report.json','write',False)
 control('reject_external_source_write',source,'write',False);control('reject_nested_child_write',output.parent/'future-source-r1-case-0'/'nested'/'report.json','write',False)
 produced={str(output/'report.json')};control('own_produced_output_read',output/'report.json','read',True,produced=produced)
 files={str(q):hashlib.sha256(q.read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};p=out/'report.json';p.write_text(json.dumps(dict(passed=True,controls=results,production_audit_AST_executed=True,source_machine_constructed=False,ordinary_reader_opened=False,canonical_reader_opened=False,worker_launched=False,files=files),indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
