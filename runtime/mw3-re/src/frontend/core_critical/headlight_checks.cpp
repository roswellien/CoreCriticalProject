#include "renderer/mech_headlights.hpp"
#include <cstdio>
#include <limits>

namespace {
unsigned checks = 0;
void require(bool value, const char *message) {
    ++checks;
    if (!value)
        throw std::runtime_error(message);
}
using namespace mw34::headlights;
void check_envelope() {
    Envelope full{true, 0, 0}, split{true, 0, 0};
    full.advance(.1, 1, false);
    require(std::abs(full.current - (1 - std::exp(-3.7446653419424887 * .1))) < 1e-12,
            "fade differs from independent exponential");
    split.advance(.05, 1, false);
    split.advance(.05, 2, false);
    require(std::abs(full.current - split.current) < 1e-12, "fade depends on timestep splitting");
    const double prior = full.current;
    full.advance(0, 2, false);
    require(full.current == prior && full.tick == 2, "pause advanced fade");
    full.advance(.2, 2, false);
    require(full.current == prior, "repeated tick advanced fade");
    for (double seconds : {-1.0, std::numeric_limits<double>::quiet_NaN()}) {
        bool rejected = false;
        try { full.advance(seconds, 3, false); } catch (const std::runtime_error &) { rejected = true; }
        require(rejected && full.current == prior && full.tick == 2 && full.desired,
                "invalid delta mutated envelope or was accepted");
    }
    full.advance(0, 2, true);
    require(!full.desired && full.current == 0 && full.tick == 2, "paused shutdown did not retire immediately");
    Envelope invalid{true, 2, 7};
    bool rejected = false;
    try { invalid.advance(.1, 8, false); } catch (const std::runtime_error &) { rejected = true; }
    require(rejected && invalid.current == 2 && invalid.tick == 7, "invalid current was accepted or changed");
}
void check_edge() {
    Edge edge;
    require(!edge.sample(true, true), "initial held input triggered");
    require(!edge.sample(false, true), "release triggered");
    require(edge.sample(true, true), "released edge did not arm");
    require(!edge.sample(true, true), "held input repeated");
    require(!edge.sample(true, false), "disabled input triggered");
    require(!edge.sample(true, true), "reenabling held input triggered");
    require(!edge.sample(false, true) && edge.sample(true, true), "release did not rearm after disable");
}
void check_retirement() {
    Owner owner;
    owner.generation = 9;
    owner.bind_root(10);
    owner.valid_emitters = {{"left", true}, {"right", true}};
    owner.source_ancestry = {{"left", {10, 42, 43}}, {"right", {10, 42, 44}}};
    owner.bind_root(10);
    require(owner.valid_emitters.size() == 2 && owner.generation == 9, "same root changed lifetime");
    require(!owner.retire_node(42, 8) && owner.retired_emitters.empty() && owner.valid_emitters.at("left"),
            "stale generation retired a current lamp");
    require(!owner.retire_node(0, 9) && owner.retired_emitters.empty(), "zero node changed retirement");
    require(!owner.retire_node(999, 9) && owner.retired_emitters.empty(), "unrelated node reported retirement");
    require(owner.retire_node(42, 9), "current generation retirement rejected");
    require(!owner.valid_emitters.at("left") && !owner.valid_emitters.at("right") && owner.retired_emitters.size() == 2,
            "saved ancestor did not retire every mounted lamp");
    owner.bind_root(20);
    require(owner.root == 20 && owner.generation == 9 && owner.retired_emitters.size() == 2 &&
            owner.valid_emitters.empty() && owner.source_ancestry.empty(), "root change repaired damage or changed generation");
    owner.valid_emitters["new"] = true;
    owner.source_ancestry["new"] = {20, 50};
    require(owner.retire_node(20, 9) && owner.root == 0 && owner.source_ancestry.empty() &&
            owner.valid_emitters.empty() && owner.generation == 9, "root retirement kept node identities");
}
void check_player_state() {
    PlayerState player;
    player.update(1, 10, 1, 0, false, false, true);
    player.update(1, 10, 1, 0, false, true, true);
    require(!player.owner.envelope.desired, "duplicate tick accepted input");
    player.update(1, 10, 2, .1, false, true, true);
    require(player.owner.envelope.desired && player.owner.envelope.current > 0,
            "player edge did not start fade");
    player.owner.retired_emitters.insert("left");
    player.update(1, 0, 3, 0, false, true, true);
    player.update(1, 20, 4, 0, false, true, true);
    require(player.owner.envelope.desired && player.owner.retired_emitters.count("left") == 1,
            "temporary root loss reset actor state");
    player.update(1, 20, 4, 0, true, true, true);
    require(!player.owner.envelope.desired && player.owner.envelope.current == 0,
            "shutdown did not clear light on repeated tick");
    player.update(2, 20, 5, .1, false, true, true);
    require(player.owner.generation == 2 && player.owner.retired_emitters.empty() &&
                !player.owner.envelope.desired,
            "replacement actor inherited retired lamps or held input");
}
} // namespace
int main() {
    try {
        check_envelope(); check_edge(); check_retirement(); check_player_state();
        std::printf("Headlight state: %u checks passed\n", checks);
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "Headlight state: %s\n", error.what());
        return 1;
    }
}
