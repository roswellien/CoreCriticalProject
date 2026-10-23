// The driver extracts the actual setter branches and renamed snapshot methods
// from the reviewed host into the .inc files below. No setter logic is
// duplicated here; off/on calls run those source branches directly.
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <d3d.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void require(bool value, const char* message) {
    if (!value)
        throw std::runtime_error(message);
}
struct Fault : std::runtime_error {
    unsigned address;
    Fault(const std::string& message, unsigned value) : std::runtime_error(message), address(value) {}
};
struct D3DDev {
    std::array<unsigned, 256> rs{};
    std::array<std::array<unsigned, 32>, 8> tss{};
    std::uint64_t epoch{1}, snap_epoch{};
    unsigned current{1};
    std::vector<unsigned> viewports{1, 2};
    std::shared_ptr<const std::vector<unsigned>> snap;
};
struct D3DViewport {
    unsigned guest{1};
    std::array<unsigned char, 44> vp{};
};
struct MockRenderer {
    D3DDev device;
    D3DViewport view;
    bool reuse{};
    unsigned result{}, arguments{}, completions{}, snapshot_builds{};

    bool render_reuse_enabled() const { return reuse; }
    unsigned vsurf_root(unsigned guest) const { return guest; }
    D3DViewport* viewport(unsigned guest) { return guest == view.guest ? &view : nullptr; }
    [[noreturn]] void deny(const std::string& message, unsigned address = 0) {
        throw Fault(message, address);
    }
    void* rs_off(unsigned state, unsigned value) {
        auto* dev = &device;
        const std::string n = "SetRenderState";
        const std::array<unsigned, 3> args{0, state, value};
        auto arg = [&](unsigned index) { return args.at(index); };
        auto done = [&](unsigned r, unsigned count) -> void* {
            result = r; arguments = count; ++completions; return nullptr;
        };
#include "set_rs_off.inc"
        throw std::runtime_error("Extracted render-state branch did not run");
    }
    void* rs_on(unsigned state, unsigned value) {
        auto* dev = &device;
        const std::string n = "SetRenderState";
        const std::array<unsigned, 3> args{0, state, value};
        auto arg = [&](unsigned index) { return args.at(index); };
        auto done = [&](unsigned r, unsigned count) -> void* {
            result = r; arguments = count; ++completions; return nullptr;
        };
#include "set_rs_on.inc"
        throw std::runtime_error("Extracted render-state branch did not run");
    }
    void* tss_off(unsigned stage, unsigned state, unsigned value) {
        auto* dev = &device;
        const std::string n = "SetTextureStageState";
        const std::array<unsigned, 4> args{0, stage, state, value};
        auto arg = [&](unsigned index) { return args.at(index); };
        auto done = [&](unsigned r, unsigned count) -> void* {
            result = r; arguments = count; ++completions; return nullptr;
        };
#include "set_tss_off.inc"
        throw std::runtime_error("Extracted texture-state branch did not run");
    }
    void* tss_on(unsigned stage, unsigned state, unsigned value) {
        auto* dev = &device;
        const std::string n = "SetTextureStageState";
        const std::array<unsigned, 4> args{0, stage, state, value};
        auto arg = [&](unsigned index) { return args.at(index); };
        auto done = [&](unsigned r, unsigned count) -> void* {
            result = r; arguments = count; ++completions; return nullptr;
        };
#include "set_tss_on.inc"
        throw std::runtime_error("Extracted texture-state branch did not run");
    }
    void* delete_off(unsigned guest) {
        auto* dev = &device;
        const std::string n = "DeleteViewport";
        const std::array<unsigned, 2> args{0, guest};
        auto arg = [&](unsigned index) { return args.at(index); };
        auto done = [&](unsigned r, unsigned count) -> void* {
            result = r; arguments = count; ++completions; return nullptr;
        };
#include "delete_off.inc"
        throw std::runtime_error("Extracted viewport deletion branch did not run");
    }
    void* delete_on(unsigned guest) {
        auto* dev = &device;
        const std::string n = "DeleteViewport";
        const std::array<unsigned, 2> args{0, guest};
        auto arg = [&](unsigned index) { return args.at(index); };
        auto done = [&](unsigned r, unsigned count) -> void* {
            result = r; arguments = count; ++completions; return nullptr;
        };
#include "delete_on.inc"
        throw std::runtime_error("Extracted viewport deletion branch did not run");
    }
#include "snapshot_off.inc"
#include "snapshot_on.inc"

