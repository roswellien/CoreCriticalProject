"""Consume only fresh isolated controls, one level at a time after coordination."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def hardware(a,b,rich=False):
 need(len(a)==len(b)==544,'Retained raw hardware512+ENV28+padding')
 need(a[:5]==b[:5]and a[24:28]==b[24:28]and a[512:540]==b[512:540],'Exact architectural x87 CW/SW/FTW/MXCSR/legacy ENV')
 for k in range(8):need(a[32+k*16:42+k*16]==b[32+k*16:42+k*16],'Exact each80-bit x87 register')
 need(a[256:416]==b[256:416],'Exact nonvolatile XMM6..15')
 if rich:need(struct.unpack_from('<H',a)[0]==0xa7f and struct.unpack_from('<I',a,24)[0]==0x5fa5 and a[4]and any(a[524:540]),'Actual rich FP seed and instruction metadata')
def main(execution,digest,name,levels=('O0','O2')):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh controls validator');out.mkdir(parents=True);pins={};counts=Counter();causes=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();a=pins.get(str(p))or sha(p);need(h is None or a==h,'Exact physically sealed current input '+str(p));pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def records(a,p,fmt):
  b=a.data(p);need(len(b)%struct.calcsize(fmt)==0,'Whole actual record '+p);return list(struct.iter_unpack(fmt,b))
 try:
  e=read(execution,digest);need(e['passed'],'Fresh current controls workers passed bothlevels')
  b=read(e['build_path'],e['build_sha256']);need(b['passed'],'Fresh actual compiled controls')
  p=read(b['preparation'],b['preparation_sha256']);need(p['control_scenarios']==18 and p['control_attempts']==36 and p['actual_Runtime_selected_call'],'Literal selected tree Context control contract')
  need(p['native_preparation_sha256']==e['native_preparation_sha256']=='9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2','Exact current native5 throughout causal evidence')
  read(p['native_preparation'],p['native_preparation_sha256'])
  for q,h in b['sources'].items():pin(q,h)
  pin(__file__);pin(R/'tools/m4-tree-review/check_controls.py')
  direct=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('tree_controls_reader',direct);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
  for f in ('capture_bundle.py','paths.py','stages.py','manifests.py'):pin(R/'tools/m4-pipeline'/f)
  for level in levels:
   w=e['workers'][level];need(w['exit_code']==0,'Actual worker status '+level);pin(b['workers'][level]['path'],b['workers'][level]['sha256'])
   a=D.DirectSet(pin(w['transport'],w['transport_sha256']),pin)
   try:
    need(a.words('header.bin',9)==(1,18,36,9968,0x4b7f70,3504,40,512,65),'Immutable full caller/machine ABI')
    need(a.data('COMPLETE.txt').startswith(b'Bounded actual Runtime tree controls passed'),'Whole controls completion record')
    for case in range(18):
     first=None
     for retry in (0,1):
      root=f'case-{case}/'+('retry/'if retry else'first/');sample=a.data(root+'sample.bin');need(len(sample)==9968,'Full actual sample')
      tags=struct.unpack_from('<32Q',sample);before=struct.unpack_from('<32Q',sample,256);after=struct.unpack_from('<32Q',sample,512)
      need(tags[:3]==(1,case,retry)and tags[5]==tags[9]==1 and tags[6]==0x4d573354 and not((tags[7]^tags[8])&0x400),'Exact actual scenario/cleanup/caller LastError/DF')
      need(not any(after[i]for i in(10,11,15)),'No live native allocations/critical sections/heap')
      hardware(sample[8880:9424],sample[9424:9968],True);hardware(a.data(root+'actual-cleanup-hardware-before.bin'),a.data(root+'actual-cleanup-hardware-after.bin'));counts['rich_caller_hardware_pairs']+=1;counts['actual_cleanup_hardware_pairs']+=1
      for n,z in(('State',3504),('CPU',40),('FX',512),('guest-ENV',28)):need(len(a.data(root+'actual-causal-'+n+'.bin'))==z,'Complete precise causal machine '+n)
      live=root+'actual-live/';clean=root+'actual-cleaned/'
      if retry:
       need(not tags[3]and not tags[4]and before==after,'Same cleaned Session refuses without lifecycle progress')
       need(sample[768:4272]==sample[4272:7776]and sample[7776:8288]==sample[8288:8800]and sample[8800:8840]==sample[8840:8880],'Refused same-Session fullState3504/FX512/CPU40 unchanged')
       need(first[4272:7776]==sample[768:4272]and first[8288:8800]==sample[7776:8288]and first[8840:8880]==sample[8800:8840],'Retry inherits exact cleaned machine, no reseed')
       old=f'case-{case}/first/actual-cleaned/'
       for suffix in ('locale-source-accesses.bin','locale-api-transports.bin','locale-call-frames.bin','locale-summary.bin','fs-chain-events.bin','fs-active-records.bin','fs-owned-accesses.bin','fs-owned-publications.bin','tree-lockit-contexts.bin','tree-lockit-held.bin','tree-status.bin','lockit-calls.bin','lockit-imports.bin','lockit-source-CS.bin','lockit-native-images.bin','locale-allocations.bin','locale-critical-sections.bin','registry-exception-message.bin','current-page-addresses.bin'):
        need(a.data(old+suffix)==a.data(live+suffix)==a.data(clean+suffix),'Same-Session retry preserves complete current history '+suffix);counts['whole_retry_history_joins']+=2
       pages=a.words(old+'current-page-addresses.bin',65)
       for page in pages:
        suffix='current-page-'+str(page)+'.bin';need(len(a.data(old+suffix))==4096 and a.data(old+suffix)==a.data(live+suffix)==a.data(clean+suffix),'Entire current-page retry conservation '+hex(page));counts['whole_retry_page_endpoint_joins']+=2
       counts['same_session_refusals']+=1
       continue
      first=sample;allocs=records(a,live+'locale-allocations.bin','<16Q');access=records(a,live+'locale-source-accesses.bin','<2IQ2I')
      # Generation/initial bytes are real actual owners. Every complete current
      # guest page is reconstructed solely from its measured initial and source
      # stores. This checks that negative candidates cannot commit hidden stores.
      for o in allocs:
       if o[6]!=4 or not o[9]:continue
       need(o[2]==24 and o[3]==32 and o[4]==4096 and o[8]and o[5],'Positive actual tree owner24/rounded32 with current native association')
       stem=live+f'locale-allocation-{o[5]}';initial=a.data(stem+'-initial.bin');want=bytearray(initial+bytes(4096-len(initial)))
       need(len(initial)==32,'Full genuine native initial backing32')
       for pc,address,value,width,writing in access:
        if writing and o[1]<=address<o[1]+4096:
         need(address+width<=o[1]+24,'Actual committed source store within requested tree owner');want[address-o[1]:address-o[1]+width]=value.to_bytes(width,'little')
       need(bytes(want)==a.data(stem+'-expected.bin')==a.data(stem+'-owned-page.bin'),'Full mapped owner page follows only genuine source commits')
       need(want[24:32]==initial[24:32],'All capacity tails retain genuine initial bytes');counts['whole_owner_page_source_replays']+=1
      if case==0:
       need(tags[3]==tags[4]==1 and tags[10]==tags[11]==7 and not tags[12]and not tags[13],'Actual registered positive tree extent')
       need(a.words(live+'tree-status.bin',8,'Q')==(1,1,1,0,26,85,172,7),'Positive exact tree causal cursors/depth bound')
       need(len(records(a,live+'fs-owned-publications.bin','<16Q'))==7 and len(records(a,live+'tree-lockit-contexts.bin','<16Q'))==26,'Positive seven generation publications and26 scratch context CALLs')
       counts['registered_positive_roots']+=1;continue
      need(not tags[3]and not tags[4]and tags[12]==tags[13]==tags[14]==tags[15]==1,'Exactly one actual intervention and refusal, no credited root')
      trig=root+'trigger/';id=a.words(trig+'identity.bin',4);need(id[2:]==(1,1),'Exact one real trigger/intervention')
      v=a.words(trig+'intervention.bin',16,'Q');fault=a.words(live+'locale-fault.bin',4);reason=a.data(live+'locale-fault-reason.bin').decode();need(fault[0]==1 and reason and a.data(live+'registry-exception-message.bin').decode()==reason,'First native predicate reason retained beyond generic Runtime exception')
      if case<=4:
       need(id[:2]==(86,0x4bab44)and v[0]==1 and v[3]==v[2]+4 and v[6:9]==(4,0x4bab44,case),'Actual source [EDI+4] counterfactual matches precise decoded operand')
       probe=a.words(trig+'fs-owned-access-probe.bin',16,'Q');need(probe[0]==1 and probe[3]==0x4bab44 and probe[4]==v[1]+4,'Actual pending original owner write before intervention')
       a0=records(a,trig+'locale-allocations.bin','<16Q');target=next(o for o in a0 if o[1]<=v[3]and v[3]+4<=o[1]+o[3]);current=next(o for o in a0 if o[1]==v[1]);need(current[6]==4,'Actual current tree owner')
       offset=v[3]-target[1];need(int.from_bytes(a.data(trig+f'locale-allocation-{target[5]}-owned-page.bin')[offset:offset+4],'little')==v[4],'True original candidate cell before reentrant service')
       need(a.data(trig+f'locale-allocation-{target[5]}-owned-page.bin')==a.data(live+f'locale-allocation-{target[5]}-owned-page.bin'),'Exact candidate store denied before full target page commit')
       expected='Owned tree operand cannot use a foreign, expired or non-MFC allocation'if case==1 else'Tree access requires exact source operand and current requested owner generation'if case==2 else'Tree access retains its exact source PC, role occurrence, offset and causal order'
       need(reason==expected and fault[1]==0x4bab44 and fault[2]==v[3],'Exact owner admission first fault, not generic observer mutation')
       if case==1:need(target[6]==1,'Foreign actual registry kind1 still live')
       if case==2:need(target[1]==current[1]and offset==24 and offset+4<=32,'Requested-tail access is physically within real capacity but outside admitted request')
       if case==3:need(target[1]==int.from_bytes(a.data(trig+'whole-page-'+str(0x60b000)+'.bin')[0x314:0x318],'little'),'Wrong live header role')
       if case==4:need(target[1]!=current[1]and target[6]==4 and target[5]!=current[5],'Wrong repeated allocator occurrence with distinct actual current generation')
       counts['exact_owner_service_denials']+=1
      elif 5<=case<=10:
       old=a.data(trig+'private-before.bin');new=a.data(trig+'private-after.bin');need(len(old)==len(new)and sum(x!=y for x,y in zip(old,new))==1 and sum((x^y).bit_count()for x,y in zip(old,new))==1,'One bit of actual direct private vector changed')
       need(v[0]==2 and v[1]<len(old)and v[2]==len(old),'Actual private mutation offset and full evidence')
       need('observer changed'in reason.lower(),'Explicit observer conservation first fault');counts['private_witness_denials']+=1
      elif case==15:
       old=a.data(trig+'native40-before.bin');new=a.data(trig+'native40-after.bin');need(len(old)==len(new)==40 and old[:12]==new[:12]and old[16:]==new[16:]and int.from_bytes(old[12:16],'little')^int.from_bytes(new[12:16],'little')==1,'Exactly actual native40 RecursionCount bit changed')
       need(reason=='Lockit observer changed actual native resource bytes','Native bytes first fault precedes actual resource restoration/cleanup');counts['actual_native40_denials']+=1
      else:
       need(v[0]in(4,5,6),'Actual memory/FX/permission intervention retained');counts['source_machine_permission_denials']+=1
      causes.append(dict(level=level,scenario=case,hook_point=id[0],actual_State_PC=id[1],first_fault_PC=fault[1],first_fault_address=fault[2],reason=reason,intervention=list(v),exact_owner_service=case<=4))
      counts['causal_denials']+=1
    counts['levels']+=1
   finally:a.close()
  need(counts['causal_denials']==17*len(levels)and counts['same_session_refusals']==18*len(levels),'Every selected case and same-Session refusal consumed')
  for q,h in pins.items():need(sha(q)==h,'Final physical immutability '+q)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'actual-causes.json').write_text(json.dumps(causes,indent=2)+'\n')
  report=dict(passed=passed,scope='Independent full isolated actual Runtime tree controls reader: exact source owner admission and separate private/resource/source machine refusals; no broad125 or alternate-path credit',execution_sha256=digest,build_sha256=b['preparation_sha256']if False else e['build_sha256']if'e'in locals()else None,native_preparation_sha256=e['native_preparation_sha256']if'e'in locals()else None,levels=list(levels),counts=dict(counts),wholeState_retry=True,wholeCPU_retry=True,wholeFX_retry=True,full_caller_FX512_equality_claim=False,source_API_volatile_equality_claim=False,initializer_credit=0,reader_closed=True,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3],tuple(sys.argv[4:])or('O0','O2'))
