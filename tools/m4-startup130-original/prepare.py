"""Full130 genuine original preparation; execution never consumes expected effects."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-startup130-original'
OLD=ROOT/'reports/m4-tree-original/original125-preparation-r1'
MIX=ROOT/'reports/m4-mixed-format-original/prefix-preparation-r1'
COS=ROOT/'reports/m4-cosine-original/preparation-r2'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(s,a,b):
 need(s.count(a)==1,'Exact additive source anchor '+a[:90]);return s.replace(a,b,1)
def array(s,field):return[int(v,16)for v in re.search(r' '+field+r'\{([^;]+)\};',s)[1].split(',')]
def arr(s,field,values):
 return re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',s)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No inherited canonical capture reader');v=sha(p);need(h is None or h==v,'Exact physical source '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable pinned identity');pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def report(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=report(OLD/'report.json','6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1')
 mix=report(MIX/'report.json','9a770096b8f19c794e150771a7578832a30a333a65f93619882895769930a779')
 cos=report(COS/'report.json','aac031ac5949fa6fb1698c63130aa2652f352e521e140c02034fcb5df9f492df')
 for parent in(old,mix,cos):
  for p,h in parent['files'].items():pin(p,h)
 measured=[('reports/m4-mixed-format-original/original-source-r7/report.json','3a30f008243812bc5205487cbb08265e4ab9fd1e0e8377cb7ccd176230929823'),('reports/m4-mixed-format-original/linked-observer-r2/report.json','f736dd6b086964f6a96b23d5ce6d6174e0a8be88b4cfeebb49bbd445de91a335'),('reports/m4-cosine-original/validation-r2/report.json','cee385275cfd924366a867fc4442cf0fe78bae47af136d3b9569e0ace9952b4e'),('reports/m4-formatting-original/trace-validation-r1/report.json','441a584515859cce4b2636bf9e2e5b2d64220c3c88248eef47b7bf06f6bafbf9')]
 for p,h in measured:need(report(ROOT/p,h)['passed'],'Bounded actual first-prefix prerequisite')
 spec=text(OLD/'spec.hpp');oldpairs=list(zip(array(spec,'table_slots'),array(spec,'entries')))
 added=[(0x5e0160,0x4b64f0),(0x5e01c8,0x4df610),(0x5e01cc,0x4e0710),(0x5e01d0,0x4e0810),(0x5e01d4,0x4e1ca0)]
 pairs=sorted(oldpairs+added);need(len(pairs)==130 and[p for p in pairs if p not in added]==oldpairs,'Exact accepted125 relative order retained')
 sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 cp=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').read_bytes())
 for slot,entry in pairs:
  offset,_=game.rva_range(slot-game.image_base,4);need(struct.unpack_from('<I',game.data,offset)[0]==entry,'Every root selected from physical startup table')
 raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',raw,8)[0])}
 mixraw=pin(MIX/'pages.bin',mix['pack_sha256']).read_bytes();mixpages={struct.unpack_from('<I',mixraw,12+i*4104)[0]:(struct.unpack_from('<I',mixraw,16+i*4104)[0],bytearray(mixraw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',mixraw,8)[0])}
 extras=[0x5cd000,0x5e3000,0x5e9000]
 for page in extras:
  need(page not in records and page in mixpages,'Exactly three additive complete asset pages');records[page]=mixpages[page]
 spans=list(old['source_spans']);known={r['pc']:r for r in spans}
 for parent in(mix,cos):
  for r in parent['source_spans']:
   image=cp if r['origin']else game;offset,_=image.rva_range(r['pc']-image.image_base,r['size']);need(offset==r['image_offset'],'Every code binding derives physical image extent');code=image.data[offset:offset+r['size']]
   if r['pc']in known:need(all(known[r['pc']][k]==r[k]for k in('pc','size','image_offset','origin')),'Exact inherited shared instruction');continue
   need(not r['origin'],'No new provider source implementation in original sparse game image');page=r['pc']&~4095
   if page not in records:records[page]=(1,bytearray(b'\xcc'*4096))
   records[page][1][r['pc']&4095:(r['pc']&4095)+r['size']]=code;spans.append(r);known[r['pc']]=r
 section=next(s for s in game.sections if game.image_base+s['virtual_address']<=0x5e8000<game.image_base+s['virtual_address']+max(s['raw_size'],s['virtual_size']))
 need(section['writable'],'Physical cosine source output page belongs to writable game data');records[0x5e8000]=(2,records[0x5e8000][1])
 out.mkdir(parents=True);pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,permission)+data for p,(permission,data)in records.items());(out/'pages.bin').write_bytes(pack)
 for field,values in [('entries',[e for s,e in pairs]),('table_slots',[s for s,e in pairs]),('page_bases',list(records)),('page_permissions',[p for p,d in records.values()])]:spec=arr(spec,field,values)
 spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(r[k])for k in('pc','size','image_offset','origin'))+'}'for r in spans)+'}};',spec)
 spec=one(spec,'std::array<LockitRoot,5>lockit_roots','std::array<LockitRoot,6>lockit_roots');spec=one(spec,'{0x4b7f70,0x60b2f8,0x60b314,0x60b318,24}}};','{0x4b7f70,0x60b2f8,0x60b314,0x60b318,24},{0x4e1ca0,0x60b668,0x60b7d4,0x60b7d0,24}}};')
 (out/'spec.hpp').write_text(spec);(out/'protocol.hpp').write_text(one(text(OLD/'protocol.hpp'),'sequences=6, roots=125','sequences=6, roots=130'))
 broker=text(OLD/'original_broker.hpp');bases=list(dict.fromkeys([int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')]+[p&~65535 for p in records]));broker=re.sub(r'std::array<std::uint32_t,\d+> bases\{[^;]+;',f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(v)for v in bases)+'};',broker);(out/'original_broker.hpp').write_text(broker)
 ref=text(OLD/'reference.cpp');mixedref=text(MIX/'reference.cpp');ref=re.sub(r'std::array<void\*,\d+> pages',f'std::array<void*,{len(records)}> pages',ref)
 contract=report(ROOT/'reports/m4-mixed-format-original/recovery-r1/instruction-contracts.json')
 newhooks=[(f[k],kind,'64a100000000'if kind==0 else'64892500000000'if kind==1 else'64890d00000000')for f in contract['FS_frame_contracts']for k,kind in [('read',0),('install',1),('restore',2)]]
 oldhooks=report(OLD/'fs-hook-bindings.json');allhooks=[(x['PC'],x['kind'],x['raw_bytes'])for x in oldhooks]+newhooks;need(len(allhooks)==63 and len({x[0]for x in allhooks})==63,'57 inherited +6 mixed physical FS observer sites')
 p=pin(ROOT/'tools/m4-fs-source/fs_hooks_v2.py');module_spec=importlib.util.spec_from_file_location('full130_fs_generator',p);fs=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(fs)
 fs.HOOKS=newhooks;ref=one(ref,'struct FsHook{',fs.declarations()+'struct FsHook{');fs.HOOKS=allhooks;table=fs.hook_table().replace('FsHook,9>','FsHook,'+str(len(allhooks))+'>');ref,n=re.subn(r'struct FsHook\{[^\n]+\nconst std::array<FsHook,57> fs_hooks\{\{[^;]+;',lambda m:table.rstrip(),ref);need(n==1,'Exact full FS table replacement');(out/'fs_observer_x86.asm').write_text(fs.asm());(out/'fs-hook-bindings.json').write_text(json.dumps([dict(PC=pc,kind=k,raw_bytes=b,continuation=pc+len(bytes.fromhex(b)),declared_observer=f'fs_hook_{pc:x}')for pc,k,b in allhooks],indent=2)+'\n')
 ref=one(ref,'void lockit_observe_allocation(unsigned,unsigned,unsigned);','void lockit_observe_allocation(unsigned,unsigned,unsigned);\nvoid mixed_observe_allocation(unsigned,unsigned,unsigned);')
 ref=one(ref,'lockit_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));','lockit_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));mixed_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));')
 implementation=mixedref[mixedref.index('struct MixedAllocation{'):mixedref.index('#include "format_observer.hpp"')]
 implementation=one(implementation,'unsigned mixed_allocation_count{};','unsigned mixed_allocation_count{};unsigned mixed_owner_heaps[8]{};unsigned char mixed_owner_initial[8][1024]{};')
 implementation=one(implementation,'e.API_index=ai;e.pointer=pointer;e.capacity=capacity;','e.API_index=ai;e.pointer=pointer;e.capacity=capacity;mixed_owner_heaps[e.index]=registry_API_ledger[ai].args[0];std::memcpy(mixed_owner_initial[e.index],registry_initial_bytes[ai],capacity);')
 ref=one(ref,'static std::uint32_t execute(){',implementation+'\n#include "format_observer.hpp"\nstatic std::uint32_t execute(){')
 header=text(MIX/'format_observer.hpp');header=one(header,' const auto last_error=GetLastError();',' if(fs_phase_root!=0x4df610&&fs_phase_root!=0x4e0710&&fs_phase_root!=0x4e0810&&fs_phase_root!=0x4e1ca0)return;\n const auto last_error=GetLastError();');(out/'format_observer.hpp').write_text(header)
 install=mixedref[mixedref.index('const std::array<unsigned,3> format_iats'):mixedref.index('unsigned sequence{};',mixedref.index('const std::array<unsigned,3> format_iats'))]
 # Named targets are admitted once; source imports and return patches are restored/reinstalled per complete sequence.
 install=install[:install.index('    out.append("formatting/import-targets.bin"')]
 target_loop=install[install.index('    for(unsigned i=0;i<3;++i)'):install.index('    for(const auto&hook:format_hooks)')]
 hook_loop=install[install.index('    for(const auto&hook:format_hooks)'):install.index('    const std::array<unsigned,3> format_extra_pages')]
 install='const std::array<unsigned,3> format_iats{0x5bb5a8,0x5bb664,0x5bb658};const std::array<const char*,3> format_names{"strrchr","malloc","sprintf"};const std::array<void(*)(),3> format_entries{&format_entry_strrchr,&format_entry_malloc,&format_entry_sprintf};\n    const std::array<unsigned,3> format_extra_pages{0x5cd000,0x5e3000,0x5e9000};\n    for(unsigned i=0;i<3;++i){format_targets[i]=reinterpret_cast<unsigned>(GetProcAddress(crt,format_names[i]));require(format_targets[i]==(i==0?0x780264a9u:i==1?0x780012b3u:0x78022b9au),"Exact named formatting CRT exports");}\n    out.append("formatting/import-targets.bin",format_targets,sizeof(format_targets));\n    const auto install_format_hooks=[&](){\n'+target_loop+hook_loop+'    };\n'
 ref=one(ref,'unsigned sequence{};',install+'    unsigned sequence{};')
 ref=one(ref,'        lockit_allocation_count=0;','        mixed_allocation_count=0;std::memset(mixed_allocations,0,sizeof(mixed_allocations));std::memset(mixed_owner_heaps,0,sizeof(mixed_owner_heaps));std::memset(mixed_owner_initial,0,sizeof(mixed_owner_initial));format_owner_count=0;std::memset(format_owners,0,sizeof(format_owners));\n        lockit_allocation_count=0;')
 ref=one(ref,'        for(unsigned phase=0;phase<entries.size();++phase){','        install_format_hooks();\n        for(unsigned phase=0;phase<entries.size();++phase){')
 before='''            format_count=0;format_active_owner=0xffffffff;std::memset(format_snapshots,0,sizeof(format_snapshots));
            for(auto page:format_extra_pages)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/extra-before/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);
            const bool format_phase=entries[phase]==0x4df610||entries[phase]==0x4e0710||entries[phase]==0x4e0810||entries[phase]==0x4e1ca0;
            const auto crt_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/CRT-image/";std::vector<unsigned> crt_pages_metadata;
            if(format_phase){for(unsigned page=0x78000000;page<0x78040000;page+=4096){MEMORY_BASIC_INFORMATION region{};require(VirtualQuery(reinterpret_cast<void*>(page),&region,sizeof(region))==sizeof(region),"Actual current CRT page query");const auto flags=region.Protect;if(region.State!=MEM_COMMIT||(flags&(PAGE_NOACCESS|PAGE_GUARD)))continue;crt_pages_metadata.push_back(page);crt_pages_metadata.push_back(flags);crt_pages_metadata.push_back(region.Type);out.append(crt_stem+"before/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);}out.append(crt_stem+"metadata.bin",crt_pages_metadata.data(),crt_pages_metadata.size()*4);}
'''
 ref=one(ref,'            if(entries[phase]==0x4b7f70)',before+'            if(entries[phase]==0x4b7f70)')
 dump=mixedref[mixedref.index('            const auto mixed_stem='):mixedref.index('            const auto lockbase=')]
 dump=one(dump,'reinterpret_cast<HANDLE>(registry_API_ledger[a.API_index].args[0])','reinterpret_cast<HANDLE>(mixed_owner_heaps[a.index])');dump=one(dump,'registry_initial_bytes[a.API_index],a.capacity','mixed_owner_initial[a.index],a.capacity')
 dump+='            for(unsigned i=0;i<crt_pages_metadata.size();i+=3)out.append(crt_stem+"after/"+std::to_string(crt_pages_metadata[i])+".bin",reinterpret_cast<void*>(crt_pages_metadata[i]),4096);\n'
 ref=one(ref,'            const auto lockbase=',dump+'            const auto lockbase=')
 restore=mixedref[mixedref.index('        for(const auto&hook:format_hooks){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(hook.pc)'):mixedref.index('        for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;bool hooked')]
 ref=one(ref,'        for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;bool hooked',restore+'        for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;bool hooked')
 ref=one(ref,'require(*crtnext-*crtbegin==97*4,"Exact97callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),97*4);','require(*crtnext-*crtbegin==101*4,"Exact101callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),101*4);')
 cleanup=mixedref[mixedref.index('        out.append("cleanup/mixed-owner-count.bin"'):mixedref.index('        require(!std::memcmp(mfc540_loaded_page',mixedref.index('        out.append("cleanup/mixed-owner-count.bin"'))]
 cleanup=cleanup[:cleanup.index('original_free(reinterpret_cast<void*>(*crtbegin));')]
 cleanup=cleanup.replace('"cleanup/mixed-owner-count.bin"','"cleanup/"+std::to_string(sequence)+"/mixed-owner-count.bin"').replace('"cleanup/mixed/"','"cleanup/"+std::to_string(sequence)+"/mixed/"').replace('"cleanup/formatting-owner-count.bin"','"cleanup/"+std::to_string(sequence)+"/formatting-owner-count.bin"').replace('"cleanup/formatting/"','"cleanup/"+std::to_string(sequence)+"/formatting/"')
 ref=one(ref,'        require(lockit_allocation_count>0',cleanup+'        require(lockit_allocation_count>0')
 ref=ref.replace('Original125','Original130').replace('Connected original125','Connected original130').replace('MW4J125D','MW4J130D').replace('MW4J125O','MW4J130O').replace('6 connected sequences /750 actual original initializer phases captured','6 connected sequences /780 actual original initializer phases captured')
 (out/'reference.cpp').write_text(ref)
 for fn in('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm'):(out/fn).write_text(text(OLD/fn))
 (out/'format_observer_x86.asm').write_text(text(MIX/'format_observer_x86.asm'));(out/'CMakeLists.txt').write_text(one(text(OLD/'CMakeLists.txt'),'lockit_observer_x86.asm "${MW34_WRITER_SOURCE}"','lockit_observer_x86.asm format_observer_x86.asm "${MW34_WRITER_SOURCE}"'))
 selected=[dict(phase=i,slot=s,entry=e)for i,(s,e)in enumerate(pairs)];(out/'selected-order.json').write_text(json.dumps(selected,indent=2)+'\n')
 pin(__file__)
 for p in out.iterdir():pin(p)
 result=dict(passed=True,scope='Full130 genuine original persistent sequence preparation; exact accepted125 relative order plus independently measured formatter3/mixed/FCOS source. Execution and credit pending.',parent_preparation_sha256=sha(OLD/'report.json'),prerequisite_receipts=dict(measured),original_sequences=6,original_roots=130,original_phases=780,callback_count=101,record_bytes=356992,ordinary_record_pages=43,extra_whole_source_pages=extras,combined_source_page_count=46,source_spans=spans,observed_pages=old['observed_pages'],pack_sha256=sha(out/'pages.bin'),sparse_pack_pages=len(records),FS_hooks=63,selected_order=selected,added_root_phases=[r for r in selected if(r['slot'],r['entry'])in added],format_event_bytes=2244,format_owner_bytes=1088,mixed_owner_meta_bytes=68,actual_API_initial_inputs_copied_at_return=True,owner_initial_storage_persistent_per_sequence=True,format_IAT_and_return_hooks_restored_each_sequence=True,format_observers_transparent_outside_selected_four_roots=True,CRT_whole_current_pages_captured_for_four_format_roots=True,predicted_counts_supplied_to_execution=False,source_output_seed=False,source_permission_update=dict(page=0x5e8000,from_permission=0,to_permission=2,physical_section=section['name']),original_execution_pending=True,native_executed=False,initializer_credit=False,inherited_capture_reader_opened=False,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),roots=130,phases=780,pages=len(records),FS_hooks=63)))
if __name__=='__main__':main(sys.argv[1])
