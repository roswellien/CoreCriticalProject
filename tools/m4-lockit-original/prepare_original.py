"""Additive genuine loaded-MSVC original124, with exact observer/owner inputs."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-lockit-original';OLD=ROOT/'reports/m4-vtable-original/preparation-r3';SRC=ROOT/'reports/m4-lockit-source/recovery-r1';PROBE=BASE/'probe-preparation-r2'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise ValueError(w)
def one(s,a,b):need(s.count(a)==1,'Exact one replacement '+a[:60]);return s.replace(a,b,1)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original124 preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'No pin conflict');pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','a2e7635100478713acbc5efbc7557ba20ac8d060c461241b2ef1785b291105b5').read_bytes());rec=json.loads(pin(SRC/'report.json','25a04a5a9e4cec894c5272d398794850aeab968a22f77b21494706680015fa4d').read_bytes())
 for parent in(old,rec):
  for p,h in parent['files'].items():pin(p,h)
 authentic=json.loads(pin(BASE/'probe-validation-r1/report.json','ae8fe51982fbc608fa5b3f3b529acaca67baac508f9539e4ae00cb10be31f9c2').read_bytes());need(authentic['passed']and authentic['post_DllMain_state']==2,'Authentic initialized domain')
 for p,h in authentic['files'].items():pin(p,h)
 gi=json.loads(pin(SRC/'instruction-contracts.json').read_bytes());need(len(gi['selected_order'])==124 and len(gi['roots'])==4,'Frozen four-root selected124 order')
 game=PEImage(pin(ROOT/'MW3/Mech3.exe').read_bytes());provider=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').read_bytes());raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',raw,8)[0])}
 # The actual DLL owns these two previously sparse/raw numeric pages now.
 removed={p:records.pop(p)for p in(0x780c1000,0x78115000)};spans=list(old['source_spans']);known={s['pc']:s for s in spans}
 for r in gi['instructions']:
  pc=r['pc'];code=bytes.fromhex(r.get('bytes_hex',r.get('bytes')));off,_=game.rva_range(pc-game.image_base,len(code));need(game.data[off:off+len(code)]==code,'Exact original game instruction')
  if pc in known:need(known[pc]['size']==len(code)and known[pc]['image_offset']==off,'Identical accepted instruction');continue
  base=pc&~4095;need(pc+len(code)<=base+4096,'Single-page source');
  if base not in records:records[base]=(1,bytearray(b'\xcc'*4096))
  records[base][1][pc&4095:(pc&4095)+len(code)]=code;spans.append(dict(pc=pc,size=len(code),image_offset=off,origin=0));known[pc]=spans[-1]
 initialized=json.loads(pin(ROOT/'reports/m4-lockit-frontier/recovery-r1/initialized-provider-path.json').read_bytes())
 for r in initialized['constructor_rows']+initialized['destructor_rows']:
  pc=r['pc'];code=bytes.fromhex(r['bytes']);off,_=provider.rva_range(pc-provider.image_base,len(code));need(provider.data[off:off+len(code)]==code,'Exact initialized provider instruction');spans.append(dict(pc=pc,size=len(code),image_offset=off,origin=1))
 out.mkdir(parents=True);pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',a,p)+code for a,(p,code)in records.items());(out/'pages.bin').write_bytes(pack)
 observed=old['observed_pages']+[0x7810a000,0x78145000,0x78146000];need(len(observed)==43,'43 complete observed pages');spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for key,vals in [('entries',[r['entry']for r in gi['selected_order']]),('table_slots',[r['slot']for r in gi['selected_order']]),('page_bases',list(records)),('page_permissions',[p for p,code in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+key+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(vals)}> '+key+'{'+','.join(hex(v)for v in vals)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(s[k])for k in('pc','size','image_offset','origin'))+'}'for s in spans)+'}};',spec)
 alloc=gi['allocations'];spec+='\ninline constexpr std::array<FsAllocationBinding,8> lockit_allocation_bindings{{'+','.join('{'+','.join(hex(r[k])for k in('root','CALL_pc','requested'))+'}'for r in alloc)+'}};\n'
 spec+='struct LockitRoot{unsigned root,object,header,counter,request;};\ninline constexpr std::array<LockitRoot,4>lockit_roots{{'+','.join('{'+','.join(hex(v)for v in(r['entry'],r['objects'][0]['address'],r['header_global'],r['header_counter'],r['allocation_request']))+'}'for r in rec['roots'])+'}};\n'
 (out/'spec.hpp').write_text(spec)
 protocol=text(OLD/'protocol.hpp').replace('roots=120','roots=124').replace('observed_page_count=40','observed_page_count=43').replace('sizeof(Record)==332416','sizeof(Record)==356992');protocol=one(protocol,'0x5bc000,0x5cf000,0x5fc000};','0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000};');(out/'protocol.hpp').write_text(protocol)
 broker=text(OLD/'original_broker.hpp');m=re.search(r'std::array<std::uint32_t,\d+> bases\{([^;]+)\};',broker);bases=[int(x,16)for x in m[1].split(',')if int(x,16)not in(0x780c0000,0x78110000)];bases=list(dict.fromkeys(bases+[a&~65535 for a in records]));need(all(a<0x78000000 for a in bases),'DLL resource is not manually reserved');broker=broker[:m.start()]+f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(a)for a in bases)+'};'+broker[m.end():];(out/'original_broker.hpp').write_text(broker)
 fs=json.loads(pin(OLD/'fs-hook-bindings.json').read_bytes());hooks=[(r['PC'],r['kind'],r['raw_bytes'])for r in fs]
 for r in gi['FS_frame_contracts']:
  for k,key in enumerate(('read','install','restore')):
   pc=r[key];row=next(q for q in gi['instructions']if q['pc']==pc);hooks.append((pc,k,row.get('bytes_hex',row.get('bytes'))))
 need(len(hooks)==45 and len(set(p for p,k,c in hooks))==45,'45 exact FS observer sites');S=importlib.util.spec_from_file_location('lockit124_fs',pin(ROOT/'tools/m4-fs-source/fs_hooks_v2.py'));F=importlib.util.module_from_spec(S);S.loader.exec_module(F);F.HOOKS=hooks
 ref=text(OLD/'reference.cpp').replace('MW4J120','MW4J124').replace('Original120','Original124').replace('original120','original124').replace('92*4','96*4').replace('Exact92callback','Exact96callback')
 start=ref.index('void fs_hook_');end=ref.index('struct FsAllocation {',start);ref=ref[:start]+F.declarations()+F.hook_table().replace('std::array<FsHook,9>','std::array<FsHook,45>')+ref[end:];ref=re.sub(r'std::array<void\*,116> pages',f'std::array<void*,{len(records)}> pages',ref)
 first='for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original committed instruction/source binding rejected");}'
 ref=one(ref,first,first.replace('const auto&origin','if(span.origin)continue;const auto&origin'))
 loader='''
    auto cp=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCP50.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);require(reinterpret_cast<unsigned>(cp)==0x780c0000,"Genuine exact preferred MSVCP50 loader");
    const auto cpctor=GetProcAddress(cp,"??0_Lockit@std@@QAE@XZ"),cpdtor=GetProcAddress(cp,"??1_Lockit@std@@QAE@XZ");require(reinterpret_cast<unsigned>(cpctor)==0x7810a290&&reinterpret_cast<unsigned>(cpdtor)==0x7810a350,"Exact genuine Lockit exports");
    require(*reinterpret_cast<unsigned*>(0x78145658)==2&&*reinterpret_cast<unsigned*>(0x78145648)==0&&*reinterpret_cast<unsigned*>(0x7814564c)==0,"Authentic loaded state2 initialized unheld critical section");
    for(const auto&span:code_bindings)if(span.origin)require(!std::memcmp(reinterpret_cast<void*>(span.pc),provider.data()+span.image_offset,span.size),"Actual DLL preferred bytes equal physical provider source");
    *reinterpret_cast<unsigned*>(0x5bb4f8)=reinterpret_cast<unsigned>(cpctor);*reinterpret_cast<unsigned*>(0x5bb4f4)=reinterpret_cast<unsigned>(cpdtor);
    unsigned bootstrap_i{};for(unsigned page:lockit_bootstrap_bases){std::memcpy(lockit_bootstrap_pages[bootstrap_i++],reinterpret_cast<void*>(page),4096);}
    lockit_actual_Enter=*reinterpret_cast<unsigned*>(0x78146198);lockit_actual_Leave=*reinterpret_cast<unsigned*>(0x78146184);
'''
 ref=one(ref,'    const auto original_onexit=GetProcAddress',loader+'    const auto original_onexit=GetProcAddress')
 ref=one(ref,'void container_observe_allocation(unsigned,unsigned,unsigned);','void container_observe_allocation(unsigned,unsigned,unsigned);\nvoid lockit_observe_allocation(unsigned,unsigned,unsigned);')
 ref=one(ref,'container_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));','container_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));lockit_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));')
 hookrows=json.loads(pin(PROBE/'hook-bindings.json').read_bytes());declarations='extern "C" {\n'+''.join('void lockit_hook_'+format(h['pc'],'x')+'();\n'+('extern const unsigned lockit_continue_'+format(h['pc'],'x')+'='+hex(h['continuation'])+';\n'if h['continuation']else'')for h in hookrows)+'void lockit_api_Enter();void lockit_api_Leave();\n}\n'
 table='struct LockitHook{unsigned pc,size;void(*entry)();unsigned char raw[7];};const std::array<LockitHook,4>lockit_hooks{{'+','.join('{'+hex(h['pc'])+','+str(h['size'])+',&lockit_hook_'+format(h['pc'],'x')+',{'+','.join(hex(v)for v in bytes.fromhex(h['raw']))+'}}'for h in hookrows)+'}};\n'
 ref=one(ref,'static std::uint32_t execute()',CPP+'\n'+declarations+table+'\nstatic std::uint32_t execute()')
 ref=one(ref,'    install_null_hooks();',INSTALL+'\n    install_null_hooks();')
 ref=one(ref,'    out.append("user32-image.bin"',METADATA+'\n    out.append("user32-image.bin"')
 ref=one(ref,'        container_allocation_count=0;', '        lockit_allocation_count=0;std::memset(lockit_allocations,0,sizeof(lockit_allocations));\n        container_allocation_count=0;')
 ref=one(ref,'fs_phase_root=entries[phase];fs_event_count=0;','lockit_count=0;std::memset(lockit_snapshots,0,sizeof(lockit_snapshots));fs_phase_root=entries[phase];fs_event_count=0;')
 ref=one(ref,'            const auto vbase=',EMIT+'\n            const auto vbase=')
 # Mask only declared source-observer spans, never unrelated provider bytes.
 needle='if(!hooked)require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original selected source changed after checkpoint");'
 replacement='for(const auto&hook:lockit_hooks)if(hook.pc<=span.pc&&span.pc+span.size<=hook.pc+hook.size){const unsigned off=span.pc-hook.pc;require(!std::memcmp(origin.data()+span.image_offset,hook.raw+off,span.size),"Exact Lockit physical source observer input");for(unsigned n=0;n<span.size;++n){const unsigned relative=off+n,d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);const unsigned char wanted=relative==0?0xe9:relative<5?static_cast<unsigned char>(d>>(8*(relative-1))):0x90;require(*reinterpret_cast<unsigned char*>(span.pc+n)==wanted,"Exact Lockit declared observer byte");}hooked=true;}'+needle
 ref=one(ref,needle,replacement)
 ref=one(ref,'        remove_CRT_hooks();registry_cleanup.restore();',CLEANUP+'\n        remove_CRT_hooks();registry_cleanup.restore();')
 ref=one(ref,'    out.append("COMPLETE.txt"',RESTORE+'\n    out.append("COMPLETE.txt"')
 (out/'reference.cpp').write_text(ref)
 for n in('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','mfc-import-bindings.json','mfc-raw-page.bin','nullfree-hook-bindings.json','vtable-hook-bindings.json','vtable-inputs.json'):(out/n).write_bytes(pin(OLD/n).read_bytes())
 assembly=text(PROBE/'observer_x86.asm').replace('probe_','lockit_');assembly=assembly[:assembly.index('PUBLIC lockit_call')]+'END\n';assembly=assembly.replace('EXTERN lockit_cpu:BYTE','EXTERN mixed_host_esp:DWORD\nEXTERN lockit_head:DWORD\nEXTERN lockit_cpu:BYTE').replace(' pushfd\n pop DWORD PTR lockit_cpu[32]',' mov esp,mixed_host_esp\n pushfd\n pop DWORD PTR lockit_cpu[32]\n mov eax,DWORD PTR fs:[0]\n mov lockit_head,eax');(out/'lockit_observer_x86.asm').write_text(assembly)
 (out/'fs_observer_x86.asm').write_text(F.asm());(out/'CMakeLists.txt').write_text(text(OLD/'CMakeLists.txt').replace('Startup120','Startup124').replace('startup120','startup124').replace('vtable_observer_x86.asm','vtable_observer_x86.asm lockit_observer_x86.asm'))
 (out/'fs-hook-bindings.json').write_text(json.dumps([dict(PC=p,kind=k,raw_bytes=c,continuation=p+len(bytes.fromhex(c)),declared_observer='fs_hook_'+format(p,'x'))for p,k,c in hooks],indent=2)+'\n');(out/'lockit-hook-bindings.json').write_text(json.dumps(hookrows,indent=2)+'\n');(out/'lockit-inputs.json').write_text(json.dumps(gi,indent=2)+'\n')
 for p in out.iterdir():pin(p)
 pin(__file__)
 report=dict(passed=True,scope='Original124 preparation with genuine MSVCP50 DllMain and balanced Lockit observers, eight finite owner sites, six full relative-order sequences; execution pending',parent_preparation=str(OLD),parent_sha256=sha(OLD/'report.json'),source_recovery_sha256=sha(SRC/'report.json'),authentic_provider_domain_sha256=sha(BASE/'probe-validation-r1/report.json'),order=gi['selected_order'],observed_pages=observed,page_count=len(records),record_bytes=356992,pack_sha256=sha(out/'pages.bin'),source_spans=spans,mfc_bindings=old['mfc_bindings'],fs_allocations=old['fs_allocations'],container_allocations=old['container_allocations'],string_inputs=old['string_inputs'],Lockit_allocations=alloc,Lockit_roots=rec['roots'],FS_hooks=45,fs_event_record_bytes=1216,nullfree_snapshot_bytes=628,nullfree_snapshots_per_sequence=10,vtable_hooks=6,vtable_snapshot_bytes=660,vtable_snapshots_per_sequence=12,Lockit_hooks=4,Lockit_snapshot_bytes=12988,Lockit_snapshots_per_reached_root=6,Lockit_snapshot_scope='Ctor actual entry/APIentry/sourceAPIreturn preepilogue; dtor actual entry/APIentry/immediatepreRET; same authenticguestCALLframes, host-only observation stores',offsets=dict(memory_before=2276,memory_after=178404,end=354532,registry_header=356464,registry_bytes=356480),removed_manual_provider_pages=list(removed),genuine_DllMain_bootstrap_pages=[0x780c1000,0x78115000,0x7810a000,0x78145000,0x78146000],callbacks=96,original_executed=False,native_executed=False,per_phase_reseed=False,AFTER_machine_seed=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),pages=len(records))))
CPP=r'''
inline constexpr unsigned lockit_bootstrap_bases[]={0x780c1000,0x78115000,0x7810a000,0x78145000,0x78146000};unsigned char lockit_bootstrap_pages[5][4096]{};
extern "C" {
Cpu lockit_cpu{};unsigned lockit_head{},lockit_kind{},lockit_count{},lockit_actual_Enter{},lockit_actual_Leave{};alignas(16) unsigned char lockit_fx[512]{};unsigned char lockit_env[28]{};
struct LockitSnapshot{unsigned words[16];Cpu cpu;unsigned char fx[512],env[28],frame[32],CS[24],pages[3*4096];};static_assert(sizeof(LockitSnapshot)==12988);LockitSnapshot lockit_snapshots[6]{};
void lockit_observe(){
 if(!fs_phase_root)return;const LockitRoot*spec{};for(const auto&r:lockit_roots)if(r.root==fs_phase_root)spec=&r;if(!spec||lockit_count>=6){fs_error=1;return;}const auto F=lockit_cpu.esp;if(F<0x20001000||F+32>0x20002000){fs_error=1;return;}
 auto&s=lockit_snapshots[lockit_count];s={};s.words[0]=1;s.words[1]=lockit_count;s.words[2]=fs_phase_root;s.words[3]=lockit_kind;s.words[4]=lockit_cpu.pc;s.words[5]=lockit_head;s.words[6]=GetCurrentThreadId();s.words[7]=*reinterpret_cast<unsigned*>(0x78145658);s.words[8]=spec->object;s.words[9]=lockit_kind==1?lockit_actual_Enter:lockit_kind==4?lockit_actual_Leave:0;s.words[10]=*reinterpret_cast<unsigned*>(spec->header);s.words[11]=*reinterpret_cast<unsigned*>(spec->counter);s.words[12]=lockit_allocation_count_placeholder();s.words[13]=*reinterpret_cast<unsigned*>(0x5bb4f8);s.words[14]=*reinterpret_cast<unsigned*>(0x5bb4f4);s.words[15]=registry_API_count;s.cpu=lockit_cpu;if(s.words[9])s.cpu.pc=s.words[9];std::memcpy(s.fx,lockit_fx,512);std::memcpy(s.env,lockit_env,28);std::memcpy(s.frame,reinterpret_cast<void*>(F),32);std::memcpy(s.CS,reinterpret_cast<void*>(0x78145640),24);unsigned k{};for(unsigned page:{0x7810a000u,0x78145000u,0x78146000u})std::memcpy(s.pages+(k++)*4096,reinterpret_cast<void*>(page),4096);++lockit_count;
}
}
FsAllocation lockit_allocations[8]{};unsigned lockit_allocation_count{};
void lockit_observe_allocation(unsigned ai,unsigned pointer,unsigned capacity){
 if(!fs_phase_root||registry_API_kind!=0||!pointer)return;const auto A=registry_API_before.esp,F=A+104;if(A<0x20001000||F+8>0x20002000){fs_error=1;return;}const auto ret=*reinterpret_cast<unsigned*>(F),request=*reinterpret_cast<unsigned*>(F+4);for(const auto&b:lockit_allocation_bindings){if(b.root!=fs_phase_root||b.CALL_pc+5!=ret)continue;if(lockit_allocation_count>=8||request!=b.request||*reinterpret_cast<unsigned*>(A)!=0x78001385||*reinterpret_cast<unsigned*>(A+80)!=0x5f401eb7){fs_error=1;return;}auto&e=lockit_allocations[lockit_allocation_count];e={1,lockit_allocation_count,fs_phase_root,b.CALL_pc,request,F,ai,pointer,capacity};++lockit_allocation_count;return;}
}
'''.replace('s.words[12]=lockit_allocation_count_placeholder();','s.words[12]=0;')
INSTALL=r'''
    for(const auto&hook:lockit_hooks){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,hook.size),"Exact authentic Lockit observer span");DWORD prior{},ignored{};require(VirtualProtect(code,hook.size,PAGE_EXECUTE_READWRITE,&prior),"Lockit observer protect");code[0]=0xe9;const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&d,4);for(unsigned n=5;n<hook.size;++n)code[n]=0x90;require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"Lockit observer source protection restore");}
    for(const auto pair:{std::pair<unsigned,unsigned>{0x78146198,reinterpret_cast<unsigned>(&lockit_api_Enter)},{0x78146184,reinterpret_cast<unsigned>(&lockit_api_Leave)}}){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(pair.first),4,PAGE_READWRITE,&prior),"Lockit owning provider IAT protect");*reinterpret_cast<unsigned*>(pair.first)=pair.second;require(VirtualProtect(reinterpret_cast<void*>(pair.first),4,prior,&ignored),"Lockit IAT protection restore");}
'''
METADATA=r'''
    for(unsigned k=0;k<5;++k)out.append("lockit/post-DllMain/"+std::to_string(lockit_bootstrap_bases[k])+"-page.bin",lockit_bootstrap_pages[k],4096);
    struct CPImport{unsigned cell;const char*library;const char*name;};const CPImport cpimports[]={{0x78146184,"KERNEL32.dll","LeaveCriticalSection"},{0x7814618c,"KERNEL32.dll","InterlockedExchange"},{0x78146190,"KERNEL32.dll","InitializeCriticalSection"},{0x78146194,"KERNEL32.dll","Sleep"},{0x78146198,"KERNEL32.dll","EnterCriticalSection"},{0x78146278,"MSVCRT.dll","__dllonexit"},{0x7814627c,"MSVCRT.dll","_onexit"}};std::vector<unsigned> cpimports_ledger;std::vector<unsigned> cpmodules;
    for(const auto&b:cpimports){const unsigned target=word<unsigned>(lockit_bootstrap_pages[4]+(b.cell&4095));auto declared=GetModuleHandleA(b.library);const auto named=GetProcAddress(declared,b.name);HMODULE owner_module{};require(target==reinterpret_cast<unsigned>(named)&&GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(target),&owner_module),"Actual named CP import and owner");for(unsigned value:{b.cell,target,reinterpret_cast<unsigned>(named),reinterpret_cast<unsigned>(declared),reinterpret_cast<unsigned>(owner_module)})cpimports_ledger.push_back(value);for(unsigned module:{reinterpret_cast<unsigned>(declared),reinterpret_cast<unsigned>(owner_module)})if(std::find(cpmodules.begin(),cpmodules.end(),module)==cpmodules.end())cpmodules.push_back(module);}
    out.append("lockit/import-ledger.bin",cpimports_ledger.data(),cpimports_ledger.size()*4);const unsigned cp_thread=GetCurrentThreadId();out.append("lockit/thread.bin",&cp_thread,4);
    for(unsigned base:cpmodules){std::array<wchar_t,32768> path{};const auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(base),path.data(),path.size());require(n&&n<path.size(),"Actual CP provider module path");const auto raw=read(std::filesystem::path(path.data()).string().c_str(),64*1024*1024);const auto stem="lockit/modules/"+std::to_string(base);out.append(stem+"/path.bin",path.data(),(n+1)*sizeof(wchar_t));out.append(stem+"/image.bin",raw.data(),raw.size());}
'''
EMIT=r'''
            const auto lockbase="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/lockit";out.append(lockbase+"-count.bin",&lockit_count,4);out.append(lockbase+"-snapshots.bin",lockit_snapshots,lockit_count*sizeof(LockitSnapshot));
            for(unsigned li=0;li<lockit_allocation_count;++li){const auto&a=lockit_allocations[li];const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(a.pointer));require(cap==a.capacity,"Persistent actual Lockit owned backing");const auto stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/lockit-allocation/"+std::to_string(li);out.append(stem+"/meta.bin",&a,sizeof(a));out.append(stem+"/bytes.bin",reinterpret_cast<void*>(a.pointer),cap);}
            require(*reinterpret_cast<unsigned*>(0x78145658)==2&&*reinterpret_cast<unsigned*>(0x78145648)==0&&*reinterpret_cast<unsigned*>(0x7814564c)==0,"Balanced actual Lockit at every root endpoint");
'''
CLEANUP=r'''
        require(lockit_allocation_count==8,"Eight genuine four-root Lockit owners");for(unsigned li=0;li<lockit_allocation_count;++li){const auto&a=lockit_allocations[li];const auto stem="cleanup/"+std::to_string(sequence)+"/lockit-allocation-"+std::to_string(li);out.append(stem+"-before.bin",&a,sizeof(a));out.append(stem+"-owned.bin",reinterpret_cast<void*>(a.pointer),a.capacity);mfc825(reinterpret_cast<void*>(a.pointer));const unsigned returned=1;out.append(stem+"-returned.bin",&returned,4);}
'''
RESTORE=r'''
    for(const auto&hook:lockit_hooks){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,PAGE_EXECUTE_READWRITE,&prior),"Restore CP observer source");std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size);require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(hook.pc),hook.size),"Restore CP source bytes and protection");}
    for(const auto pair:{std::pair<unsigned,unsigned>{0x78146198,lockit_actual_Enter},{0x78146184,lockit_actual_Leave}}){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(pair.first),4,PAGE_READWRITE,&prior),"Restore CP IAT");*reinterpret_cast<unsigned*>(pair.first)=pair.second;require(VirtualProtect(reinterpret_cast<void*>(pair.first),4,prior,&ignored),"Restore CP IAT protection");}
    for(unsigned k=0;k<5;++k){require(!std::memcmp(lockit_bootstrap_pages[k],reinterpret_cast<void*>(lockit_bootstrap_bases[k]),4096),"Complete authentic CP bootstrap pages conserved after all sequences");out.append("lockit/restored/"+std::to_string(lockit_bootstrap_bases[k])+"-page.bin",reinterpret_cast<void*>(lockit_bootstrap_bases[k]),4096);}
'''
if __name__=='__main__':main(sys.argv[1])
