"""Strict actual controls: authored caller boundary, causal source prefixes, retry conservation."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-container-controls'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
sys.path.insert(0,str(ROOT/'tools/m4-crt-locale-batch-review'))
from stages import verify_stage
from manifests import verify_manifest

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def rows(a,p,fmt):
 b=a.data(p);need(len(b)%struct.calcsize(fmt)==0,'Whole record extent '+p);return list(struct.iter_unpack(fmt,b))
def hardware(a,z,rich=False):
 need(len(a)==len(z)==544,'Full retained FX512 and ENV28 boundary')
 need(a[:5]==z[:5]and a[24:28]==z[24:28]and a[512:540]==z[512:540],'Exact CW/SW/FTW/MXCSR and complete legacy ENV28')
 for k in range(8):need(a[32+k*16:42+k*16]==z[32+k*16:42+k*16],'Exact each raw80 x87 register')
 need(a[256:416]==z[256:416],'Exact nonvolatile XMM6..15')
 if rich:need(struct.unpack_from('<H',a)[0]==0xa7f and struct.unpack_from('<I',a,24)[0]==0x5fa5 and a[4] and any(a[524:540]),'Genuinely loaded rich domain and nonzero legacy instruction metadata')

def copied_suffixes(a,src,dst):
 names=[n[len(src):]for n in a.entries if n.startswith(src)]
 other=[n[len(dst):]for n in a.entries if n.startswith(dst)]
 need(set(names)==set(other),'Exact full dump logical inventory on same Session retry')
 for name in names:need(a.data(src+name)==a.data(dst+name),'Same Session retry retains complete raw dump '+name)
 return len(names)

def independent_identity(a,c,pin):
 p=f'case-{c}/first-cleanup-api-';v=a.words(p+'after.bin',11,'Q')
 target,named,owner,owner_named,base,size,allocation,state,kind,protect,_=v
 need(target==named==owner_named and owner==allocation and base<=target<base+size and state==0x1000 and kind==0x1000000 and protect&0xf0 and not(protect&0x101),'Independent actual HeapDestroy executable owner identity')
 path=a.data(p+'path.bin').decode('utf-16-le').split('\0',1)[0];digest=a.data(p+'sha.bin').decode();pin(path,digest)
 return target,owner,path,digest

def owned_replay(a,live,allocs,source,metrics):
 for o in allocs:
  if o[6]not in(3,4):continue
  stem=live+f'locale-allocation-{o[5]}';initial=a.data(stem+'-initial.bin');expected=a.data(stem+'-expected.bin');actual=a.data(stem+'-owned-page.bin')
  need(len(initial)==o[3] and len(expected)==len(actual)==o[4] and o[2]<=o[3]<=o[4]and o[8]==o[7]and o[8]and o[9],'True requested/rounded/full guest/native owner geometry')
  want=bytearray(initial+bytes(o[4]-o[3]));writes=[]
  for pc,address,value,width,write in source:
   if write and o[1]<=address<o[1]+o[4]:
    need(address+width<=o[1]+o[2]and width in(1,2,4,8),'Literal write stays in exact requested object')
    want[address-o[1]:address-o[1]+width]=value.to_bytes(width,'little');writes.append((pc,address,value,width))
  need(bytes(want)==expected==actual,'Whole actual owned guest page reconstructed only from real initial extent and literal source writes')
  metrics['full_owned_page_source_replays']+=1
 return

def chain_checks(a,live,source,ordinary,metrics):
 frames=rows(a,live+'fs-frame-witnesses.bin','<32Q');events=rows(a,live+'fs-chain-events.bin','<16Q');raw=rows(a,live+'fs-record-bytes.bin','<16Q')
 tib=a.words(live+'fs-current-tib.bin',5);active=rows(a,live+'fs-active-records.bin','<I');prov=a.words(live+'fs-native-input.bin',16,'Q')
 need(tib[0]==tib[4]==0x7ffde000 and tib[2:4]==(0x20002000,0x20001000),'Actual minimal current TIB fields retain private identity')
 for e in events:
  if e[4]in(82,84):
   f=frames[e[3]];value=f[9]if e[4]==82 else f[8]
   need(e[13]>0 and source[e[13]-1]==(e[5],tib[0],value,4,1),'Post-store FS event follows actual memory/expected/source-ledger commit')
   metrics['actual_postcommit_FS_events']+=1
 for r in raw:
  f=frames[r[2]];need(r[0]==1 and r[6:8]==(f[9],12)and r[8]==f[8]and r[9]==f[10],'Authentic contiguous full12-byte source record identity')
  if r[4]==81:need(r[8:11]==(f[8],f[10],0xffffffff)and f[27:30]==r[8:11],'Actual installation previous/handler/scope bytes')
  else:need(r[4]==84 and f[30:32]==r[8:10]and f[26]==r[10],'Actual restoration fullrecord and legitimately changed scope')
  # Independently join each byte to the most recent genuine source write at capture.
  for k in range(12):
   address=r[6]+k;match=next((s for s in reversed(source[:r[11]])if s[4]and s[1]<=address<s[1]+s[3]),None)
   need(match is not None and ((match[2]>>(8*(address-match[1])))&255)==struct.pack('<3I',*r[8:11])[k],'Raw12-byte record came from committed literal stack writes')
  metrics['authentic_full_record_observations']+=1
 if ordinary:
  need(len(frames)==7 and len(raw)==14 and not active and tib[1]==0xffffffff,'Seven genuinely restored normal game records')
  need([f[2]for f in frames]==[0x47f5b0,0x47f6d0,0x48f210,0x4ada90,0x4b12d0,0x4d84a0,0x5a7dc0],'Seven exact selected root records')
  need(prov[:8]==(1,0x7ffde000,0x7ffde000,0xffffffff,0x20002000,0x20001000,0x7ffde000,0xffffffff)and not any(prov[8:]),'Explicit independent native sentinel provenance')
  for n,f in enumerate(frames):need(f[:2]==(1,n)and f[9]==f[5]-12 and f[15]==f[19]==f[21]==1 and f[17]==f[22]==f[8]and not f[13]and(f[20],f[5],f[6],4,0)in source,'Complete true frame/saved predecessor/RET')
  metrics['ordinary_sequences']+=1
 return frames,tib,active

def ordinary_container(a,live,source,metrics):
 nulls=rows(a,live+'container-nullfree-witnesses.bin','<32Q');borrowed=rows(a,live+'container-borrowed-witnesses.bin','<32Q');stores=rows(a,live+'container-vector-stores.bin','<16Q')
 need(len(nulls)==5 and len(borrowed)==3 and len(stores)==17,'Five true null frees/three borrowed copies/seventeen vector stores')
 need(a.words(live+'container-active.bin',2)==(0,0)and a.words(live+'container-null-active.bin',1)==a.words(live+'container-borrowed-active.bin',1)==(0,),'All actual private constructor/null-free indexes returned')
 for w in nulls:
  need(w[4]==0x5f401782 and w[7]==0 and w[8:10]==(0x80000339,0x5abd1a)and w[11]==w[16]==0x78001390 and w[12]==w[5]-8 and w[13]==0x5f40178c and w[17]==w[18]==1,'Complete literal825→CRTfree NULL frame and RET')
  need(w[19]==w[20]==w[21]==w[22]==w[29]==w[30]and w[19]!=0xffffffff,'Literal void free retains actual nonzero outer FS0 in EAX; no invented zero result')
  need(w[23]==w[24]and w[25]==w[26]and w[10]==w[31],'Null free has zero native API/owner/generation effects')
  seq=source[w[27]:w[28]];F=w[12];head=F-20
  for row in [(0x7800139f,0x7ffde000,w[19],4,0),(0x780013a5,head,w[19],4,1),(0x7800139a,F-16,0x7800ef03,4,1),(0x78001395,F-12,0x7802e260,4,1),(0x780013a6,0x7ffde000,head,4,1),(0x780013b3,F+4,0,4,0),(0x78001416,F-20,w[19],4,0),(0x78001419,0x7ffde000,w[19],4,1),(0x78001424,F,0x5f40178c,4,0)]:need(row in seq,'Authentic complete nested CRT FS/zero argument/return source prefix')
  need(not any(r[0]==0x78001435 for r in seq),'Normal zero branch never reaches native HeapFree CALL')
 for w in borrowed:
  need(w[3]==0x5f4020b4 and w[8:10]==(0x8000021c,0x5abdb0)and w[10]==w[5]-8 and w[11]==0x5f4020bc and w[12]==w[13]==0x5f4ccb54 and w[14:20]==(0x5f4020bc,0x5f4cecec,w[7],0x5f4020be,0x5f4cecec,1),'Exact borrowed DWORD accessor and committed source object copy')
  need(w[20]==0x5f4020c3 and w[21]==w[7]and w[22]==1 and w[25]==w[26]and w[27]==w[28]and w[29]==w[30],'Borrowed constructor genuine object RET/no owner/API/chain change')
 footprint=[s for s in source if s[1]<0x5f4cd000 and s[1]+s[3]>0x5f4cc000]
 need(footprint==[(0x5f4020bc,0x5f4ccb54,0x5f4cecec,4,0)]*3,'Entire observed provider data-page source footprint is exactly three scalar reads')
 for w in stores:
  need(w[15]>0 and source[w[15]-1]==(w[3],w[4],w[6],4,1)and w[6]==w[9]+(w[11]if w[7]==3 else 0),'Every precise endpoint is a genuine owned source store')
 need({w[3]for w in stores if w[7]in(4,5)}=={0x5a8800,0x5a8803},'Both additional source-derived empty vector pointer fields')

def cause_checks(a,c,live,source,frames,tib,active,metrics,causes):
 if not c:return
 p=f'case-{c}/first-trigger/';null=a.words(p+'nullfree.bin',32,'Q');borrowed=a.words(p+'borrowed.bin',32,'Q');string=a.words(p+'string.bin',32,'Q');vec=a.words(p+'vector.bin',16,'Q');mf=a.words(p+'mfc.bin',32,'Q');frame=a.words(p+'frame.bin',32,'Q');identity=a.words(p+'identity.bin',3)
 fault=a.words(live+'locale-fault.bin',4);reason=a.data(live+'locale-fault-reason.bin').decode();tags=struct.unpack_from('<32Q',a.data(f'case-{c}/first.bin'))
 store='Checked actual source locale/parser store fault';private='Container observer changed private import/borrowed/null-free/store witnesses';observer='Deliberate precise container/borrowed/null-free boundary observer failure';page='Only committed source/API/research effects may change owned locale pages'
 expected={1:(0x5abd1a,0x5bb4c8,75,'Exact container game owning ordinal source import relocation'),2:(0x5abdb0,0x5bb454,55,'Exact container game owning ordinal source import relocation'),3:(0x5f4020b4,0x5f4cc000,94,page),4:(0x5f4020be,borrowed[7],97,store),5:(0x5f401782,0x20001000,90,page),6:(0x78001390,0,91,observer),7:(0x5f40178c,0,92,observer),8:(0x780013a6,0x7ffde000,91,store),9:(0x4ad8eb,0x60b11c,100,store),10:(0x4ad90c,0x60b114,73,store),11:(0x4ad91a,0x60b118,100,store),12:(0x78002fde,string[10]+4,53,store),13:(0x4ad8eb,mf[16],101,'Checked complete current guest/native allocation backing and private generation required'),14:(0x482b4e,0x7ffde000,81,store),15:(0x4ad91f,0x7ffde000,83,store)}
 for k,pc,point in [(16,0x5f4020be,97),(17,0x78001390,91),(18,0x5f4020b4,94),(19,0x4ad8eb,100),(20,0x4ad8eb,101),(21,0x5f401782,90)]:expected[k]=(pc,pc,point,private)
 points={90:0x5f401782,91:0x78001390,92:0x5f40178c,93:0x4ad8dd,94:0x5f4020b4,95:0x5f4020bc,96:0x5f4020bc,97:0x5f4020be,98:0x5f4020be,99:0x482b7b,100:0x4ad8eb,101:0x4ad8eb}
 if c>=22:point=90+c-22;expected[c]=(points[point],0,point,observer)
 need((fault[1],fault[2],fault[3],reason)==expected[c]and tags[12:14]==fault[1:3],'Exact actual reached cause/stage/source PC/address '+str(c))
 need(50<=identity[0]<=101 and identity[1]!=0,'Actual observed trigger boundary/source PC identity')
 if c in(4,8,9,10,11,12,14,15):need(not any(s[0]==fault[1]and s[1]==fault[2]and s[4]for s in source),'First refused source store never committed')
 if c in(9,10,11,13,32,33):
  need(mf[17]and len(a.data(p+'native-before.bin'))==mf[19]and not any(s[4]and mf[16]<=s[1]<mf[16]+mf[7]for s in source),'Actual full vector backing retained with no fabricated initialization/relocation')
  need(a.data(p+'native-before.bin')==a.data(live+f'locale-allocation-{mf[18]}-initial.bin'),'Full native vector backing remains genuine acquired initial bytes')
  if c==13:
   want=bytearray(a.data(p+'native-before.bin'));want[-1]^=0x55;need(a.data(p+'native-after.bin')==want==a.data(live+f'native-full-{mf[18]}.bin'),'True entire rounded native backing and exact last-byte corruption')
  metrics['full_native_prefix_controls']+=1
 if c==12:
  need(string[16]==4 and len(a.data(p+'native-before.bin'))==string[13],'Actual genuine four-byte string copy prefix')
  initial=a.data(live+f'locale-allocation-{string[12]}-initial.bin');want=bytearray(initial);want[:4]=a.data(live+'string-0-input.bin')[:4]
  need(a.data(p+'native-before.bin')==bytes(want)==a.data(live+f'native-full-{string[12]}.bin'),'Exactly four real copied bytes and all untouched initial trailing native backing')
  metrics['full_native_prefix_controls']+=1
 if c in(6,7,8,17,21,22,23,24,25):need(null[19]==frame[9]and frame[15]and not frame[19]and tib[1]==frame[9],'Actual null-free source boundary retains genuine active game outer record')
 if c==7 or c==24:need(null[17]and not null[18]and null[21]==frame[9]and null[23]==a.words(live+'registry-summary.bin',32,'Q')[12],'Actual literal CRT null RET precedes MFC RET and has no API effect')
 if c in(16,17,18,19,20,21):
  need(identity[2]==1,'Exactly one actual private span/scalar mutation')
  if c==16:need(rows(a,live+'container-borrowed-witnesses.bin','<32Q')[-1][18]==borrowed[18]^1,'Genuine private borrowed witness word flipped')
  if c==17:need(rows(a,live+'container-nullfree-witnesses.bin','<32Q')[-1][7]==null[7]^1,'Genuine private zero-argument witness flipped')
  if c==18:need(rows(a,live+'container-import-ledger.bin','<8Q')[-1][6]==0x5f4020b4^1,'Genuine last import relocation witness flipped')
  if c==19:need(a.words(live+'container-vector-probe.bin',16,'Q')[6]==vec[6]^1,'Genuine private source endpoint probe flipped')
  if c==20:need(rows(a,live+'container-vector-stores.bin','<16Q')[-1][6]==vec[6]^1 and source[-1]==(vec[3],vec[4],vec[6],4,1),'Only private committed ledger changes; actual source store stays genuine')
  if c==21:need(a.words(live+'container-null-active.bin',1)==(1^1,),'Genuine private active scalar changed')
 causes.append(dict(case=c,pc=fault[1],address=fault[2],stage=fault[3],message=reason,trigger_point=identity[0],trigger_PC=identity[1],completed_roots=tags[4]));metrics['causal_faults']+=1

def main(execution,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh strict controls receipt');out.mkdir();pins={};levels=[];causes=[];passed=False
 metrics=dict(actual_attempts=0,ordinary_sequences=0,causal_faults=0,retry_refusals=0,rich_hardware_pairs=0,cleanup_hardware_pairs=0,full_retry_dump_records=0,physical_API_proofs=0,independent_postdestroy_identity_triplets=0,full_owned_page_source_replays=0,actual_postcommit_FS_events=0,authentic_full_record_observations=0,full_native_prefix_controls=0,nested_prefix_controls=0,normal_MFC_source_frees=0,normal_registry_source_frees=0)
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical closure '+str(p));pins[str(p)]=v;return p
 try:
  r=json.loads(pin(execution,digest).read_bytes());need(r['passed'],'Frozen final executable controls completed')
  for p,h in json.loads(pin(Path(execution).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  pin(__file__);pin(ROOT/'tools/m4-container-controls/causes.inc.py');pin(ROOT/'reports/m4-container-native/preparation-r2/report.json','4d1eb214d383b99a857e927e90768e3de4f87429f1c4def90c49067340e02164')
  pin(ROOT/'reports/m4-container-source/recovery-r3/report.json','b078cff8698dfbefa8d4e45a0368d4820e72c7d659520161e4316e77d3c2f26b')
  pin(ROOT/'reports/m4-container-source/recovery-r3/game-normal-graphs.json')
  archive=module('fs_control_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));physical=module('fs_physical_exports',pin(ROOT/'tools/m4-crt-locale-batch-review/check_v2.py'))
  physical.FORWARDS.update(HeapSize='RtlSizeHeap',HeapReAlloc='RtlReAllocateHeap',HeapFree='RtlFreeHeap')
  for level in r['levels']:
   verify_stage(Path(level['stage']).parent,level['stage_sha256']);a=archive.DirectSet(pin(level['capture'],level['capture_sha256']),pin)
   try:
    need(a.words('header.bin',6)==(1,34,68,9968,7,8),'Exact complete current control sample extent')
    for c in range(34):
     first=None
     for retry in(0,1):
      attempt='retry'if retry else'first';p=f'case-{c}/{attempt}';b=a.data(p+'.bin');need(len(b)==9968,'Actual complete sample')
      tags=struct.unpack_from('<32Q',b);before=struct.unpack_from('<32Q',b,256);after=struct.unpack_from('<32Q',b,512)
      need(tags[:3]==(1,c,retry)and tags[6]==tags[16]==1 and tags[7]==0x4d573354 and not((tags[8]^tags[9])&0x400),'Actual boundary/LastError/DF and cleanup witness')
      need(after[4]==1 and not any(after[k]for k in(10,11,15)),'No live native heap/allocation/CS owners after cleanup')
      hardware(b[8880:9424],b[9424:9968],True);metrics['rich_hardware_pairs']+=1
      hardware(a.data(p+'-cleanup-hardware-before.bin'),a.data(p+'-cleanup-hardware-after.bin'));metrics['cleanup_hardware_pairs']+=1
      need(len(a.data(p+'-causal-State.bin'))==3504 and len(a.data(p+'-causal-CPU.bin'))==40 and len(a.data(p+'-causal-FX.bin'))==512 and len(a.data(p+'-causal-guest-ENV.bin'))==28 and len(a.data(p+'-causal-stack.bin'))==4096,'Actual complete causal machine, explicit guest ENV and whole source stack')
      if retry:
       need(tags[3]==tags[4]==0 and before==after and b[768:4272]==b[4272:7776]and b[7776:8288]==b[8288:8800]and b[8800:8840]==b[8840:8880],'Refused same Session preserves full State/CPU/FX and every owner/lifecycle counter')
       need(first[4272:7776]==b[768:4272]and first[8288:8800]==b[7776:8288]and first[8840:8880]==b[8800:8840],'Retry entered the exact actually cleaned prior machine')
       need(a.data(p+'-causal-State.bin')==b[768:4272]and a.data(p+'-causal-FX.bin')==b[7776:8288]and a.data(p+'-causal-CPU.bin')==b[8800:8840],'Retry causal machine is genuine unchanged pre-attempt machine')
       for dest in('retry-live/','retry-cleaned/'):
        metrics['full_retry_dump_records']+=copied_suffixes(a,f'case-{c}/first-cleaned/',f'case-{c}/'+dest)
       metrics['retry_refusals']+=1
      else:
       first=b
       if c:need(tags[3]==0 and tags[5]==1 and tags[14]==1,'Exactly one targeted reached observer or source refusal')
       else:need(tags[3:7]==(1,7,0,1)and tags[10:12]==(7,5)and tags[17]==1,'Genuine seven-root ordinary source extent and independently unmapped borrowed pointee')
      metrics['actual_attempts']+=1
     live=f'case-{c}/first-live/';clean=f'case-{c}/first-cleaned/'
     source=rows(a,live+'locale-source-accesses.bin','<IIQII');live_allocs=rows(a,live+'locale-allocations.bin','<16Q');allocs=rows(a,clean+'locale-allocations.bin','<16Q');sections=rows(a,clean+'locale-critical-sections.bin','<16Q')
     need(len(live_allocs)==len(allocs)and all(o[8]==o[9]==0 and bool(o[10])!=bool(o[11])for o in allocs),'Every genuinely acquired owner unmapped and exactly source/host-safeguard freed')
     need(all(s[5]==0 and s[8]and s[9]and s[7]==1 for s in sections),'Every actual initialized CS deleted once')
     summary=a.words(clean+'locale-summary.bin',32);need(summary[23]==1 and summary[14]==summary[15]==summary[30]==0,'Actual finished binding no native resources')
     owned_replay(a,live,live_allocs,source,metrics)
     for o in live_allocs:
      need(o[8] and o[9],'Live first-refusal owner has genuine full native and guest storage')
      actual=a.data(live+f'native-full-{o[5]}.bin');expected=a.data(live+f'locale-allocation-{o[5]}-expected.bin')[:o[3]]
      need(len(actual)==o[3],'Complete actual live native backing extent')
      if c==13 and actual!=expected:
       need(o[6]==4 and actual[:-1]==expected[:-1]and actual[-1]==expected[-1]^0x55,'Only actual final vector native byte deliberately differs')
      else:need(actual==expected,'Full live native extent equals committed expected backing')

     frames,tib,active=chain_checks(a,live,source,c==0,metrics);cause_checks(a,c,live,source,frames,tib,active,metrics,causes)
     if c==0:
      qs=rows(a,clean+'mfc-allocation-witnesses.bin','<32Q');ss=rows(a,clean+'strings-witnesses.bin','<32Q')
      need(len(qs)==5 and len(ss)==3 and len(allocs)==9 and sum(o[6]==4 for o in allocs)==5 and sum(o[6]==3 for o in allocs)==3 and all(o[10]and not o[11]for o in allocs),'Five MFC/three strings/registry genuinely source freed')
      for q in qs:need(q[21]==q[23]==q[30]==1 and not q[31]and q[25]==0x5f401782 and q[27]==q[26]-8 and q[28:30]==(0x7800138a,0x78001390),'Genuine cdecl MFC825 cleanup of every whole owner')
      ordinary_container(a,live,source,metrics)
      metrics['normal_MFC_source_frees']+=5;metrics['normal_registry_source_frees']+=1
     else:need(all(o[11]and not o[10]for o in allocs),'Fault path retains genuine virtual source prefix; only native safeguards free owners')
     need(a.data(live+'fs-current-tib.bin')==a.data(clean+'fs-current-tib.bin')and a.data(live+'fs-active-records.bin')==a.data(clean+'fs-active-records.bin'),'Fault source chain never fabricated-unwound by host cleanup')
     heap=a.words(clean+'heap-create-witness.bin',16,'Q');lifecycle=a.words(clean+'heap-create-registry.bin',18,'Q')
     need(heap[:6]==(1,0,1,0,4096,0)and heap[6]and heap[6]!=0x48450001 and heap[7]==0x48450001 and heap[11]==heap[6],'Genuine actual full-width uninjected native heap')
     need(lifecycle[0]==1 and lifecycle[1]and lifecycle[2:11]==(1,0x48450001,heap[6],1,1,0,1,1,1)and lifecycle[12:]==(1,0,0,1,heap[6],0),'Exactly one genuine matching HeapDestroy')
     for service,requested in(('create','HeapCreate'),('query','GetVersionExA'),('destroy','HeapDestroy')):
      stem=clean+'heap-'+service+'-api-';ib=physical.identity(a,stem+'before',pin);iz=physical.identity(a,stem+'after',pin)
      need(ib==iz,'Actual pre/post native lifecycle target identity')
      rva,forward=physical.export(Path(ib[2]),requested);need(not forward and ib[1]+rva==ib[0],'Actual physical named native export')
      if service=='destroy':need(ib==independent_identity(a,c,pin),'Genuine pre/post/independent postdestroy identities equal');metrics['independent_postdestroy_identity_triplets']+=1
      metrics['physical_API_proofs']+=1
     for n in range(summary[18]):
      stem=clean+f'locale-api-{n}';q=a.words(stem+'-witness.bin',32,'Q')
      if not q[14]:continue
      before=physical.identity(a,stem+'-identity-before',pin);after=physical.identity(a,stem+'-identity-after',pin);proof=a.data(stem+'-export-before.bin')
      need(before==after and proof==a.data(stem+'-export-after.bin'),'Genuine actual typed API identity and full physical forwarding chain unchanged')
      requested=proof[48:80].split(b'\0',1)[0].decode();physical.export_proof(proof,before,requested,pin);metrics['physical_API_proofs']+=1
    need(a.words('counts.bin',3)[1:]==(34,68)and a.data('COMPLETE.txt')==b'Bounded seven-root container/borrowed/null-free research controls passed; canonical116 is separate\n','Actual compiled fixture completed all34 cases and68 attempts')
    levels.append(dict(level=level['level'],logical_records=len(a.entries),capture=level['capture'],capture_sha256=level['capture_sha256'],elapsed_seconds=level['elapsed_seconds']));print(json.dumps(levels[-1]),flush=True)
   finally:a.close()
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,schema='mw34-container-authored-controls-v1',execution=str(execution),execution_sha256=digest,levels=levels,metrics=metrics,causes=causes,files=pins,physical_closure=verify_manifest(pins),native_executed=True,initializer_credit=False,API_response_injection=False,source_bodies_modified=False,exception_handler_execution=False,whole_TIB_page_claim=False,whole_M4_complete=False,hardware_scope='Exact finite authored caller NumericHostBoundary/ErrorBoundary through source invocation and its C++ catch, matching connected Context. Naked throwing Session API plus caller catch preservation is NOT claimed. No naked throwing API preservation claim.',retry_scope='Same actually finished or failed Session; no additional virtual source/API/native-owner effects; entire raw dump logical inventories and payloads equal, full State/CPU/FX and explicit guest ENV captured.',cleanup_scope='Normal5 MFC,3strings plusregistry source frees; fault native ownership safeguards without fabricated virtual FS unwind. Actual HeapDestroy pre/post/independent identities measured.')
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
