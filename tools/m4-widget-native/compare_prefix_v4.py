"""Pure six-widget source prefix from the current native branch's own BEFORE.

Only actual GDI scalar/typed-handle responses are transported at their literal
CALL. The source registry provider and complete post-provider epilogue remain
separate obligations. No original handle, output value, stack or State is read.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={};READS=set();OPTIONAL=set()
def need(v,m):
 if not v:raise ValueError(m)
def audit(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
 if not p.is_relative_to(R):return
 if isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3):
  need(p.suffix.lower()not in('.mwb','.zip'),'No canonical/archive reader in current widget source comparison')
  (READS if p.is_file()else OPTIONAL).add(str(p))
sys.addaudithook(audit)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Unchanged actual source input');PINS[str(p)]=v;return p
def raw(p,h=None):return pin(p,h).read_bytes()
def read(p,h=None):return json.loads(raw(p,h))
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,n,o=0):return struct.unpack_from('<'+'I'*n,b,o)
def eq(a,b,label):
 if a!=b:
  differences=[(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:12]
  raise ValueError(label+' '+str(differences))
def rows(b,size,fmt):
 need(len(b)%size==0,'Whole typed private rows');return [struct.unpack_from(fmt,b,o)for o in range(0,len(b),size)]
def region_memory(folder):
 memory={}
 for f in sorted(folder.glob('game-region-*.bin')):
  address=int(f.stem.removeprefix('game-region-'));b=raw(f);need(b and len(b)%4096==0,'Whole mapped game region');memory[address]=bytearray(b)
 memory[0x20001000]=bytearray(raw(folder/'stack.bin'));need(len(memory[0x20001000])==4096,'Whole own BEFORE stack')
 tib=words(raw(folder/'TIB.bin'),5);need(tib[0]and tib[2:4]==(0x20002000,0x20001000)and tib[4]==tib[0],'Actual minimal TIB identity/stack fields')
 for offset,value in ((0,tib[1]),(4,tib[2]),(8,tib[3]),(24,tib[4])):memory[tib[0]+offset]=bytearray(struct.pack('<I',value))
 return memory,tib
def checkpoint_index(folder):
 result=[]
 for f in folder.glob('registry-checkpoint-*-name.bin'):
  n=int(f.stem.split('-')[2]);result.append((n,raw(f).decode()))
 return sorted(result)
def main(execution,execution_sha,name):
 out=R/'reports/m4-widget-native'/name;need(not out.exists(),'Fresh current own-BEFORE source receipt');out.mkdir();passed=False;counts=collections.Counter();derivations=[]
 try:
  e=read(execution,execution_sha);need(e['passed']and e['all_workers_terminal'],'Actual closed exact widget execution');bh='036d33c85494a29c358a4d7e2016606bbdb9290316be52ac2ae32b07f96a3d98';ph='58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401';need(e['build_sha256']==bh and e['preparation_sha256']==ph,'Exact current linked build/preparation');read(R/'reports/m4-widget-native/fixture-build-r13/build.json',bh);prep=read(R/'reports/m4-widget-native/fixture-preparation-r16/report.json',ph)
  c=read(R/'reports/m4-widget-native/preparation-r3/contracts.json');roots=c['roots'];G=load(R/'reports/m4-font479590-original/source-preparation-r1/game_model.py','widget_current_literal_model');F=load(R/'tools/m4-formatting-source/flag_domain.py','widget_current_defined_flags');program,callbacks=G.source_program();sites=(0x5a013c,0x5a063f,0x5a074b);slots=(0x5bb070,0x5bb074,0x5bb068);targets=(0x71f00010,0x71f00020,0x71f00030)
  for level in('O0','O2'):
   run=e['runs'][level];folder=Path(run['capture']);manifest=read(run['output_manifest'],run['output_manifest_sha256'])
   for logical,v in manifest.items():pin(folder/logical,v['sha256'])
   checkpoints=checkpoint_index(folder/'cleanup');service_before=[n for n,label in checkpoints if label=='widget-onexit-before'];need(len(service_before)==6,'Six actual borrowed-provider entry checkpoints');prefix=folder/'cleanup';access_start=api_start=virtual_start=FS_start=array_start=0
   for phase,root in enumerate(roots):
    root_pc=root['root'];phase_dir=folder/f'phase-{phase}';component=phase_dir/f'root-{root_pc}';before_dir=component/'before';after_dir=component/'after';state=raw(before_dir/'State.bin');fx=raw(before_dir/'FX.bin');cpu=raw(before_dir/'CPU.bin');need(len(state)==3504 and len(fx)==512 and len(cpu)==40,'Complete actual owned component entry machine');CPU=words(cpu,10);status=struct.unpack('<12Q',raw(before_dir/'status.bin'));frame=status[3];need(status[1]==phase and status[2]==root_pc and status[4:7]==(1,0,0)and CPU[4]==frame and CPU[9]==root_pc,'Exact current registered component route entry')
    memory,tib=region_memory(phase_dir/'before');stack=memory[0x20001000];need(0x20001000<=frame<=0x20002000-4,'Actual current root CALL frame');stack[frame-0x20001000:frame-0x20001000+4]=struct.pack('<I',0xfffffff0)
    # The Runtime writes precisely its external return token before the callback.
    need(words(raw(phase_dir/'before'/'CPU.bin'),10)[4]==frame+4,'Actual outer caller to committed Runtime CALL geometry')
    imports={(pc,slot):dict(raw_value=words(bytes(memory[next(a for a,b in memory.items()if a<=slot<slot+4<=a+len(b))]),1,slot-next(a for a,b in memory.items()if a<=slot<slot+4<=a+len(b)))[0],target=target)for pc,slot,target in zip(sites,slots,targets)}
    cumulative_apis=raw(after_dir/'APIs.bin');need(len(cumulative_apis)%1488==0,'Whole actual ApiRecord layout');api_records=[]
    for o in range(api_start*1488,len(cumulative_apis),1488):
     b=cumulative_apis[o:o+1488];w=struct.unpack_from('<16Q',b);need(w[0]==1 and w[1]==root_pc and w[3]<3,'Actual API owner/current selected root');api_records.append(dict(words=w,before=words(b,10,128),after=words(b,10,168),args=words(b,14,208),frame=b[264:328],hardware=b[336:1488]))
    boundary_index=[0];undefined={};FS=[];FP=fx
    class Prefix(G.Machine):
     def read(self,address,size=4,domain='source',pc=None):
      source_pc=self.word(2472)if pc is None else pc
      if domain=='source'and(source_pc,address,size)==(0x5ac11e,0x5bb52c,4):
       value=G.I.Machine.read(self,address,size,domain,pc);need(value==0x1decb0,'Own raw named onexit source import');self.import_projections.append((5,source_pc,address,value,0x78004a36,0,0,0));return 0x78004a36
      return super().read(address,size,domain,pc)
     def step(self):
      nonlocal undefined
      row=self.program.get(self.cursor);need(row is not None,'Recovered literal widget source PC');next_undefined=F.advance(self,row,undefined);consumed={'je':('ZF',),'jne':('ZF',),'jl':('SF','OF'),'jge':('SF','OF'),'jle':('ZF','SF','OF'),'js':('SF',),'sbb':('CF',),'stosd':('DF',)}.get(row['mnemonic'],());need(not set(consumed)&set(undefined),'No undefined flag consumed by current widget path');counts['defined_flag_uses']+=bool(consumed);value=super().step();undefined=next_undefined;return value
    def hook(m,event,data):
     if event not in('read-before','write-before')or data['domain']!='source'or data['address']!=tib[0]:return
     FS.append((root_pc,data['pc'],int(event=='write-before'),int.from_bytes(m.bytes(tib[0],4),'little'),data['value']))
    m=Prefix(state,fx,cpu,memory,program=program,callbacks=callbacks,hook=hook,widget_imports=imports);m.call_stack.append((root_pc,frame,0xfffffff0,0,CPU[5],CPU[3],CPU[6],CPU[7],0));m.begin_widget(root_pc)
    def external(model,target):
     nonlocal undefined
     need(boundary_index[0]<len(api_records),'No unobserved native GDI response');a=api_records[boundary_index[0]];w=a['words'];index=w[3];site=model.PCs[-1];need(target==targets[index]and site==sites[index]and(w[2],w[4],w[5],w[6])==(site,boundary_index[0],model.reg('esp'),int.from_bytes(model.bytes(model.reg('esp'),4),'little')),'Source-derived API site/order/frame/return');eq(F.project(model.projected_cpu(),undefined),F.project(a['before'],undefined),'Whole defined API entry CPU');eq(model.bytes(model.reg('esp'),64),a['frame'],'Whole literal API frame64');args=words(model.bytes(model.reg('esp')+4,4*w[7]),w[7]);eq(args,a['args'][:w[7]],'Complete literal API argument DWORDs');hardware=a['hardware'];actual=struct.unpack_from('<4Q',hardware,576);need(a['after'][0]==w[9]and actual[0]==w[10]and a['after'][1]==actual[1]&0xffffffff and a['after'][2]==actual[2]&0xffffffff,'Typed handle/scalar EAX and actual native ECX/EDX projection');model.api_return(site,w[7],w[9]);model.reg('ecx',actual[1]);model.reg('edx',actual[2]);
     for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('OF',11)):model.flag(flag,(actual[3]>>bit)&1)
     undefined={};eq(tuple(model.projected_cpu()),a['after'],'Whole source CPU after explicit typed native GDI response');eq(model.fx,FP,'Whole guest FP carried without native hardware transport');counts['actual_GDI_scalar_response_joins']+=1;counts['whole_API_frame64_joins']+=1;boundary_index[0]+=1
    m.run(lambda x:x.cursor==0x78004a36,api=external);need(boundary_index[0]==len(api_records),'All actual current GDI responses exhausted at registration entry');n=service_before[phase];observed_state=raw(prefix/f'registry-checkpoint-{n}-state.bin');observed_cpu=words(raw(prefix/f'registry-checkpoint-{n}-cpu.bin'),10)
    eq(F.project(m.projected_cpu(),undefined),F.project(observed_cpu,undefined),'Whole defined borrowed-service entry CPU');eq(bytes(m.state),observed_state,'Whole independently derived State3504 at provider entry');eq(m.fx,raw(prefix/f'registry-checkpoint-{n}-fx.bin'),'Whole source-derived provider entry FX512');eq(m.bytes(0x20001000,4096),raw(prefix/f'registry-checkpoint-{n}-page-{0x20001000}.bin'),'Entire native current source stack from own BEFORE and literal writes')
    accesses=rows(raw(after_dir/'accesses.bin'),24,'<IIQII');current_accesses=accesses[access_start:];expected=[tuple(v)for v in m.accesses];eq(current_accesses[:len(expected)],expected,'Every current native source prefix PC/address/value/width/direction');need(len(current_accesses)==len(expected)+3,'Exactly three separately reviewed literal tail RET accesses');counts['exact_prefix_operand_rows']+=len(expected)
    native_FS=rows(raw(after_dir/'FS-events.bin'),32,'<8I')[FS_start:];need(len(native_FS)==len(FS),'Complete current source FS order');eq([v[:5]for v in native_FS],FS,'Actual current FS operand chronology');counts['FS_source_relations']+=len(FS)
    native_virtual=rows(raw(after_dir/'virtuals.bin'),32,'<8I')[virtual_start:];derived=[(v['root'],v['PC'],v['instance'],v['source_store']['PC'],v['source_store']['value'],v['slot'],v['target'],v['source_access_index']+access_start)for v in m.widget_virtual_calls];eq(native_virtual,derived,'Full current-instance vptr/slot/value/call provenance');counts['virtual_source_relations']+=len(derived)
    native_arrays=rows(raw(after_dir/'arrays.bin'),32,'<8I')[array_start:];derived=[]
    for a in m.widget_arrays:
     for iteration in a['iterations']:derived.append((root_pc,a['caller'],a['frame'],a['base'],iteration['iteration'],iteration['instance'],iteration['target'],iteration['ESP']-4))
    eq(native_arrays,derived,'Whole current vector invocation/frame/ordered element callback');counts['array_source_relations']+=len(derived)
    for f in sorted((phase_dir/'after').glob('game-region-*.bin')):
     address=int(f.stem.removeprefix('game-region-'));b=raw(f);eq(m.bytes(address,len(b)),b,'Whole mapped game memory from source prefix');counts['whole_game_region_relations']+=1;counts['whole_game_bytes_compared']+=len(b)
    derivations.append(dict(level=level,phase=phase,root=root_pc,source_PCs=m.PCs,source_accesses=m.accesses,source_virtual_calls=m.widget_virtual_calls,source_array_invocations=m.widget_arrays,source_FS=FS,source_entry_State_sha256=hashlib.sha256(state).hexdigest(),computed_provider_entry_State_sha256=hashlib.sha256(bytes(m.state)).hexdigest(),provider_checkpoint=n,original_output_input=False,registration_provider_executed_by_model=False));counts['literal_prefixes']+=1;counts['whole_State3504_entry_joins']+=1;counts['whole_stack4096_relations']+=1;api_start=len(cumulative_apis)//1488;access_start=len(accesses);virtual_start+=len(native_virtual);FS_start+=len(native_FS);array_start+=len(native_arrays)
  need(counts['literal_prefixes']==12 and counts['actual_GDI_scalar_response_joins']==294 and counts['exact_prefix_operand_rows']==49250 and counts['FS_source_relations']==1158 and counts['virtual_source_relations']==1010 and counts['array_source_relations']==150,'Exact both-level current six-root finite prefix extent');passed=True
 except BaseException:
  passed=False;(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'source-derivations.json';q.write_text(json.dumps(derivations,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable)
  for q in list(READS):pin(q)
  report=dict(passed=passed,scope='Actual current native widget prefixes derived from their own component entry State and current memory BEFORE plus only literal measured GDI scalar/typed-handle responses; source registration provider and post-provider machine remain separate',execution_sha256=execution_sha,counts=dict(counts),actual_successful_read_dependencies=len(READS),successful_read_chain_physically_pinned=READS<=set(PINS),optional_missing_reads=sorted(OPTIONAL),AFTER_State_or_memory_seed=False,original_numeric_or_handle_seed=False,whole_registration_provider_source_model=False,post_provider_whole_machine_equality=False,connected_initializer_credit=0,archive_reader_opened=False,files=PINS);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=passed,counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
