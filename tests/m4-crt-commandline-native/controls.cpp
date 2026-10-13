#include "registry.hpp"

#include "common.hpp"
#include <iostream>
using namespace mw34;
using namespace mw34::m4_cmd_native;
static State seed() {
    State s{};
    s.gpr.rip.dword = writer.value;
    s.gpr.rsp.dword = 0x20001800;
    s.gpr.rax.dword = 0x13579bdf;
    s.gpr.rcx.dword = 0x2468ace0;
    s.gpr.rdx.dword = 0x81726354;
    s.gpr.rbx.dword = 0x10293847;
    s.gpr.rbp.dword = 0x92837465;
    s.gpr.rsi.dword = 0x56473829;
    s.gpr.rdi.dword = 0xaabbccdd;
    s.x87.fxsave.cwd.flat = 0x37f;
    s.x87.fxsave.mxcsr.flat = 0x1f80;
    s.rflag.flat = 0x202;
    return s;
}
static bool absent(GuestMemory &m, GuestAddress a) {
    try {
        (void)m.load<unsigned>(a);
        return false;
    } catch (const MemoryFault &e) {
        return e.reason() == MemoryFaultReason::unmapped;
    }
}
struct Isolation {
    alignas(16) std::array<std::byte, 512> saved{}, after{};
    std::array<std::byte, 28> env{}, ae{};
    Isolation() {
        __asm__ volatile("fxsave64 %0\n\tfnstenv %1" : "=m"(saved), "=m"(env)::"memory");
    }
    void restore() {
        __asm__ volatile("fxrstor64 %2\n\tfldenv %3\n\tfxsave64 %0\n\tfnstenv %1"
                         : "=m"(after), "=m"(ae)
                         : "m"(saved), "m"(env)
                         : "memory", "st", "st(1)", "st(2)", "st(3)", "st(4)", "st(5)", "st(6)",
                           "st(7)", "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7",
                           "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
        require(std::equal(saved.begin(), saved.begin() + 5, after.begin()) &&
                    std::equal(saved.begin() + 24, saved.begin() + 28, after.begin() + 24) &&
                    env == ae,
                "Control host FP core/ENV restoration");
        for (unsigned i = 0; i < 8; ++i)
            require(std::equal(saved.begin() + 32 + i * 16, saved.begin() + 42 + i * 16,
                               after.begin() + 32 + i * 16),
                    "Control host raw80 restoration");
        require(std::equal(saved.begin() + 160, saved.begin() + 416, after.begin() + 160),
                "Control host SIMD restoration");
    }
    ~Isolation() {
        __asm__ volatile("fxrstor64 %0\n\tfldenv %1" ::"m"(saved), "m"(env)
                         : "memory", "st", "st(1)", "st(2)", "st(3)", "st(4)", "st(5)", "st(6)",
                           "st(7)", "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7",
                           "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
    }
};
int main(int argc, char **argv) {
    try {
        require(argc == 4, "Control exact inputs");
        auto game = readfile(argv[1], 2384384), provider = readfile(argv[2], 266293),
             pack = readfile(argv[3], 12324);
        unsigned checks{}, scenarios{};
        for (unsigned mode = 0; mode < 30; ++mode) {
            std::cerr << "control-mode " << mode << std::endl;
            auto runtime = m4_runtime::Runtime::from_admitted_image(game);
            auto &m = runtime.memory();
            State s = seed();
            m.store<unsigned>({0x20001800}, capture_gate.value);
            bool collision = mode == 3 || mode == 4 || mode == 5 || mode == 13;
            GuestAddress foreign = mode == 3   ? GuestAddress{0x78001000}
                                   : mode == 4 ? GuestAddress{0x7802e000}
                                   : mode == 5 ? GuestAddress{0x78037000}
                                               : buffer_start;
            if (collision) {
                m.map(foreign, 16, Permissions::read | Permissions::write);
                m.store<unsigned>(foreign, 0xfeedbaad);
            }
            {
                Registry r(runtime);
                auto file = provider, input = pack;
                if (mode == 1)
                    file[0] ^= std::byte{1};
                if (mode == 2)
                    input[100] ^= std::byte{1};
                bool admitted = r.admit(file, input);
                if (mode >= 1 && mode <= 5) {
                    require(!admitted && r.first_fault() && !r.ready(),
                            "Bad source/collision admitted");
                    ++checks;
                } else {
                    require(admitted, "Authored positive ownership admission failed");
                    switch (mode) {
                    case 6:
                        s.gpr.rip.dword += 1;
                        break;
                    case 7:
                        s.gpr.rsp.dword += 4;
                        break;
                    case 8:
                        s.aflag.df = 1;
                        break;
                    case 9:
                        s.addr.ds_base.dword = 4;
                        break;
                    case 10:
                        s.addr.ss_base.dword = 4;
                        break;
                    case 11:
                        m.protect({0x20000000}, Permissions::read);
                        break;
                    case 12:
                        m.protect({0x78037000}, Permissions::read);
                        break;
                    case 14:
                        m.protect({0x78001000}, Permissions::read | Permissions::write);
                        m.store<unsigned>(writer, 0);
                        break;
                    case 15:
                        m.protect({0x7802e000}, Permissions::read | Permissions::write);
                        m.store<unsigned>(provider_iat, 1);
                        break;
                    case 16:
                        m.protect({0x5bb000}, Permissions::read | Permissions::write);
                        m.store<unsigned>(game_iat, 1);
                        break;
                    case 17:
                        m.store<unsigned>(provider_global, 1);
                        break;
                    case 18:
                        m.protect({0x7802e000}, Permissions::none);
                        break;
                    case 19:
                        m.protect({0x78037000}, Permissions::none);
                        break;
                    case 25:
                        m.unmap({0x20000000});
                        break;
                    case 26:
                        m.unmap({0x78037000});
                        break;
                    case 27:
                        m.unmap({0x7802e000});
                        break;
                    case 28:
                        m.unmap({0x78001000});
                        break;
                    case 29:
                        require(!r.compiled_service(&s, service_gate.value),
                                "Inactive wrong service entered");
                        break;
                    }
                    bool ok;
                    {
                        Isolation isolation;
                        ok = r.initialize(s);
                        isolation.restore();
                    }
                    ++checks;
                    if ((mode >= 6 && mode <= 19) || mode >= 25) {
                        require(!ok && !r.ready() && r.first_fault(),
                                "Bad actual writer context became complete");
                        ++checks;
                        if (mode == 12 || mode == 13)
                            require(!r.host_snapshot().bytes.empty(),
                                    "Late partial failure did not reach actual native query");
                        else
                            require(r.host_snapshot().bytes.empty(),
                                    "Entry/identity guard reached host query");
                        ++checks;
                    } else {
                        require(ok && r.ready() && r.compiled_capture_complete(),
                                "Real positive writer failed");
                        auto ptr = r.resolve_data(game_iat);
                        require(ptr && *ptr == provider_global &&
                                    m.load<unsigned>(*ptr) == buffer_start.value,
                                "Actual writer data-global result failed");
                        ++checks;
                        switch (mode) {
                        case 20:
                            require(!r.resolve_data({game_iat.value + 4}),
                                    "Unknown data import accepted");
                            break;
                        case 21:
                            m.store<unsigned>(provider_global, buffer_start.value + 4);
                            require(!r.resolve_data(game_iat), "Changed global accepted");
                            break;
                        case 22:
                            m.protect(buffer_start, Permissions::read | Permissions::write);
                            m.store<unsigned>(buffer_start, 0);
                            require(!r.resolve_data(game_iat),
                                    "Changed actual owning buffer accepted");
                            break;
                        case 23:
                            m.protect(buffer_start, Permissions::none);
                            require(!r.resolve_data(game_iat), "Unreadable own buffer accepted");
                            break;
                        case 24:
                            require(!r.initialize(s), "Used writer reentered");
                            break;
                        }
                        if (mode) {
                            require(r.first_fault() && !r.ready(),
                                    "Ready-state invalidation lost typed fault");
                            ++checks;
                        }
                    }
                }
                if (mode) {
                    const auto first = *r.first_fault();
                    require(!r.initialize(s) && !r.resolve_data(game_iat) &&
                                !r.admit(provider, pack),
                            "Failed registry reused");
                    require(r.first_fault()->reason == first.reason &&
                                r.first_fault()->site == first.site &&
                                r.first_fault()->detail == first.detail,
                            "First typed fault overwritten");
                    ++checks;
                }
            }
            if (collision) {
                require(m.load<unsigned>(foreign) == 0xfeedbaad,
                        "Collision cleanup deleted foreign sentinel");
                ++checks;
            }
            for (auto a : {GuestAddress{0x78001000}, GuestAddress{0x7802e000},
                           GuestAddress{0x78037000}, buffer_start})
                if (!collision || a != foreign) {
                    require(absent(m, a), "Failed/destructed ownership remained live");
                    ++checks;
                }
            ++scenarios;
        }
        // A live borrower is valid only until its owner is destroyed; old raw guest
        // address is then rejected. This does not give a host pointer lifetime.
        auto runtime = m4_runtime::Runtime::from_admitted_image(game);
        {
            Registry r(runtime);
            auto s = seed();
            require(r.admit(provider, pack) && r.initialize(s) && r.resolve_data(game_iat),
                    "Live borrower setup failed");
            ++checks;
        }
        require(absent(runtime.memory(), buffer_start),
                "Closed owned guest buffer remained addressable");
        ++checks;
        std::cout
            << "{\"passed\":true,\"scenarios\":" << scenarios + 1 << ",\"checks\":" << checks
            << ",\"initialization_denials_poison\":true,\"original_provider_execution\":false}\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
