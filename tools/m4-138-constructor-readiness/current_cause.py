"""Ordinary-file causal join for current r8 FS restore shadowing refusal."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-constructor-readiness'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,str(p);pins[str(p)]=v;return p
 root=R/'reports/m4-138-constructor-readiness/current-failure-r2'
 d=json.loads(pin(root/'report.json','80cf83859a2b212e2d3703cd34250fe704ac2e98c30313d706faf34486196b38').read_bytes())
 assert d['passed']and d['reader_closed']and d['initializer_credit']==0
 def raw(n):
  p=(root/n).resolve();return pin(p,d['files'][str(p)]).read_bytes()
 prefix='sequence-0/selected/'
 reason=raw(prefix+'locale-fault-reason.bin').decode();fault=struct.unpack('<4I',raw(prefix+'locale-fault.bin'))
 assert fault==(1,0x78001371,0x2000177c,43)
 a=list(struct.iter_unpack('<IIQII',raw(prefix+'locale-source-accesses.bin')))
 matches=[(i,r)for i,r in enumerate(a)if r[1]==0x7ffde000 and r[2]==fault[2]and r[3:]==(4,1)]
 assert matches==[(1700,(0x58aece,0x7ffde000,0x2000177c,4,1)),(1740,(0x7800136a,0x7ffde000,0x2000177c,4,1))]
 mirror=list(struct.iter_unpack('<12Q',raw(prefix+'constructor-source-mirror-accesses.bin')))
 frame={}
 for row in mirror:
  if row[5]and row[3]==4 and fault[2]<=row[2]<fault[2]+12:frame[row[2]]=row[4]
 assert frame=={0x2000177c:0x200017b4,0x20001780:0x5ba08b,0x20001784:0}
 guard=pin(R/'reports/m4-constructor-native/service-preparation-r5/fs_operations.inc').read_text()
 assert 'source_accesses_.rbegin(),source_accesses_.rend()'in guard
 assert 'case 0x58aece:handler=0x5ba08b;'in guard and 'switch(install->pc)'in guard
 assert 'runtime.memory().load<unsigned>({head+4})!=0x7800ef03'in guard
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Ordinary current fault/source-journal/private-mirror causal join only; no reader or native worker',
  reader_opened=False,native_execution_performed=False,initializer_credit=0,
  current_source_reason=reason,current_fault_words=list(fault),same_head_source_store_candidates=[dict(index=i,row=r)for i,r in matches],
  latest_constructor_frame_mirror_words=[frame[fault[2]+4*i]for i in range(3)],
  conclusion='Latest matching FS head write is accepted CRT predecessor restore0x7800136a, shadowing original literal constructor install0x58aece. Guard applies constructor-install switch to restoration PC, then rejects game handler0x5ba08b against CRT handler0x7800ef03.',
  smallest_repair='Distinguish genuine constructor install provenance from subsequent CRT restore to same head; authenticate exact literal constructor install/root scope/full12B mirror and preserve inherited CRT checks. Bind intervening restore to accepted CRT provenance rather than broadly accepting any old same-head row.',
  constraints=['Do not broaden to arbitrary handler/frame/PC','Preserve previous+handler+scope full frame relation and finite predecessor ordering','Keep active same-thread constructor scope and source store witness','Require fresh independent prelaunch/build/controller receipts before next worker'],files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
