"""Independent complete124 original observer COFF/link, resource and owner audit."""
from collections import Counter
import hashlib,importlib.util,json,re,struct,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def expected_lockit(pc,kind,replay=b'',continuation=None,target=None):
    b=bytearray();rel=[]
    def emit(h):b.extend(bytes.fromhex(h))
    def addr(name,addend=0,typ=6):rel.append((len(b),name,typ));b.extend(struct.pack('<I',addend))
    for i,op in enumerate(('a3','890d','8915','891d','8925','892d','8935','893d')):emit(op);addr('_lockit_cpu',i*4)
    emit('c705');addr('_lockit_cpu',36);b.extend(struct.pack('<I',pc))
    emit('c705');addr('_lockit_kind');b.extend(struct.pack('<I',kind))
    emit('8b25');addr('_mixed_host_esp')
    emit('9c8f05');addr('_lockit_cpu',32)
    emit('64a100000000a3');addr('_lockit_head')
    emit('0fae05');addr('_lockit_fx');emit('d935');addr('_lockit_env');emit('d925');addr('_lockit_env')
    emit('e8');addr('_lockit_observe',0,0x14)
    emit('0fae0d');addr('_lockit_fx');emit('d925');addr('_lockit_env');emit('ff35');addr('_lockit_cpu',32);emit('9d')
    for i,op in enumerate(('a1','8b0d','8b15','8b1d','8b25','8b2d','8b35','8b3d')):
        if i==4:continue
        emit(op);addr('_lockit_cpu',i*4)
    emit('8b25');addr('_lockit_cpu',16);b.extend(replay)
    if continuation or target:emit('ff25');addr(continuation or target)
    return bytes(b),rel
