"""Bounded indexed actual first-fault rows; no full capture reader/hash credit."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};results=[];index_bytes=payload_bytes=0
 p=R/'tools/m4-pipeline/capture_bundle.py';sys.path.insert(0,str(p.parent));s=importlib.util.spec_from_file_location('bounded_mixed_reasons',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);pins[str(p)]=sha(p)
 for level in('O0','O2'):
  root=R/'reports/m4-tree-review/mixed-controls-execution-r3'/level;tp=root/'transport.json';pins[str(tp)]=sha(tp);t=json.loads(tp.read_bytes());names={f'case-{case}/first/actual-live/{n}' for case in(8,9) for n in('locale-fault-reason.bin','locale-fault.bin','registry-exception-message.bin')};got={}
  for part in t['parts']:
   with m._locked_stream(root/part['bundle']) as f:
    magic,size,h=m.HEADER.unpack(f.read(m.HEADER.size));assert magic==m.MAGIC and size==part['index_bytes'];raw=f.read(size);index_bytes+=size;assert hashlib.sha256(raw).digest()==h and h.hex()==part['index_sha256'];idx=json.loads(raw);base=m.HEADER.size+size
    for e in idx['files']:
     if e['path'] not in names:continue
     assert e['size']<=1024;f.seek(base+e['offset']);b=f.read(e['size']);payload_bytes+=len(b);assert len(b)==e['size'] and hashlib.sha256(b).hexdigest()==e['sha256'];got[e['path']]=b
  assert set(got)==names
  for case in(8,9):
   stem=f'case-{case}/first/actual-live/';reason=got[stem+'locale-fault-reason.bin'].decode();assert reason==got[stem+'registry-exception-message.bin'].decode();fault=struct.unpack('<4I',got[stem+'locale-fault.bin']);r=dict(level=level,scenario=case,fault=list(fault),reason=reason);results.append(r);print(json.dumps(r),flush=True)
 pins[str(Path(__file__).resolve())]=sha(__file__);report=dict(passed=True,scope='Bounded index-authenticated actual scenario8/9 first fault records; no full archive authenticity renewal or acceptance credit',index_bytes=index_bytes,payload_bytes=payload_bytes,rows=results,all_streams_closed=True,canonical_readers_opened=0,full_archive_hash_verified=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(sha256=sha(out/'report.json'),payload_bytes=payload_bytes,index_bytes=index_bytes)))
if __name__=='__main__':main(sys.argv[1])
