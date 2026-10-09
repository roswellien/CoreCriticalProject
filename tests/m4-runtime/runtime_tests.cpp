#include "runtime.hpp"
#include "admission.hpp"
#include <algorithm>
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>

using namespace mw34;
using namespace mw34::m4_runtime;
static_assert(sizeof(NT_TIB32) == 28 && offsetof(NT_TIB32, ExceptionList) == 0 &&
              offsetof(NT_TIB32, StackBase) == 4 && offsetof(NT_TIB32, StackLimit) == 8 &&
              offsetof(NT_TIB32, Self) == 0x18);
namespace {
unsigned checks{};
void check(bool ok, const char *why) { if (!ok) throw std::runtime_error(why); ++checks; }
template<class F> void reject(F function, FaultReason reason, const char *why) {
    try { function(); }
    catch (const Fault &fault) { check(fault.reason() == reason, why); return; }
    throw std::runtime_error(std::string("Expected fault: ") + why);
}
Policy small_policy() {
    Policy p; p.stack_bytes = 8192; p.heap_bytes = 4096; p.max_call_depth = 8; return p;
}
m4::LoadedImage fixture() {
    m4::LoadedImage image;
    image.metadata.image_base = 0x1000;
    image.metadata.image_size = 0x3000;
    image.metadata.entry_point = GuestAddress{0x1100};
    const auto rx = Permissions::read | Permissions::execute;
    const auto rw = Permissions::read | Permissions::write;
    image.memory.map(GuestAddress{0x1000}, 4096, rx);
    image.memory.map(GuestAddress{0x2000}, 4096, rw);
    image.memory.map(GuestAddress{0x3000}, 4096, rw);
    image.metadata.mapped_regions = {{"authored-code", GuestAddress{0x1000}, 4096, rx},
                                    {"authored-data", GuestAddress{0x2000}, 4096, rw},
                                    {"authored-IAT", GuestAddress{0x3000}, 4096, Permissions::read}};
    image.memory.store<std::uint32_t>(GuestAddress{0x3000}, 0x12345678);
    image.memory.protect(GuestAddress{0x3000}, Permissions::read);
    m4::ImportSymbol import;
    import.library = "AUTHORED_TEST.dll"; import.name = "WriteCounter";
    import.iat_rva = 0x2000; import.original_iat_value = 0x12345678;
    import.iat_permissions = Permissions::read;
    image.metadata.imports.push_back(import);
    return image;
}
Translation binding(std::uint32_t entry, NativeEntry callback, Abi abi = Abi::Cdecl,
                    std::uint32_t args = 0, bool preserve = true) {
    return {GuestAddress{entry}, {abi, args, preserve}, callback, "authored-only", {}};
}
void increment(Runtime &r) {
    const auto old = r.memory().load<std::uint32_t>(GuestAddress{0x2200});
    r.memory().store<std::uint32_t>(GuestAddress{0x2200}, old + 1);
    r.remill_state()[3000] ^= std::byte{1};
    r.cpu().eax = old + 1; r.ret();
}
void nested(Runtime &r) {
    r.call_direct(GuestAddress{0x1200}, GuestAddress{0x1110});
    r.call_indirect(GuestAddress{0x2210}, GuestAddress{0x1114}); r.ret();
}
void argument_sum(Runtime &r) {
    const auto sp = r.cpu().esp;
    r.cpu().eax = r.memory().load<std::uint32_t>(GuestAddress{sp + 4}) +
                  r.memory().load<std::uint32_t>(GuestAddress{sp + 8}) +
                  r.memory().load<std::uint32_t>(GuestAddress{sp + 12});
    r.ret(12);
}
void twenty(Runtime &r) { r.cpu().eax = r.cpu().ecx; r.ret(20); }
void service_write(Runtime &r) {
    r.memory().store<std::uint32_t>(GuestAddress{0x2204}, 0xabcdef01); r.cpu().eax = 7; r.ret();
}
void wrong_sp(Runtime &r) { r.cpu().eip = Runtime::external_return; }
void wrong_nonvolatile(Runtime &r) { r.cpu().ebx ^= 1; r.ret(); }
void wrong_ret(Runtime &r) { r.memory().store<std::uint32_t>(GuestAddress{r.cpu().esp}, 0x1120); r.ret(); }
void swallowed(Runtime &r) {
    try { r.call_direct(GuestAddress{0x1777}, GuestAddress{0x1110}); } catch (const Fault &) {}
    r.cpu().esp += 4; r.cpu().eip = Runtime::external_return;
}
void recurse(Runtime &r) { r.call_direct(GuestAddress{0x1500}, GuestAddress{0x1510}); r.ret(); }
void first(Runtime &r) { r.memory().store<std::uint32_t>(GuestAddress{0x2208}, 1); r.ret(); }
void last(Runtime &r) { r.memory().store<std::uint32_t>(GuestAddress{0x2208}, 99); r.ret(); }
void change_next(Runtime &r) { r.memory().store<std::uint32_t>(GuestAddress{0x2304}, 0x1200); r.ret(); }

void main_thread() {
    auto r = Runtime::for_authored_fixture(fixture(), small_policy());
    check(r.fs_load32(0) == 0xffffffff && r.fs_load32(4) == r.stack_top().value &&
          r.fs_load32(8) == r.stack_low().value && r.fs_load32(0x18) == r.fs_base().value,
          "Explicit guest NT_TIB32 state");
    check(reinterpret_cast<std::uintptr_t>(r.remill_state().data()) % 64 == 0 &&
          r.remill_state().size() == 3504 && !r.remill_seeded(), "Stable aligned complete opaque State");
    r.remill_state()[3000] = std::byte{0x77}; r.mark_remill_seeded();
    r.fx()[160] = std::byte{0x66};
    auto *state = r.remill_state().data();
    r.register_translation(binding(0x1200, increment)); r.freeze_registry();
    r.invoke(GuestAddress{0x1200}); r.invoke(GuestAddress{0x1200});
    check(r.memory().load<std::uint32_t>(GuestAddress{0x2200}) == 2 &&
          r.remill_state().data() == state && r.remill_state()[3000] == std::byte{0x77} &&
          r.remill_seeded() && r.fx()[160] == std::byte{0x66}, "Calls persist globals, complete State and FX backing");
    reject([&] { (void)r.fs_load32(0x2c); }, FaultReason::unsupported_fs, "Unsupported TLS field rejected");
    reject([&] { r.fs_store32(4, 0); }, FaultReason::unsupported_fs, "Thread bounds are not writable FS fields");
    for (const auto address : {r.stack_low().value - 1, r.stack_top().value,
                               r.fs_base().value + 0x0c, r.fs_base().value + 0x2c}) {
        try { (void)r.memory().load<std::uint8_t>(GuestAddress{address}); }
        catch (const MemoryFault &fault) { check(fault.reason() == MemoryFaultReason::unmapped, "Stack guards/TEB holes unmapped"); continue; }
        throw std::runtime_error("Unsupported guard/thread field mapped");
    }
    try { r.memory().store<std::uint32_t>(r.fs_base().wrapping_add(8), 1); throw std::runtime_error("TIB bounds write unexpectedly succeeded"); }
    catch (const MemoryFault &fault) { check(fault.reason() == MemoryFaultReason::permission_denied, "TIB bounds read-only"); }
}
void routing() {
    auto r = Runtime::for_authored_fixture(fixture(), small_policy());
    r.memory().store<std::uint32_t>(GuestAddress{0x2210}, 0x1200);
    r.cpu().ebx = 12; r.cpu().ebp = 34; r.cpu().esi = 56; r.cpu().edi = 78;
    r.register_translation(binding(0x1100, nested)); r.register_translation(binding(0x1200, increment));
    r.register_service({GuestAddress{0x3000}, {}, service_write, "authored-service", Domain::authored_fixture, {}, {}});
    r.freeze_registry(); const auto initial_sp = r.cpu().esp;
    r.invoke(GuestAddress{0x1100});
    check(r.cpu().esp == initial_sp && r.cpu().eip == Runtime::external_return && r.cpu().eax == 2 &&
          r.calls().size() == 3 && std::all_of(r.calls().begin(), r.calls().end(), [](const auto &call) { return call.completed; }),
          "Nested checked direct and indirect calls actually execute and return");
    r.call_indirect(GuestAddress{0x3000}, GuestAddress{0x1110});
    check(r.cpu().eax == 7 && r.cpu().esp == initial_sp && r.calls().back().import &&
          r.memory().load<std::uint32_t>(GuestAddress{0x2204}) == 0xabcdef01 &&
          r.memory().load<std::uint32_t>(GuestAddress{0x3000}) == 0x12345678,
          "Typed import service executes without altering raw read-only IAT");
    auto before = r.cpu();
    reject([&] { r.call_direct(GuestAddress{0x1777}, GuestAddress{0x1110}); }, FaultReason::unresolved_translation, "Unknown direct target rejected");
    check(r.cpu() == before, "Unresolved direct route admits no guest frame/CPU mutation");
    reject([&] { r.call_indirect(GuestAddress{0x5000}, GuestAddress{0x1110}); }, FaultReason::memory_access, "Unmapped indirect operand rejected");
    reject([&] { r.register_translation(binding(0x1400, increment)); }, FaultReason::registry_frozen, "Registry immutable during/after execution");
    reject([&] { r.call_direct(GuestAddress{0x1200}, GuestAddress{0x2000}); }, FaultReason::abi_violation, "Non-executable return PC rejected");
    auto missing = Runtime::for_authored_fixture(fixture(), small_policy()); missing.freeze_registry();
    reject([&] { missing.call_import(GuestAddress{0x3000}, GuestAddress{0x1110}); }, FaultReason::unresolved_import, "Missing service gives symbol-specific denial");
    reject([&] { missing.call_import(GuestAddress{0x3004}, GuestAddress{0x1110}); }, FaultReason::invalid_binding, "Unknown IAT slot rejected");
    auto unfrozen = Runtime::for_authored_fixture(fixture(), small_policy());
    reject([&] { unfrozen.invoke(GuestAddress{0x1200}); }, FaultReason::invalid_binding, "Execution before freeze rejected");
    auto bad = binding(0x1200, increment); bad.evidence.domain = Domain::admitted_game;
    reject([&] { unfrozen.register_translation(bad); }, FaultReason::invalid_binding, "Fixture callbacks cannot claim actual-game domain");
    unfrozen.register_translation(binding(0x1200, increment));
    reject([&] { unfrozen.register_translation(binding(0x1200, increment)); }, FaultReason::invalid_binding, "Duplicate translation rejected");
}
void arguments_and_failures() {
    auto r = Runtime::for_authored_fixture(fixture(), small_policy());
    r.register_translation(binding(0x1300, argument_sum, Abi::Stdcall, 12));
    r.register_translation(binding(0x1400, twenty, Abi::Thiscall, 20)); r.freeze_registry();
    const auto top = r.stack_top().value; r.cpu().esp = top - 12;
    for (unsigned i = 0; i < 3; ++i) r.memory().store<std::uint32_t>(GuestAddress{r.cpu().esp + i * 4}, i + 1);
    r.invoke(GuestAddress{0x1300}); check(r.cpu().esp == top && r.cpu().eax == 6, "Actual RET12 cleanup and ordered stack arguments");
    r.cpu().esp = top - 20; r.cpu().ecx = 0x2200; r.invoke(GuestAddress{0x1400});
    check(r.cpu().esp == top && r.cpu().eax == 0x2200, "Actual RET20/thiscall ECX contract");
    r.cpu().esp = r.stack_low().value;
    reject([&] { r.invoke(GuestAddress{0x1300}); }, FaultReason::stack_bounds, "CALL lower guard rejected before wrap");
    for (auto callback : {wrong_sp, wrong_nonvolatile, wrong_ret, swallowed}) {
        auto failed = Runtime::for_authored_fixture(fixture(), small_policy());
        failed.register_translation(binding(0x1600, callback)); failed.freeze_registry();
        reject([&] { failed.invoke(GuestAddress{0x1600}); }, callback == swallowed ? FaultReason::poisoned : FaultReason::abi_violation,
               "Incorrect/caught-required callback cannot publish successful return");
        check(failed.poisoned() && !failed.calls().back().completed, "Failed callback poisons context and call remains incomplete");
        reject([&] { failed.invoke(GuestAddress{0x1600}); }, FaultReason::poisoned, "Failed context cannot be reused");
    }
    auto recursive = Runtime::for_authored_fixture(fixture(), small_policy());
    recursive.register_translation(binding(0x1500, recurse)); recursive.freeze_registry();
    reject([&] { recursive.invoke(GuestAddress{0x1500}); }, FaultReason::call_limit, "Recursive native calls terminate at explicit depth");
    check(recursive.poisoned(), "Recursive failure propagates without fabricated returns");
}
void seh_and_heap() {
    auto r = Runtime::for_authored_fixture(fixture(), small_policy());
    const auto a = GuestAddress{r.stack_top().value - 64}, b = GuestAddress{r.stack_top().value - 96};
    r.seh_push(a, GuestAddress{0x1700}); r.seh_push(b, GuestAddress{0x1710});
    const auto chain = r.seh_chain();
    check(chain.size() == 2 && chain[0].frame == b && chain[0].previous == a && chain[1].previous.value == Runtime::seh_end,
          "FS:[0] registrations form actual checked guest stack chain");
    reject([&] { r.seh_pop(a); }, FaultReason::invalid_seh_chain, "SEH non-head unlink rejected");
    reject([&] { r.dispatch_exception(0xc0000005, GuestAddress{0x1700}); }, FaultReason::unimplemented_seh_dispatch,
           "SEH storage does not pretend dispatch/unwind implemented");
    r.seh_pop(b); r.seh_pop(a); check(r.fs_load32(0) == Runtime::seh_end, "SEH epilogue restores sentinel");
    r.seh_push(a, GuestAddress{0x1700}); r.memory().store<std::uint32_t>(a, a.value);
    reject([&] { (void)r.seh_chain(); }, FaultReason::invalid_seh_chain, "Cyclic SEH chain rejected");
    r.fs_store32(0, r.fs_base().value);
    reject([&] { (void)r.seh_chain(); }, FaultReason::invalid_seh_chain, "Non-stack SEH frame rejected");
    const auto first_alloc = r.heap_allocate(17), next = r.heap_allocate(32, 32);
    check(first_alloc.value % 16 == 0 && next.value % 32 == 0 && next.value >= first_alloc.value + 17,
          "Arena allocations aligned and disjoint");
    r.memory().store<std::uint32_t>(first_alloc, 0x98765432);
    check(r.memory().load<std::uint32_t>(first_alloc) == 0x98765432 && r.heap_allocation_live(first_alloc), "Guest heap uses owned checked storage");
    reject([&] { r.heap_release(first_alloc.wrapping_add(1)); }, FaultReason::invalid_allocation, "Interior release rejected");
    r.heap_release(first_alloc); check(!r.heap_allocation_live(first_alloc), "Arena exact release invalidates ownership record");
    reject([&] { r.heap_release(first_alloc); }, FaultReason::invalid_allocation, "Double release rejected");
    reject([&] { (void)r.heap_allocate(0xffffffff); }, FaultReason::heap_exhausted, "Oversized allocation fails without arithmetic wrap");
    reject([&] { (void)r.heap_allocate(1, 3); }, FaultReason::invalid_allocation, "Non-power-of-two alignment rejected");
    const auto next_after_failure = r.heap_allocate(1);
    check(next_after_failure.value == next.value + 32, "Failed allocation does not advance cursor");
}
void ordering() {
    auto r = Runtime::for_authored_fixture(fixture(), small_policy());
    for (const auto &[offset, target] : {std::pair{0U, 0U}, {4U, 0x1800U}, {8U, 0x1777U}, {12U, 0x1900U}})
        r.memory().store<std::uint32_t>(GuestAddress{0x2300 + offset}, target);
    auto ledger = r.prepare_initializers(GuestAddress{0x2300}, GuestAddress{0x2310});
    r.register_translation(binding(0x1800, first)); r.register_translation(binding(0x1900, last)); r.freeze_registry();
    reject([&] { r.run_initializers(ledger); }, FaultReason::unresolved_translation, "Ledger stops on first missing required initializer");
    check(ledger.failed() && !ledger.completed() && ledger.cursor() == 2 &&
          ledger.items()[0].status == InitializerStatus::zero_sentinel && ledger.items()[1].status == InitializerStatus::complete &&
          ledger.items()[2].status == InitializerStatus::fault && ledger.items()[3].status == InitializerStatus::pending &&
          r.memory().load<std::uint32_t>(GuestAddress{0x2208}) == 1 && r.calls().size() == 1,
          "Zero is recorded, known effect persists, missing root is not skipped, later root untouched");
    reject([&] { r.run_initializers(ledger); }, FaultReason::initializer_failed, "Failed ordering cannot resume by skipping missing root");
    auto changed = Runtime::for_authored_fixture(fixture(), small_policy());
    changed.memory().store<std::uint32_t>(GuestAddress{0x2300}, 0x1800);
    changed.memory().store<std::uint32_t>(GuestAddress{0x2304}, 0x1900);
    auto captured = changed.prepare_initializers(GuestAddress{0x2300}, GuestAddress{0x2308});
    changed.register_translation(binding(0x1800, change_next)); changed.register_translation(binding(0x1900, last)); changed.freeze_registry();
    reject([&] { changed.run_initializers(captured); }, FaultReason::initializer_changed, "Changed next pointer rejects exact ordering snapshot");
    check(captured.cursor() == 1 && captured.items()[1].status == InitializerStatus::fault && changed.calls().size() == 1,
          "Changed table never routes altered or later target");
    auto complete = Runtime::for_authored_fixture(fixture(), small_policy());
    complete.memory().store<std::uint32_t>(GuestAddress{0x2300}, 0x1800);
    complete.memory().store<std::uint32_t>(GuestAddress{0x2304}, 0x1900);
    auto all = complete.prepare_initializers(GuestAddress{0x2300}, GuestAddress{0x2308});
    complete.register_translation(binding(0x1800, first)); complete.register_translation(binding(0x1900, last)); complete.freeze_registry();
    complete.run_initializers(all);
    check(all.completed() && !all.failed() && complete.memory().load<std::uint32_t>(GuestAddress{0x2208}) == 99,
          "Fully registered authored initializer sequence completes in exact order");
    reject([&] { complete.run_initializers(all); }, FaultReason::initializer_failed, "Completed initializers cannot run twice");
}
void construction_admission() {
    bool wrong_size_rejected = false;
    try { (void)Runtime::from_admitted_image({}); }
    catch (const std::runtime_error &error) {
        check(std::string(error.what()) == "Wrong M4 image size", "Wrong image size rejected before owned-copy/mapping");
        wrong_size_rejected = true;
    }
    if (!wrong_size_rejected) throw std::runtime_error("Wrong image size unexpectedly admitted");
    for (unsigned variant = 0; variant < 4; ++variant) {
        auto policy = small_policy();
        if (variant == 0) policy.stack_low = GuestAddress{0x2000};
        if (variant == 1) policy.teb = policy.heap_low;
        if (variant == 2) policy.stack_low = GuestAddress{0xfffff000};
        if (variant == 3) policy.stack_bytes = 4095;
        try { (void)Runtime::for_authored_fixture(fixture(), policy); }
        catch (const std::invalid_argument &) { ++checks; continue; }
        throw std::runtime_error("Invalid image/guard/arena/thread policy admitted");
    }
}
} // namespace
int main() {
    try { construction_admission(); main_thread(); routing(); arguments_and_failures(); seh_and_heap(); ordering();
        std::cout << "Runtime authored contract checks: " << checks << '\n'; return 0;
    } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
