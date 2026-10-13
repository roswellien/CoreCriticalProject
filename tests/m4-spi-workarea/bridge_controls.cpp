// Authored fault injection only. The production caller/query source is compiled
// with private Context fields exposed for causal tests; its public API is intact.
// A local fixture replaces only the host query token. This is never a provider
// oracle, a native service backend, or evidence of an actual BOOLfalse query.
#include "common.hpp"
#include "image_loader.hpp"
#include <remill/Arch/X86/Runtime/State.h>

#include <memory>
static unsigned fixture_calls{};
static BOOL fixture_result{};
static RECT fixture_rect{};
static BOOL WINAPI authored_query(UINT action, UINT param, PVOID data, UINT flags) {
    mw34::spi::require(action == SPI_GETWORKAREA && !param && !flags && data,
                       "Authored query received wrong arguments");
    ++fixture_calls;
    if (fixture_result)
        *static_cast<RECT *>(data) = fixture_rect;
    return fixture_result;
}
#define SystemParametersInfoA authored_query
#define main spi_primary_main_not_run
#define class struct
#include "../../tools/m4-spi-workarea/native.cpp"
#undef class
#undef main
#undef SystemParametersInfoA
using namespace mw34::spi;
using mw34::Permissions;
static void prepare(Context &c) {
    c.fixture(2);
    seed(c.state, 0x37f, 0, 2, 0);
    c.active = true;
    c.used = true;
    c.state.gpr.rax.dword = output;
    c.state.gpr.rcx.dword = 0;
    c.state.gpr.rbx.dword = object;
    c.state.gpr.rsi.dword = 0x5e6018;
    c.state.gpr.rdi.dword = output;
    c.state.gpr.rsp.dword = frame - 32;
    c.state.gpr.rip.dword = call;
    const unsigned values[]{resume, 0x30, 0, output, 0};
    for (unsigned i = 0; i < 5; ++i)
        c.memory.store<unsigned>({frame - 32 + i * 4}, values[i]);
}
static void text(const std::filesystem::path &p, const char *s) {
    std::ofstream f(p, std::ios::binary);
    require(bool(f), "Control sentinel unavailable");
    f << s;
}
static std::string contents(const std::filesystem::path &p) {
    std::ifstream f(p, std::ios::binary);
    return std::string((std::istreambuf_iterator<char>(f)), {});
}
int main(int argc, char **argv) {
    try {
        require(argc == 4, "Usage: controls pack image fresh-control-dir");
        auto pack = admit(argv[1], argv[2]);
        check_import(read(argv[2], 2384384));
        std::filesystem::path out(argv[3]);
        require(!std::filesystem::exists(out), "Fresh fixture directory required");
        require(std::filesystem::create_directory(out), "Fixture directory unavailable");
        unsigned denied{}, faithful{}, ownership{};
        for (unsigned mode = 0; mode < 15; ++mode) {
            Record r{};
            Context c(pack, r);
            prepare(c);
            fixture_calls = 0;
            unsigned pc = call, owner = iat;
            switch (mode) {
            case 0:
                c.active = false;
                break;
            case 1:
                c.failed = true;
                break;
            case 2:
                c.queries = 1;
                break;
            case 3:
                pc = call + 1;
                break;
            case 4:
                owner = iat + 4;
                break;
            case 5:
                c.state.gpr.rip.dword = call + 1;
                break;
            case 6:
                c.state.gpr.rsp.dword = frame - 28;
                break;
            case 7:
                c.memory.store<unsigned>({frame - 32}, resume + 1);
                break;
            case 8:
                c.memory.store<unsigned>({frame - 28}, 0x2f);
                break;
            case 9:
                c.memory.store<unsigned>({frame - 24}, 1);
                break;
            case 10:
                c.memory.store<unsigned>({frame - 20}, output + 4);
                break;
            case 11:
                c.memory.store<unsigned>({frame - 16}, 1);
                break;
            case 12:
                c.state.aflag.df = 1;
                break;
            case 13:
                c.state.addr.ss_base.dword = 4;
                break;
            case 14:
                c.memory.protect({0x608000}, Permissions::none);
                break;
            }
            bool rejected{};
            try {
                c.query(pc, owner);
            } catch (const std::exception &) {
                rejected = true;
            }
            require(rejected && !fixture_calls && !r.service.called,
                    "Invalid query reached authored fixture");
            ++denied;
        }
        for (BOOL result : {BOOL(0), BOOL(1), BOOL(-19)}) {
            Record r{};
            Context c(pack, r);
            c.fixture(2);
            seed(c.state, 0x37f, 0, 2, 0);
            RECT before{};
            c.memory.read({output}, std::as_writable_bytes(std::span{&before, 1}));
            fixture_result = result;
            fixture_rect = {-313, 17, 2048, 777};
            fixture_calls = 0;
            c.enter();
            const auto expected = result ? fixture_rect : before;
            require(c.completed && fixture_calls == 1 &&
                        r.service.BOOL_value == static_cast<unsigned>(result) &&
                        c.state.gpr.rax.dword == object,
                    "Caller altered/discarded BOOL contract");
            RECT got{};
            c.memory.read({output}, std::as_writable_bytes(std::span{&got, 1}));
            require(std::memcmp(&got, &expected, 16) == 0,
                    "Authored false/true RECT transport changed bytes");
            require(c.state.gpr.rcx.dword == 0 && c.state.gpr.rdx.dword == initial(2).gpr[2] &&
                        cpu(c.state).flags == initial(2).flags,
                    "Representative volatility policy changed");
            ++faithful;
        }
        auto dst = out / "existing-result.bin";
        text(dst, "external-result");
        bool bad{};
        try {
            Output f(dst.string().c_str());
        } catch (const std::exception &) {
            bad = true;
        }
        require(bad && contents(dst) == "external-result", "Existing result overwritten");
        ++ownership;
        dst = out / "stage-result.bin";
        auto stage = std::filesystem::path(dst.string() + ".spi-stage-" +
                                           std::to_string(GetCurrentProcessId()));
        text(stage, "external-stage");
        bad = false;
        try {
            Output f(dst.string().c_str());
        } catch (const std::exception &) {
            bad = true;
        }
        require(bad && !std::filesystem::exists(dst) && contents(stage) == "external-stage",
                "Existing stage removed/overwritten");
        ++ownership;
        dst = out / "late-result.bin";
        stage = std::filesystem::path(dst.string() + ".spi-stage-" +
                                      std::to_string(GetCurrentProcessId()));
        bad = false;
        {
            Output f(dst.string().c_str());
            const unsigned v = 0x12345678;
            f.write(&v, 4);
            text(dst, "late-external-result");
            try {
                f.commit();
            } catch (const std::exception &) {
                bad = true;
            }
        }
        require(bad && contents(dst) == "late-external-result" && !std::filesystem::exists(stage),
                "Late result/owned stage semantics failed");
        ++ownership;
        std::cout << "{\"passed\":true,\"authored_query_denials\":" << denied
                  << ",\"authored_BOOL_transport\":" << faithful
                  << ",\"output_ownership\":" << ownership
                  << ",\"actual_provider_execution\":false}\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
