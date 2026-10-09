"""Correct only original54 raw/BSS page provenance, preserving frozen r7 source."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-onexit-source'
OLD=BASE/'original-preparation-r7';OLD_SHA='91fdcc4522e5a4bb71ea44c207f878f707350328e5b4255981bb4765076d7744'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,s):
 if not x:raise ValueError(s)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh output');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Pinned input '+str(p));files[str(p)]=v;return p
 old=json.loads(pin(OLD/'report.json',OLD_SHA).read_bytes())
 for p,h in json.loads(pin(OLD/'pins.json').read_bytes())['files'].items():pin(p,h)
 for name in ('protocol.hpp','original_broker.hpp','reference_x86.asm','reference.cpp','preserve_x86.asm','CMakeLists.txt'):
  (out/name).write_bytes(pin(OLD/name).read_bytes())
 spec=pin(OLD/'spec.hpp').read_text();pack=bytearray(pin(OLD/'pages.bin',old['pack_sha256']).read_bytes())
 need(pack[:8]==b'MW4J54P1' and len(pack)==12+struct.unpack_from('<I',pack,8)[0]*4104,'Pack shape')
 sp=importlib.util.spec_from_file_location('original_page_PE',pin(ROOT/'tools/analysis/pe.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 pe=m.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 changed=[];provenance=[]
 for i in range(struct.unpack_from('<I',pack,8)[0]):
  base,permission=struct.unpack_from('<II',pack,12+i*4104);start=20+i*4104
  if base not in old['observed_pages'][17:]:continue
  raw=bytearray(4096);pieces=[]
  for s in pe.sections:
   a=pe.image_base+s['virtual_address'];lo=max(base,a);hi=min(base+4096,a+s['raw_size'])
   if lo<hi:
    off=s['raw_offset']+lo-a;raw[lo-base:hi-base]=pe.data[off:off+hi-lo];pieces.append(dict(section=s['name'],address=lo,file_offset=off,size=hi-lo))
  previous=bytes(pack[start:start+4096]);offsets=[j for j,(a,b) in enumerate(zip(previous,raw))if a!=b]
  if offsets:
   changed.append(dict(base=base,changed_bytes=len(offsets),first=offsets[0],last=offsets[-1],old_sha256=hashlib.sha256(previous).hexdigest(),new_sha256=hashlib.sha256(raw).hexdigest()));pack[start:start+4096]=raw
  provenance.append(dict(base=base,raw_pieces=pieces,zero_fill_bytes=4096-sum(p['size']for p in pieces),page_sha256=hashlib.sha256(raw).hexdigest()))
 need(len(changed)==1 and changed[0]['base']==0x5f4000,'Only raw/BSS boundary page changes')
 (out/'pages.bin').write_bytes(pack);spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);(out/'spec.hpp').write_text(spec)
 (out/'page-provenance.json').write_text(json.dumps(dict(changes=changed,observed_new_pages=provenance),indent=2)+'\n')
 for p in out.iterdir():pin(p)
 pin(__file__)
 report={k:v for k,v in old.items() if k!='files'}
 report.update(passed=True,scope='Additive original54 preparation correcting the sole raw/BSS input page; literal sources and all sequence semantics preserved',parent_preparation=str(OLD),parent_sha256=OLD_SHA,pack_sha256=sha(out/'pages.bin'),record_bytes=242304,changed_input_pages=changed,source_code_changed=False,observed_game_after_used=False,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),changes=changed)))
if __name__=='__main__':main(sys.argv[1])
