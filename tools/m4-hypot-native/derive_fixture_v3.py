"""Retain finite execution and measure final FSTP C1 with raw80 hardware."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
source=R/'tools/m4-hypot-native/fixture_v2.cpp'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='4f786aaf282193ba961209d73d86432187c13754be722e26cb9318d96f6f7a2a'
text=source.read_text()
old='extern "C" void *mw34_hypot_write_memory_f32(void*p,unsigned a,float v){return store(p,a,v);}'
assert text.count(old)==1
new=r'''struct FinalStoreProof {
    unsigned PC{}, address{};
    std::uint16_t actual_CW{}, actual_SW{};
    std::array<std::byte,10> input_raw80{};
    std::array<std::byte,4> lowered_F32{}, hardware_F32{};
};
extern "C" void *mw34_hypot_write_memory_f32(void*p,unsigned a,float v){
    auto &c=owner(p);
    if(c.s.gpr.rip.dword==0x4b5905){
        need(a==0x60b2e8,"Exact literal final FSTP source destination");
        FinalStoreProof proof{};proof.PC=c.s.gpr.rip.dword;proof.address=a;
        std::memcpy(proof.input_raw80.data(),reinterpret_cast<const std::byte*>(&c.s)+2486,10);
        std::memcpy(proof.lowered_F32.data(),&v,4);
        float measured;
        __asm__ volatile("fnstcw %2\n\tfldt %3\n\tfstps %0\n\tfnstsw %1"
            :"=m"(measured),"=m"(proof.actual_SW),"=m"(proof.actual_CW)
            :"m"(proof.input_raw80):"memory","st");
        need(proof.actual_CW==c.s.x87.fxsave.cwd.flat,"Source CW owns final raw80 conversion");
        std::memcpy(proof.hardware_F32.data(),&measured,4);
        need(proof.lowered_F32==proof.hardware_F32,"Actual lowered and hardware final F32 agree");
        // Intel SDM vol2 FST/FSTP: C1 records roundup when precision is
        // inexact. The compiler's earlier temporary operations cannot supply
        // this source bit. It is measured from the current source ST0 value.
        c.s.sw.c1=static_cast<unsigned char>((proof.actual_SW>>9)&1);
        dump("final-FSTP-proof.bin",&proof,sizeof(proof));
    }
    return store(p,a,v);
}'''
text=text.replace(old,new)
target=R/'tools/m4-hypot-native/fixture_v3.cpp'
assert not target.exists()
target.write_text(text)
print(hashlib.sha256(target.read_bytes()).hexdigest())
