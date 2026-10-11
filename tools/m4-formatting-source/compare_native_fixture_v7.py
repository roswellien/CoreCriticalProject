"""Persistent formatting3 source proof from bootstrap BEFORE and finite APIs."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PINS={};READS=set()
def audit(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
 if p.is_relative_to(ROOT)and p.is_file()and(isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)):READS.add(str(p))
sys.addaudithook(audit)
sys.path.insert(0,str(ROOT/'tools/m4-lockit-source'));sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_bridge as B
import bridge_v2 as B2
import capture as C
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000,0x5cd000,0x5e3000,0x5e9000)
ROOTS=(0x4df610,0x4e0710,0x4e0810)
def need(x,s):
 if not x:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve()
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest()
 need(h is None or d==h,'Exact physical source '+str(p));PINS[str(p)]=d;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def equal(a,b,s):
 if a!=b:
  delta=[(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:8]if isinstance(a,(bytes,list,tuple))and isinstance(b,(bytes,list,tuple))else(a,b)
  raise ValueError(s+' '+str(delta))
def projection(n,state):
 fx,env=n.proj(state);return fx[:6]+bytes(18)+fx[24:],env
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;need(not out.exists(),'Fresh source gate');out.mkdir(parents=True);passed=False;reader=None;counts=collections.Counter();results=[]
 try:
  receipt=read(ROOT/'reports/m4-formatting-native/fixture-execution-r4/report.json','55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0');need(receipt['passed'],'Both actual fixture levels succeeded')
  build=read(receipt['build_path'],receipt['build_sha256']);prep=read(receipt['native_preparation'],receipt['native_preparation_sha256']);fixture=read(build['preparation'],build['preparation_sha256'])
  model=read(ROOT/'reports/m4-formatting-source/persistent-model-r3/report.json','8a6f4968d524105ea04aeaa4c08a78ec2a259cf6b279ff719ddc0cabf05ad9cf');G=load('persistent_formatter_source',model['model']);pin(model['model'],model['model_sha256'])
  R=load('formatting_native_API',ROOT/'tools/m4-tree-source/responses125.py');R.EXPECTED_LOCKIT_CALLS=0;B.R=R
  D=load('formatting_native_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');J=load('formatting_native_projection',ROOT/'tools/m4-joint-startup27-review/observe.py');n,_,_,_=J.models();n.PAGES=list(PAGES)
  PE=load('formatting_native_PE',ROOT/'tools/analysis/pe.py')
  game=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes());cpraw=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes();cp=PE.PEImage(cpraw);crt=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
  rw=pin(prep['loaded_input_page'],prep['loaded_input_page_sha256']).read_bytes();iat=pin(prep['loaded_IAT_page'],prep['loaded_IAT_page_sha256']).read_bytes()
  def initial(page):
   if page==0x78145000:return rw
   if page==0x78146000:return iat
   if page==0x780c1000:return cpraw[0x1000:0x2000]
   if page==0x78115000:return cpraw[0x54c00:0x55c00]
   if page==0x5f498000:return pin(ROOT/'reports/m4-mfc-source/original-preparation-r1/mfc-raw-page.bin','751e6229f4c61085d8e23814a5079e40fa99d411bd0f50ceb010f56d753b2d67').read_bytes()
   if page==0x20000000:return bytes(4096)
   need(page!=0x20001000,'Bootstrap supplies genuine stack BEFORE');pe=crt if 0x78000000<=page<0x78040000 else cp if page==0x7810a000 else mfc if 0x5f400000<=page<0x5f500000 else game;b=bytearray(4096)
   for sec in pe.sections:
    lo=max(page,pe.image_base+sec['virtual_address']);hi=min(page+4096,pe.image_base+sec['virtual_address']+sec['raw_size'])
    if hi>lo:off=sec['raw_offset']+lo-pe.image_base-sec['virtual_address'];b[lo-page:hi-page]=pe.data[off:off+hi-lo]
   return bytes(b)
  imports={(0x4dea15,0x5bb5a8):0x780264a9,(0x4deab1,0x5bb664):0x780012b3,(0x4dead1,0x5bb658):0x78022b9a}
  raw_imports={key:int.from_bytes(initial(key[1]&~4095)[key[1]&4095:(key[1]&4095)+4],'little')for key in imports}
  static=out/'static';static.mkdir();material=B.material(static,pin);program,callbacks=G.source_program()
  contracts=read(ROOT/'reports/m4-formatting-source/normal-contracts-r1/normal-contracts.json','121d091142d4a72a84e26aeb8254724b8f3a6ebac1593dc8296eecc2160e18aa')
  for level in('O0','O2'):
   reader=D.DirectSet(receipt['workers'][level]['transport'],pin);stem='actual-cleaned/';index=C.checkpoints(reader,stem);before,facts,heap,pc,sp=C.bootstrap_inputs(reader,stem,index);before['memory']=dict(before['memory'])
   for page in fixture['current_pages']:
    if page not in before['memory']:before['memory'][page]=initial(page)
    if page in(0x7810a000,0x78145000,0x78146000):equal(before['memory'][page],initial(page),'Entire original loaded provider input')
   seen=[];fmt_calls=[];active_root=[0]
   class Observed(G.Machine):
    def read(self,address,size=4,domain='source',pc=None):
     original_pc=self.word(2472)if pc is None else pc;value=super().read(address,size,domain,pc)
     key=(original_pc,address)
     if domain=='source'and size==4 and key in imports:
      need(value==raw_imports[key],'Actual physical formatter owning IAT input');self.import_projections.append((10,original_pc,address,value,imports[key],0,0,0));return imports[key]
     return value
    def emit(self,event,**data):
     super().emit(event,**data)
     if event=='instruction-after'and data.get('row',{}).get('pc')in{a[0]for a in imports}:
      row=data['row'];argc={0x4dea15:2,0x4deab1:1,0x4dead1:4}[row['pc']];frame=self.reg('esp');fmt_calls.append(dict(root=active_root[0],PC=row['pc'],target=self.cursor,frame=frame,args=[int.from_bytes(self.bytes(frame+4+4*i,4),'little')for i in range(argc)],returned=False))
     if event=='instruction-after'and self.cursor in(0x4dea1b,0x4deab7,0x4dead7)and data.get('row',{}).get('mnemonic')=='ret':
      call=next(c for c in reversed(fmt_calls)if not c['returned']);call.update(returned=True,result=self.reg('eax'),returned_ESP=self.reg('esp'))
    def snapshot(self,name):
     if name=='registry-producer-before':need(self.cursor==0x5ac3ec and self.word(2472)==0x5ac3e2,'Literal producer stop projection');self.word(2472,self.cursor)
     super().snapshot(name)
     if name in index:
      actual=C.checkpoint(reader,index,name);equal(bytes(self.state),actual['state'],'Entire checkpoint State '+name);equal(B.cpu(self.state),actual['cpu'],'Entire checkpoint CPU '+name);equal(self.fx,actual['fx'],'Entire checkpoint FX '+name)
      for page,raw in actual['memory'].items():equal(self.bytes(page,len(raw)),raw,'Whole checkpoint page '+name+' '+hex(page))
      seen.append(name);counts['whole_provider_checkpoints']+=1
   resource=reader.words(stem+'lockit-resource.bin',8,'Q');need(reader.data(stem+'lockit-native-images.bin')==b'','No rooted Lockit calls in isolated formatter3')
   def associate(machine,responses):
    machine.snapshot('lockit-resource-association-before');responses.associate_lockit(machine,resource,[],rw[0x640:0x658]);machine.snapshot('lockit-resource-association-after')
   machine,responses=B2.bootstrap(before,facts,heap,material,Observed,program,callbacks,pc,sp,resource_association=associate)
   cpu=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001804,0x92837465,0x56473829,0xaabbccdd,0x202,0x410a80);n.statecpu(machine.state,cpu);machine.cursor=0x410a80;machine.cpu=struct.pack('<10I',*cpu);machine.fx=projection(n,machine.state)[0]
   records=reader.data('actual-root-records.bin');need(len(records)==3*159716,'Three exact Native records');expected_callbacks=[]
   for phase,entry in enumerate(ROOTS):
    active_root[0]=entry;access_start=len(machine.accesses);call_start=len(fmt_calls);alloc_start=len(responses.allocations);pc_start=len(machine.PCs);dispatch_start=len(machine.output_dispatches)
    G.begin_root(machine,entry);n.statecpu(machine.state,machine.projected_cpu());machine.cpu=B.cpu(machine.state);record=records[phase*159716:(phase+1)*159716]
    equal(bytes(machine.state),record[141540:145044],'Full3504B literal BEFORE State');equal(machine.cpu,record[36:76],'Full40B BEFORE CPU');fx,env=projection(n,machine.state);equal(fx,record[116:628],'FullFX BEFORE');equal(env,record[2164:2192],'WholeENV BEFORE')
    for page in fixture['current_pages']:
     actual=record[2276+PAGES.index(page)*4096:2276+(PAGES.index(page)+1)*4096]if page==0x20001000 else reader.data(f'actual-before-root-{phase}/current-page-{page}.bin');equal(machine.bytes(page,4096),actual,'Whole carried BEFORE page '+hex(page));counts['whole_BEFORE_pages']+=1
    G.complete_root(machine,api=responses);machine.cpu=B.cpu(machine.state);machine.fx=projection(n,machine.state)[0]
    equal(bytes(machine.state),record[145044:148548],'Full3504B literal AFTER State');equal(machine.cpu,record[76:116],'Whole40B AFTER CPU');fx,env=projection(n,machine.state);equal(fx,record[628:1140],'WholeFX AFTER');equal(env,record[2192:2220],'WholeENV AFTER')
    for page in fixture['current_pages']:equal(machine.bytes(page,4096),reader.data(f'actual-after-root-{phase}/current-page-{page}.bin'),'Whole4096B AFTER page '+hex(page));counts['whole_AFTER_pages']+=1
    actual_accesses=list(struct.iter_unpack('<IIQII',reader.data(f'actual-after-root-{phase}/locale-source-accesses.bin')));equal([tuple(r)for r in machine.accesses],actual_accesses,'Entire persistent bootstrap and formatter source access ledger');counts['whole_source_access_records']+=len(actual_accesses)
    owner_new=responses.allocations[alloc_start:];need(len(owner_new)==1,'One actual finite new HeapAlloc per formatter');owner=owner_new[0];generation=owner['generation'];need(owner['requested']==(8,10,12)[phase]and owner['extent']==16 and generation>0,'Actual source malloc requested/capacity/generation');actual_owners=list(struct.iter_unpack('<16Q',reader.data(f'actual-after-root-{phase}/locale-allocations.bin')));matching=[r for r in actual_owners if r[1]==owner['guest']and r[5]==generation];need(len(matching)==1 and matching[0][2:4]==(owner['requested'],owner['extent'])and matching[0][6]==1 and matching[0][8]==owner['native'],'Genuine actual generic native owner kind and physical backing identity')
    source_bytes=machine.bytes(owner['guest'],16);equal(source_bytes,reader.data(f'actual-after-root-{phase}/native-full-{generation}.bin'),'Whole actual native16B owner including untouched tail');equal(source_bytes[owner['requested']:],owner['initial'][owner['requested']:],'Every untouched capacity tail byte remains genuine acquired input');counts['whole_native_owner_backings']+=1
    own_ops=[r for r in machine.accesses[access_start:]if owner['guest']<=r[1]and r[1]+r[3]<=owner['guest']+owner['extent']and r[0]not in(0x78001990,)]
    expected_callbacks.append((0x4df680,0x4e07b0,0x4e0850)[phase]);responses.completed_registry(machine,expected_callbacks)
    result=dict(level=level,phase=phase,root=entry,source_PCs=machine.PCs[pc_start:],source_accesses=machine.accesses[access_start:],calls=fmt_calls[call_start:],dispatches=machine.output_dispatches[dispatch_start:],owner=owner|dict(initial=owner['initial'].hex(),source_final_hex=source_bytes.hex()),owned_accesses=own_ops,API_index=responses.index,checkpoints=seen)
    results.append(result);counts['strict_native_phases']+=1
   responses.lockit_complete();need(len(fmt_calls)==9 and all(c['returned']for c in fmt_calls),'Nine exact source cdecl CALL/RET lifetimes');counts['literal_cdecl_CALL_RET']+=len(fmt_calls)
   need(len(machine.output_dispatches)==12 and [d['index']for d in machine.output_dispatches]==[1,7,1,7]*3,'Twelve literal normal source table dispatches');counts['literal_table_dispatches']+=12
   n.statecpu(machine.state,machine.projected_cpu());machine.cpu=B.cpu(machine.state)
   producer=responses.allocations[0];oldsp=machine.reg('esp');oldpc=machine.word(2472)
   machine.write(oldsp-4,producer['guest'],domain='research',pc=oldpc);machine.reg('esp',oldsp-4);machine.invoke_external(0x78001390,0xffffff80,responses);machine.reg('esp',oldsp);machine.cpu=B.cpu(machine.state)
   need(not producer['live'],'Literal producer free retires genuine acquired mapping');counts['literal_producer_source_frees']+=1
   for guest,section in reversed(list(responses.sections.items())):
    fact=responses.facts[responses.index];w=tuple(fact['words'])
    need(fact['name']=='DeleteCriticalSection'and w[:8]==(1,responses.index,0,0x7802e040,0x3446a,0,0,0)and w[8]==1 and w[9]==w[11]and w[14:17]==(1,1,section['native'])and w[31]==1 and not fact['inputs']and not fact['outputs'],'Actual reverse-order same native CS cleanup lifecycle witness')
    need(section['initialized']and section['depth']==0 and not section['deletes'],'Live unheld source resource at genuine cleanup');section['deletes']=1;responses.index+=1;counts['actual_native_CS_deletes']+=1
   for owner in reversed(responses.allocations[1:]):
    fact=responses.facts[responses.index];w=tuple(fact['words'])
    need(fact['name']=='HeapFree'and w[:8]==(1,responses.index,0,0x7802e090,0x345ba,0,0,0)and w[8]==1 and w[9]==w[11]and w[14:17]==(1,1,owner['native'])and w[31]==1 and not fact['inputs']and not fact['outputs'],'Actual reverse-order native formatter cleanup frees same acquired pointer')
    need(owner['live']and owner['extent']==16 and len(machine.memory[owner['guest']])==owner['mapped'],'Source live acquired owner alias remains present until real cleanup');owner['live']=False;machine.memory.pop(owner['guest']);responses.index+=1;counts['actual_native_formatter_cleanup_frees']+=1
   responses.complete();equal(bytes(machine.state),reader.data('sample.bin')[4272:7776],'Whole3504B actual outside-return postcleanup State derived by literal producer free');equal(machine.cpu,reader.data('sample.bin')[8840:8880],'Whole40B outside-return postcleanup CPU from literal source')
   actual_accesses=list(struct.iter_unpack('<IIQII',reader.data('actual-cleaned/locale-source-accesses.bin')));equal([tuple(r)for r in machine.accesses],actual_accesses,'Entire complete source ledger including literal producer cleanup')
   counts['whole_cleaned_source_access_records']+=len(actual_accesses);counts['complete_actual_lifecycles']+=1
   for name,phase in machine.bootstrap_prefix['phases'].items():
    if name in index and name not in seen:
     actual=C.checkpoint(reader,index,name);equal(phase['state'],actual['state'],'Whole literal heap-prefix checkpoint State '+name);equal(phase['cpu'],actual['cpu'],'Whole literal heap-prefix checkpoint CPU '+name);equal(phase['fx'],actual['fx'],'Whole literal heap-prefix checkpoint FX '+name)
     for page,raw in actual['memory'].items():
      matches=[(p,b)for p,b in phase['memory'].items()if p<=page and page+len(raw)<=p+len(b)];need(len(matches)==1,'One original heap-prefix BEFORE-backed memory interval');p,b=matches[0];equal(bytes(b[page-p:page-p+len(raw)]),raw,'Whole literal heap-prefix checkpoint page '+name+' '+hex(page))
     seen.append(name);counts['whole_heap_prefix_checkpoints']+=1
   need(set(index)-set(seen)=={'registry-bootstrap-before'},'Every captured provider checkpoint predicted from bootstrap BEFORE '+str(sorted(set(index)-set(seen))))
   reader.close();reader.entries.clear();reader.bundles.clear();reader=None
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear()
  (out/'source-derivations.json').write_text(json.dumps(results,indent=2)+'\n');pin(out/'source-derivations.json');pin(__file__)
  for p in list(READS):pin(p)
  need(READS<=set(PINS),'Every consumed physical input pinned')
  report=dict(passed=passed,scope='Actual native O0/O2 persistent formatter3 source comparison from bootstrap BEFORE and bounded measured API responses',counts=dict(counts),candidate_AFTER_machine_seed=False,root_BEFORE_machine_seed=False,native_whole_stack_compared=True,reader_closed=True,initializer_credit=0,actual_dependency_reads=len(READS),files=PINS)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