def main(name):
    out=R/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh independent original revision');out.mkdir(parents=True)
    pins={};counts=Counter();passed=False;reader=None
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact independent physical input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Immutable physical input');pins[str(p)]=v;return p
    def read(p):return json.loads(pin(p).read_bytes())
    def module(p,n):
        s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    try:
        p=R/'reports/m4-lockit-original/original-preparation-r4';b=R/'reports/m4-lockit-original/original-build-r3';e=R/'reports/m4-lockit-original/original-execution-r2';v=R/'reports/m4-lockit-original/original-validation-r2/report.json'
        prep=read(p/'report.json');build=read(b/'build.json');execution=read(e/'report.json');validation=read(v)
        need(all(x['passed']for x in(prep,build,execution,validation)),'Final current original gates')
        need(build['preparation_sha256']==sha(p/'report.json') and execution['build_sha256']==sha(b/'build.json') and validation['preparation_sha256']==sha(p/'report.json') and validation['execution_sha256']==sha(e/'report.json'),'Direct final original receipt pins')
        for q,h in validation['files'].items():pin(q,h)
        pin(__file__);P=module(pin(R/'tools/analysis/pe.py'),'independent124_PE')
        game=P.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());cp=P.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        def physical(pe,a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
        worker=P.PEImage(pin(build['worker'],build['worker_sha256']).read_bytes());need(worker.machine==0x14C,'Actual linked i386 final worker')
        C=module(pin(R/'tools/m4-fs-source/observer_attribution.py'),'independent124_COFF')
        release=b/'build-x86/mw34_joint_startup124_original.dir/Release'
        symbols,sections=C.parse_coff(pin(release/'lockit_observer_x86.obj').read_bytes());defs={x['name']:x for x in symbols.values()if x['section']>0 and x['storage']==2}
        links=list(release.rglob('link.command.1.tlog'));need(len(links)==1,'One actual final original link command');link=pin(links[0]).read_text(encoding='utf-16');need('LOCKIT_OBSERVER_X86.OBJ' in link.upper(),'Actual new observer COFF linked into worker')
        fsbindings=read(p/'fs-hook-bindings.json');need(len(fsbindings)==45,'Exactly45 real FS hook sites')
        fs_symbols,fs_sections=C.parse_coff(pin(release/'fs_observer_x86.obj').read_bytes());fsdefs={x['name']:x for x in fs_symbols.values()if x['section']>0 and x['storage']==2}
        crt=P.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
        for item in fsbindings:
            code=bytes.fromhex(item['raw_bytes']);need(physical(crt if item['PC']>=0x78000000 else game,item['PC'],len(code))==code,'Exact physical FS original broker span')
            expected,rel,marks=C.expected_function(item['PC'],item['kind'],code);d=fsdefs[item['declared_observer'] if item['declared_observer'].startswith('_')else'_'+item['declared_observer']];sec=fs_sections[d['section']]
            need(sec['bytes'][d['value']:d['value']+len(expected)]==expected,'Complete compiled FS preservation/replay/host stack')
            need([(o-d['value'],n,t)for o,n,t in sec['relocations']if d['value']<=o<d['value']+len(expected)]==rel,'Every compiled FS relocation')
            counts['compiled_FS_functions']+=1;counts['compiled_FS_bytes']+=len(expected);counts['compiled_FS_relocations']+=len(rel)
        # Unchanged accepted NULLfree/vtable observer code and relocations survive this actual final link.
        old=R/'reports/m4-vtable-original/build-r2/build-x86/mw34_joint_startup120_original.dir/Release'
        for filename in('nullfree_observer_x86.obj','vtable_observer_x86.obj'):
            new_symbols,new_sections=C.parse_coff(pin(release/filename).read_bytes());old_symbols,old_sections=C.parse_coff(pin(old/filename).read_bytes())
            need(filename.upper()in link.upper(),'Actual inherited observer named in current final link')
            for k,sec in new_sections.items():
                if sec['characteristics']&0x20000000:
                    candidates=[x for x in old_sections.values()if x['name']==sec['name'] and x['characteristics']&0x20000000]
                    need(len(candidates)==1 and candidates[0]['bytes']==sec['bytes'] and candidates[0]['relocations']==sec['relocations'],'Exact inherited compiled executable observer code/relocation equality')
                    counts['inherited_observer_executable_bytes']+=len(sec['bytes'])
        D=module(pin(R/'tools/m4-crt-allocation-root/run_v2.py'),'independent124_original_reader');reader=D.DirectSet(validation['original_capture'],pin)
        need(reader.data('COMPLETE.txt')==b'complete' and reader.data('header.bin')[:8]==b'MW4J124O','Actual complete original124 transport')
        boot={a:reader.data(f'lockit/post-DllMain/{a}-page.bin')for a in(0x7810A000,0x78145000,0x78146000)}
        for a,x in boot.items():need(len(x)==4096 and reader.data(f'lockit/restored/{a}-page.bin')==x,'Every complete final loaded provider page restored')
        need(boot[0x7810A000]==physical(cp,0x7810A000,4096),'Current post-DllMain entire RX page matches exact PE at preferred base')
        tid=struct.unpack('<I',reader.data('lockit/thread.bin'))[0];need(tid>0,'Actual owning game/provider thread')
        imports=reader.data('lockit/import-ledger.bin');named={struct.unpack_from('<I',imports,i)[0]:struct.unpack_from('<5I',imports,i)for i in range(0,len(imports),20)}
        order=prep['order'];roots={x['entry']:x for x in prep['Lockit_roots']};pageindex={a:i for i,a in enumerate(prep['observed_pages'])};hooks=read(p/'lockit-hook-bindings.json');linked_symbols={};functions=[];patched=None;IATpage=None
        firstphase=next(i for i,x in enumerate(order)if x['entry']in roots);first=reader.data(f'phase/0/{firstphase}/lockit-snapshots.bin');need(len(first)==6*12988,'First authentic full six-boundary record')
        patched=first[700:4796];IATpage=first[8892:12988]
        def executable(a):return any(s['executable']and worker.image_base+s['virtual_address']<=a<worker.image_base+s['virtual_address']+s['raw_size']for s in worker.sections)
        for h in hooks:
            code=bytes.fromhex(h['raw']);need(physical(cp,h['pc'],h['size'])==code,'Entire four source observer patch spans physical')
            i=h['pc']-0x7810A000;span=patched[i:i+h['size']];need(span[0]==0xE9 and span[5:]==bytes([0x90])*(h['size']-5),'Exact observed E9 and explicit padding span')
            target=(h['pc']+5+int.from_bytes(span[1:5],'little',signed=True))&0xFFFFFFFF;need(executable(target),'Current original patch points to current owned worker')
            functions.append((h['name'].replace('probe_','lockit_'),h['pc'],h['kind'],bytes.fromhex(h['replay']),'_lockit_continue_'+format(h['pc'],'x')if h['continuation']else None,None,target))
        for name,kind,cell in(('lockit_api_Enter',1,0x78146198),('lockit_api_Leave',4,0x78146184)):
            target=struct.unpack_from('<I',IATpage,cell&4095)[0];need(executable(target),'Current loaded API IAT targets owned observer wrapper');functions.append((name,0,kind,b'',None,'_lockit_actual_'+('Enter'if kind==1 else'Leave'),target))
        for name,pc,kind,replay,cont,target,linked in functions:
            expected,rel=expected_lockit(pc,kind,replay,cont,target);d=defs['_'+name];sec=sections[d['section']]
            need(sec['bytes'][d['value']:d['value']+len(expected)]==expected,'Every actual assembled CPU/FX/ENV/host-stack/replay byte')
            need([(o-d['value'],n,t)for o,n,t in sec['relocations']if d['value']<=o<d['value']+len(expected)]==rel,'Every actual assembled observer relocation')
            linkedbytes=physical(worker,linked,len(expected));normalized=bytearray(linkedbytes)
            for offset,symbol,typ in rel:
                addend=struct.unpack_from('<I',expected,offset)[0];value=struct.unpack_from('<I',linkedbytes,offset)[0];address=(value-addend)&0xFFFFFFFF if typ==6 else (linked+offset+4+value-addend)&0xFFFFFFFF
                need(symbol not in linked_symbols or linked_symbols[symbol]==address,'Every final observer linked relocation target consistent');linked_symbols[symbol]=address;normalized[offset:offset+4]=expected[offset:offset+4]
            need(bytes(normalized)==expected,'Complete final linked observer byte attribution')
            if cont:need(struct.unpack('<I',physical(worker,linked_symbols[cont],4))[0]==pc+len(replay),'Final linked physical continuation DWORD')
            counts['compiled_linked_Lockit_functions']+=1;counts['compiled_linked_Lockit_bytes']+=len(expected);counts['compiled_linked_Lockit_relocations']+=len(rel)
        expectedcode=bytearray(boot[0x7810A000])
        for h in hooks:
            i=h['pc']-0x7810A000;expectedcode[i:i+h['size']]=patched[i:i+h['size']]
        need(bytes(expectedcode)==patched,'Only four declared patches change whole code page')
        expectediat=bytearray(boot[0x78146000])
        for cell in(0x78146198,0x78146184):expectediat[cell&4095:(cell&4095)+4]=IATpage[cell&4095:(cell&4095)+4]
        need(bytes(expectediat)==IATpage,'Only two actual API wrappers change entire loaded provider IAT page')
        source=read(R/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json');allocspec={a['CALL_pc']:a for a in source['allocations']};offsets=read(R/'reports/m4-lockit-source/provider-interface-r1/instruction-contracts.json')['game_scratch_offsets'];owner_joins=[]
        for sequence in range(6):
            owners=[]
            for phase,item in enumerate(order):
                data=reader.data(f'phase/{sequence}/{phase}.bin');need(len(data)==356992 and struct.unpack_from('<I',data,16)[0]==item['entry'],'Actual phase root and immutable original ABI');entry=item['entry']
                off,_=game.rva_range(item['slot']-game.image_base,4);need(struct.unpack('<I',game.read(off,4))[0]==entry,'Actual original table slot per current phase')
                for after,start in((False,2276),(True,178404)):
                    for page in(0x7810A000,0x78145000,0x78146000):
                        actual=data[start+pageindex[page]*4096:start+(pageindex[page]+1)*4096];expected=patched if page==0x7810A000 else IATpage if page==0x78146000 else boot[page];need(actual==expected,'Entire current loaded provider page carried through every phase');counts['whole_provider_endpoint_pages']+=1
                count=struct.unpack('<I',reader.data(f'phase/{sequence}/{phase}/lockit-count.bin'))[0];snap=reader.data(f'phase/{sequence}/{phase}/lockit-snapshots.bin');need(count==(6 if entry in roots else 0)and len(snap)==count*12988,'Exactly actual declared root boundaries')
                if entry in roots:
                    rs=[snap[i*12988:(i+1)*12988]for i in range(6)];root=roots[entry];parsed=[]
                    for index,x in enumerate(rs):
                        w=struct.unpack_from('<16I',x);cpu=struct.unpack_from('<10I',x,64);frame=struct.unpack_from('<8I',x,644);cs=struct.unpack_from('<6I',x,676);depth=int(index in(2,3,4))
                        need(w[:4]==(1,index,entry,index)and w[6:8]==(tid,2)and w[13:15]==(0x7810A290,0x7810A350),'Authentic whole root/provider import/source interface identity')
                        need(cs==(0xFFFFFFFF,0xFFFFFFFE if depth else 0xFFFFFFFF,depth,tid if depth else 0,0,0x020007D0),'Genuine same-thread full24B held/unheld CS')
                        expectedpc=(named[0x78146198][1]if index==1 else named[0x78146184][1]if index==4 else {0:0x7810A290,2:0x7810A311,3:0x7810A350,5:0x7810A364}[index]);need(cpu[9]==expectedpc,'Exact captured source/interface PC label')
                        need(x[700:4796]==patched and x[8892:12988]==IATpage,'Complete snapshot source and IAT pages')
                        expecteddata=bytearray(boot[0x78145000]);expecteddata[0x640:0x658]=x[676:700];need(x[4796:8892]==bytes(expecteddata),'Every complete held/unheld provider data page')
                        parsed.append((w,cpu,frame,cs));counts['actual_Lockit_CPU_FX_ENV_boundaries']+=1;counts['whole_Lockit_snapshot_pages']+=3
                    for start in(0,3):
                        a,m,z=parsed[start:start+3];ctor=start==0;F=a[1][4];need(m[1][4]==F-(16 if ctor else 8)and z[1][4]==F-(8 if ctor else 0),'Actual F−16/F−8 API and epilogue frames')
                        need(m[2][:2]==((0x7810A311 if ctor else 0x7810A364),0x78145640),'Actual complete API CALL return and single CS argument')
                        need(a[1][1]==F+offsets[str(entry)]['constructor'if ctor else'destructor'],'Exact physical scratch address in genuine game CALL frame')
                        need(rs[start][104:644]==rs[start+1][104:644]==rs[start+2][104:644],'Complete actual512BFX+28BENV triple equality')
                        if ctor:need(m[2][2:4]==(a[1][7],a[1][6])and z[2][:3]==(a[1][7],a[1][6],a[2][0])and z[1][7]==a[1][1],'Exact saved source EDI/ESI and retained scratchECX before epilogue')
                        else:need(a[2]==z[2]and all(a[1][i]==m[1][i]==z[1][i]for i in(3,5,6,7)),'Exact actual destructor caller frame and nonvolatile preservation')
                        counts['actual_API_frame_relations']+=1;counts['full_FX_ENV_triples']+=1
                    for call in sorted((a for a in allocspec.values()if a['root']==entry),key=lambda a:a['CALL_pc']):
                        index=len(owners);meta=reader.data(f'phase/{sequence}/{phase}/lockit-allocation/{index}/meta.bin');w=struct.unpack('<9I',meta);owned=reader.data(f'phase/{sequence}/{phase}/lockit-allocation/{index}/bytes.bin');initial=reader.data(f'phase/{sequence}/{phase}/api-initial/{w[6]}/bytes.bin')
                        need(w[:5]==(1,index,entry,call['CALL_pc'],call['requested'])and w[8]==len(owned)==len(initial)==32,'Exact genuine requested20B/24B owner and actual32B capacity')
                        expected=bytearray(initial);parent=0 if call['kind']=='shared-header'else owners[-1][2];self_=0 if call['kind']=='shared-header'else w[7];struct.pack_into('<III',expected,0,self_,parent,self_);struct.pack_into('<I',expected,call['requested']-4,int(call['kind']=='shared-header'));need(owned==expected,'Every exact source write plus complete untouched initial owner bytes')
                        owners.append((meta,owned,w[7]));owner_joins.append(dict(sequence=sequence,phase=phase,CALL=call['CALL_pc'],requested=w[4],pointer=w[7],capacity=w[8]));counts['actual_new_owners']+=1
                for index,(meta,owned,ptr)in enumerate(owners):
                    need(reader.data(f'phase/{sequence}/{phase}/lockit-allocation/{index}/meta.bin')==meta and reader.data(f'phase/{sequence}/{phase}/lockit-allocation/{index}/bytes.bin')==owned,'Complete persistent actual owner identity/backing carry');counts['whole_owner_phase_carries']+=1
                counts['original_phases']+=1
            need(len(owners)==8,'Eight authentic new owners per complete sequence')
            for index,(meta,owned,ptr)in enumerate(owners):
                need(reader.data(f'cleanup/{sequence}/lockit-allocation-{index}-before.bin')==meta and reader.data(f'cleanup/{sequence}/lockit-allocation-{index}-owned.bin')==owned and reader.data(f'cleanup/{sequence}/lockit-allocation-{index}-returned.bin')==struct.pack('<I',1),'Actual positive whole-owned MFC825 cleanup after original CRT restoration');counts['actual_new_owner_cleanups']+=1
        need(counts['original_phases']==744 and counts['actual_Lockit_CPU_FX_ENV_boundaries']==144 and counts['actual_API_frame_relations']==48 and counts['actual_new_owners']==48 and counts['whole_owner_phase_carries']==1860,'Exact full current original observation cardinalities')
        emit=out/'owner-joins.json';emit.write_text(json.dumps(owner_joins,indent=2)+'\n');pin(emit);passed=True
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if reader:reader.close()
        report=dict(passed=passed,scope='Independent compiled/final-linked45FS+6Lockit observers, complete744 original provider page carries,144 Lockit boundaries,48 genuine new owner+cleanup receipts; no native initializer acceptance',counts=dict(counts),original_preparation_sha256=sha(p/'report.json')if'p'in locals()else None,original_build_sha256=sha(b/'build.json')if'b'in locals()else None,original_execution_sha256=sha(e/'report.json')if'e'in locals()else None,original_validation_sha256=sha(v)if'v'in locals()else None,actual_initialized_state=2,constructor_actual_pre_epilogue=True,API_PC_interface_labels=True,original_postRET_CPU_captured=False,whole_game_complete=False,initializer_credit=0,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
