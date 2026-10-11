"""Fresh genuine32 Lockit scratch capture, without source-state seeding."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;BASE=ROOT/'reports/m4-lockit-original'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 provider=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
 hooks=[]
 for pc,size,kind,replay,continuation in [(0x7810a290,5,0,5,0x7810a295),(0x7810a311,5,2,5,0),(0x7810a350,7,3,7,0x7810a357),(0x7810a364,5,5,1,0)]:
  off,_=provider.rva_range(pc-provider.image_base,size);raw=provider.data[off:off+size];hooks.append(dict(pc=pc,size=size,kind=kind,raw=raw.hex(),replay=raw[:replay].hex(),continuation=continuation,physical_offset=off,name='probe_hook_'+format(pc,'x')))
 lines=['.686p','.xmm','.model flat,C','option casemap:none']
 for n,t in [('probe_cpu','BYTE'),('probe_fx','BYTE'),('probe_env','BYTE'),('probe_kind','DWORD'),('probe_observe','PROC'),('probe_actual_Enter','DWORD'),('probe_actual_Leave','DWORD')]:lines.append('EXTERN '+n+':'+t)
 for h in hooks:
  if h['continuation']:lines.append('EXTERN probe_continue_'+format(h['pc'],'x')+':DWORD')
 lines.append('.code');regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
 def observe(name,pc,kind,replay='',continuation=0,target=None):
  lines.extend(['PUBLIC '+name,name+' PROC']);lines.extend(f' mov DWORD PTR probe_cpu[{i*4}],{r}'for i,r in enumerate(regs));lines.extend([f' mov DWORD PTR probe_cpu[36],{pc:08x}h',f' mov probe_kind,{kind}',' pushfd',' pop DWORD PTR probe_cpu[32]',' fxsave probe_fx',' fnstenv probe_env',' fldenv probe_env',' call probe_observe',' fxrstor probe_fx',' fldenv probe_env',' push DWORD PTR probe_cpu[32]',' popfd']);lines.extend(f' mov {r},DWORD PTR probe_cpu[{i*4}]'for i,r in enumerate(regs)if r!='esp');lines.append(' mov esp,DWORD PTR probe_cpu[16]')
  if replay:lines.append(' db '+','.join('0%02xh'%b for b in bytes.fromhex(replay)))
  if continuation:lines.append(' jmp DWORD PTR probe_continue_'+format(pc,'x'))
  if target:lines.append(' jmp DWORD PTR '+target)
  lines.append(name+' ENDP')
 for h in hooks:observe(h['name'],h['pc'],h['kind'],h['replay'],h['continuation'])
 observe('probe_api_Enter',0,1,target='probe_actual_Enter');observe('probe_api_Leave',0,4,target='probe_actual_Leave')
 lines+=['PUBLIC probe_call','probe_call PROC',' push ebp',' mov ebp,esp',' push ebx',' push esi',' push edi',' mov ecx,DWORD PTR [ebp+12]',' call DWORD PTR [ebp+8]',' pop edi',' pop esi',' pop ebx',' pop ebp',' ret','probe_call ENDP','END']
 (out/'observer_x86.asm').write_text('\n'.join(lines)+'\n')
 declarations='extern "C" {\n'+''.join('void '+h['name']+'();\n'+('extern const unsigned probe_continue_'+format(h['pc'],'x')+'='+hex(h['continuation'])+';\n'if h['continuation']else'')for h in hooks)+'void probe_api_Enter();void probe_api_Leave();unsigned probe_call(void*,void*);\n}\n'
 table='struct Hook{unsigned pc,size;void(*entry)();unsigned char raw[7];};const Hook hooks[]={'+','.join('{'+hex(h['pc'])+','+str(h['size'])+',&'+h['name']+',{'+','.join(hex(b)for b in bytes.fromhex(h['raw']))+'}}'for h in hooks)+'};\n'
 loader=pin(HERE/'loader_probe.cpp').read_text();loader=loader.replace('int main(int argc,char**argv){',declarations+table+CPP+'\nint main(int argc,char**argv){')
 loader=loader.replace('FreeLibrary(msvcp);FreeLibrary(crt);return 0;',RUN+'\n FreeLibrary(msvcp);FreeLibrary(crt);return 0;')
 (out/'reference.cpp').write_text(loader);(out/'hook-bindings.json').write_text(json.dumps(hooks,indent=2)+'\n')
 for p in out.iterdir():pin(p)
 pin(__file__);pin(ROOT/'tools/analysis/pe.py');pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
 report=dict(passed=True,scope='Transparent observer preparation for actual balanced scratch Lockit calls; execution pending',hooks=hooks,provider_IATs=[0x78146198,0x78146184],snapshot_bytes=13000,cpu_bytes=40,FX_bytes=512,ENV_bytes=28,frame_bytes=32,CS_bytes=24,page_count=3,state_seeded=False,original_executed=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
CPP=r'''
struct Cpu{unsigned eax,ecx,edx,ebx,esp,ebp,esi,edi,flags,pc;};static_assert(sizeof(Cpu)==40);
struct Snapshot{unsigned words[8];Cpu cpu;unsigned char fx[512],env[28],frame[32],CS[24],pages[3*4096],scratch[8];};static_assert(sizeof(Snapshot)==13064);
extern "C" {
Cpu probe_cpu{};alignas(16) unsigned char probe_fx[512]{};unsigned char probe_env[28]{};unsigned probe_kind{},probe_actual_Enter{},probe_actual_Leave{};
unsigned probe_sequence{},probe_object{},probe_count{},probe_error{};unsigned char probe_scratch[8]{};Snapshot probe_snapshots[32]{};
void probe_observe(){
 if(probe_count>=32){probe_error=1;return;}auto&s=probe_snapshots[probe_count];s={};s.words[0]=1;s.words[1]=probe_count;s.words[2]=probe_sequence;s.words[3]=probe_kind;s.words[4]=GetCurrentThreadId();s.words[5]=*reinterpret_cast<unsigned*>(0x78145658);s.words[6]=probe_object;s.words[7]=probe_kind==1?probe_actual_Enter:probe_kind==4?probe_actual_Leave:0;s.cpu=probe_cpu;if(s.words[7])s.cpu.pc=s.words[7];std::memcpy(s.fx,probe_fx,512);std::memcpy(s.env,probe_env,28);std::memcpy(s.frame,reinterpret_cast<void*>(s.cpu.esp),32);std::memcpy(s.CS,reinterpret_cast<void*>(0x78145640),24);unsigned n{};for(unsigned page:{0x7810a000u,0x78145000u,0x78146000u}){std::memcpy(s.pages+n*4096,reinterpret_cast<void*>(page),4096);++n;}std::memcpy(s.scratch,probe_scratch,8);++probe_count;
}
}
static bool patch(void*address,const void*data,unsigned size){DWORD prior{},ignored{};if(!VirtualProtect(address,size,PAGE_EXECUTE_READWRITE,&prior))return false;std::memcpy(address,data,size);return VirtualProtect(address,size,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),address,size);}
'''
RUN=r'''
 if(state!=2)return 11;probe_actual_Enter=*reinterpret_cast<unsigned*>(0x78146198);probe_actual_Leave=*reinterpret_cast<unsigned*>(0x78146184);
 for(const auto&h:hooks){if(std::memcmp(reinterpret_cast<void*>(h.pc),h.raw,h.size))return 12;unsigned char data[7]{0xe9};unsigned delta=ptr(reinterpret_cast<void*>(h.entry))-(h.pc+5);std::memcpy(data+1,&delta,4);for(unsigned n=5;n<h.size;++n)data[n]=0x90;if(!patch(reinterpret_cast<void*>(h.pc),data,h.size))return 13;}
 unsigned enter=ptr(reinterpret_cast<void*>(&probe_api_Enter)),leave=ptr(reinterpret_cast<void*>(&probe_api_Leave));if(!patch(reinterpret_cast<void*>(0x78146198),&enter,4)||!patch(reinterpret_cast<void*>(0x78146184),&leave,4))return 14;
 for(unsigned sequence=0;sequence<2;++sequence){probe_sequence=sequence;probe_object=ptr(probe_scratch);if(probe_call(reinterpret_cast<void*>(ctor),probe_scratch)!=probe_object)return 15;if(sequence){probe_object=ptr(probe_scratch+4);if(probe_call(reinterpret_cast<void*>(ctor),probe_scratch+4)!=probe_object)return 16;probe_call(reinterpret_cast<void*>(dtor),probe_scratch+4);}probe_object=ptr(probe_scratch);probe_call(reinterpret_cast<void*>(dtor),probe_scratch);if(*reinterpret_cast<unsigned*>(0x78145658)!=2||*reinterpret_cast<unsigned*>(0x78145648)||*reinterpret_cast<unsigned*>(0x7814564c))return 17;}
 if(probe_error||probe_count!=18)return 18;std::ofstream snapshots(out/"snapshots.bin",std::ios::binary);snapshots.write(reinterpret_cast<char*>(probe_snapshots),sizeof(Snapshot)*probe_count);snapshots.close();if(!snapshots)return 19;
 for(const auto&h:hooks)if(!patch(reinterpret_cast<void*>(h.pc),h.raw,h.size))return 20;if(!patch(reinterpret_cast<void*>(0x78146198),&probe_actual_Enter,4)||!patch(reinterpret_cast<void*>(0x78146184),&probe_actual_Leave,4))return 21;
 for(const auto page:{0x7810a000u,0x78145000u,0x78146000u}){char name[64]{};std::snprintf(name,sizeof(name),"after-restored-%08x-page.bin",page);if(!save(out/name,page,4096))return 22;}
 for(const auto pair:{std::pair<const char*,HMODULE>{"kernel32-image.bin",GetModuleHandleW(L"kernel32.dll")},{"ntdll-image.bin",GetModuleHandleW(L"ntdll.dll")}}){wchar_t module[32768]{};if(!GetModuleFileNameW(pair.second,module,32768))return 23;std::ifstream original(std::filesystem::path(module),std::ios::binary);std::ofstream copied(out/pair.first,std::ios::binary);copied<<original.rdbuf();if(!original||!copied)return 24;}
 std::ofstream run(out/"run.json");run<<"{\"passed\":true,\"snapshots\":"<<probe_count<<",\"snapshot_bytes\":"<<sizeof(Snapshot)<<",\"actual_Enter\":"<<probe_actual_Enter<<",\"actual_Leave\":"<<probe_actual_Leave<<",\"scratch\":"<<ptr(probe_scratch)<<",\"sequences\":2,\"balanced_pairs\":3,\"recursive_depth\":2,\"state_seeded\":false,\"original_executed\":true,\"game_called\":false,\"restored\":true}\n";if(!run)return 25;
'''
if __name__=='__main__':main(sys.argv[1])
