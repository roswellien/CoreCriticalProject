"""Bounded exact current version common caller CPU diagnostic, no source execution."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();out.mkdir();pins={};reader=None;closed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 o=read(R/'reports/m4-version-source/original-common-execution-r1/report.json','58cfb381f6cd3b1d59769d82e6c88cfe5d0ca517cada7020fe221e6fddb3ca68');n=read(R/'reports/m4-version-source/fixture-common-execution-r1/report.json','bb756ca14b542246a89c8a5e63b4c67c0bd295c8fb7cea032a171a3f5bb9504f');assert o['passed']and n['passed']and o['all_workers_terminal']and n['all_workers_terminal']
 spec=importlib.util.spec_from_file_location('narrow_version_reader',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 rows={}
 def retain(key,raw):
  q=out/(key+'.bin');q.write_bytes(raw);pin(q);return list(struct.unpack('<10I',raw))
 try:
  transport=Path(o['run']['capture'])/'transport.json';metadata=read(transport,o['run']['transport_sha256']);assert metadata['logical_files']<=2048 and metadata['payload_bytes']<=256*1024*1024 and len(metadata['parts'])<=8
  reader=m.DirectSet(transport,pin)
  rec=reader.data('phase/0/0.bin');assert len(rec)==356992
  rows['original']=dict(before=retain('original-before-CPU',rec[36:76]),after=retain('original-after-CPU',rec[76:116]),authored=retain('original-authored-CPU',reader.data('common-caller/authored-CPU.bin')),application=list(struct.unpack('<8I',reader.data('common-caller/application.bin'))),registration=list(struct.unpack('<I',reader.data('cleanup/0/registry.bin'))))
 finally:
  if reader:reader.close()
  closed=True
 for level in('O0','O2'):
  run=n['runs'][level];manifest=read(run['output_manifest'],run['output_manifest_sha256']);root=Path(run['capture']);row={}
  for side in('before','after'):
   key='phase-0/'+side+'/CPU.bin';p=pin(root/key,manifest[key]['sha256']);raw=p.read_bytes();assert len(raw)==manifest[key]['bytes']==40;row[side]=retain(level+'-'+side+'-CPU',raw)
  rows[level]=row
 pin(__file__);pin(sys.executable)
 for p,h in pins.items():assert sha(p)==h
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Current whole raw root endpoint CPU10 tuples only; no acceptance policy changes',reader_closed=closed,archive_reader_opened=True,initializer_credit=0,rows=rows,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),reader_closed=closed,rows=rows)))
if __name__=='__main__':main(sys.argv[1])
