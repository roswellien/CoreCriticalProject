#include "admission.hpp"
#include "runtime.hpp"
#include <fstream>
#include <iostream>
#include <iterator>

using namespace mw34;
using namespace mw34::m4_runtime;
namespace {
unsigned checks{};
std::vector<std::byte> provider;
std::vector<std::byte> game;
void check(bool ok, const char *why) {
    if (!ok)
        throw std::runtime_error(why);
    ++checks;
}
template <class F> void reject(F fn, FaultReason expected, const char *why) {
    try {
        fn();
    } catch (const Fault &f) {
        check(f.reason() == expected, why);
        return;
    }
    throw std::runtime_error(why);
}
m4::LoadedImage fixture() {
    m4::LoadedImage x;
    const auto rx = Permissions::read | Permissions::execute;
    x.metadata.image_base = 0x1000;
    x.metadata.entry_point = GuestAddress{0x1100};
    x.memory.map(GuestAddress{0x1000}, 4096, rx);
    x.memory.map(GuestAddress{0x3000}, 4096, Permissions::read | Permissions::write);
    x.memory.store<std::uint32_t>(GuestAddress{0x3000}, 0x12345678);
    x.memory.protect(GuestAddress{0x3000}, Permissions::read);
    x.metadata.mapped_regions = {{"authored-only", GuestAddress{0x1000}, 4096, rx}};
    m4::ImportSymbol i;
    i.library = "AUTHORED_TEST.dll";
    i.name = "_initterm";
    i.iat_rva = 0x2000;
    i.original_iat_value = 0x12345678;
    x.metadata.imports.push_back(i);
    return x;
}
Policy policy() {
    Policy p;
    p.stack_bytes = 8192;
    p.heap_bytes = 8192;
    return p;
}
ServiceContinuation evidence() {
    // Reviewed identity only. Vendor code bytes remain in the user's private
    // staged provider/extraction, never embedded into distributable tests.
    ServiceContinuation c;
    c.code_start = GuestAddress{0x780014f8};
    c.call_pc = GuestAddress{0x7800150e};
    c.return_pc = GuestAddress{0x78001510};
    c.service_iat_slot = GuestAddress{0x3000};
    c.source_bytes = 28;
    c.provider_sha256 = "2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7";
    c.source_sha256 = "960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678";
    c.name = "_initterm";
    return c;
}
Translation translation(unsigned pc, NativeEntry fn) {
    return {GuestAddress{pc}, {}, fn, "authored callback", {}};
}
void leaf(Runtime &r) {
    check(r.memory().load<std::uint32_t>(GuestAddress{r.cpu().esp}) == 0x78001510,
          "Real provider callback return DWORD");
    r.cpu().eax = 0xabcdef01;
    r.ret();
}
void service(Runtime &r) {
    r.cpu().eip = 0x7800150e;
    r.call_direct(GuestAddress{0x1200}, GuestAddress{0x78001510});
    r.ret();
}
void wrong_site(Runtime &r) {
    r.cpu().eip = 0x7800150f;
    r.call_direct(GuestAddress{0x1200}, GuestAddress{0x78001510});
    r.ret();
}
void nonservice(Runtime &r) {
    r.cpu().eip = 0x7800150e;
    r.call_direct(GuestAddress{0x1200}, GuestAddress{0x78001510});
    r.ret();
}
void captured_mutation(Runtime &r) {
    const auto return_pc = r.memory().load<std::uint32_t>(GuestAddress{r.cpu().esp});
    r.memory().protect(GuestAddress{0x780014f8}, Permissions::read | Permissions::write);
    r.memory().store<std::uint8_t>(GuestAddress{0x7800150e}, 0);
    r.memory().protect(GuestAddress{0x780014f8}, Permissions::read | Permissions::execute);
    r.cpu().esp += 4;
    r.cpu().eip = return_pc; // Generated-adapter style direct RET capture.
}
void captured_service(Runtime &r) {
    r.cpu().eip = 0x7800150e;
    r.call_direct(GuestAddress{0x1250}, GuestAddress{0x78001510});
    r.ret();
}
void outer(Runtime &r) {
    r.call_import(GuestAddress{0x3000}, GuestAddress{0x1110});
    r.ret();
}
void bind(Runtime &r, NativeEntry cb = service) {
    r.register_service({GuestAddress{0x3000},
                        {},
                        cb,
                        "authored service",
                        Domain::authored_fixture,
                        evidence().provider_sha256,
                        {}});
    r.register_translation(translation(0x1100, outer));
    r.register_translation(translation(0x1200, leaf));
}
void tests() {
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        bind(r);
        r.register_service_continuation(provider, evidence());
        check(r.service_continuation_count() == 1, "One exact provider continuation");
        check(r.memory().load<std::uint8_t>(GuestAddress{0x7800150e}) == 0xff,
              "Original provider CALL bytes readable");
        try {
            r.memory().store<std::uint8_t>(GuestAddress{0x7800150e}, 0);
            throw std::runtime_error("RX provider write accepted");
        } catch (const MemoryFault &e) {
            check(e.reason() == MemoryFaultReason::permission_denied,
                  "Provider exact source RX protection");
        }
        try {
            (void)r.memory().load<std::uint8_t>(GuestAddress{0x78001514});
            throw std::runtime_error("Adjacent provider bytes mapped");
        } catch (const MemoryFault &e) {
            check(e.reason() == MemoryFaultReason::unmapped, "Only exact reviewed source mapped");
        }
        r.freeze_registry();
        const auto sp = r.cpu().esp;
        r.invoke(GuestAddress{0x1100});
        check(r.cpu().esp == sp && r.cpu().eip == Runtime::external_return &&
                  r.cpu().eax == 0xabcdef01,
              "Nested service/callback ABI returns");
        check(r.calls().size() == 3 && r.calls()[2].site.value == 0x7800150e &&
                  r.calls()[2].return_pc.value == 0x78001510 && r.calls()[2].completed,
              "Exact provider CALL route record");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        bind(r);
        r.freeze_registry();
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::abi_violation,
               "Unadmitted provider return rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        bind(r, wrong_site);
        r.register_service_continuation(provider, evidence());
        r.freeze_registry();
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::abi_violation,
               "Wrong original provider CALL site rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.register_translation(translation(0x1100, nonservice));
        r.register_translation(translation(0x1200, leaf));
        r.register_service_continuation(provider, evidence());
        r.freeze_registry();
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::abi_violation,
               "Provider route requires owning active service");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto e = evidence();
        e.provider_sha256[0] = '0';
        reject([&] { r.register_service_continuation(provider, e); }, FaultReason::invalid_binding,
               "Changed provider identity rejected");
        check(r.service_continuation_count() == 0, "Bad provider publishes no continuation");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto e = evidence();
        e.source_sha256[0] = e.source_sha256[0] == '0' ? '1' : '0';
        reject([&] { r.register_service_continuation(provider, e); }, FaultReason::invalid_binding,
               "Changed exact source identity rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto e = evidence();
        e.return_pc = GuestAddress{0x78001511};
        reject([&] { r.register_service_continuation(provider, e); }, FaultReason::invalid_binding,
               "Continuation must follow exact CALL encoding");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto e = evidence();
        e.domain = Domain::admitted_game;
        reject([&] { r.register_service_continuation(provider, e); }, FaultReason::invalid_binding,
               "Authored and game continuation domains separate");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto e = evidence();
        e.service_iat_slot = GuestAddress{0x3010};
        reject([&] { r.register_service_continuation(provider, e); }, FaultReason::invalid_binding,
               "Provider continuation requires real named IAT owner");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.register_service_continuation(provider, evidence());
        reject([&] { r.register_service_continuation(provider, evidence()); },
               FaultReason::invalid_binding, "Duplicate continuation rejected");
        r.freeze_registry();
        reject([&] { r.register_service_continuation(provider, evidence()); },
               FaultReason::registry_frozen, "Frozen continuation registry rejects mutation");
    }
    {
        auto p = policy();
        p.heap_low = GuestAddress{0x78000000};
        auto r = Runtime::for_authored_fixture(fixture(), p);
        reject([&] { r.register_service_continuation(provider, evidence()); },
               FaultReason::invalid_binding, "Provider/thread overlap rejected before mapping");
        check(r.memory().load<std::uint32_t>(GuestAddress{0x780014f8}) == 0,
              "Existing arena preserved on overlap rejection");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.register_service_continuation(provider, evidence());
        reject([&] { r.register_translation(translation(0x780014f8, leaf)); },
               FaultReason::invalid_binding,
               "Continuation code does not authorize game translation entry");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        bind(r);
        r.register_service_continuation(provider, evidence());
        r.memory().protect(GuestAddress{0x780014f8}, Permissions::read | Permissions::write);
        r.memory().store<std::uint8_t>(GuestAddress{0x7800150e}, 0);
        r.freeze_registry();
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::invalid_binding,
               "Changed protected source detected at routing");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto e = evidence();
        e.source_bytes = 0;
        reject([&] { r.register_service_continuation(provider, e); }, FaultReason::invalid_binding,
               "Zero source span rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        bind(r, captured_service);
        r.register_translation(translation(0x1250, captured_mutation));
        r.register_service_continuation(provider, evidence());
        r.freeze_registry();
        reject([&] { r.invoke(GuestAddress{0x1100}); }, FaultReason::invalid_binding,
               "Direct-captured RET rechecks exact provider source at generic exit");
        check(r.poisoned() && r.calls().size() == 3 && !r.calls()[2].completed,
              "Changed source direct RET cannot publish completed callback");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.register_service_continuation(provider, evidence());
        reject(
            [&] {
                r.register_service({GuestAddress{0x3000},
                                    {},
                                    service,
                                    "wrong provider",
                                    Domain::authored_fixture,
                                    std::string(64, '0'),
                                    {}});
            },
            FaultReason::invalid_binding, "Continuation-first different service provider rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.register_service({GuestAddress{0x3000},
                            {},
                            service,
                            "wrong provider",
                            Domain::authored_fixture,
                            std::string(64, '0'),
                            {}});
        reject([&] { r.register_service_continuation(provider, evidence()); },
               FaultReason::invalid_binding,
               "Service-first different continuation provider rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        auto e = evidence();
        e.gate_report_sha256 = std::string(64, '1');
        r.register_service_continuation(provider, e);
        reject(
            [&] {
                r.register_service({GuestAddress{0x3000},
                                    {},
                                    service,
                                    "wrong gate",
                                    Domain::authored_fixture,
                                    e.provider_sha256,
                                    std::string(64, '2')});
            },
            FaultReason::invalid_binding, "Continuation-first different service gate rejected");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.register_service({GuestAddress{0x3000},
                            {},
                            service,
                            "wrong gate",
                            Domain::authored_fixture,
                            evidence().provider_sha256,
                            std::string(64, '2')});
        reject([&] { r.register_service_continuation(provider, evidence()); },
               FaultReason::invalid_binding, "Service-first different continuation gate rejected");
    }
    // Actual-image registry admission negatives only. Placeholder artifact/gate
    // syntax is not an actual service proof; these callbacks are never invoked.
    {
        auto r = Runtime::from_admitted_image(game);
        auto e = evidence();
        e.domain = Domain::admitted_game;
        e.service_iat_slot = GuestAddress{0x5bb510};
        e.native_artifact_sha256 = std::string(64, '1');
        e.gate_report_sha256 = std::string(64, '2');
        r.register_service_continuation(provider, e);
        reject(
            [&] {
                r.register_service({e.service_iat_slot,
                                    {},
                                    service,
                                    "rejection-only",
                                    Domain::admitted_game,
                                    std::string(64, '0'),
                                    e.gate_report_sha256});
            },
            FaultReason::invalid_binding, "Actual IAT continuation-first wrong provider rejected");
        check(r.service_count() == 0, "Actual rejected service not published");
    }
    {
        auto r = Runtime::from_admitted_image(game);
        auto e = evidence();
        e.domain = Domain::admitted_game;
        e.service_iat_slot = GuestAddress{0x5bb510};
        e.native_artifact_sha256 = std::string(64, '1');
        e.gate_report_sha256 = std::string(64, '2');
        r.register_service({e.service_iat_slot,
                            {},
                            service,
                            "rejection-only",
                            Domain::admitted_game,
                            std::string(64, '0'),
                            e.gate_report_sha256});
        reject([&] { r.register_service_continuation(provider, e); }, FaultReason::invalid_binding,
               "Actual IAT service-first wrong provider rejected");
        check(r.service_continuation_count() == 0, "Actual rejected continuation not published");
    }
}
} // namespace
int main(int argc, char **argv) {
    try {
        if (argc != 3)
            throw std::runtime_error("Exact original provider/game inputs required as data");
        std::ifstream file(argv[1], std::ios::binary | std::ios::ate);
        if (!file || file.tellg() != 266293)
            throw std::runtime_error("Exact provider size required");
        provider.resize(266293);
        file.seekg(0);
        file.read(reinterpret_cast<char *>(provider.data()), 266293);
        if (!file || m4::sha256(provider) != evidence().provider_sha256)
            throw std::runtime_error("Exact provider identity required");
        std::ifstream game_file(argv[2], std::ios::binary | std::ios::ate);
        if (!game_file || game_file.tellg() != 2384384)
            throw std::runtime_error("Exact game size required");
        game.resize(2384384);
        game_file.seekg(0);
        game_file.read(reinterpret_cast<char *>(game.data()), 2384384);
        if (!game_file ||
            m4::sha256(game) != "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf")
            throw std::runtime_error("Exact game identity required");
        tests();
        std::cout << checks
                  << " service-continuation authored controls passed; original provider bytes read "
                     "only, no body executed\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
