#pragma once

#include "image_loader.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <map>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::m4_runtime {

struct Cpu32 {
    std::uint32_t eax{}, ecx{}, edx{}, ebx{}, esp{}, ebp{}, esi{}, edi{};
    std::uint32_t eflags = 0x202;
    std::uint32_t eip{};
    friend bool operator==(const Cpu32 &, const Cpu32 &) = default;
};
static_assert(sizeof(Cpu32) == 40);

enum class Domain { authored_fixture, admitted_game, research_game };
enum class Abi { Cdecl, Stdcall, Thiscall, Internal };
struct AbiContract {
    Abi abi = Abi::Cdecl;
    std::uint32_t stack_argument_bytes{};
    bool preserve_nonvolatile = true;
};

enum class FaultReason {
    unresolved_translation, unresolved_import, invalid_binding, registry_frozen,
    memory_access, stack_bounds, abi_violation, poisoned, call_limit,
    unsupported_fs, invalid_seh_chain, unimplemented_seh_dispatch,
    heap_exhausted, invalid_allocation, initializer_changed, initializer_failed
};

class Fault : public std::runtime_error {
  public:
    Fault(FaultReason reason, GuestAddress site, GuestAddress target, std::string detail);
    [[nodiscard]] FaultReason reason() const noexcept { return reason_; }
    [[nodiscard]] GuestAddress site() const noexcept { return site_; }
    [[nodiscard]] GuestAddress target() const noexcept { return target_; }
  private:
    FaultReason reason_;
    GuestAddress site_, target_;
};
[[nodiscard]] const char *fault_name(FaultReason reason) noexcept;

struct Policy {
    GuestAddress stack_low{0x20000000};
    std::uint32_t stack_bytes = 1024 * 1024;
    GuestAddress heap_low{0x30000000};
    std::uint32_t heap_bytes = 16 * 1024 * 1024;
    GuestAddress teb{0x7ffde000};
    std::uint32_t max_call_depth = 64;
    std::uint32_t max_call_records = 65536;
};

class Runtime;
using NativeEntry = void (*)(Runtime &);

// Binding metadata is checked against the owned executable bytes. The native
// artifact/gate hashes identify reviewed static callbacks; the build/review must
// independently establish that callback-to-object association.
struct Evidence {
    Domain domain = Domain::authored_fixture;
    std::string image_sha256;
    std::uint32_t source_bytes{};
    std::string source_sha256;
    std::string native_artifact_sha256;
    std::string gate_report_sha256;
};
struct Translation {
    GuestAddress entry;
    AbiContract contract;
    NativeEntry native{};
    std::string name;
    Evidence evidence;
};
struct Service {
    GuestAddress iat_slot;
    AbiContract contract;
    NativeEntry native{};
    std::string name;
    Domain domain = Domain::authored_fixture;
    std::string provider_sha256;
    std::string gate_report_sha256;
};

// A native service's callback must return to its real provider instruction,
// not an invented address in the game. This admits data/identity and a route;
// it neither runs provider x86 nor resolves its dependencies/DllMain.
struct ServiceContinuation {
    GuestAddress code_start, call_pc, return_pc, service_iat_slot;
    std::uint32_t source_bytes{};
    Domain domain = Domain::authored_fixture;
    std::string provider_sha256, source_sha256;
    std::string native_artifact_sha256, gate_report_sha256, name;
};

struct CallRecord {
    GuestAddress site, target, return_pc;
    bool import{};
    bool completed{};
    std::string name;
};
struct SehRecord { GuestAddress frame, previous, handler; };
enum class InitializerStatus { pending, zero_sentinel, attempted, complete, fault };
struct InitializerItem {
    GuestAddress slot, target;
    InitializerStatus status = InitializerStatus::pending;
    std::string failure;
};

class InitializerLedger {
  public:
    InitializerLedger(const InitializerLedger &) = delete;
    InitializerLedger &operator=(const InitializerLedger &) = delete;
    InitializerLedger(InitializerLedger &&) = default;
    [[nodiscard]] const std::vector<InitializerItem> &items() const noexcept { return items_; }
    [[nodiscard]] std::size_t cursor() const noexcept { return cursor_; }
    [[nodiscard]] bool completed() const noexcept { return cursor_ == items_.size() && !failed_; }
    [[nodiscard]] bool failed() const noexcept { return failed_; }
  private:
    friend class Runtime;
    explicit InitializerLedger(Runtime *owner) : owner_(owner) {}
    Runtime *owner_;
    std::vector<InitializerItem> items_;
    std::size_t cursor_{};
    bool failed_{};
};

class Runtime {
  public:
    static constexpr std::uint32_t external_return = 0xfffffff0;
    static constexpr std::uint32_t seh_end = 0xffffffff;
    static constexpr std::size_t remill_state_bytes = 3504;

    // Actual-image construction copies and hash-admits input before loading.
    [[nodiscard]] static Runtime from_admitted_image(std::span<const std::byte> file,
                                                     const Policy &policy = {});
    // Exact experimental target identity; never grants the admitted MW3 domain.
    [[nodiscard]] static Runtime from_research_image(std::span<const std::byte> file,
                                                     const std::string &expected_sha256,
                                                     const Policy &policy = {});
    // This factory explicitly cannot register game translations/services.
    [[nodiscard]] static Runtime for_authored_fixture(m4::LoadedImage image,
                                                      const Policy &policy = {});
    Runtime(const Runtime &) = delete;
    Runtime &operator=(const Runtime &) = delete;
    Runtime(Runtime &&) = delete;
    Runtime &operator=(Runtime &&) = delete;

