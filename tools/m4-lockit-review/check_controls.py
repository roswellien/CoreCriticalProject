"""Independent whole-machine, live owner, real resource and targeted refusal audit."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-lockit-review'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import verify_stage
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(execution,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh control gate');out.mkdir(parents=True);pins={};counts=Counter();causes=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();a=pins.get(str(p)) or sha(p);need(h is None or h==a,'Immutable physical input '+str(p));pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def module(n,p):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def records(a,p,n):
  b=a.data(p);need(len(b)%(8*n)==0,'Whole record '+p);return list(struct.iter_unpack('<'+str(n)+'Q',b))
 try:
  ex=read(execution,digest);need(ex['passed'],'Actual complete control execution');build=read(ex['build'],ex['build_sha256']);need(build['passed'],'Actual compiled controls')
  for p,h in build['sources'].items():pin(p,h)
  pin(__file__);H=module('lockit_whole_machine_control_helpers',ROOT/'tools/m4-container-controls/check_v2.py');D=module('lockit_control_strict_reader',ROOT/'tools/m4-crt-allocation-root/run_v2.py')
  preparation=read(build['preparation']);native=read(Path(preparation['native_include'])/'report.json');need(native['passed'],'Actual new native source preparation')
  need(read(BASE/'native-integration-r3/report.json')['passed'],'Independent current source/resource guard gate')
  for l in ex['levels']:
   verify_stage(Path(l['stage']).parent,l['stage_sha256']);a=D.DirectSet(pin(l['capture'],l['capture_sha256']),pin)
   try:
    need(a.words('header.bin',6)==(1,16,32,9968,4,8),'Actual whole retained control record ABI')
    for case in range(16):
     base=f'case-{case}/';first=None
     for retry in (0,1):
      stem=base+('retry' if retry else 'first');sample=a.data(stem+'.bin');need(len(sample)==9968,'Complete retained caller/machine sample')
      tags=struct.unpack_from('<32Q',sample);before=struct.unpack_from('<32Q',sample,256);after=struct.unpack_from('<32Q',sample,512)
      need(tags[:3]==(1,case,retry) and tags[6]==tags[16]==1 and tags[7]==0x4d573354 and not((tags[8]^tags[9])&0x400),'Real complete cleanup/caller hardware/LastError/DF')
      need(after[4]==1 and not any(after[i] for i in (10,11,15)),'No real live native owner, CS or heap after cleanup')
      H.hardware(sample[8880:9424],sample[9424:9968],True);H.hardware(a.data(stem+'-cleanup-hardware-before.bin'),a.data(stem+'-cleanup-hardware-after.bin'));counts['rich_caller_hardware_pairs']+=1;counts['real_cleanup_hardware_pairs']+=1
      for suffix,size in (('State',3504),('CPU',40),('FX',512),('guest-ENV',28),('stack',4096)):need(len(a.data(stem+'-causal-'+suffix+'.bin'))==size,'Complete causal machine '+suffix)
      if retry:
       need(not tags[3] and not tags[4] and before==after and sample[768:4272]==sample[4272:7776] and sample[7776:8288]==sample[8288:8800] and sample[8800:8840]==sample[8840:8880],'Same poisoned/finished Session refuses work while conserving entireState3504/FX512/CPU40 and ownership')
       need(first[4272:7776]==sample[768:4272] and first[8288:8800]==sample[7776:8288] and first[8840:8880]==sample[8800:8840],'Retry starts from exact whole prior cleaned machine')
       for target in ('retry-live/','retry-cleaned/'):counts['whole_retry_records']+=H.copied_suffixes(a,base+'first-cleaned/',base+target)
       counts['same_session_refusals']+=1
      else:
       first=sample
       if case:need(not tags[3] and tags[5]==tags[14]==1 and not tags[4],'Exactly one reached first-root targeted refusal with no initializer credit')
       else:need(tags[3:7]==(1,4,0,1) and tags[10:12]==(4,8),'Four original small roots, fourFSframes, eightactualMFCowners completed')
      counts['actual_attempts']+=1
     live=base+'first-live/';clean=base+'first-cleaned/';trigger=base+'first-trigger/'
     source=list(struct.iter_unpack('<IIQII',a.data(live+'locale-source-accesses.bin')));calls=records(a,live+'lockit-calls.bin',16);imports=records(a,live+'lockit-imports.bin',8);owners=records(a,live+'locale-allocations.bin',16);freed=records(a,clean+'locale-allocations.bin',16);sections=records(a,clean+'locale-critical-sections.bin',16)
     need(len(owners)==len(freed) and all(o[:8]==f[:8] and f[8:10]==(0,0) and f[10]+f[11]==1 for o,f in zip(owners,freed)),'Every real owner provenance retained, backing freed and guest alias unmapped exactly once')
     need(len(sections)==5 and all(s[5]==0 and s[8] and s[9] and s[6]==s[7]==1 for s in sections),'All inherited four plus distinct actual fifth resource initialized and deleted exactly once')
     named=next(s for s in sections if s[1]==0x78145640);need(named[11]==40 and named[10],'Actual distinct native40 object identity')
     H.chain_checks(a,live,source,not case,counts);H.independent_identity(a,case,pin);counts['named_cleanup_API_identities']+=1
     addresses=a.words(live+'current-page-addresses.bin',len(a.data(live+'current-page-addresses.bin'))//4)
     need(0x78145000 in addresses and 0x78146000 in addresses and 0x7810a000 in addresses,'Whole loaded provider/code/input pages retained')
     for address in addresses:need(len(a.data(live+f'current-page-{address}.bin'))==4096,'Whole unmasked current admitted page');counts['whole_current_pages']+=1
     if not case:
      need(len(calls)==len(imports)==8 and all(w[11]==1 for w in calls),'Eight genuine source CALL/RET records completed')
      for index,w in enumerate(calls):
       need(w[0:2]==(1,index) and w[3]==(0x7810a290 if index%2==0 else 0x7810a350) and w[8]==index%2 and w[13]==(1 if index%2==0 else 0),'Exact balanced serial source constructor/destructor/resource recursion')
       need(w[12]==w[7] if index%2==0 else True,'Actual constructor return is source scratchECX')
      need(len([o for o in owners if o[6]==4])==8,'Eight genuine new MFC owners')
      H.owned_replay(a,live,owners,source,counts)
      for o in owners:
       expected=a.data(live+f'locale-allocation-{o[5]}-expected.bin');actual=a.data(live+f'native-full-{o[5]}.bin');need(actual==expected[:o[3]],'Complete actual native backing agrees with independently source-rebuilt committed guest backing')
      counts['positive_four_root_runs']+=1;counts['positive_actual_Lockit_CALL_RET']+=8;counts['positive_actual_new_owners']+=8
     else:
      identity=a.words(trigger+'identity.bin',3);need(identity[0]==(41 if case in (11,12) else 40) and identity[1]==0x7810a30b,'Exact targeted first genuine source API boundary')
      trigger_call=records(a,trigger+'calls.bin',16);need(len(trigger_call)==1 and trigger_call[0][2]==0x411010 and trigger_call[0][3]==0x7810a290,'Retained genuine constructor CALL source prefix')
      fault=a.words(live+'locale-fault.bin',4);need(fault[0] and fault[1]==0x7810a30b,'Checked first-fault source PC identity')
      reason=a.data(live+'registry-exception-message.bin').decode();need(reason,'Actual source/private guard refusal reason retained')
      effect=a.words(trigger+'actual-intervention.bin',8,'Q')
      if case in (1,2,3,4,5,6,7):
       address=0x78145658 if case<=3 else {4:0x78145640,5:0x5bb4f8,6:0x78146198,7:0x7810a290}[case]
       need(effect[0]==1 and effect[1]==address and effect[2]!=effect[3] and effect[6]==effect[3],'Actual causal source byte/DWORD intervention')
       if case<=3:need(effect[2]==2 and effect[3]==(0 if case==1 else 1 if case==2 else 3),'Only authentic observed state2 admitted')
       need(struct.unpack_from('<I',a.data(live+f'current-page-{address&~4095}.bin'),address&4095)[0]==effect[3],'Actual retained whole page contains intervention')
      elif case in (8,9,10,11):
       old=a.data(trigger+'private-before.bin');new=a.data(trigger+'private-after.bin');need(identity[2]==1 and len(old)==len(new)>0 and sum(x!=y for x,y in zip(old,new))==1,'One physical actual private witness byte changed')
       name=a.data(trigger+'private-name.bin').decode();need(a.data(live+name)==new,'Actual retained private backing is changed witness; not authored substitute')
      elif case==12:
       old=a.data(trigger+'native40-before.bin');new=a.data(trigger+'native40-after.bin');need(identity[2]==1 and len(old)==len(new)==40 and old[:12]==new[:12] and old[16:]==new[16:] and struct.unpack_from('<I',old,12)[0]==1 and struct.unpack_from('<I',new,12)[0]==0,'Actual held native40 RecursionCount intervention before guard; physical state restored after refusal before cleanup')
       need('actual native resource bytes' in reason,'Complete actual native40 observer guard caused refusal')
      elif case==13:
       old=a.data(trigger+'FX.bin');new=a.data(base+'first-causal-FX.bin');need(len(old)==len(new)==512 and new[0]==old[0]^1 and new[1:]==old[1:],'Whole genuine guestFX512 byte intervention carried into refusal')
      elif case==14:need(effect[0]==2 and effect[1]==0x78145000 and effect[5]==1,'Read-only authentic sourceCS data page intervention')
      elif case==15:
       need(effect[0]==3 and effect[1]==struct.unpack_from('<I',a.data(trigger+'CPU.bin'),16)[0]+4 and effect[2]==0x78145640 and effect[3]==0x78145644,'Actual source API frame argument intervention')
      causes.append({'level':l['level'],'case':case,'point':identity[0],'source_PC':identity[1],'reason':reason,'source_prefix_rows':len(source),'actual_intervention':effect})
      counts['causal_targeted_refusals']+=1
     counts['real_resources_deleted']+=5
    need(a.data('COMPLETE.txt') and a.words('counts.bin',3)[1:]==(16,32),'Actual fixture completion after all controls and retries')
   finally:a.close()
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'causes.json').write_text(json.dumps(causes,indent=2)+'\n');pin(out/'causes.json')
  report={'passed':passed,'scope':'Independent actual isolated four-root resource/source/private/machine causal controls; canonical124 paired acceptance separate','initializer_credit':False,'counts':dict(counts),'files':pins}
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':passed,'sha256':sha(out/'report.json'),'counts':dict(counts)}))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
