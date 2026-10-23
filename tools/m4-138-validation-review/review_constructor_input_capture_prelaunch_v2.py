review_source=__file__;prior=__file__
"""Independent physical admission for bounded original constructor chronology."""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='222f3e87042964c9865872e4fffb8b9b67a025cb62b5f179d2705037c64bf285'
BH='039dc53233f739f3fb4616859051377ac46f87a3520bee92c8106bc3c9a8a175'

def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(name):
    out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir()
    files={};counts=collections.Counter();links=[];passed=False
    def pin(path,identity=None):
        path=Path(path).resolve();assert path.suffix.lower()not in('.zip','.mwb')
        value=sha(path);assert identity is None or value==identity,(path,identity,value)
        assert str(path)not in files or files[str(path)]==value;files[str(path)]=value;return path
    def read(path,identity=None):return json.loads(pin(path,identity).read_bytes())
    def load(path,name):
        spec=importlib.util.spec_from_file_location(name,pin(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def sparse(path,identity):
        data=pin(path,identity).read_bytes();n=struct.unpack_from('<I',data,8)[0];assert len(data)==12+n*4104
        result={struct.unpack_from('<I',data,12+4104*i)[0]:(struct.unpack_from('<I',data,16+4104*i)[0],data[20+4104*i:4116+4104*i])for i in range(n)};assert len(result)==n;return result
    try:
        folder=R/'reports/m4-138-validation-review/constructor-input-capture-preparation-r5';bf=R/'reports/m4-138-validation-review/constructor-input-capture-build-r2'
        p=read(folder/'report.json',PH);b=read(bf/'build.json',BH)
        supplement=p;parent_current=R/'reports/m4-constructor-original/chronological-preparation-r10';parent_geometry=read(parent_current/'report.json','22cc8626a26963643e2a56d600c282f128f6db46920353f4e7ac58f81580cefe');p={**parent_geometry,**supplement}
        cpp_changes=read(folder/'changes.json');asm_changes=read(folder/'asm-changes.json')
        def undo(text,deltas):
            for delta in reversed(deltas):assert text.count(delta['new'])==1; text=text.replace(delta['new'],delta['old'])
            return text
        assert undo(pin(folder/'reference.cpp').read_text(),cpp_changes)==pin(parent_current/'reference.cpp').read_text()
        assert undo(pin(folder/'reference_x86.asm').read_text(),asm_changes)==pin(parent_current/'reference_x86.asm').read_text()
        for leaf in parent_current.iterdir():
            if leaf.is_file()and leaf.name not in('report.json','pins.json','reference.cpp','reference_x86.asm'):assert pin(leaf).read_bytes()==pin(folder/leaf.name).read_bytes()
        assert len(cpp_changes)==7 and len(asm_changes)==2
        assert supplement['maximum_additional_whole_CRT_page_bytes']==9437184 and supplement['CRT_CS24_API_inputs_outputs']and supplement['asm_exact_inverse']
        counts['current37_complete_source_inverse']=1;counts['current37_unchanged_observer_files']=len(list(parent_current.iterdir()))-4
        assert p['passed']and b['passed']and b['preparation_sha256']==PH
        for receipt,field in((p,'files'),(b,'sources')):
            for q,h in receipt[field].items():pin(q,h)
        assert(p['original_roots'],p['original_sequences'],p['original_phases'],p['record_bytes'],p['source_frame'])==(37,6,222,356992,0x20001800)
        assert not p['writer_executed']and not p['writer_admitted']and not p['capture_archive_opened']and p['initializer_credit']==0
        parent_path=R/'reports/m4-startup131-original/preparation-r4/report.json'
        parent=read(parent_path,'1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
        contract=read(folder/'contracts.json')
        new=[dict(entry=0x4103f0,slot=0x5e0038),dict(entry=0x410440,slot=0x5e003c),dict(entry=0x459b40,slot=0x5e00a0)]
        expected=sorted([x for x in parent['selected_order']if x['slot']<=0x5e00a0]+new,key=lambda x:x['slot'])
        assert p['selected_order']==contract['selected_order']==expected
        assert expected[13:16]==new[:2]+[dict(entry=0x5ae3e4,slot=0x5e0040)]and expected[36]==new[2]
        assert contract['MFC1168_phase']==15 and contract['source_AFTER_seed']is False
        assert contract['omitted_unaccepted_widget_slots'],'Selected chronology must explicitly distinguish omitted slots'
        PE=load(R/'tools/analysis/pe.py','ctor37_physical_pe')
        game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        cp=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        def physical(image,address,size):start,_=image.rva_range(address-image.image_base,size);return image.data[start:start+size]
        pack=sparse(folder/'pages.bin',p['pack_sha256']);oldpack=sparse(parent_path.parent/'pages.bin',parent['pack_sha256'])
        assert len(pack)==149 and len(oldpack)==134
        overlay=read(folder/'source-overlay.json');deltas={}
        for row in overlay:
            address=row['address'];before=bytes.fromhex(row['old_hex']);after=bytes.fromhex(row['source_hex']);assert len(before)==len(after)
            assert after==physical(game,row['physical_source_PC'],len(after))
            for offset,value in enumerate(after):
                at=address+offset;assert at not in deltas or deltas[at]==value;deltas[at]=value
                assert pack[at&~4095][1][at&4095]==value
            counts['whole_physical_overlay_spans']+=1
        for address,(permission,before)in oldpack.items():
            assert pack[address][0]==permission
            for offset,(a,z)in enumerate(zip(before,pack[address][1])):
                if a!=z:assert permission==1 and a==0xcc and deltas.get(address+offset)==z;counts['exact_prior_CC_to_source_bytes']+=1
            counts['whole_retained_pack_pages']+=1
        for address,(permission,data)in pack.items():
            assert address%4096==0 and len(data)==4096 and permission in(0,1,2)
            if address not in oldpack and permission in(0,2):assert data==physical(game,address,4096);counts['whole_new_physical_data_pages']+=1
        for row in p['source_spans']:
            image=cp if row['origin']else game;data=physical(image,row['pc'],row['size']);assert image.data[row['image_offset']:row['image_offset']+row['size']]==data
            if not row['origin']:
                for offset,value in enumerate(data):assert pack[(row['pc']+offset)&~4095][1][(row['pc']+offset)&4095]==value
            counts['whole_physical_source_spans']+=1
        for row in expected:
            assert struct.unpack('<I',physical(game,row['slot'],4))[0]==row['entry']==struct.unpack_from('<I',pack[row['slot']&~4095][1],row['slot']&4095)[0];counts['physical_selected_pairs']+=1
        broker=pin(folder/'original_broker.hpp').read_text();bases=[int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')]
        assert all(address&~65535 in bases for address in pack)
        asm=pin(folder/'constructor_observer_x86.asm').read_text();bindings=read(folder/'constructor-hook-bindings.json');assert len(bindings)==8
        for row in bindings:
            data=bytes.fromhex(row['raw_bytes']);assert data==physical(game,row['return_PC'],len(data))and row['continuation']==row['return_PC']+len(data)
            block=asm[asm.index(row['symbol']+' PROC'):asm.index(row['symbol']+' ENDP')]
            db=' db '+','.join('0%02xh'%v for v in data)
            assert db in block and 'jmp DWORD PTR ctor_continue_%x'%row['return_PC']in block
            for token in('fxsave ctor_fx','fnstenv ctor_env','fldenv ctor_env','fxrstor ctor_fx','call ctor_observe','mov esp,mixed_host_esp','mov esp,DWORD PTR ctor_cpu[16]'):assert token in block
            counts['whole_normal_stolen_return_bytes']+=1
        assert physical(game,0x40a850,4)==bytes.fromhex('8b4104c3') and ' db 08bh,041h,004h' in asm and ' db 0c3h' in asm
        observer=pin(folder/'constructor_normal.hpp').read_text()
        for token in('sizeof(ConstructorNormalSnapshot)==189108','constructor_normal_count>=256','capacity==v.capacity','safe_read','seen.size()<256','dword(header+4)==previous'):assert token in observer
        cpp=pin(folder/'reference.cpp').read_text();main_cpp=cpp[cpp.index('int main('):]
        for token in('if(phase){mixed_input=mixed_after;','require(phase==15','constructor_graph(phase_stem+"/BEFORE-constructor")','constructor_member_graph(phase_stem+"/AFTER-member")','constructor_whole_live_owners(phase_stem+"/BEFORE-owners")','constructor_normal_dump(phase_stem+"/normal")','mfc825(reinterpret_cast<void*>(v.pointer))'):assert token in main_cpp
        assert main_cpp.index('Actual original823 named owning target')<main_cpp.index('r->tag.status=execute();')<main_cpp.index('Restore exact original823 named target')<main_cpp.index('constructor_normal_dump(phase_stem+"/normal")')
        assert main_cpp.index('Constructor source observer permissions')<main_cpp.index('r->tag.status=execute();')<main_cpp.index('Restore actual constructor source')
        assert main_cpp.count('constructor_collect(phase,phase_stem);if(constructor_phase)')==1

        chain=read(R/'reports/m4-constructor-original/entry-chain-r1/report.json','80bc3b7041473bd8fb643aa0b5e0839bae1d185659adca2fc802728bcccd18a7')
        assert chain['passed'] and not chain['source_AFTER_seed'] and not chain['new_constructor_reached_path_observed']
        for path,identity in chain['files'].items():pin(path,identity)
        mfc=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
        crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
        for ordinal in (823,825):
            actual=next(row for row in mfc.exports()if row['ordinal']==ordinal)
            assert 'forwarder'not in actual and actual['rva']+mfc.image_base==chain['MFC_exports'][str(ordinal)]['target']
            assert '==0x%x'%chain['MFC_exports'][str(ordinal)]['target']in main_cpp
            counts['independently_resolved_named_MFC_exports']+=1
        for name in ('malloc','free'):
            actual=next(row for row in crt.exports()if name in row['names'])
            assert 'forwarder'not in actual and actual['rva']+crt.image_base==chain['CRT_named_exports'][name]['target']
            counts['independently_resolved_named_CRT_exports']+=1
        owning={mfc.image_base+s['iat_rva']:(row['library'],s)for row in mfc.imports()for s in row['symbols']}
        for cell,name in ((0x5f49814c,'malloc'),(0x5f498148,'free')):
            library,source=owning[cell];assert library.casefold()=='msvcrt.dll'and source['name']==name
            assert source=={k:v for k,v in chain['MFC_CRT_IAT'][str(cell)].items()if k!='library'}
            assert 'dword(0x%x)==reinterpret_cast<unsigned>(GetProcAddress(crt,"%s"))'%(cell,name)in main_cpp
            counts['independently_resolved_owning_MFC_CRT_cells']+=1
        for ordinal,pc,cell in ((823,0x5abd26,0x5bb4bc),(825,0x5abd1a,0x5bb4c8)):
            assert physical(game,pc,6)==bytes.fromhex('ff25')+struct.pack('<I',cell)
            raw=struct.unpack('<I',physical(game,cell,4))[0];assert raw==0x80000000|ordinal
            counts['physical_game_ordinal_import_cells']+=1
        deltas={}
        for role,value in chain['source_frames'].items():
            current=0
            for row in value['rows']:
                raw=bytes.fromhex(row['bytes_hex']);image=mfc if row['PC']<0x78000000 else crt
                assert raw==physical(image,row['PC'],len(raw))
                if raw[:2]==bytes.fromhex('83ec'):adjustment=-raw[2]
                elif raw[:2]==bytes.fromhex('81ec'):adjustment=-struct.unpack_from('<I',raw,2)[0]
                else:
                    assert (0x50<=raw[0]<=0x57 or raw[0]in(0x68,0x6a,0xe8)or raw[0]==0xff and (raw[1]>>3)&7 in(2,6))
                    adjustment=-4
                current+=adjustment;assert current==row['ESP_delta_after'];counts['whole_physical_source_stack_adjustments']+=1
            assert current==value.get('entry_to_callee_delta',value.get('entry_to_API_delta'));deltas[role]=current
        assert deltas['MFC823_to_malloc']+deltas['CRT_malloc_to_HeapAlloc']==chain['MFC823_entry_to_HeapAlloc_before_delta']==-104
        assert deltas['MFC825_to_free']+deltas['CRT_free_to_HeapFree']==chain['MFC825_entry_to_HeapFree_before_delta']==-80
        for role,key in (('CRT_malloc_to_HeapAlloc','HeapAlloc_source_saved_return'),('CRT_free_to_HeapFree','HeapFree_source_saved_return')):
            last=chain['source_frames'][role]['rows'][-1];assert last['PC']+len(bytes.fromhex(last['bytes_hex']))==chain[key]
        assert contract['source_MFC_entry_chain_sha256']=='80bc3b7041473bd8fb643aa0b5e0839bae1d185659adca2fc802728bcccd18a7'
        assert contract['source_MFC_entry_target']==chain['MFC_exports']['823']['target'] and contract['source_MFC_release_target']==chain['MFC_exports']['825']['target']
        assert 'out.append("constructor/provider-entries.bin",ctor_named_entries.data(),sizeof(ctor_named_entries))'in cpp

        olddir=R/'reports/m4-constructor-original/chronological-preparation-r7'
        oldprep=read(olddir/'report.json','6d3f97e734647085ee51c00538527e3e82ad31880d1310f946839be0e15720a0')
        for leaf in ('pages.bin','selected-order.json','constructor-hook-bindings.json','constructor_observer_x86.asm','boundaries_x86.asm','normal-bindings.hpp'):
            if (olddir/leaf).exists():assert pin(olddir/leaf).read_bytes()==pin(folder/leaf).read_bytes(),leaf
        oldspec=pin(olddir/'spec.hpp').read_text()
        old='inline constexpr std::array<NullFreeBinding,5> nullfree_bindings{{{0x4ada90,0x4ad8d8},{0x4b12d0,0x4b1210},{0x4b12d0,0x4b1287},{0x4d84a0,0x4d82ec},{0x5a7dc0,0x5a87cf}}};'
        new='inline constexpr std::array<NullFreeBinding,7> nullfree_bindings{{{0x4ada90,0x4ad8d8},{0x4b12d0,0x4b1210},{0x4b12d0,0x4b1287},{0x4d84a0,0x4d82ec},{0x5a7dc0,0x5a87cf},{0x4103f0,0x58af9a},{0x410440,0x58af9a}}};'
        assert oldspec.count(old)==1 and oldspec.replace(old,new)==pin(folder/'spec.hpp').read_text()
        call=physical(game,0x58af9a,5);assert call[0]==0xe8 and 0x58af9f+struct.unpack_from('<i',call,1)[0]==0x5abd1a
        counts['exact_new_NULL_free_source_CALLs']=2
        oldref=pin(olddir/'reference.cpp').read_text().replace('fs_error=1','ctor_record_fs_failure(__LINE__,__FILE__)')
        def one(before,after):
            nonlocal_dummy=None
            assert oldref.count(before)==1,before
            return oldref.replace(before,after,1)
        diag='unsigned ctor_fs_failure_line{},ctor_fs_failure_root{};const char*ctor_fs_failure_source{};\nvoid ctor_record_fs_failure(unsigned line,const char*source){if(!fs_error){ctor_fs_failure_line=line;ctor_fs_failure_root=fs_phase_root;ctor_fs_failure_source=source;}fs_error=1;}\n'
        oldref=one('FsEvent fs_events[256]{};','FsEvent fs_events[256]{};\n'+diag)
        oldref=one('constructor_occurrences.clear();registry_API_count=0;fs_error=0;','constructor_occurrences.clear();registry_API_count=0;fs_error=0;ctor_fs_failure_line=0;ctor_fs_failure_root=0;')
        oldref=one('fs_event_count=0;fs_error=0;vtable_count=0;','fs_event_count=0;fs_error=0;ctor_fs_failure_line=0;ctor_fs_failure_root=0;vtable_count=0;')
        oldref=one('std::memset(constructor_normal_records,0,sizeof(constructor_normal_records));','std::memset(constructor_normal_records,0,sizeof(constructor_normal_records));std::memset(constructor_getter_backings,0,sizeof(constructor_getter_backings));')
        diagnostic='if(fs_error)std::cerr<<"Constructor37 first observer fault sequence="<<sequence<<" phase="<<phase<<" root="<<std::hex<<ctor_fs_failure_root<<" source="<<(ctor_fs_failure_source?ctor_fs_failure_source:"none")<<" source-line="<<std::dec<<ctor_fs_failure_line<<" FS-count="<<fs_event_count<<" NULL-count="<<nullfree_count<<" NULL-PC="<<std::hex<<nullfree_cpu.pc<<" NULL-frame="<<nullfree_cpu.esp<<" vtable-PC="<<vtable_cpu.pc<<" normal-count="<<std::dec<<constructor_normal_count<<"\\n";'
        oldref=one('fs_phase_root=0;require(!fs_error,"Exact FS observer/allocation transparency");','fs_phase_root=0;'+diagnostic+'require(!fs_error,"Exact FS observer/allocation transparency");')
        assert oldref==undo(cpp,cpp_changes),'Full inherited source and exact new supplement inverse remain'
        oldobserver=pin(olddir/'constructor_normal.hpp').read_text().replace('fs_error=1','ctor_record_fs_failure(__LINE__,__FILE__)')
        oldobserver=oldobserver.replace('static unsigned constructor_normal_count{};','static unsigned constructor_normal_count{};\nstatic std::array<unsigned,10>constructor_getter_backings[256]{};',1)
        oldguard='        if((vptr!=0x5bcc68&&vptr!=0x5cab60&&vptr!=0x5ca6d8)||dword(vptr+0x18)!=0x40a850){ctor_record_fs_failure(__LINE__,__FILE__);return;}'
        start=observer.index('        bool receiver_page=false,vptr_page=false;')
        end=observer.index('\n    }',start)
        guard=observer[start:end]
        assert guard.count('VirtualQuery(')==2 and guard.count('safe_read(')==1 and 'PAGE_READWRITE' in guard and 'PAGE_READONLY' in guard
        for token in ('(ctor_cpu.ecx&4095U)+8<=4096','(vptr&4095U)+0x1c<=4096','ctor_cpu.edx!=vptr','dword(vptr+0x18)!=0x40a850','node!=header&&raw[2]==ctor_cpu.ecx','if(!published)','n<256','if(node==header)break','if(n==255)','constructor_getter_backings[constructor_normal_count]={1,constructor_normal_count,ctor_cpu.ecx,ctor_cpu.ecx&~4095U,vptr,vptr&~4095U,vptr+0x18,dword(vptr+0x18),receiver_region.Protect,vptr_region.Protect}'):
            assert token in guard,token
        # Whole current guard is the independently inspected additive header;
        # preserve every line outside that bounded ownership expansion.
        assert oldobserver.count(oldguard)==1
        oldobserver=oldobserver.replace(oldguard,guard,1)
        export='    constructor_dump(stem+"/normal-records.bin",constructor_normal_records,constructor_normal_count*sizeof(ConstructorNormalSnapshot));'
        oldobserver=oldobserver.replace(export,export+'\n    constructor_dump(stem+"/getter-backings.bin",constructor_getter_backings,constructor_normal_count*sizeof(constructor_getter_backings[0]));',1)
        assert oldobserver==observer,'Entire other original observer code unchanged'
        checker=pin(R/'tools/m4-constructor-original/validate_v5.py','e702b75020c12b15a3ade692e66484e5b29c8be4b74ae22ba8e22e93d5e6cb74').read_text()
        assert 'getter-backings.bin' in checker and 'NULL' in checker and 'header' in checker
        counts['whole_additive_observer_source_relations']=3
        C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','ctor37_actual_coff')

        worker=PE.PEImage(pin(b['worker'],b['worker_sha256']).read_bytes());assert worker.machine==0x14c and worker.image_base==0x18000000
        release=bf/'build-x86/mw34_joint_startup124_original.dir/Release'
        for obj in [release/(leaf+'.obj') for leaf in ('reference_x86','boundaries','api_boundaries','preserve_x86','fs_observer_x86','nullfree_observer_x86','vtable_observer_x86','lockit_observer_x86','format_observer_x86','constructor_observer_x86')]:
            if obj.name=='reference.obj':continue
            sy,se=C.coff(pin(obj).read_bytes());sections=[i for i,v in se.items()if v['flags']&0x20000000 and v['bytes']]
            if not sections:continue
            assert len(sections)==1
            name=obj.stem+' complete assembly';fake={0:dict(name=name,value=0,section=sections[0],type=0x20,storage=2)}
            proof=C.linked_function(worker,fake,se,name);links.append(proof);counts['whole_linked_ASM_sections']+=1;counts['whole_linked_ASM_bytes']+=proof['bytes']
        sy,se=C.coff(pin(release/'reference.obj').read_bytes())
        names=['_main','_observe_boundary','_observe_named_API','_ctor_observe']+[v['name']for v in sy.values()if v['type']==0x20 and v['section']>0 and any(v['name'].startswith(a)for a in('?constructor_collect@@','?constructor_graph@@','?constructor_member_graph@@','?constructor_whole_live_owners@@','?constructor_normal_dump@@'))]
        assert len(names)==9
        for name in names:proof=C.linked_function(worker,sy,se,name);links.append(proof);counts['whole_linked_CPP_functions']+=1
        for name in ('_registry_observe_allocation','?capture_constructor_input_segments@@YAXXZ','?execute@@YAIXZ'):
            proof=C.linked_function(worker,sy,se,name);links.append(proof);counts['whole_linked_current_input_CPP_functions']+=1
        asm_current=pin(folder/'reference_x86.asm').read_text();block=asm_current[asm_current.index(' ; Integer-only CS-before copy;'):asm_current.index(' mov registry_API_active,0',asm_current.index(' ; Integer-only CS-before copy;'))];assert block.count('pushfd')==block.count('popfd')==1 and block.count('push eax')==block.count('pop eax')==1 and block.count('push ecx')==block.count('pop ecx')==1 and block.count('push esi')==block.count('pop esi')==1 and block.count('push edi')==block.count('pop edi')==1 and not any(op in block for op in('call ','fxsave','fxrstor','fld','fst','fnstenv'))
        consumed=set();tlogs=list(release.rglob('CL.read.1.tlog'));assert len(tlogs)==1
        for line in pin(tlogs[0]).read_text(encoding='utf-16').splitlines():
            path=Path(line.strip().lstrip('^'))
            if path.is_absolute()and path.is_file():consumed.add(pin(path))
        assert all((folder/leaf).resolve()in consumed for leaf in('protocol.hpp','spec.hpp','constructor_normal.hpp','connected_observer.hpp','prerequisite_observer.hpp','format_observer.hpp','original_broker.hpp'))
        counts['actual_compiler_input_files']=len(consumed)
        log=pin(bf/'compile.log').read_text();assert '/MACHINE:X86'in log and '/W4 /WX'in log and '0 Warning(s)'in log and '0 Error(s)'in log
        pin(review_source);pin(prior);pin(R/'tools/m4-constructor-original/run.py');pin(__file__);pin(sys.executable)
        for path,identity in files.items():assert sha(path)==identity
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        path=out/'physical-links.json';path.write_text(json.dumps(links,indent=2)+'\n');pin(path)
        report=dict(passed=passed,scope='Independent physical37-root selected original chronology; all omitted unaccepted slots explicit, actual constructors and source/resource equivalence uncredited before execution',preparation_sha256=PH,build_sha256=BH,counts=dict(counts),worker_launched=False,capture_archive_reader_opened=False,initializer_credit=0,files=files)
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(path),counts=dict(counts),files=len(files))))

if __name__=='__main__':main(sys.argv[1])
