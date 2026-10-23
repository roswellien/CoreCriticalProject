"""ROOT-admitted serial ordinary admission + strict checks; never native workers.

Requires independently passed O0/mode7 strict receipt. Exactly the remaining23
current sealed raw cases then receive fresh admission/checker directories.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PRODUCTION_SHA='59fbbf6c9da98b54b2bf84fe7ee7582557b789ab73260255822ca93206b9c69f'
BUILDER_SHA='f9a62165a3e18622a39a5382cd9b33f2c41e253a0bf306951e5b09ca84d6833f'
BUILDER_PREP_SHA='eb3551dc4662fc0ff24a8e1d2acb44ad3056e9141d0e5ab93da5dc50238c83e6'
P=R/'reports/m4-138-preresource-strict-review/serial-batch-preparation-r2'

def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:need(k not in d,'No duplicated field '+k);d[k]=v
 return d

def main(a):
 need(re.fullmatch('[A-Za-z0-9_-]{1,40}',a.name),'Fresh bounded output prefix')
 out=R/'reports/m4-138-preresource-strict-review'/a.name;need(not out.exists(),'Fresh immutable batch output')
 admitted_path=Path(a.admission).resolve();need(sha(admitted_path)==a.admission_sha,'Independent ROOT controller admission SHA')
 admission=json.loads(admitted_path.read_bytes(),object_pairs_hook=unique)
 need(admission['passed']is True and admission['scope_identity']=='current138_preresource_serial_strict_remaining23','Independent exact serial-controller scope')
 need(admission['no_native_workers']is True and admission['no_archive_readers']is True,'Only ordinary admission/checker subprocesses')
 admitted=admission['files'];files={str(admitted_path):a.admission_sha};spellings={};runs=[];processes=[];passed=False;started=time.monotonic();child_active=False
 for p,h in admitted.items():
  q=Path(p).resolve();need(str(q)==p and q.suffix.lower()not in('.mwb','.mwi','.zip')and q.name!='transport.json','Closed canonical-spelled ordinary input')
  need(spellings.setdefault(p.casefold(),p)==p,'Unique physical spelling');need(sha(q)==h,'Entire admitted control closure before subprocess')
 def pin(p,h=None):
  q=Path(p).resolve();v=sha(q);need(h is None or h==v,'Exact immutable input');need(q.is_relative_to(out)or admitted.get(str(q))==v,'External controller input already ROOT admitted')
  need(files.setdefault(str(q),v)==v,'No conflicting path hash');return q
 def read(p,h=None):return json.loads(pin(p,h).read_bytes(),object_pairs_hook=unique)
 prep=read(P/'report.json',admission['preparation_sha256']);need(prep['passed']and not prep['controller_executed'],'Unexecuted current immutable preparation')
 for p,h in prep['files'].items():pin(p,h)
 production=read(R/'reports/m4-138-preresource-root-review/root-case-production-r1/report.json',PRODUCTION_SHA)
 need(production['passed']and production['raw_cases']==24 and production['all_workers_terminal']and production['strict_outcomes_verified']is False,'Actual24 terminal raw production only')
 manifest=read(P/'raw-case-manifest.json');need(manifest['production_sha256']==PRODUCTION_SHA and manifest['runs']==production['runs'],'Exact frozen raw case rows with no invented strict outcome')
 rows=manifest['runs'];need(len(rows)==24 and {(r['level'],r['mode'])for r in rows}=={(l,m)for l in('O0','O2')for m in range(1,13)},'Exactly24 distinct current raw cases')
 need([(r['level'],r['mode'])for r in rows]==[(l,m)for l in('O0','O2')for m in range(1,13)],'Exact actual serial production order')
 builder=pin(R/'tools/m4-138-preresource-strict-review/root_admission_builder_v4.py',BUILDER_SHA)
 read(R/'reports/m4-138-preresource-strict-review/admission-builder-preparation-r4/report.json',BUILDER_PREP_SHA)
 checker=pin(R/'reports/m4-138-preresource-strict-review/preparation-r5/verify_case_v5.py',prep['strict_checker_sha256']);python=pin(sys.executable)
 prior=read(a.mode7_strict,a.mode7_strict_sha)
 def strict_facts(v,row):
  need(v['passed']is True and v['all_bounded_readers_closed']is True and v['initializer_credit']==0,'Passed complete strict receipt, never failed receipt reuse')
  need((v['level'],v['mode'])==(row['level'],row['mode'])and v['execution']==row['report']and v['execution_sha256']==row['sha256'],'Exact current actual raw-to-strict case binding')
  c=v['counts'];need(c['actual_precise_denials']==c['actual_unchanged_poisoned_retries']==c['entryframe64_checked']==1 and c['whole_caller_FX512_ENV28']==2,'Whole strict case finite extents')
  need(c.get('whole_source_API_CPU40_frame64_joins',0)==(1 if row['mode']in(7,8)else 0),'Exact finite0/1 whole source API frame/CPU join')
 old=next(r for r in rows if(r['level'],r['mode'])==('O0',7));strict_facts(prior,old)
 need(admission['mode7_strict_report']==str(Path(a.mode7_strict).resolve())and admission['mode7_strict_sha256']==a.mode7_strict_sha,'ROOT binds successful first strict case explicitly')
 # ROOT already admitted prior full physical strict receipt. Do not remerge
 # its ~48k filemap or manufacture a new semantic outcome from raw success.
 runs.append(dict(level='O0',mode=7,report=str(Path(a.mode7_strict).resolve()),sha256=a.mode7_strict_sha,raw_execution=old['report'],raw_execution_sha256=old['sha256'],prior_passed_strict_case=True))
 # Preflight every future output namespace before any child starts.
 for row in rows:
  if(row['level'],row['mode'])==('O0',7):continue
  for suffix in('admission','strict'):
   need(not(R/'reports/m4-138-preresource-strict-review'/f"{a.name}-{suffix}-{row['level']}-mode{row['mode']}").exists(),'All fresh child namespaces')
 out.mkdir()
 def launch(command,label):
  nonlocal child_active
  # Synchronous subprocess.run guarantees at most one child; no native worker
  # binary is ever permitted in this finite command whitelist.
  need(command[0]==str(python)and command[1]=='-B'and command[2]in(str(builder),str(checker)),'Exact ordinary controller child whitelist')
  child_active=True;t=time.monotonic()
  with(out/(label+'.stdout')).open('wb')as stdout,(out/(label+'.stderr')).open('wb')as stderr:
   try:result=subprocess.run(command,cwd=R,stdout=stdout,stderr=stderr,timeout=1800,creationflags=0x08000000)
   finally:child_active=False
  processes.append(dict(label=label,command=command,exit_code=result.returncode,elapsed_seconds=time.monotonic()-t))
  need(result.returncode==0,'Fail stop on child '+label)
 try:
  for row in rows:
   level,mode=row['level'],row['mode']
   if(level,mode)==('O0',7):continue
   # Rehash this single raw receipt; each independent builder rehashes every
   # output and exact current physical source/native-owner closure itself.
   execution=pin(row['report'],row['sha256']);d=read(execution);need(d['passed']and d['worker_closed']and d['worker_executed']and(d['level'],d['mode'])==(level,mode),'Only actual terminal current raw cases')
   aname=f'{a.name}-admission-{level}-mode{mode}';sname=f'{a.name}-strict-{level}-mode{mode}'
   launch([str(python),'-B',str(builder),str(execution),row['sha256'],aname],f'{level}-{mode}-admission')
   ap=R/'reports/m4-138-preresource-strict-review'/aname/'report.json';ah=sha(ap);av=json.loads(ap.read_bytes(),object_pairs_hook=unique)
   need(av['passed']is True and av['scope_identity']=='current138_preresource_strict_outputs'and(av['level'],av['mode'])==(level,mode)and av['execution']==row['report']and av['execution_sha256']==row['sha256'],'Fresh independent builder closes same current actual case')
   need(av['strict_checker']==str(checker)and av['strict_checker_sha256']==sha(checker)and av['helpers_imported']is False and av['source_model_executed']is False and av['worker_executed']is False,'Only closed pre-import ordinary admission')
   # The child checker itself authenticates admission.files in full before
   # importing code; this controller binds its report without helper imports.
   launch([str(python),'-B',str(checker),str(execution),row['sha256'],sname,str(ap),ah],f'{level}-{mode}-strict')
   sp=R/'reports/m4-138-preresource-strict-review'/sname/'report.json';sh=sha(sp);sv=json.loads(sp.read_bytes(),object_pairs_hook=unique);strict_facts(sv,row)
   need(sv['files'].get(str(ap))==ah,'Strict child physically binds exact independent admission')
   runs.append(dict(level=level,mode=mode,report=str(sp),sha256=sh,raw_execution=row['report'],raw_execution_sha256=row['sha256'],admission=str(ap),admission_sha256=ah,prior_passed_strict_case=False))
   (out/'progress.json').write_text(json.dumps(dict(completed_strict_cases=len(runs),last_case=[level,mode]),indent=2)+'\n')
   print(json.dumps(dict(strict_cases=len(runs),level=level,mode=mode,report_sha256=sh)),flush=True)
  need(len(runs)==24 and len(processes)==46,'Exactly23 fresh admissions plus23 strict checks and one actual prior strict case')
  need({(r['level'],r['mode'])for r in runs}=={(l,m)for l in('O0','O2')for m in range(1,13)},'All24 distinct strict actual outcomes')
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p in out.iterdir():
   if p.is_file():files[str(p.resolve())]=sha(p)
  for p,h in files.items():need(sha(p)==h,'Controller input/output files stable at terminal boundary')
  result=dict(passed=passed,scope='Serial exact23 fresh independent ordinary admissions+strict checks, one ROOT-admitted passing mode7 retained; aggregation/acceptance separate',production_sha256=PRODUCTION_SHA,strict_cases=runs,processes=processes,strict_case_count=len(runs),all_children_terminal=not child_active,native_worker_executed=False,capture_reader_opened=False,acceptance_executed=False,configuration_created=False,accepted_function_credit=0,initializer_credit=0,elapsed_seconds=time.monotonic()-started,files=files)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,strict_case_count=len(runs),report_sha256=sha(out/'report.json'))),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('admission');p.add_argument('admission_sha');p.add_argument('name');p.add_argument('mode7_strict');p.add_argument('mode7_strict_sha');main(p.parse_args())
