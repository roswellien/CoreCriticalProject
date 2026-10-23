"""Unexecuted narrow CS24/TLS64 source supplement; ROOT admission required."""
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BATCH_SHA='2cf7c24beaa1bf64ce79861c1b08c2ade3e3498acbde8c697f819119341ec654'
def main(admission_path,admission_sha,name):
 out=R/'reports/m4-138-preresource-strict-review'/name;assert not out.exists();out.mkdir();pins={};passed=False;cases=[];counts=collections.Counter()
 def sha(p):
  with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
 def pin(p,h):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';assert sha(p)==h;assert pins.setdefault(str(p),h)==h;return p
 admission_path=pin(admission_path,admission_sha);admission=json.loads(admission_path.read_bytes())
 assert admission['passed']is True and admission['scope_identity']=='current138_preresource_named_facets'
 declared=admission['files']
 def ordinary(p):
  p=Path(p).resolve();assert str(p)in declared;return pin(p,declared[str(p)])
 def module(p,n):
  p=ordinary(p);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  batch_path=ordinary(R/'reports/m4-138-preresource-strict-review/root-strict-remaining23-r1/report.json');assert sha(batch_path)==BATCH_SHA;batch=json.loads(batch_path.read_bytes());assert batch['passed']is True and batch['strict_case_count']==24 and batch['all_children_terminal']is True
  for p in('tools/m4-mfc1168-native/persistent_source.py','tools/m4-crt-locale-batch-model-review/interpreter_v2.py','tools/m4-formatting-source/flag_domain.py'):ordinary(R/p)
  F=module(R/'tools/m4-138-preresource-strict-review/named_facets_v1.py','extra_named_MFC_facets');L=module(R/'tools/m4-mfc1168-native/persistent_source.py','extra_named_MFC_literal')
  build=json.loads(ordinary(R/'reports/m4-138-preresource-controls/build-r4/build.json').read_bytes());prep=json.loads(ordinary(build['preparation']).read_bytes());parent=json.loads(ordinary(prep['parent_preparation']).read_bytes());inputs=parent['inputs']
  contracts_path=ordinary(R/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json');assert sha(contracts_path)=='f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64';contracts=json.loads(contracts_path.read_bytes())
  seen=set()
  for row in batch['strict_cases']:
   rp=ordinary(row['report']);assert sha(rp)==row['sha256'];key=row['level'],row['mode'];assert key not in seen;seen.add(key)
   # This is a scoped streaming declaration lookup, not a raw union expansion.
   # Retain only exact paths needed by the narrow functions (<=MFC entry pages).
   with rp.open('rb')as f:head=f.read(65536)
   marker=b'  "files":';assert head.count(marker)==1
   meta=json.loads(head[:head.index(marker)]+b'  "files":{}}');assert(meta['level'],meta['mode'])==key
   ep=ordinary(row['raw_execution']);assert sha(ep)==row['raw_execution_sha256']
   with ep.open('rb')as f:head=f.read(65536)
   pos=head.index(marker);execution=json.loads(head[:pos]+b'  "files":{}}');root=Path(execution['facts']['arguments'][-3]).resolve()
   allowed={};causal_path=rp.parent/'causal-controls.json';rawprefix=str(root).casefold();inside=False
   with rp.open('rb')as f:
    for line in f:
     if line.startswith(marker):inside=True;continue
     if inside and line.startswith(b'  }'):inside=False;continue
     if not inside:continue
     item=json.loads(b'{'+line.strip().rstrip(b',')+b'}');assert len(item)==1
     p,h=next(iter(item.items()));p=Path(p).resolve();keep=p==causal_path
     if p.is_relative_to(root):
      rel=p.relative_to(root).as_posix();base=f'control-{key[1]}/'
      keep=(rel.startswith(base+'MFC/entry/')or rel.startswith(base+'MFC/refused/')or rel in(base+'retry-before/memory-536875008-4096.bin',base+'refusal.txt'))
     if keep:assert allowed.setdefault(str(p),h)==h
   assert str(causal_path)in allowed;case_data=json.loads(pin(causal_path,allowed[str(causal_path)]).read_bytes());assert len(case_data)==1;c=case_data[0];assert(c['level'],c['mode'])==key
   class Facade:
    def data(self,k):
     p=(root/k).resolve();assert p.is_relative_to(root)and str(p)in allowed;assert p.stat().st_size<=1024*1024;return pin(p,allowed[str(p)]).read_bytes()
   a=Facade();result=dict(level=key[0],mode=key[1],CS24=None,TLS64=None)
   if c['terminal'][7]:result['CS24']=F.guest_CS24(a,key[1],inputs,c);counts['whole_borrowed_guestCS24_prefixes']+=1
   if key[1]==11:result['TLS64']=F.TLS_frame64(a,11,inputs,c,L,contracts);counts['source_TLS_refusal_frame64']+=1
   cases.append(result)
  assert seen=={(l,m)for l in('O0','O2')for m in range(1,13)}and counts==dict(whole_borrowed_guestCS24_prefixes=12,source_TLS_refusal_frame64=2)
  q=out/'named-source-facet-joins.json';q.write_text(json.dumps(cases,indent=2)+'\n');pins[str(q)]=sha(q)
  ordinary(Path(__file__));ordinary(sys.executable)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Narrow independently source-derived actual CS24/TLS64 supplement only; full24 strict/fullphysical union retained separately',counts=dict(counts),all_bounded_readers_closed=True,whole_raw_inventory_rehashed=False,source_seed_from_AFTER=False,worker_executed=False,capture_archives_opened=0,initializer_credit=0,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
