"""Finite current141 lock25 CRT cell (0x8C) binding probe (v2).

v2 adds the index-25 API lifetime that v1 left open: in each original phase15
MFC named-API ledger exactly one EnterCriticalSection entry (EIP = resolved real
export, EAX 25, stack [78001075, target]) followed by its return, and one
LeaveCriticalSection entry (EAX 25, stack [780012B1, target]) followed by its
return; in each native MFC APIs ledger exactly one Enter (site 7800106F, return
78001075, EAX 25, frame arg = native target, depth 1) and one Leave (site
780012AB, return 780012B1, EAX 25, arg, depth 0).

Original141: the MFC phase15 BEFORE/AFTER CRT-codepage-lock record must name
slot 7803708C (the lock25 cell) with target == cell value, size 24, initialized,
and hold the idle balanced CS24; the cell value must be constant at all 1,692
original endpoints. Native141 source6 O0/O2: the MFC BEFORE/AFTER memory index
must contain exactly (cell value, 24) whose 24 guest bytes equal guestCS24 and
the same idle CS24; the native cell must be constant at all endpoints.
v1 text retained for the identity half. No policy admission or credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
SLOT=0x7803708c;IDLE=struct.pack('<6I',0xffffffff,0xffffffff,0,0,0,0x020007d0)
ORIGINAL_VALIDATION=('reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c')
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 pin(__file__);hp=pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');sp=importlib.util.spec_from_file_location('ordinary_entries',hp);D=importlib.util.module_from_spec(sp);sp.loader.exec_module(D)
 V=json.loads(pin(R/ORIGINAL_VALIDATION[0],ORIGINAL_VALIDATION[1]).read_bytes());N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert V['passed']and V['reader_closed']and N['passed']is True and N['reader_closed']is True
 def opened(row,pattern):
  i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256']);es=D.entries(i,re.compile(pattern));f=p.open('rb')
  def rd(k):
   z=es[k];f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
  return i,p,f,es,rd
 IC=json.loads(pin(R/'reports/m4-startup141-paired/import-cells141-r1/report.json').read_bytes());assert IC['passed']is True and IC['violations']==0
 real={c['name']:c['original_real_target']for c in json.loads(pin(IC['output']['path'],IC['output']['sha256']).read_bytes())['cells']};ENTER=real['EnterCriticalSection'];LEAVE=real['LeaveCriticalSection']
 relations=[]
 oi,op,of,oes,ord_=opened(next(e for e in V['paired_exports']if e['branch']=='original'),r'phase/[0-5]/(?:\d+/CRT-(?:before|after)/2013491200|15/MFC1168/(?:BEFORE|AFTER)/CRT-codepage-lock/(?:bytes|meta)|15/MFC1168/named-API/(?:count|records))\.bin')
 original={}
 try:
  for s in range(6):
   cell={struct.unpack_from('<I',ord_(f'phase/{s}/{ph}/CRT-{side}/2013491200.bin'),0x8c)[0]for ph in range(141)for side in('before','after')};assert len(cell)==1,'Original lock25 cell constant at every endpoint';target=cell.pop()
   for side in('BEFORE','AFTER'):
    meta=struct.unpack('<4I',ord_(f'phase/{s}/15/MFC1168/{side}/CRT-codepage-lock/meta.bin'));cs=ord_(f'phase/{s}/15/MFC1168/{side}/CRT-codepage-lock/bytes.bin')
    assert meta==(SLOT,target,24,1)and cs==IDLE,'MFC phase15 codepage lock names the lock25 cell, its target and idle CS24'
   count=struct.unpack('<I',ord_(f'phase/{s}/15/MFC1168/named-API/count.bin'))[0];rec=ord_(f'phase/{s}/15/MFC1168/named-API/records.bin');assert len(rec)==count*668
   rows=[(struct.unpack_from('<I',rec,k*668)[0],struct.unpack_from('<I',rec,k*668+36)[0],struct.unpack_from('<2I',rec,k*668+580))for k in range(count)]
   life=[]
   for api,ret in((ENTER,0x78001075),(LEAVE,0x780012b1)):
    hits=[k for k,(eax,eip,st)in enumerate(rows)if eip==api]
    assert len(hits)==1,'Exactly one original index-25 '+hex(api);k=hits[0];eax,eip,st=rows[k]
    assert eax==25 and st==(ret,target)and k+1<count and rows[k+1][1]==ret,'Original lock25 API entry EAX25/arg target and its return';life.append(k)
   assert life[0]<life[1],'Enter precedes Leave'
   original[s]=target
 finally:of.close()
 for lv in('O0','O2'):
  ni,np_,nf,nes,nrd=opened(next(e for e in N['paired_exports']if e['branch']==lv),r'sequence-[0-5]/(?:phase-\d+-(?:before|after)-page-2013491200|MFC/(?:before|after)/(?:memory/(?:index|\d+)|guestCS24)|MFC/after/APIs)\.bin')
  try:
   for s in range(6):
    cell={struct.unpack_from('<I',nrd(f'sequence-{s}/phase-{ph}-{side}-page-2013491200.bin'),0x8c)[0]for ph in range(141)for side in('before','after')};assert len(cell)==1,'Native lock25 cell constant at every endpoint';target=cell.pop()
    for side in('before','after'):
     idx=[struct.unpack_from('<3I',nrd(f'sequence-{s}/MFC/{side}/memory/index.bin'),i)for i in range(0,len(nrd(f'sequence-{s}/MFC/{side}/memory/index.bin')),12)]
     assert sum(1 for a,n,_ in idx if a==target)==1 and next(n for a,n,_ in idx if a==target)==24,'Native MFC memory owns exactly the 24-byte region at the lock25 target'
     region=nrd(f'sequence-{s}/MFC/{side}/memory/{target}.bin');guest=nrd(f'sequence-{s}/MFC/{side}/guestCS24.bin')
     assert region==guest==IDLE,'Native guest CS24 at the lock25 target is the idle balanced descriptor'
    apis=nrd(f'sequence-{s}/MFC/after/APIs.bin');assert len(apis)%352==0;recs=[(struct.unpack_from('<16Q',apis,i),struct.unpack_from('<I',apis,i+128)[0],struct.unpack_from('<2I',apis,i+208))for i in range(0,len(apis),352)]
    for site,ret,depth in((0x7800106f,0x78001075,1),(0x780012ab,0x780012b1,0)):
     hits=[r for r in recs if r[0][2]==site];assert len(hits)==1,'Exactly one native index-25 call at '+hex(site);w,eax,fr=hits[0]
     assert w[6]==ret and eax==25 and fr==(ret,target)and w[13]==depth and w[4]==1,'Native lock25 API index25/arg target/depth'
    relations.append(dict(level=lv,sequence=s,index25_API_lifetime=True,original_target=original[s],native_target=target,original_slot=SLOT,whole_CS24_hex=IDLE.hex(),original_constant_endpoints=282,native_constant_endpoints=282))
  finally:nf.close()
  assert sha(ni)==pins[str(ni)]and sha(np_)==pins[str(np_)]
 assert sha(oi)==pins[str(oi)]and sha(op)==pins[str(op)]
 rp=out/'lock25-relations.json';rp.write_text(json.dumps(relations,indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=True,scope='Current141 lock25 cell object identity: original MFC phase15 codepage-lock slot/target/CS24 and native MFC guest region/CS24, both cells constant at every endpoint; plus paired index-25 Enter/Leave API lifetime on both branches; no policy admission or credit',
  relations=len(relations),original_targets=sorted({r['original_target']for r in relations}),native_targets=sorted({r['native_target']for r in relations}),index25_API_lifetime_rederived=True,
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','relations','original_targets','native_targets')}))
if __name__=='__main__':main(sys.argv[1])
