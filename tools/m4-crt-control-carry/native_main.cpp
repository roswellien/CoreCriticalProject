// Isolated control wrapper followed by the exact selected26 initializer order.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "native_protocol.hpp"
#include "control_capture.hpp"
#include "spec.hpp"
#include "carry_bindings.hpp"
#include "../m4-initializer-chain/runtime_adapter.hpp"
#include "../m4-integer-startup/runtime_adapter.hpp"
#include "probe_io.hpp"
#include <iostream>
#include <memory>

namespace carry = mw34::m4_crt_control_carry;
namespace control = mw34::m4_crt_control_integration;
namespace original = mw34::m4_crt_control_carry_original;
namespace rt = mw34::m4_runtime;
using namespace mw34;
using namespace mw34::m4_crt_probe;

namespace mw34::m4_crt_control_carry {
thread_local Native *observation{};
void verify_current_fp_code(rt::Runtime &runtime) {
    for (const auto &binding : fp_bindings) if (binding.entry == runtime.cpu().eip) {
        std::vector<std::byte> bytes(binding.bytes);
        runtime.memory().read({binding.entry}, bytes);
        require(m4::sha256(bytes) == binding.code, "Carry FP original source changed after registration");
        return;
    }
    throw std::runtime_error("Missing current carry FP source binding");
}
}

namespace {
constexpr unsigned carry_original_stride = 92388;
void register_all(rt::Runtime &runtime) {
    using namespace rt;
    m4_initializer_chain::register_component(runtime, carry::chain_object, carry::chain_gate);
    m4_integer_startup::register_component(runtime, carry::integer_object, carry::integer_gate);
    for (const auto &b : carry::fp_bindings) runtime.register_translation({{b.entry}, {Abi::Cdecl,0,true}, b.native,
        "Carry actual FP initializer " + std::to_string(b.entry), {Domain::admitted_game,m4::admitted_image_hash,b.bytes,b.code,b.object,b.gate}});
    runtime.register_translation({{control::wrapper}, {Abi::Cdecl,0,true}, control::wrapper_adapter,
        "Carry actual control wrapper", {Domain::admitted_game,m4::admitted_image_hash,19,
        "ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac", carry::control_object,
        "2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a"}});
    runtime.register_service({{control::slot}, {Abi::Cdecl,8,true}, control::provider_adapter, "MSVCRT.dll!_controlfp",
        Domain::admitted_game,"2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7",
        "b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56"});
    runtime.freeze_registry();
}
void mount_provider(rt::Runtime &runtime, std::span<const std::uint8_t> pack) {
    for (unsigned i : {24U,25U}) {
        const auto offset = 12 + i * 4104;
        const auto address = control::get<unsigned>(pack.data() + offset);
        runtime.memory().map({address},4096,Permissions::read|Permissions::write);
        runtime.memory().write({address},std::as_bytes(pack.subspan(offset+8,4096)));
        runtime.memory().protect({address},Permissions::read|Permissions::execute);
    }
}
State &seed_before_only(rt::Runtime &runtime, const std::uint8_t *row, unsigned sequence) {
    carry::Cpu cpu{};
    std::memcpy(&cpu,row+36,40);
    need(cpu.pc == control::wrapper && cpu.gpr[4] == carry::frame, "Actual initial original control CPU required");
    auto *state = std::construct_at(reinterpret_cast<State *>(runtime.remill_state().data()));
    control::Cpu c{cpu.gpr[0],cpu.gpr[1],cpu.gpr[2],cpu.gpr[3],cpu.gpr[4],cpu.gpr[5],cpu.gpr[6],cpu.gpr[7],cpu.flags,cpu.pc};
    // Actual first-phase original BEFORE fields seed the single persistent State.
    control::initialize(*state,c,row+116,row+2164,sequence);
    state->seg.cs.flat=0x23;state->seg.ds.flat=0x2b;state->seg.ss.flat=0x2b;
    std::memcpy(runtime.fx().data(),row+116,512);
    runtime.mark_remill_seeded();
    constexpr unsigned memory_before=2276;
    for (unsigned i=0;i<carry::pages.size()-1;++i) {
        std::array<std::byte,4096> bytes{};
        runtime.memory().read({carry::pages[i]},bytes);
        need(std::memcmp(bytes.data(),row+memory_before+i*4096,4096)==0,"Actual image initial page identity required before numerical execution");
    }
    runtime.memory().write({0x20001000},std::as_bytes(std::span{row+memory_before+10*4096,4096}));
    runtime.cpu()=control::cpu_view(*state);
    runtime.cpu().esp+=4;runtime.cpu().eip=0x5ac431;
    return *state;
}
void routes(carry::CarryNative &record, const rt::Runtime &runtime, std::size_t before) {
    const auto count=runtime.calls().size()-before;
    need(count<=2,"Actual carry runtime route extent rejected");
    record.Runtime_call_count=static_cast<unsigned>(count);
    for(unsigned i=0;i<count;++i) {
        const auto &c=runtime.calls()[before+i];
        record.Runtime_routes[i]={c.site.value,c.target.value,c.return_pc.value,c.import?1U:0U,c.completed?1U:0U,static_cast<unsigned>(before+i)};
        need(c.completed,"Actual carry route incomplete");
    }
}
}

