// Shared-runtime integration control. Page/CPU observations come from actual
// compiled callbacks; this host never supplies a game implementation or menu.
#include "runtime_adapter.hpp"
#include "protocol.hpp"
#include "admission.hpp"
#include "execution.hpp"
#include <iostream>
using namespace mw34::m4_initializer_chain;
int main(int argc,char **argv) {
    try {
        require(argc==4,"Runtime component: image object-sha256 gate-report-sha256");
        auto raw=file_bytes(argv[1]);
        auto runtime=mw34::m4_runtime::Runtime::from_admitted_image(std::as_bytes(std::span{raw}));
        register_component(runtime,argv[2],argv[3]);runtime.freeze_registry();
        const auto stack=runtime.cpu().esp;
        runtime.cpu().eax=0x13579bdf;runtime.cpu().ecx=0x76543210;runtime.cpu().edx=0xabcddcba;
        runtime.cpu().ebx=0x12345678;runtime.cpu().ebp=0x87654321;runtime.cpu().esi=0xf0f0a5a5;runtime.cpu().edi=0x0f0f5a5a;
        auto ledger=runtime.prepare_initializers({0x5e0000},{0x5e0244});
        require(ledger.items().size()==145&&ledger.items()[22].slot.value==0x5e0058&&ledger.items()[22].target.value==preceding_entry
                &&ledger.items()[23].slot.value==0x5e005c&&ledger.items()[23].target.value==entry,"Owned recovered initializer table differs");
        runtime.invoke(ledger.items()[22].target);runtime.invoke(ledger.items()[23].target);
        require(!ledger.completed()&&!ledger.failed(),"Selected dispatch incorrectly completed full initializer ledger");
        require(runtime.translation_count()==2&&runtime.calls().size()==2&&runtime.calls()[0].completed&&runtime.calls()[1].completed,"Shared registry did not route both actual callbacks");
        require(runtime.cpu().esp==stack&&runtime.cpu().eax==0x604100&&runtime.cpu().ecx==0x6040d0&&runtime.cpu().edx==0,"Shared actual volatile/return CPU differs");
        require(runtime.cpu().ebx==0x12345678&&runtime.cpu().ebp==0x87654321&&runtime.cpu().esi==0xf0f0a5a5&&runtime.cpu().edi==0x0f0f5a5a,"Shared nonvolatile CPU failed");
        std::array<std::byte,4096> page{};runtime.memory().read({global_base},page);
        const auto page_hash=mw34::m4::sha256(page);
        // FXSAVE pointer bytes and persistent legacy environment fields are
        // distinct observations on this host. Exercise both compiled callbacks
        // on a second owned image without erasing legacy metadata between them.
        auto legacy=mw34::m4_runtime::Runtime::from_admitted_image(std::as_bytes(std::span{raw}));
        register_component(legacy,argv[2],argv[3]);legacy.freeze_registry();legacy.invoke({preceding_entry});
        auto &state=*std::launder(reinterpret_cast<State *>(legacy.remill_state().data()));
        state.x87.fxsave.fop=0x123;state.x87.fxsave.ip=0x12345678;state.x87.fxsave.cs.flat=0x33;
        state.x87.fxsave.dp=0x87654321;state.x87.fxsave.ds.flat=0x2b;
        std::array<std::byte,18> metadata{};std::memcpy(metadata.data(),reinterpret_cast<std::byte *>(&state.x87)+6,metadata.size());
        const auto fx_before=std::array<std::byte,18>{};
        require(std::memcmp(legacy.fx().data()+6,fx_before.data(),fx_before.size())==0,"Runtime FX initial metadata domain changed");
        legacy.invoke({entry});
        require(std::memcmp(metadata.data(),reinterpret_cast<std::byte *>(&state.x87)+6,metadata.size())==0,"Integer callback erased persistent legacy metadata");
        require(std::memcmp(legacy.fx().data()+6,fx_before.data(),fx_before.size())==0,"Integer callback conflated FX with legacy metadata");
        require(state.addr.fs_base.dword==legacy.fs_base().value,"Integer callback erased persistent FS base");
        std::cout<<"{\"passed\":true,\"actual_callbacks\":2,\"ledger_items\":145,\"selected_table_slots\":2,\"full_ledger_completed\":false,\"cpu_eax\":"<<runtime.cpu().eax
                 <<",\"cpu_ecx\":"<<runtime.cpu().ecx<<",\"cpu_edx\":"<<runtime.cpu().edx<<",\"cpu_esp\":"<<runtime.cpu().esp
                 <<",\"cpu_eip\":"<<runtime.cpu().eip<<",\"cpu_flags\":"<<runtime.cpu().eflags
                 <<",\"page_sha256\":\""<<page_hash<<"\",\"persistent_State_seeded\":"<<(runtime.remill_seeded()?"true":"false")
                 <<",\"legacy_metadata_preserved\":true,\"FX_metadata_distinct\":true,\"FS_base_preserved\":true}\n";
        return 0;
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
