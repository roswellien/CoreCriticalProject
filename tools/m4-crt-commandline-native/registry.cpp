#include "registry.hpp"
#include "spec.hpp"
namespace mw34::m4_cmd_native {
extern "C" void*mw34_cmd_writer(State*,std::uint32_t,void*);
constexpr std::array<GuestAddress,3>pages{{GuestAddress{0x78001000},GuestAddress{0x7802e000},GuestAddress{0x78037000}}};
static std::uint32_t word(std::span<const std::byte>b,unsigned o){require(o+4<=b.size(),"Pack word bounds");std::uint32_t v{};for(unsigned i=0;i<4;++i)v|=std::to_integer<unsigned>(b[o+i])<<(8*i);return v;}
Registry::~Registry(){cleanup();}
void Registry::fault(FaultReason r,GuestAddress at,const char*why)noexcept{if(!fault_)fault_=Fault{r,at,why};ready_=false;active_=false;}
void Registry::cleanup()noexcept{
    if(owns_buffer_){try{runtime_.memory().unmap(buffer_);}catch(...){}owns_buffer_=false;}
    for(unsigned i=3;i-->0;)if(owns_pages_[i]){try{runtime_.memory().unmap(pages[i]);}catch(...){}owns_pages_[i]=false;}
}
const m4::ImportSymbol&Registry::game_owner()const{
    require(runtime_.domain()==m4_runtime::Domain::admitted_game&&runtime_.image_metadata().image_base==0x400000,"Actual admitted game metadata required");const m4::ImportSymbol*found{};
    for(const auto&i:runtime_.image_metadata().imports)if(std::uint64_t(runtime_.image_metadata().image_base)+i.iat_rva==game_iat.value){require(!found&&i.name&&*i.name=="_acmdln"&&library(i.library,"msvcrt.dll"),"Unique real MSVCRT _acmdln owner required");found=&i;}require(found,"Actual named data IAT missing");return *found;
}
bool Registry::admit(std::span<const std::byte>file,std::span<const std::byte>pack)noexcept{
    if(fault_)return false;
    try{require(!admitted_&&!entered_,"Provider registry admits once");Provider provider(file);const auto&owner=game_owner();game_word_=owner.original_iat_value;require(runtime_.memory().load<std::uint32_t>(game_iat)==game_word_,"Original game data IAT changed");provider_word_=provider.dword(provider_iat);
        require(pack.size()==12324&&m4::sha256(pack)==pack_sha&&std::memcmp(pack.data(),"MW4CNPK1",8)==0&&word(pack,8)==3,"Exact private writer/capture pack required");
        const std::array<std::uint32_t,3>permissions{5,1,3};
        for(unsigned i=0;i<3;++i){auto o=12+i*4104;require(word(pack,o)==pages[i].value&&word(pack,o+4)==permissions[i],"Exact provider page ownership contract");original_pages_[i]={pack.begin()+o+8,pack.begin()+o+4104};}
        auto code=provider.slice(writer,11,0x60000000);require(std::equal(code.begin(),code.end(),original_pages_[0].begin()+0x88c),"Actual original CALL/MOV bytes required");
        require(original_pages_[1]==provider.slice(pages[1],4096,0x40000000)&&original_pages_[2]==provider.slice(pages[2],4096,0xc0000000),"Exact original provider IAT/RW sources required");
        for(unsigned i=0;i<3;++i){runtime_.memory().map(pages[i],4096,Permissions::read|Permissions::write);owns_pages_[i]=true;runtime_.memory().write(pages[i],original_pages_[i]);runtime_.memory().protect(pages[i],i==0?Permissions::read|Permissions::execute:i==1?Permissions::read:Permissions::read|Permissions::write);}
        admitted_=true;integrity(false);return true;
    }catch(const MemoryFault&){fault(FaultReason::memory,provider_global,"Required provider ownership/admission memory fault");}catch(...){fault(FaultReason::invalid_admission,writer,"Exact provider/pack/game owner admission rejected");}cleanup();return false;
}
void Registry::integrity(bool initialized){
    require(admitted_&&owns_pages_[0]&&owns_pages_[1]&&owns_pages_[2],"Owned provider mappings incomplete");const auto&owner=game_owner();require(owner.original_iat_value==game_word_&&runtime_.memory().load<std::uint32_t>(game_iat)==game_word_&&runtime_.memory().load<std::uint32_t>(provider_iat)==provider_word_,"Raw game/provider IAT identity changed");
    std::array<std::byte,4096>code{},imports{};runtime_.memory().read(pages[0],code);runtime_.memory().read(pages[1],imports);require(std::equal(code.begin(),code.end(),original_pages_[0].begin())&&std::equal(imports.begin(),imports.end(),original_pages_[1].begin()),"Actual writer/capture/IAT page identity changed");
    if(initialized){require(service_called_&&global_written_&&owns_buffer_&&buffer_==buffer_start&&!host_.bytes.empty()&&host_.bytes.size()<=131072&&host_.bytes.back()==std::byte{}&&runtime_.memory().load<std::uint32_t>(provider_global)==buffer_.value,"Actual initialized global/owned buffer incomplete or changed");std::vector<std::byte>v(host_.bytes.size());runtime_.memory().read(buffer_,v);require(v==host_.bytes,"Live actual host snapshot buffer changed");}
    else require(runtime_.memory().load<std::uint32_t>(provider_global)==0,"Uninitialized source global changed");
}
void Registry::log(unsigned pc,unsigned a,unsigned value,unsigned width,unsigned op){require(events_.size()<32,"Actual compiled/adapter event capacity");events_.push_back({pc,a,value,width,op});}
bool Registry::initialize(State&s)noexcept{
    if(fault_)return false;
    try{require(admitted_&&!entered_&&!active_&&!ready_,"Fresh admitted writer required");entered_=true;state_=&s;outer_esp_=s.gpr.rsp.dword;require(s.gpr.rip.dword==writer.value&&outer_esp_==0x20001800&&!s.aflag.df&&!s.addr.ds_base.dword&&!s.addr.ss_base.dword,"Exact writer State/frame/flat DF0 domain required");integrity(false);nonvolatile_={s.gpr.rbx.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword};active_=true;
        {const auto returned=mw34_cmd_writer(&s,writer.value,this);if(returned!=this||!captured_||fault_)throw std::invalid_argument("Incomplete actual compiled writer/capture");}
        if(fault_){cleanup();return false;}integrity(true);ready_=true;active_=false;return true;
    }catch(const MemoryFault&){fault(FaultReason::memory,writer,"Required writer-entry memory fault");}catch(...){fault(FaultReason::partial_writer,writer,"Writer initialization did not complete exact source/capture contract");}cleanup();return false;
}
std::uint32_t Registry::compiled_read32(std::uint32_t a)noexcept{
    if(fault_)return 0;
    try{require(active_&&state_&&state_->gpr.rip.dword==writer.value&&a==provider_iat.value&&!service_called_,"Only exact actual writer IAT read admitted");integrity(false);auto raw=runtime_.memory().load<std::uint32_t>({a});log(writer.value,a,raw,4,0);require(raw==provider_word_,"Provider import lookup bytes changed");return service_gate.value;}
    catch(const MemoryFault&){fault(FaultReason::memory,{a},"Required actual compiled read fault");}catch(...){fault(FaultReason::import_owner,{a},"Actual provider import/source/route read rejected");}return 0;
}
bool Registry::compiled_write32(std::uint32_t a,std::uint32_t v)noexcept{
    if(fault_)return false;
    try{require(active_&&state_,"Actual writer write has no active State");auto pc=state_->gpr.rip.dword;
        if(!service_called_){require(pc==writer.value&&a==outer_esp_-4&&v==return_pc.value,"Exact actual compiled CALL return-frame store required");}
        else require(!global_written_&&pc==return_pc.value&&a==provider_global.value&&owns_buffer_&&v==buffer_.value,"Only actual post-service global writer store admitted");
        runtime_.memory().store<std::uint32_t>({a},v);log(pc,a,v,4,1);if(service_called_)global_written_=true;return true;
    }catch(const MemoryFault&){fault(FaultReason::memory,{a},"Required actual compiled store fault");}catch(...){fault(FaultReason::partial_writer,{a},"Actual CALL/global writer store rejected");}return false;
}
bool Registry::compiled_service(State*s,std::uint32_t target)noexcept{
    if(fault_)return false;
    try{require(active_&&s==state_&&target==service_gate.value&&s->gpr.rip.dword==target&&!service_called_&&s->gpr.rsp.dword==outer_esp_-4,"Exact active actual compiled provider-import call required");integrity(false);auto ret=runtime_.memory().load<std::uint32_t>({outer_esp_-4});log(writer.value,outer_esp_-4,ret,4,0);require(ret==return_pc.value,"Actual service continuation stack word changed");route_={target,ret,s->gpr.rsp.dword,0,false};
        service_before_=*s;__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(sf_before_),"=m"(se_before_)::"memory");
        host_=own_host_input();
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(sf_after_),"=m"(se_after_)::"memory");
        buffer_=buffer_start;runtime_.memory().map(buffer_,host_.bytes.size(),Permissions::read|Permissions::write);owns_buffer_=true;runtime_.memory().write(buffer_,host_.bytes);log(writer.value,buffer_.value,0,static_cast<unsigned>(host_.bytes.size()),2);runtime_.memory().protect(buffer_,Permissions::read);
        service_called_=true;s->gpr.rax.dword=buffer_.value;s->gpr.rsp.dword+=4;s->gpr.rip.dword=ret;route_.exit_esp=s->gpr.rsp.dword;route_.completed=true;service_after_=*s;return true;
    }catch(const MemoryFault&){fault(FaultReason::memory,provider_iat,"Required actual service frame/buffer ownership fault");}catch(...){fault(FaultReason::host_input,provider_iat,"Exact native host snapshot/import continuation rejected");}return false;
}
bool Registry::compiled_capture(State*s,std::uint32_t target)noexcept{
    if(fault_)return false;
    try{require(active_&&s==state_&&target==capture_gate.value&&s->gpr.rip.dword==target&&s->gpr.rsp.dword==outer_esp_&&service_called_&&global_written_&&route_.completed,"Only declared authored outer capture after actual source stores admitted");require(std::array<std::uint32_t,4>{s->gpr.rbx.dword,s->gpr.rbp.dword,s->gpr.rsi.dword,s->gpr.rdi.dword}==nonvolatile_,"Writer/service nonvolatile registers changed");integrity(true);captured_=true;return true;}
    catch(const MemoryFault&){fault(FaultReason::memory,provider_global,"Actual capture/global integrity memory fault");}catch(...){fault(FaultReason::partial_writer,capture_gate,"Declared outer capture rejected actual writer state");}return false;
}
std::optional<GuestAddress>Registry::resolve_data(GuestAddress slot)noexcept{
    if(fault_)return std::nullopt;
    try{require(slot==game_iat&&ready_&&captured_,"Only ready actual _acmdln data import admitted");integrity(true);return provider_global;}
    catch(const MemoryFault&){fault(FaultReason::memory,slot,"Required native data/global/buffer access fault");}catch(...){fault(FaultReason::unresolved_data,slot,"Actual initialized command-line data route rejected");}cleanup();return std::nullopt;
}
struct BridgeAbort{};
[[noreturn]]void Registry::abort_bridge(){if(!fault_)fault(FaultReason::partial_writer,writer,"Compiled helper aborted without recorded completion");throw BridgeAbort{};}
}
extern "C" std::uint32_t __remill_read_memory_32(void*p,std::uint32_t a){auto*c=static_cast<mw34::m4_cmd_native::Registry*>(p);auto v=c->compiled_read32(a);if(c->first_fault())c->abort_bridge();return v;}
extern "C" void*__remill_write_memory_32(void*p,std::uint32_t a,std::uint32_t v){auto*c=static_cast<mw34::m4_cmd_native::Registry*>(p);if(!c->compiled_write32(a,v))c->abort_bridge();return p;}
extern "C" void*__remill_function_call(State*s,std::uint32_t target,void*p){auto*c=static_cast<mw34::m4_cmd_native::Registry*>(p);if(!c->compiled_service(s,target))c->abort_bridge();return p;}
extern "C" void*mw34_cmd_outer_capture(State*s,std::uint32_t target,void*p){auto*c=static_cast<mw34::m4_cmd_native::Registry*>(p);if(!c->compiled_capture(s,target))c->abort_bridge();return p;}
