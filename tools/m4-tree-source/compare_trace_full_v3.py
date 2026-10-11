"""Execute the literal tree from genuine one-root BEFORE and typed API facts."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}

def pin(path,expected=None):
    path=Path(path).resolve();digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected is not None and digest!=expected:raise ValueError('Exact physical source input '+str(path))
    if str(path)in PINS and PINS[str(path)]!=digest:raise ValueError('Stable input '+str(path))
    PINS[str(path)]=digest;return path
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,pin(path));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def read(path,expected=None):return json.loads(pin(path,expected).read_bytes())
def words(raw,offset=0,count=1):return struct.unpack_from('<'+'I'*count,raw,offset)
def need(value,label):
    if not value:raise ValueError(label)
def equal(a,b,label):need(a==b,label+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:12]))

def main(name,model_path):
    out=ROOT/'reports/m4-tree-source'/name;need(not out.exists(),'Fresh tree semantic receipt');out.mkdir(parents=True)
    passed=False;reader=None;result={};counts=collections.Counter();boundaries=[]
    try:
        validation=read(ROOT/'reports/m4-tree-original/trace-prefix-validation-r1/report.json','249bdebcb98f732d863611b4b8805442e53ecdea6882e8b2e282d6ee87a735fe');need(validation['passed'],'Genuine independently measured prefix')
        execution=read(validation['execution_path'],validation['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);preparation=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);pages=preparation['observed_pages'];need(len(pages)==43,'Complete accepted page scope')
        D=load('tree_prefix_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');reader=D.DirectSet(execution['original_capture'],pin)
        O=load('tree_original_state_helpers',ROOT/'tools/m4-mfc-source/compare_original_game.py');O.PAGES=tuple(pages);O.MFC_IMPORTS=[tuple(r[:3])for r in struct.iter_unpack('<7I',reader.data('mfc-import-ledger.bin'))]
        G=load('tree_literal_model',model_path);program,callbacks=G.source_program();J=load('tree_numerical_projection',ROOT/'tools/m4-joint-startup27-review/observe.py');projection,_,_,_=J.models();projection.PAGES=list(pages)
        PE=load('tree_provider_PE',ROOT/'tools/analysis/pe.py');provider=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes());worker=pin(build['worker'],build['worker_sha256']).read_bytes()
        hooks=read(ROOT/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json');patches=[]
        for hook in hooks:
            pc,size=hook['pc'],hook['size'];raw=bytes.fromhex(hook['raw']);offset,_=provider.rva_range(pc-provider.image_base,size);equal(provider.data[offset:offset+size],raw,'Exact original observer source span')
            key=struct.pack('<2I',pc,size);matches=[i for i in range(len(worker))if worker.startswith(key,i)and worker[i+12:i+12+size]==raw];need(len(matches)==1,'Unique linked observer target')
            target=words(worker,matches[0]+8)[0];patched=b'\xe9'+struct.pack('<I',(target-pc-5)&0xffffffff)+b'\x90'*(size-5);patches.append(dict(pc=pc,width=size,patched_hex=patched.hex(),source_hex=raw.hex()))
        bootstrap={p:reader.data(f'lockit/post-DllMain/{p}-page.bin')for p in(0x7810a000,0x78145000,0x78146000)}
        imports={r[0]:r[1]for r in struct.iter_unpack('<5I',reader.data('lockit/import-ledger.bin'))};thread=words(reader.data('lockit/thread.bin'))[0]
        def normalized(raw):
            memory=O.normalize_memory(raw,0x1df20c)
            for address,actual,value in((0x5bb454,0x5f4020b4,0x8000021c),(0x5bb4c8,0x5f401782,0x80000339),(0x5bb4f8,0x7810a290,0x1df582),(0x5bb4f4,0x7810a350,0x1df568)):
                need(words(memory[address&~4095],address&4095)[0]==actual,'Exact owning game IAT prior to named projection');struct.pack_into('<I',memory[address&~4095],address&4095,value)
            for patch in patches:
                offset=patch['pc']&4095;equal(memory[0x7810a000][offset:offset+patch['width']],bytes.fromhex(patch['patched_hex']),'Exact compiled observer jump');memory[0x7810a000][offset:offset+patch['width']]=bytes.fromhex(patch['source_hex'])
            for slot in(0x78146198,0x78146184):
                current=words(memory[0x78146000],slot&4095)[0];need(0x18000000<=current<0x19000000,'Authentic x86 API observer cell');struct.pack_into('<I',memory[0x78146000],slot&4095,imports[slot])
            equal(memory[0x78146000],bootstrap[0x78146000],'Whole authentic loaded IAT after exact two shim corrections')
            return memory
        phase=reader.data('phase/0/0.bin');memory=normalized(phase[2276:178404]);actual_after=normalized(phase[178404:354532])
        fs_raw=reader.data('phase/0/0/fs-events.bin');memory[0x7ffde000]=bytearray(struct.pack('<I',words(fs_raw,16)[0]));state=bytearray(O.original_state(projection,G,words(phase,36,10),phase));struct.pack_into('<I',state,2168,0x7ffde000)
        owners=read(ROOT/'reports/m4-tree-original/trace-prefix-validation-r1/actual-owners.json',validation['files'][str((ROOT/'reports/m4-tree-original/trace-prefix-validation-r1/actual-owners.json').resolve())]);owner_index=[0];API=list(struct.iter_unpack('<26I',reader.data('phase/0/0/api-ledger.bin')));allocfacts=[(i,r)for i,r in enumerate(API)if r[24]==0]
        lock_raw=reader.data('phase/0/0/lockit-snapshots.bin');snaps=[lock_raw[i:i+12988]for i in range(0,len(lock_raw),12988)];lock_index=[0];fs_index=[0];unused_frame_bytes=[]
        def owner_resolver(machine,pending,pointer):
            owner=owners[owner_index[0]];owner_index[0]+=1
            need((pending['CALL_pc'],pending['per_site_invocation_ordinal'],pointer,pending['source_frame'][1])==(owner['CALL_pc'],owner['site_invocation'],owner['pointer'],owner['source_frame']),'Literal MFC CALL/site ordinal/frame joins independent owner witness')
            return dict(guest=pointer,native=pointer,requested=24,generation=owner['generation'],capacity=owner['capacity'],initial=bytes.fromhex(owner['initial_hex']))
        def boundary(machine):
            raw=snaps[lock_index[0]];header=words(raw,0,16);cpu=list(machine.projected_cpu());cpu[9]=machine.cursor
            equal(tuple(cpu),words(raw,64,10),'Whole genuine original Lockit boundary CPU '+str(lock_index[0]))
            fx,env=projection.proj(machine.state);equal(projection.hardwarefx(fx),raw[104:616],'Whole source Lockit hardware FX');equal(env,raw[616:644],'Whole source Lockit ENV')
            modeled=machine.bytes(machine.reg('esp'),32);actual=raw[644:676]
            invocation=machine.invocation();invocation_rows=[r for r in machine.tree_function_invocations if r['index']==invocation]
            first=invocation_rows[0]['source_access_index']if invocation_rows else 0
            for offset,(expected,observed)in enumerate(zip(modeled,actual)):
                address=machine.reg('esp')+offset
                writes=[r for r in machine.accesses[first:]if r[4]and r[1]<=address<r[1]+r[3]]
                if writes:need(expected==observed,'Every source-established current-frame byte matches actual original')
                elif expected!=observed:unused_frame_bytes.append(dict(boundary_index=lock_index[0],address=address,source_value=expected,actual_observation=observed,source_access_index=len(machine.accesses),invocation=invocation,source_frame_first_access=first,current_frame_source_write=False))
            equal(machine.bytes(0x78145640,24),raw[676:700],'Full carried CS24 at original boundary')
            boundaries.append(dict(index=lock_index[0],kind=header[3],CPU=cpu,source_access_index=len(machine.accesses),source_CS24_hex=raw[676:700].hex()));lock_index[0]+=1;counts['whole_original_CPU_FX_ENV_frame_CS_boundaries']+=1
        def fs(machine,event,data):
            if event not in('read-before','write-before')or data['domain']!='source'or data['address']!=0x7ffde000:return
            raw=fs_raw[fs_index[0]*1216:(fs_index[0]+1)*1216];header=words(raw,0,8);writing=event=='write-before'
            need(header[2]==data['pc']and data['bytes']==4 and writing==(header[3]!=0),'Finite genuine original FS PC/direction/width')
            equal(machine.bytes(0x7ffde000,4),struct.pack('<I',header[4]),'Genuine FS previous head');need(data['value']==(header[5]if writing else header[4])and machine.reg('esp')==words(raw,32,10)[4],'Actual source-derived FS value/frame')
            if header[7]:equal(machine.bytes(header[6],12),raw[112:124],'Complete actual original12B FS record')
            fs_index[0]+=1;counts['whole_original_FS_records']+=1
        trace_validation=read(ROOT/'reports/m4-tree-original/trace-validation-r2/report.json','1c099256ca7bdc076bffa23a37c9aab6975a4769337ce8c7cff64ba623bea463');need(trace_validation['passed'],'Independent genuine debugger trace validation');actual_trace=read(ROOT/'reports/m4-tree-original/trace-validation-r2/actual-instructions.json',trace_validation['files'][str((ROOT/'reports/m4-tree-original/trace-validation-r2/actual-instructions.json').resolve())]);CRT_returns=[r for r in actual_trace if r['PC']==0x5f401eb7];need(len(CRT_returns)==7,'Every genuine MFC malloc volatile return');CRT_registration=next(r for r in actual_trace if r['PC']==0x5ac124);frontier_facts=[]
        trace_points=read(ROOT/'reports/m4-tree-original/trace-preparation-r1/trace_points.json','df175b8bcfd1c0c49b99fe6b980240e898cd6b7adeff9c43d48ba47f93e31b4a');trace_PCs={r['pc']for r in trace_points};literal_instructions=[]
        class Prefix(G.Machine):
            def step(self):
                if self.cursor in(0x7810a290,0x7810a311,0x7810a350,0x7810a364):boundary(self)
                pc=self.cursor;start=len(self.accesses);before=list(self.projected_cpu());before[9]=pc
                answer=super().step()
                if pc in trace_PCs:
                    after=list(self.projected_cpu());after[9]=self.cursor
                    literal_instructions.append(dict(PC=pc,next_PC=self.cursor,source_before_CPU=before,source_after_CPU=after,source_access_first=start,source_access_end=len(self.accesses)))
                return answer
        machine=Prefix(state,phase[116:628],phase[36:76],memory,program=program,callbacks=callbacks,hook=fs,tree_owner_resolver=owner_resolver)
        machine.call_stack.append((0x4b7f70,0x20001800,0x410a80,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));alloc_index=[0]
        def external(model,target):
            site=model.PCs[-1]
            if site in(0x7810a30b,0x7810a35e):
                before=snaps[lock_index[0]];after=snaps[lock_index[0]+1];header=words(before,0,16);kind=header[3]
                need(kind==(1 if site==0x7810a30b else 4)and target==imports[0x78146198 if kind==1 else 0x78146184],'Exact source/API target and boundary kind');boundary(model)
                bc=words(before,64,10);ac=words(after,64,10);need(ac[3]==bc[3]and ac[5:8]==bc[5:8]and ac[4]==bc[4]+8 and ac[9]==(0x7810a311 if kind==1 else 0x7810a364),'API preserves nonvolatiles and exact stdcall frame')
                equal(before[104:644],after[104:644],'Actual API preserves complete FP environment')
                expected=bytearray(model.bytes(0x78145640,24));depth=words(expected,8)[0]+(1 if kind==1 else -1);need(0<=depth<=2,'Balanced same-thread source recursion')
                struct.pack_into('<III',expected,4,0xfffffffe if depth else 0xffffffff,depth,thread if depth else 0);equal(bytes(expected),after[676:700],'Whole typed original CS24 output derived from original opaque identity and source depth')
                model.api_return(site,1,ac[0],[(0x78145640,bytes(expected))]);cpu=list(model.projected_cpu());cpu[1:3]=ac[1:3];cpu[8]=ac[8];projection.statecpu(model.state,cpu);counts['bounded_original_API_volatile_inputs']+=1;return
            need(target==0x780012b3 and site==0x5f401eb5,'Only genuine MFC malloc scalar frontier')
            api_index,fact=allocfacts[alloc_index[0]];owner=owners[alloc_index[0]];request=words(model.bytes(model.reg('esp')+4,4))[0]
            need(request==24 and fact[21]==0 and fact[22]==32 and fact[10]==owner['pointer']and owner['actual_API_index']==api_index,'Exact positive original allocator request/result')
            initial=reader.data(f'phase/0/0/api-initial/{api_index}/bytes.bin');need(not any(p<=fact[10]<p+len(b)for p,b in model.memory.items()),'Fresh genuine API allocation memory');model.memory[fact[10]]=bytearray(initial)
            model.reg('edx',fact[12]);model.api_return(site,0,fact[10])
            frontier=CRT_returns[alloc_index[0]];actual=list(frontier['raw_debugger_before_cpu']);actual[8]&=~0x10100;actual[9]=frontier['PC'];modeled=list(model.projected_cpu());modeled[9]=model.cursor
            need(actual[0]==fact[10] and actual[2]==fact[12] and actual[3:8]==modeled[3:8] and actual[9]==model.cursor,'Finite malloc return keeps exact result/nonvolatiles/current cdecl source frame')
            modeled[1]=actual[1];modeled[8]=actual[8];projection.statecpu(model.state,modeled)
            frontier_facts.append(dict(service='genuine CRT malloc return',event=frontier['index'],caller=site,return_PC=model.cursor,actual_EAX=actual[0],actual_ECX=actual[1],actual_EDX=actual[2],actual_EFLAGS_without_debugger_TF_RF=actual[8],memory_effects_seeded=False))
            alloc_index[0]+=1;counts['actual_initial_allocator_witnesses']+=1
        machine.run(lambda model:model.cursor==0x78004a36,api=external)
        need(lock_index[0]==len(snaps)and fs_index[0]*1216==len(fs_raw)and alloc_index[0]==owner_index[0]==len(owners),'Exhaust all genuine finite boundary/owner witnesses')
        equal(machine.bytes(machine.reg('esp'),8),struct.pack('<2I',0x5ac124,0x4b7fa0),'Literal source callback CALL frame/value')
        actual=list(CRT_registration['raw_debugger_before_cpu']);actual[8]&=~0x10100;actual[9]=CRT_registration['PC']
        need(actual[0]==0x4b7fa0,'Original registration scalar return is the exact literal callback')
        machine.api_return(0x5ac11e,0,actual[0]);modeled=list(machine.projected_cpu());modeled[9]=machine.cursor
        need(actual[3:8]==modeled[3:8] and actual[9]==machine.cursor,'Finite registration return keeps actual cdecl frame and source nonvolatiles')
        modeled[1:3]=actual[1:3];modeled[8]=actual[8];projection.statecpu(machine.state,modeled)
        frontier_facts.append(dict(service='genuine CRT registration return',event=CRT_registration['index'],caller=0x5ac11e,return_PC=machine.cursor,actual_EAX=actual[0],actual_ECX=actual[1],actual_EDX=actual[2],actual_EFLAGS_without_debugger_TF_RF=actual[8],memory_effects_seeded=False))
        G.complete_root(machine);result=machine.tree_result();counts['actual_finite_CRT_volatile_return_frontiers']=len(frontier_facts)
        need(len(literal_instructions)==len(actual_trace)==1198,'Complete genuine/literal selected source instruction extent')
        joins=[]
        for modeled,actual_row in zip(literal_instructions,actual_trace):
            need(modeled['PC']==actual_row['PC'],'Every reached source PC and occurrence equals genuine trace')
            for side in ('before','after'):
                actual_cpu=list(actual_row['raw_debugger_'+side+'_cpu']);actual_cpu[8]&=~0x10100
                if side=='before':actual_cpu[9]=actual_row['PC']
                if side=='after' and actual_row['instruction_kind']==1:continue
                equal(modeled['source_'+side+'_CPU'],actual_cpu,'Full source CPU matches actual debugger projection '+hex(modeled['PC'])+' '+side)
                counts['whole_projected_instruction_CPU_relations']+=1
            accesses=machine.accesses[modeled['source_access_first']:modeled['source_access_end']]
            if actual_row['instruction_kind']==1:
                need(len(accesses)==1 and accesses[0][1]==0x7ffde000,'FS source instruction separately joins its authoritative raw observer operation');counts['FS_instruction_separate_raw_joins']+=1
            else:
                actual_accesses=[]
                for cell in actual_row['cells']:
                    for direction in (0,1):
                        if cell['write' if direction else 'read']:
                            value=cell['after_value' if direction else 'before_value'];address=cell['address']
                            if not direction:
                                for slot,raw,target in O.MFC_IMPORTS:
                                    if address==slot:need(value==target,'Physical owning MFC import before named source projection');value=raw
                                normalized_IAT={0x5bb454:(0x5f4020b4,0x8000021c),0x5bb4c8:(0x5f401782,0x80000339),0x5bb4f8:(0x7810a290,0x1df582),0x5bb4f4:(0x7810a350,0x1df568),0x5bb52c:(0x78004a36,0x1decb0),0x5bb530:(0x78002fe5,0x1deca2),0x5bb4bc:(0x5f401ea0,0x80000337),0x5bb670:(0x78010a6d,0x1df886),0x5bb4fc:(0x780c10f0,0x1df59c)}
                                if address in normalized_IAT:
                                    raw,target=normalized_IAT[address];need(value==raw,'Exact loaded game import before named source projection');value=target
                            actual_accesses.append((actual_row['PC'],address,value,cell['width'],direction))
                equal([tuple(r)for r in accesses],actual_accesses,'Every instruction read/write/address/value/direction equals actual original '+hex(modeled['PC']));counts['whole_source_instruction_access_relations']+=len(actual_accesses)
            joins.append(dict(event=actual_row['index'],PC=modeled['PC'],source_access_first=modeled['source_access_first'],source_access_end=modeled['source_access_end'],actual_instruction_kind=actual_row['instruction_kind']))
        result['actual_instruction_joins']=joins;result['finite_original_CRT_returns']=frontier_facts
        need(result['candidate_AFTER_seed'] is False,'No tree AFTER seeding')
        for page in pages:
            if page==0x20001000:continue
            equal(machine.bytes(page,4096),bytes(actual_after[page]),'Whole actual original nonstack page '+hex(page));counts['whole_original_nonstack_pages']+=1
        for computed,owner in zip(result['owners'],owners):
            equal(computed['source_final_hex'],owner['final_hex'],'Entire original backing from literal writes and untouched initial capacity tails');counts['whole_original_owner_backings']+=1
        for row in unused_frame_bytes:
            subsequent=[(index,access)for index,access in enumerate(machine.accesses[row['source_access_index']:],row['source_access_index'])if access[1]<=row['address']<access[1]+access[3]]
            if subsequent:
                index,access=subsequent[0];need(access[4],'Observed opaque unused frame byte cannot enter a subsequent literal source read before overwrite')
                row['subsequent_dominating_source_write']=dict(index=index,pc=access[0],address=access[1],width=access[3],value=access[2])
            else:row['never_subsequently_read_or_written']=True
        result['unused_original_frame_observations']=unused_frame_bytes
        result['original_boundary_joins']=boundaries;result['observer_patches']=patches;result['reached_original_PCs']=machine.PCs;result['literal_instructions']=literal_instructions;result['trace_source_frontier']=0x78004a36;passed=True
        for module in(O,projection):
            for path,digest in getattr(module,'PINS',{}).items():pin(path,digest if isinstance(digest,str)else digest['sha256'])
        pin(__file__)
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear()
        (out/'source-derivations.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'source-derivations.json')
        report=dict(passed=passed,scope='Literal persistent tree prefix from genuine untouched original BEFORE and finite scalar/typed API boundaries; no tree AFTER effect seed',counts=dict(counts),candidate_AFTER_machine_seed=False,original_postRET_source_derived=True,original_postRET_observed=False,whole_provider_stack_compared=False,original_unused_frame_bytes_seeded=False,all_current_frame_source_written_bytes_compared=True,opaque_disagreements_proven_unused_before_overwrite=True,initializer_credit=False,files=PINS)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1],ROOT/(sys.argv[2]if len(sys.argv)>2 else'tools/m4-tree-source/game_model.py'))
