"""Literal five-widget normal prefixes from genuine BEFORE and typed GDI APIs.

No native output, object AFTER, API stack output, or expected callback result is
an input. API volatile CPU/FP responses are admitted only at their measured
source CALL with exact stdcall frames and complete input-memory joins.
"""
from pathlib import Path
import bisect,collections,hashlib,importlib.util,json,struct,sys,traceback
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
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.mwi')and p.name not in('transport.json','manifest.json','bundle.json'),'No canonical capture input');v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Immutable physical input');PINS[str(p)]=v;return p
def raw(p,h=None):return pin(p,h).read_bytes()
def read(p,h=None):return json.loads(raw(p,h))
def load(p,name):
    s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def eq(a,b,label):
    need(a==b,label+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:12]))
def main(name):
    out=R/'reports/m4-startup138-original'/name;need(not out.exists(),'Fresh additive literal output');out.mkdir();passed=False;counts=collections.Counter();results=[];API_inputs=[];memory_joins=[];FPS_joins=[];reader=None;source_fonts=[];source_stock={};cleanup_rows=[]
    try:
        exports=R/'reports/m4-startup138-original/original-validation-r2';validation_path=exports/'report.json';validation=read(validation_path,'74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181');need(validation['passed']and validation['reader_closed']and validation['paired_export_readers_closed']and validation['counts']['phases']==828 and validation['callbacks']==108 and validation['combined_pages']==69,'Exact complete closed original138 observations')
        execution=read(Path(validation['execution_path'])/'report.json',validation['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);prepdir=Path(build['preparation']);prep=read(prepdir/'report.json',build['preparation_sha256']);contract=read(prep['contracts'])
        import re
        compiled=raw(prepdir/'spec.hpp').decode();match=re.search(r'std::array<unsigned,69> widget_whole_pages\{([^}]+)\};',compiled);need(match is not None,'Exact compiled original69 snapshot page order');whole=[int(v.strip(),16)for v in match[1].split(',')];need(whole[:43]==prep['observed_pages']and len(set(whole))==69 and set(whole[43:])==set(prep['extra_whole_source_pages']),'Complete physical source69 snapshot inventory')
        E=load(R/'tools/m4-startup131-original/export_reader.py','current138_original_raw_export');reader=E.ExportReader(validation_path,'74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181','original',pin)
        def capture(logical):return reader.data(logical)
        def actual_pages(record,stem,side):
            offset=2276 if side=='before'else 178404
            return {p:record[offset+i*4096:offset+(i+1)*4096]if i<43 else capture(stem+f'extra-{side}/{p}.bin')for i,p in enumerate(whole)}
        def sealed(name):return read(exports/name,validation['files'][str((exports/name).resolve())])
        source_prep=read(R/'reports/m4-fps-original/source-preparation-r4/report.json');need(source_prep['passed'],'Finite newroot source adapter');G=load(R/'reports/m4-fps-original/source-preparation-r4/game_model.py','literal_widget_machine');program,callbacks=G.source_program();provider=read(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d');need(provider['schema']=='mw34-onexit-independent-provider-source-v1'and not provider['AFTER_machine_seed'],'Exact accepted registrar source contract');provider_callbacks=read(R/'reports/m4-onexit-review/callbacks-r1/callbacks.json','3c0a5fab10ec834c8e027ed88a8443b7d63d559c151d40ade6a045a71ce1565d');
        for row in provider['instructions']:
            need(row['pc']not in program or program[row['pc']]==row,'Identical inherited registrar row');program[row['pc']]=row
        for pc,offsets in provider_callbacks['State_offsets_by_original_PC'].items():
            pc=int(pc);offsets=tuple(offsets);need(pc not in callbacks or callbacks[pc]==offsets,'Exact registrar undefined callbacks');callbacks[pc]=offsets
        F=load(R/'tools/m4-formatting-source/flag_domain.py','widget_flag_definedness')
        FPS=sealed('FPS-observations.json');fps_identity=u(capture('fps/identity.bin'),0,4)
        boundaries=sealed('widget-GDI-observations.json');fsrows=sealed('widget-FS-observations.json');endpoints=sealed('widget-root-observations.json');lifetimes=sealed('font-resource-lifetimes.json')
        need(len(endpoints)==42 and len(boundaries)==validation['counts']['widget_complete_GDI_boundary_sides']and len(fsrows)==validation['counts']['widget_actual_FS_instruction_events'],'Complete current metadata extents')
        for fact in boundaries:fact['side']='entry'if fact['side']==0 else'first-source-return'
        for fact in fsrows:fact.update(words=fact['header'],FX_before_hex=fact['FX_hex'],ENV_before_hex=fact['ENV28_hex'],record_before_hex=fact['frame16_hex'])
        for fact in FPS:fact.update(format_input16_hex=fact['format16_hex'],va_input64_hex=fact['va64_hex'])
        provider_targets=u(capture('crt-api-targets.bin'),0,8);provider_sites={(0x78001091,0x7802e044):(5,1),(0x780015b5,0x7802e1dc):(2,3),(0x780012ab,0x7802e048):(6,1)}
        identity=u(capture('widget/identity.bin'),0,15);targets=[identity[5*i+1]for i in range(3)];calls=(0x5a013c,0x5a063f,0x5a074b);slots=(0x5bb070,0x5bb074,0x5bb068);argc=(1,1,14)
        roots={r['entry']:r for r in G.contracts()['selected_roots']};schedule=((15,0x40e250),(16,0x40ef50),(17,0x40f000),(47,0x479590),(134,0x5a3c30),(135,0x5a3ff0),(136,0x5a66f0));need(set(roots)=={r for _,r in schedule},'Exact seven literal roots');need(all(contract['selected_order'][p]['entry']==r for p,r in schedule),'Exact current chronological widget phases')
        for seq,phase,root in [(s,p,roots[r])for s in range(6)for p,r in schedule]:
            stem=f'phase/{seq}/{phase}/';record=capture(f'phase/{seq}/{phase}.bin');cpu=u(record,36,10);need(root['entry']==cpu[9]and cpu[4]==0x20001800,'Actual current selected widget root BEFORE')
            memory={p:bytearray(b)for p,b in actual_pages(record,stem,'before').items()};need(all(len(b)==4096 for b in memory.values()),'Whole own actual69 BEFORE inputs')
            for p in range(0x78000000,0x78040000,4096):
                data=capture(stem+f'CRT-before/{p}.bin');need(p not in memory or memory[p]==data,'Overlapping whole source/CRT BEFORE aliases exact');memory[p]=bytearray(data)
            registry=u(capture(stem+'registry-before-meta.bin'),0,4);backing=capture(stem+'registry-before-backing.bin');need(len(backing)==registry[2]and registry[0]<=registry[1]<=registry[0]+registry[2]and u(memory[0x78037000],0x888)[0]==registry[1]and u(memory[0x78037000],0x88c)[0]==registry[0],'Actual current registry BEFORE capacity/order');memory[registry[0]]=bytearray(backing)
            facts=[v for v in boundaries if v['sequence']==seq and v['phase']==phase];fsfacts=[v for v in fsrows if v['sequence']==seq and v['phase']==phase];need(fsfacts and fsfacts[0]['words'][3]==0,'First actual current source FS instruction is a read')
            memory[0x7ffde000]=bytearray(struct.pack('<I',fsfacts[0]['words'][4]))
            state=bytearray(3504)
            for k,v in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu[:8]):struct.pack_into('<I',state,G.I.REG[k],v)
            for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):state[G.I.FLAGS[flag]]=(cpu[8]>>bit)&1
            struct.pack_into('<I',state,2472,cpu[9]);struct.pack_into('<I',state,G.I.BASE['fs'],0x7ffde000)
            imports={(pc,slot):dict(raw_value=u(memory[slot&~4095],slot&4095)[0],target=targets[i])for i,(pc,slot)in enumerate(zip(calls,slots))}
            fpsfacts=[v for v in FPS if v['sequence']==seq and v['phase']==phase];fps_index=[0];imports[(0x5a2f68,0x5bb53c)]=dict(raw_value=u(memory[0x5bb000],0x53c)[0],target=fps_identity[1])
            provider_ledger=capture(stem+'api-ledger.bin');provider_count=u(capture(stem+'api-count.bin'))[0];need(len(provider_ledger)==104*provider_count,'Whole current original26DWORD API ledger');provider_index=[0];provider_joins=[]
            boundary_index=[0];fs_index=[0];undefined={};env=[record[2164:2192]];phase_api=[];source_FS=[];snap_cache={};dead_stack=[]
            def snapshot(fact):
                key=fact['index']
                if key not in snap_cache:
                    blob=capture(stem+'widget-snapshots.bin');need(len(blob)==len(facts)*287444,'Whole original GDI69 snapshot blob');snap_cache[key]=blob[key*287444:(key+1)*287444];need(hashlib.sha256(snap_cache[key]).hexdigest()==fact['raw_sha256'],'Current individually sealed GDI snapshot identity')
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
                memory_joins.append(dict(phase=phase,index=fact['index'],source_access_index=len(model.accesses),source_CPU=list(model.projected_cpu()),undefined_flags=dict(undefined),complete_nonstack_pages=68,whole_frame64=True))
            def fps_boundary(model,fact):
                CPU(model,fact['CPU'],'Literal full FPS CPU '+str((phase,fact['index'])))
                eq(model.fx.hex(),fact['FX512_hex'],'Whole literal FPS FX512');eq(env[0].hex(),fact['ENV28_hex'],'Whole literal FPS ENV28');eq(model.bytes(model.reg('esp'),64).hex(),fact['frame64_hex'],'Whole source-derived true FPS cdecl frame64')
                eq(model.bytes(0x7ffde000,4),struct.pack('<I',fact['header'][5]),'Literal carried FPS hidden FS head')
                blob=capture(stem+'fps-snapshots.bin');need(len(blob)==len(fpsfacts)*550180,'Whole original FPS snapshot blob');s=blob[fact['index']*550180:(fact['index']+1)*550180];need(hashlib.sha256(s).hexdigest()==fact['raw_sha256'],'Current individually sealed FPS snapshot identity');stack=model.bytes(0x20001000,4096);actual_stack=s[4820+whole.index(0x20001000)*4096:4820+(whole.index(0x20001000)+1)*4096]
                for i,(a,b)in enumerate(zip(stack,actual_stack)):
                    if a!=b:dead_stack.append(dict(boundary_role='FPS',boundary_index=fact['index'],address=0x20001000+i,source_value=a,actual_value=b,source_access_index=len(model.accesses),value_seeded=False))
                for j,p in enumerate(whole):
                    if p==0x20001000:continue
                    eq(model.bytes(p,4096),s[4820+j*4096:4820+(j+1)*4096],'Whole literal FPS source page '+hex(p));counts['literal_FPS_whole_nonstack_pages']+=1
                for j,p in enumerate(range(0x78000000,0x78040000,4096)):
                    eq(model.bytes(p,4096),s[287444+j*4096:287444+(j+1)*4096],'Whole literal FPS CRT page '+hex(p));counts['literal_FPS_whole_CRT_pages']+=1
                destination,format_,va=fact['header'][13:16]
                eq(model.bytes(destination,512).hex(),fact['destination512_hex'],'Complete literal FPS destination512');eq(model.bytes(format_,16).hex(),fact['format_input16_hex'],'Complete source FPS format16');eq(model.bytes(va,64).hex(),fact['va_input64_hex'],'Complete literal FPS real va_list64')
                if fact['index']:
                    counts['literal_FPS_provider_instructions']=sum(0x78000000<=p<0x78040000 for p in model.PCs)
                    eq(s[724:4820],blob[:550180][724:4820],'Whole separately observed FPS5A2000 page carried; not a model seed')
                join=dict(phase=phase,index=fact['index'],source_access_index=len(model.accesses),source_CPU=list(model.projected_cpu()),undefined_flags=dict(undefined),complete_source_nonstack_pages=68,complete_CRT_pages=64,whole_frame64=True,whole_destination512=True,whole_format16=True,whole_va64=True,provider_CPU_or_output_seed=False)
                FPS_joins.append(join);counts['literal_FPS_CPU_FX_ENV_frame_joins']+=1
            def fs(model,event,data):
                if event not in('read-before','write-before')or data['domain']!='source'or data['address']!=0x7ffde000:return
                if 0x78000000<=data['pc']<0x78040000:
                    counts['literal_provider_uninstrumented_FS_operations']+=1;return
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
                    if domain=='source'and size==4 and(original_pc,address)in provider_sites:
                        kind,n=provider_sites[(original_pc,address)];value=G.I.Machine.read(self,address,size,domain,pc);self.import_projections.append((7,original_pc,address,value,provider_targets[kind],0,0,0));return provider_targets[kind]
                    if domain=='source'and size==4 and(address,original_pc)==(0x5bb52c,0x5ac11e):
                        value=G.I.Machine.read(self,address,size,domain,pc);need(value==0x78004a36,'Actual named register source import');self.import_projections.append((5,original_pc,address,value,value,0,0,0));return value
                    return super().read(address,size,domain,pc)
                def step(self):
                    nonlocal undefined
                    pc=self.cursor
                    if fps_index[0]<len(fpsfacts)and pc==fpsfacts[fps_index[0]]['CPU'][9]:fps_boundary(self,fpsfacts[fps_index[0]]);fps_index[0]+=1
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
                if target in provider_targets:
                    need(provider_index[0]<provider_count,'No unmeasured original provider API');w=u(provider_ledger,104*provider_index[0],26);kind=w[24];site=model.PCs[-1];need(kind in(2,5,6)and target==provider_targets[kind],'Finite warm registrar APIs only; allocation/growth requires independent owned witnesses');n=3 if kind==2 else 1
                    need((site,{2:0x7802e1dc,5:0x7802e044,6:0x7802e048}[kind])in provider_sites,'Exact contracted registrar IAT CALL');CPU(model,list(w[:10]),'Whole actual source-defined provider API BEFORE CPU');eq(list(u(model.bytes(model.reg('esp')+4,4*n),0,n)),list(w[20:20+n]),'Whole source-derived provider API arguments');need(model.read(model.reg('esp'),domain='api')==w[25],'Actual provider source return frame');need(all(w[i]==w[10+i]for i in(3,5,6,7))and w[14]==w[4]+4*(n+1),'Original API stdcall nonvolatile/stack relation')
                    if kind==2:need(w[20]==u(model.bytes(0x78035000,4))[0]and w[21]==0 and w[22]==registry[0]and w[10]==registry[2],'Own current registry bounded HeapSize witness')
                    model.api_return(site,n,w[10]);model.reg('ecx',w[11]);model.reg('edx',w[12])
                    for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):model.flag(flag,(w[18]>>bit)&1)
                    undefined={};CPU(model,list(w[10:20]),'Whole current original provider API first return CPU');provider_joins.append(dict(kind=kind,site=site,args=list(w[20:20+n]),return_word=w[25],memory_output_seed=False));provider_index[0]+=1;counts['literal_provider_API_joins']+=1;return
                need(boundary_index[0]<len(facts),'No unmeasured external widget service '+hex(target));before=facts[boundary_index[0]];after=facts[boundary_index[0]+1];api=before['header'][3]//2;site=model.PCs[-1]
                need(before['side']=='entry'and after['side']=='first-source-return'and target==targets[api]and site==calls[api],'Exact measured named GDI CALL/order');gdi_boundary(model,before);boundary_index[0]+=1
                eq(list(u(model.bytes(model.reg('esp')+4,4*argc[api]),0,argc[api])),before['arguments'],'Entire literal actual GDI arguments');ac=after['CPU'];bc=before['CPU'];need(all(bc[i]==ac[i]for i in(3,5,6,7))and ac[4]==bc[4]+4*(argc[api]+1),'Actual stdcall nonvolatile/stack projection')
                model.api_return(site,argc[api],ac[0]);model.reg('ecx',ac[1]);model.reg('edx',ac[2])
                for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):model.flag(flag,(ac[8]>>bit)&1)
                eq(before['FX512_hex'],after['FX512_hex'],'Entire actual GDI FX512 conserved; no FP output transport');eq(before['ENV28_hex'],after['ENV28_hex'],'Entire actual GDI ENV28 conserved; no environment output transport');counts['actual_GDI_whole_FP_conservation_relations']+=1;undefined={}
                phase_api.append(dict(API=before['API'],source_CALL_pc=site,target=target,entry_index=before['index'],source_frame=bc[4],arguments=before['arguments'],finite_volatile_EAX_ECX_EDX_EFLAGS=list(ac[i]for i in(0,1,2,8)),FX512_actual_API_response=after['FX512_hex'],ENV28_actual_API_response=after['ENV28_hex'],object_or_stack_bytes_seeded=False));counts['finite_typed_actual_GDI_responses']+=1
            machine.run(lambda m:m.cursor==0x78004a36,api=external)
            need(boundary_index[0]==len(facts)and fs_index[0]==len(fsfacts)and fps_index[0]==len(fpsfacts),'All actual GDI and FS observations exhausted at literal registration prefix')
            eq(machine.bytes(machine.reg('esp'),8),struct.pack('<2I',0x5ac124,root['registration']['callback']),'Literal registration CALL frame/callback')
            machine.run(lambda m:m.cursor==0x410a80,api=external);need(provider_index[0]==provider_count,'Every original registrar API consumed');CPU(machine,list(u(record,76,10)),'Whole literal root source-defined AFTER CPU');eq(machine.fx,record[628:1140],'Whole carried root AFTER FX512');eq(env[0],record[2192:2220],'Whole carried root AFTER ENV28');eq(machine.bytes(0x7ffde000,4),struct.pack('<I',fsfacts[0]['words'][4]),'Source widget/provider FS restored to own root BEFORE')
            actual_registry=u(record,356464,4);need(actual_registry==(registry[0],registry[1]+4,registry[2],registry[3]),'Actual warm one-callback registry endpoint');eq(machine.bytes(registry[0],registry[2]),record[356480:356480+registry[2]],'Whole source-derived own registry backing AFTER');need(u(machine.bytes(registry[1],4))[0]==root['registration']['callback'],'Own literal ordered callback appended')
            for p in range(0x78000000,0x78040000,4096):
                eq(machine.bytes(p,4096),capture(stem+f'CRT-after/{p}.bin'),'Whole source-derived registrar CRT AFTER '+hex(p));counts['whole_root_CRT_page_relations']+=1
            counts['literal_complete_registrar_root_endpoints']+=1
            for p in whole:
                if p==0x20001000:continue
                eq(machine.bytes(p,4096),actual_pages(record,stem,'after')[p],'Whole actual nonstack source page from literal prefix '+hex(p));counts['whole_root_nonstack_page_relations']+=1
            by_stack_byte=collections.defaultdict(list)
            for i,a in enumerate(machine.accesses):
                for address in range(max(0x20001000,a[1]),min(0x20002000,a[1]+a[3])):by_stack_byte[address].append(i)
            for observation in dead_stack:
                indexes=by_stack_byte[observation['address']];position=bisect.bisect_left(indexes,observation['source_access_index']);subsequent=(indexes[position],machine.accesses[indexes[position]])if position<len(indexes)else None
                if subsequent:
                    i,a=subsequent;need(a[4],'Unmodeled original API stack byte cannot be consumed by later literal source before overwrite '+str((phase,observation,a)));observation['dominating_literal_store']=dict(index=i,PC=a[0],address=a[1],value=a[2],width=a[3])
                else:observation['never_subsequently_source_accessed']=True
                counts['unseeded_unused_API_stack_byte_relations']+=1
            machine.end_widget();results.append(dict(sequence=seq,phase=phase,root=root['entry'],registration_callback=root['registration']['callback'],registration_frame=machine.reg('esp'),source_PCs=machine.PCs,source_accesses=machine.accesses,virtual_calls=machine.widget_virtual_calls,array_invocations=machine.widget_arrays,zero_string_clear=machine.widget_strings,GDI_import_reads=machine.widget_import_reads,API_inputs=phase_api,FS_joins=source_FS,source_callback_execution=False,provider_API_joins=provider_joins,FPS_joins=fpsfacts,provider_dispatches=machine.output_dispatches,unused_observed_API_stack_bytes=dead_stack));API_inputs.extend(phase_api);counts['literal_widget_registration_prefixes']+=1;counts['literal_virtual_calls']+=len(machine.widget_virtual_calls);counts['literal_array_invocations']+=len(machine.widget_arrays);counts['literal_array_callback_iterations']+=sum(len(a['iterations'])for a in machine.widget_arrays)
        need(counts['literal_widget_registration_prefixes']==42 and counts['literal_FPS_CPU_FX_ENV_frame_joins']==12 and counts['literal_FPS_provider_instructions']>0 and counts['finite_typed_actual_GDI_responses']==validation['counts']['widget_actual_stdcall_RETURN_relations'] and counts['actual_literal_FS_PC_CPU_FX_ENV_frame_joins']==validation['counts']['widget_actual_FS_instruction_events'],'Exact complete observed normal prefix extent');passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if reader is not None:reader.close()
        for name_,value in(('literal-FPS-joins.json',FPS_joins),('source-derivations.json',results),('typed-GDI-inputs.json',API_inputs),('source-memory-boundary-joins.json',memory_joins)):
            p=out/name_;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
        pin(__file__);pin(R/'tools/m4-fps-original/prepare_source_v4.py');pin(R/'tools/m4-fps-original/derive_source_v4.py');pin(R/'tools/m4-fps-original/prepare_source_v3.py');pin(R/'tools/m4-fps-original/derive_source_v3.py');pin(R/'tools/m4-fps-original/prepare_source_v2.py');pin(R/'tools/m4-fps-original/derive_source_v2.py');pin(R/'tools/m4-fps-original/fps_source_join.inc');pin(R/'tools/m4-font479590-original/prepare_source.py');pin(R/'tools/m4-font479590-original/compare_source.py');pin(R/'tools/m4-widget-source/compare_original_v6.py','e9e79d55d25f219ce8469de71cb05fcaecf3b04768881b669feefbe5273759ce');pin(R/'tools/m4-widget-source/compare_original_v5.py');pin(sys.executable)
        for p in list(READS):pin(p)
        result=dict(passed=passed,scope='Current138 six-sequence literal seven-root widget/font/fps registration prefixes including complete finite vsprintf source from untouched actual root BEFORE, typed measured GDI volatile/FP responses, current registry BEFORE and flat segment evidence. Every source-derived array/virtual effect is joined to complete actual object pages and GDI snapshots; individual unobserved CALL PCs are not claimed as directly traced.',counts=dict(counts),actual_dependency_reads=len(READS),complete_successful_read_chain_pinned=READS<=set(PINS),failed_optional_read_paths=sorted(OPTIONAL),AFTER_machine_or_memory_seed=False,GDI_object_stack_output_seed=False,source_shutdown_executed=False,source_failure_unwind_admitted=False,whole_source_root_stack_compared=False,source_registration_provider_executed=True,every_virtual_CALL_PC_directly_observed=False,GDI_FP_output_seed=False,unused_API_stack_bytes_seeded=False,unused_API_stack_bytes_proven_unread_before_literal_overwrite=True,first_source_FS_input_bound_without_prior_FS_access=True,initializer_credit=0,archive_reader_opened=False,ordinary_raw_export_closed=reader is None or reader.closed,complete_current_widget_gate=False,registration_provider69_endpoint_frontier=not passed,files=PINS)
        p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(p),sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
