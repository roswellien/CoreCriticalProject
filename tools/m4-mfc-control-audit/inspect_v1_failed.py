"""Inspect causal facts from immutable actual MFC controls, without acceptance."""
import hashlib, importlib.util, json, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main(name):
 out=ROOT/'reports/m4-mfc-control-audit'/name;assert not out.exists();out.mkdir(parents=True)
 pins={};results=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return p
 pin(__file__)
 receipt=json.loads(pin(ROOT/'reports/m4-mfc-review/controls-execution-r1/report.json','a938c73cf79afa61d79ae8a4425359346e8beefe132b3b49cf6ab6582186e68d').read_bytes());assert receipt['passed']
 d=module('independent_control_archive_reader',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
 for level in receipt['levels']:
  a=d.DirectSet(pin(level['capture'],level['capture_sha256']),pin)
  try:
   for case in range(21):
    base=f'case-{case}/first-live/';tags=a.words(f'case-{case}/first.bin',1246,'Q')[:32]
    ws=list(struct.iter_unpack('<32Q',a.data(base+'mfc-allocation-witnesses.bin')))
    alloc=list(struct.iter_unpack('<16Q',a.data(base+'locale-allocations.bin')))
    fault=a.words(base+'locale-fault.bin',4)
    reason=a.data(base+'locale-fault-reason.bin').decode() if case else ''
    state=a.data(f'case-{case}/first.bin')[4272:7776]
    rootregs={n:struct.unpack_from('<I',state,o)[0] for n,o in [('eax',2216),('ebx',2232),('ecx',2248),('esp',2312),('eip',2472)]}
    projections=list(struct.iter_unpack('<8I',a.data(base+'locale-research-projections.bin')))
    research=list(struct.iter_unpack('<IIQII',a.data(base+'locale-research-accesses.bin')))
    results.append(dict(level=level['level'],case=case,tags=tags,fault=fault,reason=reason,witnesses=ws,allocations=alloc,State=rootregs,
                        last_research_projections=projections[-6:],last_research_accesses=research[-6:]))
    print(json.dumps(dict(level=level['level'],case=case,completed=tags[4],stage=fault[3],pc=hex(fault[1]),address=hex(fault[2]),reason=reason,MFC=len(ws),allocated=sum(r[6]==4 for r in alloc),last_mfc=ws[-1][20:31]if ws else (),State=rootregs)),flush=True)
  finally:a.close()
 (out/'facts.json').write_text(json.dumps(dict(scope='Read-only actual causal fact inspection; no acceptance',cases=results,files=pins),indent=2)+'\n')
 print(json.dumps(dict(facts=str(out/'facts.json'),sha256=sha(out/'facts.json'))))
if __name__=='__main__':main(sys.argv[1])
