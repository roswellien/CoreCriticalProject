#include "protocol.hpp"
#include "spec.hpp"
#include "original_broker.hpp"
#include <memory>
using namespace mw34::m4_mixed_original;
static_assert(sizeof(void*)==4);
extern "C" {
Cpu mixed_input{},mixed_before{},mixed_after{};
std::uint32_t mixed_host_esp{},mixed_env_ready{};
alignas(16) std::uint8_t mixed_guest_fx[512]{},mixed_host_fx[512]{},mixed_host_after[512]{};
alignas(16) std::uint8_t mixed_fx_before[512]{},mixed_fx_after[512]{};
std::uint8_t mixed_guest_env[28]{},mixed_env_before[28]{},mixed_env_after[28]{},mixed_host_env[28]{},mixed_host_env_after[28]{};
void mixed_enter();void mixed_capture();void mixed_restore();
}
static std::uint32_t execute(){__try{mixed_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){const auto code=GetExceptionCode();mixed_restore();return code;}}
struct Region {
    void*base{};
    explicit Region(std::uint32_t address):base(mw34::original_broker::reserve_or_adopt(address)){}
    ~Region(){if(base)VirtualFree(base,0,MEM_RELEASE);}
    Region(const Region&)=delete;
};
static void protect(void*page,DWORD flags){DWORD previous{};require(VirtualProtect(page,page_size,flags,&previous),"Page protect failed");}
static void copy_pages(std::array<std::uint8_t,memory_size>&target){
    for(unsigned i=0;i<observed_pages.size();++i)std::memcpy(target.data()+i*page_size,reinterpret_cast<void*>(observed_pages[i]),page_size);
}
static void copy_capture(Record&r){
    r.before=mixed_before;r.after=mixed_after;
    std::memcpy(r.guest_fx_before.data(),mixed_fx_before,512);std::memcpy(r.guest_fx_after.data(),mixed_fx_after,512);
    std::memcpy(r.host_fx_before.data(),mixed_host_fx,512);std::memcpy(r.host_fx_after.data(),mixed_host_after,512);
    std::memcpy(r.guest_env_before.data(),mixed_env_before,28);std::memcpy(r.guest_env_after.data(),mixed_env_after,28);
    std::memcpy(r.host_env_before.data(),mixed_host_env,28);std::memcpy(r.host_env_after.data(),mixed_host_env_after,28);
}
int main(int argc,char**argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc==2&&std::string(argv[1])=="--check-protocol"){std::cout<<protocol_controls()<<" protocol controls passed\n";return 0;}
    if(argc==3&&std::string(argv[1])=="--check-publication"){publication_controls(argv[2]);return 0;}
    if(auto broker=mw34::original_broker::dispatch(argc,argv,4))return *broker;
    require(argc==4,"Connected original: exact-pack exact-image fresh-output");
    std::vector<std::unique_ptr<Region>> regions;
    for(auto base:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(base));
    const auto image=read(argv[2],2384384);require(image.size()==2384384&&sha256(image)==image_sha,"Image identity rejected");
    const auto pack=read(argv[1],pack_size);require(pack.size()==pack_size&&sha256(pack)==pack_sha,"Pack identity rejected");
    require(std::memcmp(pack.data(),"MW4MXP01",8)==0&&word<std::uint32_t>(pack.data()+8)==page_bases.size(),"Pack header rejected");
    for(const auto&span:code_bindings)require(std::uint64_t{span.image_offset}+span.size<=image.size()&&std::uint64_t{span.pack_offset}+span.size<=pack.size()&&
        std::memcmp(image.data()+span.image_offset,pack.data()+span.pack_offset,span.size)==0,"Selected original instruction/image binding rejected");
    std::array<void*,22> pages{};
    for(unsigned i=0;i<pages.size();++i){
        const auto offset=12+i*4104;
        require(word<std::uint32_t>(pack.data()+offset)==page_bases[i]&&word<std::uint32_t>(pack.data()+offset+4)==page_permissions[i],"Pack page layout rejected");
        pages[i]=VirtualAlloc(reinterpret_cast<void*>(page_bases[i]),page_size,MEM_COMMIT,PAGE_READWRITE);
        require(pages[i]==reinterpret_cast<void*>(page_bases[i]),"Exact page commit failed");std::memcpy(pages[i],pack.data()+offset+8,page_size);
    }
    auto*stub=reinterpret_cast<std::uint8_t*>(capture_pc);
    for(unsigned i=0;i<5;++i)require(stub[i]==0xcc,"Capture broker sparse slot differs");
    stub[0]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&mixed_capture)-(capture_pc+5));std::memcpy(stub+1,&delta,4);
    const std::array<std::uint8_t,5> broker_bytes{stub[0],stub[1],stub[2],stub[3],stub[4]};
    for(unsigned i=0;i<pages.size();++i){
        protect(pages[i],page_permissions[i]==1?PAGE_EXECUTE_READ:page_permissions[i]==0?PAGE_READONLY:PAGE_READWRITE);
        if(page_permissions[i]==1)require(FlushInstructionCache(GetCurrentProcess(),pages[i],page_size),"Code cache flush failed");
    }
    Output out(argv[3]);Header header{};std::memcpy(header.magic,"MW4MXO01",8);
    header.version=1;header.sequence_count=sequences;header.root_count=roots;header.total_phases=phase_count;header.page_count=observed_page_count;header.record_size=sizeof(Record);out.write(header);
    unsigned sequence{};
    for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:control_words)for(unsigned top:{0u,7u}){
        // One fresh writable image/stack per complete selected-root sequence.
        for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]==2)std::memcpy(pages[i],pack.data()+12+i*4104+8,page_size);
        mixed_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entries[0]};
        std::memset(mixed_guest_fx,0,512);std::memcpy(mixed_guest_fx,&cw,2);
        const auto sw=static_cast<std::uint16_t>(top<<11);std::memcpy(mixed_guest_fx+2,&sw,2);
        const std::uint32_t mxcsr=0x1f80;std::memcpy(mixed_guest_fx+24,&mxcsr,4);mixed_env_ready=0;
        for(unsigned phase=0;phase<entries.size();++phase){
            if(phase){mixed_input=mixed_after;std::memcpy(mixed_guest_fx,mixed_fx_after,512);std::memcpy(mixed_guest_env,mixed_env_after,28);mixed_env_ready=1;}
            // This framing is the only CPU override between actual bodies.
            mixed_input.esp=frame;mixed_input.pc=entries[phase];std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);
            auto r=std::make_unique<Record>();r->tag={sequence,repeat,phase,table_slots[phase],entries[phase],cw,top,0,0};copy_pages(r->memory_before);
            mixed_before={};mixed_after={};std::memset(mixed_fx_after,0,512);std::memset(mixed_env_after,0,28);
            r->tag.status=execute();copy_capture(*r);copy_pages(r->memory_after);r->tag.host_restored=host_restored(*r)?1U:0U;out.write(*r);
            if(r->tag.status||!r->tag.host_restored||r->after.pc!=capture_pc||r->after.esp!=returned_esp){
                // The partial raw prefix is deliberately preserved as failed
                // evidence; its header still declares the full intended domain.
                out.commit();std::cerr<<"Actual original phase failed sequence="<<sequence<<" phase="<<phase<<" status="<<r->tag.status<<'\n';return 1;
            }
        }
        ++sequence;
    }
    require(sequence==sequences,"Connected sequence count differs");
    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){
        const auto*actual=static_cast<std::uint8_t*>(pages[i]);const auto*expected=pack.data()+12+i*4104+8;
        for(unsigned byte=0;byte<page_size;++byte){const auto pc=page_bases[i]+byte;
            require(actual[byte]==(pc>=capture_pc&&pc<capture_pc+5?broker_bytes[pc-capture_pc]:expected[byte]),"Protected owned page identity changed");}
    }
    out.commit();std::cout<<"48 connected sequences / 1248 actual original initializer phases captured; full ledger and native equivalence remain open\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
