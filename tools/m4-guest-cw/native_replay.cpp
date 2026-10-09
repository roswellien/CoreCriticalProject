// Actual hardware BEFORE fields only; no observed CW or after-state oracle.
#include "guest_cw.hpp"
#include "probe_io.hpp"
#include <iostream>
using namespace mw34;
using namespace mw34::m4_guest_cw;
using namespace mw34::m4_crt_probe;
namespace {
std::uint16_t w(const std::uint8_t*p){std::uint16_t v{};std::memcpy(&v,p,2);return v;}
std::uint32_t d(const std::uint8_t*p){std::uint32_t v{};std::memcpy(&v,p,4);return v;}
std::array<std::uint8_t,28>legacy(const State&s,const std::uint8_t*reserved){auto &f=s.x87.fxsave;std::array<std::uint8_t,28>e{};std::memcpy(e.data(),reserved,28);put16(e.data(),f.cwd.flat);put16(e.data()+4,f.swd.flat);need(f.ftw.flat==0,"Measured empty physical tags");put16(e.data()+8,0xffff);put32(e.data()+12,f.ip);put16(e.data()+16,f.cs.flat);put16(e.data()+18,f.fop);put32(e.data()+20,f.dp);put16(e.data()+24,f.ds.flat);return e;}
}
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 need(argc==3,"Guest CW replay: exact-hardware-prestates fresh-output");const auto input=read(argv[1],285212696);need(input.size()==285212696&&digest(input)=="a31f18e7960db0caba66c63cfd949ba776e08b33564f17d7a0bd2918574801b4","Exact hardware input identity rejected");need(std::memcmp(input.data(),"MW4CW001",8)==0,"Hardware input version rejected");const std::uint32_t expected[]{1,131072,2176,65536};need(std::memcmp(input.data()+8,expected,16)==0,"Hardware input header rejected");
 GuestMemory memory;memory.map(GuestAddress{0x2000},8,Permissions::read|Permissions::write);State state{};auto *raw_state=reinterpret_cast<std::byte*>(&state);for(unsigned i=0;i<3504;++i)raw_state[i]=std::byte(static_cast<std::uint8_t>(i*13+7));std::memset(&state.sw,0,sizeof(state.sw));std::memcpy(&state.x87,input.data()+24+16,512);auto &f=state.x87.fxsave;const auto *initial_env=input.data()+24+2064;f.ip=d(initial_env+12);f.cs.flat=w(initial_env+16);f.fop=w(initial_env+18);f.dp=d(initial_env+20);f.ds.flat=w(initial_env+24);state.addr.fs_base.dword=0x7ffde000;state.addr.ds_base.dword=state.addr.ss_base.dword=0;
 std::array<std::byte,512>fx{};std::memcpy(fx.data(),input.data()+24+16,512);Context context(memory,state,fx,GuestAddress{0x2000},8);const auto cw_offset=static_cast<std::uint32_t>(reinterpret_cast<std::byte*>(&f.cwd.flat)-raw_state);Output output(argv[2]);output.write("MW4GCW01",8);const std::uint32_t header[]{1,65536,8120,cw_offset};output.write(header,sizeof(header));
 for(unsigned i=0;i<65536;++i){
  const auto *record=input.data()+24+i*2176;need(d(record)==0&&d(record+4)==i&&d(record+12)==0,"Actual requested input tag/status");
  // Same measured entry CW for every independent input. No hidden State or
  // metadata reseeding after the first record; all other bytes must persist.
  need(std::memcmp(fx.data()+2,record+18,510)==0,"Persistent non-CW physical input");f.cwd.flat=w(record+16);std::memcpy(fx.data(),record+16,2);const auto env_before=legacy(state,record+2064);need(std::memcmp(env_before.data(),record+2064,28)==0,"Persistent actual legacy input");
  memory.store<std::uint64_t>(GuestAddress{0x2000},0xffeeddcc0000bbaaULL);memory.store<std::uint16_t>(GuestAddress{0x2002},static_cast<std::uint16_t>(i));std::array<std::byte,8>mb{},ma{};memory.read(GuestAddress{0x2000},mb);std::array<std::byte,3504>before{};std::memcpy(before.data(),&state,3504);const auto fx_before=fx;
  need(mw34_m4_guest_fldcw(&state,0x2002,&context)==&context&&context.fault()==Fault::none,"Typed load required fault");need(mw34_m4_guest_fnstcw(&state,0x2004,&context)==&context&&context.fault()==Fault::none,"Typed store required fault");memory.read(GuestAddress{0x2000},ma);const auto env_after=legacy(state,record+2064);
  auto allowed=before;std::memcpy(allowed.data()+cw_offset,&f.cwd.flat,2);need(std::memcmp(allowed.data(),&state,3504)==0,"Complete State except2 CW bytes preserved");auto allowed_fx=fx_before;std::memcpy(allowed_fx.data(),&f.cwd.flat,2);need(allowed_fx==fx,"Separate FX except CW preserved");
  const std::uint32_t tag[]{0,i,memory.load<std::uint16_t>(GuestAddress{0x2004}),0};output.write(tag,sizeof(tag));output.write(before.data(),3504);output.write(&state,3504);output.write(fx_before.data(),512);output.write(fx.data(),512);output.write(env_before.data(),28);output.write(env_after.data(),28);output.write(mb.data(),8);output.write(ma.data(),8);
 }
 output.commit();std::cout<<"65536 actual native guest CW outputs; numerical/provider integration pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
