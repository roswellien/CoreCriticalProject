"""Ordinary-file proof of current carried Context fault/retry/cleanup.

This checker never launches a worker or opens a canonical archive. Each partial
fault memory endpoint is reconstructed from that same Context's full input
bytes plus its committed Runtime CALL and exact literal operand prefix. It
does not predict partial scalar registers, unexported Runtime frames or rights.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'
SERVICE='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9'
COMPONENT='c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21'
CASES=((0,127,0),(0,895,7),(0,3967,0),(1,1151,7),(1,2687,0),(1,3711,7))
DETAIL={1:'Flat source DS/ES/SS/current owned minimal TIB',2:'Source forward-string DF input',3:'Exact current owning IAT operand preimage',4:'Complete physical widget source instruction bytes',5:'Guest access permission denied',6:'Guest access permission denied',7:'Guest access permission denied',8:'Exact selected source root and actual Runtime route'}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def eq(a,b,m):need(a==b,m)
def rows(b,size,fmt):
 need(len(b)%size==0,'Complete fixed-width rows');return [struct.unpack_from(fmt,b,n)for n in range(0,len(b),size)]
def main(execution,execution_sha,name):
 out=R/'reports/m4-joint-startup138'/name;need(not out.exists(),'Fresh immutable ordinary Context verification');out.mkdir();pins={};counts=collections.Counter();proofs=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No canonical archive input');v=sha(p);need(h is None or v==h,'Exact ordinary input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable current ordinary input');pins[str(p)]=v;return p
 def raw(p,h=None):return pin(p,h).read_bytes()
 def read(p,h=None):return json.loads(raw(p,h))
 def W(p,n):b=raw(p);need(len(b)==4*n,'Whole DWORD record');return struct.unpack('<'+'I'*n,b)
 def Q(p,n):b=raw(p);need(len(b)==8*n,'Whole QWORD record');return struct.unpack('<'+'Q'*n,b)
 def inventory(folder):return {str(p.relative_to(folder)).replace('\\','/'):p for p in folder.rglob('*')if p.is_file()}
 def equal_folder(before,after,label):
  a,b=inventory(before),inventory(after);eq(set(a),set(b),label+' complete exported inventory');need(a,label+' nonempty');
  for n in sorted(a):eq(raw(a[n]),raw(b[n]),label+' whole '+n);counts['whole_exported_retry_files_equal']+=1
 def component(folder,stem):
  found=[p for p in (folder/'Widget').glob('root-*/*')if p.name==stem];need(len(found)==1,'One actual current component '+stem);return found[0]
 def memory(folder):
  m={int(p.stem.split('-')[-1]):bytearray(raw(p))for p in folder.glob('game-region-*.bin')};need(m and all(v and len(v)%4096==0 for v in m.values()),'Whole current admitted Game extents');
  for p in folder.glob('provider-source-page-*.bin'):
   a=int(p.stem.split('-')[-1]);b=bytearray(raw(p));need(len(b)==4096 and a not in m,'Whole distinct finite provider source page');m[a]=b
  need(len(list(folder.glob('provider-source-page-*.bin')))==5,'All five current formatter provider pages');m[0x20001000]=bytearray(raw(folder/'stack.bin'));need(len(m[0x20001000])==4096,'Whole own current stack');t=W(folder/'TIB.bin',5);need(t[0]==t[4]and t[2:4]==(0x20002000,0x20001000),'Exact current minimal TIB identity');
  for o,v in((0,t[1]),(4,t[2]),(8,t[3]),(24,t[4])):m[t[0]+o]=bytearray(struct.pack('<I',v))
  ordered=sorted(m);need(all(a+len(m[a])<=b for a,b in zip(ordered,ordered[1:])),'Exact disjoint observed own memory inventory');return m,t
 def payload(m,a,n):
  found=[(s,b)for s,b in m.items()if s<=a and a+n<=s+len(b)];need(len(found)==1,'One complete own operand backing '+hex(a));s,b=found[0];return bytes(b[a-s:a-s+n])
 def store(m,a,b):
  found=[(s,v)for s,v in m.items()if s<=a and a+len(b)<=s+len(v)];need(len(found)==1,'One exact committed output backing');s,v=found[0];v[a-s:a-s+len(b)]=b
 def equal_memory(m,actual,label):
  eq(set(m),set(actual),label+' complete inventory');
  for a in sorted(m):eq(bytes(m[a]),bytes(actual[a]),label+' whole '+hex(a));counts['whole_fault_memory_extent_relations']+=1
 def hardware(p,label):
  b=raw(p);need(len(b)==1632,'Complete current ASM boundary1632');eq(b[:512],b[1088:1600],label+' complete rawFX512 restoration');eq(b[512:540],b[1600:1628],label+' complete ENV28 restoration');counts['whole_ASM_FX512_ENV28_restore_pairs']+=1
 try:
  e=read(execution,execution_sha);need(e['passed']and e['all_workers_terminal']and e['actual_workers_launched']==16 and e['preparation_sha256']==PH and e['ordinary_outputs_only']and not e['archive_reader_opened'],'Exact terminal current eight-by-two ordinary controls');p=read(e['preparation_path'],PH);b=read(e['build_path'],e['build_sha256']);ad=read(e['admission_review'],e['admission_review_sha256']);need(b['passed']and b['preparation_sha256']==PH and ad['passed']and ad['preparation_sha256']==PH and ad['build_sha256']==e['build_sha256'],'Exact current physical worker/admission lineage');need(p['borrowed_service_preparation_sha256']==SERVICE and p['control_modes']==8 and p['control_phase']==135 and p['completed_prefix_roots']==135 and p['source_owned_font_create_calls']==15,'Exact current source-owned service and fault prefix');
  for d in(p,b,ad):
   for q,h in d['files'].items():pin(q,h)
  cp=read(R/'reports/m4-fps-native/connected-component-preparation-r4/report.json',COMPONENT);contract=read(R/'reports/m4-fps-native/connected-component-preparation-r4/contracts.json');lit=raw(R/'reports/m4-fps-native/connected-component-preparation-r4/literals.hpp').decode();component_code=raw(R/'reports/m4-fps-native/connected-component-preparation-r4/component.cpp').decode();runtime_code=raw(R/'tools/m4-runtime/runtime.cpp').decode();pin(R/'runtime/memory/guest_memory.cpp');pin(R/'tools/m4-joint-startup138/controls_main.cpp');pin(R/'tools/m4-joint-startup138/run_context_controls.py');
  for text in DETAIL.values():need(text in component_code or text=='Guest access permission denied','Exact consumed refusal literal');need('Admitted native callback failed: 'in runtime_code and 'image_.memory.store<std::uint32_t>(GuestAddress{frame_sp}, return_pc.value)'in runtime_code,'Actual Runtime CALL-first committed-memory and exception wrapper');
  def table(kind):
   match=re.search(r'inline constexpr '+kind+r' (\w+)\[\]\{(.*?)\n\};',lit,re.S);need(match,'Exact frozen literal table '+kind);return match.group(2)
  roots=[tuple(map(int,x.split(',')))for x in re.findall(r'\{([^{}]+)\}',table('Root'))];need([v[0]for v in roots]==[0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0],'Current actual sorted component root slices');second=roots[5];first=roots[4];prefix_access_count=sum(v[12]for v in roots[:5]);prefix_GDI_count=sum(v[6]for v in roots[:5])
  operands=[(int(a),int(role),int(off),int(width),writing=='true')for a,role,off,width,writing in re.findall(r'\{(\d+),(\d+),(-?\d+),(\d+),(true|false)\}',table('Operand'))];need(len(operands)>=second[11]+second[12],'Complete actual ordered operands');pcs={v['pc']:v for v in contract['instructions']};F=0x20001800;BROKER=0x410a80;need('frame=0x20001800, broker=0x410a80'in raw(Path(p['parent_preparation']).parent/'joint_protocol.hpp').decode(),'Exact current actual caller frame and broker');
  gp=pin(R/'tools/m4-widget-growth-review/gdi_identity.py');spec=importlib.util.spec_from_file_location('context_GDI_identity',gp);GDI=importlib.util.module_from_spec(spec);spec.loader.exec_module(GDI);read(R/'reports/m4-widget-growth-review/gdi-preparation-r1/report.json','47c4e97080b280ba3e34a2923b054fa564ee84240a35436303ecb9a4f72e18de');seen=set()
  for run in e['runs']:
   level,mode=run['level'],run['mode'];need(level in('O0','O2')and mode in range(1,9)and(level,mode)not in seen,'Unique actual level/mode');seen.add((level,mode));folder=Path(run['capture']);manifest=read(run['output_manifest'],run['output_manifest_sha256']);observed=inventory(folder);eq(set(manifest),set(observed),'Every ordinary output is covered by current full manifest');
   for n,v in manifest.items():need(Path(n).as_posix()==n and '..'not in Path(n).parts and not Path(n).is_absolute(),'Canonical safe manifest path');q=pin(folder/n,v['sha256']);eq(q.stat().st_size,v['bytes'],'Whole actual output size')
   status=W(folder/'status.bin',16);eq(status[:5],(1,mode,*CASES[(mode-1)%6]),'Actual six-domain carried case');eq(status[5:10],(1,1,1,1,135),'Actual first Context failure/Runtime poison/sixteen completed');need(status[10]==status[11] and status[12]==135 and status[15]==1,'Same actual route count/firstfault phase/complete resource release');eq(raw(folder/'admission.txt').decode(),e['admission_review_sha256'],'Actual independent admission marker');eq(raw(folder/'COMPLETE.txt'),b'Complete current Context refusal/retry and owned cleanup','Complete actual Context output');
   records=raw(folder/'prefix-records.bin');need(len(records)==135*159716,'135 whole successful current Native records');
   for phase,item in enumerate(p['selected_order'][:135]):
    record=records[phase*159716:(phase+1)*159716];head=struct.unpack_from('<9I',record);need(head[:7]==(0,status[2],phase,item['slot'],item['entry'],status[3],status[4])and head[7]==0,'Exact complete actual chronological prefix metadata');before_cpu=struct.unpack_from('<10I',record,36);after_cpu=struct.unpack_from('<10I',record,76);need(before_cpu[4]==F and before_cpu[9]==item['entry']and after_cpu[4]==F+4 and after_cpu[9]==BROKER,'Every prefix actual Runtime CALL/RET frame');flags=struct.unpack_from('<10I',record,148548);need(flags[8]==1 and flags[9]==0,'Every successful prefix source State admitted');counts['whole_successful_prefix_records']+=1
   before_folder=folder/'Widget/input-before';after_folder=folder/'Widget/input-after';before,tib=memory(before_folder);after,tib_after=memory(after_folder);eq(tib,tib_after,'Fault injection preserves whole observed TIB');before_state=raw(before_folder/'State.bin');after_state=raw(after_folder/'State.bin');before_cpu=W(before_folder/'CPU.bin',10);after_cpu=W(after_folder/'CPU.bin',10);need(len(before_state)==len(after_state)==3504 and before_cpu[4]==F+4 and before_cpu[9]==BROKER,'Full carried machine before actual post-creation widget CALL');state=bytearray(before_state);cpu=list(before_cpu);ctx=list(Q(before_folder/'Context.bin',13));need(ctx[:7]==[1,1,0,135,0,status[3],0]and ctx[7:]==[0]*6,'Exact carried Context injection boundary without earlier failure');cause=W(folder/'cause.bin',9);need(cause[:4]==(1,mode,135,0x5a3ff0),'Exact source-authored current mutation identity');
   if mode==1:
    need(cause[4:]==(2184,4,struct.unpack_from('<I',state,2184)[0],4,0),'Exact full DS scalar mutation');struct.pack_into('<I',state,2184,4)
   elif mode==2:
    need(cause[4:]==(0,4,before_cpu[8],before_cpu[8]|0x400,0),'Exact DF CPU flag cause');state[2075]=1;struct.pack_into('<Q',state,2080,struct.unpack_from('<Q',state,2080)[0]|0x400);cpu[8]|=0x400
   elif mode in(3,4):
    address,width=(0x5bb52c,4)if mode==3 else(0x5a3ff0,1);old=int.from_bytes(payload(before,address,width),'little');new=0 if mode==3 else old^1;need(cause[4:8]==(address,width,old,new)and cause[8]in before and cause[8]<=address<cause[8]+len(before[cause[8]]),'Exact actual IAT/source byte injection');store(before,address,new.to_bytes(width,'little'))
   elif mode in(5,6,7):
    address=0x736130 if mode==5 else 0x20001000 if mode==6 else tib[0];need(cause[4:8]==(address,0,0,0)and cause[8]<=address,'Only declared current mapped permission cause; rights bytes not observed');
    if mode==5:need(cause[8]in before and cause[8]<=address<cause[8]+len(before[cause[8]]),'Exact second-object protected current Game region')
    else:eq(cause[8],address,'Exact protected stack/TIB region')
   else:need(cause[4:]==(0,4,0,1,0),'Exact current route override field');ctx[6]=1
   equal_memory(before,after,'Whole own carried input plus only exact fault mutation');eq(bytes(state),after_state,'Every State byte plus only declared scalar fault');eq(tuple(cpu),after_cpu,'Whole CPU plus only declared DF flag fault');eq(raw(before_folder/'FX.bin'),raw(after_folder/'FX.bin'),'Whole guest FX unchanged by fault injection');eq(tuple(ctx),Q(after_folder/'Context.bin',13),'Whole current Context input plus exact route selector fault');eq(raw(before_folder/'routes.bin'),raw(after_folder/'routes.bin'),'Complete real Runtime routes unchanged by injection')
   cb=component(folder,'input-before');ca=component(folder,'input-after');same_before=component(folder,'same-context-before');same_after=component(folder,'same-context-after');eq(cb.parent.name,'root-'+str(first[0]),'Actual successful first-root component retained before injection');eq(raw(cb/'State.bin'),before_state,'Whole component and Context input State same');eq(raw(ca/'State.bin'),after_state,'Whole component and Context authored State same');
   for n in inventory(cb):
    if n not in('State.bin','CPU.bin'):eq(raw(cb/n),raw(ca/n),'Whole component private input conserved by source-authored fault '+n)
   need(len(raw(ca/'APIs.bin'))==prefix_GDI_count*1488,'All149 actual current prefix GDI source calls retained');eq(raw(ca/'APIs.bin'),raw(same_before/'APIs.bin'),'No extra source native GDI API before required fault');eq(raw(ca/'fonts.bin'),raw(same_before/'fonts.bin'),'All current typed fonts conserved across required fault');font_rows=rows(raw(ca/'fonts.bin'),32,'<IIIIQBB6x');owned=[x for x in font_rows if x[5]and x[6]];need(len(owned)==15 and all(x[3]==first[0]and x[0]==0x72001000+16*x[1]for x in owned),'Fifteen actual current source-created owned fonts after full prefix');counts['actual_owned_font_prefixes']+=1
   private=Q(same_before/'status.bin',12);need(private[0]and private[1]==5 and private[5:7]==(1,0),'Actual component Context-fault mark prior to cleanup');eq(same_before.parent.name,'root-'+str(first[0]if mode==6 else second[0]),'Exact component entry timing versus failed Runtime CALL');whole_before=folder/'Widget/same-context-before';whole_after=folder/'Widget/same-context-after';faultctx=Q(whole_before/'Context.bin',13);need(faultctx[:6]==(1,1,1,135,0,status[3])and faultctx[6]==int(mode==8)and faultctx[7]==135 and faultctx[11]==status[14]and faultctx[12]==1 and faultctx[8]==status[13],'Entire Context firstfault/failed/poison structure');equal_folder(whole_before,whole_after,'Same actual Context whole observable retry');equal_folder(same_before,same_after,'Same actual component full private/machine retry');equal_folder(folder/'retry-before/Registry',folder/'retry-after/Registry','Same actual provider/resource full retry');counts['same_actual_Context_retry_relations']+=1
   routes=rows(raw(whole_before/'routes.bin'),20,'<5I');need(len(routes)==status[10]and routes[-1]==(BROKER,second[0],BROKER,0,0)and all(v[4]==1 for v in routes[:-1]),'Exactly real final incomplete required Runtime route and completed prefix');site=BROKER if mode==6 else second[0];reason=raw(folder/'refusal.txt').decode();eq(reason,f'memory_access site=0x{site:08x} target=0x{second[0]:08x}: Admitted native callback failed: {DETAIL[mode]}','Exact actual first source/Runtime refusal text');counts['exact_current_first_refusals']+=1
   start=rows(raw(ca/'accesses.bin'),24,'<IIQII');finish=rows(raw(same_before/'accesses.bin'),24,'<IIQII');eq(finish[:len(start)],start,'Full successful component operand prefix retained');suffix=finish[len(start):];need(len(start)==prefix_access_count and len(suffix)<=second[12],'Current exact root operand cursor extent');need(bool(suffix)if mode in(3,5,7)else not suffix,'Exact early/current-literal fault prefix distinction');faultmap={a:bytearray(v)for a,v in after.items()};
   if mode!=6:store(faultmap,F,struct.pack('<I',BROKER))
   denied=None
   for index,(pc,address,value,width,writing)in enumerate(suffix):
    need(pc in pcs and width in(1,2,4)and writing in(0,1),'Whole physically recovered source operand');expected=operands[second[11]+index];ep,role,off,ew,write=expected;ea=F+off if role==1 else tib[0]if role==2 else off;eq((pc,address,width,bool(writing)),(ep,ea,ew,write),'Every repeated exact source PC/address/frame role/width/direction');need(value<1<<(8*width),'Exact finite source payload width')
    if not writing:eq(value,int.from_bytes(payload(faultmap,address,width),'little'),'Every actual reached source read joins same own input byteflow')
    elif mode in(5,7)and index==len(suffix)-1:
     if mode==7:need(address==tib[0]and width==4,'Actual final denied source FS DWORD')
     else:need(cause[8]<=address and address+width<=cause[8]+len(faultmap[cause[8]]),'Actual final denied source object write in authored read-only region')
     denied=[pc,address,value,width]
    else:store(faultmap,address,value.to_bytes(width,'little'))
   if mode in(5,7):need(denied is not None,'Actual failed write logged but uncommitted')
   if mode==5:need(len(suffix)==16 and suffix[-1]==(0x59fba5,0x736130,0x5cfd10,4,1),'First complete literal object store row15 denied; no later source instruction')
   if mode==7:need(len(suffix)==6 and suffix[-1]==(0x5a459e,tib[0],F-16,4,1),'First complete literal FS install row5 denied; actual source frame value')
   if mode==3:need(len(suffix)==461,'Exact 460 prior source operands followed by first owning onexit IAT read')
   if mode==3:eq(suffix[-1],(0x5ac11e,0x5bb52c,0,4,0),'Actual changed source IAT operand before GDI target call')
   observed_fault,_=memory(whole_before);equal_memory(faultmap,observed_fault,'Every complete own fault memory byteflow');counts['exact_causal_source_operand_prefix_rows']+=len(suffix)
   cleaned=component(folder,'cleaned');cleanfonts=rows(raw(cleaned/'fonts.bin'),32,'<IIIIQBB6x');need(len(cleanfonts)==len(font_rows),'All typed font records retained through actual cleanup');
   for old,new in zip(font_rows,cleanfonts):eq(new,old[:6]+(0,)+old[7:]if old[5]and old[6]else old,'Exact only-owned current font live transition')
   status_clean=Q(cleaned/'status.bin',12);need(status_clean[5:7]==(1,1),'Current failed component marked cleaned');eq(raw(cleaned/'APIs.bin'),raw(ca/'APIs.bin'),'Cleanup does not invent source GDI calls');manual=[]
   for f in sorted(owned,key=lambda x:x[1],reverse=True):
    stem=folder/'Widget/manual-font-cleanup'/str(f[1]);row=raw(Path(str(stem)+'-row.bin'));w=struct.unpack('<8Q',row);eq(w[:5],f[:5],'Actual manual cleanup joins complete owned generation/instance/root/native identity');need(w[5]==private[0]and w[6]and w[7]==1,'Actual successful current-thread DeleteObject');manual.append((row,raw(Path(str(stem)+'-hardware.bin'))));counts['actual_owned_font_cleanup_calls']+=1
   eq({str(q.relative_to(folder)).replace('\\','/')for q in (folder/'Widget/manual-font-cleanup').glob('*')},{'Widget/manual-font-cleanup/'+str(f[1])+s for f in owned for s in('-row.bin','-hardware.bin')},'All and only fifteen current manual owned-font cleanups');gdi=GDI.verify(lambda n:raw(folder/n),pin,prefix='Widget/',source_records=raw(cleaned/'APIs.bin'),manual_records=manual,logical_names=manifest,expected_thread=private[0]);counts['actual_named_GDI_source_calls']+=gdi['actual_source_calls'];counts['whole_GDI_identity_sides']+=gdi['whole_identity_sides'];summary=Q(folder/'cleaned/Registry/registry-summary.bin',32);need(summary[:5]==(1,1,0,1,1)and summary[5]==Q(folder/'retry-before/Registry/registry-summary.bin',32)[5] and summary[10]==summary[11]==summary[15]==0,'Actual poisoned current registry native ownership/CS/heap cleanup');counts['actual_poisoned_Session_cleanup_relations']+=1
   for label in('invoke','retry','cleanup'):hardware(folder/(label+'-hardware.bin'),label)
   proofs.append(dict(level=level,mode=mode,case=CASES[(mode-1)%6],actual_reason=reason,actual_fault_context_words=faultctx,actual_cause_words=cause,actual_suffix_operands=suffix,last_denied_uncommitted_write=denied,actual_GDI_identity=gdi,hidden_Runtime_frames_or_permissions_equality=False))
  eq(seen,{(l,m)for l in('O0','O2')for m in range(1,9)},'All current actual eight by two controls');need(counts['whole_ASM_FX512_ENV28_restore_pairs']==48 and counts['actual_owned_font_cleanup_calls']==240 and counts['same_actual_Context_retry_relations']==16,'All full hardware/owned-lifetime/same-context obligations');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'actual-Context-causes.json';q.write_text(json.dumps(proofs,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable)
  for q,h in list(pins.items()):eq(sha(q),h,'All consumed physical/ordinary files unchanged at completion')
  d=dict(passed=passed,execution_sha256=execution_sha,preparation_sha256=PH,borrowed_service_preparation_sha256=SERVICE,counts=dict(counts),scope='Actual current Context post-creation widget refusal after 135 carried roots and fifteen owned fonts; complete observed private/machine retry, own-input memory byteflow and real provider/cleanup/hardware joins',partial_fault_register_prediction=False,hidden_Runtime_frames_or_permissions_bytes_observed=False,whole_prior131_semantic_source_equivalence_claimed=False,source_callbacks_executed=False,source_bootstrap_or_teardown_modeled=False,hardware_scope='Inside three actual ASM invoke/retry/cleanup boundaries; resource construction and outside diagnostics excluded',archive_reader_opened=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
