#pragma once

#include "memory/guest_memory.hpp"

#include <cstdint>

namespace mw34::graphics {

using Hresult = std::uint32_t; // Preserve HRESULT bits; this game tests zero, not sign.

inline constexpr GuestAddress direct_draw_adapter_receiver{0x809644};
inline constexpr GuestAddress direct_draw4_global{0x809358};
inline constexpr GuestAddress direct_draw4_iid{0x5ce790};
inline constexpr GuestAddress video_error_file{0x5f0a5c};

struct ComMethod {
    GuestAddress object;
    GuestAddress target; // Guest vtable entry, never a host function pointer.
};

// Implementations must marshal guest addresses, preserve actual provider output
// writes (including on failure), and return actual status bits. No default or
// synthetic-success provider is supplied. These calls do not emulate CPU state.
class DirectDrawCreationProvider {
  public:
    virtual ~DirectDrawCreationProvider() = default;
    virtual Hresult direct_draw_create(GuestMemory &memory, GuestAddress adapter,
                                       GuestAddress output, GuestAddress outer) = 0;
    virtual Hresult query_interface(GuestMemory &memory, ComMethod method, GuestAddress iid,
                                    GuestAddress output) = 0;
    virtual std::uint32_t release(GuestMemory &memory, ComMethod method) = 0;
    virtual Hresult restore_display_mode(GuestMemory &memory, ComMethod method) = 0;
    virtual std::uint32_t report_error(Hresult status, GuestAddress file, std::uint32_t line) = 0;
};

// Functional boundary for 0x577D40. temporary_output is the caller-owned writable
// four-byte stack-local equivalent; it must not alias game state. Its initial
// contents are retained until the provider writes them. Throws/faults propagate.
// Does not run 0x576EE0, install callbacks, initialize surfaces, or report startup
// completion. The caller must supply the admitted image's GUID and receiver data.
[[nodiscard]] std::uint32_t create_direct_draw4(GuestMemory &memory,
                                                DirectDrawCreationProvider &provider,
                                                GuestAddress temporary_output);

// Functional boundary for 0x57893A..0x578954 ONLY. The caller must already have
// destroyed every dependent surface/device/texture/clipper/palette. This is not
// full 0x5788B0 cleanup. RestoreDisplayMode's result is ignored by the original;
// Release precedes clearing the global. Repeated calls with a zero global do nothing.
void release_direct_draw4_after_dependents(GuestMemory &memory,
                                           DirectDrawCreationProvider &provider);

} // namespace mw34::graphics
