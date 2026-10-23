"""Independent ordinary malloc FS instruction/lift identity audit only."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h; pins[str(p)]=v;return p
 root=R/'reports/m4-crt-allocation-recovery/recovery-r1';d=json.loads(pin(root/'report.json','5ea56445e5367a421a28251f5e097b72f0d8370cf232a2fb4734b6698f14c2c6').read_bytes());assert d['passed']
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 crt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');pe=PEImage(crt.read_bytes());rows=[]
 for pc,data,meaning in[(0x780012e6,'6aff','Push scope index -1'),(0x780012e8,'6848e20278','Push scope table7802e248'),(0x780012ed,'6803ef0078','Push handler7800ef03'),(0x780012f2,'64a100000000','Read previous FS:[0] into EAX'),(0x780012f8,'50','Push saved EAX predecessor at EBP-10'),(0x780012f9,'64892500000000','Install exact current ESP to FS:[0]'),(0x78001367,'8b4df0','Read saved EBP-10 predecessor into ECX'),(0x7800136a,'64890d00000000','Restore saved ECX to FS:[0]')]:
  b=bytes.fromhex(data);off=pe.rva_range(pc-pe.image_base,len(b))[0];assert pe.data[off:off+len(b)]==b;rows.append(dict(pc=pc,hex=data,meaning=meaning))
 span=d['spans']['malloc-worker-hot'];raw=pin(root/'malloc-worker-hot.bin',span['sha256']).read_bytes();assert raw==pe.data[pe.rva_range(span['start']-pe.image_base,len(raw))[0]:pe.rva_range(span['start']-pe.image_base,len(raw))[0]+len(raw)]
 decode=pin(root/'malloc-worker-hot-decode.stdout').read_text()
 for r in rows:assert f'{r["pc"]:x}:'in decode
 irs=[]
 for leaf in ['worker-host.ll','worker_epilogue-host.ll']:
  p=pin(R/'reports/m4-crt-allocation/lifts-r1'/leaf);text=p.read_text();assert '__remill_read_memory_32'in text and '__remill_write_memory_32'in text;irs.append(dict(path=str(p),sha256=sha(p)))
 pin(R/'tools/m4-crt-allocation/lift.py');pin(R/'reports/m4-crt-allocation/lifts-r1/report.json');pin(R/'reports/m4-crt-allocation-recovery/recovery-r1/malloc24-source-ledger.json');pin(R/'tools/analysis/pe.py');pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Independent exact physical malloc source FS/SEH and authoritative cached lifted-span identity only; no model merge or execution',
  authoritative_recovery=str(root/'report.json'),normal_malloc_wrapper=0x780012b3,normal_worker_start=span['start'],normal_worker_end_exclusive=span['end_exclusive'],
  missing_constructor_descriptor_PCs=[0x780012f2,0x780012f9,0x78001367,0x7800136a],physical_source_rows=rows,
  authoritative_lift_component='tools/m4-crt-allocation/lift.py COMPONENTS worker→malloc-worker-hot; overlapping worker_epilogue→78001367/15bytes; actualRemill read/write32 callbacks',
  lifted_IRs=irs,FSrecord_words='at EBP-10 previous, EBP-0C handler7800ef03, EBP-08 scope7802e248, EBP-04 indexFFFFFFFF',
  distinction='Malloc worker literal source instructions were absent from constructor interpreter descriptors; source IR/bytes already exist and need additive descriptor/semantics admission, not treating old journal counters as literal interpreter execution.',
  archive_reader_opened=False,worker_executed=False,source_model_changed=False,initializer_credit=0,files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
