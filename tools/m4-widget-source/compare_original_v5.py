"""Literal five-widget normal prefixes from genuine BEFORE and typed GDI APIs.

No native output, object AFTER, API stack output, or expected callback result is
an input. API volatile CPU/FP responses are admitted only at their measured
source CALL with exact stdcall frames and complete input-memory joins.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={};READS=set();OPTIONAL=set()
def need(v,s):
    if not v:raise ValueError(s)
def audit(event,args):
    if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
    p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
    if not p.is_relative_to(R):return
    reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
    if reading:
        need(p.suffix.lower()!='.mwb','No archive or target reader in literal widget comparison')
        (READS if p.is_file()else OPTIONAL).add(str(p))
sys.addaudithook(audit)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Immutable physical input');PINS[str(p)]=v;return p
def raw(p,h=None):return pin(p,h).read_bytes()
def read(p,h=None):return json.loads(raw(p,h))
def load(p,name):
    s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def eq(a,b,label):
    need(a==b,label+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:12]))
def main(name):
    out=R/'reports/m4-widget-source'/name;need(not out.exists(),'Fresh additive literal output');out.mkdir();passed=False;counts=collections.Counter();results=[];API_inputs=[];memory_joins=[]
    try:
        exports=R/'reports/m4-widget-source/original-inputs-r1';export=read(exports/'report.json','e45e403b85ced5cc0a9d7b5737c661a9c91b1d1bfa58aa65bda43592b8cb1af8');need(export['passed']and export['all_reader_aliases_closed'],'Exact actual closed widget capture exports')
        validation_path=R/'reports/m4-widget-original/validation-r1/report.json';validation=read(validation_path,'2cf3792eeecce837f141dd7d1347c634ddd6e14e275189e5f56e1ed737ec996c');need(validation['passed'],'Actual genuine widget observations')
        execution=read(validation['execution_path'],validation['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);prepdir=Path(build['preparation']);prep=read(prepdir/'report.json',build['preparation_sha256']);contract=read(prepdir/'normal-contracts.json');whole=contract['whole_pages']
        index=read(exports/'logical-capture-export-index.json',export['files'][str((exports/'logical-capture-export-index.json').resolve())]);paths={v['logical_capture_name']:(v['export_path'],v['sha256'])for v in index}
        def capture(logical):return raw(*paths[logical])
        G=load(R/'tools/m4-widget-source/game_model.py','literal_widget_machine');program,callbacks=G.source_program();F=load(R/'tools/m4-formatting-source/flag_domain.py','widget_flag_definedness')
        boundaries=read(validation_path.parent/'actual-GDI-boundaries.json',validation['files'][str((validation_path.parent/'actual-GDI-boundaries.json').resolve())]);fsrows=read(validation_path.parent/'actual-source-FS-events.json',validation['files'][str((validation_path.parent/'actual-source-FS-events.json').resolve())]);endpoints=read(validation_path.parent/'actual-root-endpoints.json',validation['files'][str((validation_path.parent/'actual-root-endpoints.json').resolve())])
        identity=u(capture('widget/identity.bin'),0,15);targets=[identity[5*i+1]for i in range(3)];calls=(0x5a013c,0x5a063f,0x5a074b);slots=(0x5bb070,0x5bb074,0x5bb068);argc=(1,1,14)
        for phase,root in enumerate(G.contracts()['selected_roots']):
            stem=f'phase/0/{phase}/';record=capture(f'phase/0/{phase}.bin');cpu=u(record,36,10);need(root['entry']==cpu[9]and cpu[4]==0x20001800,'Actual current selected widget root BEFORE')
            memory={p:bytearray(raw(exports/'actual-inputs'/f'phase-{phase}'/'BEFORE'/f'{p}.bin'))for p in whole}
            for p in range(0x78000000,0x78040000,4096):
                data=capture(stem+f'CRT-before/{p}.bin');need(p not in memory or memory[p]==data,'Overlapping whole source/CRT BEFORE aliases exact');memory[p]=bytearray(data)
            registry=u(capture(stem+'registry-before-meta.bin'),0,4);backing=capture(stem+'registry-before-backing.bin');need(len(backing)==registry[2]and registry[1]-registry[0]==4*phase,'Actual current registry BEFORE capacity/order');memory[registry[0]]=bytearray(backing)
            facts=[v for v in boundaries if v['phase']==phase];fsfacts=[v for v in fsrows if v['phase']==phase];need(fsfacts and fsfacts[0]['words'][3]==0,'First actual current source FS instruction is a read')
            memory[0x7ffde000]=bytearray(struct.pack('<I',fsfacts[0]['words'][4]))
            state=bytearray(3504)
            for k,v in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu[:8]):struct.pack_into('<I',state,G.I.REG[k],v)
            for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):state[G.I.FLAGS[flag]]=(cpu[8]>>bit)&1
            struct.pack_into('<I',state,2472,cpu[9]);struct.pack_into('<I',state,G.I.BASE['fs'],0x7ffde000)
            imports={(pc,slot):dict(raw_value=u(memory[slot&~4095],slot&4095)[0],target=targets[i])for i,(pc,slot)in enumerate(zip(calls,slots))}
            boundary_index=[0];fs_index=[0];undefined={};env=[record[2164:2192]];phase_api=[];source_FS=[];snap_cache={};dead_stack=[]
            def snapshot(fact):
                key=fact['index']
                if key not in snap_cache:snap_cache[key]=raw(fact['raw_snapshot'],fact['raw_snapshot_sha256'])
                return snap_cache[key]
            def CPU(model,observed,label):eq(F.project(list(model.projected_cpu()),undefined),F.project(observed,undefined),label)
            def gdi_boundary(model,fact):
                CPU(model,fact['CPU'],'Full source-defined GDI CPU '+str((phase,fact['index'])))
                eq(model.fx.hex(),fact['FX512_hex'],'Whole literal carried GDI FX512');eq(env[0].hex(),fact['ENV28_hex'],'Whole carried GDI ENV28');eq(model.bytes(model.reg('esp'),64).hex(),fact['frame64_hex'],'Whole source-derived GDI frame64')
                s=snapshot(fact);modeled_stack=model.bytes(0x20001000,4096);actual_stack=s[4820+whole.index(0x20001000)*4096:4820+(whole.index(0x20001000)+1)*4096];eq(snapshot(facts[0])[724:4820],s[724:4820],'Whole separately captured source code page5A0000 carried across API observations; no model input');counts['whole_actual_API_separate_source_code_page_carries']+=1
                for i,(a,b)in enumerate(zip(modeled_stack,actual_stack)):
                    if a!=b:dead_stack.append(dict(boundary_index=fact['index'],address=0x20001000+i,source_value=a,actual_value=b,source_access_index=len(model.accesses),value_seeded=False))
                eq(model.bytes(0x7ffde000,4),struct.pack('<I',fact['header'][5]),'Actual same current source/API FS head')
                for j,p in enumerate(whole):
                    if p==0x20001000:continue
                    eq(model.bytes(p,4096),s[4820+j*4096:4820+(j+1)*4096],'Whole source-derived GDI nonstack page '+hex(p));counts['whole_GDI_nonstack_page_relations']+=1
                counts['whole_GDI_CPU_FX_ENV_frame_joins']+=1
                memory_joins.append(dict(phase=phase,index=fact['index'],source_access_index=len(model.accesses),source_CPU=list(model.projected_cpu()),undefined_flags=dict(undefined),complete_nonstack_pages=63,whole_frame64=True))
            def fs(model,event,data):
                if event not in('read-before','write-before')or data['domain']!='source'or data['address']!=0x7ffde000:return
                need(fs_index[0]<len(fsfacts),'No unobserved source FS operation');fact=fsfacts[fs_index[0]];w=fact['words'];writing=event=='write-before'
                need(data['pc']==w[2]and data['bytes']==4 and writing==(w[3]!=0),'Exact actual FS PC/width/direction');CPU_FS=list(model.projected_cpu());CPU_FS[9]=data['pc'];eq(F.project(CPU_FS,undefined),F.project(fact['CPU_before'],undefined),'Whole source-defined actual FS CPU '+str((phase,fs_index[0])));eq(model.fx.hex(),fact['FX_before_hex'],'Whole carried actual FS FX');eq(env[0].hex(),fact['ENV_before_hex'],'Whole carried actual FS ENV')
                eq(model.bytes(0x7ffde000,4),struct.pack('<I',w[4]),'Source-derived complete FS predecessor');need(data['value']==(w[5]if writing else w[4]),'Literal actual FS operand')
                if w[7]:eq(model.bytes(w[6],16).hex(),fact['record_before_hex'],'Whole actual source FS16 frame')
                if fs_index[0]==0:
                    prior=model.PCs[:-1];need(all(not any(o.get('segment')=='fs' for o in model.program[p]['decoded_operands'])for p in prior),'Literal no prior source FS operand before measured first FS input');counts['source_first_FS_no_prior_access_proofs']+=1
                source_FS.append(dict(index=fs_index[0],PC=w[2],writing=writing,head_before=w[4],head_after=w[5],source_access_index=len(model.accesses)));fs_index[0]+=1;counts['actual_literal_FS_PC_CPU_FX_ENV_frame_joins']+=1
            class Prefix(G.Machine):
                def read(self,address,size=4,domain='source',pc=None):
                    original_pc=self.word(2472)if pc is None else pc
                    if domain=='source'and size==4 and(address,original_pc)==(0x5bb52c,0x5ac11e):
                        value=G.I.Machine.read(self,address,size,domain,pc);need(value==0x78004a36,'Actual named register source import');self.import_projections.append((5,original_pc,address,value,value,0,0,0));return value
                    return super().read(address,size,domain,pc)
                def step(self):
                    nonlocal undefined
                    pc=self.cursor
                    if boundary_index[0]<len(facts)and pc==facts[boundary_index[0]]['CPU'][9]and facts[boundary_index[0]]['side']=='first-source-return':
                        gdi_boundary(self,facts[boundary_index[0]]);boundary_index[0]+=1
                    row=self.program.get(pc);need(row is not None,'Exact recovered widget source PC '+hex(pc));next_undefined=F.advance(self,row,undefined)
                    consumed={'je':('ZF',),'jne':('ZF',),'jl':('SF','OF'),'jge':('SF','OF'),'jle':('ZF','SF','OF'),'js':('SF',),'sbb':('CF',),'stosd':('DF',)}.get(row['mnemonic'],())
                    need(not set(consumed)&set(undefined),'Every reached widget conditional/carry/repeat flag source-defined')
                    if consumed:counts['defined_control_flag_uses']+=1
                    value=super().step();undefined=next_undefined;return value
            machine=Prefix(state,record[116:628],record[36:76],memory,program=program,callbacks=callbacks,hook=fs,widget_imports=imports)
            machine.call_stack.append((root['entry'],cpu[4],0x410a80,0,cpu[5],cpu[3],cpu[6],cpu[7],0));machine.begin_widget(root['entry'])
            def external(model,target):
                nonlocal undefined
                need(boundary_index[0]<len(facts),'No unmeasured external widget service '+hex(target));before=facts[boundary_index[0]];after=facts[boundary_index[0]+1];api=before['header'][3]//2;site=model.PCs[-1]
                need(before['side']=='entry'and after['side']=='first-source-return'and target==targets[api]and site==calls[api],'Exact measured named GDI CALL/order');gdi_boundary(model,before);boundary_index[0]+=1
                eq(list(u(model.bytes(model.reg('esp')+4,4*argc[api]),0,argc[api])),before['arguments'],'Entire literal actual GDI arguments');ac=after['CPU'];bc=before['CPU'];need(all(bc[i]==ac[i]for i in(3,5,6,7))and ac[4]==bc[4]+4*(argc[api]+1),'Actual stdcall nonvolatile/stack projection')
                model.api_return(site,argc[api],ac[0]);model.reg('ecx',ac[1]);model.reg('edx',ac[2])
                for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):model.flag(flag,(ac[8]>>bit)&1)
                model.fx=bytes.fromhex(after['FX512_hex']);env[0]=bytes.fromhex(after['ENV28_hex']);undefined={}
                phase_api.append(dict(API=before['API'],source_CALL_pc=site,target=target,entry_index=before['index'],source_frame=bc[4],arguments=before['arguments'],finite_volatile_EAX_ECX_EDX_EFLAGS=list(ac[i]for i in(0,1,2,8)),FX512_actual_API_response=after['FX512_hex'],ENV28_actual_API_response=after['ENV28_hex'],object_or_stack_bytes_seeded=False));counts['finite_typed_actual_GDI_responses']+=1
            machine.run(lambda m:m.cursor==0x78004a36,api=external)
            need(boundary_index[0]==len(facts)and fs_index[0]==len(fsfacts),'All actual GDI and FS observations exhausted at literal registration prefix')
            eq(machine.bytes(machine.reg('esp'),8),struct.pack('<2I',0x5ac124,root['registration']['callback']),'Literal registration CALL frame/callback')
            for p in whole:
                if p==0x20001000:continue
                eq(machine.bytes(p,4096),raw(exports/'actual-inputs'/f'phase-{phase}'/'AFTER'/f'{p}.bin'),'Whole actual nonstack source page from literal prefix '+hex(p));counts['whole_root_nonstack_page_relations']+=1
            for observation in dead_stack:
                subsequent=next(((i,a)for i,a in enumerate(machine.accesses[observation['source_access_index']:],observation['source_access_index'])if a[1]<=observation['address']<a[1]+a[3]),None)
                if subsequent:
                    i,a=subsequent;need(a[4],'Unmodeled original API stack byte cannot be consumed by later literal source before overwrite '+str((phase,observation,a)));observation['dominating_literal_store']=dict(index=i,PC=a[0],address=a[1],value=a[2],width=a[3])
                else:observation['never_subsequently_source_accessed']=True
                counts['unseeded_unused_API_stack_byte_relations']+=1
            machine.end_widget();results.append(dict(phase=phase,root=root['entry'],registration_callback=root['registration']['callback'],registration_frame=machine.reg('esp'),source_PCs=machine.PCs,source_accesses=machine.accesses,virtual_calls=machine.widget_virtual_calls,array_invocations=machine.widget_arrays,zero_string_clear=machine.widget_strings,GDI_import_reads=machine.widget_import_reads,API_inputs=phase_api,FS_joins=source_FS,source_callback_execution=False,unused_observed_API_stack_bytes=dead_stack));API_inputs.extend(phase_api);counts['literal_widget_registration_prefixes']+=1;counts['literal_virtual_calls']+=len(machine.widget_virtual_calls);counts['literal_array_invocations']+=len(machine.widget_arrays);counts['literal_array_callback_iterations']+=sum(len(a['iterations'])for a in machine.widget_arrays)
        need(counts['literal_widget_registration_prefixes']==5 and counts['finite_typed_actual_GDI_responses']==145 and counts['actual_literal_FS_PC_CPU_FX_ENV_frame_joins']==570,'Exact complete observed normal prefix extent');passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        for name_,value in(('source-derivations.json',results),('typed-GDI-inputs.json',API_inputs),('source-memory-boundary-joins.json',memory_joins)):
            p=out/name_;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
        pin(__file__);pin(sys.executable)
        for p in list(READS):pin(p)
        result=dict(passed=passed,scope='Literal five-widget normal registration prefixes from untouched actual root BEFORE, typed measured GDI volatile/FP responses, current registry BEFORE and flat segment evidence. Every source-derived array/virtual effect is joined to complete actual object pages and GDI snapshots; individual unobserved CALL PCs are not claimed as directly traced.',counts=dict(counts),actual_dependency_reads=len(READS),complete_successful_read_chain_pinned=READS<=set(PINS),failed_optional_read_paths=sorted(OPTIONAL),AFTER_machine_or_memory_seed=False,GDI_object_stack_output_seed=False,source_shutdown_executed=False,source_failure_unwind_admitted=False,whole_source_root_stack_compared=False,source_registration_provider_executed=False,every_virtual_CALL_PC_directly_observed=False,unused_API_stack_bytes_seeded=False,unused_API_stack_bytes_proven_unread_before_literal_overwrite=True,first_source_FS_input_bound_without_prior_FS_access=True,initializer_credit=0,archive_reader_opened=False,files=PINS)
        p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(p),sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
