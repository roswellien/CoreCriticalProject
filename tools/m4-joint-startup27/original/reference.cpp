#include "protocol.hpp"
#include "spec.hpp"
#include "original_broker.hpp"
#include <memory>
using namespace mw34::m4_mixed_original;
static_assert(sizeof(void*)==4 && sizeof(CONTEXT)==716);
extern "C" {
Cpu mixed_input{},mixed_before{},mixed_after{};
std::uint32_t mixed_host_esp{},mixed_env_ready{};
alignas(16) std::uint8_t mixed_guest_fx[512]{},mixed_host_fx[512]{},mixed_host_after[512]{};
alignas(16) std::uint8_t mixed_fx_before[512]{},mixed_fx_after[512]{};
std::uint8_t mixed_guest_env[28]{},mixed_env_before[28]{},mixed_env_after[28]{},mixed_host_env[28]{},mixed_host_env_after[28]{};
void mixed_enter();void mixed_capture();void mixed_restore();
}
static std::uint32_t execute(){__try{mixed_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){const auto code=GetExceptionCode();mixed_restore();return code;}}
static CONTEXT checkpoint{};static unsigned checkpoint_seen{},checkpoint_pending{},checkpoint_error{};static DWORD owner{};
bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){
 const auto&exception=event.u.Exception.ExceptionRecord;auto code=exception.ExceptionCode;
 if((code!=EXCEPTION_BREAKPOINT&&code!=0x4000001fU)||exception.ExceptionAddress!=reinterpret_cast<void*>(0x4c1a09))return false;
 auto get=[&](const void*address,void*data,SIZE_T size){SIZE_T copied{};require(ReadProcessMemory(child,address,data,size,&copied)&&copied==size,"Checkpoint child read failed");};
 auto put=[&](void*address,const void*data,SIZE_T size){SIZE_T copied{};require(WriteProcessMemory(child,address,data,size,&copied)&&copied==size,"Checkpoint child write failed");};
 unsigned pending{},seen{};DWORD child_owner{};get(&checkpoint_pending,&pending,4);get(&checkpoint_seen,&seen,4);get(&owner,&child_owner,4);
 require(pending==1&&!seen&&child_owner==event.dwThreadId,"Checkpoint owner/pending rejected");
 Handle thread(OpenThread(THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,event.dwThreadId));require(thread.value!=nullptr,"Checkpoint thread open failed");
 CONTEXT actual{};actual.ContextFlags=CONTEXT_FULL|CONTEXT_FLOATING_POINT|CONTEXT_EXTENDED_REGISTERS;require(GetThreadContext(thread.value,&actual),"Actual stopped x86 CONTEXT unavailable");
 require(actual.Eip==0x4c1a0a&&actual.Esp==frame-12&&actual.Ebp==frame-12,"Actual provider return frame/PC rejected");
 std::uint8_t byte{};get(reinterpret_cast<void*>(0x4c1a09),&byte,1);require(byte==0xcc,"Checkpoint trap byte differs");
 // Retain the debugger's literal CONTEXT before the authored EIP rewind.
 put(&checkpoint,&actual,sizeof(actual));DWORD old{};require(VirtualProtectEx(child,reinterpret_cast<void*>(0x4c1000),4096,PAGE_EXECUTE_READWRITE,&old),"Checkpoint source writable transition failed");
 byte=0xd9;put(reinterpret_cast<void*>(0x4c1a09),&byte,1);DWORD ignored{};require(FlushInstructionCache(child,reinterpret_cast<void*>(0x4c1a09),1)&&VirtualProtectEx(child,reinterpret_cast<void*>(0x4c1000),4096,PAGE_EXECUTE_READ,&ignored),"Checkpoint source restore failed");
 seen=1;pending=0;put(&checkpoint_seen,&seen,4);put(&checkpoint_pending,&pending,4);
 // GetThreadContext's FX/FloatSave legacy metadata was measured zero. Never
 // write that observer projection back over the live guest FP environment.
 actual.Eip=0x4c1a09;actual.ContextFlags=CONTEXT_CONTROL;
 require(SetThreadContext(thread.value,&actual),"Original FSTP continuation restore failed");return true;
}

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
    const bool debugger=argc>1&&std::string(argv[argc-1])=="--checkpoint";mw34::original_broker::checkpoint_mode=debugger;
    if(auto broker=mw34::original_broker::dispatch(argc,argv,debugger?6:5))return *broker;
    require(argc==(debugger?6:5),"Connected original27: exact-pack exact-image exact-provider fresh-output [--checkpoint]");
    std::vector<std::unique_ptr<Region>> regions;
    for(auto base:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(base));
    const auto image=read(argv[2],2384384);require(image.size()==2384384&&sha256(image)==image_sha,"Image identity rejected");
    const auto provider=read(argv[3],565760);require(provider.size()==565760&&sha256(provider)=="91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a","Provider identity rejected");
    const auto pack=read(argv[1],pack_size);require(pack.size()==pack_size&&sha256(pack)==pack_sha,"Pack identity rejected");
    require(std::memcmp(pack.data(),"MW4J27P1",8)==0&&word<std::uint32_t>(pack.data()+8)==page_bases.size(),"Pack header rejected");
    for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(std::uint64_t{span.image_offset}+span.size<=origin.size(),"Original source extent rejected");}
    std::array<void*,26> pages{};
    for(unsigned i=0;i<pages.size();++i){
        const auto offset=12+i*4104;
        require(word<std::uint32_t>(pack.data()+offset)==page_bases[i]&&word<std::uint32_t>(pack.data()+offset+4)==page_permissions[i],"Pack page layout rejected");
        pages[i]=VirtualAlloc(reinterpret_cast<void*>(page_bases[i]),page_size,MEM_COMMIT,PAGE_READWRITE);
        require(pages[i]==reinterpret_cast<void*>(page_bases[i]),"Exact page commit failed");std::memcpy(pages[i],pack.data()+offset+8,page_size);
    }
    for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original committed instruction/source binding rejected");}
    require(*reinterpret_cast<unsigned*>(0x5bb4fc)==0x780c10f0,"Declared owning IAT relocation rejected");
    auto*stub=reinterpret_cast<std::uint8_t*>(capture_pc);
    for(unsigned i=0;i<5;++i)require(stub[i]==0xcc,"Capture broker sparse slot differs");
    stub[0]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&mixed_capture)-(capture_pc+5));std::memcpy(stub+1,&delta,4);
    const std::array<std::uint8_t,5> broker_bytes{stub[0],stub[1],stub[2],stub[3],stub[4]};
    for(unsigned i=0;i<pages.size();++i){
        protect(pages[i],page_permissions[i]==1?PAGE_EXECUTE_READ:page_permissions[i]==0?PAGE_READONLY:PAGE_READWRITE);
        if(page_permissions[i]==1)require(FlushInstructionCache(GetCurrentProcess(),pages[i],page_size),"Code cache flush failed");
    }
    owner=GetCurrentThreadId();
    Output out(argv[4]);Header header{};std::memcpy(header.magic,debugger?"MW4J27D1":"MW4J27O1",8);
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
            checkpoint={};checkpoint_seen=0;checkpoint_pending=debugger&&entries[phase]==0x4c19f0;checkpoint_error=0;
            if(checkpoint_pending){protect(reinterpret_cast<void*>(0x4c1000),PAGE_EXECUTE_READWRITE);require(*reinterpret_cast<std::uint8_t*>(0x4c1a09)==0xd9,"Checkpoint instruction identity differs");*reinterpret_cast<std::uint8_t*>(0x4c1a09)=0xcc;require(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(0x4c1a09),1),"Checkpoint cache flush failed");protect(reinterpret_cast<void*>(0x4c1000),PAGE_EXECUTE_READ);}
            r->tag.status=execute();copy_capture(*r);copy_pages(r->memory_after);r->tag.host_restored=host_restored(*r)?1U:0U;
            std::memcpy(r->checkpoint_context.data(),&checkpoint,sizeof(checkpoint));r->checkpoint_seen=checkpoint_seen;out.write(*r);
            if(r->tag.status||!r->tag.host_restored||r->after.pc!=capture_pc||r->after.esp!=returned_esp||checkpoint_error||checkpoint_seen!=(debugger&&entries[phase]==0x4c19f0)){
                // The partial raw prefix is deliberately preserved as failed
                // evidence; its header still declares the full intended domain.
                out.commit();std::cerr<<"Actual original phase failed sequence="<<sequence<<" phase="<<phase<<" status="<<r->tag.status<<'\n';return 1;
            }
        }
        for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Original selected source changed after checkpoint");}
        ++sequence;
    }
    require(sequence==sequences,"Connected sequence count differs");
    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){
        const auto*actual=static_cast<std::uint8_t*>(pages[i]);const auto*expected=pack.data()+12+i*4104+8;
        for(unsigned byte=0;byte<page_size;++byte){const auto pc=page_bases[i]+byte;
            require(actual[byte]==(pc>=capture_pc&&pc<capture_pc+5?broker_bytes[pc-capture_pc]:expected[byte]),"Protected owned page identity changed");}
    }
    out.commit();std::cout<<"48 connected sequences / 1296 actual original initializer phases captured; full ledger and native equivalence remain open\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
