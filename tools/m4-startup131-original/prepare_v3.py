"""Authentic full131 original, preserving130 chronology and genuine MFC domain.

Constructor5F2000/shared-header observations are separate prerequisite exports;
no additional initializer is executed and no observed value seeds the worker.
"""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent;B=R/'reports/m4-startup131-original'
OLD=R/'reports/m4-startup130-original/preparation-r2';MFC=R/'reports/m4-mfc1168-connected-original/preparation-r3'
sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact additive source hunk '+a[:100]);return s.replace(a,b,1)
def array(s,field,values):
 p=r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;';need(len(re.findall(p,s))==1,'Exact array '+field);return re.sub(p,f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',s)
def main(name):
 out=B/name;need(not out.exists(),'Fresh full131 original preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture archive');v=sha(p);need(h is None or v==h,'Physical input '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def data(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=data(OLD/'report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814');mfc=data(MFC/'report.json','4f3510adc78d8766df79c9cd1c56bd1de754a483444d1caf3015e208f43850e1');need(old['passed']and mfc['passed'],'Immutable full130 and chronological MFC preparations')
 native=data(R/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25');need(native['passed'],'Exact connected131 candidate schedule')
 source=data(R/'reports/m4-mfc1168-connected-original/source-r3/report.json','3afcb5f1669726f43fa4c86a23eb1af8349dae1710e63ca7e87271a4fa1907d0');need(source['passed'],'Genuine current first13 to MFC literal domain')
 data(R/'reports/m4-tree-review/mfc1168-chronological-source-r2/report.json','cad4c935d169fccf4adbdff725daf3aa6bee617970cb96c90a42cbcf1c3c9f58')
 selected=data(R/'reports/m4-joint-startup131/preparation-r1/selected-order.json');need(len(selected)==131,'Exact selected131 extent')
 pairs=[(v['slot'],v['entry'])for v in selected];oldpairs=[(v['slot'],v['entry'])for v in old['selected_order']];need([v for v in pairs if v!=(0x5e0040,0x5ae3e4)]==oldpairs and pairs[13]==(0x5e0040,0x5ae3e4),'Full130 relative chronology retained and MFC after13')
 raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();count=struct.unpack_from('<I',raw,8)[0];need(len(raw)==12+count*4104,'Exact frozen full130 pack geometry');records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(count)}
 game=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());spans=list(old['source_spans']);known={r['pc']:r for r in spans};new=[]
 for r in mfc['source_spans']:
  if r['pc']in known:need(r==known[r['pc']],'Whole shared source binding identical');continue
  need(r['origin']==0,'Only game MFC root source is new');off,_=game.rva_range(r['pc']-game.image_base,r['size']);need(off==r['image_offset'],'Exact new physical instruction offset');bytes_=game.data[off:off+r['size']];taken=0
  while taken<len(bytes_):
   a=r['pc']+taken;p=a&~4095;o=a&4095;n=min(len(bytes_)-taken,4096-o)
   if p not in records:records[p]=(1,bytearray(b'\xcc'*4096))
   need(len(records[p][1])==4096 and all(v==0xcc for v in records[p][1][o:o+n]),'New source row only overlays exact inherited sparse padding');records[p][1][o:o+n]=bytes_[taken:taken+n];taken+=n
  spans.append(r);new.append(r);known[r['pc']]=r
 need(len(new)==25,'Whole MFC game closure25 physical rows')
 page=0x5f2000;rva=page-game.image_base;section=next(s for s in game.sections if s['virtual_address']<=rva and rva+4096<=s['virtual_address']+max(s['virtual_size'],s['raw_size']));need(section['writable']and section['readable']and not section['executable']and page not in records,'New whole physical constructor prerequisite data page')
 off,_=game.rva_range(rva,4096);records[page]=(2,bytearray(game.data[off:off+4096]));need(all(len(v)==4096 for _,v in records.values()),'Every whole source page exactly4096B')
 for slot,entry in pairs:
  offset,_=game.rva_range(slot-game.image_base,4);need(struct.unpack_from('<I',game.data,offset)[0]==entry and struct.unpack_from('<I',records[slot&~4095][1],slot&4095)[0]==entry,'Each genuine root physical table cell')
 pack=raw[:8]+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+v for p,(perm,v)in records.items());need(len(pack)==12+4104*len(records),'Final exact pack geometry')
 out.mkdir(parents=True);(out/'pages.bin').write_bytes(pack)
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 for field,values in [('entries',[e for s,e in pairs]),('table_slots',[s for s,e in pairs]),('page_bases',list(records)),('page_permissions',[v[0]for v in records.values()])]:spec=array(spec,field,values)
 pattern=r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;';need(len(re.findall(pattern,spec))==1,'Exact complete source-binding array');spec=re.sub(pattern,f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(r[k])for k in('pc','size','image_offset','origin'))+'}'for r in spans)+'}};',spec)
 (out/'spec.hpp').write_text(spec);(out/'protocol.hpp').write_text(one(text(OLD/'protocol.hpp'),'sequences=6, roots=130','sequences=6, roots=131'))
 # Preserve each reviewed current observation bridge. The reference ASM adds
 # coherent true entry/return TIB copies and bounded API-ledger export guard.
 for fn in('reference_x86.asm','boundaries.asm','api_boundaries.asm','connected_observer.hpp'):(out/fn).write_text(text(MFC/fn))
 obs=text(out/'connected_observer.hpp');obs=one(obs,'static mw34::capture_direct::Writer*connected_writer{};','static mw34::capture_direct::Writer*connected_writer{};static std::string connected_stem;')
 obs=one(obs,'connected_writer->append("MFC1168/"+name,data,n);','connected_writer->append(connected_stem+name,data,n);');(out/'connected_observer.hpp').write_text(obs)
 prerequisite=text(T/'prerequisite_observer_v2.hpp');(out/'prerequisite_observer.hpp').write_text(prerequisite)
 for fn in('preserve_x86.asm','fs_observer_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer_x86.asm','format_observer.hpp','original_broker.hpp','fs-hook-bindings.json'):(out/fn).write_text(text(OLD/fn))
 broker=text(out/'original_broker.hpp');bases={int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')};need(all(p&~65535 in bases for p in records),'All pack pages have exact admitted pre-CRT reservation, no new broker geometry')
 cmake=one(text(OLD/'CMakeLists.txt'),'format_observer_x86.asm "${MW34_WRITER_SOURCE}"','format_observer_x86.asm boundaries.asm api_boundaries.asm "${MW34_WRITER_SOURCE}"');(out/'CMakeLists.txt').write_text(cmake)
 ref=text(OLD/'reference.cpp');ref=one(ref,'int main(int argc,char**argv)', '#include "connected_observer.hpp"\n#include "prerequisite_observer.hpp"\nint main(int argc,char**argv)')
 ref=re.sub(r'std::array<void\*,132> pages',f'std::array<void*,{len(records)}> pages',ref)
 ref=one(ref,'    if(auto broker=mw34::original_broker::dispatch','    require(!debugger,"Normal full131 only; instruction tracing is not admitted");\n    if(auto broker=mw34::original_broker::dispatch')
 ref=one(ref,'    for(unsigned i=0;i<pages.size();++i){\n        protect','    const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");require(reinterpret_cast<unsigned>(service)==0x5f401083&&reinterpret_cast<unsigned>(mbcp)==0x78003ddb,"Actual named1168/setmbcp physical exports");require(dword(0x5bb210)==0x80000490,"Raw physical1168 game import");*reinterpret_cast<unsigned*>(0x5bb210)=reinterpret_cast<unsigned>(service);*reinterpret_cast<unsigned*>(0x5bb674)=reinterpret_cast<unsigned>(mbcp);\n    for(unsigned i=0;i<pages.size();++i){\n        protect')
 ref=one(ref,'mw34::capture_direct::Writer out(argv[4]);','mw34::capture_direct::Writer out(argv[4]);connected_writer=&out;')
 ref=one(ref,'    unsigned sequence{};','    const auto restore_registry_hooks=[&](){for(unsigned i=0;i<8;++i){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(registry_IATs[i]),4,PAGE_READWRITE,&prior),"Current actual CRT IAT restoration before MFC");*reinterpret_cast<unsigned*>(registry_IATs[i])=registry_API_targets[i];require(VirtualProtect(reinterpret_cast<void*>(registry_IATs[i]),4,prior,&ignored),"Current actual CRT IAT protection restored");}};\n    const auto reinstall_registry_hooks=[&](){for(unsigned i=0;i<8;++i){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(registry_IATs[i]),4,PAGE_READWRITE,&prior),"Current CRT IAT reentry after MFC");*reinterpret_cast<unsigned*>(registry_IATs[i])=reinterpret_cast<unsigned>(registry_shims[i]);require(VirtualProtect(reinterpret_cast<void*>(registry_IATs[i]),4,prior,&ignored),"Current CRT IAT reentry protection restored");}};\n    unsigned sequence{};')
 ref=one(ref,'        mixed_allocation_count=0;','        constructor_occurrences.clear();registry_API_count=0;fs_error=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));std::memset(registry_initial_sizes,0,sizeof(registry_initial_sizes));std::memset(registry_initial_bytes,0,sizeof(registry_initial_bytes));\n        mixed_allocation_count=0;')
 ref=one(ref,'        out.append("bootstrap/"+std::to_string(sequence)+"/producer-after-cpu.bin",','        require(!fs_error&&registry_API_count<=256,"Current producer ledger bound before any export");const auto cboot="bootstrap/"+std::to_string(sequence);constructor_collect(0xffffffffU,cboot);out.append(cboot+"/producer-api-count.bin",&registry_API_count,4);out.append(cboot+"/producer-api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));\n        out.append("bootstrap/"+std::to_string(sequence)+"/producer-after-cpu.bin",')
 # The temporary named-API seam is installed only for the actual MFC root.
 # Capture loaded input pages before replacing its four named cells; restore
 # those cells and source spans before complete AFTER/phase record exports.
 before='''            const auto phase_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase);const bool mfc_phase=entries[phase]==0x5ae3e4;
            if(mfc_phase){require(phase==13,"Actual chronology has13 carried roots before MFC");constructor_graph(phase_stem+"/BEFORE-MFC");remove_CRT_hooks();restore_registry_hooks();connected_stem=phase_stem+"/MFC1168/";boundary_count=0;named_count=0;observer_error=0;std::memset(boundaries,0,sizeof(boundaries));std::memset(named_boundaries,0,sizeof(named_boundaries));connected_named_identity();module_pages("BEFORE/MFC",0x5f400000,0xed000);module_pages("BEFORE/CRT",0x78000000,0x40000);domain("BEFORE/domain");connected_lock("BEFORE/CRT-codepage-lock");}
'''
 ref=one(ref,'            auto r=std::make_unique<Record>();',before+'            auto r=std::make_unique<Record>();')
 ref=one(ref,'            if(entries[phase]==0x4b7f70)require(', '            if(mfc_phase){named_IAT(true);connected_patch_sources(true);}\n            if(entries[phase]==0x4b7f70)require(')
 after='''if(mfc_phase){named_IAT(false);connected_patch_sources(false);require(!observer_error,"Authentic full131 MFC observation transparency");dump("boundaries/count.bin",&boundary_count,4);require(boundary_count<=16,"Full MFC boundary extent before export");dump("boundaries/records.bin",boundaries,boundary_count*sizeof(Boundary));dump("named-API/count.bin",&named_count,4);require(named_count<=64,"Full named API extent before export");dump("named-API/records.bin",named_boundaries,named_count*sizeof(NamedBoundary));module_pages("AFTER/MFC",0x5f400000,0xed000);module_pages("AFTER/CRT",0x78000000,0x40000);domain("AFTER/domain");connected_lock("AFTER/CRT-codepage-lock");constructor_graph(phase_stem+"/AFTER-MFC");}'''
 ref=one(ref,'copy_capture(*r);copy_pages(r->memory_after);', 'copy_capture(*r);'+after+'copy_pages(r->memory_after);')
 ref=one(ref,'            require(registry_API_count<=256,"Bounded actualAPI ledger");','            if(phase<13)constructor_collect(phase,phase_stem);\n            require(registry_API_count<=256,"Bounded actualAPI ledger");')
 ref=one(ref,'            out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+".bin",r.get(),sizeof(*r));','            if(mfc_phase){out.append(phase_stem+"/TEB-before-base.bin",&mixed_teb_before_base,4);out.append(phase_stem+"/TEB-before.bin",mixed_teb_before_pages,8192);out.append(phase_stem+"/TEB-after-base.bin",&mixed_teb_after_base,4);out.append(phase_stem+"/TEB-after.bin",mixed_teb_after_pages,8192);reinstall_registry_hooks();install_CRT_hooks();}\n            out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+".bin",r.get(),sizeof(*r));')
 # New owning source imports are exact named cells, never ignored bytes.
 ref=one(ref,'            bool format_import_byte=false;', '            if((pc>=0x5bb210&&pc<0x5bb214)||(pc>=0x5bb674&&pc<0x5bb678)){const unsigned cell=pc<0x5bb214?0x5bb210:0x5bb674,target=cell==0x5bb210?reinterpret_cast<unsigned>(service):reinterpret_cast<unsigned>(mbcp);require(actual[byte]==reinterpret_cast<const unsigned char*>(&target)[pc-cell],"Exact named1168/setmbcp source IAT byte");continue;}\n            bool format_import_byte=false;')
 ref=ref.replace('Original130','Original131').replace('original130','original131').replace('MW4J130','MW4J131').replace('/780 actual original initializer phases','/786 actual original initializer phases')
 ref=one(ref,'    out.finish();std::cout<<','    connected_writer=nullptr;out.finish();std::cout<<');(out/'reference.cpp').write_text(ref)
 patches=data(MFC/'contracts.json')['active_code_patches'];active=[v for v in patches if v['family']=='MFC1168-game-boundary'];fs=data(OLD/'fs-hook-bindings.json')
 inherited=[]
 for v in fs:inherited.append(dict(PC=v['PC'],size=len(bytes.fromhex(v['raw_bytes'])),family='FS'))
 # Exhaustive source families from the actual baseline C++ authored patch
 # arrays, including NULL-free/vtable/Lockit/formatter, plus capture/terminal.
 for field in('null_hooks','vtable_hooks','lockit_hooks','format_hooks'):
  owner=ref if field!='format_hooks'else text(out/'format_observer.hpp')
  pattern=rf'{field}\{{\{{(.*?)\}}\}};';m=re.search(pattern,owner,re.S);need(m is not None,'Whole actual patch-family declaration '+field)
  if field=='null_hooks':
   found=[(pc,'5')for pc in re.findall(r'\{(0x[0-9a-f]+),&nullfree_',m[1])]
   need(len(found)==2,'Exact two fixed-five-byte NULL-free hooks')
  else:found=re.findall(r'\{(0x[0-9a-f]+),(\d+),',m[1])
  need(found,'Concrete patch rows '+field)
  inherited.extend(dict(PC=int(pc,16),size=int(n),family=field)for pc,n in found)
 inherited += [dict(PC=0x410a80,size=5,family='capture'),dict(PC=0x5ac3ec,size=5,family='sentinel')]
 for a in active:
  for b in inherited:need(a['PC']+a['size']<=b['PC']or b['PC']+b['size']<=a['PC'],'New MFC patches do not overlap inherited physical observers')
 contracts=dict(selected_order=selected,source_frame=0x20001800,sequences=6,phases=786,callbacks=101,current46_source_pages=old['observed_pages']+old['extra_whole_source_pages'],MFC_root=0x5ae3e4,MFC_phase=13,whole_MFC_loaded_bytes=0xed000,whole_CRT_loaded_bytes=0x40000,normal_boundary_bytes=664,named_API_boundary_bytes=668,active_new_code_patches=active,inherited_active_code_patches=inherited,generic_CRT_FS_NULL_IAT_restored_before_MFC=True,new_named_and_source_patches_restored_before_AFTER=True,generic_CRT_FS_NULL_IAT_reinstalled_after_MFC=True,all_provider_pages_carried_across_sequences=True,coherent_true_root_TIB8192=True,constructor_prerequisites=dict(page=0x5f2000,whole_page_sha256=hashlib.sha256(bytes(records[page][1])).hexdigest(),physical_section=section,physical_file_offset=off,shared_header_cell=0x603fdc,counter_cell=0x603fe0,actual_identifier_cell=0x5f2a48,root_entries_executed=[],source_inputs=False,capacity_and_occurrence_policy='Genuine prefix HeapAlloc-return whole inputs and persistent ordered API occurrence revisions; true HeapSize full list backings/currentlinks at actual BEFORE/AFTER MFC'),provider_preinvoked=False,per_phase_reseed=False,source_AFTER_seed=False,writer_admitted=False,initializer_credit=0)
 for fn,obj in [('contracts.json',contracts),('selected-order.json',selected)]:p=out/fn;p.write_text(json.dumps(obj,indent=2)+'\n');pin(p)
 pin(__file__);pin(R/'tools/analysis/pe.py');pin(R/'tools/m4-capture-direct/capture_direct_v3.hpp');pin(R/'tools/m4-capture-direct/capture_direct_v3.cpp')
 for p in out.iterdir():pin(p)
 report=dict(passed=True,scope='Full131 genuine original preparation-only; accepted130 order plus measured chronological MFC and separate authentic constructor prerequisites',original_sequences=6,original_roots=131,original_phases=786,callback_count=101,record_bytes=356992,ordinary_record_pages=43,extra_whole_source_pages=old['extra_whole_source_pages'],combined_source_page_count=46,observer_prerequisite_extra_pages=[0x5f2000],MFC_domain_extra_regions=12,source_spans=spans,observed_pages=old['observed_pages'],pack_sha256=sha(out/'pages.bin'),pack_bytes=len(pack),sparse_pack_pages=len(records),FS_hooks=63,selected_order=selected,new_game_source_rows=len(new),source_frame=0x20001800,true_TIB8192_from_reviewed_current_ASM=True,constructor_prerequisites_observation_only=True,provider_preinvoked=False,predicted_values_supplied_to_execution=False,source_output_seed=False,original_executed=False,capture_reader_opened=False,initializer_credit=0,contracts=str(out/'contracts.json'),files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),pages=len(records),roots=131)))
if __name__=='__main__':main(sys.argv[1])
