"""Authorized small indexed fault records only; no canonical reader or full payload hash."""
import hashlib, importlib.util, json, os, struct, sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True);rows=[];payload_bytes=0;index_bytes=0;pins={}
 script=R/'tools/m4-pipeline/capture_bundle.py';sys.path.insert(0,str(script.parent));spec=importlib.util.spec_from_file_location('mixed_tiny_locked_reader',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);pins[str(script)]=sha(script)
 for level in('O0','O2'):
  root=R/'reports/m4-tree-review/mixed-controls-execution-r1'/level;tp=root/'transport.json';t=json.loads(tp.read_bytes());pins[str(tp)]=sha(tp);got={}
  names=('case-1/first/sample.bin','case-1/first/actual-live/locale-fault-reason.bin','case-1/first/actual-cleanup-hardware-before.bin','case-1/first/actual-cleanup-hardware-after.bin')
  for part in t['parts']:
   path=root/part['bundle']
   with m._locked_stream(path)as f:
    magic,size,expected=m.HEADER.unpack(f.read(m.HEADER.size));assert magic==m.MAGIC and size==part['index_bytes'];raw=f.read(size);index_bytes+=size;assert hashlib.sha256(raw).digest()==expected and expected.hex()==part['index_sha256'];index=json.loads(raw);base=m.HEADER.size+size
    for e in index['files']:
     if e['path']not in names:continue
     assert e['size']<=9968;f.seek(base+e['offset']);v=f.read(e['size']);payload_bytes+=len(v);assert len(v)==e['size']and hashlib.sha256(v).hexdigest()==e['sha256'];got[e['path']]=v
  assert set(got)==set(names);sample=got[names[0]];assert len(sample)==9968;tag=struct.unpack_from('<32Q',sample);before=sample[8880:9424];after=sample[9424:9968]
  row=dict(level=level,tags=list(tag),precise_reason=got[names[1]].decode(),host_raw_differences=[dict(offset=i,before=a,after=b)for i,(a,b)in enumerate(zip(before,after))if a!=b],ENV_before=before[512:540].hex(),ENV_after=after[512:540].hex(),cleanup_raw_differences=[i for i,(a,b)in enumerate(zip(got[names[2]],got[names[3]]))if a!=b]);rows.append(row)
  print(json.dumps(row))
 report=dict(passed=True,scope='Small authorized diagnostic exact indexed sample/fault/cleanup records only, no whole archive authenticity renewal',payload_bytes=payload_bytes,index_bytes=index_bytes,canonical_readers_opened=0,full_archive_hash_verified=False,all_streams_closed=True,rows=rows,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(sha256=sha(out/'report.json'),payload_bytes=payload_bytes,index_bytes=index_bytes)))
if __name__=='__main__':main(sys.argv[1])
