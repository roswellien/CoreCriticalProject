"""Small genuine selected chronology through the third new constructor.

First13 carried roots, new constructors at0038/003C, current MFC at0040,
remaining current131 prefix through009C, then constructor459B40 at00A0.
Preparation/build only; no writer admission or fabricated allocator inputs.
"""
from pathlib import Path
import hashlib,json,re,struct,sys,traceback
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OLD=ROOT/'reports/m4-startup131-original/preparation-r4'
BASE=ROOT/'reports/m4-constructor-original'
def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def need(value,message):
    if not value:raise ValueError(message)
def one(text,old,new):need(text.count(old)==1,'Exact bounded additive hunk '+old[:100]);return text.replace(old,new,1)
def array(text,field,values):
    pattern=r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;';need(len(re.findall(pattern,text))==1,'Exact array '+field)
    return re.sub(pattern,f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',text)
def bridge(name,kind,pc,replay,tail):
    def save(kind,pc):
        return f''' mov ctor_kind,{kind}
 mov DWORD PTR ctor_cpu[0],eax
 mov DWORD PTR ctor_cpu[4],ecx
 mov DWORD PTR ctor_cpu[8],edx
 mov DWORD PTR ctor_cpu[12],ebx
 mov DWORD PTR ctor_cpu[16],esp
 mov DWORD PTR ctor_cpu[20],ebp
 mov DWORD PTR ctor_cpu[24],esi
 mov DWORD PTR ctor_cpu[28],edi
 mov DWORD PTR ctor_cpu[36],0{pc:08x}h
 pushfd
 pop DWORD PTR ctor_cpu[32]
 mov eax,DWORD PTR fs:[0]
 mov ctor_source_head,eax
 mov esp,mixed_host_esp
 cld
 fxsave ctor_fx
 fnstenv ctor_env
 fldenv ctor_env
 call ctor_observe
 fxrstor ctor_fx
 fldenv ctor_env
 push DWORD PTR ctor_cpu[32]
 popfd
 mov eax,DWORD PTR ctor_cpu[0]
 mov ecx,DWORD PTR ctor_cpu[4]
 mov edx,DWORD PTR ctor_cpu[8]
 mov ebx,DWORD PTR ctor_cpu[12]
 mov ebp,DWORD PTR ctor_cpu[20]
 mov esi,DWORD PTR ctor_cpu[24]
 mov edi,DWORD PTR ctor_cpu[28]
 mov esp,DWORD PTR ctor_cpu[16]
'''
    text='PUBLIC '+name+'\n'+name+' PROC\n'+save(kind,pc)
    if replay:text+=' db '+','.join('0'+format(v,'02x')+'h'for v in replay)+'\n'
    if kind==10:text+=save(11,0x40a853)+' db 0c3h\n'
    else:text+=tail+'\n'
    return text+name+' ENDP\n'
def main(name):
    out=BASE/name;need(not out.exists(),'Fresh bounded original constructor preparation');out.mkdir(parents=True);files={}
    def pin(path,expected=None):
        path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.zip'),'No archive opened');digest=sha(path);need(expected is None or digest==expected,'Exact source '+str(path));files[str(path)]=digest;return path
    def read(path,expected=None):return json.loads(pin(path,expected).read_bytes())
    def text(path,expected=None):return pin(path,expected).read_text(encoding='utf-8-sig')
    try:
        parent=read(OLD/'report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb');need(parent['passed'],'Exact authentic current131 worker preparation')
        prerequisite=read(ROOT/'reports/m4-constructor-source/preparation-r1/report.json','0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf');need(prerequisite['passed'],'Genuine current prefix prerequisites, no zero-list substitute')
        contracts=read(ROOT/'reports/m4-constructor-source/preparation-r1/contracts.json');newroots=contracts['roots'];need({r['entry']for r in newroots}=={0x4103f0,0x410440,0x459b40},'Exact three new roots')
        old_order=read(OLD/'selected-order.json');selected=[r for r in old_order if r['slot']<=0x5e00a0]+[dict(entry=r['entry'],slot=r['slot'])for r in newroots];selected.sort(key=lambda row:row['slot'])
        need(len(selected)==37 and [r for r in selected if r['entry']not in {x['entry']for x in newroots}]==old_order[:34],'Entire current34-root selected prefix order retained')
        need(selected[13]['entry']==0x4103f0 and selected[14]['entry']==0x410440 and selected[15]['entry']==0x5ae3e4 and selected[-1]['entry']==0x459b40,'Firsttwo before MFC, third at actual later slot')
        sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
        pin(ROOT/'tools/analysis/pe.py');game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        def physical(pc,width):off,_=game.rva_range(pc-game.image_base,width);return game.data[off:off+width],off
        raw=pin(OLD/'pages.bin',parent['pack_sha256']).read_bytes();count=struct.unpack_from('<I',raw,8)[0];need(len(raw)==12+count*4104,'Exact inherited pack')
        pages={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(count)}
        spans=list(parent['source_spans']);known={row['pc']:row for row in spans};new=[];overlay=[]
        source_rows=read(ROOT/'reports/m4-constructor-source/preparation-r1/source-instructions.json');rows={row['pc']:row for row in source_rows}
        for row in source_rows:
            actual,offset=physical(row['pc'],row['size']);need(actual.hex()==row['bytes'],'Every whole new physical source row')
            if row['pc']in known:need(known[row['pc']]['size']==row['size']and known[row['pc']]['image_offset']==offset and known[row['pc']]['origin']==0,'Inherited whole source identity');continue
            taken=0
            while taken<len(actual):
                address=row['pc']+taken;base=address&~4095;start=address&4095;n=min(len(actual)-taken,4096-start)
                if base not in pages:pages[base]=(1,bytearray(b'\xcc'*4096))
                permission,page=pages[base];need(permission==1 and len(page)==4096,'Fixed whole sparse RX source page')
                previous=bytes(page[start:start+n]);target=actual[taken:taken+n]
                need(all(a==0xcc or a==b for a,b in zip(previous,target)),'Only exact inherited padding/source overlay')
                overlay.append(dict(address=address,old_hex=previous.hex(),source_hex=target.hex(),physical_source_PC=row['pc']))
                page[start:start+n]=target;taken+=n
            span=dict(pc=row['pc'],size=row['size'],image_offset=offset,origin=0);known[row['pc']]=span;spans.append(span);new.append(span)
        getter_raw,getter_offset=physical(0x40a850,5)
        need(getter_raw[:4]==bytes.fromhex('8b4104c3'),'Whole physical getter body')
        # The fifth hook byte is actual unreachable padding after the source
        # RET. It is a physical input, never a claimed reached instruction.
        base=0x40a000;page=pages[base][1];need(page[0x854]in(0xcc,getter_raw[4]),'Exact sparse getter padding')
        overlay.append(dict(address=0x40a854,old_hex=bytes([page[0x854]]).hex(),source_hex=getter_raw[4:].hex(),physical_source_PC=0x40a854,scope='Unexecuted physical padding beyond getterRET'))
        page[0x854]=getter_raw[4]
        padding=dict(pc=0x40a854,size=1,image_offset=getter_offset+4,origin=0,scope='Unexecuted physical padding beyond sourceRET')
        need(padding['pc']not in known,'Independent getter padding span')
        spans.append(padding);new.append(padding)
        need(all(len(v)==4096 for _,v in pages.values()),'No instruction extends a sparse page')
        for row in selected:
            value,_=physical(row['slot'],4);need(value==struct.pack('<I',row['entry'])and pages[row['slot']&~4095][1][row['slot']&4095:(row['slot']&4095)+4]==value,'Exact physical startup cell')
        pack=raw[:8]+struct.pack('<I',len(pages))+b''.join(struct.pack('<2I',base,perm)+page for base,(perm,page)in pages.items());need(len(pack)==12+len(pages)*4104,'Exact final pack geometry');(out/'pages.bin').write_bytes(pack)
        spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
        for field,values in(('entries',[r['entry']for r in selected]),('table_slots',[r['slot']for r in selected]),('page_bases',list(pages)),('page_permissions',[v[0]for v in pages.values()])):spec=array(spec,field,values)
        pattern=r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;';need(len(re.findall(pattern,spec))==1,'Exact complete source-binding declaration');spec=re.sub(pattern,f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(row[key])for key in('pc','size','image_offset','origin'))+'}'for row in spans)+'}};',spec);(out/'spec.hpp').write_text(spec)
        protocol=one(text(OLD/'protocol.hpp'),'sequences=6, roots=131','sequences=6, roots=37')
        protocol=one(protocol,'memory_size==151552','memory_size==176128')
        (out/'protocol.hpp').write_text(protocol)
        for file in('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer_x86.asm','format_observer.hpp','boundaries.asm','api_boundaries.asm','connected_observer.hpp','prerequisite_observer.hpp'):(out/file).write_text(text(OLD/file))
        broker=text(OLD/'original_broker.hpp');match=re.search(r'inline constexpr std::array<std::uint32_t,(\d+)> bases\{([^;]+)\};',broker);need(match is not None,'Exact pre-CRT reservation inventory')
        bases={int(value,16)for value in match[2].split(',')};newbases={base&~65535 for base in pages}-bases
        if newbases:
            allbases=sorted(bases|newbases);broker=one(broker,match[0],f'inline constexpr std::array<std::uint32_t,{len(allbases)}> bases{{'+','.join(hex(v)for v in allbases)+'};')
        (out/'original_broker.hpp').write_text(broker)
        bindings=read(OLD/'fs-hook-bindings.json');oldpcs={row['PC']for row in bindings};fsnew=[]
        for row in source_rows:
            if 'fs:'not in row['operands']or row['pc']in oldpcs:continue
            kinds={'64a100000000':0,'64892500000000':1,'64890d00000000':2};need(row['bytes']in kinds,'Supported exact normal FS replay');fsnew.append(dict(PC=row['pc'],kind=kinds[row['bytes']],raw_bytes=row['bytes'],continuation=row['pc']+row['size'],declared_observer=f'fs_hook_{row["pc"]:x}'))
        fsasm=text(OLD/'fs_observer_x86.asm');template=re.search(r'PUBLIC fs_hook_4e78d7\nfs_hook_4e78d7 PROC\n.*?fs_hook_4e78d7 ENDP\n',fsasm,re.S)[0];generated=[]
        for row in fsnew:
            generated.append(template.replace('4e78d7',f'{row["PC"]:x}').replace(' mov fs_event_kind,0',f' mov fs_event_kind,{row["kind"]}').replace(' db 064h,0a1h,000h,000h,000h,000h',' db '+','.join('0'+format(v,'02x')+'h'for v in bytes.fromhex(row['raw_bytes']))))
        fsasm=one(fsasm,'.code\n','\n'.join(f'EXTERN fs_continue_{row["PC"]:x}:DWORD'for row in fsnew)+'\n.code\n');fsasm=one(fsasm,'END\n',''.join(generated)+'END\n');(out/'fs_observer_x86.asm').write_text(fsasm)
        (out/'fs-hook-bindings.json').write_text(json.dumps(bindings+fsnew,indent=2)+'\n')
        allocations=contracts['allocation_CALL_sites'];return_hooks=[]
        for index,binding in enumerate(allocations):
            ret=binding['return_PC'];position=ret;replay=b''
            while len(replay)<5:
                row=rows[position];need(row['mnemonic']not in('call','jmp','ret')and not row['mnemonic'].startswith('j'),'Exact straight-line MFC return replay');replay+=bytes.fromhex(row['bytes']);position+=row['size']
            return_hooks.append(dict(kind=index+1,CALL_PC=binding['CALL_PC'],return_PC=ret,continuation=position,raw_bytes=replay.hex(),symbol=f'ctor_return_{ret:x}'))
        getter,offset=physical(0x40a850,5);need(getter[:4]==bytes.fromhex('8b4104c3'),'Exact getter MOV/RET plus physical padding')
        asm='.686p\n.xmm\n.model flat,C\nassume fs:nothing\noption casemap:none\n'+'\n'.join('EXTERN '+name+':'+kind for name,kind in [('mixed_host_esp','DWORD'),('ctor_cpu','BYTE'),('ctor_fx','BYTE'),('ctor_env','BYTE'),('ctor_kind','DWORD'),('ctor_source_head','DWORD'),('ctor_MFC_target','DWORD'),('ctor_observe','PROC')])+'\n'+'\n'.join(f'EXTERN ctor_continue_{row["return_PC"]:x}:DWORD'for row in return_hooks)+'\n.code\n'
        asm+=bridge('ctor_MFC_entry',0,0x5f401eb0,b'',' jmp DWORD PTR ctor_MFC_target')
        for row in return_hooks:asm+=bridge(row['symbol'],row['kind'],row['return_PC'],bytes.fromhex(row['raw_bytes']),f' jmp DWORD PTR ctor_continue_{row["return_PC"]:x}')
        asm+=bridge('ctor_getter_bridge',10,0x40a850,bytes.fromhex('8b4104'),'')+'END\n';(out/'constructor_observer_x86.asm').write_text(asm)
        declarations='extern \"C\" void ctor_getter_bridge();\nstruct ConstructorAllocSite {unsigned CALL_PC,return_PC;};\ninline constexpr std::array<ConstructorAllocSite,'+str(len(return_hooks))+'>constructor_alloc_sites{{'+','.join('{'+hex(row['CALL_PC'])+','+hex(row['return_PC'])+'}'for row in return_hooks)+'}};\n'
        declarations+='\n'.join(f'extern "C" void {row["symbol"]}();\nextern "C" const unsigned ctor_continue_{row["return_PC"]:x}={hex(row["continuation"])};'for row in return_hooks)+'\n'
        declarations+='struct ConstructorPatch {unsigned pc,size;void(*entry)();unsigned char raw[8];};\nconst std::array<ConstructorPatch,'+str(len(return_hooks)+1)+'>constructor_patches{{'+','.join('{'+hex(row['return_PC'])+','+str(len(bytes.fromhex(row['raw_bytes'])))+',&'+row['symbol']+',{' +','.join(hex(v)for v in bytes.fromhex(row['raw_bytes']))+'}}'for row in return_hooks)+',{0x40a850,5,&ctor_getter_bridge,{'+','.join(hex(v)for v in getter)+'}}}};\n'
        declarations+=text(HERE/'normal_observer_v2.hpp');(out/'constructor_normal.hpp').write_text(declarations)
        ref=text(OLD/'reference.cpp');ref=one(ref,'#include "prerequisite_observer.hpp"','#include "prerequisite_observer.hpp"\n#include "constructor_normal.hpp"')
        declarations='\n'.join(f'extern "C" void fs_hook_{row["PC"]:x}();\nextern "C" const unsigned fs_continue_{row["PC"]:x}={hex(row["continuation"])};'for row in fsnew)+'\n'
        ref=one(ref,'struct FsHook{',declarations+'struct FsHook{');pattern=r'const std::array<FsHook,63> fs_hooks\{\{[^;]+;';need(len(re.findall(pattern,ref))==1,'Exact inherited FS table')
        table='const std::array<FsHook,'+str(len(bindings+fsnew))+'> fs_hooks{{'+','.join('{'+hex(row['PC'])+','+str(len(bytes.fromhex(row['raw_bytes'])))+','+str(row['kind'])+',&fs_hook_'+format(row['PC'],'x')+',{'+','.join(hex(v)for v in bytes.fromhex(row['raw_bytes']))+'}}'for row in bindings+fsnew)+'}};';ref=re.sub(pattern,lambda _:table,ref)
        ref=one(ref,'std::array<void*,134> pages',f'std::array<void*,{len(pages)}> pages')
        ref=one(ref,'require(phase==13,"Actual chronology has13 carried roots before MFC")','require(phase==15,"Actual chronology has13 carried roots plus2 new constructors before MFC")')
        ref=one(ref,'copy_pages(r->memory_before);','copy_pages(r->memory_before);\n            const bool constructor_phase=constructor_is_root(entries[phase]);if(constructor_phase){constructor_graph(phase_stem+"/BEFORE-constructor");constructor_member_graph(phase_stem+"/BEFORE-member");constructor_whole_live_owners(phase_stem+"/BEFORE-owners");constructor_normal_count=0;std::memset(constructor_normal_records,0,sizeof(constructor_normal_records));}')
        install='''            if(constructor_phase){const unsigned actual=dword(0x5bb4bc);require(actual==ctor_MFC_target,"Actual original823 named owning target before temporary observer");DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb4bc),4,PAGE_READWRITE,&prior),"Temporary constructor MFC import observer");*reinterpret_cast<unsigned*>(0x5bb4bc)=reinterpret_cast<unsigned>(&ctor_MFC_entry);require(VirtualProtect(reinterpret_cast<void*>(0x5bb4bc),4,prior,&ignored),"Constructor import permissions restored");for(const auto&hook:constructor_patches){require(!std::memcmp(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size),"Exact new source before bounded normal patch");require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,PAGE_EXECUTE_READWRITE,&prior),"Constructor source observer permissions");auto*code=reinterpret_cast<unsigned char*>(hook.pc);code[0]=0xe9;const unsigned ctor_patch_delta=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&ctor_patch_delta,4);for(unsigned i=5;i<hook.size;++i)code[i]=0x90;require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"Constructor observer final permissions");}}
'''
        ref=one(ref,'            if(mfc_phase){named_IAT(true);connected_patch_sources(true);}',install+'            if(mfc_phase){named_IAT(true);connected_patch_sources(true);}')
        restore='''if(constructor_phase){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb4bc),4,PAGE_READWRITE,&prior),"Restore exact original823 named target");*reinterpret_cast<unsigned*>(0x5bb4bc)=ctor_MFC_target;require(VirtualProtect(reinterpret_cast<void*>(0x5bb4bc),4,prior,&ignored),"Restore original823 permissions");for(const auto&hook:constructor_patches){require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,PAGE_EXECUTE_READWRITE,&prior),"Restore actual constructor source");std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size);require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(hook.pc),hook.size),"Constructor original source permissions");}constructor_normal_dump(phase_stem+"/normal");}'''
        ref=one(ref,'copy_capture(*r);if(mfc_phase)', 'copy_capture(*r);'+restore+'if(mfc_phase)')
        ref=one(ref,'            if(phase<13)constructor_collect(phase,phase_stem);','            constructor_collect(phase,phase_stem);if(constructor_phase){constructor_graph(phase_stem+"/AFTER-constructor");constructor_member_graph(phase_stem+"/AFTER-member");constructor_whole_live_owners(phase_stem+"/AFTER-owners");}')
        ref=one(ref,'const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");','ctor_MFC_target=reinterpret_cast<unsigned>(GetProcAddress(mfc,reinterpret_cast<LPCSTR>(823)));require(ctor_MFC_target==0x5f401eb0,"Actual named ordinal823 physical entry");const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");')
        # The same genuine source cleanup is restricted to roots that actually
        # ran. Fresh new owners are separately observed/freed, never invented.
        ref=one(ref,'require(container_allocation_count==5,"Five genuine new positive vector allocations")','require(container_allocation_count<=5,"Bounded genuinely selected vector allocations")')
        ref=one(ref,'require(fs_allocation_count==10,"Exact ten genuine FS allocations")','require(fs_allocation_count<=10,"Bounded genuinely selected FS allocations")')
        ref=one(ref,'const auto&binding=mfc_bindings[mi];const auto pointer=', 'const auto&binding=mfc_bindings[mi];if(std::find(entries.begin(),entries.end(),binding.root)==entries.end())continue;const auto pointer=')
        ref=one(ref,'for(const auto&binding:string_bindings){const auto pointer=', 'for(const auto&binding:string_bindings){if(std::find(entries.begin(),entries.end(),binding.entry)==entries.end())continue;const auto pointer=')
        cleanup='''        for(auto&v:constructor_occurrences)if(v.alive&&v.phase<entries.size()&&constructor_is_root(entries[v.phase])){const auto stem="cleanup/"+std::to_string(sequence)+"/constructor-owner-"+std::to_string(v.serial);out.append(stem+"/meta.bin",&v,sizeof(v));out.append(stem+"/before.bin",reinterpret_cast<void*>(v.pointer),v.capacity);mfc825(reinterpret_cast<void*>(v.pointer));const unsigned returned=1;out.append(stem+"/returned.bin",&returned,4);v.alive=0;}
'''
        ref=one(ref,'        out.append("cleanup/"+std::to_string(sequence)+"/mixed-owner-count.bin",',cleanup+'        out.append("cleanup/"+std::to_string(sequence)+"/mixed-owner-count.bin",')
        # Recover exact selected callbacks from the existing root metadata.
        callback_paths=[('m4-onexit-batch-recovery/recovery-r3/registration-roots.json',None),('m4-strings-source/recovery-r7/string-roots.json',None),('m4-mfc-source/recovery-r4/mfc-roots.json',None),('m4-fs-source/recovery-r3/fs-roots.json',None),('m4-container-source/recovery-r3/container-roots.json',None),('m4-next-source/recovery-r1/instruction-contracts.json','roots'),('m4-lockit-source/recovery-r1/Lockit-roots.json',None)]
        callback_map={}
        for relative,key in callback_paths:
            values=read(ROOT/'reports'/relative);values=values[key]if key else values
            for row in values:callback_map[row['entry']]=row['registration']['callback']
        for row in newroots:callback_map[row['entry']]=row['callback']
        callbacks=[callback_map[row['entry']]for row in selected if row['entry']in callback_map];need(len(callbacks)>13,'Genuine three new registrations and entire selected prefix')
        ref=one(ref,'require(*crtnext-*crtbegin==101*4,"Exact101callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),101*4);',f'require(*crtnext-*crtbegin=={len(callbacks)}*4,"Exact selected-prefix callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),{len(callbacks)}*4);')
        ref=ref.replace('Original131','Constructor37').replace('original131','constructor37').replace('MW4J131','MW4C037').replace('/786 actual original initializer phases','/222 actual original initializer phases');(out/'reference.cpp').write_text(ref)
        (out/'CMakeLists.txt').write_text(one(text(OLD/'CMakeLists.txt'),'api_boundaries.asm "','api_boundaries.asm constructor_observer_x86.asm "'))
        patches=[dict(family='FS',PC=row['PC'],size=len(bytes.fromhex(row['raw_bytes'])),raw=row['raw_bytes'])for row in bindings+fsnew]
        patches+=[dict(family='constructor-return',PC=row['return_PC'],size=len(bytes.fromhex(row['raw_bytes'])),raw=row['raw_bytes'])for row in return_hooks]+[dict(family='constructor-getter',PC=0x40a850,size=5,raw=getter.hex())]
        oldcontracts=read(OLD/'contracts.json');patches+=oldcontracts['active_new_code_patches']+[row for row in oldcontracts['inherited_active_code_patches']if row['family']!='FS']
        for i,a in enumerate(patches):
            for b in patches[i+1:]:need(a['PC']+a['size']<=b['PC']or b['PC']+b['size']<=a['PC'],'All bounded normal active source patches disjoint')
        artifacts={'selected-order.json':selected,'source-overlay.json':overlay,'constructor-hook-bindings.json':return_hooks,
                   'contracts.json':dict(selected_order=selected,parent131_selected_prefix=old_order[:34],new_roots=newroots,root_frame=0x20001800,callback_values=callbacks,sequences=6,source_pages46=parent['observed_pages']+[0x5cd000,0x5e3000,0x5e9000],new_source_spans=new,normal_patch_spans=patches,
                                         source_MFC_entry_target=0x5f401eb0,MFC1168_phase=15,borrowed_MFC_domain='Untouched chronological state after13 carried roots and2 actual constructors, not reused isolated AFTER',
                                         whole_owner_policy='Every genuine HeapAlloc-return capacity/initial backing plus actual source-published list/vector/member role and occurrence identity; no OS generation claim',
                                         normal_boundary_scope='Actual MFC callee entry and game CALL returns; getter entry and source preRET at40A853; postRET derived only',
                                         new_constructor_counts_unmeasured=True,third_root_selected_chronology='After all34 current131 roots with slot<5E00A0 plus firsttwo new roots; outstanding widget slots remain explicitly unexecuted',
                                         omitted_unaccepted_widget_slots=[0x5e0048,0x5e004c,0x5e0050],source_AFTER_seed=False,new_callback_shutdown_executed=False,trace_admitted=False,
                                         trace_prerequisite='Separate physically reviewed descriptor union, exhaustive all-source-hook overlap removal, validate-all-before-INT3, CONTROL-only debugger writes',new_preCRT_reservation_bases=sorted(newbases))}
        for filename,value in artifacts.items():p=out/filename;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
        for path in(out.iterdir()):pin(path)
        pin(__file__);pin(HERE/'prepare_chronological.py');pin(HERE/'prepare_chronological_v2.py');pin(HERE/'derive_chronological_v2.py');pin(HERE/'derive_chronological_v3.py');pin(HERE/'prepare_chronological_v3.py');pin(HERE/'derive_chronological_v4.py');pin(HERE/'prepare_chronological_v4.py');pin(HERE/'derive_chronological_v5.py');pin(HERE/'normal_observer.hpp');pin(ROOT/'tools/m4-capture-direct/capture_direct_v3.cpp');pin(ROOT/'tools/m4-capture-direct/capture_direct_v3.hpp')
        report=dict(passed=True,scope='Preparation-only smallest current selected chronology through three new constructors; first13 untouched inputs, first2newroots, current MFC and later own third-root BEFORE',parent_preparation_sha256=sha(OLD/'report.json'),prerequisite_preparation_sha256=sha(ROOT/'reports/m4-constructor-source/preparation-r1/report.json'),selected_order=selected,source_spans=spans,observed_pages=parent['observed_pages'],original_sequences=6,original_roots=37,original_phases=222,callback_count=len(callbacks),record_bytes=356992,pack_sha256=sha(out/'pages.bin'),pack_bytes=len(pack),sparse_pack_pages=len(pages),FS_hooks=len(bindings+fsnew),constructor_normal_record_bytes=189108,normal_WRAPPER_functions=10,source_frame=0x20001800,new_source_rows=len(new),new_physical_reservation_bases=sorted(newbases),writer_executed=False,writer_admitted=False,capture_archive_opened=False,initializer_credit=0,files=files)
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');files[str(p.resolve())]=sha(p);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),roots=37,phases=222,pages=len(pages),new_rows=len(new))))
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
