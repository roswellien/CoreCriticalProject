#pragma once
#include "provider.hpp"
#include "host_input.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>

#include <optional>
namespace mw34::m4_cmd_native {
enum class FaultReason { invalid_admission, source_changed, import_owner, memory, call_frame, reentry, host_input, partial_writer, unresolved_data, changed_buffer, poisoned };
struct Fault {FaultReason reason;GuestAddress site;const char*detail;};
struct Event {std::uint32_t pc,address,value,width,operation;};
struct Route {std::uint32_t target,return_pc,entry_esp,exit_esp;bool completed;};
// Separate typed provider import/data adapter. It never registers a fabricated
// game import in Runtime r9. Runtime must outlive the registry and its borrowers.
class Registry {
  public:
    explicit Registry(m4_runtime::Runtime&r):runtime_(r){}
    ~Registry();Registry(const Registry&)=delete;Registry&operator=(const Registry&)=delete;
    bool admit(std::span<const std::byte>provider,std::span<const std::byte>pack) noexcept;
    bool initialize(State&state) noexcept;
    std::optional<GuestAddress> resolve_data(GuestAddress slot) noexcept;
    [[nodiscard]] bool ready()const noexcept{return ready_&&!fault_;}
    [[nodiscard]] const std::optional<Fault>&first_fault()const noexcept{return fault_;}
    [[nodiscard]] GuestAddress owned_buffer()const noexcept{return buffer_;}
    [[nodiscard]] const HostInput&host_snapshot()const noexcept{return host_;}
    [[nodiscard]] const std::vector<Event>&events()const noexcept{return events_;}
    [[nodiscard]] const Route&route()const noexcept{return route_;}
    [[nodiscard]] const State&service_state_before()const noexcept{return service_before_;}
    [[nodiscard]] const State&service_state_after()const noexcept{return service_after_;}
    [[nodiscard]] std::uint32_t original_provider_iat()const noexcept{return provider_word_;}
    [[nodiscard]] std::uint32_t original_game_iat()const noexcept{return game_word_;}
    [[nodiscard]] bool compiled_capture_complete()const noexcept{return captured_;}
    [[nodiscard]] std::span<const std::byte,512> service_fx_before()const noexcept{return sf_before_;}
    [[nodiscard]] std::span<const std::byte,512> service_fx_after()const noexcept{return sf_after_;}
    [[nodiscard]] std::span<const std::byte,28> service_env_before()const noexcept{return se_before_;}
    [[nodiscard]] std::span<const std::byte,28> service_env_after()const noexcept{return se_after_;}
    std::uint32_t compiled_read32(std::uint32_t address) noexcept;
    bool compiled_write32(std::uint32_t address,std::uint32_t value) noexcept;
    bool compiled_service(State*state,std::uint32_t target) noexcept;
    bool compiled_capture(State*state,std::uint32_t target) noexcept;
    [[noreturn]] void abort_bridge();
  private:
    m4_runtime::Runtime&runtime_;State*state_{};std::optional<Fault>fault_;
    State service_before_{},service_after_{};
    bool admitted_{},entered_{},active_{},ready_{},captured_{},service_called_{},global_written_{},owns_buffer_{};
    std::array<bool,3>owns_pages_{};std::array<std::vector<std::byte>,3>original_pages_{};
    GuestAddress buffer_{};std::uint32_t provider_word_{},game_word_{},outer_esp_{};
    HostInput host_;std::vector<Event>events_;Route route_{};
    alignas(16)std::array<std::byte,512>sf_before_{},sf_after_{};std::array<std::byte,28>se_before_{},se_after_{};
    std::array<std::uint32_t,4>nonvolatile_{};
    void fault(FaultReason,GuestAddress,const char*) noexcept;
    void cleanup() noexcept;
    void integrity(bool initialized);
    void log(unsigned pc,unsigned address,unsigned value,unsigned width,unsigned operation);
    [[nodiscard]] const m4::ImportSymbol&game_owner()const;
};
}
