"""UNEXECUTED ordinary typed-layout proof. No models, exports or acceptance."""
from pathlib import Path
import ast,hashlib,json,re,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
HELPER=R/'tools/m4-startup141-paired/original7_child_view_v2.py'
HELPER_SHA='5523aec0f60e54ac9e424b7f42f867f2dc05796af86f0c974bcd8b0e2d18446f'
PARSER=R/'tools/m4-138-controls-review/full_raw_review_v2.py'
ORDER=R/'reports/m4-original141/source-preparation-r6/selected-order.json'
ORDER_SHA='da5d37940d51dbfe971e692c4b52f673fd2dda289d9314d078148a70f27519bd'

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def ordinary(p):
 p=Path(p).resolve()
 assert p.is_relative_to(R) and p.suffix.lower()in('.json','.py') and p.name!='transport.json'
 assert p.is_file()
 return p

def stable(p):
 s=Path(p).stat();return(s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def main(admission_path,admission_sha,name):
 ap=ordinary(admission_path);assert sha(ap)==admission_sha and ap.stat().st_size<4*1024*1024
 A=json.loads(ap.read_bytes());assert A['passed']is True and A['independent_review']is True and A['scope_identity']=='original141_source7_typed_layout_only'
 admitted={str(ordinary(p)):h for p,h in A['files'].items()};assert len(admitted)==len(A['files'])
 assert admitted[str(Path(__file__).resolve())]==sha(__file__) and admitted[str(HELPER)]==HELPER_SHA
 assert A['original7_sha256']=='44a46bd0fda7776578232af60e2d9f0188275660350a239eb8c8def4790d9334' and A['selected_order_sha256']==ORDER_SHA
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True)
 files={str(ap):admission_sha};stats={};opened=0;closed=0;stream_rows=0;passed=False;view=None
 def pin(p,h):
  p=ordinary(p);assert admitted.get(str(p))==h and re.fullmatch('[0-9a-f]{64}',h)
  if str(p)in stats:
   assert files[str(p)]==h and stable(p)==stats[str(p)];return p
  old=stable(p);assert sha(p)==h and stable(p)==old
  assert str(p)not in files or files[str(p)]==h
  files[str(p)]=h;stats[str(p)]=old;return p
 # All directly/indirectly consumed files must be admitted before imports.
 # This finite admission contains only the typed view inputs, not every file
 # declared by the underlying source gates. Those gates are separately owned.
 for p,h in admitted.items():pin(p,h)
 def audit(event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
  reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if reading:assert p.is_relative_to(out)or str(p)in admitted or p==ap,'External input not admitted before open'
 sys.addaudithook(audit)
 try:
  helper_raw=pin(HELPER,HELPER_SHA).read_bytes();env={};exec(compile(ast.parse(helper_raw.decode()),str(HELPER),'exec'),env)
  parser_raw=pin(PARSER,A['stream_parser_sha256']).read_bytes();tree=ast.parse(parser_raw.decode())
  nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='StreamJSON'];assert len(nodes)==1
  def need(v,s):
   if not v:raise ValueError(s)
  penv=dict(json=json,need=need);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(PARSER),'exec'),penv);S=penv['StreamJSON']
  def unique(pairs):
   d={}
   for k,v in pairs:assert k not in d,'Duplicate metadata JSON key';d[k]=v
   return d
  def read_json(p,h):
   nonlocal opened,closed
   p=pin(p,h);assert p.stat().st_size<4*1024*1024
   opened+=1
   try:
    with p.open('r',encoding='utf-8')as f:value=json.load(f,object_pairs_hook=unique)
   finally:closed+=1
   pin(p,h);return value
  def iter_rows(p,h):
   nonlocal opened,closed,stream_rows
   p=pin(p,h);opened+=1
   try:
    with p.open('r',encoding='utf-8')as f:
     s=S(f);s.expect('[');s.trim()
     if s.buf.startswith(']'):s.expect(']');s.finish();return
     while True:
      row=s.value();assert type(row)is dict;stream_rows+=1;yield row
      s.trim()
      if s.buf.startswith(']'):s.expect(']');break
      s.expect(',')
     s.finish()
   finally:closed+=1;pin(p,h)
  order=read_json(ORDER,ORDER_SHA)
  view=env['load_authenticated_view'](read_json,iter_rows,order)
  assert view['source_case_extent']==120 and len(view['cases'])==120 and len({(v['family'],v['sequence'],v['root'])for v in view['cases']})==120
  assert stream_rows==102 and view['complete_paired141_gate']is False and view['accepted_function_credit']==0
  # Authenticate each referenced complete artifact even if the selector view
  # did not decode its body; authenticate all per-case constructor files and
  # the actual tree child receipts. No dependency body is reinterpreted.
  for case in view['cases']:
   for ref in list(case['artifact_references'].values())+case['case_artifact_references']:pin(ref['path'],ref['sha256'])
   if case['family']=='tree':
    p=R/('reports/m4-original141-tree-source/source-r1-case-'+str(case['sequence'])+'/report.json');pin(p,admitted[str(p)])
  assert opened==closed
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p,h in files.items():assert sha(p)==h and (p not in stats or stable(p)==stats[p]),'Final whole input conservation'
  if view is not None:(out/'typed-child-view.json').write_text(json.dumps(view,indent=2)+'\n')
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Whole authenticated ordinary original7 child layout and120 typed selectors only; source claims retained without new equality',admission_sha256=admission_sha,original7_sha256=A['original7_sha256'],source_case_extent=120 if passed else 0,whole_source_artifact_references_authenticated=passed,all_consumed_files_rehashed_before_and_after=passed,ordinary_stream_rows=stream_rows,ordinary_handles_opened=opened,ordinary_handles_closed=closed,ordinary_reader_closed=opened==closed,source_models_executed=False,export_reader_opened=False,canonical_reader_opened=False,original_whole_State_claim=False,complete_paired141_gate=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))

if __name__=='__main__':main(*sys.argv[1:])