    [[nodiscard]] Domain domain() const noexcept { return domain_; }
    [[nodiscard]] Cpu32 &cpu() noexcept { return cpu_; }
    [[nodiscard]] const Cpu32 &cpu() const noexcept { return cpu_; }
    [[nodiscard]] GuestMemory &memory() noexcept { return image_.memory; }
    [[nodiscard]] const GuestMemory &memory() const noexcept { return image_.memory; }
    [[nodiscard]] const m4::ImageMetadata &image_metadata() const noexcept { return image_.metadata; }
    [[nodiscard]] std::span<std::byte, 512> fx() noexcept { return fx_; }
    [[nodiscard]] std::span<const std::byte, 512> fx() const noexcept { return fx_; }
    [[nodiscard]] std::span<std::byte, remill_state_bytes> remill_state() noexcept { return state_; }
    [[nodiscard]] bool remill_seeded() const noexcept { return remill_seeded_; }
    void mark_remill_seeded() noexcept { remill_seeded_ = true; }
    [[nodiscard]] GuestAddress fs_base() const noexcept { return policy_.teb; }
    [[nodiscard]] GuestAddress stack_low() const noexcept { return policy_.stack_low; }
    [[nodiscard]] GuestAddress stack_top() const noexcept { return stack_top_; }
    [[nodiscard]] const Policy &policy() const noexcept { return policy_; }
    [[nodiscard]] bool poisoned() const noexcept { return poisoned_; }
    [[nodiscard]] const std::vector<CallRecord> &calls() const noexcept { return calls_; }

    void register_translation(Translation translation);
    void register_service(Service service);
    void register_service_continuation(std::span<const std::byte> provider_image,
                                       ServiceContinuation continuation);
    [[nodiscard]] std::size_t service_continuation_count() const noexcept { return continuations_.size(); }
    void freeze_registry();
    [[nodiscard]] bool registry_frozen() const noexcept { return frozen_; }
    [[nodiscard]] std::size_t translation_count() const noexcept { return translations_.size(); }
    [[nodiscard]] std::size_t service_count() const noexcept { return services_.size(); }
    void call_direct(GuestAddress target, GuestAddress return_pc);
    void call_indirect(GuestAddress operand, GuestAddress return_pc);
    void call_import(GuestAddress slot, GuestAddress return_pc);
    void invoke(GuestAddress target);
    // Authored/service callbacks may use this helper. Remill adapters capture
    // their actual RET EIP/ESP instead; both paths face the same exit checks.
    void ret(std::uint32_t callee_pop_bytes = 0);

    [[nodiscard]] std::uint32_t fs_load32(std::uint32_t offset) const;
    void fs_store32(std::uint32_t offset, std::uint32_t value);
    [[nodiscard]] std::vector<SehRecord> seh_chain(std::uint32_t max_depth = 64) const;
    void seh_push(GuestAddress frame, GuestAddress handler);
    void seh_pop(GuestAddress frame);
    [[noreturn]] void dispatch_exception(std::uint32_t code, GuestAddress fault_address);

    // Bounded private arena, not an implementation of imported malloc/new/HeapAlloc.
    [[nodiscard]] GuestAddress heap_allocate(std::uint32_t bytes, std::uint32_t alignment = 16);
    void heap_release(GuestAddress address);
    [[nodiscard]] bool heap_allocation_live(GuestAddress address) const noexcept;

    [[nodiscard]] InitializerLedger prepare_initializers(GuestAddress begin, GuestAddress end);
    // External orchestration only. The real _initterm service/CRT ABI is still
    // required before this ledger can be called from a translated CRT entry.
    void run_initializers(InitializerLedger &ledger);

  private:
    Runtime(m4::LoadedImage image, Domain domain, const Policy &policy,
            std::string image_sha256 = {});
    struct Frame {
        GuestAddress target, return_pc;
        std::uint32_t caller_esp{}, expected_esp{};
    };
    struct ContinuationBinding {
        ServiceContinuation identity;
        std::vector<std::byte> original_code;
    };
    m4::LoadedImage image_;
    Domain domain_;
    Policy policy_;
    GuestAddress stack_top_;
    Cpu32 cpu_;
    std::array<std::byte, 512> fx_{};
    alignas(64) std::array<std::byte, remill_state_bytes> state_{};
    bool remill_seeded_{}, frozen_{};
    mutable bool poisoned_{};
    std::map<std::uint32_t, Translation> translations_;
    std::map<std::uint32_t, Service> services_;
    std::map<std::uint32_t, ContinuationBinding> continuations_;
    std::map<std::uint32_t, std::uint32_t> allocations_;
    std::uint32_t heap_cursor_{};
    std::vector<Frame> frames_;
    std::vector<CallRecord> calls_;
    std::string image_sha256_;
    [[noreturn]] void fail(FaultReason reason, GuestAddress target, const std::string &detail) const;
    void ready() const;
    [[nodiscard]] bool executable(GuestAddress address, std::uint32_t bytes = 1) const;
    [[nodiscard]] bool admitted_return_pc(GuestAddress address) const;
    [[nodiscard]] const m4::ImportSymbol *import_at(GuestAddress slot) const;
    void validate_contract(const AbiContract &contract, GuestAddress target) const;
    void call(NativeEntry native, const AbiContract &contract, GuestAddress target,
              GuestAddress return_pc, bool imported, const std::string &name);
    [[nodiscard]] bool stack_span(GuestAddress address, std::uint32_t bytes) const;
};

} // namespace mw34::m4_runtime
