"""Add genuine original MFC103 source execution to frozen original71."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mfc-source';OLD=ROOT/'reports/m4-strings-source/original-preparation-r3';REC=BASE/'recovery-r4'
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def one(s,a,b):need(s.count(a)==1,'Unique additive source '+a[:70]);return s.replace(a,b)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original103 source preparation');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact original preparation input '+str(p));files[str(p)]=v;return p
 def read(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','36f77f67e5ba1cbf4483209e525ebeecf367563b3ecb9d449bc94fbbd6449d5f').read_bytes());rec=json.loads(pin(REC/'report.json','b50217399d254eddc620ab39bf8d934fd2cc30233e575356a9d8c40761c33e0f').read_bytes());geometry=json.loads(pin(BASE/'allocation-contracts-r4/report.json','30ef9954b16ba185294871d5cb419df502b656aab7f12fc521a4e3b09fe156f2').read_bytes());allocs=json.loads(pin(BASE/'allocation-contracts-r4/allocation-inputs.json',geometry['allocation_inputs_sha256']).read_bytes());need(len(allocs)==35,'Exact source-derived35 allocations')
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());mfc=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes());pin(BASE/'loader-identity-r1/report.json','7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b')
 def page(image,base):
  raw=bytearray(4096);pieces=[];permission=0
  for s in image.sections:
   a=image.image_base+s['virtual_address'];lo=max(base,a);hi=min(base+4096,a+s['raw_size'])
   if lo<hi:
    off=s['raw_offset']+lo-a;raw[lo-base:hi-base]=image.data[off:off+hi-lo];pieces.append(dict(section=s['name'],address=lo,size=hi-lo,file_offset=off))
   if max(base,a)<min(base+4096,a+max(s['raw_size'],s['virtual_size']))and s['writable']:permission=2
  return raw,pieces,permission
 oldpack=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',oldpack,12+i*4104)[0]:(struct.unpack_from('<I',oldpack,16+i*4104)[0],bytearray(oldpack[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',oldpack,8)[0])};provenance=[]
 for base in rec['data_pages']:
  if base in records:continue
  raw,pieces,permission=page(game,base);records[base]=(permission,raw);provenance.append(dict(base=base,raw_pieces=pieces,zero_fill_bytes=4096-sum(p['size']for p in pieces),sha256=hashlib.sha256(raw).hexdigest()))
 spec=read(OLD/'spec.hpp');match=re.search(r'code_bindings\{\{([^;]+)\}\};',spec);spans=[dict(zip(('pc','size','image_offset','origin'),map(lambda x:int(x,16),m)))for m in re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+)\}',match[1])]
 graphs=json.loads(pin(REC/'game-new-graphs.json').read_bytes());rows={r['pc']:r for g in graphs.values()for r in g['instructions']}
 for row in rows.values():
  a=row['pc'];base=a&~4095;raw=bytes.fromhex(row['bytes']);off,_=game.rva_range(a-game.image_base,len(raw));need(game.data[off:off+len(raw)]==raw,'Every genuine added game instruction')
  if base not in records:records[base]=(1,bytearray(b'\xcc'*4096))
  records[base][1][a&4095:(a&4095)+len(raw)]=raw;spans.append(dict(pc=a,size=len(raw),image_offset=off,origin=0))
 observed=old['observed_pages']+[a for a in rec['data_pages']if a not in old['observed_pages']]+[0x5f498000];need(len(observed)==35 and len(set(observed))==35,'35 complete observed pages')
 pack=b'MW4J103P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',a,p)+raw for a,(p,raw)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for n,values in(('entries',[r['entry']for r in rec['order']]),('table_slots',[r['slot']for r in rec['order']]),('page_bases',list(records)),('page_permissions',[p for p,b in records.values()])):
  spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+n+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+n+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(x[k])for k in('pc','size','image_offset','origin'))+'}'for x in spans)+'}};',spec)
 mfcraw,pieces,permission=page(mfc,0x5f498000);need(permission==0,'Original MFC .rdata source read-only');importrows=[]
 for d in mfc.imports():
  for row in d['symbols']:
   a=mfc.image_base+row['iat_rva']
   if 0x5f498000<=a<0x5f499000:importrows.append(dict(slot=a,raw=struct.unpack_from('<I',mfcraw,a&4095)[0],library=d['library'],name=row.get('name'),ordinal=row.get('ordinal',0)))
 need(len(importrows)==511 and len({r['slot']for r in importrows})==511,'Exact physical MFC import slots on whole page')
 spec+='\nstruct MfcBinding {unsigned root,CALL_pc,size,object,publication;};\ninline constexpr std::array<MfcBinding,35> mfc_bindings{{'+','.join('{'+','.join(hex(r[k])for k in('root','CALL_pc','requested_size','object','publication'))+'}'for r in allocs)+'}};\n'
 spec+='struct MfcImportBinding {unsigned slot,raw,ordinal;const char*library;const char*name;};\ninline constexpr std::array<MfcImportBinding,511> mfc_import_bindings{{'+','.join('{'+','.join((hex(r['slot']),hex(r['raw']),str(r['ordinal']),json.dumps(r['library']),json.dumps(r['name'])if r['name']else'nullptr'))+'}'for r in importrows)+'}};\n'
 spec+='inline constexpr std::array<unsigned char,4096> mfc_raw_page{'+','.join(hex(b)for b in mfcraw)+'};\n';(out/'spec.hpp').write_text(spec)
 protocol=read(OLD/'protocol.hpp').replace('roots=71','roots=103').replace('observed_page_count=32','observed_page_count=35').replace('sizeof(Record)==266880','sizeof(Record)==291456').replace('memory_size==131072','memory_size==143360');protocol=one(protocol,'0x5e7000};','0x5e7000,0x72b000,0x731000,0x5f498000};');(out/'protocol.hpp').write_text(protocol)
 broker=read(OLD/'original_broker.hpp');match=re.search(r'std::array<std::uint32_t,\d+> bases\{([^;]+)\};',broker);bases=list(dict.fromkeys([int(x,16)for x in match[1].split(',')]+[a&~65535 for a in records]));broker=broker[:match.start()]+f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(a)for a in bases)+'};'+broker[match.end():];(out/'original_broker.hpp').write_text(broker)
 asm=read(OLD/'reference_x86.asm');asm=one(asm,'EXTERN registry_API_ledger:BYTE','EXTERN registry_API_ledger:BYTE\nEXTERN registry_observe_allocation:PROC\nEXTERN registry_observer_fx:BYTE\nEXTERN registry_observer_env:BYTE')
 asm=one(asm,' push DWORD PTR registry_API_after[32]',' fxsave registry_observer_fx\n fnstenv registry_observer_env\n fldenv registry_observer_env\n call registry_observe_allocation\n fxrstor registry_observer_fx\n fldenv registry_observer_env\n push DWORD PTR registry_API_after[32]');(out/'reference_x86.asm').write_text(asm)
 ref=read(OLD/'reference.cpp').replace('MW4J71P1','MW4J103P').replace('MW4J71D1','MW4J103D').replace('MW4J71O1','MW4J103O').replace('Original71','Original103').replace('original71','original103');ref=re.sub(r'std::array<void\*,80> pages',f'std::array<void*,{len(records)}> pages',ref)
 ref=one(ref,'RegistryAPIEntry registry_API_ledger[32]{};','''RegistryAPIEntry registry_API_ledger[32]{};
alignas(16) unsigned char registry_observer_fx[512]{};unsigned char registry_observer_env[28]{};
unsigned registry_initial_sizes[32]{};unsigned char registry_initial_bytes[32][512]{};
void registry_observe_allocation(){
 const auto i=registry_API_count-1;if(i>=32||registry_API_kind!=0||!registry_API_after.eax)return;
 const auto pointer=reinterpret_cast<void*>(registry_API_after.eax);const auto size=reinterpret_cast<SIZE_T(WINAPI*)(HANDLE,DWORD,LPCVOID)>(registry_API_targets[2])(reinterpret_cast<HANDLE>(registry_API_args[0]),0,pointer);
 if(size==SIZE_T(-1)||size>512)return;registry_initial_sizes[i]=static_cast<unsigned>(size);std::memcpy(registry_initial_bytes[i],pointer,size);
}''')
 ref=one(ref,'    auto*crtbegin=', '''    const auto mfcpath=std::filesystem::path("D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MFC42.DLL");const auto mfcbytes=read(mfcpath.string().c_str(),1100592);require(sha256(mfcbytes)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact genuine MFC42 image");
    auto mfc=LoadLibraryExW(mfcpath.c_str(),nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(reinterpret_cast<std::uintptr_t>(mfc)==0x5f400000,"Original32 exact MFC preferred base");
    auto mfc823=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(823));const auto mfc825=reinterpret_cast<OriginalFree>(GetProcAddress(mfc,reinterpret_cast<LPCSTR>(825)));require(reinterpret_cast<std::uintptr_t>(mfc823)==0x5f401ea0&&reinterpret_cast<std::uintptr_t>(mfc825)==0x5f401782,"Actual MFC ordinal source identities");
    require(*reinterpret_cast<unsigned*>(0x5f49814c)==0x780012b3&&*reinterpret_cast<unsigned*>(0x5f498148)==0x78001390&&*reinterpret_cast<unsigned*>(0x5f498970)==0xffffffff,"Genuine loader named CRT imports and handler");*reinterpret_cast<unsigned*>(0x5bb4bc)=reinterpret_cast<std::uintptr_t>(mfc823);
    MEMORY_BASIC_INFORMATION mfc_region{};require(VirtualQuery(reinterpret_cast<void*>(0x5f498000),&mfc_region,sizeof(mfc_region))==sizeof(mfc_region)&&mfc_region.Protect==PAGE_READONLY,"Actual MFC source .rdata read-only");
    auto*crtbegin=''')
 ref=one(ref,'    std::cerr<<"Original103 writermetadataready', '''    out.append("mfc-image.bin",mfcbytes.data(),mfcbytes.size());out.append("mfc-raw-page.bin",mfc_raw_page.data(),4096);out.append("mfc-loaded-page.bin",reinterpret_cast<void*>(0x5f498000),4096);out.append("mfc-page-region.bin",&mfc_region,sizeof(mfc_region));
    std::vector<unsigned> mfc_import_ledger;std::vector<unsigned> mfc_module_bases;
    for(const auto&binding:mfc_import_bindings){auto declared=GetModuleHandleA(binding.library);require(declared!=nullptr,"Exact declared MFC import library loaded");const auto named=GetProcAddress(declared,binding.ordinal?reinterpret_cast<LPCSTR>(binding.ordinal):binding.name);const auto actual=*reinterpret_cast<unsigned*>(binding.slot);require(actual==reinterpret_cast<std::uintptr_t>(named),"Every original loaded MFC import has exact named or ordinal identity");HMODULE owner_module{};require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(actual),&owner_module),"Actual MFC import forwarder owner");const unsigned declaredbase=reinterpret_cast<std::uintptr_t>(declared),ownerbase=reinterpret_cast<std::uintptr_t>(owner_module);for(auto base:{declaredbase,ownerbase})if(std::find(mfc_module_bases.begin(),mfc_module_bases.end(),base)==mfc_module_bases.end())mfc_module_bases.push_back(base);for(auto value:{binding.slot,binding.raw,actual,declaredbase,ownerbase,reinterpret_cast<unsigned>(named),binding.ordinal})mfc_import_ledger.push_back(value);}
    require(mfc_import_ledger.size()==511*7,"Exact511 loader-authenticated import DWORDs");out.append("mfc-import-ledger.bin",mfc_import_ledger.data(),mfc_import_ledger.size()*4);
    auto normalized_mfc=mfc_raw_page;std::memcpy(normalized_mfc.data(),reinterpret_cast<void*>(0x5f498000),4096);for(const auto&binding:mfc_import_bindings)std::memcpy(normalized_mfc.data()+(binding.slot&4095),&binding.raw,4);require(normalized_mfc==mfc_raw_page,"No unexplained nonimport MFC page mutation");
    for(auto base:mfc_module_bases){std::array<wchar_t,32768> path{};const auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(base),path.data(),path.size());require(n&&n<path.size(),"Original declared/forwarder module path");const auto imagebytes=read(std::filesystem::path(path.data()).string().c_str(),64*1024*1024);const auto stem="mfc-modules/"+std::to_string(base);out.append(stem+"/path.bin",path.data(),(n+1)*sizeof(wchar_t));out.append(stem+"/image.bin",imagebytes.data(),imagebytes.size());}
    std::cerr<<"Original103 writermetadataready''')
 ref=one(ref,'registry_API_count=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));','registry_API_count=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));std::memset(registry_initial_sizes,0,sizeof(registry_initial_sizes));std::memset(registry_initial_bytes,0,sizeof(registry_initial_bytes));')
 ref=one(ref,'            const auto stringbase=', '''            for(unsigned ai=0;ai<registry_API_count;++ai)if(registry_API_ledger[ai].kind==0&&registry_API_ledger[ai].after.eax){require(registry_initial_sizes[ai]>=registry_API_ledger[ai].args[2]&&registry_initial_sizes[ai]<=512,"Actual HeapAlloc initial backing captured before guest writes");const auto ibase="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/api-initial/"+std::to_string(ai);out.append(ibase+"/size.bin",&registry_initial_sizes[ai],4);out.append(ibase+"/bytes.bin",registry_initial_bytes[ai],registry_initial_sizes[ai]);}
            const auto mfcbase="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/mfc/";
            for(unsigned mi=0;mi<mfc_bindings.size();++mi){const auto&binding=mfc_bindings[mi];if(binding.root>entries[phase])continue;const auto pointer=*reinterpret_cast<unsigned*>(binding.publication);require(pointer!=0,"Actual live original MFC object publication");const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(pointer));require(cap!=SIZE_T(-1)&&cap>=binding.size&&cap<=512,"Actual full original MFC object backing extent");const std::array<unsigned,8> meta{binding.root,binding.CALL_pc,binding.size,binding.object,binding.publication,pointer,static_cast<unsigned>(cap),mi};out.append(mfcbase+std::to_string(mi)+"/meta.bin",meta.data(),sizeof(meta));out.append(mfcbase+std::to_string(mi)+"/bytes.bin",reinterpret_cast<void*>(pointer),cap);}
            const auto stringbase=''')
 ref=ref.replace('43*4','75*4').replace('Exact43callback','Exact75callback')
 ref=one(ref,'registry_cleanup.restore();for(const auto&binding:string_bindings)', '''registry_cleanup.restore();for(unsigned mi=0;mi<mfc_bindings.size();++mi){const auto&binding=mfc_bindings[mi];const auto pointer=*reinterpret_cast<unsigned*>(binding.publication);require(pointer!=0,"Original MFC source free owns live object");const auto actual_heap=*reinterpret_cast<HANDLE*>(0x78035000);const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(pointer));const std::array<unsigned,8> meta{binding.root,binding.CALL_pc,binding.size,binding.object,binding.publication,pointer,static_cast<unsigned>(cap),mi};out.append("cleanup/"+std::to_string(sequence)+"/mfc-"+std::to_string(mi)+"-before.bin",meta.data(),sizeof(meta));out.append("cleanup/"+std::to_string(sequence)+"/mfc-"+std::to_string(mi)+"-owned.bin",reinterpret_cast<void*>(pointer),cap);mfc825(reinterpret_cast<void*>(pointer));const unsigned returned=1;out.append("cleanup/"+std::to_string(sequence)+"/mfc-"+std::to_string(mi)+"-returned.bin",&returned,4);*reinterpret_cast<unsigned*>(binding.publication)=0;}for(const auto&binding:string_bindings)''')
 ref=one(ref,'||(pc>=0x5bb670&&pc<0x5bb674)', '||(pc>=0x5bb670&&pc<0x5bb674)||(pc>=0x5bb4bc&&pc<0x5bb4c0)');ref=ref.replace('/426 actual','/618 actual');ref='#include <algorithm>\n'+ref
 (out/'reference.cpp').write_text(ref);(out/'preserve_x86.asm').write_text(read(OLD/'preserve_x86.asm'));(out/'CMakeLists.txt').write_text(read(OLD/'CMakeLists.txt').replace('Startup71','Startup103').replace('startup71','startup103'))
 for fn,value in(('mfc-import-bindings.json',importrows),('allocation-inputs.json',allocs),('page-provenance.json',provenance)):(out/fn).write_text(json.dumps(value,indent=2)+'\n')
 (out/'mfc-raw-page.bin').write_bytes(mfcraw)
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);report=dict(passed=True,scope='Additive genuine original103 preparation; unchanged accepted71 +32 roots/35 owned MFC allocations',parent_preparation=str(OLD),parent_sha256=sha(OLD/'report.json'),order=rec['order'],observed_pages=observed,page_count=len(records),source_spans=spans,pack_sha256=sha(out/'pages.bin'),record_bytes=291456,mfc_bindings=allocs,mfc_import_slots=511,complete_MFC_observed_page=True,import_relation='Exact physical511 raw DWORDs, actual own-process named/ordinal/declared/forwarder identities; zero nonimport differences',real_HeapAlloc_initial_backing_observed_before_guest_write=True,source_cleanup='Genuine original MFC825 literal free then CRTfree; callbacks stored but not executed',per_phase_reseed=False,original_executed=False,native_executed=False,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),pages=len(records),observed=len(observed))))
if __name__=='__main__':main(sys.argv[1])
