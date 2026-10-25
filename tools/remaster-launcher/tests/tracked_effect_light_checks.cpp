#include "../../../runtime/graphics/effect_lighting.hpp"
#include <iostream>

namespace {
unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value)
        throw std::runtime_error("Tracked effect light contract failed");
}
} // namespace

int main() {
    using namespace mw34::effects;
    const Emitter fire{6, 14.f, 2.f, .1f, {1.f, .4f, .08f}};
    Cache cache;
    for (unsigned frame = 0; frame < 40; ++frame) {
        const Point position{float(frame * 3), 2.f, 3.f};
        const double t = frame * .001;
        cache.observe_tracked(1, fire, {position}, t);
        require(cache.size() == 1);
        const auto uniform = cache.uniform(t, {}, 16, 1.f);
        require(uniform.params[0] == 1);
        require(uniform.lights[0].start ==
                std::array<float, 4>{position[0], position[1], position[2], fire.radius});
    }
    // Identical sources at one position cannot merge with another tracked ID,
    // or with a spatially coincident muzzle/impact/exhaust observation.
    const std::vector<Point> same{{117.f, 2.f, 3.f}};
    cache.observe_tracked(2, fire, same, .04);
    cache.observe(fire, same, .04);
    require(cache.size() == 3);
    for (unsigned repeat = 0; repeat < 10; ++repeat) {
        cache.observe_tracked(1, fire, same, .04);
        cache.observe_tracked(2, fire, same, .04);
        cache.observe(fire, same, .04);
        require(cache.size() == 3);
    }
    require(cache.uniform(.04, {}, 16, 1.f).params[0] == 3);
    cache.observe_tracked(1, fire, {{130.f, 2.f, 3.f}}, .05);
    require(cache.size() == 3);
    const auto moving = cache.uniform(.05, {}, 16, 1.f);
    unsigned moved{}, stayed{};
    for (unsigned i = 0; i < unsigned(moving.params[0]); ++i) {
        moved += moving.lights[i].start[0] == 130.f;
        stayed += moving.lights[i].start[0] == 117.f;
    }
    require(moved == 1 && stayed == 2);
    // Updating a tracked source replaces its parameters as well as its position.
    auto changed = fire;
    changed.color = {.1f, 1.f, .2f};
    changed.radius = 8.f;
    cache.observe_tracked(1, changed, {{140.f, 2.f, 3.f}}, .06);
    require(cache.size() == 3);
    const auto updated = cache.uniform(.06, {140.f, 2.f, 3.f}, 16, 1.f);
    require(updated.lights[0].start == std::array<float, 4>{140.f, 2.f, 3.f, 8.f});
    require(updated.lights[0].color == std::array<float, 4>{.1f, 1.f, .2f, 2.f});
    cache.expire(.17);
    require(cache.size() == 0);
    cache.observe_tracked(1, fire, same, .18);
    require(cache.size() == 1);
    cache.clear();
    require(cache.size() == 0);
    cache.observe_tracked(1, fire, {{5.f, 6.f, 7.f}}, .001);
    require(cache.size() == 1);
    require(cache.uniform(.001, {}, 16, 1.f).lights[0].start ==
            std::array<float, 4>{5.f, 6.f, 7.f, 14.f});
    // Backward presentation time also discards previous identities.
    cache.observe_tracked(2, fire, same, 0);
    require(cache.size() == 1);
    bool rejected{};
    try {
        cache.observe_tracked(0, fire, same, 0);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected && cache.size() == 1);
    // Tracked and untracked sources share the existing bounded cache.
    cache.clear();
    for (unsigned i = 0; i < 300; ++i) {
        if (i % 2)
            cache.observe_tracked(i, fire, {{float(i * 3), 0.f, 0.f}}, i * .00001);
        else
            cache.observe(fire, {{float(i * 3), 0.f, 0.f}}, i * .00001);
        require(cache.size() == std::min(i + 1, 256U));
    }
    cache.observe_tracked(299, fire, {{1000.f, 0.f, 0.f}}, .004);
    require(cache.size() == 256);
    cache.expire(.2);
    require(cache.size() == 0);
    // Retirement must remove a rocket even when photo mode freezes time.
    cache.observe_tracked(17, fire, same, 1);
    cache.observe_tracked(18, fire, same, 1);
    cache.observe(fire, same, 1);
    cache.erase_tracked(17);
    require(cache.size() == 2);
    require(cache.uniform(1, {}, 16, 1.f).params[0] == 2);
    cache.erase_tracked(0);
    cache.erase_tracked(999);
    require(cache.size() == 2);
    cache.erase_tracked(18);
    require(cache.size() == 1);
    // A 20-missile salvo cannot fill the complete weapon list. Its strongest
    // eight lights retain their order, leaving the laser and PPC selectable.
    cache.clear();
    const Emitter missile{7, 20.f, 4.f, .1f, {1.f, .2f, .01f}};
    const Emitter laser{1, 8.f, 2.f, .1f, {.12f, 1.f, .2f}};
    const Emitter ppc{3, 9.f, 2.2f, .1f, {.15f, .4f, 1.f}};
    for (unsigned i = 0; i < 20; ++i)
        cache.observe_tracked(i + 1, missile, {{float(i) * .1f, 0.f, 0.f}}, 2);
    cache.observe(laser, {{0.f, 0.f, 1.f}}, 2);
    cache.observe(ppc, {{0.f, 0.f, 2.f}}, 2);
    auto salvo = cache.uniform(2, {}, 16, 1.f);
    require(salvo.params[0] == 10);
    unsigned missiles{}, lasers{}, ppcs{};
    for (unsigned i = 0; i < unsigned(salvo.params[0]); ++i) {
        missiles += salvo.lights[i].color[0] == 1.f;
        lasers += salvo.lights[i].color[1] == 1.f;
        ppcs += salvo.lights[i].color[2] == 1.f;
        if (i < 8)
            require(salvo.lights[i].start[0] == float(i) * .1f);
    }
    require(missiles == 8 && lasers == 1 && ppcs == 1);
    require(fixture_slots(unsigned(salvo.params[0]), 64, 16) == 48);
    // Smaller weapon budgets still impose their original total limit.
    for (unsigned limit = 1; limit <= 16; ++limit) {
        salvo = cache.uniform(2, {}, limit, 1.f);
        require(salvo.params[0] == float(std::min(limit, 10U)));
        missiles = 0;
        for (unsigned i = 0; i < unsigned(salvo.params[0]); ++i)
            missiles += salvo.lights[i].color[0] == 1.f;
        require(missiles == std::min(8U, limit));
        require(fixture_slots(unsigned(salvo.params[0]), 64, 16) == 48);
    }
    // After skipping excess missiles, fill remaining slots from other ranked
    // candidates rather than truncating the list at the eighth missile.
    for (unsigned i = 0; i < 60; ++i)
        cache.observe_tracked(1000 + i, laser, {{30.f + float(i), 0.f, 0.f}}, 2);
    salvo = cache.uniform(2, {}, 64, 1.f);
    require(salvo.params[0] == 64);
    missiles = 0;
    for (unsigned i = 0; i < 64; ++i)
        missiles += salvo.lights[i].color[0] == 1.f;
    require(missiles == 8);
    // No missile observations: all 64 ordinary lights remain selectable in
    // their prior score order. No new sub-budget applies to other families.
    cache.clear();
    for (unsigned i = 0; i < 64; ++i)
        cache.observe_tracked(i + 1, laser, {{float(i * 3), 0.f, 0.f}}, 3);
    for (unsigned limit : {8U, 16U, 32U, 64U}) {
        const auto original = cache.uniform(3, {}, limit, 1.f);
        require(original.params[0] == float(limit));
        for (unsigned i = 0; i < limit; ++i)
            require(original.lights[i].start[0] == float(i * 3));
    }
    std::cout << checks << " tracked effect light checks passed\n";
}
