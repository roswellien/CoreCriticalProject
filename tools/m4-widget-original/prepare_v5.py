"""Prepare a bounded authentic five-widget normal sequence. No execution."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BASE=R/'reports/m4-widget-original';OLD=R/'reports/m4-cosine-original/prefix-preparation-r2'
CURRENT=R/'reports/m4-startup130-original/preparation-r2'
sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact additive derivation '+a[:90]);return s.replace(a,b,1)
def bridge(name,api,side,raw):
 pc=[0x5a0142,0x5a0645,0x5a0751][api]
 lines=[f'PUBLIC {name}',f'{name} PROC']
 for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):lines.append(f' mov DWORD PTR widget_cpu[{4*i}],{reg}')
 lines+=([f' mov DWORD PTR widget_cpu[36],0{pc:x}h']if side else[f' mov eax,DWORD PTR widget_targets[{4*api}]',' mov DWORD PTR widget_cpu[36],eax'])
 lines += [f' mov widget_kind,{2*api+side}',' mov esp,mixed_host_esp',' pushfd',' pop DWORD PTR widget_cpu[32]',' cld',' mov eax,DWORD PTR fs:[0]',' mov widget_head,eax',' mov ax,ds',' mov widget_ds,ax',' mov ax,es',' mov widget_es,ax',' mov ax,ss',' mov widget_ss,ax',' fxsave widget_fx',' fnstenv widget_env',' fldenv widget_env',' call widget_observe',' fxrstor widget_fx',' fldenv widget_env',' push DWORD PTR widget_cpu[32]',' popfd']
 for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):
  if reg!='esp':lines.append(f' mov {reg},DWORD PTR widget_cpu[{4*i}]')
 lines+=[' mov esp,DWORD PTR widget_cpu[16]']
 if side:lines+=[' db '+','.join('0'+format(v,'02x')+'h'for v in raw),f' jmp DWORD PTR widget_continues[{4*api}]']
 else:lines+=[f' jmp DWORD PTR widget_targets[{4*api}]']
 return '\n'.join(lines+[f'{name} ENDP'])+'\n'

def main(name):
 out=BASE/name;need(not out.exists(),'Fresh preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture archive');v=sha(p);need(h is None or h==v,'Exact physical pin '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(text(OLD/'report.json'));cur=json.loads(text(CURRENT/'report.json'));need(old['passed']and cur['passed'],'Authentic bootstrap sources')
 planp=pin(R/'reports/m4-widget-source/normal-plan-r1/normal-plan.json','4abe1fd05f20ed6077b1022d4c2d04a2149f7467b39b1d91e704053579dabd10');plan=json.loads(planp.read_bytes())
 for p in ('recovery-r2/report.json','dispatch-r1/report.json','normal-plan-r1/report.json','lift-preparation-r1/report.json'):need(json.loads(text(R/'reports/m4-widget-source'/p))['passed'],'Exact static receipt')
 contracts=json.loads(text(R/'reports/m4-widget-source/lift-preparation-r1/instruction-contracts.json'));rows=contracts['instructions'];need(len(rows)==1081 and sum(r['width']for r in rows)==3350,'Exact finite literal union')
 regs=json.loads(text(R/'reports/m4-widget-source/recovery-r2/registration-roots.json'));need(len(regs)==5,'Five exact slots')
 game=PEImage(pin(R/'MW3/Mech3.exe').read_bytes());pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL');pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL');pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL')
 raw=pin(CURRENT/'pages.bin',cur['pack_sha256']).read_bytes();records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',raw,8)[0])}
 spans=list(cur['source_spans']);known={(r['pc'],r['size'])for r in spans}
 physical_pages=[]
 def raw_page(page):
  b=bytearray(4096);segments=[]
  for sec in game.sections:
   s=game.image_base+sec['virtual_address'];end=s+max(sec['virtual_size'],sec['raw_size']);lo=max(page,s);hi=min(page+4096,end)
   if lo>=hi:continue
   file_end=min(hi,s+sec['raw_size'])
   if lo<file_end:b[lo-page:file_end-page]=game.data[sec['raw_offset']+lo-s:sec['raw_offset']+file_end-s]
   segments.append(dict(section=sec['name'],lo=lo,hi=hi,writable=sec['writable'],file_end=max(lo,file_end)))
  need(segments,'Physical page section extent '+hex(page));return b,segments
 for page in plan['page_inventory']['prospective_combined_pages']:
  if page not in records:
   if not game.image_base<=page<game.image_base+game.size_of_image:
    need(page in cur['observed_pages'],'Exact inherited real loader/stack page '+hex(page));continue
   b,segs=raw_page(page);need(all(not s['section']=='.text'for s in segs),'Source-data page');perm=2 if any(s['writable']for s in segs)else 0
   records[page]=(perm,b);physical_pages.append(dict(page=page,permission=perm,segments=segs,raw_sha256=hashlib.sha256(b).hexdigest()))
 for row in rows:
  pc=row['pc'];b=bytes.fromhex(row['bytes_hex']);off,_=game.rva_range(pc-game.image_base,len(b));need(game.data[off:off+len(b)]==b,'Exact instruction '+hex(pc));page=pc&~4095
  if page not in records:records[page]=(1,bytearray(b'\xcc'*4096))
  records[page][1][pc&4095:(pc&4095)+len(b)]=b
  if (pc,len(b))not in known:spans.append(dict(pc=pc,size=len(b),image_offset=off,origin=0));known.add((pc,len(b)))
 # Full code page observed at every GDI seam: bytes outside selected source remain original sparse input.
 need(0x5a0000 in records,'Shared GDI source page')
 for v in regs:need(struct.unpack_from('<I',records[v['slot']&~4095][1],v['slot']&4095)[0]==v['root'],'Genuine selected table DWORD')
 whole=plan['page_inventory']['prospective_combined_pages'];need(len(whole)==64 and len(cur['observed_pages'])==43,'Whole coverage geometry');extra=[p for p in whole if p not in cur['observed_pages']];need(len(extra)==21,'External21 pages')
 out.mkdir(parents=True);(out/'pages.bin').write_bytes(b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+b for p,(perm,b)in records.items()))
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str((out/'pages.bin').stat().st_size),spec)
 for field,values in [('entries',[v['root']for v in regs]),('table_slots',[v['slot']for v in regs]),('page_bases',list(records)),('page_permissions',[v[0]for v in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(r[k])for k in('pc','size','image_offset','origin'))+'}'for r in spans)+'}};',spec)
 spec+='\ninline constexpr std::array<unsigned,64> widget_whole_pages{'+','.join(hex(v)for v in whole)+'};\ninline constexpr std::array<unsigned,21> widget_extra_pages{'+','.join(hex(v)for v in extra)+'};\n';(out/'spec.hpp').write_text(spec)
 ref=text(OLD/'reference.cpp');ref=re.sub(r'std::array<void\*,119> pages',f'std::array<void*,{len(records)}> pages',ref)
 ref=ref.replace('registry_API_ledger[32]','registry_API_ledger[256]').replace('registry_initial_sizes[32]','registry_initial_sizes[256]').replace('registry_initial_bytes[32]','registry_initial_bytes[256]').replace('if(i>=32||','if(i>=256||').replace('registry_API_count<=32','registry_API_count<=256')
 ref=ref.replace('FsEvent fs_events[64]','FsEvent fs_events[2048]').replace('fs_event_count>=64','fs_event_count>=2048').replace('record_before[12],record_after[12]','record_before[16],record_after[16]').replace('sizeof(FsEvent)==1216','sizeof(FsEvent)==1224').replace('address+12<=','address+16<=').replace('reinterpret_cast<void*>(address),12','reinterpret_cast<void*>(address),16').replace('reinterpret_cast<void*>(e.record_address),12','reinterpret_cast<void*>(e.record_address),16').replace('e.record_before,e.record_after,12','e.record_before,e.record_after,16')
 # Old target observers have finite old-root bindings. Keep raw shared bodies for this new batch.
 ref=re.sub(r'const std::array<VtableHook,6>vtable_hooks\{\{.*?\}\};','const std::array<VtableHook,0>vtable_hooks{};',ref,flags=re.S)
 ref=re.sub(r'const std::array<NullHook,2> null_hooks\{\{.*?\}\};','const std::array<NullHook,0> null_hooks{};',ref,flags=re.S)
 bindings=json.loads(text(OLD/'fs-hook-bindings.json'));existing={b['PC']for b in bindings};fsnew=[]
 for row in rows:
  if 'fs:'not in row['operands']or row['pc']in existing:continue
  rawb=row['bytes_hex'];need(rawb in('64a100000000','64892500000000','64890d00000000'),'Exact supported FS source');kind={'64a100000000':0,'64892500000000':1,'64890d00000000':2}[rawb];pc=row['pc'];fsnew.append(dict(PC=pc,kind=kind,raw_bytes=rawb,continuation=pc+row['width'],declared_observer=f'fs_hook_{pc:x}'))
 declarations='\n'.join(f'extern "C" void {b["declared_observer"]}();\nextern "C" const unsigned fs_continue_{b["PC"]:x}=0x{b["continuation"]:x};'for b in fsnew)+'\n'
 ref=one(ref,'struct FsHook',declarations+'struct FsHook')
 match=re.search(r'const std::array<FsHook,(\d+)>\s*fs_hooks\{\{(.*?)\}\};',ref,re.S);need(match is not None,'Inherited FS array')
 newrows=''.join(',{0x'+format(b['PC'],'x')+','+str(len(bytes.fromhex(b['raw_bytes'])))+','+str(b['kind'])+',&'+b['declared_observer']+',{'+','.join('0x'+format(v,'x')for v in bytes.fromhex(b['raw_bytes']))+'}}'for b in fsnew)
 ref=ref[:match.start()]+f'const std::array<FsHook,{len(bindings)+len(fsnew)}>fs_hooks{{{{'+match[2]+newrows+'}};'+ref[match.end():]
 ref=one(ref,'bool mw34::original_broker::handle_debug_checkpoint','#include "widget_observer.hpp"\n\nbool mw34::original_broker::handle_debug_checkpoint')
 setup='''    auto gdi=LoadLibraryExW(L"gdi32.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);require(gdi!=nullptr,"Actual system GDI provider");
    const std::array<const char*,3> widget_names{"GetStockObject","DeleteObject","CreateFontA"};
    for(unsigned i=0;i<3;++i){widget_targets[i]=reinterpret_cast<unsigned>(GetProcAddress(gdi,widget_names[i]));require(widget_targets[i]!=0,"Genuine named GDI export");*reinterpret_cast<unsigned*>(widget_IATs[i])=widget_targets[i];}
'''
 ref=one(ref,'    auto*crtbegin=',setup+'    auto*crtbegin=')
 install='''    for(unsigned i=0;i<3;++i){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(widget_IATs[i]),4,PAGE_READWRITE,&prior),"GDI observer IAT protection");require(*reinterpret_cast<unsigned*>(widget_IATs[i])==widget_targets[i],"Actual GDI named target before observer");*reinterpret_cast<unsigned*>(widget_IATs[i])=reinterpret_cast<unsigned>(widget_entries[i]);require(VirtualProtect(reinterpret_cast<void*>(widget_IATs[i]),4,prior,&ignored),"GDI observer IAT permissions");}
    for(const auto&hook:widget_hooks){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,hook.size),"Exact whole GDI return source span");DWORD prior{},ignored{};require(VirtualProtect(code,hook.size,PAGE_EXECUTE_READWRITE,&prior),"GDI return observer protection");code[0]=0xe9;const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&d,4);for(unsigned n=5;n<hook.size;++n)code[n]=0x90;require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"GDI return observer permissions");}
'''
 ref=one(ref,'    owner=GetCurrentThreadId();',install+'    owner=GetCurrentThreadId();')
 meta='''    std::vector<unsigned> widget_identity;std::vector<unsigned> widget_modules;
    for(unsigned i=0;i<3;++i){HMODULE actual_owner{};require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(widget_targets[i]),&actual_owner),"Actual GDI forwarder owner");for(unsigned v:{widget_IATs[i],widget_targets[i],reinterpret_cast<unsigned>(widget_entries[i]),reinterpret_cast<unsigned>(gdi),reinterpret_cast<unsigned>(actual_owner)})widget_identity.push_back(v);for(unsigned m:{reinterpret_cast<unsigned>(gdi),reinterpret_cast<unsigned>(actual_owner)})if(std::find(widget_modules.begin(),widget_modules.end(),m)==widget_modules.end())widget_modules.push_back(m);}
    out.append("widget/identity.bin",widget_identity.data(),widget_identity.size()*4);
    for(unsigned m:widget_modules){std::array<wchar_t,32768> path{};const auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(m),path.data(),path.size());require(n&&n<path.size(),"Actual GDI module path");const auto bytes=read(std::filesystem::path(path.data()).string().c_str(),64*1024*1024);const auto stem="widget/modules/"+std::to_string(m);out.append(stem+"/path.bin",path.data(),(n+1)*2);out.append(stem+"/image.bin",bytes.data(),bytes.size());}
'''
 ref=one(ref,'    out.append("crt-image.bin",',meta+'    out.append("crt-image.bin",')
 ref=re.sub(r'const std::array<std::array<unsigned,3>,6> cases\{\{[^;]+;', 'const std::array<std::array<unsigned,3>,1> cases{{{0,0x37f,0}}};',ref)
 ref=one(ref,'        lockit_allocation_count=0;', '        widget_resource_count=0;std::memset(widget_resources,0,sizeof(widget_resources));\n        lockit_allocation_count=0;')
 producer='''        out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-count.bin",&registry_API_count,4);out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));
        require(registry_API_count<=256,"Bounded actual source producer API ledger");
        for(unsigned ai=0;ai<registry_API_count;++ai)if(registry_API_ledger[ai].kind==0&&registry_API_ledger[ai].after.eax){const auto stem="bootstrap/"+std::to_string(sequence)+"/producer-api-initial/"+std::to_string(ai);require(registry_initial_sizes[ai]&&registry_initial_sizes[ai]<=1024,"Actual producer full initial HeapAlloc input");out.append(stem+"/size.bin",&registry_initial_sizes[ai],4);out.append(stem+"/bytes.bin",registry_initial_bytes[ai],registry_initial_sizes[ai]);}
'''
 ref=one(ref,'        // One external game-caller projection',producer+'        // One external game-caller projection')
 initial='''            const auto registry_cap_before=HeapSize(*reinterpret_cast<HANDLE*>(0x78035000),0,reinterpret_cast<void*>(*crtbegin));require(registry_cap_before!=SIZE_T(-1)&&registry_cap_before<=512&&*crtnext>=*crtbegin&&*crtnext-*crtbegin<=registry_cap_before,"Actual entire current registry BEFORE backing");const std::array<unsigned,4> registry_before{*crtbegin,*crtnext,static_cast<unsigned>(registry_cap_before),*reinterpret_cast<unsigned*>(0x78035004)};out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/registry-before-meta.bin",registry_before.data(),sizeof(registry_before));out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/registry-before-backing.bin",reinterpret_cast<void*>(*crtbegin),registry_cap_before);
            for(unsigned i=0;i<64;++i)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/CRT-before/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);
'''
 ref=one(ref,'            r->tag.status=execute();',initial+'            r->tag.status=execute();')
 provider_after='''            for(unsigned i=0;i<64;++i)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/CRT-after/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);
'''
 ref=one(ref,'            require(registry_API_count<=256,',provider_after+'            require(registry_API_count<=256,')

 ref=one(ref,'            auto r=std::make_unique<Record>();','            widget_count=0;widget_error=0;std::memset(widget_snapshots,0,sizeof(widget_snapshots));\n            auto r=std::make_unique<Record>();')
 before='''            for(unsigned p:widget_extra_pages)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/extra-before/"+std::to_string(p)+".bin",reinterpret_cast<void*>(p),4096);
'''
 ref=one(ref,'            r->tag.status=execute();',before+'            r->tag.status=execute();')
 after='''            const auto wstem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/widget";out.append(wstem+"-count.bin",&widget_count,4);out.append(wstem+"-snapshots.bin",widget_snapshots,widget_count*sizeof(WidgetSnapshot));out.append(wstem+"-segments.bin",widget_segments,widget_count*sizeof(WidgetSegments));out.append(wstem+"-resources.bin",widget_resources,widget_resource_count*sizeof(WidgetResource));
            for(unsigned p:widget_extra_pages)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/extra-after/"+std::to_string(p)+".bin",reinterpret_cast<void*>(p),4096);
            for(unsigned ai=0;ai<registry_API_count;++ai)if(registry_API_ledger[ai].kind==0&&registry_API_ledger[ai].after.eax){const auto pointer=registry_API_ledger[ai].after.eax;const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(pointer));require(cap==registry_initial_sizes[ai],"Every actual new allocation complete endpoint capacity");const auto stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/api-final/"+std::to_string(ai);out.append(stem+"/bytes.bin",reinterpret_cast<void*>(pointer),cap);}
'''
 ref=one(ref,'            require(registry_API_count<=256,',after+'            require(registry_API_count<=256,')
 ref=one(ref,'            if(r->tag.status||','            if(widget_error||r->tag.status||')
 hookproof='''for(const auto&hook:widget_hooks)if(hook.pc<=span.pc&&span.pc+span.size<=hook.pc+hook.size){const unsigned off=span.pc-hook.pc;require(!std::memcmp(origin.data()+span.image_offset,hook.raw+off,span.size),"Exact GDI return physical source input");const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);for(unsigned n=0;n<span.size;++n){const unsigned relative=off+n;const unsigned char expected=relative==0?0xe9:relative<5?static_cast<unsigned char>(d>>(8*(relative-1))):0x90;require(*reinterpret_cast<unsigned char*>(span.pc+n)==expected,"Exact declared GDI return observer byte");}hooked=true;}'''
 ref=one(ref,'if(!hooked)require(',hookproof+'if(!hooked)require(')
 ref=one(ref,'        require(*crtnext==*crtbegin,"Actual FCOS root registers no callback");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),0);','        require(*crtnext>=*crtbegin&&*crtnext-*crtbegin<=512,"Actual current bounded registrations");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),*crtnext-*crtbegin);')
 ref=one(ref,'        require(!lockit_allocation_count&&!container_allocation_count&&!fs_allocation_count,"Actual cosine prefix has no owned allocation observations");','''        require(!lockit_allocation_count&&!container_allocation_count&&!fs_allocation_count,"No old finite owner contract used for new widgets");
        for(unsigned i=0;i<widget_resource_count;++i)if(widget_resources[i].live){const auto c=widget_cleanup_resource(i);out.append("cleanup/"+std::to_string(sequence)+"/owned-font/"+std::to_string(i)+".bin",&c,sizeof(c));require(c.BOOL_result!=0,"Actual owned font manual cleanup succeeded");}
        out.append("cleanup/"+std::to_string(sequence)+"/resources.bin",widget_resources,widget_resource_count*sizeof(WidgetResource));
''')
 restore='''    for(unsigned i=0;i<3;++i){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(widget_IATs[i]),4,PAGE_READWRITE,&prior),"GDI IAT restoration protection");require(*reinterpret_cast<unsigned*>(widget_IATs[i])==reinterpret_cast<unsigned>(widget_entries[i]),"Exact GDI observer before restoration");*reinterpret_cast<unsigned*>(widget_IATs[i])=widget_targets[i];require(VirtualProtect(reinterpret_cast<void*>(widget_IATs[i]),4,prior,&ignored),"GDI named IAT restored");}
    for(const auto&hook:widget_hooks){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,PAGE_EXECUTE_READWRITE,&prior),"GDI return source restoration");std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size);require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(hook.pc),hook.size),"Exact GDI source bytes restored");}
'''
 ref=one(ref,'    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){',restore+'    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){')
 ref=one(ref,'            require(actual[byte]==(pc>=capture_pc','            bool gdi_byte=false;for(unsigned gi=0;gi<3;++gi)if(widget_IATs[gi]<=pc&&pc<widget_IATs[gi]+4){require(actual[byte]==reinterpret_cast<const unsigned char*>(&widget_targets[gi])[pc-widget_IATs[gi]],"Exact measured named GDI IAT after restoration");gdi_byte=true;}if(gdi_byte)continue;\n            require(actual[byte]==(pc>=capture_pc')
 ref=ref.replace('Six genuine FCOS initializer hardware endpoints captured','Five genuine widget initializer endpoints captured');(out/'reference.cpp').write_text(ref)
 protocol=one(text(OLD/'protocol.hpp'),'sequences=6, roots=1','sequences=1, roots=5');(out/'protocol.hpp').write_text(protocol)
 for fn in('original_broker.hpp','reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm'):(out/fn).write_text(text(OLD/fn))
 registryasm=(out/'reference_x86.asm').read_text()
 registryasm=one(registryasm,'EXTERN registry_API_ledger:BYTE','EXTERN registry_API_ledger:BYTE\nEXTERN fs_error:DWORD')
 registryasm=one(registryasm,' mov eax,registry_API_count\n dec eax\n imul eax,eax,104',' mov eax,registry_API_count\n dec eax\n cmp eax,256\n jae api_ledger_overflow\n imul eax,eax,104')
 registryasm=one(registryasm,' push DWORD PTR registry_API_after[32]',' jmp api_ledger_restore\napi_ledger_overflow:\n mov fs_error,1\napi_ledger_restore:\n push DWORD PTR registry_API_after[32]')
 (out/'reference_x86.asm').write_text(registryasm)
 fsasm=text(OLD/'fs_observer_x86.asm');template=re.search(r'PUBLIC fs_hook_4e78d7\nfs_hook_4e78d7 PROC\n.*?fs_hook_4e78d7 ENDP\n',fsasm,re.S)[0];generated=[]
 for b in fsnew:
  pc=b['PC'];v=template.replace('4e78d7',format(pc,'x')).replace(' mov fs_event_kind,0',f' mov fs_event_kind,{b["kind"]}').replace(' db 064h,0a1h,000h,000h,000h,000h',' db '+','.join('0'+format(x,'02x')+'h'for x in bytes.fromhex(b['raw_bytes'])));generated.append(v)
 fsasm=one(fsasm,'.code\n','\n'.join(f'EXTERN fs_continue_{b["PC"]:x}:DWORD'for b in fsnew)+'\n.code\n');fsasm=one(fsasm,'END\n',''.join(generated)+'END\n');(out/'fs_observer_x86.asm').write_text(fsasm);(out/'fs-hook-bindings.json').write_text(json.dumps(bindings+fsnew,indent=2)+'\n')
 (out/'widget_observer.hpp').write_text(text(R/'tools/m4-widget-original/widget_observer_v2.hpp'))
 asm='.686p\n.xmm\n.model flat,C\nassume fs:nothing\noption casemap:none\n'+'\n'.join('EXTERN '+n+':'+t for n,t in [('mixed_host_esp','DWORD'),('widget_head','DWORD'),('widget_ds','WORD'),('widget_es','WORD'),('widget_ss','WORD'),('widget_cpu','BYTE'),('widget_fx','BYTE'),('widget_env','BYTE'),('widget_kind','DWORD'),('widget_targets','DWORD'),('widget_continues','DWORD'),('widget_observe','PROC')])+'\n.code\n'
 for i,(name,rawb)in enumerate([('stock','898658020000'),('delete','c7865802000000000000'),('create','85c0898658020000')]):asm+=bridge('widget_'+name+'_entry',i,0,b'')+bridge('widget_'+name+'_return',i,1,bytes.fromhex(rawb))
 (out/'widget_observer_x86.asm').write_text(asm+'END\n');(out/'CMakeLists.txt').write_text(one(text(OLD/'CMakeLists.txt'),'lockit_observer_x86.asm "','lockit_observer_x86.asm widget_observer_x86.asm "'))
 # Explicit normal patches, no tracing worker and no trace admission in this receipt.
 patches=[dict(family='FS',PC=b['PC'],size=len(bytes.fromhex(b['raw_bytes'])),raw=b['raw_bytes'])for b in bindings+fsnew]+[dict(family='GDI-return',PC=p,size=n,raw=b)for p,n,b in[(0x5a0142,6,'898658020000'),(0x5a0645,10,'c7865802000000000000'),(0x5a0751,8,'85c0898658020000')]]
 patches += [dict(family='Lockit',PC=p,size=n,raw=b)for p,n,b in[(0x7810a290,5,'a158561478'),(0x7810a311,5,'8bc75f5ec3'),(0x7810a350,7,'833d5856147802'),(0x7810a364,5,'c390909090')]]
 patches += [dict(family='capture-broker',PC=0x410a80,size=5,raw=None),dict(family='source-sentinel-terminal',PC=0x5ac3ec,size=5,raw=None)]
 for i,a in enumerate(patches):
  for b in patches[i+1:]:need(a['PC']+a['size']<=b['PC']or b['PC']+b['size']<=a['PC'],'All current source patch spans disjoint')
 (out/'normal-contracts.json').write_text(json.dumps(dict(plan_sha256=sha(planp),roots=regs,instructions=rows,physical_added_pages=physical_pages,whole_pages=whole,external_pages=extra,normal_patch_spans=patches,GDI_hook_replays=[dict(pc=p,size=n,raw=b)for p,n,b in[(0x5a0142,6,'898658020000'),(0x5a0645,10,'c7865802000000000000'),(0x5a0751,8,'85c0898658020000')]],source_FS_view_bytes=16,source_FS_semantic_width='12B constructor records;16B vector helper; observer raw16B view retains extra source caller DWORD explicitly',normal_counts_are_unmeasured=True,normal_initial_heap_owners_unclassified=True,strdup_owner_claim=False,registered_shutdown_callbacks_executed=False,source_failure_unwind_admitted=False,manual_font_cleanup_scope='Only actual successful CreateFontA handles still live, genuine DeleteObject call; research cleanup is not source callback execution',trace_admitted=False,trace_prerequisite='Independently decode reached union; remove every active overlapping source patch, validate all physical first opcodes before any INT3 patch;CONTROL-only debugger writes; no retained hook silently overrides traced source.'),indent=2)+'\n')
 pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v5.py');pin(R/'tools/m4-widget-original/prepare_v4.py');pin(R/'reports/m4-widget-original/preparation-r5/report.json','fe867d85c6ac4246624467c4fe11ec9271ba5e9dcd01e6b89fba3f3c9c673c30');pin(R/'tools/m4-widget-original/derive_prepare_v4.py');pin(R/'tools/m4-widget-original/widget_observer.hpp');pin(R/'tools/m4-widget-original/prepare_v3.py');pin(R/'reports/m4-widget-original/preparation-r4/report.json','877c05e96e45d2d926bd9c2438bb2b07c1d52f010d47f8bcb7c79e3f50a22821');pin(R/'tools/m4-widget-original/derive_prepare_v3.py');pin(R/'tools/m4-widget-original/prepare_v2.py');pin(R/'reports/m4-widget-original/preparation-r3/report.json','86f4a947c7cc870a0519ab9a49128beb751174718ebdf73713a1f9535d463172');pin(R/'tools/m4-widget-original/prepare.py');pin(R/'tools/m4-widget-original/derive_prepare_v2.py');pin(R/'reports/m4-widget-original/preparation-r2/report.json','54597ffb3c9d84fd1ad92758be4b57fa5f92f5b171bed57b17882ba3e9f1556a');pin(R/'tools/m4-capture-direct/capture_direct_v3.cpp');pin(R/'tools/m4-capture-direct/capture_direct_v3.hpp')
 for p in out.iterdir():pin(p)
 report=dict(passed=True,scope='Authentic loader/producer plus bounded five-widget normal original worker preparation; no execution or source/runtime credit',parent_preparation_sha256=sha(CURRENT/'report.json'),minimal_bootstrap_sha256=sha(OLD/'report.json'),original_sequences=1,original_roots=5,original_phases=5,record_bytes=356992,ordinary_pages=43,external_pages=extra,combined_source_pages=64,snapshot_bytes=266964,snapshot_count_bound=384,actual_GDI_selector_descriptor_bytes_per_boundary=40,actual_DS_ES_SS_flatness_observation_prepared=True,whole_CRT_phase_endpoint_pages=64,actual_registry_BEFORE_full_capacity=True,authentic_producer_API_initial_inputs_retained=True,FS_event_bytes=1224,FS_event_bound=2048,FS_hooks=len(bindings)+len(fsnew),game_rows=1081,game_instruction_bytes=3350,sparse_pack_pages=len(records),source_spans=spans,observed_pages=cur['observed_pages'],pack_sha256=sha(out/'pages.bin'),original_executed=False,trace_executed=False,trace_admitted=False,source_after_seed=False,predicted_counts_supplied_to_execution=False,provider_preinvoked=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,preparation=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