int main(int argc,char **argv) {try {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc==2&&std::string(argv[1])=="--layout") {
        std::cout<<"{\"record_size\":104808,\"original_size\":92388,\"State_size\":3504,\"sequences\":24,\"phases\":648,\"full_CRT_executed\":false}\n";return 0;
    }
    need(argc==6,"Carry native: exact-image exact-provider exact-pack exact-original fresh-output");
    auto image=read(argv[1],2384384),provider=read(argv[2],266293),pack=read(argv[3],106716),raw=read(argv[4],60000000);
    need(image.size()==2384384&&digest(image)==m4::admitted_image_hash,"Exact carry image required");
    need(provider.size()==266293&&digest(provider)==original::provider_sha,"Exact carry provider required");
    need(pack.size()==original::pack_size&&digest(pack)==original::pack_sha,"Exact carry pack required");
    need(digest(raw)==carry::original_raw_sha,"Exact actual carry original stream required");
    need(raw.size()==32+648*carry_original_stride&&std::memcmp(raw.data(),"MW4CCO01",8)==0,"Complete actual original carry stream required");
    const std::array<unsigned,6> expected_header{1,24,27,648,11,92388};
    need(std::memcmp(raw.data()+8,expected_header.data(),24)==0,"Exact original carry header");
    Output output(argv[5]);output.write("MW4CCN01",8);
    const std::array<unsigned,6> header{1,24,27,648,11,sizeof(carry::CarryNative)};output.write(header.data(),24);
    for(unsigned sequence=0;sequence<24;++sequence) {
        rt::Policy policy{};policy.stack_low={0x20001000};policy.stack_bytes=4096;
        auto runtime=rt::Runtime::from_admitted_image(std::as_bytes(std::span{image}),policy);
        mount_provider(runtime,pack);
        const auto initial=raw.data()+32+sequence*27*carry_original_stride;
        auto &state=seed_before_only(runtime,initial,sequence);
        register_all(runtime);
        control::Context context(runtime,state);control::SerialOwner owner(context);
        auto ledger=runtime.prepare_initializers({0x5e0000},{0x5e0244});need(ledger.items().size()==145,"Actual full initializer table snapshot required");
        const auto incoming_cw=control::get<unsigned>(initial+20);
        unsigned phase{};
        auto run=[&](unsigned entry,unsigned table_slot) {
            carry::CarryNative record{};record.initial_CW=incoming_cw;
            auto &c=record.phase.common;
            c.sequence=sequence;c.repeat=sequence/12;c.phase=phase;c.table_slot=table_slot;c.entry=entry;c.cw=incoming_cw;c.initial_top=0;
            carry::observation=&record.phase;
            std::memcpy(record.runtime_fx_before.data(),runtime.fx().data(),512);
            const auto count=runtime.calls().size();
            try {
                if(!phase) {
                    carry::snapshot(runtime,state,true);
                    control::HostScope host;
                    runtime.call_direct({control::wrapper},{control::outer_return});
                    host.capture();carry::host(host.before.bytes,host.after.bytes,host.env,host.env_after);
                    carry::snapshot(runtime,state,false);
                    need(context.count==13&&!context.depth&&!context.boundary_depth&&!context.failed,"Actual persistent control route closure");
                    record.control_count=context.count;
                    for(unsigned i=0;i<context.count;++i)record.control_events[i]={context.events[i].kind,context.events[i].pc,context.events[i].esp,context.events[i].return_pc};
                    record.phase.state_seeded=runtime.remill_seeded();
                } else runtime.call_direct({entry},{carry::broker});
            } catch(...) {
                carry::observation=nullptr;
                // Keep the genuine completed prefix as failed evidence. Its
                // header still declares the full intended648-phase domain.
                output.commit();
                throw;
            }
            carry::observation=nullptr;
            need(c.host_restored&&record.phase.state_seeded&&!record.phase.domain_error,"Actual carry callback/host observation closure");
            std::memcpy(record.runtime_fx_after.data(),runtime.fx().data(),512);
            routes(record,runtime,count);
            output.write(&record,sizeof(record));++phase;
        };
        run(control::wrapper,0);
        unsigned selected{};
        for(const auto &item:ledger.items())if(std::find(carry::entries.begin(),carry::entries.end(),item.target.value)!=carry::entries.end()) {run(item.target.value,item.slot.value);++selected;}
        need(phase==27&&selected==26&&runtime.calls().size()==28&&runtime.translation_count()==27&&runtime.service_count()==1&&!ledger.completed()&&!ledger.failed(),"Actual bounded27-phase order/routing extent");
    }
    output.commit();std::cout<<"648 actual control+selected26 phases; persistent observed CW/CPU/State/FX/ENV/pages; comparison/independent review pending; full CRT false\n";
    return 0;
}catch(const std::exception &error) {std::cerr<<error.what()<<'\n';return 1;}}
