"""Finite current141 5F2000 page source/API no-write probe; ordinary only.

Reuses the reviewed footprint141_v2 operand scanner unchanged (imported, not
copied) over the same 70 current original/native source and API derivation
artifacts, and records every operand on page 5F2000. Any WRITE operand there is
a violation. Complements global5F2000-relation141-r1 (whole-page endpoint
equality/carry), which cannot exclude a transient write later restored.
Coverage is the collected ledgers only; inventory completeness is not claimed.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PAGE=0x5f2000
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(__file__);F=load('footprint_scanner',R/'tools/m4-startup141-paired/footprint141_v2.py');J=load('stream_json',R/'tools/m4-138-controls-review/full_raw_review_v2.py')
 FP=json.loads(pin(R/'reports/m4-startup141-paired/footprint141-r2/report.json').read_bytes());assert FP['passed']is True
 inventory=json.loads(pin(FP['output']['path'],FP['output']['sha256']).read_bytes())['inventory'];assert len(inventory)==70
 reads=collections.Counter();writes=[];per=[];offsets=collections.Counter()
 for item in inventory:
  path=Path(item['artifact']);pin(path,FP['files'][str(path.resolve())]);found=collections.defaultdict(list)
  if path.name=='source-derivation.json':F.scan(json.loads(path.read_bytes()),(),found)
  else:
   for case in F.stream_cases(path,J):F.scan(case,(),found)
  n=0;r=0
  for key,rows in found.items():
   for pc,address,value,width,write in rows:
    n+=1
    if address+width<=PAGE or address>=PAGE+4096:continue
    if write:writes.append(dict(family=item['family'],artifact=str(path),key='/'.join(key),pc=pc,address=address,width=width,value=value))
    else:r+=1;reads[item['family']]+=1;offsets[address]+=1
  assert n==item['access_rows'],('Same collected operand extent as footprint141-r2',str(path),n,item['access_rows'])
  per.append(dict(family=item['family'],artifact=str(path),page_reads=r))
 for p_,h in list(pins.items()):assert sha(p_)==h
 rp=out/'nowrite.json';rp.write_text(json.dumps(dict(per_artifact=per,read_addresses={hex(a):n for a,n in sorted(offsets.items())},writes=writes[:2000]),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=not writes,scope='Current141 5F2000 page: no write operand in any collected current source/API derivation ledger (70 artifacts, same extent as footprint141-r2); reads recorded; not inventory completeness or credit',
  artifacts=len(inventory),page_reads=sum(reads.values()),page_read_addresses=sorted(hex(a)for a in offsets),reads_by_family=dict(reads),page_writes=len(writes),inventory_completeness_claim=False,
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','artifacts','page_reads','page_read_addresses','reads_by_family','page_writes')}))
 if writes:raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
