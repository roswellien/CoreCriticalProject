#include "runtime.hpp"
#include "admission.hpp"
#include "service_provider.hpp"

#include <algorithm>
#include <iomanip>
#include <limits>
#include <sstream>
#include <utility>

namespace mw34::m4_runtime {
namespace {
bool hash_string(const std::string &text) {
    return text.size() == 64 && std::all_of(text.begin(), text.end(), [](char ch) {
        return (ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f');
    });
}
bool staged_crt_library(const std::string &text) {
    constexpr std::string_view expected = "msvcrt.dll";
    if (text.size() != expected.size()) return false;
    for (std::size_t i = 0; i < text.size(); ++i) {
        const auto lower = text[i] >= 'A' && text[i] <= 'Z' ? text[i] + ('a' - 'A') : text[i];
        if (lower != expected[i]) return false;
    }
    return true;
}
std::string diagnostic(FaultReason reason, GuestAddress site, GuestAddress target,
                       const std::string &detail) {
    std::ostringstream stream;
    stream << fault_name(reason) << " site=0x" << std::hex << std::setw(8) << std::setfill('0')
           << site.value << " target=0x" << std::setw(8) << target.value << ": " << detail;
    return stream.str();
}
bool overlap(std::uint64_t first, std::uint64_t first_size, std::uint64_t second,
             std::uint64_t second_size) {
    return first < second + second_size && second < first + first_size;
}
std::uint32_t cleanup(const AbiContract &contract) {
    return contract.abi == Abi::Stdcall || contract.abi == Abi::Thiscall
               ? contract.stack_argument_bytes : 0;
}
} // namespace

const char *fault_name(FaultReason reason) noexcept {
    switch (reason) {
    case FaultReason::unresolved_translation: return "unresolved_translation";
    case FaultReason::unresolved_import: return "unresolved_import";
    case FaultReason::invalid_binding: return "invalid_binding";
    case FaultReason::registry_frozen: return "registry_frozen";
    case FaultReason::memory_access: return "memory_access";
    case FaultReason::stack_bounds: return "stack_bounds";
    case FaultReason::abi_violation: return "abi_violation";
    case FaultReason::poisoned: return "poisoned";
    case FaultReason::call_limit: return "call_limit";
    case FaultReason::unsupported_fs: return "unsupported_fs";
    case FaultReason::invalid_seh_chain: return "invalid_seh_chain";
    case FaultReason::unimplemented_seh_dispatch: return "unimplemented_seh_dispatch";
    case FaultReason::heap_exhausted: return "heap_exhausted";
    case FaultReason::invalid_allocation: return "invalid_allocation";
    case FaultReason::initializer_changed: return "initializer_changed";
    case FaultReason::initializer_failed: return "initializer_failed";
    }
    return "unknown_fault";
}
Fault::Fault(FaultReason reason, GuestAddress site, GuestAddress target, std::string detail)
    : std::runtime_error(diagnostic(reason, site, target, detail)), reason_(reason),
      site_(site), target_(target) {}

Runtime Runtime::from_admitted_image(std::span<const std::byte> file, const Policy &policy) {
    // Own a stable input snapshot before admission; no external span remains.
    m4::require_admission(file.size() == m4::admitted_image_size, "Wrong M4 image size");
    const std::vector<std::byte> snapshot(file.begin(), file.end());
    m4::admit_image(snapshot);
    return Runtime(m4::load_pe32(snapshot), Domain::admitted_game, policy, m4::admitted_image_hash);
}
Runtime Runtime::from_research_image(std::span<const std::byte> file,
                                    const std::string &expected_sha256, const Policy &policy) {
    m4::require_admission(!file.empty() && file.size() <= 64U * 1024U * 1024U,
                          "Experimental target input exceeds image limits");
    const std::vector<std::byte> snapshot(file.begin(), file.end());
    m4::require_admission(hash_string(expected_sha256) && m4::sha256(snapshot) == expected_sha256,
                          "Experimental target image SHA-256 mismatch");
    return Runtime(m4::load_pe32(snapshot), Domain::research_game, policy, expected_sha256);
}
Runtime Runtime::for_authored_fixture(m4::LoadedImage image, const Policy &policy) {
    return Runtime(std::move(image), Domain::authored_fixture, policy);
}
Runtime::Runtime(m4::LoadedImage image, Domain domain, const Policy &policy, std::string image_sha256)
    : image_(std::move(image)), domain_(domain), policy_(policy), image_sha256_(std::move(image_sha256)) {
    constexpr std::uint64_t space = std::uint64_t{1} << 32;
    if (!policy_.stack_bytes || policy_.stack_bytes > 16 * 1024 * 1024 ||
        !policy_.heap_bytes || policy_.heap_bytes > 64 * 1024 * 1024 ||
        (policy_.stack_low.value & 4095) || (policy_.stack_bytes & 4095) ||
        (policy_.heap_low.value & 4095) || (policy_.heap_bytes & 4095) ||
        (policy_.teb.value & 4095) || policy_.stack_low.value < 4096 ||
        std::uint64_t{policy_.stack_low.value} + policy_.stack_bytes + 4096 >= space ||
        std::uint64_t{policy_.heap_low.value} + policy_.heap_bytes > space ||
        std::uint64_t{policy_.teb.value} + 4096 > space ||
        !policy_.max_call_depth || policy_.max_call_depth > 1024 ||
        !policy_.max_call_records || policy_.max_call_records > 1000000) {
        throw std::invalid_argument("Invalid bounded main-thread memory/call policy");
    }
    const std::array<std::pair<std::uint64_t, std::uint64_t>, 3> reserved{{
        {policy_.stack_low.value - 4096U, std::uint64_t{policy_.stack_bytes} + 8192},
        {policy_.heap_low.value, policy_.heap_bytes}, {policy_.teb.value, 4096}}};
    for (std::size_t i = 0; i < reserved.size(); ++i) {
        for (std::size_t j = i + 1; j < reserved.size(); ++j) {
            if (overlap(reserved[i].first, reserved[i].second, reserved[j].first, reserved[j].second))
                throw std::invalid_argument("Thread policy mappings/guards overlap");
        }
        for (const auto &region : image_.metadata.mapped_regions) {
            if (overlap(reserved[i].first, reserved[i].second, region.start.value, region.size))
                throw std::invalid_argument("Thread policy mapping/guard overlaps admitted image");
        }
    }
    const auto rw = Permissions::read | Permissions::write;
    image_.memory.map(policy_.stack_low, policy_.stack_bytes, rw);
    image_.memory.map(policy_.heap_low, policy_.heap_bytes, rw);
    // Minimal NT_TIB32 fields only. Unimplemented TEB fields/holes are unmapped.
    image_.memory.map(policy_.teb, 4, rw);
    image_.memory.map(policy_.teb.wrapping_add(4), 8, rw);
    image_.memory.map(policy_.teb.wrapping_add(0x18), 4, rw);
    stack_top_ = GuestAddress{policy_.stack_low.value + policy_.stack_bytes};
    image_.memory.store<std::uint32_t>(policy_.teb, seh_end);
    image_.memory.store<std::uint32_t>(policy_.teb.wrapping_add(4), stack_top_.value);
    image_.memory.store<std::uint32_t>(policy_.teb.wrapping_add(8), policy_.stack_low.value);
    image_.memory.store<std::uint32_t>(policy_.teb.wrapping_add(0x18), policy_.teb.value);
    image_.memory.protect(policy_.teb.wrapping_add(4), Permissions::read);
    image_.memory.protect(policy_.teb.wrapping_add(0x18), Permissions::read);
    cpu_.esp = stack_top_.value;
    cpu_.eip = image_.metadata.entry_point.value;
    // Explicit initial *policy*, not an original CRT state observation.
    fx_[0] = std::byte{0x7f}; fx_[1] = std::byte{0x03};
    fx_[24] = std::byte{0x80}; fx_[25] = std::byte{0x1f};
    frames_.reserve(policy_.max_call_depth);
}
[[noreturn]] void Runtime::fail(FaultReason reason, GuestAddress target,
                              const std::string &detail) const {
    // A reviewed callback must not swallow a required routing/state failure
    // and then publish a successful guest return. Arena allocation failures
    // remain ordinary helper errors; imported allocation contracts are separate.
    if (!frames_.empty() && reason != FaultReason::heap_exhausted &&
        reason != FaultReason::invalid_allocation) poisoned_ = true;
    throw Fault(reason, GuestAddress{cpu_.eip}, target, detail);
}
void Runtime::ready() const {
    if (poisoned_) fail(FaultReason::poisoned, GuestAddress{cpu_.eip}, "Earlier admitted callback failed; create a new context");
    if (!frozen_) fail(FaultReason::invalid_binding, GuestAddress{cpu_.eip}, "Registry must be frozen before execution");
}
bool Runtime::executable(GuestAddress address, std::uint32_t bytes) const {
    for (const auto &region : image_.metadata.mapped_regions) {
        if ((static_cast<std::uint8_t>(region.permissions) & static_cast<std::uint8_t>(Permissions::execute)) &&
            address.value >= region.start.value && std::uint64_t{address.value} + bytes <=
            std::uint64_t{region.start.value} + region.size) return true;
    }
    return false;
}
bool Runtime::stack_span(GuestAddress address, std::uint32_t bytes) const {
    return address.value >= policy_.stack_low.value &&
           std::uint64_t{address.value} + bytes <= stack_top_.value;
}
const m4::ImportSymbol *Runtime::import_at(GuestAddress slot) const {
    for (const auto &item : image_.metadata.imports)
        if (std::uint64_t{image_.metadata.image_base} + item.iat_rva == slot.value) return &item;
    return nullptr;
}
void Runtime::validate_contract(const AbiContract &contract, GuestAddress target) const {
    if ((contract.stack_argument_bytes & 3) || contract.stack_argument_bytes > 65532 ||
        (contract.abi != Abi::Cdecl && contract.abi != Abi::Stdcall &&
         contract.abi != Abi::Thiscall && contract.abi != Abi::Internal))
        fail(FaultReason::invalid_binding, target, "Invalid bounded ABI argument/cleanup contract");
}
void Runtime::register_translation(Translation translation) {
    if (frozen_) fail(FaultReason::registry_frozen, translation.entry, "Translation registry is immutable");
    validate_contract(translation.contract, translation.entry);
    if (!translation.native || translation.name.empty() || !executable(translation.entry) ||
        translation.evidence.domain != domain_ || translations_.contains(translation.entry.value))
        fail(FaultReason::invalid_binding, translation.entry, "Null/duplicate/non-executable/domain-mismatched translation");
    if (domain_ != Domain::authored_fixture) {
        const auto &evidence = translation.evidence;
        if (evidence.image_sha256 != image_sha256_ || !evidence.source_bytes ||
            evidence.source_bytes > 1024 * 1024 || !executable(translation.entry, evidence.source_bytes) ||
            !hash_string(evidence.source_sha256) || !hash_string(evidence.native_artifact_sha256) ||
            !hash_string(evidence.gate_report_sha256))
            fail(FaultReason::invalid_binding, translation.entry, "Missing actual image/code/static-native/review bindings");
        std::vector<std::byte> code(evidence.source_bytes);
        image_.memory.read(translation.entry, code);
        if (m4::sha256(code) != evidence.source_sha256)
            fail(FaultReason::invalid_binding, translation.entry, "Registered original-code hash differs from owned image");
    }
    translations_.emplace(translation.entry.value, std::move(translation));
}
void Runtime::register_service(Service service) {
    if (frozen_) fail(FaultReason::registry_frozen, service.iat_slot, "Service registry is immutable");
    validate_contract(service.contract, service.iat_slot);
    if (!service.native || service.name.empty() || service.domain != domain_ || !import_at(service.iat_slot) ||
        services_.contains(service.iat_slot.value))
        fail(FaultReason::invalid_binding, service.iat_slot, "Null/duplicate/domain-mismatched/unrecognized IAT contract");
    if (domain_ != Domain::authored_fixture && (!hash_string(service.provider_sha256) || !hash_string(service.gate_report_sha256)))
        fail(FaultReason::invalid_binding, service.iat_slot, "Unmeasured provider/service contract");
    for (const auto &[pc, continuation] : continuations_) {
        (void)pc;
        if (continuation.identity.service_iat_slot == service.iat_slot &&
            (continuation.identity.provider_sha256 != service.provider_sha256 ||
             continuation.identity.gate_report_sha256 != service.gate_report_sha256))
            fail(FaultReason::invalid_binding, service.iat_slot, "Service and continuation provider/gate identities differ");
    }
    services_.emplace(service.iat_slot.value, std::move(service));
}
void Runtime::register_service_continuation(std::span<const std::byte> provider_image,
                                           ServiceContinuation continuation) {
    if (frozen_) fail(FaultReason::registry_frozen, continuation.return_pc, "Service continuation registry is immutable");
    const auto &c = continuation;
    const auto *owner = import_at(c.service_iat_slot);
    const auto existing_service = services_.find(c.service_iat_slot.value);
    if (c.domain != domain_ || c.name.empty() || !c.source_bytes || c.source_bytes > 65536 ||
        provider_image.empty() || provider_image.size() > 64 * 1024 * 1024 ||
        !hash_string(c.provider_sha256) || !hash_string(c.source_sha256) ||
        c.call_pc.value < c.code_start.value || c.return_pc.value <= c.call_pc.value ||
        std::uint64_t{c.code_start.value} + c.source_bytes > (std::uint64_t{1} << 32) ||
        std::uint64_t{c.return_pc.value} >= std::uint64_t{c.code_start.value} + c.source_bytes ||
        continuations_.contains(c.return_pc.value) || !owner || !owner->name || *owner->name != c.name ||
        (domain_ != Domain::authored_fixture && (!hash_string(c.native_artifact_sha256) || !hash_string(c.gate_report_sha256))))
        fail(FaultReason::invalid_binding, c.return_pc, "Incomplete/duplicate/domain-mismatched measured service continuation");
    if (domain_ == Domain::admitted_game && !staged_crt_library(owner->library))
        fail(FaultReason::invalid_binding, c.service_iat_slot, "Staged CRT continuation owner library is not MSVCRT.dll");
    if (existing_service != services_.end() &&
        (existing_service->second.provider_sha256 != c.provider_sha256 || existing_service->second.gate_report_sha256 != c.gate_report_sha256))
        fail(FaultReason::invalid_binding, c.service_iat_slot, "Continuation and service provider/gate identities differ");
    // Own and hash a bounded provider snapshot before parsing or publishing.
    const std::vector<std::byte> snapshot(provider_image.begin(), provider_image.end());
    if (m4::sha256(snapshot) != c.provider_sha256)
        fail(FaultReason::invalid_binding, c.code_start, "Service provider image identity differs");
    std::vector<std::byte> code;
    try { code = staged_crt_code(snapshot, c.code_start, c.source_bytes); }
    catch (const std::exception &error) { fail(FaultReason::invalid_binding, c.code_start, error.what()); }
    if (m4::sha256(code) != c.source_sha256)
        fail(FaultReason::invalid_binding, c.code_start, "Service original code identity differs");
    const auto offset = c.call_pc.value - c.code_start.value;
    const auto length = c.return_pc.value - c.call_pc.value;
    const auto byte = [&](std::size_t n) { return std::to_integer<std::uint8_t>(code[offset + n]); };
    // Bound currently needed ordinary near CALL encodings. Others need their
    // own recovery/admission, including far calls, prefixes and variable ModRM.
    const bool call = (length == 2 && byte(0) == 0xff && (byte(1) & 0xf8) == 0xd0) ||
                      (length == 5 && byte(0) == 0xe8) ||
                      (length == 6 && byte(0) == 0xff && byte(1) == 0x15);
    if (!call) fail(FaultReason::invalid_binding, c.call_pc, "Measured continuation does not follow an admitted near CALL encoding");
    if (overlap(c.code_start.value, c.source_bytes, policy_.stack_low.value - 4096U, std::uint64_t{policy_.stack_bytes} + 8192) ||
        overlap(c.code_start.value, c.source_bytes, policy_.heap_low.value, policy_.heap_bytes) ||
        overlap(c.code_start.value, c.source_bytes, policy_.teb.value, 4096))
        fail(FaultReason::invalid_binding, c.code_start, "Provider source overlaps owned thread policy memory/guards");
    // GuestMemory rejects all other image/previous-provider overlaps. Publish
    // only this exact RX source slice, not provider globals/imports or code.
    image_.memory.map(c.code_start, c.source_bytes, Permissions::read | Permissions::write);
    try {
        image_.memory.write(c.code_start, code);
        image_.memory.protect(c.code_start, Permissions::read | Permissions::execute);
        continuations_.emplace(c.return_pc.value, ContinuationBinding{std::move(continuation), std::move(code)});
    } catch (...) { image_.memory.unmap(c.code_start); throw; }
}
bool Runtime::admitted_return_pc(GuestAddress address) const {
    if (executable(address)) return true;
    const auto item = continuations_.find(address.value);
    if (item == continuations_.end()) return false;
    std::vector<std::byte> current(item->second.original_code.size());
    image_.memory.read(item->second.identity.code_start, current);
    if (current != item->second.original_code)
        fail(FaultReason::invalid_binding, address, "Measured service continuation source was modified");
    return true;
}
void Runtime::freeze_registry() {
    if (frozen_) fail(FaultReason::registry_frozen, GuestAddress{cpu_.eip}, "Registry already frozen");
    frozen_ = true;
}
void Runtime::call_direct(GuestAddress target, GuestAddress return_pc) {
    ready();
    const auto item = translations_.find(target.value);
    if (item == translations_.end())
        fail(FaultReason::unresolved_translation, target, "Required guest function has no admitted static native translation");
    call(item->second.native, item->second.contract, target, return_pc, false, item->second.name);
}
void Runtime::call_indirect(GuestAddress operand, GuestAddress return_pc) {
    ready();
    if (import_at(operand)) { call_import(operand, return_pc); return; }
    try { call_direct(GuestAddress{image_.memory.load<std::uint32_t>(operand)}, return_pc); }
    catch (const MemoryFault &error) { fail(FaultReason::memory_access, operand, error.what()); }
}
void Runtime::call_import(GuestAddress slot, GuestAddress return_pc) {
    ready();
    const auto *symbol = import_at(slot);
    if (!symbol) fail(FaultReason::invalid_binding, slot, "Indirect operand is not an admitted IAT slot");
    try {
        if (image_.memory.load<std::uint32_t>(slot) != symbol->original_iat_value)
            fail(FaultReason::invalid_binding, slot, "Original raw IAT dword was changed; no host pointers or fixups admitted");
    } catch (const MemoryFault &error) { fail(FaultReason::memory_access, slot, error.what()); }
    const auto item = services_.find(slot.value);
    if (item == services_.end()) {
        const auto name = symbol->name ? *symbol->name : "ordinal-" + std::to_string(*symbol->ordinal);
        fail(FaultReason::unresolved_import, slot, symbol->library + "!" + name + " has no implemented measured native service");
    }
    call(item->second.native, item->second.contract, slot, return_pc, true, item->second.name);
}
void Runtime::invoke(GuestAddress target) {
    ready();
    if (!frames_.empty()) fail(FaultReason::invalid_binding, target, "External invocation cannot bypass an active guest call frame");
    call_direct(target, GuestAddress{external_return});
}
void Runtime::call(NativeEntry native, const AbiContract &contract, GuestAddress target,
                   GuestAddress return_pc, bool imported, const std::string &name) {
    if (return_pc.value == external_return ? !frames_.empty() : !admitted_return_pc(return_pc))
        fail(FaultReason::abi_violation, return_pc, "Return PC is neither admitted code nor an outer external-return token");
    const auto continuation = continuations_.find(return_pc.value);
    if (continuation != continuations_.end() &&
        (frames_.empty() || frames_.back().target != continuation->second.identity.service_iat_slot ||
         !services_.contains(frames_.back().target.value) || cpu_.eip != continuation->second.identity.call_pc.value))
        fail(FaultReason::abi_violation, return_pc, "Provider callback CALL site/owning active native service differs");
    if (frames_.size() == policy_.max_call_depth || calls_.size() == policy_.max_call_records)
        fail(FaultReason::call_limit, target, "Bounded call depth/record capacity exhausted");
    const auto before = cpu_;
    if (before.esp < policy_.stack_low.value + 4 || !stack_span(GuestAddress{before.esp}, contract.stack_argument_bytes))
        fail(FaultReason::stack_bounds, GuestAddress{before.esp}, "Guest CALL frame/arguments exceed owned stack");
    const auto frame_sp = before.esp - 4;
    const auto expected_sp = before.esp + cleanup(contract);
    const auto record_index = calls_.size();
    calls_.push_back({GuestAddress{before.eip}, target, return_pc, imported, false, name});
    frames_.push_back({target, return_pc, before.esp, expected_sp});
    try {
        image_.memory.store<std::uint32_t>(GuestAddress{frame_sp}, return_pc.value);
        cpu_.esp = frame_sp; cpu_.eip = target.value;
        native(*this);
        if (poisoned_) fail(FaultReason::poisoned, target, "Callback caught a required routing/state failure");
        // Generated adapters capture their RET state directly, so the generic
        // exit must enforce the same integrity check as the ret() convenience.
        if (return_pc.value != external_return && !admitted_return_pc(return_pc))
            fail(FaultReason::abi_violation, return_pc, "Native callback exit destination is no longer admitted");
        if (cpu_.eip != return_pc.value || cpu_.esp != expected_sp ||
            (contract.preserve_nonvolatile && (cpu_.ebx != before.ebx || cpu_.ebp != before.ebp ||
                                              cpu_.esi != before.esi || cpu_.edi != before.edi)))
            fail(FaultReason::abi_violation, target, "Native callback violated guest return PC/ESP/nonvolatile register contract");
        calls_[record_index].completed = true;
        frames_.pop_back();
    } catch (const Fault &) {
        poisoned_ = true; frames_.pop_back(); throw;
    } catch (const std::exception &error) {
        poisoned_ = true; frames_.pop_back();
        fail(FaultReason::memory_access, target, std::string("Admitted native callback failed: ") + error.what());
    } catch (...) {
        poisoned_ = true; frames_.pop_back();
        fail(FaultReason::abi_violation, target, "Admitted native callback raised an unsupported host exception");
    }
}
void Runtime::ret(std::uint32_t callee_pop_bytes) {
    ready();
    if (frames_.empty() || callee_pop_bytes != frames_.back().expected_esp - frames_.back().caller_esp ||
        !stack_span(GuestAddress{cpu_.esp}, 4) ||
        std::uint64_t{cpu_.esp} + 4 + callee_pop_bytes > stack_top_.value)
        fail(FaultReason::abi_violation, GuestAddress{cpu_.esp}, "RET/RET n does not match active guest frame cleanup");
    const auto pc = image_.memory.load<std::uint32_t>(GuestAddress{cpu_.esp});
    if (pc != frames_.back().return_pc.value)
        fail(FaultReason::abi_violation, GuestAddress{pc}, "Guest return frame was corrupted");
    if (pc != external_return && !admitted_return_pc(GuestAddress{pc}))
        fail(FaultReason::abi_violation, GuestAddress{pc}, "Guest RET destination is not an admitted code/service continuation");
    cpu_.esp += 4 + callee_pop_bytes; cpu_.eip = pc;
}
std::uint32_t Runtime::fs_load32(std::uint32_t offset) const {
    if (offset != 0 && offset != 4 && offset != 8 && offset != 0x18)
        fail(FaultReason::unsupported_fs, GuestAddress{offset}, "Only recovered exception-chain/NT_TIB32 stack/self fields are implemented");
    return image_.memory.load<std::uint32_t>(policy_.teb.wrapping_add(offset));
}
void Runtime::fs_store32(std::uint32_t offset, std::uint32_t value) {
    if (offset != 0) fail(FaultReason::unsupported_fs, GuestAddress{offset}, "Only FS:[0] exception-chain writes are implemented");
    image_.memory.store<std::uint32_t>(policy_.teb, value);
}
std::vector<SehRecord> Runtime::seh_chain(std::uint32_t max_depth) const {
    if (!max_depth || max_depth > 1024) fail(FaultReason::invalid_seh_chain, fs_base(), "Invalid bounded SEH depth");
    std::vector<SehRecord> records;
    auto frame = GuestAddress{fs_load32(0)};
    while (frame.value != seh_end) {
        if (records.size() == max_depth || (frame.value & 3) || !stack_span(frame, 8))
            fail(FaultReason::invalid_seh_chain, frame, "SEH chain depth/alignment/stack span invalid");
        const auto previous = GuestAddress{image_.memory.load<std::uint32_t>(frame)};
        const auto handler = GuestAddress{image_.memory.load<std::uint32_t>(frame.wrapping_add(4))};
        if (!executable(handler) || (previous.value != seh_end && previous.value <= frame.value))
            fail(FaultReason::invalid_seh_chain, frame, "SEH handler is not executable or chain is cyclic/reversed");
        records.push_back({frame, previous, handler}); frame = previous;
    }
    return records;
}
void Runtime::seh_push(GuestAddress frame, GuestAddress handler) {
    const auto old = seh_chain();
    if ((frame.value & 3) || !stack_span(frame, 8) || !executable(handler) ||
        (!old.empty() && frame.value >= old.front().frame.value))
        fail(FaultReason::invalid_seh_chain, frame, "New SEH registration must be aligned, executable and below current head");
    std::array<std::byte, 8> bytes{};
    const auto previous = fs_load32(0);
    for (unsigned n = 0; n < 4; ++n) {
        bytes[n] = std::byte((previous >> (8 * n)) & 255);
        bytes[n + 4] = std::byte((handler.value >> (8 * n)) & 255);
    }
    image_.memory.write(frame, bytes); fs_store32(0, frame.value);
}
void Runtime::seh_pop(GuestAddress frame) {
    const auto chain = seh_chain();
    if (chain.empty() || chain.front().frame != frame)
        fail(FaultReason::invalid_seh_chain, frame, "SEH removal must match the current head");
    fs_store32(0, chain.front().previous.value);
}
[[noreturn]] void Runtime::dispatch_exception(std::uint32_t code, GuestAddress address) {
    (void)seh_chain();
    fail(FaultReason::unimplemented_seh_dispatch, address,
         "Guest exception " + std::to_string(code) + ": _except_handler3/_XcptFilter scope dispatch and unwind are not implemented");
}
GuestAddress Runtime::heap_allocate(std::uint32_t bytes, std::uint32_t alignment) {
    if (!bytes || !alignment || alignment > 4096 || (alignment & (alignment - 1)))
        fail(FaultReason::invalid_allocation, policy_.heap_low, "Arena allocation requires nonzero size and power-of-two alignment <=4096");
    const auto aligned = (std::uint64_t{heap_cursor_} + alignment - 1) & ~std::uint64_t{alignment - 1};
    if (aligned + bytes > policy_.heap_bytes)
        fail(FaultReason::heap_exhausted, policy_.heap_low, "Bounded private guest arena exhausted; no fabricated malloc success");
    const auto address = GuestAddress{policy_.heap_low.value + static_cast<std::uint32_t>(aligned)};
    allocations_.emplace(address.value, bytes);
    heap_cursor_ = static_cast<std::uint32_t>(aligned + bytes);
    return address;
}
void Runtime::heap_release(GuestAddress address) {
    if (allocations_.erase(address.value) != 1)
        fail(FaultReason::invalid_allocation, address, "Arena release requires an exact live allocation; no interior/double free");
}
bool Runtime::heap_allocation_live(GuestAddress address) const noexcept {
    return allocations_.contains(address.value);
}
InitializerLedger Runtime::prepare_initializers(GuestAddress begin, GuestAddress end) {
    if ((begin.value & 3) || (end.value & 3) || end.value < begin.value ||
        std::uint64_t{end.value} - begin.value > 16384)
        fail(FaultReason::invalid_binding, begin, "Invalid bounded initializer interval");
    if (domain_ == Domain::admitted_game &&
        !((begin.value == 0x5e0000 && end.value == 0x5e0244) ||
          (begin.value == 0x5e0248 && end.value == 0x5e024c)))
        fail(FaultReason::invalid_binding, begin, "Initializer interval is not a recovered actual CRT table");
    InitializerLedger ledger(this);
    for (auto slot = std::uint64_t{begin.value}; slot < end.value; slot += 4) {
        const auto address = GuestAddress{static_cast<std::uint32_t>(slot)};
        const auto target = GuestAddress{image_.memory.load<std::uint32_t>(address)};
        if (target.value && !executable(target))
            fail(FaultReason::invalid_binding, target, "Initializer table contains a non-executable target");
        ledger.items_.push_back({address, target, InitializerStatus::pending, {}});
    }
    return ledger;
}
void Runtime::run_initializers(InitializerLedger &ledger) {
    ready();
    if (ledger.owner_ != this || ledger.failed_ || ledger.completed() || !frames_.empty())
        fail(FaultReason::initializer_failed, GuestAddress{cpu_.eip}, "Ledger owner/one-shot/external orchestration state invalid");
    while (ledger.cursor_ < ledger.items_.size()) {
        auto &item = ledger.items_[ledger.cursor_];
        try {
            if (image_.memory.load<std::uint32_t>(item.slot) != item.target.value)
                fail(FaultReason::initializer_changed, item.slot, "Initializer slot differs from admitted ordering snapshot");
            if (!item.target.value) { item.status = InitializerStatus::zero_sentinel; ++ledger.cursor_; continue; }
            item.status = InitializerStatus::attempted;
            invoke(item.target);
            item.status = InitializerStatus::complete; ++ledger.cursor_;
        } catch (const std::exception &error) {
            item.status = InitializerStatus::fault; item.failure = error.what(); ledger.failed_ = true; throw;
        }
    }
}

} // namespace mw34::m4_runtime
