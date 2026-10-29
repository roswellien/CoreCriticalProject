#include "crt_services.hpp"
#include "service_provider.hpp"
#include <bit>
#include <map>

namespace mw34::m4_crt {
void compiled_initterm(m4_runtime::Runtime&);
namespace {
thread_local std::map<Runtime*,Session*> owners;
constexpr auto provider_hash="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7";
bool hash(const std::string &s){return s.size()==64&&std::all_of(s.begin(),s.end(),[](char c){return(c>='0'&&c<='9')||(c>='a'&&c<='f');});}
std::uint32_t common(std::uint32_t result){return ((std::popcount(result&255U)&1)?0U:4U)|(result==0?0x40U:0U)|(result&0x80000000U?0x80U:0U);}
std::uint32_t cmp_flags(std::uint32_t left,std::uint32_t right,std::uint32_t old){
    const auto result=left-right;
    return (old&~0xcd5U)|common(result)|(left<right?1U:0U)|((left^right^result)&0x10U)|(((left^right)&(left^result)&0x80000000U)?0x800U:0U);
}
std::uint32_t add_flags(std::uint32_t left,std::uint32_t right,std::uint32_t old){
    const auto result=left+right;
    return (old&~0xcd5U)|common(result)|(std::uint64_t{left}+right>0xffffffffULL?1U:0U)|((left^right^result)&0x10U)|((~(left^right)&(left^result)&0x80000000U)?0x800U:0U);
}
void require(bool ok,const char *why){if(!ok)throw std::invalid_argument(why);}
}
Session::Session(Runtime &r,std::span<const std::byte> provider,const Proof &proof,const Slots &slots):runtime_(r),slots_(slots){
    require(r.domain()==proof.domain&&!r.registry_frozen()&&!owners.contains(&r),"CRT session owner/domain/unfrozen registry required");
    require(proof.domain!=Domain::admitted_game||(hash(proof.native_artifact_sha256)&&hash(proof.gate_report_sha256)),"Actual CRT callbacks require measured static artifact and independent gate bindings");
    // Validate all four exact source bodies before publishing any state.
    struct Body {std::uint32_t entry,size;const char *sha;GuestAddress slot;const char *name;NativeEntry callback;std::uint32_t args;};
    const std::array<Body,4> bodies{{
        {0x780014f8,28,"960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678",slots.initterm,"_initterm",compiled_initterm,8},
        {0x78004625,10,"9b66387e70a4c7ae6a23115f73296e1b72fac54610ee6db3966b843ac9dafbef",slots.set_app_type,"__set_app_type",set_app_type,4},
        {0x7800462f,6,"eb5afece8f5f8fe130abe78bd2cfbc4c94f0f86caf8621da8a7ad51a9e26e578",slots.p_fmode,"__p__fmode",p_fmode,0},
        {0x78004635,6,"9d67fcd948d000a76431acfa77f662559957af257c435e5f9d229c365d7ad7e4",slots.p_commode,"__p__commode",p_commode,0}}};
    for(const auto &b:bodies){
        require(m4::sha256(staged_crt_code(provider,GuestAddress{b.entry},b.size))==b.sha,"Exact measured CRT source body required");
        const auto &imports=r.image_metadata().imports;
        require(std::count_if(imports.begin(),imports.end(),[&](const auto&i){return std::uint64_t{r.image_metadata().image_base}+i.iat_rva==b.slot.value&&i.name&&*i.name==b.name;})==1,"CRT callback requires exact real named import slot");
    }
    require(r.service_count()==0&&r.service_continuation_count()==0,"CRT startup session must be the first service provider; no partial/duplicate registration reuse");
    // Exact provider source globals are three zero DWORDs in the recovered RW
    // section. Explicit preferred guest addresses, no host pointer allocation.
    r.memory().map(GuestAddress{provider_app_type},12,Permissions::read|Permissions::write);owns_globals_=true;
    try {
        ServiceContinuation c;c.code_start=GuestAddress{0x780014f8};c.call_pc=GuestAddress{0x7800150e};c.return_pc=GuestAddress{0x78001510};c.service_iat_slot=slots.initterm;c.source_bytes=28;c.domain=proof.domain;c.provider_sha256=provider_hash;c.source_sha256=bodies[0].sha;c.native_artifact_sha256=proof.native_artifact_sha256;c.gate_report_sha256=proof.gate_report_sha256;c.name="_initterm";
        // First-null gate admits no callback continuation; complete provider source is owned by its literal full page.
        for(const auto &b:bodies)r.register_service({b.slot,{Abi::Cdecl,b.args,true},b.callback,b.name,proof.domain,provider_hash,proof.gate_report_sha256});
        owners.emplace(&r,this);
    } catch(...) {r.memory().unmap(GuestAddress{provider_app_type});owns_globals_=false;throw;}
}
Session::~Session(){owners.erase(&runtime_);if(owns_globals_)runtime_.memory().unmap(GuestAddress{provider_app_type});}
Session&Session::owner(Runtime&r){const auto it=owners.find(&r);if(it==owners.end())throw std::runtime_error("CRT service has no live session on its owning host thread");return *it->second;}
void Session::set_app_type(Runtime&r){(void)owner(r);r.cpu().eax=r.memory().load<std::uint32_t>(GuestAddress{r.cpu().esp+4});r.memory().store<std::uint32_t>(GuestAddress{provider_app_type},r.cpu().eax);r.ret();}
void Session::p_fmode(Runtime&r){(void)owner(r);r.cpu().eax=provider_fmode;r.ret();}
void Session::p_commode(Runtime&r){(void)owner(r);r.cpu().eax=provider_commode;r.ret();}
void Session::initterm(Runtime&r){
    auto &session=owner(r);auto &cpu=r.cpu();
    const auto saved_esi=cpu.esi;
    require(cpu.esp>=r.stack_low().value+4,"CRT ESI push exceeds owned guest stack");
    cpu.esp-=4;r.memory().store<std::uint32_t>(GuestAddress{cpu.esp},saved_esi);
    cpu.esi=r.memory().load<std::uint32_t>(GuestAddress{cpu.esp+8});
    const auto initial_end=r.memory().load<std::uint32_t>(GuestAddress{cpu.esp+12});
    require(!(cpu.esi&3)&&!(initial_end&3)&&(cpu.esi>=initial_end||std::uint64_t{initial_end}-cpu.esi<=4ULL*max_initializer_visits),"Bounded aligned CRT initializer interval required");
    unsigned count{};
    for(;;){
        // Original CMP rereads the end argument every iteration. Future slots
        // are read when reached, not frozen/guessed or skipped as unknown.
        const auto end=r.memory().load<std::uint32_t>(GuestAddress{cpu.esp+12});
        cpu.eflags=cmp_flags(cpu.esi,end,cpu.eflags);
        if(cpu.esi>=end)break;
        require(!(end&3)&&count++<max_initializer_visits,"CRT initializer bound changed/exceeded");
        cpu.eax=r.memory().load<std::uint32_t>(GuestAddress{cpu.esi});
        // TEST defines CF/PF/ZF/SF/OF; AF is undefined until the next ADD/CMP.
        cpu.eflags=(cpu.eflags&~0x8c5U)|common(cpu.eax);
        session.visits_.push_back({GuestAddress{cpu.esi},GuestAddress{cpu.eax},cpu.eax?VisitStatus::attempted:VisitStatus::null_slot,{}});
        const auto visit_index=session.visits_.size()-1;
        if(cpu.eax){
            cpu.eip=0x7800150e;
            try {r.call_direct(GuestAddress{cpu.eax},GuestAddress{0x78001510});session.visits_[visit_index].status=VisitStatus::completed;}
            catch(const std::exception &error){session.visits_[visit_index].status=VisitStatus::fault;session.visits_[visit_index].failure=error.what();throw;}
        }
        const auto prior=cpu.esi;cpu.esi+=4;cpu.eflags=add_flags(prior,4,cpu.eflags);
    }
    cpu.esi=r.memory().load<std::uint32_t>(GuestAddress{cpu.esp});cpu.esp+=4;r.ret();
}
} // namespace mw34::m4_crt
