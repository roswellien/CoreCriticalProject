// Complete original writer execution is confined to the admitted private RX
// slices. This file supplies observations, real Windows imports and ownership.
#include "common.hpp"
#include "spec.hpp"
#include "original_broker.hpp"
#include <iostream>
#include <memory>
using namespace mw34::m4_fdiv_reference;
namespace probe=mw34::m4_crt_probe;
namespace fdiv=mw34::m4_crt_fdiv;
extern "C" {
Cpu fd_input{},fd_before{},fd_after{};
unsigned fd_saved_esp{},fd_writer_sp{},fd_stack_base{},fd_stack_bytes{},fd_stack_limit{},fd_stack_top{},fd_limit_after{},fd_top_after{},fd_capture_complete{},fd_entry_complete{};
unsigned fd_page_addresses[7]{0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000};
alignas(16) std::uint8_t fd_guest_fx[512]{},fd_host_fx[512]{},fd_host_after[512]{},fd_fx_before[512]{},fd_fx_after[512]{};
std::uint8_t fd_guest_env[28]{},fd_host_env[28]{},fd_host_env_after[28]{},fd_env_before[28]{},fd_env_after[28]{};
std::uint8_t fd_stack_before[maximum_stack]{},fd_stack_after[maximum_stack]{},fd_pages_before[7*4096]{},fd_pages_after[7*4096]{};
alignas(16) std::uint8_t fd_scratch[4096]{};unsigned fd_scratch_esp{},fd_flags_temp{};
void fd_enter();void fd_capture();void fd_restore();
}
static Record*active_record{};
static DWORD reference_thread{};
static std::vector<HostRegion>stack_before_regions,stack_after_regions;
static unsigned pointer(const void*p){return static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(p));}
static std::vector<HostRegion> stack_regions(unsigned limit,unsigned top){
    need(limit<top&&!(limit&4095)&&!(top&4095)&&top-limit<=maximum_stack,"Actual bounded page-aligned NT_TIB stack extent required");
    std::vector<HostRegion>r;r.reserve((top-limit)/4096);std::uint64_t allocation{};
    for(unsigned p=limit;p<top;p+=4096){auto v=region(p);need(v.state==MEM_COMMIT&&v.type==MEM_PRIVATE&&v.protect==PAGE_READWRITE&&p>=v.base&&std::uint64_t(p)+4096<=v.base+v.bytes,"Every observed stack page must already be committed RW, without guard");if(!allocation)allocation=v.allocation;need(v.allocation==allocation,"One real stack allocation required");r.push_back(v);}
    return r;
}
// Only the dedicated reference thread is observed. A hardware instruction
// breakpoint produces an actual OS context; this is not direct FNSTENV data.
static LONG CALLBACK observe(EXCEPTION_POINTERS*p){
    if(GetCurrentThreadId()!=reference_thread||!active_record)return EXCEPTION_CONTINUE_SEARCH;
    auto&r=*active_record;const auto ordinal=r.tags.debug_count;
    if(ordinal>=maximum_debug_events){++r.tags.debug_unexpected;return EXCEPTION_CONTINUE_SEARCH;}
    auto&e=r.debug_events[ordinal];e.ordinal=ordinal;e.thread_id=reference_thread;
    std::memcpy(&e.exception,p->ExceptionRecord,sizeof(e.exception));std::memcpy(&e.before,p->ContextRecord,sizeof(e.before));
    ++r.tags.debug_count;
    const auto&c=*p->ContextRecord;
    constexpr unsigned required_context=CONTEXT_CONTROL|CONTEXT_INTEGER|CONTEXT_DEBUG_REGISTERS;
    const bool expected=r.tags.debug&&ordinal<3&&p->ExceptionRecord->ExceptionCode==EXCEPTION_SINGLE_STEP&&
        (c.ContextFlags&required_context)==required_context&&
        pointer(p->ExceptionRecord->ExceptionAddress)==return_pcs[ordinal]&&c.Eip==return_pcs[ordinal]&&
        (c.Dr6&15U)==(1U<<ordinal)&&(c.EFlags&0x100U)==0&&c.Dr0==return_pcs[0]&&
        c.Dr1==return_pcs[1]&&c.Dr2==return_pcs[2]&&(c.Dr7&0xffU)==0x15U;
    if(!expected){++r.tags.debug_unexpected;std::memcpy(&e.continued,p->ContextRecord,sizeof(e.continued));return EXCEPTION_CONTINUE_SEARCH;}
    // RF suppresses the same execute breakpoint for exactly the resumed
    // instruction. Record the original and altered CONTEXT verbatim; neither
    // the source bytes, stack, PC, GPRs nor returned FARPROC are changed.
    p->ContextRecord->EFlags|=0x10000U;
    p->ContextRecord->Dr6&=~15U;
    std::memcpy(&e.continued,p->ContextRecord,sizeof(e.continued));
    return EXCEPTION_CONTINUE_EXECUTION;
}
static unsigned execute(){
    __try{fd_enter();return fd_capture_complete?0U:0xe0000001U;}
    __except(EXCEPTION_EXECUTE_HANDLER){const auto code=GetExceptionCode();fd_restore();return code;}
}
static DWORD WINAPI thread_entry(void*){
    try{
        auto&t=*reinterpret_cast<NT_TIB*>(NtCurrentTeb());auto&r=*active_record;
        fd_stack_limit=pointer(t.StackLimit);fd_stack_top=pointer(t.StackBase);fd_stack_base=fd_stack_limit;fd_stack_bytes=fd_stack_top-fd_stack_limit;
        stack_before_regions=stack_regions(fd_stack_limit,fd_stack_top);
        need(fd_stack_limit>=4096,"Actual lower stack guard boundary bound");r.excluded_guard_before=region(fd_stack_limit-4096);
        need(r.excluded_guard_before.state==MEM_RESERVE||(r.excluded_guard_before.protect&PAGE_GUARD),"Actual excluded lower stack boundary must be reserved or guard");
        r.tags.limit_before=fd_stack_limit;r.tags.base_before=fd_stack_top;r.tags.teb=pointer(&t);
        r.tags.stack_base=fd_stack_base;r.tags.stack_bytes=fd_stack_bytes;r.tags.thread_id=GetCurrentThreadId();
        r.tags.status=execute();r.tags.writer_sp=fd_writer_sp;r.tags.limit_after=fd_limit_after;r.tags.base_after=fd_top_after;
        r.tags.snapshot_complete=fd_capture_complete;r.tags.entry_complete=fd_entry_complete;
        if(fd_capture_complete){stack_after_regions=stack_regions(fd_limit_after,fd_top_after);need(fd_limit_after>=4096,"Actual after lower stack guard boundary bound");r.excluded_guard_after=region(fd_limit_after-4096);r.tags.restore_checkpoint=std::memcmp(fd_host_fx,fd_host_after,512)==0&&std::memcmp(fd_host_env,fd_host_env_after,28)==0;}
        return r.tags.status;
    }catch(const std::exception&e){active_record->tags.status=0xe0000002U;std::cerr<<"Reference thread admission: "<<e.what()<<'\n';return active_record->tags.status;}
}
struct Region {void*base;explicit Region(unsigned a):base(mw34::original_broker::reserve_or_adopt(a)){}~Region(){VirtualFree(base,0,MEM_RELEASE);}Region(const Region&)=delete;};
static std::uint8_t*page(unsigned a){auto*p=static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(a),4096,MEM_COMMIT,PAGE_READWRITE));need(p==reinterpret_cast<void*>(a),"Exact privately owned original page commit failed");return p;}
static void protect(void*p,DWORD desired){DWORD old{};need(VirtualProtect(p,4096,desired,&old)!=0,"Original private protection failed");if(desired==PAGE_EXECUTE_READ)need(FlushInstructionCache(GetCurrentProcess(),p,4096)!=0,"Original code cache flush failed");auto v=region(pointer(p));need(v.state==MEM_COMMIT&&v.type==MEM_PRIVATE&&v.protect==desired,"Actual original private page protection differs");}
static void copy_capture(Record&r){
    r.before=fd_before;r.after=fd_after;
    std::memcpy(r.fx_before.data(),fd_fx_before,512);std::memcpy(r.fx_after.data(),fd_fx_after,512);std::memcpy(r.host_before.data(),fd_host_fx,512);std::memcpy(r.host_after.data(),fd_host_after,512);
    std::memcpy(r.env_before.data(),fd_env_before,28);std::memcpy(r.env_after.data(),fd_env_after,28);std::memcpy(r.host_env_before.data(),fd_host_env,28);std::memcpy(r.host_env_after.data(),fd_host_env_after,28);
    std::memcpy(r.pages_before.data(),fd_pages_before,r.pages_before.size());std::memcpy(r.pages_after.data(),fd_pages_after,r.pages_after.size());
    r.tags.stack_pages_before=static_cast<unsigned>(stack_before_regions.size());r.tags.stack_pages_after=static_cast<unsigned>(stack_after_regions.size());
}
int main(int argc,char**argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(pointer(GetModuleHandleW(nullptr))==0x34000000,"Deterministic disjoint original worker base rejected");
    if(auto code=mw34::original_broker::dispatch(argc,argv,4))return *code;
    need(argc==4,"Original FDIV reference: admitted-pack exact-provider fresh-output");
    const auto provider=probe::read(argv[2],266293);fdiv::Provider admitted(std::as_bytes(std::span(provider)));
    const auto pack=probe::read(argv[1],pack_bytes);need(pack.size()==pack_bytes&&probe::digest(pack)==pack_sha&&std::memcmp(pack.data(),"MW4FDIP1",8)==0,"Exact original FDIV source pack required");
    unsigned count{};std::memcpy(&count,pack.data()+8,4);need(count==7,"Exact original FDIV page count");
    Output out(argv[3]);out.write("MW4FDOR1",8);const unsigned header[]{1,records,sizeof(Record),sizeof(CONTEXT),sizeof(EXCEPTION_RECORD),maximum_stack};out.write(header,sizeof(header));
    std::vector<std::unique_ptr<Region>>owned;for(auto a:mw34::original_broker::bases)owned.push_back(std::make_unique<Region>(a));
    std::array<std::uint8_t*,7>pages{};
    for(unsigned i=0;i<7;++i){unsigned address{},permissions{};std::memcpy(&address,pack.data()+12+i*4104,4);std::memcpy(&permissions,pack.data()+16+i*4104,4);need(address==page_addresses[i]&&permissions==page_permissions[i],"Original source page identity/permissions required");pages[i]=page(address);std::memcpy(pages[i],pack.data()+20+i*4104,4096);}
    const auto kernel=GetModuleHandleW(L"kernel32.dll");need(kernel!=nullptr,"Loaded actual32bit KERNEL32 required");
    const auto module_api=reinterpret_cast<FARPROC>(&GetModuleHandleA),proc_api=reinterpret_cast<FARPROC>(&GetProcAddress);
    const auto feature=GetProcAddress(kernel,"IsProcessorFeaturePresent");need(feature!=nullptr,"Actual non-NULL32bit dynamic export required for initial success domain");
    std::array<fdiv::HostIdentity,3>identities{
        fdiv::host_identity(module_api,kernel,"GetModuleHandleA"),fdiv::host_identity(proc_api,kernel,"GetProcAddress"),fdiv::host_identity(feature,kernel,"IsProcessorFeaturePresent")};
    auto module_identity=fdiv::module_identity(kernel);
    // Only these two owning private IAT data DWORDs differ from the file pack.
    // Original CALL EAX uses the actual GetProcAddress return without a gateway.
    probe::put32(pages[3]+0x98,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(module_api)));
    probe::put32(pages[3]+0xd0,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(proc_api)));
    for(unsigned i=0;i<7;++i)protect(pages[i],page_permissions[i]==5?PAGE_EXECUTE_READ:page_permissions[i]==1?PAGE_READONLY:PAGE_READWRITE);
    auto*stub=page(0x10000000);std::memset(stub,0xcc,4096);stub[0x100]=0xe9;probe::put32(stub+0x101,pointer(reinterpret_cast<void*>(&fd_capture))-0x10000105);protect(stub,PAGE_EXECUTE_READ);
    fd_scratch_esp=pointer(fd_scratch)+sizeof(fd_scratch);
    const auto observer=AddVectoredExceptionHandler(1,observe);need(observer!=nullptr,"Original debug observer registration failed");
    struct Handler {PVOID value;~Handler(){RemoveVectoredExceptionHandler(value);}} handler{observer};
    unsigned id{};
    for(unsigned debug=0;debug<2;++debug)for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:probe::controls){
        auto r=std::make_unique<Record>();r->tags.id=id++;r->tags.repeat=repeat;r->tags.debug=debug;r->tags.cw=cw;r->tags.worker_base=pointer(GetModuleHandleW(nullptr));r->tags.context_bytes=sizeof(CONTEXT);
        r->tags.source_api_module=static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(module_api));r->tags.source_api_proc=static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(proc_api));r->tags.expected_module=pointer(kernel);r->tags.expected_feature=static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(feature));
        std::memcpy(pages[6],pack.data()+20+6*4104,4096);fd_entry_complete=fd_capture_complete=0;fd_writer_sp=fd_limit_after=fd_top_after=0;fd_before={};fd_after={};stack_before_regions.clear();stack_after_regions.clear();
        for(auto buffer:{fd_stack_before,fd_stack_after})std::memset(buffer,0,maximum_stack);
        for(auto buffer:{fd_pages_before,fd_pages_after})std::memset(buffer,0,7*4096);
        for(auto buffer:{fd_host_fx,fd_host_after,fd_fx_before,fd_fx_after})std::memset(buffer,0,512);
        for(auto buffer:{fd_host_env,fd_host_env_after,fd_env_before,fd_env_after})std::memset(buffer,0,28);
        probe::seed_fp(fd_guest_fx,fd_guest_env,cw,0);fd_input=probe::seed_cpu(0);fd_input.pc=writer;
        for(unsigned i=0;i<7;++i)r->source_regions_before[i]=region(page_addresses[i]);
        for(unsigned i=0;i<3;++i)r->api_before[i]=identity(identities[i]);r->module_before=identity(module_identity);
        active_record=r.get();mw34::original_broker::Handle thread(CreateThread(nullptr,65536,thread_entry,nullptr,CREATE_SUSPENDED,&reference_thread));need(thread.value!=nullptr,"Owned suspended reference thread creation failed");
        alignas(16) CONTEXT context{};context.ContextFlags=CONTEXT_DEBUG_REGISTERS;need(GetThreadContext(thread.value,&context)!=0,"Actual suspended debug-register capture failed");std::memcpy(&r->suspended_before,&context,sizeof(context));
        need(!(context.Dr7&0xffU),"Reference thread already has active debug breakpoints");context.Dr0=debug?return_pcs[0]:0;context.Dr1=debug?return_pcs[1]:0;context.Dr2=debug?return_pcs[2]:0;context.Dr3=0;context.Dr6=0;context.Dr7=debug?0x15U:0;
        need(SetThreadContext(thread.value,&context)!=0,"Suspended reference breakpoint installation failed");context={};context.ContextFlags=CONTEXT_DEBUG_REGISTERS;need(GetThreadContext(thread.value,&context)!=0,"Actual installed breakpoint capture failed");std::memcpy(&r->suspended_admitted,&context,sizeof(context));
        need(context.Dr0==(debug?return_pcs[0]:0)&&context.Dr1==(debug?return_pcs[1]:0)&&context.Dr2==(debug?return_pcs[2]:0)&&(context.Dr7&0xffU)==(debug?0x15U:0),"Actual installed breakpoint state differs");
        need(ResumeThread(thread.value)==1,"Reference thread resume count differs");const auto waited=WaitForSingleObject(thread.value,30000);need(waited==WAIT_OBJECT_0,"Original reference thread did not finish; broker terminates process on failure");DWORD exit{};need(GetExitCodeThread(thread.value,&exit)!=0,"Reference thread exit unavailable");active_record=nullptr;copy_capture(*r);
        for(unsigned i=0;i<7;++i)r->source_regions_after[i]=region(page_addresses[i]);
        for(unsigned i=0;i<3;++i){const auto current=fdiv::host_identity(i==0?module_api:i==1?proc_api:feature,kernel,i==0?"GetModuleHandleA":i==1?"GetProcAddress":"IsProcessorFeaturePresent");r->api_after[i]=identity(current);need(current==identities[i],"Actual32bit original API owner changed");}r->module_after=identity(fdiv::module_identity(kernel));
        // Retain every actual observed row, including failed original prefixes.
        const unsigned row_bytes=sizeof(Record)+static_cast<unsigned>((stack_before_regions.size()+stack_after_regions.size())*sizeof(HostRegion))+2*r->tags.stack_bytes;
        out.write(&row_bytes,4);out.write(r.get(),sizeof(Record));out.write(stack_before_regions.data(),stack_before_regions.size()*sizeof(HostRegion));out.write(stack_after_regions.data(),stack_after_regions.size()*sizeof(HostRegion));out.write(fd_stack_before,r->tags.stack_bytes);out.write(fd_stack_after,r->tags.stack_bytes);
        need(exit==0&&r->tags.status==0&&r->tags.snapshot_complete&&r->tags.restore_checkpoint,"Actual complete original writer failed/capture or internal host restoration differs");
        need(r->tags.limit_before==r->tags.limit_after&&r->tags.base_before==r->tags.base_after,"Actual thread stack extent changed: initial comparison admission stops");
        need(r->before.pc==writer&&r->before.esp==r->tags.writer_sp&&r->after.pc==capture&&r->after.esp==r->before.esp+4,"Original natural outer CALL/RET frame differs");
        need(r->after.ebx==r->before.ebx&&r->after.ebp==r->before.ebp&&r->after.esi==r->before.esi&&r->after.edi==r->before.edi,"Original ABI nonvolatile GPR changed");
        need(!r->tags.debug_unexpected&&r->tags.debug_count==(debug?3U:0U),"Actual original debug events differ; no fallback/query success inference");
        if(debug){need(r->debug_events[0].before.Eax==pointer(kernel)&&r->debug_events[1].before.Eax==static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(feature)),"Actual source dynamic lookup targets differ");for(unsigned j=0;j<3;++j)need(r->debug_events[j].before.Esp==r->before.esp-4,"Actual original stdcall4/8/4 cleanup differs");unsigned initialized{};std::memcpy(&initialized,r->pages_after.data()+6*4096+0xc2c,4);need(initialized==r->debug_events[2].before.Eax,"Original initialized data differs from actual source query BOOL");}
        for(unsigned i=0;i<6;++i)need(std::memcmp(r->pages_before.data()+i*4096,r->pages_after.data()+i*4096,4096)==0,"Original source RX/RO/IAT page changed");
    }
    need(id==records,"Actual original reference corpus incomplete");out.finish();std::cout<<"48 actual original FDIV rows; debug-off/direct and debug-on/CONTEXT observations kept separate\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
