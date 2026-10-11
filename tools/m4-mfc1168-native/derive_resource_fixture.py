"""Add real provider/lifecycle proof, complete host boundary and finite controls.

Historical fixture2/build3 remains byte immutable. This is unexecuted code until
its fresh preparation and prelaunch review have passed.
"""
from pathlib import Path
import hashlib
p=Path(__file__).parent;s=(p/'fixture_v2.cpp').read_text()
for name in ('TlsAlloc','TlsGetValue','TlsSetValue','TlsFree','InitializeCriticalSection','EnterCriticalSection','LeaveCriticalSection','DeleteCriticalSection','GetACP'):
 s=s.replace(name+'(', 'mf_'+name+'(')
anchor='struct Block{unsigned address,size,permissions;std::vector<std::byte>initial;};'
s=s.replace(anchor,'#include "resource_witness.hpp"\nstatic unsigned control_mode{};static bool control_fired{};static std::string refusal;\n'+anchor)
s=s.replace('InitializeCriticalSection(&CS);CS_live=true;', 'InitializeCriticalSection(&CS);CS_live=true;') # Named wrapper already renamed.
s=s.replace('mf_InitializeCriticalSection(&CS);CS_live=true;', 'resource_CS=&CS;mf_InitializeCriticalSection(&CS);CS_live=true;')
s=s.replace(' void authority(){', ''' void cleanup_failed(){require(GetCurrentThreadId()==host_thread,"Owned cleanup current-thread");if(CS_live){require(CS.RecursionCount<=1,"Finite actual native CS cleanup depth");if(CS.RecursionCount)mf_LeaveCriticalSection(&CS);CS_depth=0;mf_DeleteCriticalSection(&CS);CS_live=false;}if(TLS_live){require(mf_TlsSetValue(host_TLS,nullptr)&&mf_TlsGetValue(host_TLS)==nullptr,"Actual failed TLS clear");require(mf_TlsFree(host_TLS),"Actual failed TLS free");TLS_live=false;}if(current==this)current=nullptr;resource_CS=nullptr;}
 void authority(){''')
