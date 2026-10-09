// Replays ONLY actual captured original pre-body fields into the native model.
// Original after fields are never read or used as expected outputs here.
#include "crt_services.hpp"
#include "probe_common.hpp"
#include "probe_io.hpp"
#include "replay_spec.hpp"
#include <iostream>
#include <memory>
#include <remill/Arch/X86/Runtime/State.h>
using namespace mw34;
using namespace mw34::m4_runtime;
using namespace mw34::m4_crt;
using namespace mw34::m4_crt_probe;
static_assert(sizeof(State)==3504&&alignof(State)<=64);
namespace {
m4::LoadedImage fixture(){
 m4::LoadedImage x;const auto rx=Permissions::read|Permissions::execute;
 x.metadata.image_base=0x400000;x.metadata.entry_point=GuestAddress{0x10000080};x.metadata.mapped_regions={{"authored callback code",GuestAddress{0x10000000},8192,rx}};
 x.memory.map(GuestAddress{0x10000000},8192,rx);x.memory.map(GuestAddress{table_page},4096,Permissions::read|Permissions::write);x.memory.map(GuestAddress{0x5bb000},4096,Permissions::read|Permissions::write);
 const std::array<const char*,4>names{"_initterm","__set_app_type","__p__fmode","__p__commode"};const Slots s;const std::array<GuestAddress,4>slots{s.initterm,s.set_app_type,s.p_fmode,s.p_commode};
 for(unsigned i=0;i<4;++i){m4::ImportSymbol item;item.library="MSVCRT.dll";item.name=names[i];item.iat_rva=slots[i].value-x.metadata.image_base;item.original_iat_value=0x87654300+i;x.metadata.imports.push_back(item);x.memory.store<std::uint32_t>(slots[i],item.original_iat_value);}
 x.memory.protect(GuestAddress{0x5bb000},Permissions::read);return x;
}
Policy policy(){Policy p;p.stack_low=GuestAddress{stack_page};p.stack_bytes=4096;p.heap_bytes=4096;p.max_call_depth=8;p.max_call_records=16;return p;}
void leaf(Runtime&r,unsigned digit){
 need(r.cpu().esp==stack_entry-8&&r.memory().load<std::uint32_t>(GuestAddress{r.cpu().esp})==0x78001510,"Actual provider callback guest return frame");need(r.calls().back().site.value==0x7800150e,"Actual provider callback CALL site");
 const auto value=r.memory().load<std::uint32_t>(GuestAddress{counter});r.memory().store<std::uint32_t>(GuestAddress{counter},value*10+digit);
 r.cpu().eax=0xaabbcc00+digit;r.cpu().ecx=0x12345600+digit;r.cpu().edx=0xfedcba00+digit;r.ret();
}
void one(Runtime&r){leaf(r,1);}void two(Runtime&r){leaf(r,2);}void three(Runtime&r){leaf(r,3);}
void mutate(Runtime&r){r.memory().store<std::uint32_t>(GuestAddress{table_begin+4},callbacks[2]);leaf(r,1);}
void shrink(Runtime&r){r.memory().store<std::uint32_t>(GuestAddress{r.cpu().esp+16},table_begin+4);leaf(r,1);}
Cpu projection(const Cpu32&c){return {c.eax,c.ecx,c.edx,c.ebx,c.esp,c.ebp,c.esi,c.edi,c.eflags,c.eip};}
void memory(Runtime&r,std::uint8_t*b){r.memory().read(GuestAddress{stack_page},{reinterpret_cast<std::byte*>(b),4096});r.memory().read(GuestAddress{table_page},{reinterpret_cast<std::byte*>(b+4096),4096});r.memory().read(GuestAddress{Session::provider_app_type},{reinterpret_cast<std::byte*>(b+8192),12});}
std::uint16_t word(const std::uint8_t *p){std::uint16_t value{};std::memcpy(&value,p,2);return value;}
std::uint32_t dword(const std::uint8_t *p){std::uint32_t value{};std::memcpy(&value,p,4);return value;}
void seed_legacy(State&s,const std::uint8_t *env){
 auto &f=s.x87.fxsave;f.cwd.flat=word(env);f.swd.flat=word(env+4);need(word(env+8)==0xffff&&f.ftw.flat==0,"Empty physical legacy tag domain");f.ip=dword(env+12);f.cs.flat=word(env+16);f.fop=word(env+18);f.dp=dword(env+20);f.ds.flat=word(env+24);
}
std::array<std::uint8_t,28> legacy_capture(const State&s,const std::uint8_t *reserved_input){
 std::array<std::uint8_t,28>env{};std::memcpy(env.data(),reserved_input,28);const auto &f=s.x87.fxsave;put16(env.data(),f.cwd.flat);put16(env.data()+4,f.swd.flat);need(f.ftw.flat==0,"Native physical tags remain empty");put16(env.data()+8,0xffff);put32(env.data()+12,f.ip);put16(env.data()+16,f.cs.flat);put16(env.data()+18,f.fop);put32(env.data()+20,f.dp);put16(env.data()+24,f.ds.flat);return env;
}
}
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 need(argc==5,"CRT replay: exact-provider exact-original-prestates fresh-raw fresh-ledger");const auto provider_bytes=read(argv[1],266293);need(provider_bytes.size()==266293&&digest(provider_bytes)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7","Provider identity rejected");
 const auto raw=read(argv[2],24+record_count*original_stride);need(raw.size()==24+record_count*original_stride&&digest(raw)==original_sha,"Original input identity rejected");need(std::memcmp(raw.data(),"MW4CRO01",8)==0,"Original input version rejected");const std::array<std::uint32_t,4>expected{1,record_count,original_stride,memory_bytes};need(std::memcmp(raw.data()+8,expected.data(),16)==0,"Original input header rejected");
 Output out(argv[3]),ledger(argv[4]);out.write("MW4CRN01",8);const std::uint32_t header[]{1,record_count,native_stride,memory_bytes};out.write(header,sizeof(header));std::ostringstream events;events<<"{\"scope\":\"Authored provider contract replay; before fields only\",\"whole_M4_complete\":false,\"records\":[";
 unsigned ordinal{};for(unsigned repeat=0;repeat<2;++repeat)for(unsigned c=0;c<9;++c)for(auto cw:controls)for(unsigned top=0;top<8;++top,++ordinal){
  const auto *record=raw.data()+24+ordinal*original_stride;const std::uint32_t tag[]{repeat,c,cw,top,0};need(std::memcmp(record,tag,20)==0,"Original input tag order");
  Cpu before{};std::memcpy(&before,record+20,40);const auto seeded=seed_cpu(c);need(std::memcmp(&before,&seeded,40)==0,"Original actual pre-body CPU admission");
  std::array<std::uint8_t,memory_bytes>authored{},after{};seed_memory(authored.data(),authored.data()+4096,authored.data()+8192,c);need(std::memcmp(record+2260,authored.data(),memory_bytes)==0,"Original actual pre-body authored memory admission");
  auto r=Runtime::for_authored_fixture(fixture(),policy());Session s(r,{reinterpret_cast<const std::byte*>(provider_bytes.data()),provider_bytes.size()});const std::array<NativeEntry,5>functions{one,two,three,mutate,shrink};
  for(unsigned i=0;i<5;++i)r.register_translation({GuestAddress{callbacks[i]},{},functions[i],"authored callback",{}});
  r.memory().write(GuestAddress{stack_page},{reinterpret_cast<const std::byte*>(record+2260),4096});r.memory().write(GuestAddress{table_page},{reinterpret_cast<const std::byte*>(record+6356),4096});r.memory().write(GuestAddress{Session::provider_app_type},{reinterpret_cast<const std::byte*>(record+10452),12});
  // Runtime's CALL establishes the same entry stack frame. The captured pre-PC
  // is a declared body-entry tag in both streams, not a sampled hardware EIP.
  r.cpu()={before.eax,before.ecx,before.edx,before.ebx,before.esp+4,before.ebp,before.esi,before.edi,before.flags,0x10000080};std::memcpy(r.fx().data(),record+100,512);
  auto *state=new(r.remill_state().data())State;for(unsigned i=0;i<r.remill_state().size();++i)r.remill_state()[i]=std::byte(static_cast<std::uint8_t>(i*13+7));std::memcpy(&state->x87,record+100,512);seed_legacy(*state,record+2148);state->addr.fs_base.dword=r.fs_base().value;state->addr.ds_base.dword=0;state->addr.ss_base.dword=0;
  std::array<std::byte,Runtime::remill_state_bytes>opaque{};std::copy(r.remill_state().begin(),r.remill_state().end(),opaque.begin());r.mark_remill_seeded();
  r.freeze_registry();const Slots slots;const auto slot=c<6?slots.initterm:c==6?slots.set_app_type:c==7?slots.p_fmode:slots.p_commode;r.call_import(slot,GuestAddress{sentinel});need(!r.poisoned()&&r.calls().front().completed,"Native service complete without required fault");need(std::equal(opaque.begin(),opaque.end(),r.remill_state().begin()),"Full opaque State preservation");memory(r,after.data());const auto cpu=projection(r.cpu());
  const auto env=legacy_capture(*state,record+2148);out.write(tag,sizeof(tag));out.write(&before,40);out.write(&cpu,40);out.write(record+100,512);out.write(r.fx().data(),512);out.write(record+2148,28);out.write(env.data(),28);out.write(record+2260,memory_bytes);out.write(after.data(),after.size());
  if(ordinal)events<<',';events<<"{\"ordinal\":"<<ordinal<<",\"case\":"<<c<<",\"opaque_bytes_unchanged\":3504,\"visits\":[";bool comma=false;for(const auto &v:s.visits()){if(comma)events<<',';comma=true;events<<"{\"slot\":"<<v.slot.value<<",\"target\":"<<v.target.value<<",\"status\":"<<unsigned(v.status)<<'}';}events<<"],\"calls\":[";comma=false;for(const auto &call:r.calls()){if(comma)events<<',';comma=true;events<<"{\"site\":"<<call.site.value<<",\"target\":"<<call.target.value<<",\"return\":"<<call.return_pc.value<<",\"completed\":"<<(call.completed?"true":"false")<<'}';}events<<"]}";
 }
 events<<"]}\n";const auto text=events.str();ledger.write(text.data(),text.size());ledger.commit();out.commit();std::cout<<"1728 independent native CRT outputs captured from original before fields only\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
