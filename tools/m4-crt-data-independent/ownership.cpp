#include "data_imports.hpp"
#include "admission.hpp"
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
using namespace mw34;
using mw34::m4_runtime::Runtime;
namespace cd=mw34::m4_crt_data;
namespace {
unsigned checks{}, scenarios{};
std::vector<std::byte> provider,game,raw,measured;
std::uint32_t original_pointer{};
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);++checks;}
std::vector<std::byte> read(const char*path){std::ifstream f(path,std::ios::binary|std::ios::ate);check(bool(f),"input readable");auto n=f.tellg();check(n>0&&n<64*1024*1024,"input bounded");std::vector<std::byte>b(static_cast<std::size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),n);check(bool(f),"input complete");return b;}
std::uint32_t word(std::span<const std::byte>b,std::size_t off){check(off+4<=b.size(),"word bounds");std::uint32_t x{};for(unsigned i=0;i<4;++i)x|=std::to_integer<std::uint32_t>(b[off+i])<<(8*i);return x;}
mw34::m4_runtime::Policy policy(){mw34::m4_runtime::Policy p;p.stack_bytes=p.heap_bytes=8192;return p;}
cd::ReferenceProjection projection(std::uint32_t address=0x32000000,std::size_t size=0){auto b=measured;if(size){b.assign(size,std::byte{'Q'});b.back()=std::byte{};}return {original_pointer,GuestAddress{address},b,"2a9ed0395eaba271b317797525d699de3dd099be8f80a91921059637f546863f",m4::sha256(b)};}
struct Snapshot {
    mw34::m4_runtime::Cpu32 cpu;
    std::array<std::byte,512>fx;
    std::array<std::byte,3504>state;
    explicit Snapshot(Runtime&r):cpu(r.cpu()){std::copy(r.fx().begin(),r.fx().end(),fx.begin());std::copy(r.remill_state().begin(),r.remill_state().end(),state.begin());}
    void unchanged(Runtime&r){check(std::memcmp(&cpu,&r.cpu(),sizeof(cpu))==0,"data API preserves CPU");check(std::equal(fx.begin(),fx.end(),r.fx().begin()),"data API preserves FX");check(std::equal(state.begin(),state.end(),r.remill_state().begin()),"data API preserves complete State");}
};
void seed(Runtime&r){auto&c=r.cpu();c.eax=0xdeadbeef;c.ecx=0x12345678;c.edx=0x87654321;c.ebx=0x31415926;c.eflags=0x246;c.eip=0x401000;for(unsigned i=0;i<512;++i)r.fx()[i]=static_cast<std::byte>((i*11+9)&255);for(unsigned i=0;i<3504;++i)r.remill_state()[i]=static_cast<std::byte>((i*17+3)&255);}
bool absent(Runtime&r,GuestAddress a){try{(void)r.memory().load<std::uint8_t>(a);}catch(const MemoryFault&f){return f.reason()==MemoryFaultReason::unmapped;}return false;}
template<class F>void reject(cd::DataImportRegistry&d,F fn,cd::DataFaultReason why){try{fn();}catch(const cd::DataFault&f){check(f.reason==why,"expected typed reason");check(d.poisoned()&&d.first_fault().has_value(),"fault retained");check(d.first_fault()->reason==f.reason&&d.first_fault()->address==f.address&&std::string(d.first_fault()->what())==f.what(),"first fault exact");return;}throw std::runtime_error("required denial accepted");}
void reuse(cd::DataImportRegistry&d,cd::DataFaultReason why){auto first=*d.first_fault();reject(d,[&]{(void)d.resolve_reference_load32(GuestAddress{0x5bb518});},why);reject(d,[&]{d.admit_reference_projection(provider,projection());},why);check(first.address==d.first_fault()->address&&std::string(first.what())==d.first_fault()->what(),"no replacement of first fault");}
m4::LoadedImage fixture(unsigned which){m4::LoadedImage x;x.metadata.image_base=0x400000;x.metadata.entry_point=GuestAddress{0x401000};x.memory.map(GuestAddress{0x401000},4096,Permissions::read|Permissions::execute);x.metadata.mapped_regions={{"independent fixture",GuestAddress{0x401000},4096,Permissions::read|Permissions::execute}};x.memory.map(GuestAddress{0x5bb000},4096,Permissions::read|Permissions::write);for(auto [address,name]:std::array<std::pair<unsigned,const char*>,2>{{{0x5bb518,"_acmdln"},{0x5bb508,"_adjust_fdiv"}}}){m4::ImportSymbol i;i.library=which==0?"not-crt.dll":"MSVCRT.dll";i.name=(which==1&&address==0x5bb518)?"not-data":name;i.iat_rva=address-0x400000;i.original_iat_value=0x100000+address;x.memory.store<std::uint32_t>(GuestAddress{address},i.original_iat_value);x.metadata.imports.push_back(i);}if(which==2)x.metadata.imports.push_back(x.metadata.imports.front());if(which==3)x.metadata.imports.erase(x.metadata.imports.begin()+1);x.memory.protect(GuestAddress{0x5bb000},Permissions::read);return x;}
void suite(){
    for(auto [address,size]:std::array<std::pair<unsigned,std::size_t>,5>{{{0x32000000,1},{0x32ffffff,1},{0x32fe0000,131072},{0x32000001,17},{0x32001000,0}}}){
        ++scenarios;auto r=Runtime::from_admitted_image(game,policy());seed(r);Snapshot saved(r);auto p=projection(address,size);auto bytes=p.observed_buffer;const auto iat=r.memory().load<std::uint32_t>(GuestAddress{0x5bb518});{
            cd::DataImportRegistry d(r);d.admit_reference_projection(provider,p);check(d.record().has_value()&&d.record()->reference_projection_ready,"complete boundary admission");check(d.record()->observed_original_pointer==original_pointer&&d.record()->owned_guest_pointer.value==address,"pointer provenance separation");check(d.record()->reference_projection_only&&!d.record()->production_initialized_service&&!cd::DataImportRegistry::production_initialized_service,"reference scope fixed");check(d.resolve_reference_load32(GuestAddress{0x5bb518})==0x78037174,"load returns global address");check(r.memory().load<std::uint32_t>(GuestAddress{0x78037174})==address,"projection points to owned buffer");std::vector<std::byte>now(bytes.size());r.memory().read(GuestAddress{address},now);check(now==bytes,"complete owned copy");bool ro{};try{r.memory().store<std::uint8_t>(GuestAddress{address},1);}catch(const MemoryFault&f){ro=f.reason()==MemoryFaultReason::permission_denied;}check(ro,"initial RO admission");check(!d.poisoned(),"external caught write not registry call");saved.unchanged(r);
        }check(absent(r,GuestAddress{address})&&absent(r,GuestAddress{0x78037174}),"successful destructor releases exact owners");check(r.memory().load<std::uint32_t>(GuestAddress{0x5bb518})==iat,"IAT untouched by teardown");saved.unchanged(r);
    }
    for(unsigned kind=0;kind<16;++kind){
        ++scenarios;auto r=Runtime::from_admitted_image(game,policy());seed(r);Snapshot saved(r);cd::DataImportRegistry d(r);auto p=projection();auto pr=provider;
        if(kind==0)p.owned_guest_pointer=GuestAddress{0x31ffffff};if(kind==1)p.owned_guest_pointer=GuestAddress{0x33000000};if(kind==2)p=projection(0x32fffffe,3);if(kind==3)p=projection(0x32000000,131073);
        if(kind==4)p.observed_original_pointer=0;if(kind==5)p.observed_buffer.clear();if(kind==6)p.observed_buffer.back()=std::byte{1};if(kind==7)p.observed_buffer[0]=std::byte{};
        if(kind==8)p.original_buffer_sha256=std::string(64,'0');if(kind==9)p.original_buffer_sha256=std::string(64,'g');if(kind==10)p.original_measurement_sha256=std::string(64,'A');if(kind==11)p.original_measurement_sha256=std::string(63,'1');if(kind==12)p.original_measurement_sha256=std::string(64,'0');if(kind==13)p.original_buffer_sha256=std::string(64,'1');if(kind==14)pr[100]^=std::byte{1};if(kind==15)p.observed_buffer[1]^=std::byte{1};
        reject(d,[&]{d.admit_reference_projection(pr,p);},cd::DataFaultReason::invalid_admission);check(!d.record()||!d.record()->reference_projection_ready,"denied records cannot route");reuse(d,cd::DataFaultReason::invalid_admission);check(absent(r,GuestAddress{0x32000000})&&absent(r,GuestAddress{0x78037174}),"pre-map failure acquires no owners");saved.unchanged(r);
    }
    for(unsigned which=0;which<4;++which){++scenarios;auto r=Runtime::for_authored_fixture(fixture(which),policy());cd::DataImportRegistry d(r);reject(d,[&]{d.admit_reference_projection(provider,projection());},cd::DataFaultReason::invalid_admission);reuse(d,cd::DataFaultReason::invalid_admission);}
    for(unsigned global=0;global<2;++global){++scenarios;auto r=Runtime::from_admitted_image(game,policy());auto address=GuestAddress{global?0x78037174U:0x32000000U};r.memory().map(address,global?4:4096,Permissions::read|Permissions::write);r.memory().store<std::uint32_t>(address,0x91a2b3c4);{
        cd::DataImportRegistry d(r);reject(d,[&]{d.admit_reference_projection(provider,projection());},cd::DataFaultReason::invalid_admission);check(!d.record()->reference_projection_ready,"partial collision not ready");reuse(d,cd::DataFaultReason::invalid_admission);
    }check(r.memory().load<std::uint32_t>(address)==0x91a2b3c4,"collision preserves external bytes");check(absent(r,GuestAddress{global?0x32000000U:0x78037174U}),"collision cleanup drops only own map");}
    for(unsigned kind=0;kind<8;++kind){++scenarios;auto r=Runtime::from_admitted_image(game,policy());seed(r);Snapshot saved(r);cd::DataImportRegistry d(r);d.admit_reference_projection(provider,projection());
        if(kind==0){r.memory().protect(GuestAddress{0x5bb000},Permissions::read|Permissions::write);r.memory().store<std::uint32_t>(GuestAddress{0x5bb518},0);}
        if(kind==1)r.memory().store<std::uint32_t>(GuestAddress{0x78037174},0);
        if(kind==2){r.memory().protect(GuestAddress{0x32000000},Permissions::read|Permissions::write);r.memory().store<std::uint8_t>(GuestAddress{0x32000000},0);}
        if(kind==3)r.memory().protect(GuestAddress{0x32000000},Permissions::none);
        if(kind==4)r.memory().protect(GuestAddress{0x78037174},Permissions::none);
        if(kind==5)r.memory().protect(GuestAddress{0x5bb000},Permissions::none);
        if(kind==6)r.memory().unmap(GuestAddress{0x32000000});
        if(kind==7)r.memory().unmap(GuestAddress{0x78037174});
        auto why=kind<3?cd::DataFaultReason::changed_identity:cd::DataFaultReason::memory_fault;reject(d,[&]{(void)d.resolve_reference_load32(GuestAddress{0x5bb518});},why);reuse(d,why);saved.unchanged(r);
    }
    for(auto address:std::array<unsigned,4>{0x5bb508,0x5bb519,0x78037174,0}){++scenarios;auto r=Runtime::from_admitted_image(game,policy());cd::DataImportRegistry d(r);d.admit_reference_projection(provider,projection());reject(d,[&]{(void)d.resolve_reference_load32(GuestAddress{address});},cd::DataFaultReason::unresolved_data);reuse(d,cd::DataFaultReason::unresolved_data);}
    {++scenarios;auto r=Runtime::from_admitted_image(game,policy());cd::DataImportRegistry d(r);reject(d,[&]{(void)d.resolve_reference_load32(GuestAddress{0x5bb518});},cd::DataFaultReason::unresolved_data);reuse(d,cd::DataFaultReason::unresolved_data);}
    {++scenarios;auto r=Runtime::from_admitted_image(game,policy());cd::DataImportRegistry d(r);d.admit_reference_projection(provider,projection());reject(d,[&]{d.admit_reference_projection(provider,projection());},cd::DataFaultReason::invalid_admission);reuse(d,cd::DataFaultReason::invalid_admission);}
}
}
int main(int argc,char**argv){try{check(argc==4,"independent ownership inputs required");provider=read(argv[1]);game=read(argv[2]);raw=read(argv[3]);check(m4::sha256(provider)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7"&&m4::sha256(game)=="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf","exact library inputs");check(m4::sha256(raw)=="40b786cd8ec580316141e883f3280c9a6e5c0f8053eb143a0a8f450f2e959ad9","exact independently observed stream");auto offset=44ULL+word(raw,36)+64+28+28ULL*word(raw,40);auto n=word(raw,20);check(offset+n<=raw.size(),"buffer read bounds");original_pointer=word(raw,32);measured.assign(raw.begin()+static_cast<std::ptrdiff_t>(offset),raw.begin()+static_cast<std::ptrdiff_t>(offset+n));suite();std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"scenarios\":"<<scenarios<<",\"production_service\":false}\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
