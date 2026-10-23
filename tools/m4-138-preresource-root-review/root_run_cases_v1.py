"""Serial narrowly admitted remaining legacy refusal cases; no strict credit."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-preresource-root-review/root-case-production-r1';assert not out.exists();out.mkdir();runs=[];passed=False;started=time.monotonic()
admission=R/'reports/m4-138-preresource-root-review/root-run-admission-r1/report.json';h='8dfa8a7f753a692f3d47a3a5f4d6a7ca9700da25ed26910f2fd79e5235bca426'
try:
 assert sha(admission)==h
 for level in('O0','O2'):
  for mode in range(1,13):
   name=f'execution-{level}-mode{mode}-r'+('2'if level=='O0'and mode==1 else'1')
   report=R/'reports/m4-138-preresource-controls'/name/'report.json'
   reused=level=='O0'and mode in(1,7)
   if not reused:
    assert not report.parent.exists()
    command=[sys.executable,'-B',str(R/'tools/m4-138-preresource-controls/run_v3.py'),name,str(admission),h,level,str(mode)]
    with(out/f'{level}-{mode}.stdout').open('wb')as stdout,(out/f'{level}-{mode}.stderr').open('wb')as stderr:
     result=subprocess.run(command,cwd=R,stdout=stdout,stderr=stderr,timeout=600)
    assert result.returncode==0,(level,mode,result.returncode)
   d=json.loads(report.read_bytes());assert d['passed']and d['worker_closed']and d['facts']['exit_code']==0 and d['level']==level and d['mode']==mode
   row=dict(level=level,mode=mode,report=str(report),sha256=sha(report),prior_terminal_raw_case_reused=reused)
   runs.append(row);(out/'progress.json').write_text(json.dumps(runs,indent=2)+'\n');print(json.dumps(row),flush=True)
 assert len(runs)==24;passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
finally:
 files={str(admission):h,str(Path(__file__).resolve()):sha(__file__)}
 for p in out.iterdir():
  if p.is_file():files[str(p)]=sha(p)
 d=dict(passed=passed,raw_cases=len(runs),runs=runs,all_workers_terminal=passed,strict_outcomes_verified=False,accepted_function_credit=0,initializer_credit=0,elapsed_seconds=time.monotonic()-started,files=files)
 (out/'report.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,raw_cases=len(runs),report_sha256=sha(out/'report.json'))),flush=True)
raise SystemExit(0 if passed else 1)
