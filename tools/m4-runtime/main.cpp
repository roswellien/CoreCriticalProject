#include "runtime.hpp"
#include "admission.hpp"
#include <algorithm>
#include <iostream>
#include <string>

// Minimal admission/inspection host, not the integrated playable launcher.
// No translations or services are registered here: --startup/--initializers
// deliberately exercise visible rejection of an unresolved required route.
// --inspect reads admitted local data and reports metadata without invoking it.

using namespace mw34;
using namespace mw34::m4_runtime;

int main(int argc, char **argv) {
    try {
        if (argc != 3 ||
            (std::string(argv[1]) != "--inspect" && std::string(argv[1]) != "--startup" &&
             std::string(argv[1]) != "--initializers")) {
            std::cerr
                << "Usage: mw34_m4_runtime_host --inspect|--startup|--initializers admitted-image\n";
            return 2;
        }
        const auto file = m4::read_image(argv[2]);
        auto runtime = Runtime::from_admitted_image(file);
        auto main_ledger =
            runtime.prepare_initializers(GuestAddress{0x5e0000}, GuestAddress{0x5e0244});
        auto early_ledger =
            runtime.prepare_initializers(GuestAddress{0x5e0248}, GuestAddress{0x5e024c});
        const auto nonzero = std::count_if(main_ledger.items().begin(), main_ledger.items().end(),
                                           [](const auto &item) { return item.target.value != 0; });
        runtime.freeze_registry();
        if (std::string(argv[1]) == "--startup") {
            runtime.invoke(runtime.image_metadata().entry_point);
            throw std::runtime_error("Unregistered CRT entry unexpectedly returned");
        }
        if (std::string(argv[1]) == "--initializers") {
            runtime.run_initializers(early_ledger);
            runtime.run_initializers(main_ledger);
            throw std::runtime_error("Unregistered required initializer unexpectedly completed");
        }
        std::cout << "{\"schema_version\":1,\"domain\":\"admitted_game\","
                  << "\"image_sha256\":\"" << m4::admitted_image_hash << "\","
                  << "\"entry\":" << runtime.image_metadata().entry_point.value << ','
                  << "\"imports\":" << runtime.image_metadata().imports.size() << ','
                  << "\"initializer_slots\":" << main_ledger.items().size() << ','
                  << "\"nonzero_initializers\":" << nonzero << ','
                  << "\"early_initializer_slots\":" << early_ledger.items().size() << ','
                  << "\"translations\":" << runtime.translation_count() << ','
                  << "\"services\":" << runtime.service_count() << ','
                  << "\"guest_esp\":" << runtime.cpu().esp << ','
                  << "\"guest_fs_base\":" << runtime.fs_base().value << ','
                  << "\"guest_exception_head\":" << runtime.fs_load32(0) << ','
                  << "\"guest_stack_base\":" << runtime.fs_load32(4) << ','
                  << "\"guest_stack_limit\":" << runtime.fs_load32(8) << ','
                  << "\"guest_tib_self\":" << runtime.fs_load32(0x18) << ','
                  << "\"remill_state_bytes\":" << runtime.remill_state().size() << ','
                  << "\"remill_state_seeded\":false,\"guest_code_executed\":false,"
                  << "\"CRT_SEH_MFC_startup_complete\":false,\"native_menus_complete\":false}\n";
        return 0;
    } catch (const Fault &error) {
        std::cerr << error.what() << '\n';
        return 3;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
