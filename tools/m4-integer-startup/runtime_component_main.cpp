// Actual registry dispatch of selected owned CRT table roots, not a full startup.
#include "runtime_adapter.hpp"
#include "execution.hpp"
#include "admission.hpp"
#include <iostream>
using namespace mw34::m4_integer_startup;
int main(int argc,char **argv){try{
    require(argc==4,"Integer runtime component: image object-hash gate-hash");const auto raw=file_bytes(argv[1]);auto runtime=mw34::m4_runtime::Runtime::from_admitted_image(std::as_bytes(std::span{raw}));register_component(runtime,argv[2],argv[3]);runtime.freeze_registry();
    auto ledger=runtime.prepare_initializers({0x5e0000},{0x5e0244});require(ledger.items().size()==145,"Owned actual table size differs");
    const auto sp=runtime.cpu().esp;runtime.cpu().eax=0x13579bdf;runtime.cpu().ecx=0x76543210;runtime.cpu().edx=0xabcddcba;runtime.cpu().ebx=0x12345678;runtime.cpu().ebp=0x87654321;runtime.cpu().esi=0xf0f0a5a5;runtime.cpu().edi=0x0f0f5a5a;
    unsigned selected{};
    for(const auto &item:ledger.items())if(selected<14&&item.target.value==entries[selected]){runtime.invoke(item.target);++selected;}
    require(selected==14&&runtime.calls().size()==14&&runtime.translation_count()==14&&!ledger.completed()&&!ledger.failed(),"Actual selected14-root dispatch differs");
    require(runtime.cpu().eax==0&&runtime.cpu().ecx==0&&runtime.cpu().edx==0xabcddcba&&runtime.cpu().esp==sp&&runtime.cpu().eip==mw34::m4_runtime::Runtime::external_return,"Actual batch runtime volatile/return CPU differs");
    require(runtime.cpu().ebx==0x12345678&&runtime.cpu().ebp==0x87654321&&runtime.cpu().esi==0xf0f0a5a5&&runtime.cpu().edi==0x0f0f5a5a,"Actual batch runtime nonvolatile CPU differs");
    for(const auto &call:runtime.calls())require(call.completed,"Real callback failed");
    std::array<std::byte,4096> first{},second{};runtime.memory().read({global_base},first);runtime.memory().read({second_global_base},second);
    auto legacy=mw34::m4_runtime::Runtime::from_admitted_image(std::as_bytes(std::span{raw}));register_component(legacy,argv[2],argv[3]);legacy.freeze_registry();legacy.invoke({entries[0]});
    auto &state=*std::launder(reinterpret_cast<State *>(legacy.remill_state().data()));state.x87.fxsave.fop=0x123;state.x87.fxsave.ip=0x12345678;state.x87.fxsave.cs.flat=0x33;state.x87.fxsave.dp=0x87654321;state.x87.fxsave.ds.flat=0x2b;
    std::array<std::byte,18> metadata{},zero{};std::memcpy(metadata.data(),reinterpret_cast<std::byte *>(&state.x87)+6,metadata.size());legacy.invoke({entries[13]});
    require(std::memcmp(metadata.data(),reinterpret_cast<std::byte *>(&state.x87)+6,metadata.size())==0&&std::memcmp(legacy.fx().data()+6,zero.data(),zero.size())==0&&state.addr.fs_base.dword==legacy.fs_base().value,"Integer batch erased distinct legacy metadata/FS");
    std::cout<<"{\"passed\":true,\"actual_callbacks\":14,\"ledger_items\":145,\"selected_table_slots\":14,\"full_ledger_completed\":false,\"cpu_eax\":"<<runtime.cpu().eax<<",\"cpu_ecx\":"<<runtime.cpu().ecx<<",\"cpu_edx\":"<<runtime.cpu().edx<<",\"cpu_esp\":"<<runtime.cpu().esp<<",\"cpu_eip\":"<<runtime.cpu().eip<<",\"defined_flags\":"<<(runtime.cpu().eflags&0xcc5)<<",\"first_page_sha256\":\""<<mw34::m4::sha256(first)<<"\",\"second_page_sha256\":\""<<mw34::m4::sha256(second)<<"\",\"persistent_State_seeded\":true,\"legacy_metadata_preserved\":true,\"FX_metadata_distinct\":true,\"FS_base_preserved\":true}\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
