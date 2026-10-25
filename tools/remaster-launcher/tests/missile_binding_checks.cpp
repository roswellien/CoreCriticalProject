// Asset-free integration checks include the production stage, with checked guest
// memory and host services supplied below. Optional private XYZ input is never
// embedded in this source or required for the public checks.
#include "../../../runtime/graphics/effect_lighting.hpp"
#include "../../../runtime/graphics/missile_exhaust.hpp"
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <Windows.h>
#include <cstdio>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <xmmintrin.h>

namespace mw34::vkscene {
struct HostFpEnvironment {
    unsigned short control{};
    unsigned mxcsr{};
    HostFpEnvironment() {
        __asm__ volatile("fnstcw %0" : "=m"(control));
        mxcsr = _mm_getcsr();
        const unsigned short host = 0x027f;
        __asm__ volatile("fnclex; fldcw %0" : : "m"(host));
        _mm_setcsr(0x1f80);
    }
    ~HostFpEnvironment() {
        __asm__ volatile("fldcw %0" : : "m"(control));
        _mm_setcsr(mxcsr);
    }
};
enum class TexFormat { rgba8888 };
struct TextureRef {
    std::uint64_t key{}, hash{};
    unsigned width{}, height{};
    TexFormat format{};
    std::vector<std::uint32_t> pixels32;
};
struct Scene {
    std::vector<TextureRef> textures;
};
struct Draw {
    int texture{-1};
};
} // namespace mw34::vkscene

