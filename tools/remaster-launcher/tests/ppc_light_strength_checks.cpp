#include "../../../runtime/graphics/effect_lighting.hpp"
#include <iostream>
#include <sstream>

namespace {
unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value)
        throw std::runtime_error("PPC light strength contract failed");
}
void near(float actual, float expected) {
    require(std::abs(actual - expected) <= 0.00001f * std::max(1.f, std::abs(expected)));
}
} // namespace

int main() {
    using namespace mw34::effects;
    struct Source {
        Emitter emitter;
        float expected_power;
    };
    const Point blue{.15f, .4f, 1.f}, green{.12f, 1.f, .2f}, orange{1.f, .42f, .08f};
    // Authored MWFX1 fixtures retain the installed catalog values. In particular,
    // laser beams/blue impacts must not inherit the PPC muzzle/trail adjustment.
    const std::array sources{
        Source{{1, 8.f, 2.f, .075f, blue}, 2.f},     Source{{2, 14.f, 2.8f, .09f, blue}, 3.5f},
        Source{{2, 14.f, 2.8f, .09f, green}, 2.8f},  Source{{2, 14.f, 2.8f, .09f, orange}, 2.8f},
        Source{{3, 9.f, 2.2f, .1f, blue}, 2.75f},    Source{{4, 6.f, 1.4f, .09f, green}, 1.4f},
        Source{{5, 18.f, 2.6f, .18f, blue}, 2.6f},   Source{{5, 18.f, .65f, .18f, blue}, .65f},
        Source{{5, 18.f, 2.6f, .18f, orange}, 2.6f}, Source{{6, 28.f, 2.5f, .18f, orange}, 2.5f},
    };
    std::ostringstream encoded(std::ios::binary);
    auto bytes = [&](const auto &value) {
        encoded.write(reinterpret_cast<const char *>(&value), sizeof(value));
    };
    encoded.write("MWFX1\0\0\0", 8);
    bytes(unsigned(sources.size()));
    for (unsigned i = 0; i < sources.size(); ++i) {
        bytes(8U);
        bytes(8U);
        bytes(3U);
        const auto &e = sources[i].emitter;
        bytes(e.kind);
        bytes(std::uint64_t(i + 1));
        bytes(e.radius);
        bytes(e.intensity);
        bytes(e.lifetime);
        for (float c : e.color)
            bytes(c);
    }
    std::istringstream input(encoded.str(), std::ios::binary);
    const auto catalog = read_catalog(input);
    require(catalog.size() == sources.size());
    const std::vector<Point> points{{2.f, 3.f, 4.f}};
    for (unsigned i = 0; i < sources.size(); ++i) {
        const auto &source = sources[i];
        const auto &emitter = catalog.at(mw34::materials::SurfaceKey{8, 8, 3, i + 1U});
        require(emitter.kind == source.emitter.kind && emitter.color == source.emitter.color);
        require(emitter.radius == source.emitter.radius &&
                emitter.intensity == source.emitter.intensity &&
                emitter.lifetime == source.emitter.lifetime);
        Cache cache;
        // Refreshing one live effect repeatedly must not multiply its stored power.
        for (unsigned refresh = 0; refresh < 8; ++refresh)
            cache.observe(emitter, points, 10.0);
        require(cache.size() == 1);
        for (float strength : {0.f, .5f, 1.f, 2.f}) {
            const auto light = cache.uniform(10.0, {}, 16, strength);
            require(light.params[0] == (strength == 0 ? 0.f : 1.f));
            if (strength == 0)
                continue;
            near(light.lights[0].color[3], source.expected_power * strength);
            require(light.lights[0].start == std::array<float, 4>{2.f, 3.f, 4.f, emitter.radius});
            require(light.lights[0].end ==
                    std::array<float, 4>{2.f, 3.f, 4.f, emitter.kind == 1 ? 1.f : 0.f});
            for (unsigned c = 0; c < 3; ++c)
                require(light.lights[0].color[c] == emitter.color[c]);
        }
        const auto faded = cache.uniform(10.0 + emitter.lifetime * .5, {}, 16, 1.f);
        require(faded.params[0] == 1.f);
        near(faded.lights[0].color[3], source.expected_power * .25f);
        require(cache.uniform(10.0 + emitter.lifetime * 1.01, {}, 16, 1.f).params[0] == 0.f);
        require(cache.size() == 0);
    }
    std::cout << checks << " PPC light strength checks passed\n";
}
