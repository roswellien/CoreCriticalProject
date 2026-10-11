"""Strict actual controls: authored caller boundary, causal source prefixes, retry conservation."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-controls'
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
  if o[6]!=4:continue
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
  need(len(frames)==7 and len(raw)==14 and not active and tib[1]==0xffffffff,'Seven genuine restored normal frames and private end sentinel')
  need(prov[:8]==(1,0x7ffde000,0x7ffde000,0xffffffff,0x20002000,0x20001000,0x7ffde000,0xffffffff)and not any(prov[8:]),'Explicit native BEFORE sentinel provenance distinct from original Windows chain')
  need([f[2]for f in frames]==[0x46ab30,0x48f250,0x4b4c10,0x4c3250,0x4cfe80,0x4d4830,0x4d4830],'Exact six-root seven-frame nested extent')
  for n,f in enumerate(frames):
   need(f[:2]==(1,n)and f[9]==f[5]-12 and f[15]==f[19]==f[21]==1 and f[17]==f[22]==f[8]and(f[20],f[5],f[6],4,0)in source,'Genuine source CALL frame, saved predecessor restore and original RET')
  need(frames[6][13]==6 and frames[6][8]==frames[5][9]and frames[6][12]==1,'Inner normal frame retains actual outer source record')
  graphs=rows(a,live+'fs-shared-graph-witnesses.bin','<16Q');need([g[7]for g in graphs]==[1,2,3,4,5],'Actual shared circular owner graph grows to five nodes')
  metrics['ordinary_sequences']+=1
 return frames,tib,active

def cause_checks(a,c,live,source,frames,tib,active,metrics,causes):
 if not c:return
 p=f'case-{c}/first-trigger/';f=a.words(p+'frame.bin',32,'Q');owned=a.words(p+'owner.bin',16,'Q');mf=a.words(p+'mfc.bin',32,'Q')
 fault=a.words(live+'locale-fault.bin',4);reason=a.data(live+'locale-fault-reason.bin').decode();tags=struct.unpack_from('<32Q',a.data(f'case-{c}/first.bin'))
 need(f[0]==1 and f[:8]==frames[f[1]][:8],'Actual targeted source-frame identity retained')
 observer='Deliberate precise normal-FS/shared-owner boundary observer failure';store='Checked actual source locale/parser store fault';private='FS observer changed private source-frame/chain witnesses'
 expected={1:(0x4e78d7,0x780039bf,80,'Heap creation observer changed State/FX or ownership/lifecycle ledgers'),2:(0x4e78d7,0xfffffffb,80,'Normal FS chain retains the owned game predecessor or native sentinel'),3:(0x4e78de,0x20001000,81,'Only committed source/API/research effects may change owned locale pages'),4:(0x4e799f,f[9],83,'Installed source FS predecessor/handler and active private frame identity'),5:(0x4e78de,tib[0],81,store),6:(0x4e799f,tib[0],83,store),7:(0x4e7977,owned[4],73,store),8:(0x4e797d,mf[16],73,store),9:(0x4e7994,owned[4],73,store),10:(0x4e796e,mf[16],87,'Checked complete current guest/native allocation backing and private generation required'),11:(0x4e799f,0,84,observer),20:(0x4d4948,tib[0],83,store),21:(0x4e7922,0x4e7922,86,private),22:(0x4e7922,0x4e7922,87,private),23:(0x4e78de,0x4e78de,81,private)}
 points={12:(0x4e78d7,80),13:(0x4e78de,81),14:(0x4e78de,82),15:(0x4e799f,83),16:(0x4e799f,84),17:(0x46ab78,85),18:(0x4e7922,86),19:(0x4e7922,87)}
 if c in points:pc,pt=points[c];expected[c]=(pc,0,pt,observer)
 need((fault[1],fault[2],fault[3],reason)==expected[c]and tags[12:14]==fault[1:3],'Exact reached PC/address/stage/refusal cause '+str(c))
 if c in(5,6,20):need(not any(s[0]==fault[1]and s[1]==tib[0]and s[4]for s in source),'Refused FS store did not commit')
 if c in(7,8,9):need(not any(s[0]==fault[1]and s[1]==fault[2]and s[4]for s in source),'Refused precise owned write did not commit')
 if c in(14,19):need(source[-1][0]==expected[c][0]and source[-1][4]==1,'Observer fault retains already committed actual store')
 if c==14:need(frames[0][15]==1 and tib[1]==f[9]and active==[(0,)],'Regression guard: actual TIBhead and private active marker agree after commit')
 if c in(7,8,9,10):
  need(mf[17]and mf[19]and len(a.data(p+'native-before.bin'))==mf[19],'Actual full-width native backing captured at targeted store')
  b=a.data(live+f'locale-allocation-{mf[18]}-expected.bin')[:mf[19]]
  need(a.data(p+'native-before.bin')==b,'Complete actual native extent equals independently reconstructed committed source prefix')
  if c==10:
   after=a.data(p+'native-after.bin');want=bytearray(b);want[-1]^=0x55
   need(after==want and len(after)==mf[19],'True last rounded backing-byte corruption, no narrowed/masked extent')
  metrics['full_native_prefix_controls']+=1
 if c in(11,20):
  outer=frames[5];inner=frames[6];raw=a.data(f'case-{c}/first-causal-stack.bin');off=outer[9]-0x20001000
  need(outer[3]==0x4d48f0 and inner[3]==0x4e78d0 and inner[13]==6 and inner[8]==outer[9]and tib[1]==outer[9]and active==[(5,)],'Actual nested chain restores inner predecessor to still-installed outer record')
  need(raw[off:off+8]==struct.pack('<II',outer[8],outer[10]),'Actual entire outer predecessor/handler bytes carried through inner sequence')
  need(inner[19]==1 and inner[21]==int(c==20)and outer[19]==outer[21]==0,'Exact inner and outer restoration/return prefix')
  install=next(r for r in rows(a,live+'fs-record-bytes.bin','<16Q')if r[2]==5 and r[4]==81)
  events=rows(a,live+'fs-chain-events.bin','<16Q')
  inner_before=next(e[13]for e in events if e[3]==6 and e[4]==80)
  inner_after=next(e[13]for e in events if e[3]==6 and e[4]==84)
  need(not any(s[4]and s[1]<outer[9]+12 and s[1]+s[3]>outer[9]for s in source[inner_before:inner_after]),'All12 outer record bytes unchanged during actual inner source interval')
  if c==11:need(raw[off:off+12]==struct.pack('<3I',*install[8:11]),'Actual complete outer12B record conserved through inner restore')
  else:
   scope=(0x4d491a,outer[9]+8,0,4,1)
   need(scope in source[inner_after:] and raw[off:off+12]==struct.pack('<III',outer[8],outer[10],0),'Only literal post-inner outer scope change4D491A is carried to refused outer restore')
  metrics['nested_prefix_controls']+=1
 if c in(18,19,21,22):
  guest=owned[10];writes=[s for s in source if s[1]==guest and s[0]==0x4e7922 and s[4]]
  need(len(writes)==int(c in(19,22)),'Before/after owner observer retains exact genuine byte-store prefix')
 causes.append(dict(case=c,pc=fault[1],address=fault[2],stage=fault[3],message=reason,completed_roots=tags[4],MFC_records=tags[11]))
 metrics['causal_faults']+=1

def main(execution,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh strict controls receipt');out.mkdir();pins={};levels=[];causes=[];passed=False
 metrics=dict(actual_attempts=0,ordinary_sequences=0,causal_faults=0,retry_refusals=0,rich_hardware_pairs=0,cleanup_hardware_pairs=0,full_retry_dump_records=0,physical_API_proofs=0,independent_postdestroy_identity_triplets=0,full_owned_page_source_replays=0,actual_postcommit_FS_events=0,authentic_full_record_observations=0,full_native_prefix_controls=0,nested_prefix_controls=0,normal_MFC_source_frees=0,normal_registry_source_frees=0)
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical closure '+str(p));pins[str(p)]=v;return p
 try:
  r=json.loads(pin(execution,digest).read_bytes());need(r['passed'],'Frozen final executable controls completed')
  for p,h in json.loads(pin(Path(execution).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  pin(__file__);pin(ROOT/'reports/m4-fs-native/preparation-r3/report.json','5ee2a50044e6e887c54d49b7a574806a21be032c7352fefacfbe431397abb35e')
  pin(ROOT/'reports/m4-fs-source/recovery-r3/report.json','17c7840c58bcdce2a82989d141f202cbb25540b6c29b4f314c06c0d1c2bf3a6b')
  pin(ROOT/'reports/m4-fs-source/recovery-r3/game-normal-graphs.json')
  archive=module('fs_control_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));physical=module('fs_physical_exports',pin(ROOT/'tools/m4-crt-locale-batch-review/check_v2.py'))
  physical.FORWARDS.update(HeapSize='RtlSizeHeap',HeapReAlloc='RtlReAllocateHeap',HeapFree='RtlFreeHeap')
  for level in r['levels']:
   verify_stage(Path(level['stage']).parent,level['stage_sha256']);a=archive.DirectSet(pin(level['capture'],level['capture_sha256']),pin)
   try:
    need(a.words('header.bin',6)==(1,24,48,9968,6,10),'Exact complete current control sample extent')
    for c in range(24):
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
       else:need(tags[3:7]==(1,6,0,1)and tags[10:12]==(7,10),'Genuine six-root ordinary source extent')
      metrics['actual_attempts']+=1
     live=f'case-{c}/first-live/';clean=f'case-{c}/first-cleaned/'
     source=rows(a,live+'locale-source-accesses.bin','<IIQII');live_allocs=rows(a,live+'locale-allocations.bin','<16Q');allocs=rows(a,clean+'locale-allocations.bin','<16Q');sections=rows(a,clean+'locale-critical-sections.bin','<16Q')
     need(len(live_allocs)==len(allocs)and all(o[8]==o[9]==0 and bool(o[10])!=bool(o[11])for o in allocs),'Every genuinely acquired owner unmapped and exactly source/host-safeguard freed')
     need(all(s[5]==0 and s[8]and s[9]and s[7]==1 for s in sections),'Every actual initialized CS deleted once')
     summary=a.words(clean+'locale-summary.bin',32);need(summary[23]==1 and summary[14]==summary[15]==summary[30]==0,'Actual finished binding no native resources')
     owned_replay(a,live,live_allocs,source,metrics)
     frames,tib,active=chain_checks(a,live,source,c==0,metrics);cause_checks(a,c,live,source,frames,tib,active,metrics,causes)
     if c==0:
      qs=rows(a,clean+'mfc-allocation-witnesses.bin','<32Q');need(len(qs)==10 and len(allocs)==11 and sum(o[6]==4 for o in allocs)==10 and all(o[10]and not o[11]for o in allocs),'Isolated10 MFC plusregistry genuine source frees')
      for q in qs:need(q[21]==q[23]==q[30]==1 and not q[31]and q[25]==0x5f401782 and q[27]==q[26]-8 and q[28:30]==(0x7800138a,0x78001390),'Genuine source825/CRTfree cdecl cleanup and exact owner generation')
      metrics['normal_MFC_source_frees']+=10;metrics['normal_registry_source_frees']+=1
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
    need(a.words('counts.bin',3)[1:]==(24,48)and a.data('COMPLETE.txt')==b'Bounded six-root normal-FS research controls passed; canonical109 is separate\n','Actual compiled fixture completed all24 cases and48 attempts')
    levels.append(dict(level=level['level'],logical_records=len(a.entries),capture=level['capture'],capture_sha256=level['capture_sha256'],elapsed_seconds=level['elapsed_seconds']));print(json.dumps(levels[-1]),flush=True)
   finally:a.close()
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,schema='mw34-normal-FS-authored-controls-v1',execution=str(execution),execution_sha256=digest,levels=levels,metrics=metrics,causes=causes,files=pins,physical_closure=verify_manifest(pins),native_executed=True,initializer_credit=False,API_response_injection=False,source_bodies_modified=False,exception_handler_execution=False,whole_TIB_page_claim=False,whole_M4_complete=False,hardware_scope='Exact finite authored caller NumericHostBoundary/ErrorBoundary through source invocation and its C++ catch, matching connected Context. Naked throwing Session API plus caller catch preservation is NOT claimed. Failed execution-r1 retained.',retry_scope='Same actually finished or failed Session; no additional virtual source/API/native-owner effects; entire raw dump logical inventories and payloads equal, full State/CPU/FX and explicit guest ENV captured.',cleanup_scope='Normal10 MFC plusregistry source frees; fault native ownership safeguards without fabricated virtual FS unwind. Actual HeapDestroy pre/post/independent identities measured.')
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
