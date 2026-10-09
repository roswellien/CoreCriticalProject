#include "common.hpp"
#include "original_broker.hpp"
#include <memory>
using namespace mw34::spi;
static_assert(sizeof(void*)==4);
extern "C" {
Cpu spi_input{},spi_before{},spi_after{},spi_service_before{},spi_service_after{};
std::uint32_t spi_host_esp{},spi_service_esp{},spi_actual_provider{},spi_resume{resume},spi_provider_esp_before{},spi_provider_esp_after{};
alignas(16)std::uint8_t spi_guest_fx[512]{},spi_host_fx[512]{},spi_host_after[512]{},spi_fx_before[512]{},spi_fx_after[512]{},spi_service_fx_before[512]{},spi_service_fx_after[512]{};
std::uint8_t spi_env_before[28]{},spi_env_after[28]{},spi_host_env[28]{},spi_host_env_after[28]{},spi_service_env_before[28]{},spi_service_env_after[28]{},spi_service_rect_before[16]{},spi_service_rect_after[16]{};
void spi_enter();void spi_capture();void spi_restore();void spi_service_entry();
}
static unsigned execute(){__try{spi_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){const auto result=GetExceptionCode();spi_restore();return result;}}
struct Region{void*base;explicit Region(unsigned a):base(mw34::original_broker::reserve_or_adopt(a)){}~Region(){if(base)VirtualFree(base,0,MEM_RELEASE);}Region(const Region&)=delete;};
static void capture_pages(std::array<std::uint8_t,12288>&b){for(unsigned i=0;i<3;++i)std::memcpy(b.data()+i*4096,reinterpret_cast<void*>(observed_pages[i]),4096);}
int main(int argc,char**argv){try{SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);if(auto r=mw34::original_broker::dispatch(argc,argv,4))return*r;require(argc==4,"Usage: spi_original pack image fresh-output");const auto pack=admit(argv[1],argv[2]);provider(false);auto proc=GetProcAddress(GetModuleHandleW(L"user32.dll"),"SystemParametersInfoA");require(proc!=nullptr,"Actual SystemParametersInfoA export missing");spi_actual_provider=reinterpret_cast<std::uintptr_t>(proc);
    std::vector<std::unique_ptr<Region>>regions;for(auto a:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(a));
    for(unsigned i=0;i<5;++i){auto p=pack.data()+12+i*4104;auto a=word<unsigned>(p);auto*actual=VirtualAlloc(reinterpret_cast<void*>(a),4096,MEM_COMMIT,PAGE_READWRITE);require(actual==reinterpret_cast<void*>(a),"Exact committed page required");std::memcpy(actual,p+8,4096);}
    auto*stub=reinterpret_cast<std::uint8_t*>(broker);require(std::memcmp(stub,"\xcc\xcc\xcc\xcc\xcc",5)==0,"Capture slot is not sparse");stub[0]=0xe9;auto delta=static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(&spi_capture)-(broker+5));std::memcpy(stub+1,&delta,4);*reinterpret_cast<std::uint32_t*>(iat)=reinterpret_cast<std::uintptr_t>(&spi_service_entry);
    for(unsigned i=0;i<5;++i){auto p=pack.data()+12+i*4104;auto a=word<unsigned>(p),perm=word<unsigned>(p+4);DWORD old{};require(VirtualProtect(reinterpret_cast<void*>(a),4096,perm==1?PAGE_EXECUTE_READ:perm==0||a==0x5bb000?PAGE_READONLY:PAGE_READWRITE,&old),"Page protect failed");if(perm==1)require(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(a),4096),"Code cache flush failed");}
    Output out(argv[3]);Header h{};std::memcpy(h.magic,"MW4SPIO1",8);h.version=1;h.count=cases;h.record_bytes=sizeof(Record);h.observed_pages=3;out.write(&h,sizeof(h));unsigned id{};
    for(unsigned repeat=0;repeat<2;++repeat)for(auto cw:controls)for(unsigned top:{0U,7U})for(unsigned v=0;v<3;++v){Record r{};r.id=id++;r.repeat=repeat;r.cw=cw;r.top=top;r.variant=v;r.service_defined_cpu=0x2f9;
        for(unsigned p=1;p<3;++p){auto b=pagefixture(p,v);std::memcpy(reinterpret_cast<void*>(observed_pages[p]),b.data(),4096);}*reinterpret_cast<unsigned*>(frame)=broker;spi_input=initial(v);const auto fx=initialfx(cw,top,v);std::memcpy(spi_guest_fx,fx.data(),512);spi_before={};spi_after={};spi_service_before={};spi_service_after={};std::memset(spi_service_fx_after,0,512);capture_pages(r.memory_before);r.status=execute();capture_pages(r.memory_after);
        r.before=spi_before;r.after=spi_after;r.service.before=spi_service_before;r.service.after=spi_service_after;
        std::memcpy(r.fx_before.data(),spi_fx_before,512);std::memcpy(r.fx_after.data(),spi_fx_after,512);std::memcpy(r.env_before.data(),spi_env_before,28);std::memcpy(r.env_after.data(),spi_env_after,28);std::memcpy(r.host_before.data(),spi_host_fx,512);std::memcpy(r.host_after.data(),spi_host_after,512);std::memcpy(r.host_env_before.data(),spi_host_env,28);std::memcpy(r.host_env_after.data(),spi_host_env_after,28);
        std::memcpy(r.service.fx_before.data(),spi_service_fx_before,512);std::memcpy(r.service.fx_after.data(),spi_service_fx_after,512);std::memcpy(r.service.env_before.data(),spi_service_env_before,28);std::memcpy(r.service.env_after.data(),spi_service_env_after,28);std::memcpy(r.service.rect_before.data(),spi_service_rect_before,16);std::memcpy(r.service.rect_after.data(),spi_service_rect_after,16);r.service.called=spi_service_after.pc==resume;r.service.BOOL_value=spi_service_after.gpr[0];r.service.guest_cleanup=16;r.service.provider_ESP_before=spi_provider_esp_before;r.service.provider_ESP_after=spi_provider_esp_after;r.host_restored=hostequal(r,false);r.completed=!r.status&&r.after.pc==broker&&r.after.gpr[4]==frame+4&&r.service.called&&spi_provider_esp_before+20==spi_provider_esp_after;
        out.write(&r,sizeof(r));if(!r.completed||!r.host_restored){out.commit();std::cerr<<"Original rooted query fault: case="<<r.id<<" status="<<r.status<<'\n';return 1;}
    }require(id==cases,"Original case extent differs");out.commit();return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
