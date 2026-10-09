"""Fresh connected original54, real32CRT provider and typed host-stack API shims."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];BASE=ROOT/'reports/m4-onexit-source'
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
OLD=ROOT/'reports/m4-joint-startup28-original/preparation-r3'
APIS=(('HeapAlloc',0x7802e094,3),('HeapFree',0x7802e090,3),('HeapSize',0x7802e1dc,3),('HeapReAlloc',0x7802e0b4,4),('InitializeCriticalSection',0x7802e03c,1),('EnterCriticalSection',0x7802e044,1),('LeaveCriticalSection',0x7802e048,1),('DeleteCriticalSection',0x7802e040,1))
DATA=(0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000)
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original preparation');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or h==v,'Pinned original source '+str(p));files[str(p)]=v;return p
 def read(p):return pin(p).read_text(encoding='utf-8-sig')
 def one(s,a,b):need(s.count(a)==1,'Unique original derivation '+a[:50]);return s.replace(a,b)
 oldrep=json.loads(pin(OLD/'report.json','ae37cdfc494e3aa73b966c0d532ef94f0b2830b69203a72eb30e0567d4680bbb').read_bytes());oldpack=pin(OLD/'pages.bin',oldrep['pack_sha256']).read_bytes();records={struct.unpack_from('<I',oldpack,12+i*4104)[0]:(struct.unpack_from('<I',oldpack,16+i*4104)[0],bytearray(oldpack[20+i*4104:4116+i*4104]))for i in range(29)}
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());graph=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/game-normal-graphs.json').read_bytes());inputs=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registry-inputs.json').read_bytes());iface=json.loads(pin(BASE/'interface-r1/instruction-contracts.json').read_bytes());order=iface['selected_order']
 def page(a):
  try:off,_=game.rva_range(a-game.image_base,4096);return bytearray(game.data[off:off+4096])
  except ValueError:return bytearray(4096)
 for a in DATA:records[a]=(0 if a in(0x5ca000,0x5ed000)else 2,page(a))
 rows={r['pc']:r for g in graph.values()for r in g['instructions']};rows.update({r['pc']:r for r in inputs['game_sentinel_rows']});spans=oldrep['source_spans'].copy()
 for r in rows.values():
  a=r['pc'];p=a&~4095
  if p not in records:records[p]=(1,bytearray(b'\xcc'*4096))
  raw=bytes.fromhex(r['bytes']);off,_=game.rva_range(a-game.image_base,len(raw));need(game.data[off:off+len(raw)]==raw,'Exact originalgame row');records[p][1][a&4095:(a&4095)+len(raw)]=raw;spans.append(dict(pc=a,size=len(raw),image_offset=off,origin=0))
 records[0x20000000]=(2,bytearray(4096));records[0x20002000]=(2,bytearray(4096))
 addresses=list(records);pack=b'MW4J54P1'+struct.pack('<I',len(addresses))+b''.join(struct.pack('<2I',a,p)+raw for a,(p,raw)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=read(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for n,values in (('entries',[r['entry']for r in order]),('table_slots',[r['slot']for r in order]),('page_bases',addresses),('page_permissions',[p for p,b in records.values()])):
  spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+n+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+n+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(x[k])for k in('pc','size','image_offset','origin'))+'}'for x in spans)+'}};',spec);(out/'spec.hpp').write_text(spec)
 observed=list(oldrep['observed_pages'])+list(DATA);protocol=read(OLD/'protocol.hpp').replace('roots=28','roots=54').replace('observed_page_count=17',f'observed_page_count={len(observed)}').replace('0x608000,0x482000};','0x608000,0x482000,'+','.join(hex(a)for a in DATA)+'};').replace('sizeof(Record)==143472',f'sizeof(Record)=={143472+2*len(DATA)*4096+16+512}').replace('memory_size==69632',f'memory_size=={len(observed)*4096}')
 protocol=one(protocol,'    Service spi;','    Service spi;\n    std::uint32_t registry_begin,registry_next,registry_capacity,registry_mode;\n    std::array<std::uint8_t,512> registry_bytes;');(out/'protocol.hpp').write_text(protocol)
 broker=read(OLD/'original_broker.hpp');bases=[0x400000,0x410000,0x430000,0x460000,0x480000,0x4a0000,0x4b0000,0x4c0000,0x5b0000,0x5c0000,0x5e0000,0x600000,0x20000000,0x780c0000,0x78110000]+sorted({a&~65535 for a in addresses}-{0x400000,0x410000,0x430000,0x460000,0x480000,0x4a0000,0x4b0000,0x4c0000,0x5b0000,0x5c0000,0x5e0000,0x600000,0x20000000,0x780c0000,0x78110000});broker=re.sub(r'std::array<std::uint32_t,15> bases\{[^;]+;',f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(a)for a in bases)+'};',broker)
 broker=broker.replace('const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;','const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;std::cerr<<"Original54 debugexception code="<<std::hex<<code<<" pc="<<event.u.Exception.ExceptionRecord.ExceptionAddress<<" first="<<event.u.Exception.dwFirstChance<<std::dec<<"\\n";')
 (out/'original_broker.hpp').write_text(broker)
 asm=read(OLD/'reference_x86.asm');extern='\nEXTERN registry_API_active:DWORD\nEXTERN registry_API_targets:DWORD\nEXTERN registry_API_counts:DWORD\nEXTERN registry_API_kind:DWORD\nEXTERN registry_API_before:BYTE\nEXTERN registry_API_after:BYTE\nEXTERN registry_API_args:DWORD\nEXTERN registry_API_ret:DWORD\nEXTERN registry_API_fx:BYTE\nEXTERN registry_API_env:BYTE\nEXTERN registry_API_count:DWORD\n'
 for i in range(len(APIS)):extern+=f'PUBLIC registry_API_{i}\n'
 body='\n'
 extern+='EXTERN registry_API_entry_ecx:DWORD\n'
 for i in range(len(APIS)):body+=f'registry_API_{i} PROC\n mov registry_API_entry_ecx,ecx\n mov ecx,registry_API_active\n jecxz registry_API_{i}_outside\n mov ecx,registry_API_entry_ecx\n mov registry_API_kind,{i}\n jmp registry_API_common\nregistry_API_{i}_outside:\n mov ecx,registry_API_entry_ecx\n jmp DWORD PTR registry_API_targets[{i*4}]\nregistry_API_{i} ENDP\n'
 body+='registry_API_common PROC\n'
 for i,r in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):body+=f' mov DWORD PTR registry_API_before[{4*i}],{r}\n'
 body+=' mov eax,DWORD PTR [esp]\n mov registry_API_ret,eax\n mov esp,mixed_host_esp\n pushfd\n pop DWORD PTR registry_API_before[32]\n fxsave registry_API_fx\n fnstenv registry_API_env\n fldenv registry_API_env\n'
 body+=' mov eax,registry_API_kind\n mov ecx,DWORD PTR registry_API_counts[eax*4]\n mov edx,DWORD PTR registry_API_before[16]\napi_args_loop:\n mov eax,DWORD PTR [edx+ecx*4]\n mov DWORD PTR registry_API_args[ecx*4-4],eax\n push eax\n loop api_args_loop\n'
 body+=' mov eax,registry_API_kind\n mov registry_API_active,0\n call DWORD PTR registry_API_targets[eax*4]\n mov registry_API_active,1\n'
 for i,r in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):body+=f' mov DWORD PTR registry_API_after[{4*i}],{r}\n'
 body+=' pushfd\n pop DWORD PTR registry_API_after[32]\n inc registry_API_count\n mov eax,registry_API_kind\n mov ecx,DWORD PTR registry_API_counts[eax*4]\n mov edx,DWORD PTR registry_API_before[16]\n lea edx,[edx+ecx*4+4]\n mov DWORD PTR registry_API_after[16],edx\n push DWORD PTR registry_API_after[32]\n popfd\n'
 for i,r in enumerate(('eax','ecx','edx','ebx','ebp','esi','edi')):idx=('eax','ecx','edx','ebx','esp','ebp','esi','edi').index(r);body+=f' mov {r},DWORD PTR registry_API_after[{4*idx}]\n'
 body+=' mov esp,DWORD PTR registry_API_after[16]\n jmp registry_API_ret\nregistry_API_common ENDP\n'
 asm=one(asm,'.code',extern+'.code');asm=one(asm,'\nEND\n','\n'+body+'END\n');(out/'reference_x86.asm').write_text(asm)
 ref=read(OLD/'reference.cpp');decl='std::uint32_t registry_API_targets[8]{},registry_API_counts[8]{3,3,3,4,1,1,1,1},registry_API_kind{},registry_API_args[4]{},registry_API_ret{},registry_API_count{};\nCpu registry_API_before{},registry_API_after{};\nalignas(16) std::uint8_t registry_API_fx[512]{};std::uint8_t registry_API_env[28]{};\n'+''.join(f'void registry_API_{i}();\n'for i in range(8))
 decl+='std::uint32_t registry_API_active{},registry_API_entry_ecx{};\n'
 ref=one(ref,'void mixed_enter();void mixed_capture();void mixed_restore();',decl+'void mixed_enter();void mixed_capture();void mixed_restore();');ref=ref.replace('MW4J28','MW4J54').replace('original28','original54').replace('std::array<void*,29>',f'std::array<void*,{len(addresses)}>')
 ref=one(ref,'static std::uint32_t execute(){__try{mixed_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){const auto code=GetExceptionCode();mixed_restore();return code;}}','static std::uint32_t execute(){__try{registry_API_active=1;mixed_enter();registry_API_active=0;return 0;}__except(EXCEPTION_EXECUTE_HANDLER){const auto code=GetExceptionCode();registry_API_active=0;mixed_restore();return code;}}')
 load='''    const auto crtpath=std::filesystem::path("D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCRT.DLL");const auto crtbytes=read(crtpath.string().c_str(),266293);require(sha256(crtbytes)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Actual oldCRT image identity");
    auto crt=LoadLibraryExW(crtpath.c_str(),nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(reinterpret_cast<std::uintptr_t>(crt)==0x78000000,"Actual32CRT preferred canonical base required");
    const auto original_onexit=GetProcAddress(crt,"_onexit"),original_dllonexit=GetProcAddress(crt,"__dllonexit");require(reinterpret_cast<std::uintptr_t>(original_onexit)==0x78004a36&&reinterpret_cast<std::uintptr_t>(original_dllonexit)==0x78002fe5,"Actual source export identity");
    using OriginalFree=void(__cdecl*)(void*);const auto original_free=reinterpret_cast<OriginalFree>(GetProcAddress(crt,"free"));require(reinterpret_cast<std::uintptr_t>(original_free)==0x78001390,"Actual free export identity");
    auto*crtbegin=reinterpret_cast<unsigned*>(0x7803788c);auto*crtnext=reinterpret_cast<unsigned*>(0x78037888);require(*crtbegin&&*crtnext==*crtbegin,"Loaded CRT empty registry required");original_free(reinterpret_cast<void*>(*crtbegin));*crtbegin=0;*crtnext=0;
    *reinterpret_cast<unsigned*>(0x5bb52c)=reinterpret_cast<std::uintptr_t>(original_onexit);*reinterpret_cast<unsigned*>(0x5bb530)=reinterpret_cast<std::uintptr_t>(original_dllonexit);
'''
 load+='    const std::array<void(*)(),8> registry_shims{'+','.join('&registry_API_'+str(i)for i in range(8))+'};\n'
 for i,(api,iat,argc)in enumerate(APIS):load+=f'    registry_API_targets[{i}]=*reinterpret_cast<unsigned*>({hex(iat)});require(registry_API_targets[{i}]==reinterpret_cast<std::uintptr_t>(GetProcAddress(GetModuleHandleW(L"kernel32.dll"),"{api}")),"Actual32API namedexport target");{{DWORD oldprotect{{}},ignored{{}};require(VirtualProtect(reinterpret_cast<void*>({hex(iat)}),4,PAGE_READWRITE,&oldprotect),"CRT owningIAT writable");*reinterpret_cast<unsigned*>({hex(iat)})=reinterpret_cast<std::uintptr_t>(registry_shims[{i}]);require(VirtualProtect(reinterpret_cast<void*>({hex(iat)}),4,oldprotect,&ignored),"CRT owningIAT protection restored");}}\n'
 load+='    const std::array<unsigned,8> registry_IATs{'+','.join(hex(a)for n,a,c in APIS)+'};\n'
 load+='''    struct RegistryCleanup {unsigned*begin,*next;OriginalFree release;std::array<unsigned,8> iats;void restore()noexcept{for(unsigned i=0;i<8;++i){DWORD old{},ignored{};if(VirtualProtect(reinterpret_cast<void*>(iats[i]),4,PAGE_READWRITE,&old)){*reinterpret_cast<unsigned*>(iats[i])=registry_API_targets[i];VirtualProtect(reinterpret_cast<void*>(iats[i]),4,old,&ignored);}}}~RegistryCleanup(){restore();if(*begin)release(reinterpret_cast<void*>(*begin));*begin=0;*next=0;}} registry_cleanup{crtbegin,crtnext,original_free,registry_IATs};
'''
 load=load.replace('auto crt=LoadLibraryExW','std::cerr<<"Original54 loadingCRT\\n";auto crt=LoadLibraryExW').replace('original_free(reinterpret_cast<void*>(*crtbegin));','std::cerr<<"Original54 reclaimloader table\\n";original_free(reinterpret_cast<void*>(*crtbegin));',1)
 ref=one(ref,'    auto user=LoadLibraryExW',load+'    std::cerr<<"Original54 APIshimsready\\n";auto user=LoadLibraryExW')
 ref=one(ref,'    unsigned sequence{};','    out.append("crt-image.bin",crtbytes.data(),crtbytes.size());out.append("crt-api-targets.bin",registry_API_targets,sizeof(registry_API_targets));\n    unsigned sequence{};')
 bootstrap='''        // Actual original sentinel source fragment: authored terminal capture follows20bytes.
        auto*sentinel_end=reinterpret_cast<std::uint8_t*>(0x5ac3ec);protect(reinterpret_cast<void*>(0x5ac000),PAGE_EXECUTE_READWRITE);sentinel_end[0]=0xe9;const auto sentinel_delta=static_cast<unsigned>(capture_pc-(0x5ac3ec+5));std::memcpy(sentinel_end+1,&sentinel_delta,4);protect(reinterpret_cast<void*>(0x5ac000),PAGE_EXECUTE_READ);require(FlushInstructionCache(GetCurrentProcess(),sentinel_end,5),"Sentinel terminal cache");
        mixed_input.pc=0x5ac3d8;std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);require(execute()==0&&*reinterpret_cast<unsigned*>(0x9a17ec)==0xffffffff&&*reinterpret_cast<unsigned*>(0x9a17f0)==0xffffffff,"Actual source sentinel effects");
        std::memcpy(mixed_guest_fx,mixed_fx_after,512);std::memcpy(mixed_guest_env,mixed_env_after,28);mixed_env_ready=1;
        mixed_input=mixed_after;mixed_input.esp=frame;mixed_input.pc=0x78004482;std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);require(execute()==0&&mixed_after.pc==capture_pc&&mixed_after.esp==frame+4&&*crtbegin&&*crtnext==*crtbegin&&*reinterpret_cast<unsigned*>(*crtbegin)==0,"Actual original registry producer CALL/RET");
        out.append("bootstrap/"+std::to_string(sequence)+"/producer-after-cpu.bin",&mixed_after,sizeof(mixed_after));out.append("bootstrap/"+std::to_string(sequence)+"/producer-after-fx.bin",mixed_fx_after,512);out.append("bootstrap/"+std::to_string(sequence)+"/producer-after-env.bin",mixed_env_after,28);
        std::memcpy(mixed_guest_fx,mixed_fx_after,512);std::memcpy(mixed_guest_env,mixed_env_after,28);mixed_env_ready=1;
        // One external game-caller projection, preserving producerFX/pages/owners.
        mixed_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entries[0]};
'''
 ref=one(ref,'        for(unsigned phase=0;phase<entries.size();++phase){',bootstrap+'        for(unsigned phase=0;phase<entries.size();++phase){')
 ref=one(ref,'            r->tag.status=execute();copy_capture(*r);', '            registry_API_count=0;\n            r->tag.status=execute();copy_capture(*r);')
 ref=one(ref,'            out.append("phase/"','''            r->registry_begin=*crtbegin;r->registry_next=*crtnext;r->registry_mode=*reinterpret_cast<unsigned*>(0x78035004);const auto actual_heap=*reinterpret_cast<HANDLE*>(0x78035000);const auto capacity=HeapSize(actual_heap,0,reinterpret_cast<void*>(*crtbegin));require(capacity!=SIZE_T(-1)&&capacity<=512&&*crtnext>=*crtbegin&&*crtnext-*crtbegin<=capacity,"Actual bounded registry capacity");r->registry_capacity=static_cast<unsigned>(capacity);std::memcpy(r->registry_bytes.data(),reinterpret_cast<void*>(*crtbegin),capacity);
            out.append("phase/"''')
 cleanup='''        require(*crtnext-*crtbegin==26*4,"Exact26callback vectorextent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),26*4);
        // Genuine free itself executes on the real caller stack, with originalimports.
        registry_cleanup.restore();original_free(reinterpret_cast<void*>(*crtbegin));*crtbegin=0;*crtnext=0;
        for(unsigned i=0;i<8;++i){DWORD old{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(registry_IATs[i]),4,PAGE_READWRITE,&old),"CRT IAT shim reentry");*reinterpret_cast<unsigned*>(registry_IATs[i])=reinterpret_cast<std::uintptr_t>(registry_shims[i]);require(VirtualProtect(reinterpret_cast<void*>(registry_IATs[i]),4,old,&ignored),"CRT IAT reentry protection");}
        ++sequence;'''
 ref=one(ref,'        ++sequence;',cleanup)
 ref=one(ref,'            if(pc>=0x5bb6dc&&pc<0x5bb6e0)continue;','            if((pc>=0x5bb6dc&&pc<0x5bb6e0)||(pc>=0x5bb52c&&pc<0x5bb534)||(pc>=0x5ac3ec&&pc<0x5ac3f1))continue;')
 # The sentinel terminal patch is outside every executed source row.
 ref=ref.replace('6 connected sequences / 168 actual original initializer phases captured','6 connected sequences /324actual original initializer phases captured')
 ref=ref.replace('    std::array<void*,','    std::cerr<<"Original54 packvalidated\\n";std::array<void*,',1).replace('    const auto crtpath=','    std::cerr<<"Original54 mappedsource\\n";const auto crtpath=',1).replace('    mw34::capture_direct::Writer out','    std::cerr<<"Original54 writerready\\n";mw34::capture_direct::Writer out',1)
 ref=ref.replace('Header header{};','std::cerr<<"Original54 writerconstructed\\n";Header header{};',1).replace('    unsigned sequence{};','    std::cerr<<"Original54 writermetadataready\\n";unsigned sequence{};',1).replace('mixed_input.pc=0x5ac3d8;','std::cerr<<"Original54 sentinelstart\\n";mixed_input.pc=0x5ac3d8;',1).replace('mixed_input=mixed_after;mixed_input.esp=frame;mixed_input.pc=0x78004482;','std::cerr<<"Original54 producerstart\\n";mixed_input=mixed_after;mixed_input.esp=frame;mixed_input.pc=0x78004482;',1)
 (out/'reference.cpp').write_text(ref);(out/'preserve_x86.asm').write_text(read(OLD/'preserve_x86.asm'));cmake=read(OLD/'CMakeLists.txt').replace('Startup28','Startup54').replace('startup28','startup54');(out/'CMakeLists.txt').write_text(cmake)
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(Path(__file__));report=dict(passed=True,scope='Fresh original54preparation; real32oldCRT+Windows APIs, literalgame roots; noexecutioncredit',order=order,observed_pages=observed,page_count=len(addresses),pack_sha256=sha(out/'pages.bin'),record_bytes=143472+2*len(DATA)*4096+16+512,files=files,API_shims=APIS,loader_DLL_init='Actual32 oldCRT DllMain/initializers are outside selectednativeattachclaims',caller_projection='One fixedcallerGPR/flags/PC/ESP afteractualsentinel+producer, preservingFX/pages/liveowners',cleanup='Genuine free currentvector then explicitly clearbegin/next so no guestcallback executesonDLL/processdetach',native_executed=False,original_executed=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),page_count=len(addresses),observed_pages=len(observed),record_bytes=report['record_bytes'])))
if __name__=='__main__':main(sys.argv[1])
