"""Strict ordinary-file refusals, own-input byteflows and poisoned retries."""
from pathlib import Path
import collections,hashlib,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='47af86a27b82f00b38b5da26eeb1017058f997d32bb89cac5d4ac81fa7a45663'
BH='63f6d56ce07bba98a5ec1decdbaf3e061751393807c15b3aa625292d38d34017'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(execution,execution_sha,name):
 out=R/'reports/m4-widget-native'/name;need(not out.exists(),'Fresh exact actual control verification');out.mkdir();pins={};counts=collections.Counter();causes=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or v==h,'Exact ordinary input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable same input');pins[str(p)]=v;return p
 def raw(p,h=None):return pin(p,h).read_bytes()
 def read(p,h=None):return json.loads(raw(p,h))
 def eq(a,b,label):need(a==b,label)
 def words(p,n):return struct.unpack('<'+'I'*n,raw(p))
 def Qs(p,n):return struct.unpack('<'+'Q'*n,raw(p))
 def rows(b,size,fmt):
  need(len(b)%size==0,'Complete raw private rows');return [struct.unpack_from(fmt,b,o)for o in range(0,len(b),size)]
 def memory(folder):
  result={int(f.stem.removeprefix('game-region-')):bytearray(raw(f))for f in folder.glob('game-region-*.bin')};need(result and all(v and len(v)%4096==0 for v in result.values()),'Complete actual admitted game regions');result[0x20001000]=bytearray(raw(folder/'stack.bin'));need(len(result[0x20001000])==4096,'Whole actual stack');tib=words(folder/'TIB.bin',5);need(tib[0]==tib[4]and tib[2:4]==(0x20002000,0x20001000),'Exact current minimal TIB identity');
  for offset,value in((0,tib[1]),(4,tib[2]),(8,tib[3]),(24,tib[4])):result[tib[0]+offset]=bytearray(struct.pack('<I',value))
  return result,tib
 def payload(m,address,n):
  owners=[(a,b)for a,b in m.items()if a<=address and address+n<=a+len(b)];need(len(owners)==1,'One exact own-memory input extent '+hex(address));a,b=owners[0];return bytes(b[address-a:address-a+n])
 def store(m,address,data):
  owners=[(a,b)for a,b in m.items()if a<=address and address+len(data)<=a+len(b)];need(len(owners)==1,'One complete own-memory output extent');a,b=owners[0];b[address-a:address-a+len(data)]=data
 def hardware(p,label):
  b=raw(p);need(len(b)==1632,'Complete actual host invoke boundary');eq(b[:512],b[1088:1600],label+' raw fullFX512 before/restored');eq(b[512:540],b[1600:1628],label+' raw fullENV28 before/restored');counts['whole_ASM_FX512_ENV28_restore_pairs']+=1
 try:
  e=read(execution,execution_sha);need(e['passed']and e['all_workers_terminal']and e['actual_workers_launched']==16 and e['preparation_sha256']==PH and e['build_sha256']==BH,'Exact terminal16 current worker controls');read(R/'reports/m4-widget-native/controls-preparation-r1/report.json',PH);read(R/'reports/m4-widget-native/controls-build-r2/build.json',BH)
  recipe=read(e['source_review'],e['source_review_sha256']);need(recipe['passed']and recipe['control_modes_reviewed']==8,'Independent exact source/geometry review');contract=read(R/'reports/m4-widget-native/preparation-r6/contracts.json');root_contract=contract['roots'][0];operands=contract['ordered_operands_by_root'][0]if 'ordered_operands_by_root'in contract else None
  literal_header=raw(R/'reports/m4-widget-native/preparation-r6/literals.hpp').decode();need('inline constexpr Access operands'not in literal_header,'Operand table schema remains explicit; parse frozen contracts instead')
  # These are exact current guard messages, not guessed weaker classifications.
  detail={1:'Flat source DS/ES/SS/current owned minimal TIB',2:'Source forward-string DF input',3:'Exact current owning IAT operand preimage',4:'Complete physical widget source instruction bytes',5:'Guest access permission denied',6:'Guest access permission denied',7:'Guest access permission denied',8:'Exact selected source root and actual Runtime route'}
  component=raw(R/'reports/m4-widget-native/preparation-r6/component.cpp').decode()
  for mode,text in detail.items():need(text in component or text in raw(R/'runtime/memory/guest_memory.cpp').decode(),'Exact consumed source refusal text '+str(mode))
  seen=set()
  for run in e['runs']:
   level,mode=run['level'],run['mode'];need(level in('O0','O2')and mode in range(1,9)and(level,mode)not in seen,'Unique actual mode/level');seen.add((level,mode));folder=Path(run['capture']);manifest=read(run['output_manifest'],run['output_manifest_sha256'])
   for logical,value in manifest.items():f=pin(folder/logical,value['sha256']);need(f.stat().st_size==value['bytes'],'Whole current observation size')
   status=words(folder/'cleanup/status.bin',8);need(status[:5]==(1,mode,1,1,1)and status[5]==status[6]==1 and status[7]==1,'One incomplete actual Runtime CALL, same poisoned retry, finished cleanup')
   first=folder/'control/authored-before';before,tib=memory(first);cpu=words(first/'CPU.bin',10);state=raw(first/'State.bin');fx=raw(first/'FX.bin');need(len(state)==3504 and len(fx)==512,'Complete authored current machine');target=0x40ef50 if mode==8 else 0x40e250;F=cpu[4]-4;need(F==0x20001800,'Actual caller frame for source-address roles')
   physical,_=memory(folder/'initial-own-input');game_keys=[a for a in before if a not in(0x20001000,tib[0],tib[0]+4,tib[0]+8,tib[0]+24)]
   need(set(game_keys)=={a for a in physical if a not in(0x20001000,tib[0],tib[0]+4,tib[0]+8,tib[0]+24)},'Entire actual same admitted game mapping inventory')
   if mode==3:store(physical,0x5bb070,bytes(4))
   if mode==4:store(physical,0x40e250,bytes([payload(physical,0x40e250,1)[0]^1]))
   for a in game_keys:eq(bytes(before[a]),bytes(physical[a]),'Whole admitted game input plus exact authored fault');counts['whole_authored_Game_region_joins']+=1
   if mode==1:need(struct.unpack_from('<I',state,2184)[0]==4,'Actual source DS mutation')
   if mode==2:need(state[2075]==1 and cpu[8]&0x400 and struct.unpack_from('<Q',state,2080)[0]&0x400,'Actual source DF mutation in State and caller CPU')
   first_reason=raw(folder/'control/refusal.txt').decode();site=cpu[9]if mode==6 else target;expected=f'memory_access site=0x{site:08x} target=0x{target:08x}: Admitted native callback failed: {detail[mode]}';eq(first_reason,expected,'Exact actual first seam/Runtime target/reason');counts['exact_first_refusal_relations']+=1
   before_retry=folder/'retry-before';after_retry=folder/'retry-after';names_before={str(f.relative_to(before_retry)).replace('\\','/')for f in before_retry.rglob('*')if f.is_file()};names_after={str(f.relative_to(after_retry)).replace('\\','/')for f in after_retry.rglob('*')if f.is_file()};need(names_before-{'retry-reason.txt'}==names_after and 'retry-reason.txt'in names_before,'Exact whole retry output inventory and one separately bounded caught reason');retry_reason=raw(before_retry/'retry-reason.txt').decode();eq(retry_reason,f'poisoned site=0x{site:08x} target=0x{site:08x}: Earlier admitted callback failed; create a new context','Exact actual same poisoned Runtime denial')
   for logical in sorted(names_after):eq(raw(before_retry/logical),raw(after_retry/logical),'Whole same-context retry byte equality '+logical);counts['whole_exported_retry_files_equal']+=1
   checkpoints=list(before_retry.glob('root-*/component'));checkpoints+=list(before_retry.glob('bootstrap/component'));need(len(checkpoints)==1,'Exactly one current component refusal endpoint');c=checkpoints[0];cs=Qs(c/'status.bin',12);need(cs[0]>0 and cs[1]==0 and cs[5]==1 and cs[6]==0 and cs[7]==0 and cs[10]==0,'Current failed component, no completed selection/GDI/font generation');need(not raw(c/'APIs.bin')and not raw(c/'fonts.bin'),'No GDI/native font created before these eight required refusals');need(not list((folder/'cleanup').glob('manual-font-cleanup/*-row.bin')),'No owned-font cleanup invented for fault prefixes')
   accesses=rows(raw(c/'accesses.bin'),24,'<IIQII');failed_write=mode in(5,7);need(bool(accesses)if mode in(3,5,7)else not accesses,'Observed source-prefix extent distinguishes early boundary and literal refusals')
   # Reconstruct all observable byte changes from own BEFORE and actual exact
   # admitted source scalar rows. Scalar register predictions remain separate.
   if mode!=6:store(before,F,struct.pack('<I',0xfffffff0))
   pcs={v['pc']:v for v in contract['instructions']};blocked=None
   for n,(pc,a,value,width,writing)in enumerate(accesses):
    need(pc in pcs and width in(1,2,4)and writing in(0,1),'Exact physical current literal scalar row')
    if not writing:eq(int.from_bytes(payload(before,a,width),'little'),value,'Every actual read joins current own backing')
    elif failed_write and n==len(accesses)-1:
     blocked=dict(PC=pc,address=a,value=value,width=width);need(a==tib[0]and width==4 if mode==7 else any(start<=a and a+width<=start+len(before[start])and start<=0x5f4d78<start+len(before[start])for start in game_keys),'Actual final denied complete source write lies in authored read-only mapping')
    else:store(before,a,value.to_bytes(width,'little'))
   actual_fault,tib_after=memory(before_retry/'runtime')
   for a in game_keys:eq(bytes(before[a]),bytes(actual_fault[a]),'Complete own game fault byteflow; final denied write remains uncommitted');counts['whole_fault_Game_region_byteflows']+=1
   eq(bytes(before[0x20001000]),bytes(actual_fault[0x20001000]),'Whole actual stack from Runtime CALL plus committed source rows');eq(struct.unpack('<I',before[tib[0]])[0],tib_after[1],'Whole actual current source FS head; denied FS write is uncommitted');counts['whole_fault_stack_TIB_relations']+=1
   if mode==3:need(accesses[-1]==(0x5a013c,0x5bb070,0,4,0),'Actual exact changed raw source IAT read at first named GDI CALL')
   if mode in(1,6,8):eq(raw(before_retry/'runtime/State.bin'),state,'Early refusal leaves entire guest Remill State unprojected')
   for p,label in((folder/'control/caller-hardware.bin','first refusal'),(folder/'control/retry-hardware.bin','poisoned retry'),(folder/'cleanup/font-caller-hardware.bin','manual cleanup')):hardware(p,label)
   summary=Qs(folder/'cleanup/registry-summary.bin',32);need(summary[:5]==(1,1,0,1,1)and summary[5]==0 and summary[10]==summary[11]==summary[15]==0,'Actual poisoned Session promotion and complete native resource/heap cleanup');counts['actual_poisoned_cleanup_relations']+=1
   causes.append(dict(level=level,mode=mode,source_input_class=recipe.get('refusal_classes',[None]*8)[mode-1]if recipe.get('refusal_classes')else detail[mode],actual_first_reason=first_reason,actual_retry_reason=retry_reason,actual_Runtime_fault_site=site,target=target,source_accesses=[list(v)for v in accesses],last_denied_write=blocked,attempted_write_committed=False if blocked else None,whole_observed_retry_files=len(names_after),whole_hidden_Runtime_or_permissions_claim=False))
  need(seen=={(level,mode)for level in('O0','O2')for mode in range(1,9)}and counts['exact_first_refusal_relations']==16 and counts['whole_ASM_FX512_ENV28_restore_pairs']==48 and counts['actual_poisoned_cleanup_relations']==16,'All actual exact fault/retry/cleanup scopes closed');passed=True
 except BaseException:
  passed=False;(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'actual-causes.json';q.write_text(json.dumps(causes,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable)
  for q,h in list(pins.items()):need(sha(q)==h,'All observed current files unchanged during verification')
  report=dict(passed=passed,scope='Exact actual eight widget fault causes, observable own-BEFORE scalar byteflows, same poisoned-context full exported retries, actual native resource cleanup and complete raw ASM caller512/28 restores',execution_sha256=execution_sha,preparation_sha256=PH,build_sha256=BH,counts=dict(counts),partial_fault_State_register_prediction=False,source_scalar_register_value_prediction=False,permission_bytes_observed=False,hidden_Runtime_vector_bytes_observed=False,bootstrap_and_cleanup_source_execution_modeled=False,hardware_scope='Inside actual ASM invoke/catch/restore; outside rethrow hardware not captured',archive_reader_opened=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=passed,counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
