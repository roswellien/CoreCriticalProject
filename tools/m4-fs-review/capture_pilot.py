"""Independent bounded shared-capture review; no production adoption."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,struct,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/m4-pipeline'),str(ROOT/'tools/m4-capture-shared')]
from manifests import verify_manifest
from capture_shared_v4 import SharedDirectSet
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-fs-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};started=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 seal=pin(ROOT/'reports/m4-capture-shared/seal-r1/report.json','2037a2307b70e74ad89cec3b8fd5ceae44f684132988c692acc53e95c753a3e5');s=json.loads(seal.read_bytes());assert s['passed']and not s['format_adopted']and not s['game_executed']
 for p,h in s['files'].items():pin(p,h)
 for item in s['reports'].values():
  r=json.loads(pin(item['path'],item['sha256']).read_bytes());assert r['passed']
 sp=importlib.util.spec_from_file_location('pilot_independent_canonical',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(sp);sp.loader.exec_module(D)
 records=bytes_compared=typed=0;cases=[]
 for dataset in('authored-O0','authored-O2','retained-O2'):
  base=ROOT/'reports/m4-capture-shared/benchmark-r2'/dataset;old=D.DirectSet(base/'canonical/transport.json',pin);newpath=pin(base/'shared/transport.json');new=SharedDirectSet(newpath,sha(newpath))
  try:
   assert set(old.entries)==set(new.entries)
   for n in old.entries:
    a=old.data(n);b=new.data(n);assert a==b,(dataset,n);records+=1;bytes_compared+=len(a)
    if len(a)==40:
     assert new.words(n,10)==struct.unpack('<10I',a);typed+=1
   assert new.meta['payload_bytes']==old.value['payload_bytes']
   cases.append(dict(dataset=dataset,logical_records=len(new.entries),logical_bytes=new.meta['payload_bytes'],unique_bytes=new.meta['unique_payload_bytes']))
  finally:new.close();old.close()
 assert records==32000
 source=ROOT/'reports/m4-capture-shared/benchmark-r2/authored-O0/shared';meta=json.loads((source/'transport.json').read_bytes());refusals=0
 # Fresh owned files with genuine hashes isolate semantic type checks from SHA rejection.
 for index,(location,field)in enumerate((('part','bundle_bytes'),('part','index_bytes'),('part','logical_files'),('part','payload_bytes'),('part','unique_blobs'),('part','unique_payload_bytes'),('set','logical_files'),('set','payload_bytes'),('set','unique_blobs'),('set','unique_payload_bytes'))):
  folder=out/('float-count-'+str(index));shutil.copytree(source,folder);changed=copy.deepcopy(meta);target=changed['parts'][0]if location=='part'else changed;target[field]=float(target[field]);manifest=folder/'transport.json';manifest.write_text(json.dumps(changed,separators=(',',':')),encoding='utf-8')
  try:
   reader=SharedDirectSet(manifest,sha(manifest));reader.close()
  except ValueError:refusals+=1
  else:raise AssertionError(('Reader accepted noninteger count',location,field))
  for p in folder.iterdir():pin(p)
 # Independently recheck actual rich hardware pairs, rather than accepting a summary count.
 pairs=0
 for level in('O0','O2'):
  file=pin(ROOT/f'reports/m4-capture-shared/controls-r1-{level}/hardware.bin');raw=file.read_bytes();assert len(raw)==60*1128
  for at in range(0,len(raw),1128):
   b=raw[at:at+560];a=raw[at+560:at+1120];assert struct.unpack_from('<II',raw,at+1120)==(0x734612ab,0x734612ab)
   assert b[:5]==a[:5]and struct.unpack_from('<H',b)[0]==0xa7f
   assert b[512:540]==a[512:540]and any(b[524:532])and b[24:28]==a[24:28]and struct.unpack_from('<I',b,24)[0]==0x5fa5
   for i in range(8):assert b[32+16*i:42+16*i]==a[32+16*i:42+16*i]
   for i in range(6,16):assert b[160+16*i:176+16*i]==a[160+16*i:176+16*i]==bytes((i*31+j*17+7)&255 for j in range(16))
   assert struct.unpack_from('<Q',b,544)[0]&0x400==struct.unpack_from('<Q',a,544)[0]&0x400==0;pairs+=1
 pin(__file__);pin(ROOT/'tools/m4-capture-shared/capture_shared_v4.py');pin(ROOT/'tools/m4-pipeline/manifests.py')
 closure=verify_manifest(pins)
 value=dict(passed=True,scope='Independent frozen transport pilot physical closure, all32000 logical byte comparisons, actual hardware pairs and semantic integer refusals; production consumers have not adopted it',format_adopted=False,game_executed=False,exact_full_byte_records=records,full_bytes_compared=bytes_compared,CPU_words_relations=typed,noninteger_refusals=refusals,actual_hardware_pairs=pairs,direction_flag_scope='ABI-clear DF only',physical_scope='2GiB unique payload perpart; logical references can exceed2GiB',compatibility_gaps=s['compatibility']['not_drop_in'],cases=cases,current_physical_closure=closure,elapsed_seconds=time.perf_counter()-started,files=pins)
 (out/'report.json').write_text(json.dumps(value,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps({k:value[k]for k in('passed','exact_full_byte_records','full_bytes_compared','CPU_words_relations','noninteger_refusals','actual_hardware_pairs','elapsed_seconds','format_adopted')}))
if __name__=='__main__':main(sys.argv[1])
