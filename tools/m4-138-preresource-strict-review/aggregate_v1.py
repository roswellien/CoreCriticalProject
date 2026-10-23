"""Require all24 independently admitted actual strict case receipts; no worker."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(manifest,digest,name):
 out=R/'reports/m4-138-preresource-strict-review'/name;assert not out.exists();files={}
 def pin(p,h):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';assert sha(p)==h;assert files.setdefault(str(p),h)==h;return p
 m=json.loads(pin(manifest,digest).read_bytes());assert m['independent_ROOT_admission']is True
 rows=m['strict_cases'];assert len(rows)==24;seen=set();counts={}
 for row in rows:
  p=pin(row['report'],row['sha256']);v=json.loads(p.read_bytes());case=v['level'],v['mode'];assert case not in seen;seen.add(case)
  assert v['passed']is True and v['all_bounded_readers_closed']is True and v['initializer_credit']==0
  assert v['counts']['actual_precise_denials']==v['counts']['actual_unchanged_poisoned_retries']==v['counts']['entryframe64_checked']==1
  assert v['counts']['whole_caller_FX512_ENV28']==2
  for q,h in v['files'].items():pin(q,h)
  for k,n in v['counts'].items():counts[k]=counts.get(k,0)+n
 assert seen=={(l,m)for l in('O0','O2')for m in range(1,13)}
 out.mkdir();files[str(Path(__file__).resolve())]=sha(__file__)
 result=dict(passed=True,scope='All24 actual strict current138 pre-resource legacy refusals; complete ordinary per-case source, retry, frame and actual lifetime gates',counts=counts,case_count=24,worker_executed=False,capture_reader_opened=False,initializer_credit=0,accepted_function_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
