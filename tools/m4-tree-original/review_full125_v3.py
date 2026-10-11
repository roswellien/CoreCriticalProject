"""Independent final linked original125 observer and physical target review.

Only fresh original125 bootstrap/header/one Lockit snapshot is read. The full
750-phase observation gate is separately bound, without reopening old captures.
"""
from collections import Counter
from pathlib import Path
import hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def main(name):
    out=R/'reports/m4-tree-original'/name;need(not out.exists(),'Fresh full-original125 review');out.mkdir(parents=True)
    pins,counts,rows={},Counter(),[];reader=None;passed=False
    def pin(p,h=None):
        p=Path(p).resolve();a=pins.get(str(p))or sha(p);need(h is None or a==h,'Exact current physical file '+str(p));pins[str(p)]=a;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def module(p,n):
        s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    try:
        prepdir=R/'reports/m4-tree-original/original125-preparation-r1';builddir=R/'reports/m4-tree-original/original125-build-r1';execdir=R/'reports/m4-tree-original/original125-execution-r1';valpath=R/'reports/m4-tree-original/original125-validation-r1/report.json'
        prep=read(prepdir/'report.json','6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1')
        build=read(builddir/'build.json','e25a97c26e9a23d54f8340c7c0908a891915865b9ccda044ae3793e244d5a585')
        exe=read(execdir/'report.json','1e327ed23d5276964fc67e70308ce80a60a7e34051960b02e9c30da67b9998ae')
        val=read(valpath,'5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534')
        need(all(x['passed']for x in(prep,build,exe,val)),'All actual current original125 gates passed')
        need(build['preparation_sha256']==val['preparation_sha256']==sha(prepdir/'report.json')and exe['build_sha256']==val['build_sha256']==sha(builddir/'build.json')and val['execution_sha256']==sha(execdir/'report.json'),'Exact preparation/build/execution/validation lineage')
        need(prep['original_roots']==125 and prep['original_phases']==750 and prep['callback_count']==97 and prep['record_bytes']==356992 and not prep['predicted_counts_supplied_to_execution'] and not prep['debugger_instruction_trace_enabled'],'Genuine bounded normal full125 schedule, no prediction or debugger trace inputs')
        for k,v in dict(phases=750,Lockit_snapshots=612,owners=90,actual_initial_allocations=90,new_FS_records=198,actual_API_frames=204,whole_provider_page_relations=2250,tree_phases=6,tree_allocation_invocations=42).items():need(val['counts'][k]==v,'Exact measured full original extent '+k)
        for q,h in prep['files'].items():pin(q,h)
        for q,h in read(builddir/'pins.json')['files'].items():pin(q,h)
        for q,h in val['files'].items():
            if Path(q).suffix.lower()!='.mwb':pin(q,h)
        P=module(pin(R/'tools/analysis/pe.py'),'full125_independent_PE');C=module(pin(R/'tools/m4-fs-source/observer_attribution.py'),'full125_independent_COFF');L=module(pin(R/'tools/m4-lockit-review/full_original_review.py'),'full125_independent_Lockit')
        game=P.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());crt=P.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());cp=P.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        workerbytes=pin(build['worker'],build['worker_sha256']).read_bytes();worker=P.PEImage(workerbytes);need(worker.machine==0x14c and worker.image_base==0x18000000,'Actual declared fixed-base i386 original125 worker')
        def physical(pe,a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
        def executable(a):return any(s['executable']and worker.image_base+s['virtual_address']<=a<worker.image_base+s['virtual_address']+s['raw_size']for s in worker.sections)
        release=builddir/'build-x86/mw34_joint_startup124_original.dir/Release';links=list(release.rglob('link.command.1.tlog'));need(len(links)==1,'One actual final original link command');link=pin(links[0]).read_text(encoding='utf-16')
        shared={}
        def linked(expected,rel,target):
            need(executable(target),'Every final observer target belongs to current worker executable section');actual=physical(worker,target,len(expected));normalized=bytearray(actual)
            for offset,symbol,typ in rel:
                addend=struct.unpack_from('<I',expected,offset)[0];value=struct.unpack_from('<I',actual,offset)[0];address=(value-addend)&0xffffffff if typ==6 else(target+offset+4+value-addend)&0xffffffff
                need(typ in(6,0x14),'Exact i386 DIR32/REL32 only');need(symbol not in shared or shared[symbol]==address,'Stable actual linked observer symbol '+symbol);shared[symbol]=address;normalized[offset:offset+4]=expected[offset:offset+4]
            need(bytes(normalized)==expected,'Every final linked executable observer byte, modulo typed exact COFF relocation fields')
        fsyms,fsecs=C.parse_coff(pin(release/'fs_observer_x86.obj').read_bytes());fdefs={x['name']:x for x in fsyms.values()if x['section']>0 and x['storage']==2};fs=read(prepdir/'fs-hook-bindings.json');need(len(fs)==57 and len({h['PC']for h in fs})==57,'All57 distinct actual FS observers')
        need('FS_OBSERVER_X86.OBJ'in link.upper(),'All current FS functions in actual link')
        for h in fs:
            pc=h['PC'];raw=bytes.fromhex(h['raw_bytes']);need(physical(crt if pc>=0x78000000 else game,pc,len(raw))==raw,'Exact original source FS MOV bytes')
            expected,rel,marks=C.expected_function(pc,h['kind'],raw);symbol='_fs_hook_'+format(pc,'x');d=fdefs[symbol];sec=fsecs[d['section']]
            need(sec['bytes'][d['value']:d['value']+len(expected)]==expected and [(o-d['value'],n,t)for o,n,t in sec['relocations']if d['value']<=o<d['value']+len(expected)]==rel,'Complete compiled FS CPU/FX/ENV/host-stack/replay and all relocations')
            key=struct.pack('<3I',pc,len(raw),h['kind']);matches=[];start=0
            while True:
                i=workerbytes.find(key,start)
                if i<0:break
                if workerbytes[i+16:i+16+len(raw)]==raw:matches.append(i)
                start=i+1
            need(len(matches)==1,'Unique physical final linked FsHook initializer');target=struct.unpack_from('<I',workerbytes,matches[0]+12)[0];linked(expected,rel,target)
            need(physical(worker,shared['_fs_continue_'+format(pc,'x')],4)==struct.pack('<I',pc+len(raw)),'Every actual FS continuation points after the full original MOV')
            need(marks['source_MOV']==marks['fs_before_source_stack_restore']+6 and all(marks[n+'_host_stack_switch']+6==marks[n+'_first_stack_instruction']for n in('fs_before','fs_after')),'Actual source ESP saved before stack work; source MOV replays on restored guest stack')
            rows.append(dict(PC=pc,kind=h['kind'],raw_hex=raw.hex(),compiled_target=target,compiled_table_offset=matches[0],symbol=symbol,function_bytes=len(expected),relocations=len(rel),continuation=pc+len(raw)))
            counts['compiled_linked_FS_functions']+=1;counts['compiled_linked_FS_bytes']+=len(expected);counts['compiled_linked_FS_relocations']+=len(rel)
        # The unchanged accepted observer code and relocations are in this same actual worker.
        old=R/'reports/m4-vtable-original/build-r2/build-x86/mw34_joint_startup120_original.dir/Release'
        for filename in('nullfree_observer_x86.obj','vtable_observer_x86.obj'):
            ns,nsecs=C.parse_coff(pin(release/filename).read_bytes());os,osecs=C.parse_coff(pin(old/filename).read_bytes());need(filename.upper()in link.upper(),'Inherited observer present in final125 link')
            for sec in nsecs.values():
                if sec['characteristics']&0x20000000:
                    other=[s for s in osecs.values()if s['name']==sec['name']and s['characteristics']&0x20000000];need(len(other)==1 and other[0]['bytes']==sec['bytes']and other[0]['relocations']==sec['relocations'],'Every inherited executable observer byte and relocation unchanged');counts['inherited_observer_executable_bytes']+=len(sec['bytes'])
        D=module(pin(R/'tools/m4-crt-allocation-root/run_v2.py'),'full125_fresh_bounded_reader');transport=read(val['original_capture']);need(transport['payload_bytes']<512*1024*1024,'Fresh small original125 payload only, no inherited archives');reader=D.DirectSet(val['original_capture'],pin)
        need(reader.data('COMPLETE.txt')==b'complete'and reader.data('header.bin')[:8]==b'MW4J125O','Actual complete original125 capture')
        boot={a:reader.data(f'lockit/post-DllMain/{a}-page.bin')for a in(0x7810a000,0x78145000,0x78146000)}
        for a,x in boot.items():need(len(x)==4096 and reader.data(f'lockit/restored/{a}-page.bin')==x,'Whole authentic post-DllMain provider page restored')
        need(boot[0x7810a000]==physical(cp,0x7810a000,4096)and struct.unpack_from('<7I',boot[0x78145000],0x640)==(0xffffffff,0xffffffff,0,0,0,0x020007d0,2),'Actual authentic preferred-base loaded code and unseeded state2/CS24')
        phase=next(x['phase']for x in prep['selected_order']if x['entry']==0x411010);snap=reader.data(f'phase/0/{phase}/lockit-snapshots.bin');need(len(snap)==6*12988,'Bounded actual first six Lockit boundaries');patched=snap[700:4796];iat=snap[8892:12988]
        hooks=read(R/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json');lsyms,lsecs=C.parse_coff(pin(release/'lockit_observer_x86.obj').read_bytes());ldefs={x['name']:x for x in lsyms.values()if x['section']>0 and x['storage']==2};need('LOCKIT_OBSERVER_X86.OBJ'in link.upper(),'Actual Lockit observers linked into same final125 worker');functions=[]
        for h in hooks:
            need(physical(cp,h['pc'],h['size'])==bytes.fromhex(h['raw']),'Every exact physical source Lockit patch span');s=patched[h['pc']&4095:(h['pc']&4095)+h['size']];need(s[0]==0xe9 and s[5:]==b'\x90'*(h['size']-5),'Exact runtime source patch and padding');target=(h['pc']+5+int.from_bytes(s[1:5],'little',signed=True))&0xffffffff
            functions.append((h['name'].replace('probe_','lockit_'),h['pc'],h['kind'],bytes.fromhex(h['replay']),'_lockit_continue_'+format(h['pc'],'x')if h['continuation']else None,None,target))
        for symbol,kind,cell in(('lockit_api_Enter',1,0x78146198),('lockit_api_Leave',4,0x78146184)):functions.append((symbol,0,kind,b'',None,'_lockit_actual_'+('Enter'if kind==1 else'Leave'),struct.unpack_from('<I',iat,cell&4095)[0]))
        for symbol,pc,kind,replay,cont,api,target in functions:
            expected,rel=L.expected_lockit(pc,kind,replay,cont,api);d=ldefs['_'+symbol];sec=lsecs[d['section']];need(sec['bytes'][d['value']:d['value']+len(expected)]==expected and [(o-d['value'],n,t)for o,n,t in sec['relocations']if d['value']<=o<d['value']+len(expected)]==rel,'Every actual compiled full Lockit wrapper byte and relocation');linked(expected,rel,target)
            if cont:need(physical(worker,shared[cont],4)==struct.pack('<I',pc+len(replay)),'Exact linked Lockit source continuation')
            rows.append(dict(symbol=symbol,kind=kind,source_PC=pc,compiled_target=target,function_bytes=len(expected),relocations=len(rel)));counts['compiled_linked_Lockit_functions']+=1;counts['compiled_linked_Lockit_bytes']+=len(expected);counts['compiled_linked_Lockit_relocations']+=len(rel)
        wanted=bytearray(boot[0x7810a000])
        for h in hooks:wanted[h['pc']&4095:(h['pc']&4095)+h['size']]=patched[h['pc']&4095:(h['pc']&4095)+h['size']]
        need(bytes(wanted)==patched,'Only exact four source patches change complete code page');wanted=bytearray(boot[0x78146000])
        for cell in(0x78146198,0x78146184):wanted[cell&4095:(cell&4095)+4]=iat[cell&4095:(cell&4095)+4]
        need(bytes(wanted)==iat,'Only exact two observed real API wrappers change complete loaded IAT page')
        imports=reader.data('lockit/import-ledger.bin');named={w[0]:w[1]for w in struct.iter_unpack('<5I',imports)}
        for name,cell,index in(('_lockit_actual_Enter',0x78146198,1),('_lockit_actual_Leave',0x78146184,4)):
            address=shared[name];need(any(s['writable']and worker.image_base+s['virtual_address']<=address<worker.image_base+s['virtual_address']+s['virtual_size']for s in worker.sections),'Tailcall pointer is owned current worker writable storage')
            actual=struct.unpack_from('<I',snap,index*12988+9*4)[0];need(actual==named[cell]and struct.unpack_from('<I',boot[0x78146000],cell&4095)[0]==actual,'Actual observed BSS target field equals genuine loaded named API; runtime BSS has no raw PE value')
        reference=pin(prepdir/'reference.cpp').read_text();need('Exact declared FS observer JMP'in reference and 'Exact protected FS observer byte'in reference and 'Exact Lockit declared observer byte'in reference,'Normal actually linked worker checks every source/broker byte and current target at checkpoints')
        need(counts['compiled_linked_FS_functions']==57 and counts['compiled_linked_Lockit_functions']==6,'Complete63 final linked observer attribution')
        reader.close();reader=None
        (out/'compiled-target-attribution.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'compiled-target-attribution.json');pin(__file__);pin(R/'tools/m4-tree-original/review_full125.py');pin(R/'tools/m4-tree-original/derive_review_full125_v2.py');pin(R/'tools/m4-tree-original/review_full125_v2.py');pin(R/'tools/m4-tree-original/derive_review_full125_v3.py');passed=True
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if reader:reader.close()
        report=dict(passed=passed,scope='Independent all57 final linked FS observers, six final linked Lockit wrappers and actual fresh original125 loaded target attribution; full750-phase evidence separately pinned',counts=dict(counts),actual_full_original_counts=val['counts']if'val'in locals()else None,original_preparation_sha256=sha(prepdir/'report.json')if'prepdir'in locals()else None,original_build_sha256=sha(builddir/'build.json')if'builddir'in locals()else None,original_execution_sha256=sha(execdir/'report.json')if'execdir'in locals()else None,original_validation_sha256=sha(valpath)if'valpath'in locals()else None,actual_initialized_state=2,constructor_actual_pre_epilogue=True,original_postRET_CPU_captured=False,API_PC_interface_labels=True,full_FS_table_attribution=True,typed_COFF_relocation_fields_only=True,full_original_reader_repeated=False,inherited_capture_reader_opened=False,reader_closed=True,initializer_credit=0,files=pins)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
