"""Independent literal constructor/provider trace from genuine whole BEFORE.

Only actual Win32 allocation/volatile response inputs enter untraced APIs. No
output buffer, provider stack or original AFTER machine seeds the model.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={}
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
def main(name):
    out=R/'reports/m4-mixed-format-original'/name;need(not out.exists(),'Fresh additive source/trace comparison');out.mkdir(parents=True)
    bundle=None;passed=False;counts=collections.Counter();results=[];joins=[];api_inputs=[]
    try:
        original=R/'reports/m4-mixed-format-original/trace-validation-r1';validation=read(original/'report.json','81e5f3b3c418bd80814e1c68c2c7a9daab6fac9b32455e6d223f0b117d1bbc4a');need(validation['passed'],'Measured genuine physical provider instructions')
        normal=read(validation['normal_validation_path'],validation['normal_validation_sha256']);need(normal['passed'],'Same-process genuine cdecl CPU/FX/ENV/owners')
        boundary_path=Path(validation['normal_validation_path']).parent/'actual-cdecl-boundaries.json';boundaries=read(boundary_path,normal['files'][str(boundary_path)])
        owners_path=boundary_path.with_name('actual-owners.json');owners=read(owners_path,normal['files'][str(owners_path)])
        trace=read(original/'trace-observations.json',validation['files'][str((original/'trace-observations.json').resolve())]);phases=read(original/'actual-trace-phases.json',validation['files'][str((original/'actual-trace-phases.json').resolve())])
        execution=read(validation['execution_path'],validation['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);pin(build['worker'],build['worker_sha256']);preparation=read(Path(build['preparation'])/'report.json',build['preparation_sha256'])
        M=load(R/'tools/m4-formatting-source/provider_model.py','literal_formatter_machine');F=load(R/'tools/m4-formatting-source/flag_domain.py','original_architectural_flag_domain');rec=read(M.REC/'report.json',M.REC_SHA)
        for p,h in rec['files'].items():pin(p,h)
        # Reuse the admitted physical full allocator rows, not a host malloc.
        allocator=read(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d')
        frontier=read(R/'reports/m4-mixed-format-original/recovery-r1/report.json','5627b4234b16f5bdb493f4102f541166cbf8bde11c53c3b9a691a24d1230e5fa');game_path=R/'reports/m4-mixed-format-original/recovery-r1/instruction-contracts.json';game=read(game_path,frontier['files'][str(game_path.resolve())]);roots=game['roots'];G=load(R/'tools/m4-lockit-source/game_model.py','retained_literal_MFC_Lockit');program,callbacks=G.source_program();provider_program,_=M.source_program();
        for pc,row in provider_program.items():need(pc not in program or program[pc]==row,'Exact shared literal provider instruction');program[pc]=row
        for row in allocator['instructions']+game['instructions']:
            pc=row['pc'];need(pc not in program or program[pc]==row,'Identical retained physical source row');program[pc]=row
        D=load(R/'tools/m4-crt-allocation-root/run_v2.py','small_formatter_capture');bundle=D.DirectSet(execution['original_capture'],pin)
        named_targets=u(bundle.data('formatting/import-targets.bin'),0,3);eq(named_targets,(0x780264a9,0x780012b3,0x78022b9a),'Actual named loaded provider targets')
        instruction_PCs={row['pc']for row in rec and json.loads(Path(rec['instructions']).read_bytes())['instructions']}
        source_imports={(0x4dea15,0x5bb5a8):0x780264a9,(0x4deab1,0x5bb664):0x780012b3,(0x4dead1,0x5bb658):0x78022b9a}
        cp_targets={slot:target for slot,target,*tail in struct.iter_unpack('<5I',bundle.data('lockit/import-ledger.bin'))}
        source_imports.update({(0x7810a30b,0x78146198):cp_targets[0x78146198],(0x7810a35e,0x78146184):cp_targets[0x78146184]})
        mixed_owners=read(Path(validation['normal_validation_path']).parent/'actual-mixed-owned-relations.json');fs_events=read(Path(validation['normal_validation_path']).parent/'actual-FS-events.json');cp_events=read(Path(validation['normal_validation_path']).parent/'actual-Lockit-boundaries.json')
        for phase,root in enumerate(roots):
            raw=bundle.data(f'phase/0/{phase}.bin');need(len(raw)==356992,'Frozen complete original phase geometry')
            memory={p:bytearray(raw[2276+i*4096:2276+(i+1)*4096])for i,p in enumerate(preparation['observed_pages'])}
            for page in preparation['extra_whole_source_pages']:memory[page]=bytearray(bundle.data(f'phase/0/{phase}/extra-before/{page}.bin'))
            meta=list(struct.iter_unpack('<3I',bundle.data(f'phase/0/{phase}/CRT-image/metadata.bin')))
            for page,protect,type_ in meta:
                need(0x78000000<=page<0x78040000 and page%4096==0 and not(protect&0x101)and type_==0x1000000,'Complete actual loaded source CRT page')
                memory[page]=bytearray(bundle.data(f'phase/0/{phase}/CRT-image/before/{page}.bin'))
            cpu=u(raw,36,10);state=bytearray(3504)
            for reg,value in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),cpu[:8]):struct.pack_into('<I',state,M.I.REG[reg],value)
            for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):state[M.I.FLAGS[flag]]=(cpu[8]>>bit)&1
            struct.pack_into('<I',state,2472,cpu[9]);struct.pack_into('<I',state,M.I.BASE['fs'],0x7ffde000)
            first=next(x for x in boundaries if x['phase']==phase and x['kind']==0);memory[0x7ffde000]=bytearray(struct.pack('<I',fs_events[0]['header'][4]))
            owner=owners[phase];literal=[];imports=[];api=[];boundary_index=[0];cp_index=[0];fs_index=[0];phase_boundaries=[x for x in boundaries if x['phase']==phase];boundary_PCs={0x780264a9:0,0x4dea1b:1,0x780012b3:2,0x4deab7:3,0x78022b9a:4,0x4dead7:5}
            owner_inputs={owner['API_index']:dict(pointer=owner['pointer'],request=owner['request'],capacity=owner['capacity'],API_index=owner['API_index'],initial_hex=owner['initial_hex'],final_hex=owner['final_hex'],CALL_pc=0x4deab1)}
            for o in mixed_owners:need(o['API_index']not in owner_inputs,'Unique genuine four API allocation occurrences');owner_inputs[o['API_index']]=dict(o,request=o['source_request'])
            retained_owners={}
            def source_FS(model,address,value,size,source_pc,writing):
                if address!=0x7ffde000:return
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
                    if pc in boundary_PCs:
                        actual=phase_boundaries[boundary_index[0]];need(actual['kind']==boundary_PCs[pc],'Exact actual cdecl boundary order')
                        eq(list(self.projected_cpu()),actual['cpu'],'Full actual source-derived cdecl CPU '+str((phase,actual['kind'])))
                        eq(self.fx.hex(),actual['FX512_hex'],'Complete carried source FX')
                        eq(self.bytes(self.reg('esp'),32).hex(),actual['frame32_hex'],'Entire cdecl frame32 from root BEFORE/source writes')
                        if actual['owned_hex']:eq(self.bytes(owner['pointer'],owner['capacity']).hex(),actual['owned_hex'],'Entire actual capacity at source API boundary')
                        boundary_index[0]+=1;counts['whole_cdecl_CPU_FX_frame_capacity_joins']+=1
                    before=list(self.projected_cpu());begin=len(self.accesses);preimage={};flag_before=dict(getattr(self,'undefined_flag_domain',{}));flag_after=F.advance(self,self.program[pc],flag_before)
                    consumed={'je':('ZF',),'jne':('ZF',),'ja':('CF','ZF'),'jae':('CF',),'jb':('CF',),'jbe':('CF','ZF'),'jg':('ZF','SF','OF'),'jge':('SF','OF'),'jl':('SF','OF'),'jle':('ZF','SF','OF'),'js':('SF',),'jns':('SF',),'jo':('OF',),'jno':('OF',),'adc':('CF',),'sbb':('CF',),'scasb':('DF',)}.get(self.program[pc]['mnemonic'],())
                    need(not set(consumed)&set(flag_before),'No conditional/repeat/carry source use of an architecturally undefined flag')
                    if consumed:counts['source_defined_control_flag_uses']+=1
                    if pc in instruction_PCs:
                        for a,b in self.memory.items():
                            if a==0x20001000 or a==owner['pointer']:preimage[a]=bytes(b)
                    result=super().step();self.undefined_flag_domain=flag_after
                    if pc in instruction_PCs:literal.append(dict(PC=pc,next_PC=self.cursor,CPU_before=before,CPU_after=list(self.projected_cpu()),source_accesses=[list(r)for r in self.accesses[begin:]],preimage=preimage,undefined_flags_before=flag_before,undefined_flags_after=flag_after))
                    return result
            machine=Prefix(state,raw[116:628],raw[36:76],memory,program=program,callbacks=callbacks)
            machine.call_stack.append((root['entry'],cpu[4],0x410a80,0,cpu[5],cpu[3],cpu[6],cpu[7],0))
            API=list(struct.iter_unpack('<26I',bundle.data(f'phase/0/{phase}/api-ledger.bin')))
            def finite_API(model,target):
                site=model.PCs[-1]
                if site in(0x7810a30b,0x7810a35e):
                    index=1 if site==0x7810a30b else 4
                    need(target==cp_targets[0x78146198 if index==1 else 0x78146184],'Exact owning real Enter/Leave target');source_CP(model,index);before,returned=cp_events[index],cp_events[index+1];bc,ac=before['CPU'],returned['CPU'];need(ac[3]==bc[3]and ac[5:8]==bc[5:8]and ac[4]==bc[4]+8 and ac[9]==(0x7810a311 if index==1 else 0x7810a364),'Actual source API consumes only its genuine pointer/return frame and preserves nonvolatiles');eq(before['FX512_hex'],returned['FX512_hex'],'Genuine actual API FX512 conservation');eq(before['ENV28_hex'],returned['ENV28_hex'],'Genuine actual API ENV28 conservation')
                    cs=bytes.fromhex(returned['CS24_hex']);prior=bytes.fromhex(before['CS24_hex']);p=u(prior,0,6);d=u(cs,0,6);need(p[0]==d[0]and p[4:]==d[4:]and d[1:4]==((0xfffffffe,1,before['header'][6])if index==1 else(0xffffffff,0,0)),'Finite actual CS24 ownership output, opaque fields preserved')
                    model.api_return(site,1,ac[0],[(0x78145640,cs)]);model.reg('ecx',ac[1]);model.reg('edx',ac[2]);model.undefined_flag_domain={}
                    for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):model.flag(flag,(ac[8]>>bit)&1)
                    api.append(dict(source_CALL=site,target=target,external_kind='Actual Win32 critical-section API',actual_EAX=ac[0],actual_ECX=ac[1],actual_EDX=ac[2],actual_EFLAGS=ac[8],actual_CS24_hex=cs.hex(),original_source_postRET_seed=False,original_ctor_response_scope='pre-epilogue7810A311'if index==1 else'actualpreRET7810A364'));counts['finite_actual_CS_API_inputs']+=1;return
                need(site==0x7800137f,'Only true measured Win32 HeapAlloc is otherwise external in mixed prefix');frame=model.reg('esp');args=u(model.bytes(frame+4,12),0,3);matches=[(i,r)for i,r in enumerate(API)if r[24]==0 and r[4]==frame and r[20:23]==args];need(len(matches)==1,'Unique actual source HeapAlloc invocation/frame/arguments');ai,fact=matches[0];need(ai in owner_inputs and ai not in retained_owners,'Genuine finite owner occurrence used once');o=owner_inputs[ai];need(args[1]==0 and args[2]<=o['capacity']and fact[10]==o['pointer'],'Actual source-rounded allocator request and private returned pointer')
                need(not any(a<=o['pointer']<a+len(b)for a,b in model.memory.items()),'Fresh genuine private backing');model.memory[o['pointer']]=bytearray(bytes.fromhex(o['initial_hex']));retained_owners[ai]=o
                before=list(model.projected_cpu());actual_before=list(fact[:10]);actual_after=list(fact[10:20]);eq(before[:8],actual_before[:8],'Entire genuine API-entry GPR and reconstructed source frame');model.api_return(site,3,fact[10]);pred=list(model.projected_cpu());eq(pred[3:8],actual_after[3:8],'Actual finite API nonvolatiles/ESP preserved')
                model.reg('ecx',actual_after[1]);model.reg('edx',actual_after[2]);model.undefined_flag_domain={}
                for flag,bit in(('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)):model.flag(flag,(actual_after[8]>>bit)&1)
                api.append(dict(source_CALL=site,target=target,frame=frame,args=list(args),API_index=ai,actual_EAX=fact[10],actual_ECX=actual_after[1],actual_EDX=actual_after[2],actual_EFLAGS=actual_after[8],initial_capacity=o['capacity'],initial_hex=o['initial_hex'],source_game_CALL=o['CALL_pc'],AFTER_machine_seed=False));counts['finite_actual_HeapAlloc_inputs']+=1
            machine.run(lambda m:m.cursor==root['registration']['CALL_pc'],api=finite_API)
            need(boundary_index[0]==6 and len(imports)==5 and len(api)==6 and cp_index[0]==6 and fs_index[0]==6 and len(retained_owners)==4,'All exact cdecl/CP/FS/API witnesses exhausted')
            need(not any(x==0x4e22f2 for x in machine.PCs),'Literal zero string arguments take each JE and never call_strdup on measured normal path')
            for ai,o in retained_owners.items():eq(machine.bytes(o['pointer'],o['capacity']).hex(),o['final_hex'],'Whole source-derived capacity backing and untouched tail');counts['whole_literal_owned_byteflows']+=1
            for page in preparation['observed_pages']+preparation['extra_whole_source_pages']:
                if page==0x20001000:continue
                after=raw[178404+preparation['observed_pages'].index(page)*4096:178404+(preparation['observed_pages'].index(page)+1)*4096]if page in preparation['observed_pages']else bundle.data(f'phase/0/{phase}/extra-after/{page}.bin');eq(machine.bytes(page,4096),after,'Whole literal mixed nonstack source page '+hex(page));counts['whole_literal_nonstack_pages']+=1
            eq(machine.bytes(root['object'],root['object_extent']),raw[178404+preparation['observed_pages'].index(root['object']&~4095)*4096+(root['object']&4095):178404+preparation['observed_pages'].index(root['object']&~4095)*4096+(root['object']&4095)+root['object_extent']],'Full game object source prefix versus actual final object')
            eq(machine.bytes(owner['pointer'],owner['capacity']).hex(),owner['final_hex'],'Entire actual owned backing and untouched tail from literal formatter')
            actual=[x for x in trace if x['phase']==phase];need(len(actual)==len(literal),'Entire actual/literal provider instruction count')
            for index,(derived,event)in enumerate(zip(literal,actual)):
                eq((derived['PC'],derived['next_PC']),(event['source_pc'],event['next_pc']),'Every literal actual source instruction/control')
                eq(F.project(derived['CPU_before'],derived['undefined_flags_before']),F.project(event['CPU_before_projected'],derived['undefined_flags_before']),'Whole source-defined instruction-entry CPU '+str((phase,index,hex(derived['PC']))))
                eq(F.project(derived['CPU_after'],derived['undefined_flags_after']),F.project(event['CPU_after_projected'],derived['undefined_flags_after']),'Whole source-defined instruction-return CPU '+str((phase,index,hex(derived['PC']))))
                operands=[]
                for cell in event['cells']:
                    matched=[r for r in derived['source_accesses']if r[1]==cell['address']and r[3]==cell['width']]
                    expected=collections.Counter((cell['before'] if not write else cell['after'],write)for write,enabled in((0,cell['read']),(1,cell['write']))if enabled)
                    eq(collections.Counter((r[2],r[4])for r in matched),expected,'Exact literal source cell read/write values/direction/width')
                    if cell['owner_index']!=0xffffffff:need(cell['owner_index']==owner['index'] and cell['generation']==owner['index']+1 and cell['owner_offset']+cell['width']<=owner['request'],'Exact actual current source owner occurrence/request bounds')
                    ambient=None
                    for address,bytes_ in derived['preimage'].items():
                        offset=cell['address']-address
                        if 0<=offset and offset+cell['width']<=len(bytes_):
                            ambient=int.from_bytes(bytes_[offset:offset+cell['width']],'little');break
                    if cell['write']:
                        need(ambient is not None,'Every actual source write has whole literal BEFORE backing')
                        need(ambient==cell['before'],'Entire write operand BEFORE bytes from literal preceding source state '+str((phase,index,hex(derived['PC']),hex(cell['address']),cell['width'],ambient,cell['before'])))
                        counts['literal_actual_write_before_joins']+=1
                    operands.append(dict(**cell,source_rows=matched,source_before_value=ambient));counts['literal_actual_memory_operand_joins']+=1
                # Every modeled memory access must correspond to a measured
                # operand; no source operation or extra owner store is hidden.
                need(sum(c['read']+c['write']for c in event['cells'])==len(derived['source_accesses']),'Exact complete instruction memory extent')
                joins.append(dict(phase=phase,index=index,PC=derived['PC'],next_PC=derived['next_PC'],CPU_before=derived['CPU_before'],CPU_after=derived['CPU_after'],actual_CPU_before=event['CPU_before_projected'],actual_CPU_after=event['CPU_after_projected'],undefined_flags_before=derived['undefined_flags_before'],undefined_flags_after=derived['undefined_flags_after'],operands=operands));counts['whole_projected_CPU_sides']+=2;counts['literal_actual_provider_instructions']+=1;counts['architectural_undefined_flag_projected_sides']+=int(bool(derived['undefined_flags_before']))+int(bool(derived['undefined_flags_after']))
            eq([x['index']for x in machine.output_dispatches],[1,7,1,7],'Exact source-derived narrow-format table branches')
            results.append(dict(phase=phase,root=root['entry'],source_PCs=machine.PCs,source_accesses=machine.accesses,import_projections=imports,API_inputs=api,dispatches=machine.output_dispatches,string_iterations=machine.string_iterations,object_hex=machine.bytes(root['object'],root['object_extent']).hex(),owner=dict(owner,source_final_hex=machine.bytes(owner['pointer'],owner['capacity']).hex()),provider_instructions=len(literal),no_post_source_seed=True));api_inputs.extend(api);counts['literal_constructor_prefixes']+=1
        need(counts['literal_actual_provider_instructions']==797 and counts['whole_projected_CPU_sides']==1594,'Complete measured original provider trace extent');passed=True
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if bundle:bundle.close();bundle.entries.clear();bundle.bundles.clear()
        for filename,value in(('source-derivations.json',results),('instruction-joins.json',joins),('finite-API-inputs.json',api_inputs)):
            p=out/filename;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
        pin(__file__);pin(R/'tools/m4-mixed-format-original/derive_source_comparison.py');pin(M.I.__file__);pin(sys.executable);pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v2.py');pin(R/'tools/m4-formatting-source/compare_trace.py');pin(R/'tools/m4-formatting-source/compare_trace_v2.py');pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v3.py');pin(R/'tools/m4-formatting-source/compare_trace_v3.py');pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v4.py')
        report=dict(passed=passed,scope='Literal mixed constructor prefix including MFC, two nested FS frames, balanced initialized Lockit and797 genuine narrow provider instructions from untouched phase BEFORE. Four actual HeapAlloc initial/volatile inputs and two actual CS API volatile/output observations are finite external inputs; no source postRET or AFTER memory seed.',counts=dict(counts),files=PINS,reader_closed=True,original_undefined_flags='Only current source-dominated logical/shift undefined bits; exact source cause/lifetime retained, literal representatives unchanged',generic_formatter_closed=False,native_executed=False,registration_lifecycle_executed_by_model=False,initializer_credit=0,source_post_state_seed=False,write_operand_before_from_literal_backing=True,undefined_flag_control_denied=True)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
