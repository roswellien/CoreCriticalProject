// Fresh shared ABI integration of frozen translated initializer components.
#include "../m4-initializer-chain/runtime_adapter.hpp"
#include "../m4-integer-startup/runtime_adapter.hpp"
#include "admission.hpp"
#include <iostream>
#include <fstream>
#include <iterator>
int main(int argc,char **argv){try{
    using namespace mw34::m4_runtime;
    if(argc!=6)throw std::runtime_error("Combined integer host: image chain-object chain-gate integer-object integer-gate");
    std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("Missing admitted image");
    std::vector<char> raw((std::istreambuf_iterator<char>(input)),{});auto runtime=Runtime::from_admitted_image(std::as_bytes(std::span{raw}));
    mw34::m4_initializer_chain::register_component(runtime,argv[2],argv[3]);mw34::m4_integer_startup::register_component(runtime,argv[4],argv[5]);runtime.freeze_registry();
    constexpr std::array<std::uint32_t,16> entries{0x410910,0x410940,0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4b5b20,0x4c7940,0x4cfef0};
    auto ledger=runtime.prepare_initializers({0x5e0000},{0x5e0244});if(ledger.items().size()!=145)throw std::runtime_error("Owned full table differs");
    const auto stack=runtime.cpu().esp;runtime.cpu().eax=0x13579bdf;runtime.cpu().ecx=0x76543210;runtime.cpu().edx=0xabcddcba;runtime.cpu().ebx=0x12345678;runtime.cpu().ebp=0x87654321;runtime.cpu().esi=0xf0f0a5a5;runtime.cpu().edi=0x0f0f5a5a;
    unsigned count{};
    for(const auto &item:ledger.items())if(count<entries.size()&&item.target.value==entries[count]){runtime.invoke(item.target);++count;}
    if(count!=16||runtime.calls().size()!=16||runtime.translation_count()!=16||ledger.completed()||ledger.failed())throw std::runtime_error("Actual selected16 dispatch/ledger differs");
    if(runtime.cpu().eax||runtime.cpu().ecx||runtime.cpu().edx||runtime.cpu().esp!=stack||runtime.cpu().eip!=Runtime::external_return)throw std::runtime_error("Actual combined volatile/return CPU differs");
    if(runtime.cpu().ebx!=0x12345678||runtime.cpu().ebp!=0x87654321||runtime.cpu().esi!=0xf0f0a5a5||runtime.cpu().edi!=0x0f0f5a5a)throw std::runtime_error("Actual combined nonvolatile CPU differs");
    for(const auto &call:runtime.calls())if(!call.completed)throw std::runtime_error("Actual combined call not complete");
    std::array<std::byte,4096> first{},second{},third{};runtime.memory().read({0x604000},first);runtime.memory().read({0x605000},second);runtime.memory().read({0x60b000},third);
    std::cout<<"{\"passed\":true,\"registered_roots\":16,\"actual_callbacks\":16,\"ledger_items\":145,\"selected_table_slots\":16,\"full_ledger_completed\":false,\"cpu_eax\":0,\"cpu_ecx\":0,\"cpu_edx\":0,\"cpu_esp\":"<<runtime.cpu().esp<<",\"cpu_eip\":"<<runtime.cpu().eip<<",\"defined_flags\":"<<(runtime.cpu().eflags&0xcc5)<<",\"604000_page_sha256\":\""<<mw34::m4::sha256(first)<<"\",\"605000_page_sha256\":\""<<mw34::m4::sha256(second)<<"\",\"60b000_page_sha256\":\""<<mw34::m4::sha256(third)<<"\",\"persistent_State_seeded\":"<<(runtime.remill_seeded()?"true":"false")<<"}\n";
    return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
