#pragma once

#include "core/guest_address.hpp"

#include <cstdint>
#include <map>
#include <optional>
#include <string_view>

namespace mw34::mfc {

struct ModuleStateId {
    GuestAddress address;
    friend bool operator==(ModuleStateId, ModuleStateId) = default;
};
struct ThreadSlotId {
    GuestAddress address;
    friend bool operator==(ThreadSlotId, ThreadSlotId) = default;
};
struct AppReceiverId {
    GuestAddress address;
    friend bool operator==(AppReceiverId, AppReceiverId) = default;
};

inline constexpr std::string_view staged_mfc42_sha256 =
    "5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8";

enum class ProviderEvidence { controlled_fixture, unobserved };
struct ReceiverProviderIdentity {
    std::string_view image_sha256;
    ProviderEvidence evidence;
};

// Opaque transition ticket prevents completion of an earlier lifetime after address reuse.
class AppReceiverState;
class ConstructionTicket {
    friend class AppReceiverState;
    ConstructionTicket(const AppReceiverState *owner, std::uint64_t value)
        : owner_(owner), value_(value) {}
    const AppReceiverState *owner_;
    std::uint64_t value_;
};

// Controlled, sequential association model, not a translation of MFC constructors/destructors.
// IDs are guest addresses. Host TLS/TEB/SEH and provider factories are never consulted.
// No live-dispatch admission API exists while the provider/lifetime contract is incomplete.
// The host owns this model and serializes transitions. A ConstructionTicket belongs
// to exactly this instance and construction attempt; never persist it or infer lifetime
// from a reused guest address. Teardown invalidates associations, not guest memory.
class AppReceiverState {
  public:
    explicit AppReceiverState(ReceiverProviderIdentity provider);
    AppReceiverState(const AppReceiverState &) = delete;
    AppReceiverState &operator=(const AppReceiverState &) = delete;

    void initialize_module(ModuleStateId module);
    void initialize_thread(ThreadSlotId thread);
    void set_fallback(std::optional<ModuleStateId> module);
    // Returns the previous explicit selection (null means use the controlled fallback).
    std::optional<ModuleStateId> select_module(ThreadSlotId thread,
                                               std::optional<ModuleStateId> module);
    [[nodiscard]] std::optional<ModuleStateId> current_module(ThreadSlotId thread) const;

    // Capture the current owned module before construction. Completion publishes
    // only in that saved module; failure/teardown invalidates all its associations.
    [[nodiscard]] ConstructionTicket begin_construction(AppReceiverId receiver,
                                                        ThreadSlotId thread);
    void complete_construction(ConstructionTicket ticket);
    void fail_construction(ConstructionTicket ticket);
    void destroy_receiver(AppReceiverId receiver);
    // These tear down association metadata, not the underlying guest/provider
    // objects. Real destructors and callback lifetime admission are separate.
    void teardown_thread(ThreadSlotId thread);
    void teardown_module(ModuleStateId module);

    // Fixture-only callback-gate lookup: current module's +4 association, never a host pointer.
    [[nodiscard]] std::optional<AppReceiverId> lookup_receiver(ThreadSlotId thread) const;
    [[nodiscard]] std::optional<AppReceiverId> module_receiver(ModuleStateId module) const;
    [[nodiscard]] std::optional<AppReceiverId> thread_receiver(ThreadSlotId thread) const;
    [[nodiscard]] ModuleStateId saved_module(ConstructionTicket ticket) const;
    // Always refuses; lookup success is not provider, vtable, ABI or live callback admission.
    [[noreturn]] void require_live_dispatch() const;

  private:
    struct Module {
        std::optional<AppReceiverId> receiver; // Source-observed module-state +4.
    };
    struct Thread {
        std::optional<ModuleStateId> current;
        std::optional<AppReceiverId> receiver; // Source-observed thread-object +4.
    };
    struct Application {
        AppReceiverId receiver;
        ThreadSlotId thread;
        ModuleStateId module; // Source-observed receiver +0x1C.
        bool complete{};
    };
    void invalidate(std::uint64_t ticket);
    void validate_ticket(ConstructionTicket ticket) const;
    std::map<std::uint32_t, Module> modules_;
    std::map<std::uint32_t, Thread> threads_;
    std::map<std::uint64_t, Application> applications_;
    std::optional<ModuleStateId> fallback_;
    std::uint64_t next_ticket_{1};
};

} // namespace mw34::mfc
