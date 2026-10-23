"""Bounded code/receipt preparation and pure parser controls; no consumer run."""
from pathlib import Path,PureWindowsPath
import ast,hashlib,io,json
R=Path(__file__).resolve().parents[2]

def main():
 out=R/'reports/m4-startup141-paired/original7-layout-consumer-preparation-r1';assert not out.exists()
 files={};required={}
 def small(p):
  p=Path(p).resolve();assert p.stat().st_size<4*1024*1024;raw=p.read_bytes();files[str(p)]=hashlib.sha256(raw).hexdigest();return raw
 helper=R/'tools/m4-startup141-paired/original7_child_view_v2.py';env={};exec(compile(ast.parse(small(helper).decode()),str(helper),'exec'),env)
 consumer=R/'tools/m4-startup141-paired/consume_original7_child_view_v1.py';ctree=ast.parse(small(consumer).decode())
 parser=R/'tools/m4-138-controls-review/full_raw_review_v2.py';ptree=ast.parse(small(parser).decode());classes=[n for n in ptree.body if isinstance(n,ast.ClassDef)and n.name=='StreamJSON'];assert len(classes)==1
 def need(v,s):
  if not v:raise ValueError(s)
 penv=dict(json=json,need=need);exec(compile(ast.Module(body=classes,type_ignores=[]),str(parser),'exec'),penv);S=penv['StreamJSON']
 def array(text,chunk):
  s=S(io.StringIO(text),chunk);s.expect('[');s.trim();rows=[]
  if s.buf.startswith(']'):s.expect(']');s.finish();return rows
  while True:
   row=s.value();assert type(row)is dict;rows.append({k:row[k]for k in('sequence','root','phase')});s.trim()
   if s.buf.startswith(']'):s.expect(']');break
   s.expect(',')
  s.finish();return rows
 expected=[dict(sequence=0,root=0x40e250,phase=17),dict(sequence=5,root=0x5a66f0,phase=139)]
 controls=[]
 for chunk in(1,2,7,32,1024):
  assert array(json.dumps(expected),chunk)==expected;controls.append(dict(name='stream_two_selectors_chunk_'+str(chunk),rejected=False))
 for name,text in [('duplicate_nested_key','[{"sequence":0,"sequence":1,"root":1,"phase":1}]'),('trailing_bytes',json.dumps(expected)+'x'),('truncated_array',json.dumps(expected)[:-1]),('wrong_top_level',json.dumps(expected[0])),('scalar_row','[1]'),('missing_selector','[{"sequence":0,"root":1}]'),('trailing_comma','[{"sequence":0,"root":1,"phase":1},]')]:
  rejected=False
  try:array(text,7)
  except(AssertionError,ValueError,KeyError):rejected=True
  assert rejected;controls.append(dict(name=name,rejected=True))
 # Test exactly the production ordinary-path geometry assertion without its
 # separate actual is_file/open operation. No filesystem target is opened.
 fn=next(n for n in ctree.body if isinstance(n,ast.FunctionDef)and n.name=='ordinary');guard=fn.body[1];assert isinstance(guard,ast.Assert)
 scope=dict(R=PureWindowsPath(str(R)))
 for name,p,ok in [('workspace_json',R/'reports/x.json',True),('workspace_py',consumer,True),('canonical_G',PureWindowsPath('G:/capture/x.json'),False),('transport',R/'reports/transport.json',False),('archive',R/'reports/x.mwb',False),('raw_export_payload',R/'reports/payload.bin',False),('zip',R/'reports/x.zip',False),('escaped_workspace',PureWindowsPath('D:/elsewhere/x.json'),False)]:
  rejected=False
  try:exec(compile(ast.Module(body=[guard],type_ignores=[]),str(consumer),'exec'),dict(scope,p=PureWindowsPath(str(p))))
  except AssertionError:rejected=True
  assert rejected is(not ok);controls.append(dict(name=name,rejected=rejected))
 aggpath=R/'reports/m4-original141-source/source-r7/report.json';aggregate=json.loads(small(aggpath));assert files[str(aggpath)]==env['AGGREGATE_SHA'];required[str(aggpath)]=files[str(aggpath)]
 for family,(folder,h,roots,leaves)in env['FAMILIES'].items():
  p=R/folder/'report.json';report=json.loads(small(p));assert files[str(p)]==h;required[str(p)]=h
  for leaf in leaves:q=str(p.parent/leaf);required[q]=report['files'][q]
  if family=='constructor18':
   for row in report['cases']:
    for leaf in('input.json','source-derivation.json'):
     q=str(p.parent/('original-'+str(row['sequence'])+'-'+str(row['root']))/leaf);required[q]=report['files'][q]
  if family=='tree':
   for sequence in range(6):
    q=str(Path(str(p.parent)+'-case-'+str(sequence))/'report.json');required[q]=report['files'][q]
 order=R/'reports/m4-original141/source-preparation-r6/selected-order.json';small(order)
 for p in(helper,consumer,parser,order):required[str(p)]=files[str(p)]
 assert len(required)==len({p.casefold()for p in required})
 out.mkdir(parents=True)
 q=out/'required-ordinary-inputs.json';q.write_text(json.dumps(dict(files=required,all_source_artifact_hashes_declared_not_remeasured=True,root_rehash_before_admission_required=True),indent=2)+'\n');files[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest()
 q=out/'pure-controls.json';q.write_text(json.dumps(dict(pure_controls=True,controls=controls,actual_consumer_executed=False,actual_source_artifacts_read=False),indent=2)+'\n');files[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest()
 recipe=dict(scope_identity='original141_source7_typed_layout_only',independent_ROOT_admission_required=True,consumer_path=str(consumer),consumer_sha256=files[str(consumer)],helper_path=str(helper),helper_sha256=files[str(helper)],stream_parser_path=str(parser),stream_parser_sha256=files[str(parser)],original7_sha256=env['AGGREGATE_SHA'],selected_order_sha256=files[str(order)],required_files=required,invocation=['C:/Python314/python.exe',str(consumer),'<ROOT-admission-path>','<ROOT-admission-sha256>','<fresh-output-name>'],review_requirements=['Read whole consumer and child view; retain28 child pure controls and20 parser/path controls','Rehash each required entire ordinary file before seal; exact scoped ROOT admission forbids archives, G, transport and raw payloads','Extract unmodified StreamJSON class AST from physically pinned parser; no production module imports/models','Actual run hashes all admitted input bytes before code execution and independently at final conservation; stats reuse inside run never replaces either whole pass','Stream102 complete artifact rows without top-level giant dictionary, retain only120 case selectors including18 constructor report cases','Verify every artifact/case-reference belongs exact six source gates and all120 family/sequence/root identities unique','Actual typed layout cannot establish original State, paired ENV, source callback cleanup, eligibility or complete141 pair'])
 q=out/'ROOT-review-recipe.json';q.write_text(json.dumps(recipe,indent=2)+'\n');files[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest()
 files[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 q=out/'preparation-only.json';q.write_text(json.dumps(dict(prepared_only=True,consumer_unexecuted=True,actual_source_artifact_rows_read=False,ordinary_export_reader_opened=False,canonical_reader_opened=False,source_models_executed=False,required_physical_inputs=len(required),pure_controls=len(controls),artifact_hashes_future_ROOT_rehash_required=True,initializer_credit=0,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))

if __name__=='__main__':main()
