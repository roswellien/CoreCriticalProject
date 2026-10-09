// Independent authored controls linked to frozen native libraries. No original
// game/vendor instruction executes and no author executor/comparator is imported.
#include "registry.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
using namespace mw34;
namespace cn=mw34::m4_cmd_native;
unsigned assertions{},scenarios{};
void check(bool v,const char*w){++assertions;if(!v)throw std::runtime_error(w);}
std::vector<std::byte> file(const char*p){std::ifstream f(p,std::ios::binary|std::ios::ate);if(!f)throw std::runtime_error("Input");auto n=f.tellg();std::vector<std::byte>b(n);f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),n);return b;}
State dirty(unsigned variant){State s;auto*b=reinterpret_cast<unsigned char*>(&s);for(unsigned i=0;i<sizeof(s);++i)b[i]=static_cast<unsigned char>(i*31+variant*17+3);std::memset(&s.addr,0,sizeof(s.addr));s.addr.fs_base.dword=0x7ffde000;s.gpr.rip.dword=cn::writer.value;s.gpr.rsp.dword=0x20001800;s.gpr.rax.dword=0xbad0abcd;s.gpr.rcx.dword=0x99887766;s.gpr.rdx.dword=0x12345678;s.gpr.rbx.dword=0x99aabbcc;s.gpr.rbp.dword=0x88776655;s.gpr.rsi.dword=0x11111111;s.gpr.rdi.dword=0x22222222;s.rflag.flat=0x202;s.aflag.cf=s.aflag.pf=s.aflag.af=s.aflag.zf=s.aflag.sf=s.aflag.df=s.aflag.of=0;s.x87.fxsave.cwd.flat=0x37f;s.x87.fxsave.swd.flat=static_cast<unsigned short>((variant&1)*7<<11);s.x87.fxsave.ftw.flat=0;s.x87.fxsave.mxcsr.flat=0x1f80;return s;}
bool absent(GuestMemory&m,GuestAddress a){try{(void)m.load<unsigned>(a);return false;}catch(const MemoryFault&e){return e.reason()==MemoryFaultReason::unmapped;}}
struct Host{
 alignas(16)std::array<std::byte,512>start{},finish{};std::array<std::byte,28>env{},end{};
 Host(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(start),"=m"(env)::"memory");}
 void restore(){__asm__ volatile("fxrstor64 %2\n\tfldenv %3\n\tfxsave64 %0\n\tfnstenv %1":"=m"(finish),"=m"(end):"m"(start),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");check(start==finish&&env==end,"Independent complete host FX512/ENV28 restoration");}
 ~Host(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(start),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
};
int main(int argc,char**argv){try{
 check(argc==4,"Exact actual frozen source inputs");auto game=file(argv[1]),provider=file(argv[2]),pack=file(argv[3]);
 for(unsigned mode=0;mode<28;++mode){++scenarios;std::cerr<<"independent scenario "<<mode<<'\n';auto runtime=m4_runtime::Runtime::from_admitted_image(game);auto&m=runtime.memory();auto s=dirty(mode);m.store<unsigned>({0x20001800},cn::capture_gate.value);
  std::unique_ptr<cn::Registry>r=std::make_unique<cn::Registry>(runtime);
  GuestAddress sentinel{mode==3?0x78001000U:mode==4?0x7802e000U:mode==5?0x78037000U:0x33000000U};bool foreign=mode>=3&&mode<=6;
  if(foreign){m.map(sentinel,16,Permissions::read|Permissions::write);m.store<unsigned>(sentinel,0xaabbddee);}
  auto changed_provider=provider,changed_pack=pack;if(mode==1)changed_provider[100]^=std::byte{1};if(mode==2)changed_pack[100]^=std::byte{1};
  bool admitted=r->admit(changed_provider,changed_pack);bool success{};
  if(mode>=1&&mode<=5){check(!admitted&&!r->ready()&&r->first_fault(),"Actual identity/mapping ownership denial");}
  else{
   check(admitted&&!r->ready(),"Exact admission has not manufactured initialized success");
   if(mode==7)s.gpr.rip.dword++;
   if(mode==8)s.gpr.rsp.dword+=4;
   if(mode==9)s.aflag.df=1;
   if(mode==10)s.addr.ds_base.dword=8;
   if(mode==11)s.addr.ss_base.dword=8;
   if(mode==12)m.protect({0x20000000},Permissions::read);
   if(mode==13)m.protect({0x78037000},Permissions::read);
   if(mode==14)m.unmap({0x20000000});
   if(mode==15)m.unmap({0x78001000});
   if(mode==16)m.unmap({0x7802e000});
   if(mode==17)m.unmap({0x78037000});
   if(mode==18){m.protect({0x78001000},Permissions::read|Permissions::write);m.store<unsigned>(cn::writer,0);}
   if(mode==19){m.protect({0x7802e000},Permissions::read|Permissions::write);m.store<unsigned>(cn::provider_iat,0);}
   auto before=s;{Host host;success=r->initialize(s);host.restore();}
   if(mode==0||mode>=20){
    check(success&&r->ready()&&r->compiled_capture_complete(),"Actual statically compiled writer reaches only its declared capture");
    State wanted=before;wanted.gpr.rax.dword=cn::buffer_start.value;wanted.gpr.rsp.dword=0x20001800;wanted.gpr.rip.dword=cn::capture_gate.value;
    check(!std::memcmp(&s,&wanted,3504),"All3504 State bytes reflect only actual CALL/MOV/JMP and typed service writes");
    const auto&host=r->host_snapshot();auto actual=GetCommandLineA();auto n=std::strlen(actual)+1;
    check(host.borrowed_pointer==reinterpret_cast<std::uintptr_t>(actual)&&host.bytes.size()==n&&!std::memcmp(host.bytes.data(),actual,n),"Independent real OS bytes/host pointer provenance");
    std::vector<std::byte>owned(n);m.read(cn::buffer_start,owned);check(owned==host.bytes,"Independent owned guest bytes equal own actual OS query");
    check(r->resolve_data(cn::game_iat)==cn::provider_global&&m.load<unsigned>(cn::provider_global)==cn::buffer_start.value,"Only actual compiled global store supplies ready data load");
    check(r->route().target==cn::service_gate.value&&r->route().return_pc==cn::return_pc.value&&r->route().entry_esp==0x200017fc&&r->route().exit_esp==0x20001800&&r->route().completed,"Exact actual CALL return word and zero argument cleanup");
    check(r->events().size()==5&&r->events()[0].address==cn::provider_iat.value&&r->events()[1].address==0x200017fc&&r->events()[1].value==cn::return_pc.value&&r->events()[3].width==n&&r->events()[4].address==cn::provider_global.value,"Actual ordered access/copy/global event extent");
    if(mode==20)check(!r->resolve_data({cn::game_iat.value+4}),"Unknown data slot rejection");
    if(mode==21){m.store<unsigned>(cn::provider_global,cn::buffer_start.value+1);check(!r->resolve_data(cn::game_iat),"Changed live pointer rejection");}
    if(mode==22){m.protect(cn::buffer_start,Permissions::read|Permissions::write);m.store<unsigned>(cn::buffer_start,0);check(!r->resolve_data(cn::game_iat),"Changed actual buffer bytes rejection");}
    if(mode==23){m.protect(cn::buffer_start,Permissions::none);check(!r->resolve_data(cn::game_iat),"Unreadable own bytes rejection");}
    if(mode==24)check(!r->initialize(s),"Already entered registry cannot initialize twice");
    if(mode==25)check(!r->admit(provider,pack),"Already admitted registry cannot admit twice");
    if(mode==26){m.protect({0x7802e000},Permissions::read|Permissions::write);m.store<unsigned>(cn::provider_iat,1);check(!r->resolve_data(cn::game_iat),"Changed ready provider source owner rejection");}
    if(mode==27){m.protect({0x5bb000},Permissions::read|Permissions::write);m.store<unsigned>(cn::game_iat,1);check(!r->resolve_data(cn::game_iat),"Changed ready game data owner rejection");}
   }else{
    check(!success&&!r->ready()&&!r->compiled_capture_complete()&&r->first_fault(),"Required actual fault cannot become a completed writer");
    check((mode==6||mode==13)==!r->host_snapshot().bytes.empty(),"Only causal late buffer/global controls reached the actual OS query");
    if(mode==12||mode==14)check(r->events().size()==1,"Stack-write fault stops after the actual IAT read");
   }
  }
  if(mode){auto fault=*r->first_fault();auto state=s;check(!r->initialize(s)&&!r->resolve_data(cn::game_iat)&&!r->admit(provider,pack),"Faulted registry remains terminal on corrected requests");check(fault.reason==r->first_fault()->reason&&fault.site==r->first_fault()->site&&fault.detail==r->first_fault()->detail&&!std::memcmp(&s,&state,3504),"First fault and complete State remain stable on terminal reuse");}
  r.reset();for(auto a:{GuestAddress{0x78001000},GuestAddress{0x7802e000},GuestAddress{0x78037000},cn::buffer_start}){if(foreign&&a==sentinel)check(m.load<unsigned>(a)==0xaabbddee,"Owned cleanup preserves actual foreign collision sentinel");else check(absent(m,a),"All successfully acquired mappings/partial buffer released");}
 }
 std::cout<<"{\"independent\":true,\"checks\":"<<assertions<<",\"scenarios\":"<<scenarios<<",\"original_execution\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
