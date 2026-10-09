#include "guest_cw.hpp"
#include <cstring>
#include <iostream>
using namespace mw34;
using namespace mw34::m4_guest_cw;
namespace {
unsigned checks{};
void check(bool b,const char*why){if(!b)throw std::runtime_error(why);++checks;}
struct Fixture {
 GuestMemory memory;State state{};std::array<std::byte,512>fx{};
 Fixture(){std::memset(&state,0,sizeof(state));memory.map(GuestAddress{0x2000},8,Permissions::read|Permissions::write);state.x87.fxsave.cwd.flat=0x37f;state.x87.fxsave.mxcsr.flat=0x1f80;std::memcpy(fx.data(),&state.x87,512);}
 Context context(){return Context(memory,state,fx,GuestAddress{0x2000},8);}
};
void tests(){
 {Fixture f;auto c=f.context();f.memory.store<std::uint64_t>(GuestAddress{0x2000},0xaabbccddeeff0011ULL);check(c.store(&f.state,GuestAddress{0x2002}),"Checked16-bit CW store");check(f.memory.load<std::uint64_t>(GuestAddress{0x2000})==0xaabbccdd037f0011ULL,"Exactly2 bytes written");}
 {Fixture f;auto c=f.context();auto before=f.state;auto fx=f.fx;f.memory.store<std::uint16_t>(GuestAddress{0x2002},0xffff);check(c.load(&f.state,GuestAddress{0x2002}),"Actual measured all-bit load");before.x87.fxsave.cwd.flat=0x1f7f;std::uint16_t cw=0x1f7f;std::memcpy(fx.data(),&cw,2);check(std::memcmp(&before,&f.state,3504)==0&&fx==f.fx,"Only State+FX CW bytes change");check(c.store(&f.state,GuestAddress{0x2004})&&f.memory.load<std::uint16_t>(GuestAddress{0x2004})==0x1f7f,"Stored loaded guestCW retains53/64 PC");}
 {Fixture f;auto c=f.context();auto before=f.state;auto fx=f.fx;State wrong{};check(!c.load(&wrong,GuestAddress{0x2000})&&c.fault()==Fault::wrong_state,"Wrong persistent State denied");check(!c.store(&f.state,GuestAddress{0x2000})&&std::memcmp(&before,&f.state,3504)==0&&fx==f.fx,"Required fault cannot become successful retry");}
 for(unsigned kind=0;kind<7;++kind){Fixture f;auto c=f.context();if(kind==0)f.state.x87.fxsave.swd.flat=1;if(kind==1)f.state.x87.fxsave.swd.flat=0x800;if(kind==2)f.state.x87.fxsave.ftw.flat=1;if(kind==3)f.state.sw.pe=1;if(kind==4)f.fx[4]=std::byte{1};if(kind==5)f.state.x87.fxsave.cwd.flat=0x27f;if(kind==6)f.fx[24]=std::byte{0};auto before=f.state;check(!c.store(&f.state,GuestAddress{0x2000})&&c.fault()==Fault::unsupported_state,"Pending/TOP/nonempty/shadow/mismatch domain denied");check(std::memcmp(&before,&f.state,3504)==0,"Denied domain never reset to convenience state");}
 {Fixture f;auto c=f.context();check(!c.store(&f.state,GuestAddress{0x2007})&&c.fault()==Fault::operand_bounds,"Cross-owned-end2byte store denied");}
 {Fixture f;auto c=f.context();f.memory.protect(GuestAddress{0x2000},Permissions::read);check(!c.store(&f.state,GuestAddress{0x2000})&&c.fault()==Fault::memory_access,"Readonly required memory fault retained");}
 {Fixture f;auto c=f.context();f.memory.unmap(GuestAddress{0x2000});auto before=f.state;check(!c.load(&f.state,GuestAddress{0x2000})&&c.fault()==Fault::memory_access&&std::memcmp(&before,&f.state,3504)==0,"Unmapped load never updatesState");}
 {Fixture f;auto c=f.context();auto before=f.state;auto fx=f.fx;f.memory.protect(GuestAddress{0x2000},Permissions::write);check(!c.load(&f.state,GuestAddress{0x2000})&&c.fault()==Fault::memory_access&&std::memcmp(&before,&f.state,3504)==0&&fx==f.fx,"Unreadable load retains completeState+FX");}
 {Fixture f;bool short_span=false,wrapped=false;try{Context c(f.memory,f.state,f.fx,GuestAddress{0x2000},1);}catch(const std::invalid_argument&){short_span=true;}try{Context c(f.memory,f.state,f.fx,GuestAddress{0xffffffff},2);}catch(const std::invalid_argument&){wrapped=true;}check(short_span&&wrapped,"Short and wrapped owned spans rejected before transfer");}
 {Fixture f;auto c=f.context();f.memory.store<std::uint16_t>(GuestAddress{0x2000},0x27f);check(mw34_m4_guest_fldcw(&f.state,0x2000,&c)==&c&&c.fault()==Fault::none&&f.state.x87.fxsave.cwd.flat==0x27f,"Normal integer/pointer C ABI load");check(mw34_m4_guest_fnstcw(&f.state,0x2002,&c)==&c&&f.memory.load<std::uint16_t>(GuestAddress{0x2002})==0x27f,"Normal C ABI store53-bit PC");}
}
}
int main(){try{tests();std::cout<<checks<<" authored guest CW controls passed; numerical/provider integration pending\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
