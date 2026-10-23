"""Actual ordinary COFF/worker-based adverse controls of retained CALL target predicate."""
from pathlib import Path
import ast,json,hashlib,importlib.util,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-138-preresource-root-review/controls-r1';out.mkdir();files={};tests=[]
 def pin(p,h=None):p=Path(p).resolve();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 def module(p,n):s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 report=json.loads(pin(R/'reports/m4-138-preresource-root-review/review-r4/report.json','a882877721ffc6aa8a04d93eda88cc198c739cf43d421b9b83c24c8ba205b0e9').read_bytes());assert report['passed']
 for p,h in report['files'].items():pin(p,h)
 driver=pin(R/'tools/m4-138-preresource-root-review/review_v4.py');text=driver.read_text();start=text.index("     assert 4<=row['type']<=9");end=text.index('     is_call=',start);predicate='\n'.join(v[5:]for v in text[start:end].splitlines());ast.parse(predicate)
 C=module(R/'tools/m4-tree-review/amd64_coff.py','preresource_control_coff');M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','preresource_control_image');N=module(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','preresource_control_bytes')
 links=json.loads(pin(R/'reports/m4-138-preresource-root-review/review-r4/links.json').read_bytes());build=json.loads(pin(R/'reports/m4-138-preresource-controls/build-r4/build.json','9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f').read_bytes())
 def trial(name,env,bad=False):
  try:exec(compile(predicate,'actual current typed CALL target predicate','exec'),env)
  except AssertionError:assert bad
  else:assert not bad
  tests.append(dict(name=name,rejected=bad,passed=True))
 for level,w in build['workers'].items():
  image=M.AMD64Image(pin(w['path'],w['sha256']).read_bytes());sy,se=C.parse(pin(w['object'],w['object_sha256']).read_bytes())
  rows=next(v['rows']for v in links if v.get('level')==level and v.get('kind')=='exact_current_control_CALL_and_callback_targets')
  for j in rows:
   raw,rel=C.function(sy,se,j['caller']);selected=[v for v in rel if v['offset']==j['offset']and v['symbol']['name']==j['target']];assert len(selected)==1;row=selected[0]
   address=next(v['address']for v in links if v.get('level')==level and v.get('symbol')==j['caller']);physical=N.image_bytes(image,address,len(raw));assert row['offset']+4<=len(physical)
   env=dict(row=row,address=address,physical=physical,struct=struct,current_targets={j['target']:j['target_address']},target_name=j['target'],caller=j['caller'])
   label=level+'/'+j['caller']+'/'+str(row['offset']);trial(label+'/actual',dict(env))
   wrong=dict(env);b=bytearray(physical);b[row['offset']]^=1;wrong['physical']=bytes(b);trial(label+'/changed_actual_CALL_displacement',wrong,True)
   wrong=dict(env);wrong['current_targets']={j['target']:j['target_address']+1};trial(label+'/wrong_owning_target',wrong,True)
   wrong=dict(env);wrong['row']={**row,'type':11};trial(label+'/wrong_relocation_kind',wrong,True)
 assert len(tests)==60
 pin(__file__);result=dict(passed=True,ordinary_actual_COFF_worker_inputs=True,production_predicate_extracted_exact=True,tests=tests,controls=len(tests),actual_current_function_target_joins=15,runtime_case_executed=False,TLS_runtime_proven=False,canonical_reader_opened=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(report=str(out/'report.json'),sha256=sha(out/'report.json'),controls=len(tests))))
if __name__=='__main__':main()
