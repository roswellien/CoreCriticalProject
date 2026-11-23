#include "../tools/m4-crt-heap-carry/host/weapon_visuals.hpp"
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>

namespace {
void require(bool condition) {
    if (!condition)
        throw std::runtime_error("Weapon visual contract failed");
}
void near(mw34::donor::Vec actual, mw34::donor::Vec expected) {
    require(mw34::donor::length(mw34::donor::sub(actual, expected)) < 1e-9);
}
struct Snapshot;
struct Command {
    enum Kind { clear, Draw } kind{Draw};
    std::vector<unsigned char> vertices;
    std::shared_ptr<const Snapshot> weapon_visual;
    bool weapon_visual_seed{}, weapon_visual_end{};
    unsigned marker{};
    bool operator==(const Command &) const = default;
};
struct Snapshot {
    mw34::weapon_visuals::Identity identity;
    mw34::weapon_visuals::View view;
    bool external{true};
    std::vector<Command> replacement;
};
Command draw(float depth, unsigned marker) {
    mw34::weapon_visuals::TlVertex vertex{0, 0, depth, depth, 0xa2ffffff, 0xff000000, 0, 0};
    Command result;
    result.vertices.resize(32);
    std::memcpy(result.vertices.data(), &vertex, 32);
    result.marker = marker;
    return result;
}
std::shared_ptr<Snapshot> source(unsigned beam, float depth, unsigned marker) {
    auto result = std::make_shared<Snapshot>();
    result->identity = {beam, beam + 100, beam + 200, 99, beam + 300, beam + 400, 1};
    result->view = {
        10, 1, 0, mw34::donor::identity(), std::array<float, 6>{1, 100, -100, 320, 240, 1}, 1, 7};
    result->replacement.push_back(draw(depth, marker));
    return result;
}
Command boundary(std::shared_ptr<const Snapshot> source, bool end = false) {
    Command result;
    result.weapon_visual = std::move(source);
    result.weapon_visual_seed = true;
    result.weapon_visual_end = end;
    return result;
}
void composition_checks() {
    using namespace mw34::weapon_visuals;
    const auto a = source(1, .4f, 21), b = source(2, .6f, 22);
    auto old_a = draw(.2f, 12), old_b = draw(.3f, 13);
    old_a.weapon_visual = a;
    old_b.weapon_visual = b;
    Command before;
    before.kind = Command::clear;
    before.marker = 99;
    const std::vector<Command> input{before, boundary(a),   boundary(b),       draw(.1f, 11), old_a,
                                     old_b,  draw(.8f, 14), boundary(a, true), before};
    const auto current = [](const Identity &) { return Status::current; };
    const auto result = compose_deferred(input, current);
    require(result.commands.size() == 6 && result.observations.size() == 2);
    require(result.commands[0] == before && result.commands[5] == before);
    for (unsigned i = 0; i < 4; ++i)
        require(result.commands[i + 1].marker == std::array<unsigned, 4>{11, 21, 22, 14}[i]);
    require(result.commands[1] == input[3] && result.commands[4] == input[6]);
    // Identical weapons and even equal local generations on two actors must
    // remain separate sources. Retirement cannot delete the other actor.
    const auto retired = compose_deferred(input, [](const Identity &identity) {
        return identity.actor == 101 ? Status::retired : Status::current;
    });
    require(retired.observations.size() == 1 && retired.observations[0] == b);
    require(std::none_of(retired.commands.begin(), retired.commands.end(), [](const auto &command) {
        return command.marker == 12 || command.marker == 21;
    }));
    require(!retired.retired.empty() && retired.retired[0].actor == 101);
    // A retired descriptor arriving after its stop needs no live seed or draw.
    require(compose_deferred(std::vector<Command>{before, old_a, before}, [](const Identity &) {
                return Status::retired;
            }).commands == std::vector<Command>({before, before}));
    auto original_view = source(3, .7f, 23);
    original_view->external = false;
    auto unchanged = draw(.5f, 15);
    unchanged.weapon_visual = original_view;
    const auto pass = compose_deferred(
        std::vector<Command>{boundary(original_view), unchanged, boundary(original_view, true)},
        current);
    require(pass.commands == std::vector<Command>{unchanged} && pass.observations.size() == 1);
    // A second actual view in the same scene is distinct, but an identical
    // repeat of that view must not duplicate the beam or its tracked lights.
    auto zoom = std::make_shared<Snapshot>(*a);
    std::get<4>(zoom->view)[1] = 200;
    auto target = std::make_shared<Snapshot>(*a);
    std::get<0>(target->view) = 11;
    auto camera = std::make_shared<Snapshot>(*a);
    std::get<3>(camera->view)[3] = 1;
    std::vector<Command> views;
    auto policy = std::make_shared<Snapshot>(*a);
    std::get<5>(policy->view) = 2;
    auto producer = std::make_shared<Snapshot>(*a);
    std::get<6>(producer->view) = 8;
    for (auto view : {a, a, zoom, target, camera, policy, producer}) {
        views.push_back(boundary(view));
        views.push_back(boundary(view, true));
    }
    const auto multiple = compose_deferred(views, current);
    require(multiple.commands.size() == 6 && multiple.observations.size() == 6);
    // Old geometry can be entirely culled: only a fresh immutable source seed
    // is needed to admit its corrected geometry, never a prior-frame draw.
    require(
        compose_deferred(std::vector<Command>{boundary(a), boundary(a, true)}, current).commands ==
        a->replacement);
    // Replacement failure is atomic: no original command storage is changed.
    const auto saved = input;
    bool rejected = false;
    try {
        (void)compose_deferred(input, [](const Identity &) { return Status::invalid; });
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected && input == saved);
    for (auto malformed :
         {std::vector<Command>{boundary(a)}, std::vector<Command>{boundary(a, true)},
          std::vector<Command>{boundary(a), boundary(zoom, true)}}) {
        rejected = false;
        try {
            (void)compose_deferred(malformed, current);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected);
    }
}
} // namespace

