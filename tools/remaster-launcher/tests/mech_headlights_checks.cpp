// Authored timing/input/mount/budget fixture; no original data or guest code.
#include "fixture_lighting.hpp"
#include "mech_headlights.hpp"
#include <iostream>
#include <stdexcept>
void require(bool value, const char *message) {
    if (!value)
        throw std::runtime_error(message);
}
int main() {
    using namespace mw34::headlights;
    for (unsigned hz : {30U, 60U, 120U, 240U}) {
        Envelope fade;
        fade.desired = true;
        for (unsigned i = 1; i <= hz; ++i) {
            fade.advance(1.0 / hz, i, false);
            const double analytic = 1 - std::exp(-3.7446653419424887 * double(i) / hz);
            require(std::abs(fade.current - (analytic >= .95 - 1e-12 ? 1 : analytic)) < 1e-5,
                    "frame independent fade");
            const auto current = fade.current;
            fade.advance(1, i, false);
            require(fade.current == current, "duplicate simulation callback");
        }
        fade.desired = false;
        fade.advance(.125, hz + 1, false);
        const auto partial = fade.current;
        fade.desired = true;
        fade.advance(.01, hz + 2, false);
        require(fade.current > partial && fade.current < 1, "reverse fade immediately");
        const auto frozen = fade.current;
        fade.advance(0, hz + 3, false);
        require(fade.current == frozen, "paused fade");
        fade.advance(.1, hz + 4, true);
        require(!fade.desired && fade.current < frozen, "shutdown suppression");
    }
    Edge edge;
    require(!edge.sample(true, true), "initial held key requires neutral");
    require(!edge.sample(false, true) && edge.sample(true, true), "rising edge");
    require(!edge.sample(true, true), "held mixed inputs do not repeat");
    require(!edge.sample(false, false) && !edge.sample(true, true), "focus rearm");
    mw34::chassis::Headlight lamp;
    lamp.position = {2, 3, 4};
    lamp.direction = {0, 0, -1};
    Matrix world{0, 0, 1, 10, 0, 1, 0, 20, -1, 0, 0, 30, 0, 0, 0, 1};
    auto emitter = transform(lamp, world);
    require(emitter.position == mw34::effects::Point{14, 23, 28},
            "mount point includes translation");
    require(emitter.direction == mw34::effects::Point{-1, 0, 0},
            "mount direction excludes translation");
    bool invalid_transform = false;
    auto overflow_world = world;
    overflow_world[2] = 1e300;
    auto overflow_lamp = lamp;
    overflow_lamp.position = {};
    try {
        transform(overflow_lamp, overflow_world);
    } catch (const std::runtime_error &) {
        invalid_transform = true;
    }
    require(invalid_transform, "reject direction overflow before emitting NaNs");
    // The right mount is independent; destroying the left ancestor retires only
    // its descendants even when the raw node has already left the live tree.
    Owner owner;
    owner.generation = 1;
    owner.root = 100;
    owner.envelope = {true, 1, 7};
    owner.emitters["left"] = emitter;
    owner.emitters["right"] = emitter;
    owner.source_ancestry = {{"left", {103, 102, 100}}, {"right", {104, 100}}};
    owner.retire_node(102);
    require(!owner.emitters.at("left").valid && owner.emitters.at("right").valid,
            "ancestor retirement isolates lamps");
    owner.bind_root(200);
    require(owner.emitters.empty() && owner.source_ancestry.empty() && owner.envelope.desired &&
                owner.retired_emitters.count("left"),
            "model rebind preserves request and damage");
    mw34::chassis::Registration registration;
    registration.headlights = {{"right"}, {"left"}};
    require(retirement_mask(owner, registration) == 1, "snapshot uses full configured IDs");
    Owner restored;
    restore_retirement(restored, registration, retirement_mask(owner, registration));
    require(restored.retired_emitters == owner.retired_emitters,
            "sparse replay retirement survives");
    std::reverse(registration.headlights.begin(), registration.headlights.end());
    require(retirement_mask(restored, registration) == 1, "retirement ignores descriptor order");
    bool rejected = false;
    try {
        restore_retirement(restored, registration, 4);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected, "replay rejects unknown retirement bits");
    owner.source_ancestry = {{"right", {204, 200}}};
    owner.emitters["right"] = emitter;
    owner.retire_node(200);
    require(!owner.root && owner.emitters.empty() && !owner.retired_emitters.count("right"),
            "root teardown invalidates rather than damaging intact mounts");
    owner = {2};
    require(owner.retired_emitters.empty() && !owner.envelope.desired && !owner.root,
            "same-address reconstruction resets lifetime");
    auto &fixtures = mw34::fixtures::FixtureManager::instance();
    fixtures.clear();
    mw34::fixtures::MovingLight light{{{0, 0, 0, 50}, {0, 0, -1, 2}, {1, 1, 1, 2}},
                                      {.9f, .8f, 1, 0}};
    auto selected = fixtures.select_combined({}, 1, 1, 1, 160, 32, {light, light}, false);
    require(selected.size() == 1 && selected[0].cone == light.cone,
            "one slot per lamp with fixtures disabled");
    require(fixtures.select_combined({}, 0, 1, 1, 160, 32, {light}).empty(), "no nonweapon budget");
    require(fixtures.select_combined({}, 64).empty(), "moving lamps never retained as fixtures");
    std::cout << "Headlight timing, input, mount and shared budget passed\n";
}
