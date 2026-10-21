#include "admission.hpp"
#include "crt_services.hpp"
#include <fstream>
#include <iostream>
#include <memory>

using namespace mw34;
using namespace mw34::m4_runtime;
using namespace mw34::m4_crt;
namespace {
unsigned checks{};
std::vector<std::byte> provider;
Cpu32 observed;
Slots slots{GuestAddress{0x3000}, GuestAddress{0x3004}, GuestAddress{0x3008}, GuestAddress{0x300c}};
std::uint32_t begin = 0x2000, end = 0x2010;
void check(bool ok, const char *why) {
    if (!ok)
        throw std::runtime_error(why);
    ++checks;
}
template <class F> void reject(F fn, FaultReason reason, const char *why) {
    try {
        fn();
    } catch (const Fault &f) {
        check(f.reason() == reason, why);
        return;
    }
    throw std::runtime_error(why);
}
template <class F> void reject_input(F fn, const char *why) {
    try {
        fn();
    } catch (const std::invalid_argument &) {
        check(true, why);
        return;
    }
    throw std::runtime_error(why);
}
m4::LoadedImage fixture() {
    m4::LoadedImage x;
    const auto rx = Permissions::read | Permissions::execute;
    const auto rw = Permissions::read | Permissions::write;
    x.metadata.image_base = 0x1000;
    x.metadata.entry_point = GuestAddress{0x1100};
    x.memory.map(GuestAddress{0x1000}, 4096, rx);
    x.memory.map(GuestAddress{0x2000}, 4096, rw);
    x.memory.map(GuestAddress{0x3000}, 4096, rw);
    x.metadata.mapped_regions = {{"authored-only", GuestAddress{0x1000}, 4096, rx}};
    const std::array<const char *, 5> names{"_initterm", "__set_app_type", "__p__fmode",
                                            "__p__commode", "_controlfp"};
    for (unsigned n = 0; n < names.size(); ++n) {
        m4::ImportSymbol i;
        i.library = "AUTHORED_TEST.dll";
        i.name = names[n];
        i.iat_rva = 0x2000 + 4 * n;
        i.original_iat_value = 0x87654300 + n;
        x.metadata.imports.push_back(i);
        x.memory.store<std::uint32_t>(GuestAddress{0x3000 + 4 * n}, i.original_iat_value);
    }
    x.memory.protect(GuestAddress{0x3000}, Permissions::read);
    return x;
}
Policy policy() {
    Policy p;
    p.stack_bytes = 8192;
    p.heap_bytes = 4096;
    p.max_call_depth = 16;
    return p;
}
Translation binding(unsigned address, NativeEntry fn) {
    return {GuestAddress{address}, {}, fn, "authored-only", {}};
}
void leaf(Runtime &r, unsigned digit) {
    check(r.memory().load<std::uint32_t>(GuestAddress{r.cpu().esp}) == 0x78001510,
          "Original provider callback return address");
    check(r.calls().back().site.value == 0x7800150e, "Original provider callback CALL site");
    const auto value = r.memory().load<std::uint32_t>(GuestAddress{0x2200});
    r.memory().store<std::uint32_t>(GuestAddress{0x2200}, 10 * value + digit);
    r.cpu().eax = 0xaabbcc00 + digit;
    r.cpu().ecx = 0x12345600 + digit;
    r.cpu().edx = 0xfedcba00 + digit;
    r.remill_state()[3200] = std::byte(std::to_integer<unsigned>(r.remill_state()[3200]) + 1);
    r.ret();
}
void one(Runtime &r) { leaf(r, 1); }
void two(Runtime &r) { leaf(r, 2); }
void three(Runtime &r) { leaf(r, 3); }
void change_future(Runtime &r) {
    r.memory().store<std::uint32_t>(GuestAddress{0x2004}, 0x1400);
    leaf(r, 1);
}
void shrink_end(Runtime &r) {
    r.memory().store<std::uint32_t>(GuestAddress{r.cpu().esp + 16}, 0x2004);
    leaf(r, 1);
}
void invoke_init(Runtime &r) {
    r.cpu().esp -= 8;
    r.memory().store<std::uint32_t>(GuestAddress{r.cpu().esp}, begin);
    r.memory().store<std::uint32_t>(GuestAddress{r.cpu().esp + 4}, end);
    r.call_import(slots.initterm, GuestAddress{0x1110});
    observed = r.cpu();
    r.cpu().esp += 8;
    r.ret();
}
void globals(Runtime &r) {
    const auto flags = r.cpu().eflags;
    r.cpu().esp -= 4;
    r.memory().store<std::uint32_t>(GuestAddress{r.cpu().esp}, 2);
    r.call_import(slots.set_app_type, GuestAddress{0x1110});
    r.cpu().esp += 4;
    check(r.cpu().eax == 2 && r.cpu().eflags == flags &&
              r.memory().load<std::uint32_t>(GuestAddress{Session::provider_app_type}) == 2,
          "Exact MOV app type semantics");
    r.call_import(slots.p_fmode, GuestAddress{0x1114});
    check(r.cpu().eax == Session::provider_fmode && r.cpu().eflags == flags,
          "Original fmode guest pointer/flags");
    r.memory().store<std::uint32_t>(GuestAddress{r.cpu().eax}, 0x8000);
    r.call_import(slots.p_fmode, GuestAddress{0x1118});
    check(r.memory().load<std::uint32_t>(GuestAddress{r.cpu().eax}) == 0x8000,
          "Stable writable fmode guest address");
    r.call_import(slots.p_commode, GuestAddress{0x111c});
    check(r.cpu().eax == Session::provider_commode && r.cpu().eflags == flags,
          "Original commode guest pointer/flags");
    r.ret();
}
void unresolved(Runtime &r) {
    r.call_import(GuestAddress{0x3010}, GuestAddress{0x1110});
    r.ret();
}
void setup(Runtime &r, NativeEntry driver = invoke_init, NativeEntry first = one) {
    r.register_translation(binding(0x1100, driver));
    r.register_translation(binding(0x1200, first));
    r.register_translation(binding(0x1300, two));
    r.register_translation(binding(0x1400, three));
    r.cpu().esi = 0x99887766;
    r.cpu().ebx = 0x12121212;
    r.cpu().edi = 0xabcdef00;
    r.cpu().ebp = 0x98765432;
    r.cpu().eflags = 0xa02;
}
void table(Runtime &r, std::initializer_list<unsigned> targets) {
    unsigned address = 0x2000;
    for (auto value : targets) {
        r.memory().store<std::uint32_t>(GuestAddress{address}, value);
        address += 4;
    }
}
void tests() {
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r);
        table(r, {0, 0x1200, 0x1300, 0});
        r.fx()[9] = std::byte{0x75};
        r.remill_state()[13] = std::byte{0x5a};
        r.freeze_registry();
        begin = 0x2000;
        end = 0x2010;
        const auto sp = r.cpu().esp;
        r.invoke(GuestAddress{0x1100});
        check(s.visits().size() == 4 && s.visits()[0].status == VisitStatus::null_slot &&
                  s.visits()[1].status == VisitStatus::completed &&
                  s.visits()[2].status == VisitStatus::completed &&
                  s.visits()[3].status == VisitStatus::null_slot,
              "All reached slots ordered, only literal nulls skipped");
        check(r.memory().load<std::uint32_t>(GuestAddress{0x2200}) == 12,
              "Initializer callbacks execute in source order");
        check(r.cpu().esp == sp && r.cpu().esi == 0x99887766 && r.cpu().ebx == 0x12121212 &&
                  r.cpu().edi == 0xabcdef00 && r.cpu().ebp == 0x98765432,
              "Guest ESI push/pop and cdecl arguments preserve ABI");
        check(observed.eax == 0 && observed.ecx == 0x12345602 && observed.edx == 0xfedcba02,
              "Final null leaves EAX zero and callback volatile registers retained");
        check((observed.eflags & 0xcd5) == 0x44 && (observed.eflags & ~0xcd5U) == (0xa02 & ~0xcd5U),
              "Final equality CMP defines all arithmetic flags");
        check(r.fx()[9] == std::byte{0x75} && r.remill_state()[13] == std::byte{0x5a} &&
                  r.remill_state()[3200] == std::byte{2},
              "FP/hidden State persist across CRT callbacks");
        check(r.memory().load<std::uint32_t>(GuestAddress{0x3000}) == 0x87654300,
              "Original raw IAT preserved");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r);
        table(r, {0x1200, 0x1300});
        r.freeze_registry();
        begin = 0x2000;
        end = 0x2008;
        r.invoke(GuestAddress{0x1100});
        check(observed.eax == 0xaabbcc02,
              "Void _initterm keeps last callback EAX, no fabricated error code");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r);
        r.cpu().eax = 0x55667788;
        r.freeze_registry();
        begin = end = 0xfffff000;
        r.invoke(GuestAddress{0x1100});
        check(s.visits().empty() && observed.eax == 0x55667788 && (observed.eflags & 0xcd5) == 0x44,
              "Empty unmapped range reads no table and preserves EAX");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r);
        r.freeze_registry();
        begin = 0x9000;
        end = 0x8000;
        r.invoke(GuestAddress{0x1100});
        check(s.visits().empty() && (observed.eflags & 0xcd5) == 4,
              "Original unsigned reversed interval is empty");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r);
        table(r, {0x1200, 0x1500, 0x1300});
        r.freeze_registry();
        begin = 0x2000;
        end = 0x200c;
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::unresolved_translation,
               "Unknown initializer is a required fault");
        check(r.poisoned() && s.visits().size() == 2 &&
                  s.visits()[1].status == VisitStatus::fault &&
                  s.visits()[1].target.value == 0x1500 &&
                  r.memory().load<std::uint32_t>(GuestAddress{0x2200}) == 1,
              "Stop at first unresolved initializer; retain observed prefix");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r, invoke_init, change_future);
        table(r, {0x1200, 0x1300});
        r.freeze_registry();
        begin = 0x2000;
        end = 0x2008;
        r.invoke(GuestAddress{0x1100});
        check(r.memory().load<std::uint32_t>(GuestAddress{0x2200}) == 13 &&
                  s.visits()[1].target.value == 0x1400,
              "Source reads future table slot when reached");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r, invoke_init, shrink_end);
        table(r, {0x1200, 0x1300});
        r.freeze_registry();
        begin = 0x2000;
        end = 0x2008;
        r.invoke(GuestAddress{0x1100});
        check(s.visits().size() == 1 && r.memory().load<std::uint32_t>(GuestAddress{0x2200}) == 1,
              "Original CMP rereads caller end argument");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r, globals);
        check(r.memory().load<std::uint32_t>(GuestAddress{Session::provider_app_type}) == 0 &&
                  r.memory().load<std::uint32_t>(GuestAddress{Session::provider_fmode}) == 0 &&
                  r.memory().load<std::uint32_t>(GuestAddress{Session::provider_commode}) == 0,
              "Exact source provider globals start at zero");
        r.freeze_registry();
        r.invoke(GuestAddress{0x1100});
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r, unresolved);
        r.freeze_registry();
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::unresolved_import,
               "Unimplemented CRT services have no successful substitutes");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        setup(r);
        { Session s(r, provider, {}, slots); }
        r.freeze_registry();
        begin = 0x2000;
        end = 0x2000;
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::memory_access,
               "Destroyed provider owner cannot execute service");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        reject_input([&] { Session duplicate(r, provider, {}, slots); },
                     "Duplicate live CRT owner rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto changed = provider;
        changed.back() ^= std::byte{1};
        reject_input([&] { Session s(r, changed, {}, slots); },
                     "Changed provider rejected before state publication");
        check(r.service_count() == 0 && r.service_continuation_count() == 0,
              "Rejected provider registers no callbacks");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Proof p;
        p.domain = Domain::admitted_game;
        reject_input([&] { Session s(r, provider, p, slots); },
                     "Game and authored service proofs separated");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r);
        r.freeze_registry();
        begin = 0x2001;
        end = 0x2004;
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::memory_access,
               "Unsupported unaligned initializer domain rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        Session s(r, provider, {}, slots);
        setup(r);
        r.freeze_registry();
        begin = 0x8000;
        end = 0x8004;
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::memory_access,
               "Checked unmapped table fault propagates and poisons");
        check(r.poisoned(), "Required service memory fault poisons context");
    }
}
} // namespace
int main(int argc, char **argv) {
    try {
        if (argc != 2)
            throw std::runtime_error("Exact staged provider required as original data");
        std::ifstream file(argv[1], std::ios::binary | std::ios::ate);
        if (!file || file.tellg() != 266293)
            throw std::runtime_error("Exact provider size");
        provider.resize(266293);
        file.seekg(0);
        file.read(reinterpret_cast<char *>(provider.data()), 266293);
        if (!file)
            throw std::runtime_error("Exact provider read");
        tests();
        std::cout << checks
                  << " authored CRT native-service controls passed; original equivalence pending\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
