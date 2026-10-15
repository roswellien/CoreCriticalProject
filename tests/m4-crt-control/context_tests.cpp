#include "native_context.hpp"
#include "probe_io.hpp"
#include "probe_spec.hpp"
#include <iostream>
using namespace mw34;
using namespace mw34::m4_crt_probe;
namespace cf = mw34::m4_crt_control;
extern "C" void *sub_780042f7(State *, std::uint32_t, void *);
namespace {
unsigned checks{};
void check(bool b, const char *why) {
    need(b, why);
    ++checks;
}
struct Fixture {
    GuestMemory memory;
    State state{};
    std::array<std::byte, 512> fx{};
    cf::Context context;
    explicit Fixture(std::span<const std::uint8_t> pack) : context(memory, state, fx) {
        std::memset(&state, 0, sizeof(state));
        memory.map(GuestAddress{0x20001000}, 4096, Permissions::read | Permissions::write);
        for (unsigned i = 0; i < 2; ++i) {
            std::uint32_t base{};
            std::memcpy(&base, pack.data() + 12 + i * 4104, 4);
            memory.map(GuestAddress{base}, 4096, Permissions::read | Permissions::write);
            memory.write(GuestAddress{base}, std::as_bytes(pack.subspan(20 + i * 4104, 4096)));
            memory.protect(GuestAddress{base}, Permissions::read | Permissions::execute);
        }
        state.gpr.rip.dword = 0x780042f7;
        state.gpr.rsp.dword = 0x20001800;
        state.x87.fxsave.cwd.flat = 0x37f;
        state.x87.fxsave.mxcsr.flat = 0x1f80;
        std::memcpy(fx.data(), &state.x87, 512);
        memory.store<std::uint32_t>(GuestAddress{0x20001800}, 0x10000100);
        memory.store<std::uint32_t>(GuestAddress{0x20001804}, 0);
        memory.store<std::uint32_t>(GuestAddress{0x20001808}, 0);
    }
    void execute() {
        if (setjmp(context.boundary) == 0)
            (void)sub_780042f7(&state, state.gpr.rip.dword, &context);
    }
    void rejected(const char *why) {
        execute();
        check(context.failed && context.reason && std::strcmp(context.reason, why) == 0,
              "Required compiled-body causal diagnostic");
    }
};
void tests(std::span<const std::uint8_t> pack) {
    {
        Fixture f(pack);
        f.execute();
        check(!f.context.failed && f.context.depth == 0 && f.context.count == 6,
              "Actual compiled query reaches exact CALL/RET closure");
    }
    {
        Fixture f(pack);
        f.memory.protect(GuestAddress{0x20001000}, Permissions::read);
        f.rejected("Required checked32-bit write fault");
        check(f.memory.load<std::uint32_t>(GuestAddress{0x20001800}) == 0x10000100 &&
                  f.context.count == 1,
              "Readonly denial retains source sentinel and reached prefix");
    }
    {
        Fixture f(pack);
        f.memory.unmap(GuestAddress{0x20001000});
        f.rejected("Required checked32-bit read fault");
        check(f.context.count == 0, "Missing initial frame cannot fabricate route event");
    }
    for (unsigned kind = 0; kind < 4; ++kind) {
        Fixture f(pack);
        if (kind == 0)
            f.state.x87.fxsave.swd.flat = 1;
        if (kind == 1)
            f.state.x87.fxsave.swd.flat = 0x800;
        if (kind == 2)
            f.state.x87.fxsave.ftw.flat = 1;
        if (kind == 3)
            f.state.sw.pe = 1;
        auto before = f.state.x87;
        f.rejected("Unsupported guest FWAIT pending/nonempty state");
        check(std::memcmp(&before, &f.state.x87, 512) == 0 && f.context.count == 1,
              "Unsupported FWAIT never resets FP or completes ledger");
    }
    {
        Fixture f(pack);
        f.state.x87.fxsave.cwd.flat = 0x27f;
        f.rejected("Required typed FNSTCW fault");
        check(f.state.x87.fxsave.cwd.flat == 0x27f &&
                  f.context.cw.fault() == m4_guest_cw::Fault::unsupported_state,
              "CW mismatch retains guest input and required fault");
    }
    {
        Fixture f(pack);
        f.state.gpr.rip.dword = 0x780042f8;
        f.rejected("Unadmitted actual outer provider route");
    }
    {
        Fixture f(pack);
        f.memory.store<std::uint32_t>(GuestAddress{0x20001800}, 0x78004308);
        f.rejected("Unadmitted actual outer provider route");
    }
    for (unsigned kind = 0; kind < 2; ++kind) {
        Fixture f(pack);
        f.memory.protect(GuestAddress{0x78004000}, Permissions::read | Permissions::write);
        f.memory.store<std::uint8_t>(GuestAddress{kind ? 0x78004304U : 0x78004303U}, 0);
        f.memory.protect(GuestAddress{0x78004000}, Permissions::read | Permissions::execute);
        f.rejected(kind ? "Actual direct CALL target rejected"
                        : "Actual CALL source admission failed");
        check(f.context.count == 1, "Changed actual CALL retains incomplete prefix");
    }
    {
        Fixture f(pack);
        f.memory.protect(GuestAddress{0x78004000}, Permissions::none);
        f.rejected("Actual CALL source admission failed");
    }
    {
        Fixture f(pack);
        State other{};
        if (setjmp(f.context.boundary) == 0)
            (void)mw34_cf_enter(&other, 0x780042f7, &f.context);
        check(f.context.failed && std::strcmp(f.context.reason,
                                              "Wrong persistent State or actual entry route") == 0,
              "Wrong State identity causal denial");
    }
    {
        Fixture f(pack);
        if (setjmp(f.context.boundary) == 0)
            (void)__remill_function_return(&f.state, 0x10000100, &f.context);
        check(f.context.failed &&
                  std::strcmp(f.context.reason, "Required return State/frame missing") == 0,
              "Missing return frame required denial");
    }
    for (unsigned kind = 0; kind < 2; ++kind) {
        Fixture f(pack);
        if (setjmp(f.context.boundary) == 0) {
            f.context.enter(&f.state, 0x780042f7);
            f.state.gpr.rip.dword = 0x10000100;
            f.state.gpr.rsp.dword = kind ? 0x20001804 : 0x20001808;
            if (kind)
                f.state.gpr.rbx.dword = 1;
            f.context.returned(&f.state, 0x10000100);
        }
        check(f.context.failed &&
                  std::strcmp(f.context.reason,
                              "Actual RET/nonvolatile/cleanup contract rejected") == 0,
              "Bad cleanup/nonvolatile causal return denial");
    }
    {
        Fixture f(pack);
        if (setjmp(f.context.boundary) == 0)
            (void)mw34_cf_load_cw(&f.state, 0x20001fff, &f.context);
        check(f.context.failed && f.context.cw.fault() == m4_guest_cw::Fault::operand_bounds,
              "Typed bridge operand end rejected without retry success");
    }
}
} // namespace
int main(int argc, char **argv) {
    try {
        need(argc == 2, "Context tests: exact-private-pack");
        const auto pack = read(argv[1], 8220);
        need(pack.size() == 8220 && digest(pack) == cf::pack_sha,
             "Exact private context code binding");
        tests(pack);
        std::cout << checks << " authored compiled-provider routing/fault controls passed\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
