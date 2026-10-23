"""Immutable whole-inverse final-conservation/stdlib-closure derivative."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];O=R/'reports/m4-controls-terminal-composite/composite-review-preparation-r2';assert not O.exists();O.mkdir();p=R/'tools/m4-controls-terminal-composite/review_completed_composite_v1.py';a=p.read_text();assert hashlib.sha256(p.read_bytes()).hexdigest()=='8eae240563fd4337b7ee980d5e2cc763b3ea6205eeaf8b465ea5ec4f1457bc72';b=a;changes=[]
def sub(x,y):
 global b
 assert b.count(x)==1;b=b.replace(x,y);changes.append(dict(before=x,after=y))
sub('import hashlib,importlib.util,json,re,sqlite3,sys,traceback', 'import collections,contextlib,hashlib,importlib.util,json,linecache,os,re,sqlite3,struct,sys,textwrap,time,token,tokenize,traceback,urllib.parse')
sub('def main(admission,', '''def conserve_inputs(connection,direct_pins,measure,progress=None):
 count=0
 for path,h in connection.execute('SELECT path,sha FROM physical ORDER BY path'):
  measure(Path(path),h);count+=1
  if progress and count%5000==0:progress(count)
 assert count==connection.execute('SELECT COUNT(*)FROM physical').fetchone()[0],'All final physical union rows measured'
 for path,h in direct_pins.items():measure(Path(path),h)
 return dict(physical_rows_rehashed=count,direct_pins_rehashed=len(direct_pins),metadata_only_cache_used=False)
def main(admission,''')
sub('expanded=None;facets=None', 'expanded=None;facets=None;final_conservation=None;stdlib_preloaded=[]')
sub(' def source_only(event,args):', ''' # Explicit trusted stdlib preload occurred in the reviewed top-level imports.
 # No project machinery is loaded before its ROOT source SHA check below.
 for module_name in ('collections','contextlib','hashlib','importlib.util','json','linecache','os','re','sqlite3','struct','sys','textwrap','time','token','tokenize','traceback','urllib.parse'):
  module=sys.modules[module_name];origin=getattr(getattr(module,'__spec__',None),'origin',None)
  if origin in ('built-in','frozen',None):stdlib_preloaded.append(dict(module=module_name,origin=origin));continue
  origin_path=Path(origin).resolve();assert origin_path.is_relative_to(Path(sys.base_prefix).resolve()),'Trusted interpreter stdlib only before hook'
  pins[str(origin_path)]=sha(origin_path);record=dict(module=module_name,origin=str(origin_path),sha256=pins[str(origin_path)])
  cached=getattr(module,'__cached__',None)
  if cached and Path(cached).is_file():
   cache=Path(cached).resolve();assert cache.is_relative_to(Path(sys.base_prefix).resolve());pins[str(cache)]=sha(cache);record['preloaded_stdlib_cache_path']=str(cache);record['preloaded_stdlib_cache_sha256']=pins[str(cache)]
  stdlib_preloaded.append(record)
 def source_only(event,args):''')
sub('  direct(__file__);E=load', '  direct(sys.executable);direct(__file__);E=load')
sub('expanded=E.expand(controls_path,controls_sha,register,register_edge=edge);db.commit()', "expanded=E.expand(controls_path,controls_sha,register,register_edge=edge,progress=lambda n:print(json.dumps(dict(stage='composite-physical-expansion',rows=n)),flush=True));db.commit()")
sub('  db.commit();passed=True', "  final_conservation=conserve_inputs(db,pins,E.measured,progress=lambda n:print(json.dumps(dict(stage='final-input-conservation',rows=n)),flush=True));db.commit();passed=True")
sub('expansion=expanded,counts=', "expansion=expanded,final_input_conservation=final_conservation,trusted_stdlib_preloaded_before_strict_project_hook=stdlib_preloaded,project_cached_bytecode_allowed=False,counts=")
q=p.with_name('review_completed_composite_v2.py');assert not q.exists();ast.parse(b);q.write_text(b);back=b
for d in reversed(changes):assert back.count(d['after'])==1;back=back.replace(d['after'],d['before'])
assert back==a
files={str(x):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,Path(__file__).resolve(),R/'tools/m4-controls-terminal-composite/review_composite_facets_v1.py',R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py')};r=O/'report.json';r.write_text(json.dumps(dict(prepared_only=True,whole_parent_inverse_equal=True,changes=changes,final_everybyte_union_and_direct_inputs_before_pass=True,progress_callback_for_initial_and_final_hash_pass=True,stdlib_preload='Reviewed explicit stdlib import set before strict hook; require each file origin/cache inside trusted sys.base_prefix, record physical source/cache SHA before/after; no project machinery preloaded, every project module still ROOT source-SHA reviewed before load, .pyc reads refused after hook.',ROOT_admission_must_pin_python_executable=True,actual_production_DB_opened=False,review_runner_executed=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=hashlib.sha256(r.read_bytes()).hexdigest(),runner_sha256=files[str(q)])))
