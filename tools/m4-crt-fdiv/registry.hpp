#pragma once
#include "provider.hpp"
#include "host_services.hpp"
#include "fnclex.hpp"
#include "guest_cw.hpp"
#include <optional>
namespace mw34::m4_crt_fdiv {
enum class FaultReason{invalid_admission,memory,source_changed,state_domain,call_frame,import_owner,dynamic_route,host_service,unsupported_fallback,poisoned};
struct Fault{FaultReason reason;unsigned pc,address;const char*detail;};
struct Event{unsigned kind,pc,address,value,width;};
struct Frame{unsigned entry,esp,return_pc;std::array<unsigned,4>nonvolatile;};
struct ServiceRoute{unsigned site,target,return_pc,entry_esp,exit_esp,argument_bytes;bool complete;};
class Registry{
    friend struct RegistryControlProbe; // Authored unit fixtures, never game-slot admission.
  public:
    explicit Registry(m4_runtime::Runtime&runtime);
    ~Registry();Registry(const Registry&)=delete;Registry&operator=(const Registry&)=delete;
    bool admit(std::span<const std::byte>provider,std::span<const std::byte>pack)noexcept;
    bool initialize()noexcept;
    std::optional<GuestAddress>resolve_data(GuestAddress slot)noexcept;
    [[nodiscard]] bool ready()const noexcept{return ready_&&!fault_;}
    [[nodiscard]] const std::optional<Fault>&first_fault()const noexcept{return fault_;}
    [[nodiscard]] const std::vector<Event>&events()const noexcept{return events_;}
    [[nodiscard]] const std::vector<ServiceRoute>&routes()const noexcept{return routes_;}
    [[nodiscard]] const std::vector<LookupRecord>&lookups()const noexcept{return lookups_;}
    [[nodiscard]] const auto&host_before()const noexcept{return host_before_;}
    [[nodiscard]] const auto&host_after()const noexcept{return host_after_;}
    [[nodiscard]] const auto&host_env_before()const noexcept{return env_before_;}
    [[nodiscard]] const auto&host_env_after()const noexcept{return env_after_;}
    [[nodiscard]] unsigned original_game_word()const noexcept{return game_word_;}
    unsigned read32(unsigned address);
    void write32(unsigned address,unsigned value);
    void enter(State*state,unsigned pc);
    void returned(State*state,unsigned pc);
    void service(State*state,unsigned target);
    void fnclex(State*state,unsigned pc);
    void wait(State*state,unsigned pc);
    void store_cw(State*state,unsigned address);
    void load_cw(State*state,unsigned address);
    [[noreturn]]void unsupported(State*state,unsigned pc);
  private:
    m4_runtime::Runtime&runtime_;State&state_;m4_guest_cw::Context cw_;HostServices host_;
    std::optional<Fault>fault_;unsigned thread_{},game_word_{},pointer_writes_{};bool admitted_{},entered_{},active_{},ready_{},flag_written_{},cleared_{};
    std::array<bool,7>owned_{};std::array<std::vector<std::byte>,7>pages_{};std::vector<Frame>frames_;
    std::vector<Event>events_;std::vector<ServiceRoute>routes_;std::vector<LookupRecord>lookups_;
    alignas(16)std::array<std::byte,512>host_before_{},host_after_{};std::array<std::byte,28>env_before_{},env_after_{};
    [[noreturn]]void deny(FaultReason,unsigned,const char*);
    void cleanup()noexcept;
    void integrity();
    void identity(State*,unsigned);
    void domain();
    void event(unsigned,unsigned,unsigned,unsigned,unsigned);
    [[nodiscard]] bool stack(unsigned,unsigned)const;
    [[nodiscard]] std::array<unsigned,4>nonvolatile()const;
    [[nodiscard]] const m4::ImportSymbol&game_owner()const;
};
}
