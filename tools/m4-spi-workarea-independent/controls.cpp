// Independent causal caller/bridge fixtures. No original or Windows query
// executes here: only the host query token is replaced, never its guest caller.
#include "common.hpp"
#include "image_loader.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <memory>
static unsigned called{},checks{},scenarios{};
static BOOL reply{};
static RECT emitted{};
static bool write_reply{};
static BOOL WINAPI independent_query(UINT a,UINT b,PVOID p,UINT d){
    mw34::spi::require(a==0x30&&b==0&&d==0&&p,"independent exact query arguments");
    mw34::spi::require(reinterpret_cast<std::uintptr_t>(p)!=mw34::spi::output,"guest pointer cast into host query");
    ++called;if(write_reply)*static_cast<RECT*>(p)=emitted;return reply;
}
#define SystemParametersInfoA independent_query
#define main independent_unused_primary_main
#define class struct
#include "../m4-spi-workarea/native.cpp"
#undef class
#undef main
#undef SystemParametersInfoA
using namespace mw34::spi;
using mw34::Permissions;
void check(bool b,const char*w){require(b,w);++checks;}
void create(Context&c){c.fixture(2);seed(c.state,0xe7f,7,2,1);}
void query_frame(Context&c){create(c);c.active=true;c.used=true;c.state.gpr.rax.dword=output;c.state.gpr.rbx.dword=object;c.state.gpr.rcx.dword=0;c.state.gpr.rsi.dword=0x5e6018;c.state.gpr.rdi.dword=output;c.state.gpr.rip.dword=call;c.state.gpr.rsp.dword=frame-32;const unsigned args[]{resume,0x30,0,output,0};for(unsigned i=0;i<5;++i)c.memory.store<unsigned>({frame-32+4*i},args[i]);}
template<class F>bool rejects(F fn){try{fn();}catch(const std::exception&){return true;}return false;}
int main(int argc,char**argv){try{
    require(argc==4,"independent control inputs");auto pack=admit(argv[1],argv[2]);check_import(read(argv[2],2384384));std::filesystem::path dir(argv[3]);require(!std::filesystem::exists(dir)&&std::filesystem::create_directory(dir),"fresh controls");
    // Deliberately varied FALSE, negative BOOL, and full signed RECT edges.
    for(unsigned mode=0;mode<6;++mode){++scenarios;Record r{};Context c(pack,r);create(c);const auto initial_state=c.state;RECT prior{};c.memory.read({output},std::as_writable_bytes(std::span{&prior,1}));reply=mode<2?0:mode<4?-2147483647:23;write_reply=mode%2==0;emitted={-2147483647,2147483647,-777,991};called=0;{Isolation isolate;c.enter();isolate.finish(r);}check(c.completed&&called==1&&r.host_restored,"one-use completion and host restoration");check(r.service.BOOL_value==static_cast<unsigned>(reply)&&c.state.gpr.rax.dword==object,"BOOL observation and caller discard");RECT now{};c.memory.read({output},std::as_writable_bytes(std::span{&now,1}));auto expected=write_reply?emitted:prior;check(!std::memcmp(&now,&expected,16),"real owned RECT bytes transported even on FALSE");check(c.state.gpr.rdx.dword==initial_state.gpr.rdx.dword&&c.state.gpr.rcx.dword==0&&cpu(c.state).flags==cpu(initial_state).flags,"explicit representative volatile policy");check(rejects([&]{c.enter();})&&called==1,"complete context no second query");}
    // After-body failures are causally poisoned even when memory is repaired.
    for(unsigned mode=0;mode<5;++mode){++scenarios;Record r{};Context c(pack,r);create(c);called=0;
        if(mode==0)c.memory.protect({0x608000},Permissions::read);
        if(mode==1)c.memory.protect({0x5e6000},Permissions::none);
        if(mode==2)c.memory.protect({0x5bb000},Permissions::none);
        if(mode==3)c.memory.store<unsigned>({frame},broker+1);
        if(mode==4){c.memory.protect({0x5bb000},Permissions::read|Permissions::write);c.memory.store<unsigned>({iat},0);}
        {Isolation isolate;check(rejects([&]{c.enter();}),"body fault rejects");isolate.finish(r);}check(c.failed&&c.used&&!c.active&&!c.completed&&r.host_restored,"fault marker/restoration");const auto count=called;
        c.memory.protect({0x608000},Permissions::read|Permissions::write);c.memory.protect({0x5e6000},Permissions::read);c.memory.protect({0x5bb000},Permissions::read|Permissions::write);c.memory.store<unsigned>({iat},0x1df20c);c.memory.store<unsigned>({frame},broker);seed(c.state,0xe7f,7,2,1);
        check(rejects([&]{c.enter();})&&called==count,"repaired entered-fault context cannot execute again");}
    // A rejected pre-entry guard has not consumed the context. Record the
    // actual behavior explicitly, separate from after-entry poison evidence.
    unsigned corrected_preentry{};
    for(unsigned mode=0;mode<5;++mode){++scenarios;Record r{};Context c(pack,r);create(c);called=0;if(mode==0)c.state.aflag.df=1;if(mode==1)c.state.addr.ds_base.dword=1;if(mode==2)c.state.addr.es_base.dword=1;if(mode==3)c.state.gpr.rip.dword=entry+1;if(mode==4)c.state.gpr.rsp.dword=frame+4;
        check(rejects([&]{c.enter();})&&!called&&!c.used&&!c.failed,"pre-entry guard is not consumed");seed(c.state,0xe7f,7,2,1);c.enter();check(c.completed&&called==1,"corrected fresh unentered context admitted");++corrected_preentry;}
    // Direct query inspection is instrumentation exposing Context's private
    // markers. Cover each argument/owner/route with distinct wrong values.
    for(unsigned mode=0;mode<10;++mode){++scenarios;Record r{};Context c(pack,r);query_frame(c);called=0;unsigned pc=call,owner=iat;if(mode<5)c.memory.store<unsigned>({frame-32+4*mode},0xbaad0000+mode);if(mode==5)owner=iat+1;if(mode==6)pc=call+1;if(mode==7)c.active=false;if(mode==8)c.state.addr.es_base.dword=1;if(mode==9)c.state.addr.ds_base.dword=1;check(rejects([&]{c.query(pc,owner);})&&!called&&!r.service.called,"route rejects before authored query");}
    // Output lifetime controls exercise actual exclusive Windows handles.
    unsigned publication{};
    for(unsigned mode=0;mode<3;++mode){++scenarios;auto dest=dir/("result-"+std::to_string(mode));auto stage=std::filesystem::path(dest.string()+".spi-stage-"+std::to_string(GetCurrentProcessId()));auto text=[&](auto p,const char*s){std::ofstream f(p,std::ios::binary);f<<s;require(bool(f),"write sentinel");};auto get=[&](auto p){std::ifstream f(p,std::ios::binary);return std::string((std::istreambuf_iterator<char>(f)),{});};
        if(mode==0){text(stage,"independent-preexisting-stage");check(rejects([&]{Output o(dest.string().c_str());})&&get(stage)=="independent-preexisting-stage"&&!std::filesystem::exists(dest),"failed acquisition preserves other stage");}
        if(mode==1){text(dest,"independent-preexisting-result");check(rejects([&]{Output o(dest.string().c_str());})&&get(dest)=="independent-preexisting-result"&&!std::filesystem::exists(stage),"result admission preserves prior evidence");}
        if(mode==2){{Output o(dest.string().c_str());const unsigned x=0x87654321;o.write(&x,4);}check(!std::filesystem::exists(dest)&&!std::filesystem::exists(stage),"uncommitted owned stage released");}++publication;
    }
    std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"scenarios\":"<<scenarios<<",\"corrected_unentered_contexts\":"<<corrected_preentry<<",\"publication\":"<<publication<<",\"actual_provider_calls\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