s=s.replace(' void*dispatch(unsigned target,bool tail){authority();', ' void*dispatch(unsigned target,bool tail){authority();if(control_mode==11&&!control_fired&&!tail){control_fired=true;target=0x5f4053fe;}')
s=s.replace('std::uint64_t read(unsigned a,unsigned n){authority();', '''std::uint64_t read(unsigned a,unsigned n){authority();if(!control_fired&&access_cursor==18&&control_mode>=1&&control_mode<=3){control_fired=true;if(control_mode==1)a=mf::global_pointer+4;if(control_mode==2)n=1;if(control_mode==3)s.gpr.rip.dword+=1;}''')
s=s.replace('void write(unsigned a,std::uint64_t v,unsigned n){authority();', 'void write(unsigned a,std::uint64_t v,unsigned n){authority();if(control_mode==10&&!control_fired&&a==mf::global_pointer+0x14){control_fired=true;v=1;}')
s=s.replace('const auto&spec=mf::APIs[index];require(target==spec.raw', '''const auto&spec=mf::APIs[index];if(!control_fired){if(control_mode==4&&index==0){control_fired=true;r.memory().store<unsigned>({s.gpr.rsp.dword+4},4);}if(control_mode==5&&index==0){control_fired=true;require(mf_TlsSetValue(host_TLS,nullptr),"Control actual foreign TLS association");}if(control_mode==6&&index==1){control_fired=true;target+=4;}if(control_mode==7&&index==1){control_fired=true;r.memory().store<unsigned>({s.gpr.rsp.dword+4},mf::CS_pointer+4);}if(control_mode==8&&index==1){control_fired=true;CS_depth=1;}if(control_mode==9&&index==1){control_fired=true;r.memory().protect({mf::CS_pointer},Permissions::read);}}require(target==spec.raw''')
# Every physical source row is validated before native entry. Source code pages
# are not admitted solely because the linked body object was once reviewed.
s=s.replace('c.entered=true;auto cpu=r.cpu();', '''c.entered=true;for(const auto&span:mf::source_spans){std::array<std::byte,16>bytes{};r.memory().read({span.pc},std::span(bytes.data(),span.size));require(std::equal(bytes.begin(),bytes.begin()+span.size,span.bytes.begin()),"Exact complete physical source span admission");}auto cpu=r.cpu();''')
s=s.replace('static void native_root(Runtime&r)', 'static void native_root(Runtime&r)')
anchor='int main(int argc,char**argv)'
code='''extern "C" void mfc_hardware_call(Runtime*,void*);
extern "C" void mfc_invoke_guarded(Runtime*r){auto&c=owner(current);try{r->invoke({0x5ae3e4});require(control_mode==0,"Finite control unexpectedly completed");c.finish();}catch(const std::exception&e){refusal=e.what();require(control_mode&&control_fired&&r->poisoned(),"Precise actual control refusal/poison");c.checkpoint("retry/before");dump("retry/before/RuntimeCPU.bin",&r->cpu(),40);const std::array<unsigned,4>before{unsigned(r->calls().size()),c.access_cursor,c.API_cursor,unsigned(c.frames.size())};dump("retry/before/private.bin",before.data(),sizeof(before));bool rejected=false;try{r->invoke({0x5ae3e4});}catch(const Fault&f){rejected=f.reason()==FaultReason::poisoned;}require(rejected,"Same actual poisoned Runtime retry rejected");c.checkpoint("retry/after");dump("retry/after/RuntimeCPU.bin",&r->cpu(),40);const std::array<unsigned,4>after{unsigned(r->calls().size()),c.access_cursor,c.API_cursor,unsigned(c.frames.size())};dump("retry/after/private.bin",after.data(),sizeof(after));c.cleanup_failed();}dump("result/refusal.txt",refusal.data(),refusal.size());}
'''
s=s.replace(anchor,code+anchor)
s=s.replace('require(argc==4,"image BEFORE-pack fresh-output");output=argv[3];','require(argc==5,"image BEFORE-pack fresh-output control-mode");control_mode=std::stoul(argv[4]);require(control_mode<=12,"Finite control catalog");output=argv[3];')
s=s.replace('Context c(r,blocks);r.invoke({0x5ae3e4});require(r.calls().size()==1&&r.calls()[0].completed&&!r.poisoned(),"Actual registered Runtime dispatcher completed");', '''Context c(r,blocks);if(control_mode==12){control_fired=true;auto i=std::find_if(blocks.begin(),blocks.end(),[](const auto&b){return b.address==0x5f401000;});require(i!=blocks.end(),"Actual source provider RX page control");r.memory().protect({i->address},Permissions::read|Permissions::write);r.memory().store<std::uint8_t>({0x5f401083},0xcc);r.memory().protect({i->address},static_cast<Permissions>(i->permissions));}alignas(16)std::array<std::byte,1632>hardware{};mfc_hardware_call(&r,hardware.data());dump("host-hardware.bin",hardware.data(),hardware.size());if(control_mode==0)require(r.calls().size()==1&&r.calls()[0].completed&&!r.poisoned(),"Actual registered Runtime dispatcher completed");else require(!refusal.empty()&&r.poisoned()&&!c.TLS_live&&!c.CS_live,"Actual controlled refusal and native resource cleanup");''')
s=s.replace('c.finish();const std::array<unsigned,10>schema', 'const std::array<unsigned,10>schema')
s=s.replace('dump("COMPLETE.txt","complete",8);', 'const std::array<unsigned,6>result{control_mode,unsigned(control_fired),unsigned(r.poisoned()),unsigned(c.TLS_live),unsigned(c.CS_live),resource_serial};dump("result/status.bin",result.data(),sizeof(result));dump("COMPLETE.txt","complete",8);')
s=s.replace('current=nullptr;const std::array<std::uint64_t,8>lifecycle', 'current=nullptr;resource_CS=nullptr;const std::array<std::uint64_t,8>lifecycle')
(p/'fixture_resource.cpp').write_text(s);print(hashlib.sha256((p/'fixture_resource.cpp').read_bytes()).hexdigest())
