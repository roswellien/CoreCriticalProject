#pragma once
#include "runtime.hpp"
#include "admission.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <cstring>
#include <thread>
namespace mw34::m4_crt_entry_mainargs {
inline constexpr unsigned slot=0x5bb514,entry=0x7800ba5e,builder=0x7800bbbc,return_pc=0x5ac46e,internal_call=0x7800ba99,internal_return=0x7800ba9e,import_call=0x7800bbd0,import_slot=0x7802e018,import_return=0x7800bbd6,newmode=0x78037150;
extern "C" void*mw34_mainargs_mainargs_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_mainargs_normal_argv_body(State*,unsigned,void*) noexcept(false);
struct Access{unsigned pc,address,value,width,write;};
struct Event{unsigned kind,pc,address,value;};
struct BridgeAbort{};struct Context;inline thread_local Context*owner{};
struct Context {
 m4_runtime::Runtime&runtime;State&state;
 unsigned raw{},provider_raw{},frame{},ret{},argc_ptr{},argv_ptr{},env_ptr{},wildcard{},startup_ptr{},startup_value{},loaded_startup{},access_count{},event_count{},boundary_depth{},stage{},fault_pc{},fault_address{};
 bool used{},active{},failed{},reached_import{};const char*reason{};std::thread::id thread=std::this_thread::get_id();
 std::array<unsigned,4>nonvolatile{};std::array<Access,64>accesses{};std::array<Event,16>events{};
 void(*test_before_execute)(Context&,unsigned){};void(*test_after_access)(Context&,unsigned){};void(*test_after_event)(Context&,unsigned){};
 Context(m4_runtime::Runtime&r,std::span<const std::byte>provider):runtime(r),state(*reinterpret_cast<State*>(r.remill_state().data())) {
  if(r.domain()!=m4_runtime::Domain::admitted_game||!r.remill_seeded())throw std::invalid_argument("Exact admitted persistent mainargs State required");
  unsigned count{};for(const auto&i:r.image_metadata().imports)if(r.image_metadata().image_base+i.iat_rva==slot){if(i.library!="MSVCRT.dll"||!i.name||*i.name!="__getmainargs")throw std::invalid_argument("Unique actual mainargs named game owner");raw=i.original_iat_value;++count;}
  if(count!=1||raw!=0x1ded02||r.memory().load<unsigned>({slot})!=raw)throw std::invalid_argument("Original unique mainargs raw game IAT");
  provider_raw=provider_import(provider);if(provider_raw!=0x343b0||r.memory().load<unsigned>({import_slot})!=provider_raw)throw std::invalid_argument("Literal unique GetModuleFileNameA provider IAT");
 }
 static unsigned provider_import(std::span<const std::byte>b){
  if(m4::sha256(b)!="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7")throw std::invalid_argument("Exact provider import source required");
  auto word=[&](unsigned p){if(std::uint64_t(p)+2>b.size())throw std::invalid_argument("Provider PE word bounds");unsigned short v{};std::memcpy(&v,b.data()+p,2);return v;};
  auto dword=[&](unsigned p){if(std::uint64_t(p)+4>b.size())throw std::invalid_argument("Provider PE DWORD bounds");unsigned v{};std::memcpy(&v,b.data()+p,4);return v;};
  const auto pe=dword(0x3c),opt=pe+24;if(dword(pe)!=0x4550||word(pe+4)!=0x14c||word(opt)!=0x10b||dword(opt+28)!=0x78000000)throw std::invalid_argument("Exact PE32 provider import authority");
  auto offset=[&](unsigned rva,unsigned size){unsigned matches{},result{};for(unsigned n=0;n<word(pe+6);++n){const auto p=opt+word(pe+20)+n*40,va=dword(p+12),rs=dword(p+16),rp=dword(p+20);if(rva>=va&&std::uint64_t(rva)+size<=std::uint64_t(va)+rs){result=rp+rva-va;++matches;}}if(matches!=1||std::uint64_t(result)+size>b.size())throw std::invalid_argument("Provider import raw RVA bounds");return result;};
  auto text=[&](unsigned rva){const auto p=offset(rva,1);std::string result;for(unsigned n=0;n<4096;++n){if(p+n>=b.size())throw std::invalid_argument("Provider name bounds");auto v=std::to_integer<unsigned char>(b[p+n]);if(!v)return result;result.push_back(static_cast<char>(v));}throw std::invalid_argument("Terminated provider import name required");};
  const auto directory=dword(opt+104),size=dword(opt+108);unsigned matches{},result{};bool terminal{};
  for(unsigned d=0;d<size/20;++d){const auto p=offset(directory+d*20,20),original=dword(p),name=dword(p+12),iat=dword(p+16);if(!(original||dword(p+4)||dword(p+8)||name||iat)){terminal=true;break;}const auto library=text(name);const auto lookup=original?original:iat;bool end{};
   for(unsigned n=0;n<8192;++n){const auto value=dword(offset(lookup+4*n,4));if(!value){end=true;break;}if(!(value&0x80000000U)&&text(value+2)=="GetModuleFileNameA"){if(library!="KERNEL32.dll"||0x78000000+iat+4*n!=import_slot||word(offset(value,2))!=292)throw std::invalid_argument("Exact unique provider GetModuleFileNameA name/hint/slot");result=dword(offset(iat+4*n,4));++matches;}}
   if(!end)throw std::invalid_argument("Provider import thunk termination");
  }if(!terminal||matches!=1)throw std::invalid_argument("Exactly one named GetModuleFileNameA provider import");return result;
 }
 void first(const char*w,unsigned address=0,unsigned pc=0){if(!failed){failed=true;reason=w;fault_pc=pc?pc:state.gpr.rip.dword;fault_address=address;}}
 [[noreturn]]void deny(const char*w,unsigned address=0,unsigned pc=0){first(w,address,pc);throw BridgeAbort{};}
 void guard(){if(owner!=this||!active||failed||thread!=std::this_thread::get_id())deny("Exact current active serial mainargs owner required");}
 bool stack(unsigned a)const{return a>=0x20001000&&std::uint64_t(a)+4<=0x20002000;}
 void source_identity(){std::array<std::byte,66>a{};std::array<std::byte,140>b{};bool bad{};try{runtime.memory().read({entry},a);runtime.memory().read({builder},b);bad=m4::sha256(a)!="50b6f5f60add9aa9b90997c77efd5fc4ae886ce0443e7dfb803f4b243041073c"||m4::sha256(b)!="50452775522f91555512d02232fd46c4b4f4363b757763d00c2ba81fd0cc28c4"||runtime.memory().load<unsigned>({slot})!=raw;}catch(...){bad=true;}if(bad)deny("Exact mainargs/provider source and game IAT identity");}
 void event(unsigned kind,unsigned pc,unsigned address,unsigned value){if(event_count==events.size())deny("Mainargs route bound");events[event_count++]={kind,pc,address,value};if(test_after_event)test_after_event(*this,event_count);}
 void access(unsigned a,unsigned value,unsigned write){if(access_count==accesses.size())deny("Mainargs access bound",a);accesses[access_count++]={state.gpr.rip.dword,a,value,4,write};if(test_after_access)test_after_access(*this,access_count);}
 unsigned read(unsigned a){guard();const auto pc=state.gpr.rip.dword;
  if(!((stage==1&&pc==0x7800ba61&&a==frame+20&&state.gpr.rbp.dword==frame-4)||(stage==1&&pc==0x7800ba64&&a==frame+16&&state.gpr.rbp.dword==frame-4)||(stage==1&&pc==0x7800ba68&&a==startup_ptr)||(stage==2&&pc==import_call&&a==import_slot)))deny("Required mainargs read outside exact source operand",a);
  unsigned value{};bool bad{};try{value=runtime.memory().load<unsigned>({a});}catch(...){bad=true;}if(bad)deny("Required checked mainargs read fault",a);
  if(pc==0x7800ba61&&value!=startup_ptr)deny("Mainargs startup pointer changed",a);if(pc==0x7800ba68)loaded_startup=value;if(pc==import_call&&value!=provider_raw)deny("Actual named GetModuleFileNameA raw IAT changed",a);access(a,value,0);return value;
 }
 void write(unsigned a,unsigned value){guard();const auto pc=state.gpr.rip.dword;bool valid{};
  if(stage==1){valid=(pc==entry&&a==frame-4&&value==nonvolatile[1])||(pc==0x7800ba6a&&a==newmode&&value==loaded_startup)||((pc==internal_call||pc==0x7800ba71)&&a==frame-8&&value==(pc==internal_call?internal_return:0x7800ba76));}
  if(stage==2){const unsigned f=frame-8;valid=(pc==builder&&a==f-4&&value==frame-4)||((pc==0x7800bbbf||pc==0x7800bbc0)&&a==state.gpr.rsp.dword-4&&value==state.gpr.rcx.dword)||(pc==0x7800bbc1&&a==f-16&&value==nonvolatile[2])||(pc==0x7800bbc2&&a==f-20&&value==nonvolatile[3])||(pc==0x7800bbc8&&a==f-24&&value==260)||(pc==0x7800bbcd&&a==f-28&&value==0x7803b3f0)||(pc==0x7800bbce&&a==f-32&&value==0)||(pc==import_call&&a==f-36&&value==import_return);}
  if(!valid||(!stack(a)&&a!=newmode))deny("Required mainargs write outside actual source PUSH/CALL/store",a);
  bool bad{};try{runtime.memory().store<unsigned>({a},value);}catch(...){bad=true;}if(bad)deny("Required checked mainargs write fault",a);access(a,value,1);
  if(pc==0x7800ba6a&&value!=0)deny("Required nonzero startup mode outside admitted zero domain",a);
 }
 void nested(State*,unsigned,void*);
 [[noreturn]]void called(State*s,unsigned target){guard();source_identity();const auto f=frame-8;if(stage!=2||s!=&state||target!=provider_raw||state.gpr.rip.dword!=target||state.gpr.rsp.dword!=f-36||access_count<2)deny("Actual GetModuleFileNameA CALL State/frame rejected",target,import_call);
  const auto&r=accesses[access_count-2];const auto&w=accesses[access_count-1];if(r.pc!=import_call||r.address!=import_slot||r.value!=target||r.write||w.pc!=import_call||w.address!=f-36||w.value!=import_return||!w.write||runtime.memory().load<unsigned>({f-36})!=import_return||runtime.memory().load<unsigned>({f-32})!=0||runtime.memory().load<unsigned>({f-28})!=0x7803b3f0||runtime.memory().load<unsigned>({f-24})!=260)deny("Actual named GetModuleFileNameA argument/return words changed",import_slot,import_call);
  event(4,import_call,import_slot,target);reached_import=true;first("Required KERNEL32.dll!GetModuleFileNameA remains unresolved",import_slot,import_call);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_import,{import_call},{import_slot},reason);
 }
 [[noreturn]]void unsupported(State*s,unsigned target,void*p,unsigned site){guard();if(p!=this||s!=&state||state.gpr.rip.dword!=target)deny("Exact current mainargs unsupported helper token",target,site);if(target==0x7800b3b4)event(7,site,target,0x7800ba76);deny("Required mainargs helper remains outside admitted prefix",target,site);}
};
}
