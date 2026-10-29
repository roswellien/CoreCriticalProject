#pragma once
#include "runtime.hpp"

namespace mw34::m4_crt {
using namespace m4_runtime;
struct Slots {
    GuestAddress initterm{0x5bb510},set_app_type{0x5bb5a4},p_fmode{0x5bb57c},p_commode{0x5bb504};
};
struct Proof { Domain domain=Domain::authored_fixture;std::string native_artifact_sha256,gate_report_sha256; };
enum class VisitStatus { null_slot,attempted,completed,fault };
struct InitializerVisit {GuestAddress slot,target;VisitStatus status;std::string failure;};

// Native service model for four exact staged CRT bodies. Services are admitted
// only through explicit proof/domain, never by a host DLL pointer. The owner
// must outlive all calls and is confined to its creating host thread.
class Session {
  public:
    static constexpr std::uint32_t provider_app_type=0x78038ee8,provider_fmode=0x78038eec,provider_commode=0x78038ef0;
    static constexpr std::uint32_t max_initializer_visits=4096;
    Session(Runtime &runtime,std::span<const std::byte> provider,const Proof &proof={},const Slots &slots={});
    ~Session();
    Session(const Session&)=delete;Session&operator=(const Session&)=delete;
    Session(Session&&)=delete;Session&operator=(Session&&)=delete;
    [[nodiscard]] const std::vector<InitializerVisit>& visits() const noexcept{return visits_;}
  private:
    Runtime &runtime_;Slots slots_;std::vector<InitializerVisit> visits_;bool owns_globals_{};
    static Session& owner(Runtime &runtime);
    static void initterm(Runtime &runtime);
    static void set_app_type(Runtime &runtime);
    static void p_fmode(Runtime &runtime);
    static void p_commode(Runtime &runtime);
};
} // namespace mw34::m4_crt
