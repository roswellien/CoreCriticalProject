"""Actual finite dispatch controls, complete owned bytes and exact refused retries."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-vtable-controls'
sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
from stages import verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def records(a,p,n):
 b=a.data(p);need(len(b)%(8*n)==0,'Whole fixed records '+p);return list(struct.iter_unpack('<'+str(n)+'Q',b))
def main(execution,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh control receipt');out.mkdir();pins={};counts=collections.Counter();levels=[];causes=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=pins.get(str(p))or sha(p);need(h is None or v==h,'Physical immutable input '+str(p));pins[str(p)]=v;return p
 try:
  ex=json.loads(pin(execution,digest).read_bytes());need(ex['passed'],'Actual completed finite control executions');build=json.loads(pin(ex['build'],ex['build_sha256']).read_bytes())
  for p,h in json.loads(pin(Path(ex['build']).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  pin(__file__);H=load('accepted_complete_control_helpers',pin(R/'tools/m4-container-controls/check_v2.py'));D=load('canonical_complete_control_reader',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));P=load('physical_native_export_proofs',pin(R/'tools/m4-crt-locale-batch-review/check_v2.py'))
  P.FORWARDS.update(HeapSize='RtlSizeHeap',HeapReAlloc='RtlReAllocateHeap',HeapFree='RtlFreeHeap')
  rootprep=json.loads(pin(build['preparation']).read_bytes());native=Path(rootprep['native_include']);np=json.loads(pin(native/'report.json','b52c62a1ec6e1306a9629f53fbe80621be96404907d322efbbeef136ec10ee93').read_bytes())
  current=sorted(set(map(int,np['source_pages']))|set(np['game_pages'])|{0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x20000000})
  need(len(current)==62 and 0x7ffde000 not in current and 0x5f4ce000 not in current,'Exact admitted whole-page inventory and minimal TIB policy')
  for l in ex['levels']:
   verify_stage(Path(l['stage']).parent,l['stage_sha256']);a=D.DirectSet(pin(l['capture'],l['capture_sha256']),pin)
   try:
    need(a.words('header.bin',6)==(1,27,54,9968,4,6),'Actual complete finite-control header')
    for c in range(27):
     s=f'case-{c}/';first=None
     for retry in(0,1):
      stem=s+('retry'if retry else'first');b=a.data(stem+'.bin');need(len(b)==9968,'Complete actual machine/host sample');tag=struct.unpack_from('<32Q',b);before=struct.unpack_from('<32Q',b,256);after=struct.unpack_from('<32Q',b,512)
      need(tag[:3]==(1,c,retry)and tag[6]==tag[16]==1 and tag[7]==0x4d573354 and not((tag[8]^tag[9])&0x400),'Actual successful cleanup/finite caller hardware/LastError/DF')
      need(after[4]==1 and not any(after[i]for i in(10,11,15)),'No live native allocation/section/heap after cleanup');H.hardware(b[8880:9424],b[9424:9968],True);counts['outside_hardware_pairs']+=1
      H.hardware(a.data(stem+'-cleanup-hardware-before.bin'),a.data(stem+'-cleanup-hardware-after.bin'));counts['cleanup_hardware_pairs']+=1
      need(all(len(a.data(stem+'-causal-'+n+'.bin'))==size for n,size in [('State',3504),('CPU',40),('FX',512),('guest-ENV',28),('stack',4096)]),'Whole current causal State/CPU/FX/ENV/stack')
      if retry:
       need(not tag[3]and not tag[4]and before==after and b[768:4272]==b[4272:7776]and b[7776:8288]==b[8288:8800]and b[8800:8840]==b[8840:8880],'Same finished/poisoned Session preserves whole3504State/CPU/FX and ownership')
       need(first[4272:7776]==b[768:4272]and first[8288:8800]==b[7776:8288]and first[8840:8880]==b[8800:8840],'Actual retry starts from prior cleaned complete machine')
       for dst in('retry-live/','retry-cleaned/'):counts['retry_raw_records']+=H.copied_suffixes(a,s+'first-cleaned/',s+dst)
       counts['retry_refusals']+=1
      else:
       first=b
       if c:need(not tag[3]and tag[5]==tag[14]==1,'Exactly one reached finite observer/source refusal')
       else:need(tag[3:7]==(1,4,0,1)and tag[10:12]==(1,0),'Genuine four-root/sixCALL/oneFS ordinary extent')
      counts['actual_attempts']+=1
     live=s+'first-live/';clean=s+'first-cleaned/';t=s+'first-trigger/';source=list(struct.iter_unpack('<IIQII',a.data(live+'locale-source-accesses.bin')))
     calls=records(a,live+'vtable-call-witnesses.bin',32);stores=records(a,live+'vtable-source-stores.bin',16);frames=records(a,live+'fs-frame-witnesses.bin',32);fault=a.words(live+'locale-fault.bin',4);identity=a.words(t+'identity.bin',3)
     def guest(address,size=4):
      page=address&~4095;need(address+size<=page+4096,'Bounded actual page read');return a.data(live+f'current-page-{page}.bin')[address-page:address-page+size]
     need(list(a.words(live+'current-page-addresses.bin',len(current)))==current,'Exact complete current-page inventory')
     for page in current:need(len(a.data(live+f'current-page-{page}.bin'))==4096,'Actual whole raw admitted page');counts['whole_current_pages']+=1
     need(guest(0x20001000,4096)==a.data(s+'first-causal-stack.bin'),'Current whole source stack is causal stack')
     allocs=records(a,live+'locale-allocations.bin',16);freed=records(a,clean+'locale-allocations.bin',16);sections=records(a,clean+'locale-critical-sections.bin',16)
     need(len(allocs)==len(freed)==1 and all(x[:8]==y[:8]and y[8:10]==(0,0)and y[10]+y[11]==1 for x,y in zip(allocs,freed)),'The sole registry owner retains provenance and is freed/unmapped once')
     need(all(q[5]==0 and q[8]and q[9]and q[7]==1 for q in sections),'Each actual initialized CS deleted exactly once')
     for owner in allocs:
      p=live+f'locale-allocation-{owner[5]}';initial=a.data(p+'-initial.bin');expected=a.data(p+'-expected.bin');actual=a.data(p+'-owned-page.bin');nativebytes=a.data(live+f'native-full-{owner[5]}.bin');need(len(initial)==len(nativebytes)==owner[3]and len(expected)==len(actual)==owner[4]and owner[2]<=owner[3]<=owner[4]and owner[7]==owner[8]and owner[8]and owner[9],'Actual complete initial/native/mapped owner extents')
      rebuilt=bytearray(initial+bytes(owner[4]-owner[3]))
      for pc,address,value,width,write in source:
       if write and owner[1]<=address<owner[1]+owner[4]:need(address+width<=owner[1]+owner[3],'Committed source store within actual rounded backing');rebuilt[address-owner[1]:address-owner[1]+width]=value.to_bytes(width,'little')
      need(bytes(rebuilt)==expected==actual and nativebytes==expected[:owner[3]],'Whole registry native/guest backing from actual acquired input plus literal writes');counts['complete_owner_source_replays']+=1
     cm=collections.Counter();H.chain_checks(a,live,source,False,cm);counts.update(cm);tib=a.words(live+'fs-current-tib.bin',5)
     for w in stores:
      need(w[:2]==(1,stores.index(w))and w[5]in(1,2,4)and w[8]>w[7]and source[w[8]-1]==(w[3],w[4],w[6]^(int(c==13 and w is stores[-1])),w[5],1),'Every private object store witness joins actual committed literal source store');counts['committed_object_stores']+=1
     for w in calls:
      need(w[0]==1 and w[4]in(0x5cfd14,0x5bc100,0x5bc0fc)and w[8]<len(source)and source[w[8]]==(w[3],w[4],w[5],4,0),'Actual finite owning-cell read retained without projection');counts['genuine_cell_reads']+=1
      if w[11]:
       need(source[w[12]]==(0x59fdb3,0x608ae0 if w[2]==0x4795f0 else 0x60b270,0x5bc0e0,4,1),'Both fixed and virtual retain source-dominating vptr publication')
       if w[3]==0x59ff6e:need(source[w[13]]==(0x59ff64,source[w[12]][1],0x5bc0e0,4,0),'True virtual cell retains actual source instance-vptr read')
       else:need(w[13]==0,'Fixed absolute call does not invent a future vptr read')
      if w[21]:need(w[18]==w[14]+4+w[17]and w[24]==w[25]and w[26]==w[27]and w[28]==w[29]and source[w[23]-1]==(w[20],w[14],w[15],4,0),'Literal completed RET preserves exact frame cleanup/FS/API/owner state');counts['complete_genuine_CALL_RET']+=1
     if not c:
      need(len(calls)==6 and all(w[21]for w in calls)and len(frames)==1 and not a.data(live+'fs-active-records.bin')and tib[1]==0xffffffff,'All six zero-domain helpers and one genuine frame returned')
      need([w[2]for w in calls]==[0x40f0e0,0x4795f0,0x4795f0,0x47f5f0,0x4b5220,0x4b5220]and not a.words(live+'vtable-active.bin',1)[0],'Actual reached rooted dispatch order')
      need(freed[0][10]==1 and not freed[0][11],'Ordinary registry owner genuinely source freed');counts['ordinary_sequences']+=1
     else:
      reason=a.data(live+'locale-fault-reason.bin').decode();cause_checks(a,c,live,t,source,calls,stores,frames,identity,fault,reason,guest,counts)
      need(freed[0][11]==1 and not freed[0][10],'Fault safeguard releases native owner without fabricated source free')
      causes.append(dict(level=l['level'],case=c,PC=fault[1],address=fault[2],stage=fault[3],reason=reason));counts['causal_refusals']+=1
     need(a.data(live+'fs-current-tib.bin')==a.data(clean+'fs-current-tib.bin')and a.data(live+'fs-active-records.bin')==a.data(clean+'fs-active-records.bin'),'Native safeguard does not fabricate virtual unwind')
     summary=a.words(clean+'locale-summary.bin',32);need(summary[23]==1 and summary[14]==summary[15]==summary[30]==0,'Finished owner has no native resources')
     heap=a.words(clean+'heap-create-witness.bin',16,'Q');life=a.words(clean+'heap-create-registry.bin',18,'Q');need(heap[6]and heap[6]!=0x48450001 and heap[11]==heap[6]and life[2:11]==(1,0x48450001,heap[6],1,1,0,1,1,1)and life[12:]==(1,0,0,1,heap[6],0),'One actual matching full-width HeapDestroy and exactly-once release')
     for service,requested in(('create','HeapCreate'),('query','GetVersionExA'),('destroy','HeapDestroy')):
      p=clean+'heap-'+service+'-api-';before=P.identity(a,p+'before',pin);after=P.identity(a,p+'after',pin);need(before==after,'Actual lifecycle target unchanged');rva,forward=P.export(Path(before[2]),requested);need(not forward and before[1]+rva==before[0],'Physical named native export')
      if service=='destroy':need(before==H.independent_identity(a,c,pin),'Independent immediate postfinish HeapDestroy identity matches both worker identities');counts['HeapDestroy_identity_triplets']+=1
     for index in range(summary[18]):
      p=clean+f'locale-api-{index}';w=a.words(p+'-witness.bin',32,'Q')
      if w[14]:
       before=P.identity(a,p+'-identity-before',pin);after=P.identity(a,p+'-identity-after',pin);proof=a.data(p+'-export-before.bin');need(before==after and proof==a.data(p+'-export-after.bin'),'Actual typed API/physical chain unchanged');P.export_proof(proof,before,proof[48:80].split(b'\0',1)[0].decode(),pin);counts['physical_typed_APIs']+=1
    need(a.words('counts.bin',3)[1:]==(27,54)and a.data('COMPLETE.txt')==b'Bounded four-root finite-vtable research controls passed; canonical120 is separate\n','All authored27 cases and54attempts completed')
    levels.append(dict(level=l['level'],logical_records=len(a.entries),capture=l['capture'],capture_sha256=l['capture_sha256']));print(json.dumps(levels[-1]),flush=True)
   finally:a.close();del a
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,execution=str(execution),execution_sha256=digest,build=ex['build'],build_sha256=ex['build_sha256'],counts=dict(counts),levels=levels,causes=causes,files=pins,physical_closure=verify_manifest(pins),initializer_credit=False,scope='Actual finite four-root local controls with authored NumericHostBoundary/ErrorBoundary through caller catch; exact whole State/CPU/FX/retry dumps, current pages and native registry backing. No naked throwing Session hardware guarantee, nonzero helper copy/handler/unwind path or API failure substitution.')
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=counts)))
def cause_checks(a,c,live,t,source,calls,stores,frames,identity,fault,reason,guest,counts):
 # Expected causes are frozen from physical source boundaries plus the actual authenticated facts,
 # never a fabricated API result or repaired runtime input.
 need(identity[0]in tuple(range(110,116))+(80,81,82,83)and identity[1]and fault[0]==1,'Actual trigger boundary and first-fault state')
 # Filled with exact independently checked source refusal classes after the first causal extraction.
 expected=CAUSES[c];need((fault[1],fault[2],fault[3],reason)==expected,'Exact reached first causal source PC/address/stage/reason '+str(c))
 if c in(5,6,7,8,25):need(not any(w and pc==fault[1]and address==fault[2]for pc,address,value,width,w in source),'Actual refused source write was never committed')
 if 11<=c<=16:
  before=a.data(t+'private-before.bin');after=a.data(t+'private-after.bin');name=a.data(t+'private-name.bin').decode();index={11:len(before)//8-32+6,12:4,13:len(before)//8-16+6,14:5,15:6,16:0}[c];width=4 if c==16 else 8;need(len(before)==len(after)and identity[2]==1,'Exactly one actual mutable private span intervention');wanted=bytearray(before);v=int.from_bytes(wanted[index*width:(index+1)*width],'little')^1;wanted[index*width:(index+1)*width]=v.to_bytes(width,'little');need(bytes(wanted)==after==a.data(live+name),'Actual complete private witness has exactly the intended one-word flip');counts['actual_private_word_flips']+=1
 if c in(1,2,3,4,9,10,26):
  q=a.words(t+'actual-intervention.bin',8,'Q');need(q[0]and q[2]!=q[3],'Actual committed intervention recorded')
  if c!=10:need(int.from_bytes(guest(q[1]),'little')==q[3]and q[6]==q[3],'Actual current source byte shows intervention')
  else:
   state=bytearray(a.data(t+'State.bin'));need(int.from_bytes(state[q[1]:q[1]+4],'little')==q[2],'Full real trigger State contains incomingEDX');state[q[1]:q[1]+4]=q[3].to_bytes(4,'little');need(bytes(state)==a.data(f'case-{c}/first-causal-State.bin'),'Actual generic full-State integrity refusal follows only intendedEDX change')
 if c==6:need(guest(0x5fc338)==struct.pack('<I',0x5cfd10)and guest(0x5fc33c)==bytes(4)and stores[-1][3:7]==(0x59fba5,0x5fc338,4,0x5cfd10),'Exactly committed4Bvptr prefix retained before next zero setter refusal');counts['partial_object_prefixes']+=1
 if c==7:need(guest(0x5fc338)==struct.pack('<I',0x5cfd10)and not any(q[3]==0x40f138 for q in stores),'Base vptr retains before derived header publication refusal');counts['partial_object_prefixes']+=1
 if c==8:need(frames[-1][15]and not frames[-1][19]and guest(0x608ea8)==struct.pack('<I',0x5cfd10),'Nested setter refusal retains genuine active12B chain and base header');counts['partial_object_prefixes']+=1
 if c in(11,12,13,14,15,16,17,18,19,20,21,22,23,24,26):need(a.data(t+'State.bin')==a.data(f'case-{c}/first-causal-State.bin'),'Observer/private/record fault retains exact trigger State')
CAUSES={1: (5897131, 6094100, 110, 'Exact physical finite indirect cell target and one active call'), 2: (5897669, 6013184, 110, 'Exact physical finite indirect cell target and one active call'), 3: (5898094, 6013180, 110, 'Exact physical finite indirect cell target and one active call'), 4: (5898084, 6327008, 110, 'Actual live instance vptr follows its exact committed source publication'), 5: (5897125, 6275896, 114, 'Checked actual source locale/parser store fault'), 6: (4253732, 6275900, 114, 'Checked actual source locale/parser store fault'), 7: (4256056, 6275896, 114, 'Checked actual source locale/parser store fault'), 8: (4253732, 6327980, 114, 'Checked actual source locale/parser store fault'), 9: (5898094, 536875008, 111, 'Only committed source/API/research effects may change owned locale pages'), 10: (5898094, 2013280703, 110, 'Heap creation observer changed State/FX or ownership/lifecycle ledgers'), 11: (5897131, 5897131, 111, 'Vtable observer changed private source-cell/frame/store witnesses'), 12: (5898084, 5898084, 111, 'Vtable observer changed private source-cell/frame/store witnesses'), 13: (5897125, 5897125, 115, 'Vtable observer changed private source-cell/frame/store witnesses'), 14: (5897131, 5897131, 110, 'Vtable observer changed private source-cell/frame/store witnesses'), 15: (5897125, 5897125, 114, 'Vtable observer changed private source-cell/frame/store witnesses'), 16: (4253728, 4253728, 112, 'Vtable observer changed private source-cell/frame/store witnesses'), 17: (5897131, 0, 110, 'Independent deliberate finite-vtable source boundary observer failure'), 18: (5897131, 0, 111, 'Independent deliberate finite-vtable source boundary observer failure'), 19: (4253728, 0, 112, 'Independent deliberate finite-vtable source boundary observer failure'), 20: (5897137, 0, 113, 'Independent deliberate finite-vtable source boundary observer failure'), 21: (5897125, 0, 114, 'Independent deliberate finite-vtable source boundary observer failure'), 22: (5897125, 0, 115, 'Independent deliberate finite-vtable source boundary observer failure'), 23: (4727975, 0, 80, 'Independent deliberate finite-vtable source boundary observer failure'), 24: (4727982, 0, 82, 'Independent deliberate finite-vtable source boundary observer failure'), 25: (4728045, 2147344384, 83, 'Checked actual source locale/parser store fault'), 26: (4727982, 536875008, 81, 'Only committed source/API/research effects may change owned locale pages')}
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