    // This is the existing draw-time cache condition, not the optimized setter.
    std::shared_ptr<const std::vector<unsigned>> capture(bool optimized) {
        if (!device.snap || device.snap_epoch != device.epoch) {
            auto words = optimized ? snapshot_on(device) : snapshot_off(device);
            device.snap = std::make_shared<const std::vector<unsigned>>(std::move(words));
            device.snap_epoch = device.epoch;
            ++snapshot_builds;
        }
        return device.snap;
    }
};

struct Outcome {
    bool failed{};
    std::string message;
    unsigned address{}, result{}, arguments{};
    bool operator==(const Outcome&) const = default;
};
} // namespace

int main() {
    try {
        MockRenderer off, on;
        on.reuse = true;
        for (unsigned i = 0; i < 11; ++i) {
            // Preserve raw word patterns, including negative zero and NaN bits.
            const unsigned word = i == 0 ? 44 : i == 1 ? 0x80000000U : 0x7fc00000U + i;
            std::memcpy(off.view.vp.data() + 4 * i, &word, 4);
        }
        on.view = off.view;
        unsigned calls = 0, failures = 0, retained_checks = 0, noops_reused = 0;
        auto run = [&](bool texture, unsigned a, unsigned b, unsigned c = 0) {
            const auto old_off = off.capture(false), old_on = on.capture(true);
            const auto old_off_words = *old_off, old_on_words = *old_on;
            const auto prior_rs = on.device.rs;
            const auto prior_tss = on.device.tss;
            const auto prior_epoch = on.device.epoch;
            auto invoke = [&](MockRenderer& renderer, bool optimized) {
                Outcome out;
                const unsigned completed_before = renderer.completions;
                try {
                    if (texture) {
                        if (optimized) renderer.tss_on(a, b, c);
                        else renderer.tss_off(a, b, c);
                    } else {
                        if (optimized) renderer.rs_on(a, b);
                        else renderer.rs_off(a, b);
                    }
                    out.result = renderer.result;
                    out.arguments = renderer.arguments;
                    require(renderer.completions == completed_before + 1, "Missing setter completion");
                    require(out.result == DD_OK && out.arguments == (texture ? 4U : 3U),
                            "Setter completion contract changed");
                } catch (const Fault& fault) {
                    out.failed = true;
                    out.message = fault.what();
                    out.address = fault.address;
                    require(renderer.completions == completed_before, "Failed setter returned success");
                }
                return out;
            };
            const auto before = invoke(off, false), after = invoke(on, true);
            require(before == after, "Setter result/error differs");
            require(off.device.rs == on.device.rs && off.device.tss == on.device.tss,
                    "Stored state or getter-visible alias words differ");
            require(off.snapshot_off(off.device) == on.snapshot_on(on.device),
                    "Snapshot word construction differs");
            const auto next_off = off.capture(false), next_on = on.capture(true);
            require(*next_off == *next_on, "Draw-time cached snapshot is stale");
            require(*old_off == old_off_words && *old_on == old_on_words,
                    "Earlier draw snapshot was mutated by a setter");
            ++retained_checks;
            const bool effective_noop = prior_rs == on.device.rs && prior_tss == on.device.tss;
            if (effective_noop) {
                require(on.device.epoch == prior_epoch && next_on.get() == old_on.get(),
                        "Effective no-op rebuilt its immutable snapshot");
                ++noops_reused;
            } else {
                require(on.device.epoch == prior_epoch + 1 && next_on.get() != old_on.get(),
                        "Effective change must invalidate exactly once");
            }
            ++calls;
            if (before.failed) ++failures;
        };

        // Ordinary states, including repeated bit patterns and every valid index.
        for (unsigned state = 0; state < 256; ++state) {
            // Aliases with value validation are exercised separately below.
            if (state == D3DRENDERSTATE_TEXTUREMAG || state == D3DRENDERSTATE_TEXTUREMIN ||
                state == D3DRENDERSTATE_TEXTUREMAPBLEND) continue;
            run(false, state, 0x80000000U | state);
            run(false, state, 0x80000000U | state);
        }
        run(false, D3DRENDERSTATE_TEXTUREMAG, D3DFILTER_LINEAR);
        run(true, 0, D3DTSS_MAGFILTER, D3DTFG_POINT);
        run(false, D3DRENDERSTATE_TEXTUREMAG, D3DFILTER_LINEAR);
        require(on.device.tss[0][D3DTSS_MAGFILTER] == D3DTFG_LINEAR,
                "Repeated legacy MAG did not restore its stage alias");
        for (unsigned value = 1; value <= 6; ++value) {
            run(false, D3DRENDERSTATE_TEXTUREMIN, value);
            run(true, 0, D3DTSS_MINFILTER, 0x123);
            run(true, 0, D3DTSS_MIPFILTER, 0x456);
            run(false, D3DRENDERSTATE_TEXTUREMIN, value);
            run(false, D3DRENDERSTATE_TEXTUREMIN, value);
        }
        for (unsigned legacy : {unsigned(D3DRENDERSTATE_TEXTUREADDRESS),
                                unsigned(D3DRENDERSTATE_TEXTUREADDRESSU),
                                unsigned(D3DRENDERSTATE_TEXTUREADDRESSV)}) {
            run(false, legacy, D3DTADDRESS_WRAP);
            run(true, 0, D3DTSS_ADDRESSU, D3DTADDRESS_CLAMP);
            run(true, 0, D3DTSS_ADDRESSV, D3DTADDRESS_CLAMP);
            run(false, legacy, D3DTADDRESS_WRAP);
            run(false, legacy, D3DTADDRESS_WRAP);
        }
        // ADDRESS itself can be unchanged while its U/V aliases have drifted.
        for (unsigned stage = 0; stage < 8; ++stage) {
            run(true, stage, D3DTSS_ADDRESS, D3DTADDRESS_WRAP);
            run(true, stage, D3DTSS_ADDRESSU, D3DTADDRESS_CLAMP);
            run(true, stage, D3DTSS_ADDRESSV, D3DTADDRESS_CLAMP);
            run(true, stage, D3DTSS_ADDRESS, D3DTADDRESS_WRAP);
            run(true, stage, D3DTSS_ADDRESS, D3DTADDRESS_WRAP);
            for (unsigned state = 0; state < 32; ++state) {
                run(true, stage, state, state + stage * 100);
                run(true, stage, state, state + stage * 100);
            }
        }
        // A repeated invalid value must still fail even though the old branch
        // stored it before reporting the error. Partial state must also match.
        for (unsigned value : {0U, 7U, 0xffffffffU}) {
            run(false, D3DRENDERSTATE_TEXTUREMIN, value);
            run(false, D3DRENDERSTATE_TEXTUREMIN, value);
            run(false, D3DRENDERSTATE_TEXTUREMAG, value);
            run(false, D3DRENDERSTATE_TEXTUREMAG, value);
        }
        run(false, D3DRENDERSTATE_TEXTUREMAPBLEND, D3DTBLEND_MODULATE);
        run(false, D3DRENDERSTATE_TEXTUREMAPBLEND, D3DTBLEND_DECAL);
        run(false, D3DRENDERSTATE_TEXTUREMAPBLEND, D3DTBLEND_DECAL);
        for (unsigned invalid : {256U, 0xffffffffU}) run(false, invalid, 0);
        run(true, 8, 0, 0);
        run(true, 0xffffffffU, 0, 0);
        run(true, 0, 32, 0);
        run(true, 0, 0xffffffffU, 0);

        // Snapshot construction has the same bytes and length with no viewport,
        // an unknown viewport, and a valid viewport; replay still forces rebuild.
        for (unsigned current : {0U, 999U, 1U}) {
            off.device.current = on.device.current = current;
            ++off.device.epoch;
            ++on.device.epoch;
            const auto a = off.capture(false), b = on.capture(true);
            require(*a == *b && a->size() == (current == 1 ? 531U : 520U),
                    "Viewport snapshot layout changed");
            const auto retained = b;
            on.device.snap.reset();
            on.device.snap_epoch = 0;
            ++on.device.epoch;
            require(on.capture(true).get() != retained.get() && *on.device.snap == *retained,
                    "Forced replay-style reset did not rebuild identical state");
        }

        // Both extracted deletion branches include the correctness repair. An
        // inactive deletion must leave a cached current viewport valid; removing
        // the current viewport must invalidate even if subsequent setters are
        // effective no-ops in the optimized path.
        auto delete_pair = [&](unsigned guest) {
            const auto current = on.device.current;
            const auto before_off_epoch = off.device.epoch;
            const auto before_on_epoch = on.device.epoch;
            const unsigned before_off_done = off.completions, before_on_done = on.completions;
            off.delete_off(guest);
            on.delete_on(guest);
            require(off.result == DD_OK && on.result == DD_OK && off.arguments == 2 && on.arguments == 2 &&
                        off.completions == before_off_done + 1 && on.completions == before_on_done + 1,
                    "Viewport deletion completion differs");
            require(off.device.viewports == on.device.viewports && off.device.current == on.device.current &&
                        std::find(on.device.viewports.begin(), on.device.viewports.end(), guest) ==
                            on.device.viewports.end(), "Viewport membership differs after deletion");
            const unsigned invalidations = current == guest ? 1 : 0;
            require(off.device.epoch == before_off_epoch + invalidations &&
                        on.device.epoch == before_on_epoch + invalidations,
                    "Viewport deletion invalidated the wrong snapshot");
            require(on.device.current == (current == guest ? 0U : current),
                    "Inactive deletion cleared the current viewport");
        };
        const auto with_viewport_off = off.capture(false), with_viewport_on = on.capture(true);
        const auto retained_viewport_words = *with_viewport_on;
        require(with_viewport_off->size() == 531 && with_viewport_on->size() == 531,
                "Viewport deletion regression requires a populated cached viewport");
        delete_pair(2);
        require(off.capture(false).get() == with_viewport_off.get() &&
                    on.capture(true).get() == with_viewport_on.get(),
                "Inactive viewport deletion rebuilt the current snapshot");
        delete_pair(1);
        const unsigned perspective = on.device.rs[D3DRENDERSTATE_TEXTUREPERSPECTIVE];
        const unsigned colorop = on.device.tss[0][D3DTSS_COLOROP];
        off.rs_off(D3DRENDERSTATE_TEXTUREPERSPECTIVE, perspective);
        on.rs_on(D3DRENDERSTATE_TEXTUREPERSPECTIVE, perspective);
        off.tss_off(0, D3DTSS_COLOROP, colorop);
        on.tss_on(0, D3DTSS_COLOROP, colorop);
        const auto without_viewport_off = off.capture(false), without_viewport_on = on.capture(true);
        require(without_viewport_off->size() == 520 && without_viewport_on->size() == 520 &&
                    *without_viewport_off == *without_viewport_on,
                "Deleted current viewport survived identical RS/TSS setters in the draw cache");
        require(without_viewport_on.get() != with_viewport_on.get() &&
                    *with_viewport_on == retained_viewport_words &&
                    *with_viewport_off == retained_viewport_words,
                "Viewport deletion changed an earlier immutable draw snapshot");
        require(calls && failures && noops_reused && on.snapshot_builds < off.snapshot_builds,
                "Fixture did not cover failures and snapshot reuse");
        std::cout << "render state reuse calls=" << calls << " matched_failures=" << failures
                  << " retained_snapshots=" << retained_checks << " noops_reused=" << noops_reused
                  << " snapshot_builds=" << off.snapshot_builds << "->" << on.snapshot_builds
                  << " viewport_deletions=2 failures=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
