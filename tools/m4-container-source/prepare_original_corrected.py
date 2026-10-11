"""Additive actual original116, same-process DLL page and normal NULL-free observers."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-container-source';OLD=ROOT/'reports/m4-fs-source/original-preparation-r5'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
s=importlib.util.spec_from_file_location('immutable109_fs_observers',ROOT/'tools/m4-fs-source/fs_hooks_v2.py');F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def one(s,a,b):need(s.count(a)==1,'One additive replacement '+a[:75]);return s.replace(a,b)
def mapped_page(pe,base):
 result=bytearray(4096);rva=base-pe.image_base
 for sec in pe.sections:
  lo=max(rva,sec['virtual_address']);hi=min(rva+4096,sec['virtual_address']+max(sec['virtual_size'],sec['raw_size']))
  if hi<=lo:continue
  end=min(hi,sec['virtual_address']+sec['raw_size'])
  if end>lo:result[lo-rva:end-rva]=pe.data[sec['raw_offset']+lo-sec['virtual_address']:sec['raw_offset']+end-sec['virtual_address']]
 return result
CONTAINER_CPP=r'''
FsAllocation container_allocations[5]{};unsigned container_allocation_count{};
void container_observe_allocation(unsigned api_index,unsigned pointer,unsigned capacity){
 if(!fs_phase_root||registry_API_kind!=0||!pointer)return;
 const auto A=registry_API_before.esp,F=A+104;
 if(A<0x20001000||F+8>0x20002000){fs_error=1;return;}
 const auto ret=*reinterpret_cast<unsigned*>(F),request=*reinterpret_cast<unsigned*>(F+4);
 for(const auto&b:container_allocation_bindings){if(b.root!=fs_phase_root||b.CALL_pc+5!=ret)continue;
  if(container_allocation_count>=5||request!=b.request||*reinterpret_cast<unsigned*>(A)!=0x78001385||*reinterpret_cast<unsigned*>(A+80)!=0x5f401eb7){fs_error=1;return;}
  auto&e=container_allocations[container_allocation_count];e={1,container_allocation_count,fs_phase_root,b.CALL_pc,request,F,api_index,pointer,capacity};++container_allocation_count;return;}
}
extern "C" {
Cpu nullfree_cpu{};unsigned nullfree_head{},nullfree_point{},nullfree_count{};
alignas(16) unsigned char nullfree_fx[512]{};unsigned char nullfree_env[28]{};
struct NullFreeSnapshot{unsigned version,index,root,point,PC,frame,head,API_count;Cpu cpu;unsigned char fx[512],env[28];unsigned words[4];};
static_assert(sizeof(NullFreeSnapshot)==628);NullFreeSnapshot nullfree_snapshots[10]{};
void nullfree_observe(){
 if(!fs_phase_root)return;if(nullfree_count>=10){fs_error=1;return;}
 const auto source_frame=nullfree_cpu.esp;if(source_frame<0x20001000||source_frame+16>0x20002000){fs_error=1;return;}
 const auto*w=reinterpret_cast<unsigned*>(source_frame);bool admitted=false;
 for(const auto&b:nullfree_bindings)if(b.root==fs_phase_root&&w[0]==0x5f40178c&&w[1]==0&&w[2]==b.CALL_pc+5&&w[3]==0)admitted=true;
 if(!admitted||((nullfree_count%2)==0)!=(nullfree_point==0)){fs_error=1;return;}
 auto&e=nullfree_snapshots[nullfree_count];e={};e.version=1;e.index=nullfree_count;e.root=fs_phase_root;e.point=nullfree_point;e.PC=nullfree_cpu.pc;e.frame=source_frame;e.head=nullfree_head;e.API_count=registry_API_count;e.cpu=nullfree_cpu;
 std::memcpy(e.fx,nullfree_fx,512);std::memcpy(e.env,nullfree_env,28);std::memcpy(e.words,w,16);
 if(nullfree_point){const auto&before=nullfree_snapshots[nullfree_count-1];if(before.frame!=e.frame||before.head!=e.head||before.API_count!=e.API_count||std::memcmp(before.words,e.words,16))fs_error=1;}
 ++nullfree_count;
}
void nullfree_entry_hook();void nullfree_ret_hook();
extern const unsigned nullfree_entry_continue=0x78001395;
}
'''
def null_asm():
 lines=['.686p','.xmm','.model flat, C','assume fs:nothing','option casemap:none']
 for n,t in [('mixed_host_esp','DWORD'),('nullfree_cpu','BYTE'),('nullfree_head','DWORD'),('nullfree_point','DWORD'),('nullfree_fx','BYTE'),('nullfree_env','BYTE'),('nullfree_observe','PROC'),('nullfree_entry_continue','DWORD')]:lines.append('EXTERN '+n+':'+t)
 lines+=['.code'];regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
 def capture(pc,point):
  r=[f' mov DWORD PTR nullfree_cpu[{i*4}],{x}'for i,x in enumerate(regs)]
  r += [f' mov DWORD PTR nullfree_cpu[36],{pc:08x}h',f' mov nullfree_point,{point}',' mov esp,mixed_host_esp',' pushfd',' pop DWORD PTR nullfree_cpu[32]',' mov eax,DWORD PTR fs:[0]',' mov nullfree_head,eax',' fxsave nullfree_fx',' fnstenv nullfree_env',' fldenv nullfree_env',' call nullfree_observe',' fxrstor nullfree_fx',' fldenv nullfree_env',' push DWORD PTR nullfree_cpu[32]',' popfd']
  r += [f' mov {x},DWORD PTR nullfree_cpu[{i*4}]'for i,x in enumerate(regs)if x!='esp'];r+=[' mov esp,DWORD PTR nullfree_cpu[16]'];return r
 lines+=['PUBLIC nullfree_entry_hook','nullfree_entry_hook PROC']+capture(0x78001390,0)+[' db 055h,08bh,0ech,06ah,0ffh',' jmp DWORD PTR nullfree_entry_continue','nullfree_entry_hook ENDP','PUBLIC nullfree_ret_hook','nullfree_ret_hook PROC',' db 05fh,05eh,05bh,0c9h']+capture(0x78001424,1)+[' db 0c3h','nullfree_ret_hook ENDP','END'];return '\n'.join(lines)+'\n'
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original116 preparation');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact immutable preparation input '+str(p));pins[str(p)]=v;return p
 def read(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','57ffbf9a5d1a6375dafcacf1a2cdc9b878b8fa5dbe9af4b49180098b9da1e0d6').read_bytes())
 rec=json.loads(pin(BASE/'recovery-r3/report.json','b078cff8698dfbefa8d4e45a0368d4820e72c7d659520161e4316e77d3c2f26b').read_bytes())
 interface=json.loads(pin(BASE/'allocation-interface-r1/report.json','89a6a4b581bedd7a1b98ccfad1344ba35f6c50a011964230aecaa1f7295e95ec').read_bytes())
 bindings=json.loads(pin(BASE/'allocation-interface-r1/allocation-inputs.json',interface['allocation_inputs_sha256']).read_bytes());strings=json.loads(pin(BASE/'allocation-interface-r1/string-inputs.json',interface['string_inputs_sha256']).read_bytes())
 pin(ROOT/'reports/m4-joint-startup109-root/acceptance-r1/report.json','697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0');pin(BASE/'loader-identity-r2/report.json','f3c5a41e6afcb1c7373a911d5e20434f06c6eafee0cf7755a3fc372e93abd892')
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());mfc=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes());crt=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
 pack=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',pack,12+i*4104)[0]:(struct.unpack_from('<I',pack,16+i*4104)[0],bytearray(pack[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',pack,8)[0])}
 spec=read(OLD/'spec.hpp');match=re.search(r'code_bindings\{\{([^;]+)\}\};',spec);spans=[dict(zip(('pc','size','image_offset','origin'),[int(x,16)for x in vals]))for vals in re.findall(r'\{(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+),(0x[0-9a-f]+)\}',match[1])];oldpcs={s['pc']for s in spans}
 rows=json.loads(pin(BASE/'recovery-r3/instruction-contracts.json','3aeed69c05122c689a2f0951c2d49052db307beba917f5bcf756969aa7bbb09d').read_bytes())['instructions']
 for row in rows:
  pc=row['pc'];raw=bytes.fromhex(row['bytes_hex']);off,_=game.rva_range(pc-game.image_base,len(raw));need(game.data[off:off+len(raw)]==raw,'Physical new game source');base=pc&~4095;need((pc&4095)+len(raw)<=4096,'Bounded source instruction')
  if base not in records:records[base]=(1,bytearray(b'\xcc'*4096))
  if pc in oldpcs:need(records[base][1][pc&4095:(pc&4095)+len(raw)]==raw,'Unchanged old literal source')
  else:records[base][1][pc&4095:(pc&4095)+len(raw)]=raw;spans.append(dict(pc=pc,size=len(raw),image_offset=off,origin=0))
 need(0x736000 not in records,'New exact game mixed raw/BSS page');records[0x736000]=(2,mapped_page(game,0x736000));need(0x5f4cc000 not in records,'Actual DLL data page is never packed or reseeded')
 observed=old['observed_pages']+[0x736000,0x5f4cc000];need(len(observed)==37,'37 genuine observed pages')
 pack=b'MW4J116P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',a,p)+raw for a,(p,raw)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"',f'pack_sha[]="{sha(out/"pages.bin")}"',spec);spec=re.sub(r'pack_size=\d+',f'pack_size={len(pack)}',spec)
 for key,values in [('entries',[r['entry']for r in rec['order']]),('table_slots',[r['slot']for r in rec['order']]),('page_bases',list(records)),('page_permissions',[p for p,raw in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+key+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+key+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(s[k])for k in('pc','size','image_offset','origin'))+'}'for s in spans)+'}};',spec)
 match=re.search(r'inline constexpr std::array<StringBinding,17> string_bindings\{\{([^;]+)\}\};',spec);need(match is not None,'Old17 exact string bindings');news=','.join('{'+','.join(hex(r[k])for k in('root','source','publication','size'))+'}'for r in strings);spec=spec[:match.start()]+'inline constexpr std::array<StringBinding,20> string_bindings{{'+match[1]+','+news+'}};'+spec[match.end():]
 spec+='\ninline constexpr std::array<FsAllocationBinding,5> container_allocation_bindings{{'+','.join('{'+','.join(hex(r[k])for k in('root','CALL_pc','requested_size'))+'}'for r in bindings)+'}};\nstruct NullFreeBinding{unsigned root,CALL_pc;};\ninline constexpr std::array<NullFreeBinding,5> nullfree_bindings{{'+','.join('{'+','.join(hex(r[k])for k in('root','CALL_pc'))+'}'for r in interface['nullfree_inputs'])+'}};\n';(out/'spec.hpp').write_text(spec)
 protocol=read(OLD/'protocol.hpp').replace('roots=109','roots=116').replace('observed_page_count=35','observed_page_count=37').replace('sizeof(Record)==291456','sizeof(Record)==307840').replace('memory_size==143360','memory_size==151552');protocol=one(protocol,'0x731000,0x5f498000};','0x731000,0x5f498000,0x736000,0x5f4cc000};');(out/'protocol.hpp').write_text(protocol)
 broker=read(OLD/'original_broker.hpp');match=re.search(r'std::array<std::uint32_t,\d+> bases\{([^;]+)\};',broker);bases=list(dict.fromkeys([int(x,16)for x in match[1].split(',')]+[a&~65535 for a in records]));need(0x5f4c0000 not in bases,'Never reserve actual MFC DLL data owner');broker=broker[:match.start()]+f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(a)for a in bases)+'};'+broker[match.end():];(out/'original_broker.hpp').write_text(broker)
 hooks=list(F.HOOKS)
 for frame in interface['FS_frame_contracts']:
  for key,kind,raw in [('read',0,'64a100000000'),('install',1,'64892500000000'),('restore',2,'64890d00000000')]:
   row=(frame[key],kind,raw)
   if row not in hooks:hooks.append(row)
 hooks += [(0x7800139f,0,'64a100000000'),(0x780013a6,1,'64892500000000'),(0x78001419,2,'64890d00000000')];need(len(hooks)==30,'27 game plus3 genuine nested CRT FS source hooks');F.HOOKS=hooks
 for pc,kind,raw in hooks:
  pe=crt if pc>=0x78000000 else game;off,_=pe.rva_range(pc-pe.image_base,len(bytes.fromhex(raw)));need(pe.data[off:off+len(bytes.fromhex(raw))]==bytes.fromhex(raw),'Every transparent FS hook physically exact')
 ref=read(OLD/'reference.cpp').replace('MW4J109','MW4J116').replace('Original109','Original116').replace('original109','original116').replace('/654 actual','/696 actual').replace('81*4','88*4').replace('Exact81callback','Exact88callback')
 start=ref.index('// Fixed bounded observation arrays.');end=ref.index('struct FsAllocation {',start);cpp=F.CPP.replace('void fs_observe_before(){','void fs_observe_before(){\n if(!fs_phase_root)return;').replace('void fs_observe_after(){','void fs_observe_after(){\n if(!fs_phase_root)return;');table=F.hook_table().replace('std::array<FsHook,9>','std::array<FsHook,30>');ref=ref[:start]+cpp+F.declarations()+table+ref[end:]
 ref=one(ref,'void fs_observe_allocation(unsigned,unsigned,unsigned);','void fs_observe_allocation(unsigned,unsigned,unsigned);\nvoid container_observe_allocation(unsigned,unsigned,unsigned);');ref=ref.replace('registry_initial_bytes[32][512]','registry_initial_bytes[32][1024]').replace('size>512','size>1024').replace('registry_initial_sizes[ai]<=512','registry_initial_sizes[ai]<=1024');ref=one(ref,'fs_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));','fs_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));container_observe_allocation(i,registry_API_after.eax,static_cast<unsigned>(size));');ref=one(ref,'static std::uint32_t execute()',CONTAINER_CPP+'\nstatic std::uint32_t execute()');ref=re.sub(r'std::array<void\*,106> pages',f'std::array<void*,{len(records)}> pages',ref)
 ref=one(ref,'    MEMORY_BASIC_INFORMATION mfc_region{};',r'''    auto mfc540=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(540));require(reinterpret_cast<unsigned>(mfc540)==0x5f4020b4,"Actual MFC540 export");require(*reinterpret_cast<unsigned*>(0x5bb454)==0x8000021c&&*reinterpret_cast<unsigned*>(0x5bb4c8)==0x80000339,"Exact new raw game ordinal slots");*reinterpret_cast<unsigned*>(0x5bb454)=reinterpret_cast<unsigned>(mfc540);*reinterpret_cast<unsigned*>(0x5bb4c8)=reinterpret_cast<unsigned>(mfc825);
    std::array<unsigned char,4096> mfc540_loaded_page{};std::memcpy(mfc540_loaded_page.data(),reinterpret_cast<void*>(0x5f4cc000),4096);require(*reinterpret_cast<unsigned*>(0x5f4ccb54)==0x5f4cecec,"Same-worker actual initialized borrowed DWORD");MEMORY_BASIC_INFORMATION mfc540_region{};require(VirtualQuery(reinterpret_cast<void*>(0x5f4cc000),&mfc540_region,sizeof(mfc540_region))==sizeof(mfc540_region)&&mfc540_region.AllocationBase==mfc&&mfc540_region.State==MEM_COMMIT&&mfc540_region.Type==MEM_IMAGE,"Actual DLL initialized page owner");
    MEMORY_BASIC_INFORMATION mfc_region{};''')
 # Exact MFC540 provider code and exact CRT entry/epilog spans stay original,
 # apart from the separately declared transparent instruction replay hooks.
 providerrows=json.loads(pin(BASE/'provider-lifts-r1/instruction-contracts.json').read_bytes())['instructions'];providerchecks=[]
 for row in providerrows:
  raw=bytes.fromhex(row['bytes_hex']);providerchecks.append('require(!std::memcmp(reinterpret_cast<void*>('+hex(row['pc'])+'),std::array<unsigned char,'+str(len(raw))+'>{'+','.join(hex(b)for b in raw)+'}.data(),'+str(len(raw))+'),"Exact actual loaded MFC540 instruction");')
 nullspans=[dict(pc=0x78001390,size=5,raw='558bec6aff',entry='nullfree_entry_hook'),dict(pc=0x78001420,size=5,raw='5f5e5bc9c3',entry='nullfree_ret_hook')]
 for row in nullspans:
  off,_=crt.rva_range(row['pc']-crt.image_base,5);need(crt.data[off:off+5].hex()==row['raw'],'Exact NULL-free entry/epilog physical span')
 free_table='struct NullHook{unsigned pc;void(*entry)();unsigned char raw[5];};const std::array<NullHook,2> null_hooks{{'+','.join('{'+hex(r['pc'])+',&'+r['entry']+',{'+','.join(hex(b)for b in bytes.fromhex(r['raw']))+'}}'for r in nullspans)+'}};\n'
 ref=one(ref,'static std::uint32_t execute()',free_table+'\nstatic std::uint32_t execute()')
 install=r'''    const auto install_null_hooks=[&](){for(const auto&hook:null_hooks){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,5),"Exact NULL-free source span");DWORD prior{},ignored{};require(VirtualProtect(code,5,PAGE_EXECUTE_READWRITE,&prior),"NULL-free observer protection");code[0]=0xe9;const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&d,4);require(VirtualProtect(code,5,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,5),"NULL-free observer permissions");}};
    const auto remove_CRT_hooks=[&](){for(const auto&hook:fs_hooks)if(hook.pc>=0x78000000){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,PAGE_EXECUTE_READWRITE,&prior),"Remove CRT FS observer");std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,hook.size);require(VirtualProtect(reinterpret_cast<void*>(hook.pc),hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(hook.pc),hook.size),"Restore actual CRT FS source");}for(const auto&hook:null_hooks){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(hook.pc),5,PAGE_EXECUTE_READWRITE,&prior),"Remove CRT NULL observer");std::memcpy(reinterpret_cast<void*>(hook.pc),hook.raw,5);require(VirtualProtect(reinterpret_cast<void*>(hook.pc),5,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(hook.pc),5),"Restore actual CRT NULL source");}};
    const auto install_CRT_hooks=[&](){for(const auto&hook:fs_hooks)if(hook.pc>=0x78000000){auto*code=reinterpret_cast<unsigned char*>(hook.pc);require(!std::memcmp(code,hook.raw,hook.size),"CRT FS reinstall exact source");DWORD prior{},ignored{};require(VirtualProtect(code,hook.size,PAGE_EXECUTE_READWRITE,&prior),"CRT FS reinstall protect");code[0]=0xe9;const unsigned d=reinterpret_cast<unsigned>(hook.entry)-(hook.pc+5);std::memcpy(code+1,&d,4);for(unsigned n=5;n<hook.size;++n)code[n]=0x90;require(VirtualProtect(code,hook.size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),code,hook.size),"CRT FS reinstall permissions");}install_null_hooks();};
    install_null_hooks();
    owner=GetCurrentThreadId();'''
 ref=one(ref,'    owner=GetCurrentThreadId();','    '+''.join(providerchecks)+'\n'+install)
 ref=one(ref,'    std::vector<unsigned> mfc_import_ledger;',r'''    out.append("mfc540-loaded-page.bin",mfc540_loaded_page.data(),4096);out.append("mfc540-page-region.bin",&mfc540_region,sizeof(mfc540_region));const std::array<unsigned,7> mfc540_identity{reinterpret_cast<unsigned>(mfc),reinterpret_cast<unsigned>(mfc540),0x5bb454,0x5bb4c8,reinterpret_cast<unsigned>(mfc825),0x5f4ccb54,*reinterpret_cast<unsigned*>(0x5f4ccb54)};out.append("mfc540-identity.bin",mfc540_identity.data(),sizeof(mfc540_identity));
    std::vector<unsigned> mfc_import_ledger;''')
 ref=one(ref,'        fs_allocation_count=0;','        container_allocation_count=0;std::memset(container_allocations,0,sizeof(container_allocations));\n        require(!std::memcmp(mfc540_loaded_page.data(),reinterpret_cast<void*>(0x5f4cc000),4096),"Same-worker initialized MFC page bootstrap carry");out.append("bootstrap/"+std::to_string(sequence)+"/mfc540-page.bin",reinterpret_cast<void*>(0x5f4cc000),4096);\n        fs_allocation_count=0;')
 ref=one(ref,'            fs_phase_root=entries[phase];fs_event_count=0;fs_error=0;','            fs_phase_root=entries[phase];fs_event_count=0;fs_error=0;nullfree_count=0;std::memset(nullfree_snapshots,0,sizeof(nullfree_snapshots));')
 ref=one(ref,'            const auto stringbase=',r'''            require(!std::memcmp(mfc540_loaded_page.data(),reinterpret_cast<void*>(0x5f4cc000),4096),"Same-worker whole initialized MFC page phase carry");out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/nullfree-count.bin",&nullfree_count,4);out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/nullfree-snapshots.bin",nullfree_snapshots,nullfree_count*sizeof(NullFreeSnapshot));require((nullfree_count%2)==0,"True NULL-free entry and literal RET pair");
            for(unsigned ci=0;ci<container_allocation_count;++ci){const auto&a=container_allocations[ci];const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(a.pointer));require(cap==a.capacity,"Persistent original vector capacity");const auto stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/container-allocation/"+std::to_string(ci);out.append(stem+"/meta.bin",&a,sizeof(a));out.append(stem+"/bytes.bin",reinterpret_cast<void*>(a.pointer),cap);}
            const auto stringbase=''')
 ref=one(ref,'        registry_cleanup.restore();',r'''        remove_CRT_hooks();registry_cleanup.restore();require(container_allocation_count==5,"Five genuine new positive vector allocations");for(unsigned ci=0;ci<container_allocation_count;++ci){const auto&a=container_allocations[ci];const auto stem="cleanup/"+std::to_string(sequence)+"/container-allocation-"+std::to_string(ci);out.append(stem+"-before.bin",&a,sizeof(a));out.append(stem+"-owned.bin",reinterpret_cast<void*>(a.pointer),a.capacity);mfc825(reinterpret_cast<void*>(a.pointer));const unsigned returned=1;out.append(stem+"-returned.bin",&returned,4);}''')
 ref=one(ref,'        ++sequence;',r'''        require(!std::memcmp(mfc540_loaded_page.data(),reinterpret_cast<void*>(0x5f4cc000),4096),"Same-worker initialized MFC page source cleanup carry");out.append("cleanup/"+std::to_string(sequence)+"/mfc540-page.bin",reinterpret_cast<void*>(0x5f4cc000),4096);if(sequence+1<sequences)install_CRT_hooks();
        ++sequence;''')
 ref=one(ref,'||(pc>=0x5bb4bc&&pc<0x5bb4c0))continue;','||(pc>=0x5bb4bc&&pc<0x5bb4c0)||(pc>=0x5bb454&&pc<0x5bb458)||(pc>=0x5bb4c8&&pc<0x5bb4cc))continue;');(out/'reference.cpp').write_text(ref)
 for n in ('reference_x86.asm','preserve_x86.asm'):(out/n).write_text(read(OLD/n))
 (out/'fs_observer_x86.asm').write_text(F.asm());(out/'nullfree_observer_x86.asm').write_text(null_asm());(out/'CMakeLists.txt').write_text(read(OLD/'CMakeLists.txt').replace('Startup109','Startup116').replace('startup109','startup116').replace('fs_observer_x86.asm','fs_observer_x86.asm nullfree_observer_x86.asm'))
 for n in ('mfc-import-bindings.json','mfc-raw-page.bin'):(out/n).write_bytes(pin(OLD/n).read_bytes())
 (out/'fs-hook-bindings.json').write_text(json.dumps([dict(PC=p,kind=k,raw_bytes=r,continuation=p+len(bytes.fromhex(r)),declared_observer='fs_hook_'+format(p,'x'))for p,k,r in hooks],indent=2)+'\n');(out/'nullfree-hook-bindings.json').write_text(json.dumps(nullspans,indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);pin(F.__file__);report=dict(passed=True,scope='Fresh actual original116 worker preparation; same-process initialized DLL data page and transparent normal FS/null-free observations; execution pending',parent_preparation=str(OLD),parent_sha256=sha(OLD/'report.json'),order=rec['order'],observed_pages=observed,page_count=len(records),record_bytes=307840,pack_sha256=sha(out/'pages.bin'),source_spans=spans,mfc_bindings=old['mfc_bindings'],fs_allocations=old['fs_allocations'],container_allocations=bindings,string_inputs=strings,FS_hooks=30,fs_event_record_bytes=1216,nullfree_snapshot_bytes=628,nullfree_snapshots_per_sequence=10,initial_backing_limit=1024,loader_page=dict(address=0x5f4cc000,bytes=4096,logical_name='mfc540-loaded-page.bin',bootstrap_pattern='bootstrap/{sequence}/mfc540-page.bin',cleanup_pattern='cleanup/{sequence}/mfc540-page.bin',observed_index=36,before_offset=2276+36*4096,after_offset=153828+36*4096,same_worker_DLL_initialized=True,in_source_pack=False,reseeded=False,pointee_mapping=False),offsets=dict(memory_before=2276,memory_after=153828,end=305380,registry_header=307312,registry_bytes=307328),ordinary_nonstack_pages=35,per_phase_reseed=False,AFTER_machine_seed=False,source_cleanup='Actual825 for50 MFC owners, actualfree for19 strings+registry, zero callback execution',original_executed=False,native_executed=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),pages=len(records),observed=len(observed))))
if __name__=='__main__':main(sys.argv[1])
