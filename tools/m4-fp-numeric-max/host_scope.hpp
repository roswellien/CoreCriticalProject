#pragma once
namespace mw34::m4_numeric_max {
struct FpuScope {
    struct alignas(16) Image {std::uint8_t bytes[512];} saved;
    std::uint8_t env[28];
    explicit FpuScope(std::uint16_t cw){
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfninit\n\tfldcw %2":"=m"(saved),"=m"(env):"m"(cw):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");
        const std::uint32_t mxcsr=0x1f80;__asm__ volatile("ldmxcsr %0"::"m"(mxcsr):"memory");
    }
    void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(saved),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
    bool restored(Record &r){
        Image after;std::uint8_t after_env[28];
        __asm__ volatile("fxrstor64 %2\n\tfldenv %3\n\tfxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(after_env):"m"(saved),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
        std::memcpy(r.host_fx_before.data(),saved.bytes,512);std::memcpy(r.host_fx_after.data(),after.bytes,512);
        std::memcpy(r.host_env_before.data(),env,28);std::memcpy(r.host_env_after.data(),after_env,28);
        if(std::memcmp(saved.bytes,after.bytes,5)||std::memcmp(saved.bytes+24,after.bytes+24,4)||std::memcmp(env,after_env,28))return false;
        for(unsigned i=0;i<8;++i)if(std::memcmp(saved.bytes+32+i*16,after.bytes+32+i*16,10))return false;
        return std::memcmp(saved.bytes+160,after.bytes+160,256)==0;
    }
    ~FpuScope(){restore();}
};
}
