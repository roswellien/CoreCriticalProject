// Reuse frozen hardware capture/broker/output helpers without changing their
// source. The older ten-root main is linked but never invoked.
#define main mw34_prior_original_observation_main
#include "../m4-fp-startup/reference.cpp"
#undef main
#include "corpus.hpp"
#include <span>
#include "publication_controls.hpp"
int main(int argc,char **argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc==3&&std::string(argv[1])=="--check-publication"){mw34::m4_fp_sqrt_publication::controls<Output>(argv[2]);return 0;}
    if(auto broker=mw34::original_broker::dispatch(argc,argv,4))return *broker;
    require(argc==4,"Directed reference: exact-pack exact-image fresh-output");
    std::vector<std::unique_ptr<Region>> regions;for(auto base:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(base));
    const auto image=read(argv[2],2384384);require(image.size()==2384384&&digest(image)=="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf","Exact image identity required");
    const auto pack=read(argv[1],61572);require(pack.size()==61572&&digest(pack)==pack_sha,"Exact pack identity required");
    require(std::memcmp(pack.data(),"MW4FPK01",8)==0,"Pack header rejected");
    std::uint32_t count{};std::memcpy(&count,pack.data()+8,4);require(count==15,"Pack count rejected");
    std::array<void *,15> pages{};
    for(unsigned i=0;i<15;++i){const auto offset=12+i*4104;std::uint32_t base{},permission{};
        std::memcpy(&base,pack.data()+offset,4);std::memcpy(&permission,pack.data()+offset+4,4);
        require(base==page_bases[i]&&permission==page_permissions[i],"Pack page metadata rejected");
        pages[i]=VirtualAlloc(reinterpret_cast<void *>(base),4096,MEM_COMMIT,PAGE_READWRITE);require(pages[i]==reinterpret_cast<void *>(base),"Exact page commit failed");
        std::memcpy(pages[i],pack.data()+offset+8,4096);protect(pages[i],permission==1?PAGE_EXECUTE_READ:permission==0?PAGE_READONLY:PAGE_READWRITE);
        if(permission==1)require(FlushInstructionCache(GetCurrentProcess(),pages[i],4096),"Code cache flush failed");
    }
    auto *capture=static_cast<std::uint8_t *>(VirtualAlloc(reinterpret_cast<void *>(0x10000000),4096,MEM_COMMIT,PAGE_READWRITE));require(capture==reinterpret_cast<void *>(0x10000000),"Capture commit failed");
    auto *stub=capture+0x100;stub[0]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&fp_capture)-0x10000105);
    std::memcpy(stub+1,&delta,4);protect(capture,PAGE_EXECUTE_READ);require(FlushInstructionCache(GetCurrentProcess(),capture,4096),"Capture cache flush failed");
    Output out(argv[3]);const std::uint32_t header[]{1,mw34::m4_fp_sqrt_corpus::directed_records,9,4096};out.write("MW4FPO01",8);out.write(header,sizeof(header));
    std::array<std::uint8_t,9*4096> memory_before{},memory_after{};
    const unsigned entry=0x4adb50;
    for(unsigned repeat=0;repeat<2;++repeat)for(unsigned input=0;input<mw34::m4_fp_sqrt_corpus::fixture_count;++input)
      for(unsigned sticky=0;sticky<2;++sticky)for(auto cw:mw34::m4_fp_sqrt_corpus::controls)for(unsigned top:{0U,7U}){
        for(unsigned i=6;i<15;++i)if(page_permissions[i]==2)std::memcpy(pages[i],pack.data()+12+i*4104+8,4096);
        protect(pages[6],PAGE_READWRITE);std::memcpy(pages[6],pack.data()+12+6*4104+8,4096);
        const auto v=mw34::m4_fp_sqrt_corpus::fixture(input);
        std::memcpy(reinterpret_cast<void *>(0x5c8a88),&v.input,8);std::memcpy(reinterpret_cast<void *>(0x5c8a90),&v.left,8);std::memcpy(reinterpret_cast<void *>(0x5c8a98),&v.right,8);
        protect(pages[6],PAGE_READONLY);
        const std::uint32_t sentinel=0x10000100;std::memcpy(reinterpret_cast<void *>(0x20001800),&sentinel,4);
        for(unsigned i=6;i<15;++i)std::memcpy(memory_before.data()+(i-6)*4096,pages[i],4096);
        fp_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,entry};
        std::memset(fp_guest_fx,0,512);std::memcpy(fp_guest_fx,&cw,2);const auto sw=static_cast<std::uint16_t>((top<<11)|(sticky<<1));std::memcpy(fp_guest_fx+2,&sw,2);
        const std::uint32_t mxcsr=0x1f80;std::memcpy(fp_guest_fx+24,&mxcsr,4);fp_before={};fp_after={};const auto status=execute();
        require(!status&&fp_after.pc==sentinel&&fp_after.esp==0x20001804,"Directed original execution/return failed");
        require(std::memcmp(fp_host_fx,fp_host_after,5)==0&&std::memcmp(fp_host_fx+24,fp_host_after+24,4)==0&&std::memcmp(fp_host_env,fp_host_env_after,28)==0,"Directed host FP restoration failed");
        for(unsigned i=0;i<8;++i)require(std::memcmp(fp_host_fx+32+i*16,fp_host_after+32+i*16,10)==0,"Directed host x87 restoration failed");
        require(std::memcmp(fp_host_fx+160,fp_host_after+160,128)==0,"Directed host XMM restoration failed");
        for(unsigned i=6;i<15;++i)std::memcpy(memory_after.data()+(i-6)*4096,pages[i],4096);
        const std::uint32_t tag[]{(repeat<<16)|(sticky<<15)|input,entry,cw,top,status};out.write(tag,sizeof(tag));out.write(&fp_before,sizeof(fp_before));out.write(&fp_after,sizeof(fp_after));
        for(auto snapshot:{fp_fx_before,fp_fx_after,fp_host_fx,fp_host_after})out.write(snapshot,512);
        for(auto snapshot:{fp_env_before,fp_env_after,fp_host_env,fp_host_env_after})out.write(snapshot,28);
        out.write(memory_before.data(),memory_before.size());out.write(memory_after.data(),memory_after.size());
    }
    protect(pages[6],PAGE_READWRITE);std::memcpy(pages[6],pack.data()+12+6*4104+8,4096);protect(pages[6],PAGE_READONLY);
    for(unsigned i=0;i<15;++i)if(page_permissions[i]!=2)require(std::memcmp(pages[i],pack.data()+12+i*4104+8,4096)==0,"Protected original source changed");
    out.commit();std::cout<<mw34::m4_fp_sqrt_corpus::directed_records<<" actual original directed first FP records\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