namespace {
unsigned checks{};
void require(bool value, const char *message) {
    ++checks;
    if (!value)
        throw std::runtime_error(message);
}
// Same save/restore contract as sun_lighting_stage.inc; importantly this saves
// physical guest FP state, rather than making the fixture's guard a no-op.
struct SunCaptureFp {
    alignas(16) unsigned char fx[512];
    DWORD error{};
    SunCaptureFp() {
        __asm__ volatile("fxsave64 %0" : "=m"(fx) : : "memory");
        error = GetLastError();
    }
    ~SunCaptureFp() {
        SetLastError(error);
        __asm__ volatile("fxrstor64 %0"
                         :
                         : "m"(fx)
                         : "memory", "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7",
                           "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
    }
};
enum {
    WideWorld = 0,
    WideZoom = 6,
    D3DPT_TRIANGLELIST = 4,
    D3DRENDERSTATE_ALPHABLENDENABLE = 1,
    D3DRENDERSTATE_SRCBLEND,
    D3DRENDERSTATE_DESTBLEND,
    D3DRENDERSTATE_ZENABLE,
    D3DRENDERSTATE_ZWRITEENABLE,
    D3DRENDERSTATE_ZFUNC,
    D3DRENDERSTATE_ALPHATESTENABLE,
    D3DRENDERSTATE_COLORKEYENABLE,
    D3DRENDERSTATE_SPECULARENABLE,
    D3DRENDERSTATE_FOGENABLE,
    D3DRENDERSTATE_CULLMODE,
    D3DRENDERSTATE_SHADEMODE,
    D3DRENDERSTATE_TEXTUREPERSPECTIVE,
    D3DTSS_COLOROP = 1,
    D3DTSS_COLORARG1,
    D3DTSS_COLORARG2,
    D3DTSS_ALPHAOP,
    D3DTSS_ALPHAARG1,
    D3DTSS_ALPHAARG2,
    D3DTSS_MAGFILTER,
    D3DTSS_MINFILTER,
    D3DTSS_ADDRESSU,
    D3DTSS_ADDRESSV,
    D3DBLEND_SRCALPHA = 5,
    D3DBLEND_ONE = 2,
    D3DZB_TRUE = 1,
    D3DCMP_GREATEREQUAL = 7,
    D3DCULL_NONE = 1,
    D3DSHADE_GOURAUD = 2,
    D3DTOP_MODULATE = 4,
    D3DTA_TEXTURE = 2,
    D3DTA_DIFFUSE = 0,
    D3DTFG_LINEAR = 2,
    D3DTFN_LINEAR = 2,
    D3DTADDRESS_CLAMP = 3
};
struct D3DCmd {
    enum Kind { Draw };
    Kind kind{};
    unsigned flags{}, a{};
    float z{};
    std::vector<int> rects;
    std::vector<unsigned char> vertices;
    unsigned prim{};
    bool missile_exhaust{};
    unsigned hud_role{};
    std::shared_ptr<const std::vector<unsigned>> state_snapshot;
};
struct D3DDev {
    bool in_scene{true};
    std::vector<D3DCmd> commands;
};
struct State {
    struct Register {
        unsigned dword{};
    };
    struct Registers {
        Register rcx, rdx, rax;
    } gpr;
};
using Body = std::function<void *(State *, unsigned, void *)>;
using OverrideMatrix = std::array<double, 12>;
struct FakeRenderer {
    bool current(std::uint64_t, std::uint64_t, unsigned, unsigned) { return false; }
};
struct Stage {
    std::vector<unsigned char> memory = std::vector<unsigned char>(0x800000);
    State state;
    struct Host {
        unsigned frames{};
        std::vector<D3DDev> devices{1};
        std::unique_ptr<FakeRenderer> sren;
    } host;
    struct Effects {
        mw34::effects::Cache lights;
    } effect_lighting;
    bool frontend{}, preview{}, lights_on{true}, camera_available{true};
    unsigned role{WideWorld};
    double clock{1};
    OverrideMatrix camera{1, 0, 0, 100, 0, 1, 0, 200, 0, 0, 1, 300};
    bool readable(unsigned p, unsigned n) const {
        return p && p < memory.size() && n <= memory.size() - p;
    }
    unsigned load(unsigned p) const {
        if (!readable(p, 4))
            throw std::runtime_error("Fixture memory read outside bounds");
        unsigned v;
        std::memcpy(&v, memory.data() + p, 4);
        return v;
    }
    void store(unsigned p, unsigned v) {
        if (!readable(p, 4))
            throw std::runtime_error("Fixture memory write outside bounds");
        std::memcpy(memory.data() + p, &v, 4);
    }
    void number(unsigned p, float v) {
        unsigned bits;
        std::memcpy(&bits, &v, 4);
        store(p, bits);
    }
    void get_bytes(unsigned p, void *out, unsigned n) const {
        if (!readable(p, n))
            throw std::runtime_error("Fixture byte read outside bounds");
        std::memcpy(out, memory.data() + p, n);
    }
    std::string pose_name(unsigned p, unsigned n) const {
        if (!readable(p, n))
            return {};
        unsigned length = 0;
        while (length < n && memory[p + length])
            ++length;
        return std::string(reinterpret_cast<const char *>(memory.data() + p), length);
    }
    float world_float(unsigned p) const {
        const unsigned bits = load(p);
        float v;
        std::memcpy(&v, &bits, 4);
        return v;
    }
    float wide_float(unsigned p) const { return world_float(p); }
    bool frontend_on() const { return frontend; }
    bool override_status_preview() const { return preview; }
    unsigned wide_hud_role() const { return role; }
    unsigned override_parent(unsigned p) const {
        if (!readable(p, 100) || load(p + 0x54) != 1 || !readable(load(p + 0x58), 4))
            return 0;
        return load(load(p + 0x58));
    }
    OverrideMatrix override_matrix(unsigned p) const {
        OverrideMatrix m{};
        for (unsigned i = 0; i < 12; ++i)
            m[i] = world_float(p + i * 4);
        return m;
    }
    OverrideMatrix override_product(const OverrideMatrix &a, const OverrideMatrix &b) const {
        OverrideMatrix out{};
        for (unsigned r = 0; r < 3; ++r) {
            for (unsigned c = 0; c < 3; ++c)
                for (unsigned k = 0; k < 3; ++k)
                    out[r * 4 + c] += a[r * 4 + k] * b[k * 4 + c];
            out[r * 4 + 3] = a[r * 4 + 3];
            for (unsigned k = 0; k < 3; ++k)
                out[r * 4 + 3] += a[r * 4 + k] * b[k * 4 + 3];
        }
        return out;
    }
    double effect_time() const { return clock; }
    bool effect_enabled() const { return lights_on; }
    bool sun_camera_world(OverrideMatrix &m) const {
        m = camera;
        return camera_available;
    }
    void fixture_frame() {}
    void zoom_capture_command(D3DCmd &) {}
    std::vector<unsigned> snapshot(D3DDev &) { return std::vector<unsigned>(600); }
#include "../native-overrides/missile_exhaust_stage.inc"
};
constexpr unsigned definition = 0x1000, name = 0x2000, descriptor = 0x3000, root = 0x4000,
                   node = 0x5000, mesh = 0x6000, xyz = 0x7000;
void setup(Stage &s) {
    s.store(0x5f4c8c, 0x9000);
    s.store(definition, name);
    std::memcpy(s.memory.data() + name, "LRM5", 5);
    s.store(definition + 0x7c, descriptor);
    s.store(descriptor, 0);
    s.store(descriptor + 0x0c, root);
    s.store(descriptor + 0x20, 1);
    s.number(descriptor + 0x58c, 100);
    s.store(node + 0x3c, mesh);
    s.store(mesh + 0x10, 3);
    s.store(mesh + 0x14, 9);
    s.store(mesh + 0x38, xyz);
    s.store(node + 0x54, 1);
    s.store(node + 0x58, 0x8000);
    s.store(0x8000, root);
    s.store(0x5eda90, 0xa000);
    s.store(0xa000, 0xb000);
    const float matrix[]{1, 0, 0, 10, 0, 1, 0, 20, 0, 0, 1, 30};
    for (unsigned i = 0; i < 12; ++i)
        s.number(0xb000 + i * 4, matrix[i]);
    s.number(0x73fb80, 1);
    s.number(0x73fc30, 100);
    s.number(0x73fb98, 100);
    s.number(0x73fb88, 320);
    s.number(0x73fb8c, 240);
    s.number(0x740304, .1f);
}
void create(Stage &s) {
    s.state.gpr.rcx.dword = definition;
    unsigned calls = 0;
    void *expected = reinterpret_cast<void *>(std::uintptr_t(123));
    const auto result = s.missile_create_body(
        &s.state, 0x585010, nullptr, [&](State *state, unsigned target, void *) -> void * {
            ++calls;
            require(target == 0x585010, "Wrong original factory target");
            state->gpr.rcx.dword = 0xdeadbeef;
            state->gpr.rax.dword = descriptor;
            return expected;
        });
    require(calls == 1 && result == expected, "Factory must execute once and preserve result");
    require(s.missile_roots.size() == 1 && s.missile_roots.at(root).definition == definition,
            "Factory must bind entry ECX even when original changes RCX");
}
__declspec(noinline) void check_scope_fp(Stage &s, unsigned draw_node, bool end = false) {
    SunCaptureFp restore;
    alignas(16) unsigned char before[512]{}, after[512]{};
    const unsigned short control = 0x077f;
    __asm__ volatile("fldcw %0; fld1" : : "m"(control) : "memory");
    _mm_setcsr(0x5f80);
    SetLastError(12345);
    __asm__ volatile(
        "pcmpeqd %%xmm0,%%xmm0; pcmpeqd %%xmm1,%%xmm1; pcmpeqd %%xmm2,%%xmm2; fxsave64 %0"
        : "=m"(before)
        :
        : "memory", "xmm0", "xmm1", "xmm2");
    if (end)
        s.missile_end();
    else
        s.missile_begin(draw_node);
    __asm__ volatile("fxsave64 %0" : "=m"(after) : : "memory");
    require(GetLastError() == 12345, "Missile admission changed original last-error state");
    require(std::memcmp(before, after, 5) == 0, "Missile admission changed x87 control/status/tag");
    require(std::memcmp(before + 24, after + 24, 4) == 0, "Missile admission changed MXCSR");
    require(std::memcmp(before + 160, after + 160, 48) == 0, "Missile admission clobbered XMM0-2");
    if (!end)
        s.missile_end();
}
void public_checks() {
    // Exercise presentation after admission with authored dimensions. The
    // original body admission contract is checked independently below.
    {
        Stage emitted;
        setup(emitted);
        create(emitted);
        const auto before = emitted.memory;
        emitted.missile_scope = {emitted.missile_roots.at(root), node, -.04, .06, 1.27};
        emitted.missile_emit();
        require(emitted.host.devices[0].commands.size() == 1,
                "Stronger exhaust must keep one draw per source");
        require(emitted.host.devices[0].commands[0].vertices.size() ==
                    18 * sizeof(mw34::missiles::Vertex),
                "Larger exhaust unexpectedly increased particle geometry");
        const auto uniform =
            emitted.effect_lighting.lights.uniform(emitted.clock, {0, 0, 0}, 64, 1);
        require(uniform.params[0] == 1 && std::abs(uniform.lights[0].color[3] - 4.4f) < 1e-5f,
                "Actual emitted thrust light is not twice the previous strength");
        require(emitted.memory == before, "Exhaust gain changed original guest memory");
    }
    Stage s;
    setup(s);
    const auto original = s.memory;
    create(s);
    auto b = s.missile_roots.at(root);
    require(s.missile_live(b), "Live projectile rejected");
    s.store(descriptor + 0x20, 0);
    require(!s.missile_live(b), "Pending terminal projectile admitted");
    s.store(descriptor + 0x20, 1);
    s.number(descriptor + 0x58c, 0);
    require(!s.missile_live(b), "Pooled state-one descriptor admitted");
    s.number(descriptor + 0x58c, 100);
    s.store(definition + 0x7c, 0);
    require(!s.missile_live(b), "Unowned descriptor admitted");
    s.store(definition + 0x7c, descriptor);
    s.store(descriptor + 0x0c, root + 0x100);
    require(!s.missile_live(b), "Reused descriptor with different visual root admitted");
    s.store(descriptor + 0x0c, root);
    s.missile_begin(node);
    require(!s.missile_scope.node, "Unknown authored mesh admitted as an original missile");
    s.missile_end();
    check_scope_fp(s, node);
    check_scope_fp(s, 0);
    s.missile_begin(node);
    check_scope_fp(s, node, true);
    require(s.missile_scope_stack.empty(), "Scope exit did not balance entry");
    // Register a real cache entry through the public source-identity API, then
    // exercise the production stage's retirement and reuse paths.
    const auto id = (b.generation << 32) | node;
    const mw34::effects::Emitter emitter{7, 8, 2, .055f, {1, .36f, .06f}};
    s.effect_lighting.lights.observe_tracked(id, emitter, {{1, 2, 3}}, s.clock);
    s.missile_light_sources[descriptor].insert(id);
    s.missile_retire(descriptor);
    require(s.missile_roots.empty() && s.effect_lighting.lights.size() == 0,
            "Retirement left a detached tracked light");
    create(s);
    require(s.missile_roots.at(root).generation > b.generation, "Pooled address reused generation");
    s.missile_retire_root(root);
    require(s.missile_roots.empty(), "Root destruction retained projectile binding");
    create(s);
    s.frontend = true;
    s.missile_sync();
    require(s.missile_roots.empty(), "Frontend transition retained projectile binding");
    s.frontend = false;
    create(s);
    s.store(0x5f4c8c, 0x9100);
    s.missile_sync();
    require(s.missile_roots.empty(), "Mission context change retained projectile binding");
    s.store(0x5f4c8c, 0x9000);
    require(s.memory == original, "Production stage unexpectedly wrote guest memory");
    // A failed original factory and an unrelated weapon remain unbound.
    s.state.gpr.rcx.dword = definition;
    s.missile_create_body(&s.state, 0x585010, nullptr,
                          [](State *state, unsigned, void *) -> void * {
                              state->gpr.rax.dword = 0;
                              return nullptr;
                          });
    require(s.missile_roots.empty(), "Failed factory produced a visual binding");
    std::memcpy(s.memory.data() + name, "Laser", 6);
    s.state.gpr.rcx.dword = definition;
    s.missile_create_body(&s.state, 0x585010, nullptr,
                          [](State *state, unsigned, void *) -> void * {
                              state->gpr.rax.dword = descriptor;
                              return nullptr;
                          });
    require(s.missile_roots.empty(), "Non-missile projectile was admitted");
    bool propagated = false;
    try {
        s.missile_create_body(&s.state, 0x585010, nullptr, [](State *, unsigned, void *) -> void * {
            throw std::runtime_error("Original factory failure");
        });
    } catch (const std::runtime_error &e) {
        propagated = std::string(e.what()) == "Original factory failure";
    }
    require(propagated && s.missile_roots.empty(), "Original factory exception was swallowed");
}
void private_checks(const char *path) {
    std::ifstream file(path, std::ios::binary);
    require(bool(file), "Cannot open explicitly supplied private XYZ fixture");
    for (unsigned kind = 0; kind < 2; ++kind) {
        Stage s;
        setup(s);
        require(bool(file.read(reinterpret_cast<char *>(s.memory.data() + xyz), 108)),
                "Truncated private XYZ");
        create(s);
        const auto original = s.memory;
        check_scope_fp(s, node);
        s.missile_begin(node);
        require(s.missile_scope.node == node, "Pinned original missile mesh did not bind");
        const auto selected = s.missile_scope;
        require(selected.nozzle < 0 && selected.length > 1, "Wrong original local nozzle/length");
        s.missile_emit();
        require(s.host.devices[0].commands.size() == 1 && s.effect_lighting.lights.size() == 1,
                "Authenticated missile did not produce flame and attached light");
        auto uniform = s.effect_lighting.lights.uniform(s.clock, {0, 0, 0}, 64, 1);
        require(uniform.params[0] == 1, "Attached light missing from actual cache uniform");
        require(std::abs(uniform.lights[0].color[3] - 4.4f) < 1e-5f,
                "Missile thrust light must have twice its previous 2.2 intensity");
        require(std::abs(uniform.lights[0].start[0] - 110) < 1e-4f &&
                    std::abs(uniform.lights[0].start[1] - 220) < 1e-4f &&
                    std::abs(uniform.lights[0].start[2] -
                             (330 + selected.nozzle + selected.length * .15)) < 1e-4,
                "Light used stale simulation position instead of current body/camera transform");
        s.missile_emit();
        require(s.host.devices[0].commands.size() == 1,
                "Duplicate original matrix callback emitted twice");
        s.missile_end();
        ++s.host.frames;
        s.clock += .01;
        s.number(0xb000 + 3 * 4, 11);
        s.missile_begin(node);
        s.missile_emit();
        s.missile_end();
        uniform = s.effect_lighting.lights.uniform(s.clock, {0, 0, 0}, 64, 1);
        require(s.effect_lighting.lights.size() == 1 && uniform.params[0] == 1 &&
                    std::abs(uniform.lights[0].start[0] - 111) < 1e-4f,
                "Moving missile left a stationary light at its previous position");
        s.number(0xb000 + 3 * 4, 10);
        ++s.host.frames;
        s.role = WideZoom;
        s.missile_begin(node);
        s.missile_emit();
        require(s.host.devices[0].commands.size() == 3 && s.effect_lighting.lights.size() == 1,
                "Zoom pass duplicated tracked light identity");
        s.missile_end();
        s.preview = true;
        s.missile_begin(node);
        require(!s.missile_scope.node, "HUD schematic acquired missile exhaust");
        s.missile_end();
        s.preview = false;
        s.role = 2;
        s.missile_begin(node);
        require(!s.missile_scope.node, "Non-world preview acquired missile exhaust");
        s.missile_end();
        s.role = WideWorld;
        s.memory[xyz] ^= 1;
        s.missile_begin(node);
        require(!s.missile_scope.node, "Mutated original geometry signature admitted");
        s.missile_end();
        s.memory[xyz] ^= 1;
        require(s.memory == original, "Missile stage wrote original guest state");
        s.missile_retire(descriptor);
        require(s.effect_lighting.lights.size() == 0,
                "Private retirement retained frozen nozzle light");
    }
    require(file.peek() == std::char_traits<char>::eof(), "Trailing private XYZ bytes");
}
} // namespace
int main(int argc, char **argv) {
    try {
        public_checks();
        if (argc == 3 && std::string(argv[1]) == "--private-xyz")
            private_checks(argv[2]);
        else
            require(argc == 1, "Expected no arguments or --private-xyz <local binary>");
        std::cout << checks << " missile binding integration checks passed\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
