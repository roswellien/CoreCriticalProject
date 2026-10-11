#include "graphics/direct_draw_creation.hpp"

namespace mw34::graphics {
namespace {

ComMethod method_at(GuestMemory &memory, GuestAddress object, std::uint32_t offset) {
    const GuestAddress table{memory.load<std::uint32_t>(object)};
    return {object, GuestAddress{memory.load<std::uint32_t>(table.wrapping_add(offset))}};
}

} // namespace

std::uint32_t create_direct_draw4(GuestMemory &memory, DirectDrawCreationProvider &provider,
                                  GuestAddress temporary_output) {
    const GuestAddress receiver{memory.load<std::uint32_t>(direct_draw_adapter_receiver)};
    const GuestAddress adapter{memory.load<std::uint32_t>(receiver)};
    const Hresult creation = provider.direct_draw_create(memory, adapter, temporary_output, {0});
    if (creation != 0) {
        return provider.report_error(creation, video_error_file, 0x3bb);
    }

    const GuestAddress temporary{memory.load<std::uint32_t>(temporary_output)};
    const Hresult query = provider.query_interface(memory, method_at(memory, temporary, 0),
                                                   direct_draw4_iid, direct_draw4_global);
    if (query != 0) {
        // The recovered QI failure path reports and returns without Release.
        return provider.report_error(query, video_error_file, 0x3bf);
    }

    // Reread both the output and vtable, as at 0x577D97..0x577D9E.
    const GuestAddress completed{memory.load<std::uint32_t>(temporary_output)};
    (void)provider.release(memory, method_at(memory, completed, 8));
    return 0;
}

void release_direct_draw4_after_dependents(GuestMemory &memory,
                                           DirectDrawCreationProvider &provider) {
    const GuestAddress object{memory.load<std::uint32_t>(direct_draw4_global)};
    if (object.value == 0) {
        return;
    }
    (void)provider.restore_display_mode(memory, method_at(memory, object, 0x4c));
    const GuestAddress restored{memory.load<std::uint32_t>(direct_draw4_global)};
    (void)provider.release(memory, method_at(memory, restored, 8));
    memory.store<std::uint32_t>(direct_draw4_global, 0);
}

} // namespace mw34::graphics
