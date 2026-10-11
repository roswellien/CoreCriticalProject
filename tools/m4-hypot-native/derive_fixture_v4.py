"""Add actual guarded causal refusals and unchanged poisoned-context retries."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
BASE=R/'tools/m4-hypot-native/fixture_v3.cpp'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='539cfa327573ff8e6b163cf1f6e58dbe5428df2e6fb39af9564e335270834df9'
text=BASE.read_text()
changes=[
 ('static thread_local Context *active{};', 'static thread_local Context *active{};\nstatic unsigned control_mode{};static bool control_fired{};static std::string refusal;\nstatic bool fire(unsigned n){if(control_mode==n&&!control_fired){control_fired=true;return true;}return false;}'),
 ('authority(); need(cursor < hf::accesses.size()', 'authority(); if(fire(2))++n; need(cursor < hf::accesses.size()'),
 ('authority(); r.memory().read({a},value); access(a,unsigned(value.size()),false,value);', 'authority();if(fire(1))a+=4;if(fire(3))s.gpr.rip.dword^=1; r.memory().read({a},value); access(a,unsigned(value.size()),false,value);'),
 ('authority(); need(s.gpr.rip.dword == pc,', 'authority(); if(call&&fire(4))pc+=1; need(s.gpr.rip.dword == pc,'),
 ('authority(); need(!frames.empty() && frames.back().ret == pc,', 'authority();if(fire(8))pc+=4; need(!frames.empty() && frames.back().ret == pc,'),
 ('extern "C" void mw34_hypot_control_admit(State *s, void *p) { need(&owner(p).s == s, "Exact control State identity"); }', 'extern "C" void mw34_hypot_control_admit(State *s, void *p) { auto &c=owner(p);if(fire(5))c.s.x87.fxsave.cwd.flat^=0x400;if(fire(6))s=reinterpret_cast<State*>(reinterpret_cast<std::byte*>(s)+8);need(&c.s==s,"Exact control State identity"); }'),
 ('extern "C" unsigned mw34_hypot_fpu_exception_test(unsigned mask){need(active&&mask==127,', 'extern "C" unsigned mw34_hypot_fpu_exception_test(unsigned mask){if(fire(7))mask=126;need(active&&mask==127,'),
 ('need(argc==6,"image BEFORE-pack CPU/FX/ENV six-input file sequence fresh-output");', 'need(argc==6||argc==7,"image BEFORE-pack CPU/FX/ENV six-input file sequence fresh-output [control]");control_mode=argc==7?unsigned(std::stoul(argv[6])):0;need(control_mode<=8,"Finite numeric control catalog");'),
 ('Context c(r,pages,seq);r.invoke({0x4b5910});need(c.complete&&r.calls().size()==1&&r.calls()[0].completed&&!r.poisoned(),"Actual registered native Runtime completed");', 'Context c(r,pages,seq);alignas(16)std::array<std::byte,1632> boundary{};hypot_hardware_call(&r,boundary.data());dump("host-hardware.bin",boundary.data(),boundary.size());if(!control_mode)need(c.complete&&r.calls().size()==1&&r.calls()[0].completed&&!r.poisoned(),"Actual registered native Runtime completed");else need(control_fired&&!refusal.empty()&&r.poisoned()&&!c.complete&&!active,"Actual refused numeric context cleaned");const std::array<unsigned,5> status{control_mode,unsigned(control_fired),unsigned(r.poisoned()),unsigned(c.complete),unsigned(active==nullptr)};dump("result/status.bin",status.data(),sizeof(status));dump("result/refusal.txt",refusal.data(),refusal.size());'),
]
for old,new in changes:
    assert text.count(old)==1,old
    text=text.replace(old,new)
anchor='int main(int argc,char **argv) {'
assert text.count(anchor)==1
guard=r'''extern "C" void hypot_hardware_call(Runtime*,void*);
extern "C" void hypot_invoke_guarded(Runtime *r){
    auto &c=owner(active);
    try{r->invoke({0x4b5910});need(!control_mode,"Finite numeric control unexpectedly succeeded");}
    catch(const std::exception &e){
        refusal=e.what();need(control_mode&&control_fired&&r->poisoned()&&!c.complete,"Actual finite numeric poisoned refusal");
        auto checkpoint=[&](const std::string &stem){
            c.checkpoint(stem.c_str());dump(stem+"/RuntimeCPU.bin",&r->cpu(),40);
            dump(stem+"/RuntimeFX.bin",r->fx().data(),512);
            dump(stem+"/accesses.bin",c.accesses.data(),c.accesses.size()*sizeof(Access));
            dump(stem+"/frames.bin",c.frames.data(),c.frames.size()*sizeof(Frame));
            dump(stem+"/APIs.bin",c.APIs.data(),sizeof(c.APIs));
            std::vector<unsigned>routes;for(const auto &v:r->calls())routes.insert(routes.end(),{v.site.value,v.target.value,v.return_pc.value,unsigned(v.import),unsigned(v.completed)});
            dump(stem+"/routes.bin",routes.data(),routes.size()*4);
            const std::array<std::uint64_t,16> private_state{c.sequence,c.cursor,c.tests,c.clears,c.primitives,c.returns,c.thread,unsigned(c.entered),unsigned(c.complete),c.API_count,c.accesses.size(),c.frames.size(),reinterpret_cast<std::uintptr_t>(active),reinterpret_cast<std::uintptr_t>(&c),reinterpret_cast<std::uintptr_t>(&c.s),reinterpret_cast<std::uintptr_t>(&c.r)};
            dump(stem+"/context.bin",private_state.data(),sizeof(private_state));
        };
        checkpoint("retry/before");bool denied=false;
        try{r->invoke({0x4b5910});}catch(const Fault &f){denied=f.reason()==FaultReason::poisoned;}
        need(denied,"Same actual poisoned numeric Runtime retry refused");checkpoint("retry/after");
        active=nullptr;
    }
}
'''
text=text.replace(anchor,guard+anchor)
target=R/'tools/m4-hypot-native/fixture_v5.cpp';assert not target.exists();target.write_text(text)
hardware=(R/'tools/m4-mfc1168-native/hardware_boundary.s').read_text()
assert hardware.count('mfc_hardware_call')==3 and hardware.count('mfc_invoke_guarded')==1
hardware=hardware.replace('mfc_hardware_call','hypot_hardware_call').replace('mfc_invoke_guarded','hypot_invoke_guarded')
target=R/'tools/m4-hypot-native/hardware_boundary.s';assert not target.exists();target.write_text(hardware)
print(hashlib.sha256(text.encode()).hexdigest())
