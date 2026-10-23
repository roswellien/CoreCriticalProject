"""ROOT only, after24 strict cases: seal exact ordinary source/raw union.

Does not import helpers, execute workers/checkers/aggregation, or grant credit.
SQLite bounds union bookkeeping; only one actual case JSON is retained at once.
"""
from pathlib import Path
import argparse,hashlib,json,re,sqlite3,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BASE=R/'reports/m4-138-preresource-strict-review'
PRODUCTION_SHA='59fbbf6c9da98b54b2bf84fe7ee7582557b789ab73260255822ca93206b9c69f'
CONTROLLER_SHA='c021a492021016ee517f7d8439e3110060d090a264992810ff8af4330a2da5fa'
BUILDER_SHA='f9a62165a3e18622a39a5382cd9b33f2c41e253a0bf306951e5b09ca84d6833f'
CHECKER_SHA='36db8b6af8d57d6e72a261d80cb22b72cd6b3ceddfc654eea6b373f01416a009'
AGGREGATE_SHA='e864cb2228d33944cf3dc55beb84d6c83da55fb9bcda1d687516d0ad662562cb'
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:need(k not in d,'No duplicate JSON field '+k);d[k]=v
 return d

def main(a):
 for name in(a.name,a.aggregate_name):need(re.fullmatch('[A-Za-z0-9_-]{1,90}',name),'Fresh simple immutable namespace')
 out=BASE/a.name;need(not out.exists()and not(BASE/a.aggregate_name).exists(),'Fresh admission and future aggregation directories');out.mkdir()
 db=sqlite3.connect(out/'ordinary-union.sqlite');db.execute('PRAGMA cache_size=-2048');db.execute('PRAGMA temp_store=FILE');db.execute('CREATE TABLE deps(path TEXT PRIMARY KEY, folded TEXT UNIQUE, digest TEXT NOT NULL)');passed=False;rows=[];counts={};summary=[];metadata={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.is_file()and p.suffix.lower()not in('.mwb','.mwi','.zip','.7z','.gz')and p.name!='transport.json','Only actual ordinary dependency');key=str(p)
  prior=db.execute('SELECT path,digest FROM deps WHERE folded=?',(key.casefold(),)).fetchone()
  if prior:
   need(prior[0]==key and(h is None or prior[1]==h),'Unique spelling and hash identity');return p
  v=sha(p);need(h is None or h==v,'Exact physical input '+key);db.execute('INSERT INTO deps VALUES(?,?,?)',(key,key.casefold(),v));return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes(),object_pairs_hook=unique)
 def absorb(v):
  need(type(v)is dict,'Typed complete ordinary filemap')
  for p,h in v.items():need(type(h)is str and re.fullmatch('[0-9a-f]{64}',h),'Exact dependency SHA');pin(p,h)
 try:
  batch=read(a.batch,a.batch_sha);need(batch['passed']is True and batch['strict_case_count']==24 and batch['all_children_terminal']is True,'Completed actual all24 strict serial batch only')
  for flag in('native_worker_executed','capture_reader_opened','acceptance_executed','configuration_created'):need(batch[flag]is False,'No broader batch execution claim')
  need(batch['initializer_credit']==batch['accepted_function_credit']==0,'No batch credit');absorb(batch['files'])
  need(batch['files'].get(str(R/'tools/m4-138-preresource-strict-review/serial_batch_v2.py'))==CONTROLLER_SHA,'Actual terminal batch physically pins current reviewed controller')
  pin(R/'tools/m4-138-preresource-strict-review/serial_batch_v2.py',CONTROLLER_SHA);pin(R/'tools/m4-138-preresource-strict-review/root_admission_builder_v4.py',BUILDER_SHA);pin(BASE/'preparation-r5/verify_case_v5.py',CHECKER_SHA)
  need(batch['production_sha256']==PRODUCTION_SHA,'Exact24 raw production identity');production=read(R/'reports/m4-138-preresource-root-review/root-case-production-r1/report.json',PRODUCTION_SHA)
  need(production['passed']is True and production['raw_cases']==24 and production['all_workers_terminal']is True and production['strict_outcomes_verified']is False,'Raw producer remains separate from strict success')
  rawrows=production['runs'];need(len(rawrows)==24 and {(r['level'],r['mode'])for r in rawrows}=={(l,m)for l in('O0','O2')for m in range(1,13)},'Exactly24 actual raw case identities');rawmap={(r['level'],r['mode']):r for r in rawrows}
  actual=batch['strict_cases'];need(len(actual)==24 and len({r['report']for r in actual})==24,'No repeated strict report output');seen=set();prior=0
  children=batch['processes'];need(len(children)==46,'Exactly23 admissions and23 strict child executions')
  for n,child in enumerate(children):
   expected=R/'tools/m4-138-preresource-strict-review/root_admission_builder_v4.py'if n%2==0 else BASE/'preparation-r5/verify_case_v5.py'
   need(child['exit_code']==0 and child['command'][1]=='-B'and child['command'][2]==str(expected),'Exact terminal ordinary child command pairs; no native workers')
  for row in actual:
   need(type(row['level'])is str and row['level']in('O0','O2')and type(row['mode'])is int and 1<=row['mode']<=12,'Exact case field types and domain');case=row['level'],row['mode'];need(case not in seen,'No duplicate case');seen.add(case);raw=rawmap[case]
   need(row['raw_execution']==raw['report']and row['raw_execution_sha256']==raw['sha256'],'Exact current raw-to-strict identity')
   need(type(row['prior_passed_strict_case'])is bool,'Actual prior-case flag type')
   if row['prior_passed_strict_case']:need(case==('O0',7),'Only first already-passed strict mode7 may be reused');prior+=1
   v=read(row['report'],row['sha256']);need(v['passed']is True and v['all_bounded_readers_closed']is True and type(v['mode'])is int and(v['level'],v['mode'])==case,'Actual terminal same-case strict receipt');need(v['execution']==raw['report']and v['execution_sha256']==raw['sha256']and v['initializer_credit']==0,'Exact source/raw gate with no credit')
   for flag in('whole_Runtime_hidden_private_retry_claim','whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):need(v[flag]is False,'No inferred hidden Runtime map/private/permission equality')
   c=v['counts'];need(type(c)is dict and all(type(n)is int and n>=0 for n in c.values()),'Exact distinct measured integer counters')
   need(c['actual_precise_denials']==c['actual_unchanged_poisoned_retries']==c['entryframe64_checked']==1 and c['whole_caller_FX512_ENV28']==2,'Actual denial/same-context/fullframe/caller extents')
   need(c.get('whole_source_API_CPU40_frame64_joins',0)==(1 if case[1]in(7,8)else 0),'Finite named TLS0/1 full CPU/frame API relation')
   for field in('runtime_private_public_retry_fields','whole_registry_retry_fields','whole_widget_public_retry_fields','whole_widget_private_retry_fields'):need(c[field]>0,'Current complete named nonempty retry inventory')
   need(v['files'].get(str(BASE/'preparation-r5/verify_case_v5.py'))==CHECKER_SHA,'Actual current exact strict checker source pin');absorb(v['files'])
   # Every raw output and each separate root admission/source dependency must
   # physically enter the whole union, rather than just receipt metadata.
   execution=read(raw['report'],raw['sha256']);need(execution['passed']is True and execution['worker_closed']is True and execution['worker_executed']is True and(execution['level'],execution['mode'])==case and execution['facts']['exit_code']==0,'Actual sealed raw same case');absorb(execution['files']);del execution
   candidates=[]
   if not row['prior_passed_strict_case']:
    need(v['files'].get(row['admission'])==row['admission_sha256'],'Strict caller exact fresh admission identity');candidates=[(row['admission'],row['admission_sha256'])]
   else:
    for p,h in v['files'].items():
     q=Path(p)
     if q.name=='report.json'and q.parent.parent==BASE and 'admission'in q.parent.name:
      candidate=read(q,h)
      if candidate.get('scope_identity')=='current138_preresource_strict_outputs':candidates.append((p,h))
   need(len(candidates)==1,'Exactly one actual same-case strict independent admission')
   ap,ah=candidates[0];ad=read(ap,ah);need(ad['passed']is True and ad['scope_identity']=='current138_preresource_strict_outputs'and(ad['level'],ad['mode'])==case and ad['execution']==raw['report']and ad['execution_sha256']==raw['sha256'],'Actual exact independently admitted case');need(ad['strict_checker']==str(BASE/'preparation-r5/verify_case_v5.py')and ad['strict_checker_sha256']==CHECKER_SHA,'Current checker5 physical admission');need(ad['helpers_imported']is False and ad['worker_executed']is False and ad['source_model_executed']is False and ad['initializer_credit']==0,'Pre-import admission does not substitute semantic outcome');absorb(ad['files']);del ad
   rows.append(dict(level=case[0],mode=case[1],report=row['report'],sha256=row['sha256']))
   summary.append(dict(level=case[0],mode=case[1],strict_report=row['report'],strict_sha256=row['sha256'],raw_report=raw['report'],raw_sha256=raw['sha256'],admission=ap,admission_sha256=ah,counts=c))
   for k,n in c.items():counts[k]=counts.get(k,0)+n
   del v;db.commit();print(json.dumps(dict(case_count=len(rows),level=case[0],mode=case[1])),flush=True)
  need(prior==1 and seen=={(l,m)for l in('O0','O2')for m in range(1,13)},'Exact24 unique typed actual cases and one prior pass')
  need(counts['actual_precise_denials']==counts['actual_unchanged_poisoned_retries']==counts['entryframe64_checked']==24 and counts['whole_caller_FX512_ENV28']==48 and counts['whole_source_API_CPU40_frame64_joins']==4,'Full actual aggregate obligations without synthetic/raw success substitution')
  aggregate=pin(R/'tools/m4-138-preresource-strict-review/aggregate_v1.py',AGGREGATE_SHA);pin(__file__);pin(sys.executable);db.commit()
  # One physically bounded streamed leaf file at a time, including source and
  # all actual raw output facts. No giant all-case in-memory dictionary.
  total=db.execute('SELECT count(*) FROM deps').fetchone()[0]
  union=out/'whole-ordinary-union.json'
  with union.open('w',encoding='utf-8',newline='\n')as f:
   f.write('{"passed":true,"scope":"Whole exact physically rehashed ordinary24strict/raw/source union; no archive reader or credit","files":{\n');first=True
   for path,h in db.execute('SELECT path,digest FROM deps ORDER BY path'):
    need(sha(path)==h,'Whole admitted source/raw union stable at final boundary')
    if not first:f.write(',\n')
    f.write(json.dumps(path)+':'+json.dumps(h));first=False
   f.write('\n}}\n')
  rows.sort(key=lambda r:(r['level'],r['mode']));manifest=dict(independent_ROOT_admission=True,scope_identity='current138_preresource_24_actual_strict_aggregate',strict_cases=rows,production_sha256=PRODUCTION_SHA,batch_sha256=a.batch_sha,whole_ordinary_union=str(union),whole_ordinary_union_sha256=sha(union),whole_dependency_count=total,counts=counts,hidden_Runtime_map_equality_claim=False,hidden_private_equality_claim=False,permission_map_equality_claim=False,accepted_function_credit=0,initializer_credit=0)
  (out/'aggregate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'actual-case-domain-joins.json').write_text(json.dumps(summary,indent=2)+'\n')
  (out/'ROOT-recipe.txt').write_text(f'ROOT inspect this terminal admission/whole ordinary union before aggregation.\n{sys.executable} -B {aggregate} {out/"aggregate-manifest.json"} {sha(out/"aggregate-manifest.json")} {a.aggregate_name}\nAggregate rehashes its per-case physical filemaps; whole admission union explicitly supplements every raw/admission source dependency. No acceptance credit or hidden map/permission proof.\n')
  metadata={str(p):sha(p)for p in(out/'aggregate-manifest.json',union,out/'actual-case-domain-joins.json',out/'ROOT-recipe.txt',Path(a.batch).resolve(),Path(__file__).resolve(),aggregate)};passed=True
 except BaseException:
  import traceback
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  db.close()
  if passed:metadata[str(out/'ordinary-union.sqlite')]=sha(out/'ordinary-union.sqlite')
  result=dict(passed=passed,scope='ROOT actual24 typed strict receipt/source/raw whole-union admission; aggregation remains unexecuted',case_count=len(rows),counts=counts,whole_dependency_count=total if passed else None,dependency_union_standard_filemap=str(out/'whole-ordinary-union.json')if passed else None,aggregate_executed=False,worker_executed=False,capture_reader_opened=False,hidden_Runtime_map_equality_claim=False,hidden_private_equality_claim=False,permission_map_equality_claim=False,accepted_function_credit=0,initializer_credit=0,files=metadata)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,case_count=len(rows),sha256=sha(out/'report.json'))),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('batch_sha');p.add_argument('name');p.add_argument('aggregate_name');main(p.parse_args())
