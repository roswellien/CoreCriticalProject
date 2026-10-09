#include "guest_cw.hpp"
#include <cstring>
namespace mw34::m4_guest_cw {
static_assert(sizeof(State)==3504);
Context::Context(GuestMemory &m,State &s,std::span<std::byte,512> f,GuestAddress b,std::uint32_t n):memory_(m),state_(s),fx_(f),begin_(b),bytes_(n){
 if(n<2||std::uint64_t{b.value}+n>GuestMemory::address_space_size)throw std::invalid_argument("Checked nonwrapping CW operand span required");
}
bool Context::deny(Fault f,GuestAddress a)noexcept{if(fault_==Fault::none){fault_=f;fault_address_=a;}return false;}
bool Context::admit(State*s,GuestAddress a)noexcept{
 if(fault_!=Fault::none)return false;
 if(s!=&state_)return deny(Fault::wrong_state,a);
 std::uint16_t cw{},sw{};std::uint32_t mx{};std::memcpy(&cw,fx_.data(),2);std::memcpy(&sw,fx_.data()+2,2);std::memcpy(&mx,fx_.data()+24,4);
 const auto &f=state_.x87.fxsave;const auto &status=state_.sw;
 if(f.cwd.flat!=cw||normalized(cw)!=cw||f.swd.flat||sw||f.ftw.flat||fx_[4]!=std::byte{0}||mx!=0x1f80||f.mxcsr.flat!=0x1f80||status.ie||status.de||status.ze||status.oe||status.ue||status.pe||status.sf||status.c0||status.c1||status.c2||status.c3)return deny(Fault::unsupported_state,a);
 if(a.value<begin_.value||std::uint64_t{a.value}+2>std::uint64_t{begin_.value}+bytes_)return deny(Fault::operand_bounds,a);
 return true;
}
bool Context::store(State*s,GuestAddress a)noexcept{
 if(!admit(s,a))return false;
 try{memory_.store<std::uint16_t>(a,state_.x87.fxsave.cwd.flat);return true;}catch(...){return deny(Fault::memory_access,a);}
}
bool Context::load(State*s,GuestAddress a)noexcept{
 if(!admit(s,a))return false;
 try{const auto cw=normalized(memory_.load<std::uint16_t>(a));state_.x87.fxsave.cwd.flat=cw;std::memcpy(fx_.data(),&cw,2);return true;}catch(...){return deny(Fault::memory_access,a);}
}
}
extern "C" void *mw34_m4_guest_fnstcw(State*s,std::uint32_t a,void*p)noexcept{if(p)(void)static_cast<mw34::m4_guest_cw::Context*>(p)->store(s,mw34::GuestAddress{a});return p;}
extern "C" void *mw34_m4_guest_fldcw(State*s,std::uint32_t a,void*p)noexcept{if(p)(void)static_cast<mw34::m4_guest_cw::Context*>(p)->load(s,mw34::GuestAddress{a});return p;}
