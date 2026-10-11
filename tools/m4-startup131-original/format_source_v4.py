"""Independent literal constructor/provider trace from genuine whole BEFORE.

Only actual Win32 allocation/volatile response inputs enter untraced APIs. No
output buffer, provider stack or original AFTER machine seeds the model.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={};AUDITED_READS=set();FAILED_OPTIONAL_READS=set()
def audit_workspace_read(event,args):
    if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
    path=Path(args[0]).resolve()
    if not path.is_relative_to(R):return
    mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
    reading=isinstance(mode,str)and'r'in mode or(mode is None and isinstance(flags,int)and not(flags&3))
    if not reading:return
    if path.suffix.lower()=='.mwb':need(False,'No archive may be opened by the current raw-export source gate')
    if path.is_file():AUDITED_READS.add(str(path))
    else:FAILED_OPTIONAL_READS.add(str(path))
sys.addaudithook(audit_workspace_read)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical source identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,n):
    s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def eq(a,b,label):
    need(a==b,label+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:12]))
def main(name,shared_reader):
    out=R/'reports/m4-startup131-original'/name;need(not out.exists(),'Fresh additive source/trace comparison');out.mkdir(parents=True)
    bundle=None;passed=False;counts=collections.Counter();results=[];joins=[];api_inputs=[]
    try:
        validation=read(R/'reports/m4-startup131-original/validation-r2/report.json','9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f');need(validation['passed'],'Fresh original131 structural evidence')
        boundaries=[dict(x,cpu=x['CPU'])for x in read(R/'reports/m4-startup131-original/validation-r2/fresh-cdecl.json',validation['files'][str((R/'reports/m4-startup131-original/validation-r2/fresh-cdecl.json').resolve())])]
        owner_rows=read(R/'reports/m4-startup131-original/validation-r2/fresh-format_owners.json',validation['files'][str((R/'reports/m4-startup131-original/validation-r2/fresh-format_owners.json').resolve())])
        owners=[dict(x,pointer=x['meta'][5],request=x['meta'][4],capacity=x['meta'][6],API_index=x['meta'][7])for x in owner_rows]
        execution=read(Path(validation['execution_path'])/'report.json',validation['execution_sha256']);build=read(validation['build_path'],validation['build_sha256']);pin(build['worker'],build['worker_sha256']);preparation=read(Path(validation['preparation_path'])/'report.json',validation['preparation_sha256'])
        M=load(R/'tools/m4-formatting-source/provider_model.py','literal_formatter_machine');F=load(R/'tools/m4-formatting-source/flag_domain.py','original_architectural_flag_domain');rec=read(M.REC/'report.json',M.REC_SHA)
        for p,h in rec['files'].items():pin(p,h)
        # Reuse the admitted physical full allocator rows, not a host malloc.
        allocator=read(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d')
        frontier=read(R/'reports/m4-mixed-format-original/recovery-r1/report.json','5627b4234b16f5bdb493f4102f541166cbf8bde11c53c3b9a691a24d1230e5fa');game_path=R/'reports/m4-mixed-format-original/recovery-r1/instruction-contracts.json';game=read(game_path,frontier['files'][str(game_path.resolve())]);roots=read(R/'reports/m4-formatting-source/normal-contracts-r1/normal-contracts.json')['roots']+game['roots'];format_contracts=read(R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json');G=load(R/'tools/m4-lockit-source/game_model.py','retained_literal_MFC_Lockit');program,callbacks=G.source_program();provider_program,_=M.source_program();
        for pc,row in provider_program.items():need(pc not in program or program[pc]==row,'Exact shared literal provider instruction');program[pc]=row
        for row in allocator['instructions']+game['instructions']+format_contracts['instructions']:
            if row['pc']>=0x78000000 and row['pc']in provider_program:continue
            pc=row['pc'];need(pc not in program or program[pc]==row,'Identical retained physical source row');program[pc]=row
        D=load(R/'tools/m4-crt-allocation-root/run_v2.py','small_formatter_capture');bundle=shared_reader;need(Path(bundle.path).resolve()==Path(execution['original_capture']).resolve(),'One authenticated current-original131 session')
        named_targets=u(bundle.data('formatting/import-targets.bin'),0,3);eq(named_targets,(0x780264a9,0x780012b3,0x78022b9a),'Actual named loaded provider targets')
        instruction_PCs={row['pc']for row in rec and json.loads(Path(rec['instructions']).read_bytes())['instructions']}
        source_imports={(0x4dea15,0x5bb5a8):0x780264a9,(0x4deab1,0x5bb664):0x780012b3,(0x4dead1,0x5bb658):0x78022b9a}
        cp_targets={slot:target for slot,target,*tail in struct.iter_unpack('<5I',bundle.data('lockit/import-ledger.bin'))}
        source_imports.update({(0x7810a30b,0x78146198):cp_targets[0x78146198],(0x7810a35e,0x78146184):cp_targets[0x78146184]})
        full_mixed_owners=read(R/'reports/m4-startup131-original/validation-r2/fresh-mixed_owners.json',validation['files'][str((R/'reports/m4-startup131-original/validation-r2/fresh-mixed_owners.json').resolve())])
        full_CP=read(R/'reports/m4-startup131-original/validation-r2/fresh-mixed_CP.json',validation['files'][str((R/'reports/m4-startup131-original/validation-r2/fresh-mixed_CP.json').resolve())])
        for sequence in range(6):
         for root in roots:
            phase=next(i for i,x in enumerate(preparation['selected_order'])if x['entry']==root['entry'])
            phase_boundaries=[x for x in boundaries if x['sequence']==sequence and x['root']==root['entry']];need(len(phase_boundaries)==6,'Exactly current cdecl boundaries')
            selected_owners=[x for x in owners if x['sequence']==sequence and x['root']==root['entry']];need(len(selected_owners)==1,'Exactly current formatter owner');owner=selected_owners[0]
            mixed_owners=[]
            for x in full_mixed_owners:
             if x['sequence']!=sequence or root['entry']!=0x4e1ca0:continue
             m=x['meta'];mixed_owners.append(dict(x,pointer=m[7],source_request=m[4],capacity=m[8],API_index=m[6],CALL_pc=m[3]))
            cp_events=[x for x in full_CP if x['sequence']==sequence and root['entry']==0x4e1ca0]
            fs_raw=bundle.data(f'phase/{sequence}/{phase}/fs-events.bin');fs_events=[]
            for offset in range(0,len(fs_raw),1216):
             b=fs_raw[offset:offset+1216];h=list(u(b,0,8));fs_events.append(dict(PC=h[2],kind=h[3],header=h,CPU_before=list(u(b,32,10)),record_before_hex=b[112:124].hex(),FX_before_hex=b[136:648].hex(),ENV_before_hex=b[1160:1188].hex()))
            raw=bundle.data(f'phase/{sequence}/{phase}.bin');need(len(raw)==356992,'Frozen complete original phase geometry')
            memory={p:bytearray(raw[2276+i*4096:2276+(i+1)*4096])for i,p in enumerate(preparation['observed_pages'])}
            for page in preparation['extra_whole_source_pages']:memory[page]=bytearray(bundle.data(f'phase/{sequence}/{phase}/extra-before/{page}.bin'))
            meta=list(struct.iter_unpack('<3I',bundle.data(f'phase/{sequence}/{phase}/CRT-image/metadata.bin')))
            for page,protect,type_ in meta:
                need(0x78000000<=page<0x78040000 and page%4096==0 and not(protect&0x101)and type_==0x1000000,'Complete actual loaded source CRT page')
                memory[page]=bytearray(bundle.data(f'phase/{sequence}/{phase}/CRT-image/before/{page}.bin'))
            cpu=u(raw,36,10);state=bytearray(3504)
            for reg,value in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu[:8]):struct.pack_into('<I',state,M.I.REG[reg],value)
            for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):state[M.I.FLAGS[flag]]=(cpu[8]>>bit)&1
            struct.pack_into('<I',state,2472,cpu[9]);struct.pack_into('<I',state,M.I.BASE['fs'],0x7ffde000)
            first_head=phase_boundaries[0]['header'][5];root_head=fs_events[0]['header'][4]if fs_events else first_head
            memory[0x7ffde000]=bytearray(struct.pack('<I',root_head))
            FS_input=dict(kind='genuine_first_game_FS_read'if fs_events else'genuine_first_strrchr_entry_FS_scalar_unchanged_until_entry',actual_value=root_head,first_entry_observed_value=first_head,original_snapshot_header_index=5,original_after_memory_seed=False)
            literal=[];imports=[];api=[];boundary_index=[0];cp_index=[0];fs_index=[0];boundary_PCs={0x780264a9:0,0x4dea1b:1,0x780012b3:2,0x4deab7:3,0x78022b9a:4,0x4dead7:5}
            owner_inputs={owner['API_index']:dict(pointer=owner['pointer'],request=owner['request'],capacity=owner['capacity'],API_index=owner['API_index'],initial_hex=owner['initial_hex'],final_hex=owner['final_hex'],CALL_pc=0x4deab1)}
            for o in mixed_owners:need(o['API_index']not in owner_inputs,'Unique genuine four API allocation occurrences');owner_inputs[o['API_index']]=dict(o,request=o['source_request'])
            retained_owners={}
            def source_FS(model,address,value,size,source_pc,writing):
                if address!=0x7ffde000 or source_pc>=0x78000000:return
                need(fs_index[0]<len(fs_events),'Finite six actual FS instructions');fact=fs_events[fs_index[0]];h=fact['header'];need(source_pc==fact['PC']and size==4 and writing==(fact['kind']!=0),'Actual FS source PC/read/write relation '+str((hex(source_pc),hex(fact['PC']),writing,fact['kind'],model.PCs[-10:])));need(model.reg('esp')==fact['CPU_before'][4]and int.from_bytes(model.bytes(address,4),'little')==h[4]and value==(h[5]if writing else h[4]),'Literal complete source FS predecessor/address/value')
                if h[7]:eq(model.bytes(h[6],12).hex(),fact['record_before_hex'],'All twelve FS source bytes from untouched BEFORE and literal prior writes')
                fs_index[0]+=1;counts['literal_actual_complete_FS_joins']+=1
            def source_CP(model,index):
                need(cp_index[0]==index,'Exact genuine six CP boundaries');fact=cp_events[index];eq(list(model.projected_cpu()),fact['CPU'],'Whole literal CP boundary CPU40');eq(model.fx.hex(),fact['FX512_hex'],'Whole carried CP FX512');eq(raw[2164:2192].hex(),fact['ENV28_hex'],'Whole source ENV28 conserved through integer literal prefix');eq(model.bytes(model.reg('esp'),32).hex(),fact['frame32_hex'],'All32 CP source stack frame bytes');eq(model.bytes(0x78145640,24).hex(),fact['CS24_hex'],'Whole carried source CS24');cp_index[0]+=1;counts['literal_actual_CP_CPU_FX_ENV_frame_CS_joins']+=1
            class Prefix(M.Machine):
                def read(self,address,size=4,domain='source',pc=None):
                    source_pc=self.word(2472)if pc is None else pc;value=super().read(address,size,domain,pc)
                    target=source_imports.get((source_pc,address))if domain=='source'and size==4 else None
                    if target is not None:
                        need(0x18000000<=value<0x19000000,'Actual original observer IAT cell has declared worker owner')
                        imports.append(dict(PC=source_pc,IAT=address,actual_shim=value,named_source_target=target,source_access_index=len(self.accesses)-1));return target
                    source_FS(self,address,value,size,source_pc,False);return value
                def write(self,address,value,size=4,domain='source',pc=None):
                    source_pc=self.word(2472)if pc is None else pc;source_FS(self,address,value,size,source_pc,True);return super().write(address,value,size,domain,pc)
                def step(self):
                    pc=self.cursor
                    if pc in(0x7810a290,0x7810a311,0x7810a350,0x7810a364):source_CP(self,{0x7810a290:0,0x7810a311:2,0x7810a350:3,0x7810a364:5}[pc])
                    if pc in boundary_PCs and (pc!=0x780012b3 or int.from_bytes(self.bytes(self.reg('esp'),4),'little')==0x4deab7):
                        actual=phase_boundaries[boundary_index[0]];need(actual['kind']==boundary_PCs[pc],'Exact actual cdecl boundary order')
                        eq(list(self.projected_cpu()),actual['cpu'],'Full actual source-derived cdecl CPU '+str((phase,actual['kind'])))
                        eq(self.fx.hex(),actual['FX512_hex'],'Complete carried source FX')
                        if boundary_index[0]==0 and not fs_events:
                            need(not any(r[1]==0x7ffde000 for r in self.accesses),'The genuine first entry FS scalar is unchanged throughout the literal root prefix');FS_input['literal_no_FS_access_before_first_entry']=True;FS_input['source_PCs_before_observation']=list(self.PCs)
                        need(u(self.bytes(0x7ffde000,4))[0]==actual['header'][5],'Actual compiled observer FS head matches literal entry/return head');counts['actual_cdecl_FS_head_joins']+=1
                        eq(self.bytes(self.reg('esp'),32).hex(),actual['frame32_hex'],'Entire cdecl frame32 from root BEFORE/source writes')
                        eq(raw[2164:2192].hex(),actual['ENV28_hex'],'Entire carried source ENV at cdecl boundary')
                        if actual['owned_hex']:eq(self.bytes(owner['pointer'],owner['capacity']).hex(),actual['owned_hex'],'Entire actual capacity at source API boundary')
                        boundary_index[0]+=1;counts['whole_cdecl_CPU_FX_frame_capacity_joins']+=1
                    before=dict(getattr(self,'undefined_flag_domain',{}));after=F.advance(self,self.program[pc],before)
                    consumed={'je':('ZF',),'jne':('ZF',),'ja':('CF','ZF'),'jae':('CF',),'jb':('CF',),'jbe':('CF','ZF'),'jg':('ZF','SF','OF'),'jge':('SF','OF'),'jl':('SF','OF'),'jle':('ZF','SF','OF'),'js':('SF',),'jns':('SF',),'jo':('OF',),'jno':('OF',),'adc':('CF',),'sbb':('CF',),'scasb':('DF',)}.get(self.program[pc]['mnemonic'],())
                    need(not set(consumed)&set(before),'No undefined source control input');result=super().step();self.undefined_flag_domain=after;return result
            machine=Prefix(state,raw[116:628],raw[36:76],memory,program=program,callbacks=callbacks)
            machine.call_stack.append((root['entry'],cpu[4],0x410a80,0,cpu[5],cpu[3],cpu[6],cpu[7],0))
            API=list(struct.iter_unpack('<26I',bundle.data(f'phase/{sequence}/{phase}/api-ledger.bin')))
            def finite_API(model,target):
                site=model.PCs[-1]
                if site in(0x7810a30b,0x7810a35e):
                    index=1 if site==0x7810a30b else 4
                    need(target==cp_targets[0x78146198 if index==1 else 0x78146184],'Exact owning real Enter/Leave target');source_CP(model,index);before,returned=cp_events[index],cp_events[index+1];bc,ac=before['CPU'],returned['CPU'];need(ac[3]==bc[3]and ac[5:8]==bc[5:8]and ac[4]==bc[4]+8 and ac[9]==(0x7810a311 if index==1 else 0x7810a364),'Actual source API consumes only its genuine pointer/return frame and preserves nonvolatiles');eq(before['FX512_hex'],returned['FX512_hex'],'Genuine actual API FX512 conservation');eq(before['ENV28_hex'],returned['ENV28_hex'],'Genuine actual API ENV28 conservation')
                    cs=bytes.fromhex(returned['CS24_hex']);prior=bytes.fromhex(before['CS24_hex']);p=u(prior,0,6);d=u(cs,0,6);need(p[0]==d[0]and p[4:]==d[4:]and d[1:4]==((0xfffffffe,1,before['header'][6])if index==1 else(0xffffffff,0,0)),'Finite actual CS24 ownership output, opaque fields preserved')
                    model.api_return(site,1,ac[0],[(0x78145640,cs)]);model.reg('ecx',ac[1]);model.reg('edx',ac[2]);model.undefined_flag_domain={}
                    for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):model.flag(flag,(ac[8]>>bit)&1)
                    api.append(dict(source_CALL=site,target=target,external_kind='Actual Win32 critical-section API',actual_EAX=ac[0],actual_ECX=ac[1],actual_EDX=ac[2],actual_EFLAGS=ac[8],actual_CS24_hex=cs.hex(),original_source_postRET_seed=False,original_ctor_response_scope='pre-epilogue7810A311'if index==1 else'actualpreRET7810A364'));counts['finite_actual_CS_API_inputs']+=1;return
                need(site==0x7800137f,'Only true measured Win32 HeapAlloc is otherwise external in mixed prefix');frame=model.reg('esp');args=u(model.bytes(frame+4,12),0,3);matches=[(i,r)for i,r in enumerate(API)if r[24]==0 and r[4]==frame and r[20:23]==args and i in owner_inputs and i not in retained_owners and (owner_inputs[i]['CALL_pc']==0x4deab1 or u(model.bytes(frame+104,4))[0]==owner_inputs[i]['CALL_pc']+5)];need(len(matches)==1,'Unique actual source HeapAlloc invocation/frame/arguments '+str((hex(frame),args,[(i,hex(r[4]),r[20:23])for i,r in enumerate(API)if r[24]==0])));ai,fact=matches[0];need(ai in owner_inputs and ai not in retained_owners,'Genuine finite owner occurrence used once');o=owner_inputs[ai];need(args[1]==0 and args[2]<=o['capacity']and fact[10]==o['pointer'],'Actual source-rounded allocator request and private returned pointer')
                need(not any(a<=o['pointer']<a+len(b)for a,b in model.memory.items()),'Fresh genuine private backing');model.memory[o['pointer']]=bytearray(bytes.fromhex(o['initial_hex']));retained_owners[ai]=o
                before=list(model.projected_cpu());actual_before=list(fact[:10]);actual_after=list(fact[10:20]);eq(before[:8],actual_before[:8],'Entire genuine API-entry GPR and reconstructed source frame');model.api_return(site,3,fact[10]);pred=list(model.projected_cpu());eq(pred[3:8],actual_after[3:8],'Actual finite API nonvolatiles/ESP preserved')
                model.reg('ecx',actual_after[1]);model.reg('edx',actual_after[2]);model.undefined_flag_domain={}
                for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):model.flag(flag,(actual_after[8]>>bit)&1)
                api.append(dict(source_CALL=site,target=target,frame=frame,args=list(args),API_index=ai,actual_EAX=fact[10],actual_ECX=actual_after[1],actual_EDX=actual_after[2],actual_EFLAGS=actual_after[8],initial_capacity=o['capacity'],initial_hex=o['initial_hex'],source_game_CALL=o['CALL_pc'],AFTER_machine_seed=False));counts['finite_actual_HeapAlloc_inputs']+=1
            machine.run(lambda m:m.cursor==root['registration']['CALL_pc'],api=finite_API)
            expected_cp=6 if root['entry']==0x4e1ca0 else 0;expected_owners=4 if expected_cp else 1;need(boundary_index[0]==6 and len(imports)==(5 if expected_cp else 3)and len(api)==expected_owners+(2 if expected_cp else 0)and cp_index[0]==expected_cp and fs_index[0]==len(fs_events)and len(retained_owners)==expected_owners,'Every genuine current cdecl/CP/FS/API occurrence exhausted')
            need(not any(x==0x4e22f2 for x in machine.PCs),'Literal zero string arguments take each JE and never call_strdup on measured normal path')
            for ai,o in retained_owners.items():eq(machine.bytes(o['pointer'],o['capacity']).hex(),o['final_hex'],'Whole source-derived capacity backing and untouched tail');counts['whole_literal_owned_byteflows']+=1
            for page in preparation['observed_pages']+preparation['extra_whole_source_pages']:
                if page==0x20001000:continue
                after=raw[178404+preparation['observed_pages'].index(page)*4096:178404+(preparation['observed_pages'].index(page)+1)*4096]if page in preparation['observed_pages']else bundle.data(f'phase/{sequence}/{phase}/extra-after/{page}.bin');eq(machine.bytes(page,4096),after,'Whole literal mixed nonstack source page '+hex(page));counts['whole_literal_nonstack_pages']+=1
            eq(machine.bytes(root['object'],root['object_extent']),raw[178404+preparation['observed_pages'].index(root['object']&~4095)*4096+(root['object']&4095):178404+preparation['observed_pages'].index(root['object']&~4095)*4096+(root['object']&4095)+root['object_extent']],'Full game object source prefix versus actual final object')
            eq(machine.bytes(owner['pointer'],owner['capacity']).hex(),owner['final_hex'],'Entire actual owned backing and untouched tail from literal formatter')
            eq([x['index']for x in machine.output_dispatches],[1,7,1,7],'Literal default narrow table dispatches')
            current_next=u(machine.bytes(0x78037888,4))[0];current_begin=u(machine.bytes(0x7803788c,4))[0]
            previous=bundle.data(f'phase/{sequence}/{phase-1}.bin');prevmeta=u(previous,356464,4);aftermeta=u(raw,356464,4)
            need(prevmeta[0]==current_begin and prevmeta[1]==current_next and current_next>=current_begin,'Whole actual preceding registry input is current source BEFORE')
            used=current_next-current_begin;new_begin=current_begin;growth=[]
            if used+4>prevmeta[2]:
                growth=[(i,f)for i,f in enumerate(API)if f[24]==3 and f[22]==current_begin]
                need(len(growth)==1,'One actual original registry HeapReAlloc response at literal growth branch');ai,fact=growth[0]
                need(fact[21]==0 and fact[23]==prevmeta[2]+16 and fact[10]and aftermeta[2]>=fact[23],'Exact registry source capacity+16 request, genuine response scalar and actual extent');new_begin=fact[10];counts['separate_original_registry_growth_scalar_inputs']+=1
            else:need(aftermeta[2]==prevmeta[2],'No-growth capacity is carried exactly')
            need(aftermeta[0]==new_begin and aftermeta[1]==new_begin+used+4,'Separate physical registry pointer/cursor stores from genuine BEFORE and finite API scalar')
            expected_vector=bytearray(previous[356480:356480+prevmeta[2]]);struct.pack_into('<I',expected_vector,used,root['registration']['callback'])if used+4<=len(expected_vector)else expected_vector.extend(struct.pack('<I',root['registration']['callback']))
            eq(bytes(expected_vector),raw[356480:356480+len(expected_vector)],'Every preserved original registry input byte plus new literal callback store');counts['separate_original_registry_preserved_backing_bytes']+=len(expected_vector)
            for page,protect,type_ in meta:
                predicted=bytearray(machine.bytes(page,4096))
                if page==0x78037000:struct.pack_into('<II',predicted,0x888,new_begin+used+4,new_begin)
                eq(bytes(predicted),bundle.data(f'phase/{sequence}/{phase}/CRT-image/after/{page}.bin'),'Whole original CRT source prefix plus separate literal registration pointer/cursor stores '+hex(page));counts['whole_original_CRT_prefix_and_registration_pages']+=1
            source_owners=[]
            for ai,o in retained_owners.items():
                source_owners.append(dict(o,source_final_hex=machine.bytes(o['pointer'],o['capacity']).hex(),source_owned_accesses=[list(a)for a in machine.accesses if o['pointer']<=a[1]<o['pointer']+o['capacity']]))
            results.append(dict(sequence=sequence,phase=phase,root=root['entry'],FS_initial_input=FS_input,source_PCs=machine.PCs,source_accesses=machine.accesses,import_projections=imports,API_inputs=api,dispatches=machine.output_dispatches,string_iterations=machine.string_iterations,object_hex=machine.bytes(root['object'],root['object_extent']).hex(),owner=dict(owner,source_final_hex=machine.bytes(owner['pointer'],owner['capacity']).hex()),all_owners=source_owners,mixed_owners=[x for x in source_owners if x['CALL_pc']!=0x4deab1],FS_events=fs_events,original_boundary_joins=phase_boundaries,original_CP_joins=cp_events,registration_suffix=dict(before_begin=current_begin,before_next=current_next,source_derived_after_begin=new_begin,source_derived_after_next=new_begin+used+4,finite_HeapReAlloc_response=[dict(API_index=i,actual_words=list(f))for i,f in growth],new_unused_growth_tail_observed_only=bool(growth),callback=root['registration']['callback'],literal_cursor_store_PC=0x78004a69,literal_callback_store_PC=0x78004a67,whole_vector_source_derived=True,full_registration_provider_CPU_executed_by_model=False),no_post_source_seed=True));api_inputs.extend(api);counts['literal_constructor_prefixes']+=1
            print(json.dumps(dict(sequence=sequence,root=hex(root['entry']),source_instructions=len(machine.PCs),passed=True)),flush=True)
        need(counts['literal_constructor_prefixes']==24 and counts['whole_cdecl_CPU_FX_frame_capacity_joins']==144 and counts['whole_literal_owned_byteflows']==42 and counts['literal_actual_CP_CPU_FX_ENV_frame_CS_joins']==36,'All24 current original prefixes/full42owner byteflows/144cdecl/36CP boundaries');passed=True
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        # Aggregate retains and closes the one shared capture exactly once.
        bundle=None
        for filename,value in(('source-derivations.json',results),('instruction-joins.json',joins),('finite-API-inputs.json',api_inputs)):
            p=out/filename;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
        pin(__file__);pin(R/'tools/m4-mixed-format-original/derive_source_comparison.py');pin(M.I.__file__);pin(sys.executable);pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v2.py');pin(R/'tools/m4-formatting-source/compare_trace.py');pin(R/'tools/m4-formatting-source/compare_trace_v2.py');pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v3.py');pin(R/'tools/m4-formatting-source/compare_trace_v3.py');pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v4.py')
        for actual_read in list(AUDITED_READS):pin(actual_read)
        need(AUDITED_READS<=set(PINS),'Every successful actual dependency read physically pinned')
        report=dict(passed=passed,actual_dependency_reads=len(AUDITED_READS),complete_executed_dependency_chain_pinned=True,failed_optional_open_paths=sorted(FAILED_OPTIONAL_READS),original_game_FS_observations=36,allocator_FS_frames_literal_only=True,allocator_FS_individual_events_observed=False,actual_cdecl_FS_head_joins_required=144,scope='All24 current original131 literal formatter4 prefixes from each untouched whole46-page BEFORE/current64CRT pages, actual initial allocator backings/finite Win32 volatile inputs; six mixed balancedCP/nestedFS paths. Separate finite registry growth-or-carry cursor/vector relation from genuine preceding BEFORE and literal two stores; full registration provider CPU remains outside this prefix proof.',counts=dict(counts),files=PINS,reader_scope='Borrowed one authenticated current-original131 session; aggregate closure required',original_undefined_flags='Only current source-dominated logical/shift undefined bits; exact source cause/lifetime retained, literal representatives unchanged',generic_formatter_closed=False,native_executed=False,registration_lifecycle_executed_by_model=False,initializer_credit=0,source_post_state_seed=False,write_operand_before_from_literal_backing=True,undefined_flag_control_denied=True)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':raise SystemExit('Use current_source.py for one shared reader')