int main() {
    using mw34::weapon_visuals::arm_retired;
    require(!arm_retired("rhand", 0, true, false, true)); // Cockpit hides the whole body.
    require(arm_retired("rhand", 1, true, false, true));
    require(!arm_retired("lhand", 1, true, false, true));
    require(arm_retired("lhand", 2, true, false, true));
    require(arm_retired("rhand", 0, false, false, true));
    require(arm_retired("rhand", 0, true, false, false));
    require(!arm_retired("rhand", 0, false, {}, true)); // Meshless source controls are valid.
    composition_checks();
    using namespace mw34;
    using namespace weapon_visuals;
    Identity live{1, 2, 3, 4, 5, 6, 7};
    require(current(live, live));
    auto stale = live;
    ++stale.generation;
    require(!current(stale, live));
    for (unsigned field = 0; field < 6; ++field) {
        auto changed = live;
        unsigned *values[] = {&changed.beam,       &changed.actor,    &changed.weapon,
                              &changed.definition, &changed.position, &changed.direction};
        ++*values[field];
        require(!current(changed, live));
    }
    require(!current({}, {}));
    const donor::Vec source{12, 7, 19}, end{-81, 23, 172}, muzzle{14, 5, 20};
    const auto transform = attachment_transform(source, end, muzzle);
    near(donor::point(transform, source), muzzle);
    near(donor::point(transform, end), end);
    const auto side = donor::unit(donor::cross(donor::sub(end, source), {0, 1, 0}));
    near(donor::sub(donor::point(transform, donor::add(source, side)), muzzle), side);
    const auto middle = donor::scale(donor::add(source, end), .5);
    near(donor::point(transform, middle), donor::scale(donor::add(muzzle, end), .5));
    near(donor::point(attachment_transform(source, end, source), middle), middle);
    for (const auto &points : {std::array<donor::Vec, 3>{source, source, muzzle},
                               std::array<donor::Vec, 3>{
                                   {{std::numeric_limits<double>::quiet_NaN(), 0, 0}, end, muzzle}},
                               std::array<donor::Vec, 3>{source, end, {1000001, 0, 0}}}) {
        bool rejected = false;
        try {
            (void)attachment_transform(points[0], points[1], points[2]);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected);
    }
    std::vector<Vertex> gpu_vertices{{-1, 0, 2, 0, 0, channels(0xa2ffffff), channels(0xff000000)},
                                     {1, 0, 2, 1, 0, channels(0xa2ffffff), channels(0xff000000)},
                                     {0, 1, 2, .5, 1, channels(0xa2ffffff), channels(0xff000000)}};
    require(gpu_colour(gpu_vertices, 1, false) == 0xa2ffffffU);
    require(!gpu_colour(gpu_vertices, 1, true));
    gpu_vertices[0].fog = channels(0xfe000000);
    require(!gpu_colour(gpu_vertices, 1, false));
    gpu_vertices[0].fog = channels(0xff000000);
    gpu_vertices[0].color = channels(0xa2fffffe);
    require(!gpu_colour(gpu_vertices, 1, false));
    gpu_vertices[0].color = channels(0xa2ffffff);
    gpu_vertices[0].z = 1.00001;
    require(!gpu_colour(gpu_vertices, 1, false));
    // A near-plane crossing must retain independent opacity, RGB and fog.
    const Vertex a{-1, 0, .5, 0, 0, channels(0x20406080), channels(0x10010203)};
    const Vertex b{1, 0, 1.5, 1, 0, channels(0xe0c0a080), channels(0xf0090807)};
    const Vertex c{0, 1, 1.5, .5, 1, channels(0x80604020), channels(0xa0010203)};
    const std::array<float, 6> projection{1, 100, -100, 320, 240, 1};
    const auto clipped = project({a, b, c}, projection);
    require(clipped.size() == 6);
    bool crossing = false;
    for (const auto &vertex : clipped) {
        require(vertex.z > 0 && vertex.z <= 1);
        if (vertex.u == .5f && vertex.v == 0) {
            require(vertex.color == 0x80808080 && vertex.specular == 0x80050505);
            crossing = true;
        }
    }
    require(crossing);
    auto hidden = std::vector<Vertex>{a, a, a};
    require(project(hidden, projection).empty());
    // Rebuilding before clipping admits a moved source even if the old polygon
    // supplied no TL draw. No previous frame's command is needed.
    for (auto &vertex : hidden)
        vertex.z += 1;
    require(!project(hidden, projection).empty());
    for (unsigned field = 0; field < 6; ++field) {
        auto invalid = live;
        unsigned *values[] = {&invalid.beam,       &invalid.actor,    &invalid.weapon,
                              &invalid.definition, &invalid.position, &invalid.direction};
        *values[field] = 0;
        require(!current(invalid, invalid));
    }
    std::cout << "Weapon visual identity and endpoint preservation checks passed\n";
}
