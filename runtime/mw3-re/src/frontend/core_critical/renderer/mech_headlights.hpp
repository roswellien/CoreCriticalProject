#pragma once

#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <stdexcept>
#include <vector>

// WP05 unit1: MechWarrior 3 headlight presentation state only.
//
// These types carry owned scalar/integer state with no rendering hooks, no
// globals, no clocks, no RNG and no floating-point environment changes. Node
// identities are opaque uintptr_t values; ancestry lookups read the saved maps
// only, so retiring a node never dereferences a live node pointer. Lamp
// catalog and transform state are deliberately out of scope (next unit).
namespace mw34::headlights {

// Exponential fade constant for the presentation envelope.
inline constexpr double fade_rate = 3.7446653419424887;

// Distance to target at which the envelope snaps to target instead of tailing.
inline constexpr double snap_distance = 0.05;

struct Envelope {
    bool desired{};
    double current{};
    std::uint64_t tick{};

    // Validate seconds (finite, >= 0) and current (finite, within [0, 1])
    // BEFORE any mutation; throw std::runtime_error on invalid state.
    //
    // shutdown: desired becomes false, current becomes 0, tick becomes
    //   next_tick; this applies immediately even on a paused or repeated tick.
    // Otherwise a repeated tick (next_tick == tick) performs no advancement;
    // a changed tick stores tick. seconds == 0.0 freezes current. Any other
    // positive finite seconds fades current toward the target:
    //     current = target + (current - target) * exp(-fade_rate * seconds)
    // and snaps current to target when it lies within snap_distance.
    void advance(double seconds, std::uint64_t next_tick, bool shutdown) {
        const bool seconds_valid =
            std::isfinite(seconds) && seconds >= 0.0;
        const bool current_valid =
            std::isfinite(current) && current >= 0.0 && current <= 1.0;
        if (!seconds_valid || !current_valid) {
            throw std::runtime_error("headlights: Envelope::advance invalid input");
        }
        if (shutdown) {
            desired = false;
            current = 0.0;
            tick = next_tick;
            return;
        }
        if (next_tick == tick) {
            // Repeated tick: no advancement.
            return;
        }
        tick = next_tick;
        if (seconds == 0.0) {
            // Freeze current.
            return;
        }
        const double target = desired ? 1.0 : 0.0;
        double next =
            target + (current - target) * std::exp(-fade_rate * seconds);
        if (std::abs(next - target) <= snap_distance) {
            next = target;
        }
        current = next;
    }
};

struct Edge {
    bool armed{}, held{};
    bool sample(bool down, bool allowed) {
        if (!allowed) {
            armed = held = false;
            return false;
        }
        if (!down) {
            armed = true;
            held = false;
            return false;
        }
        if (!armed || held)
            return false;
        held = true;
        return true;
    }
};

struct Owner {
    std::uint64_t generation{};
    std::uintptr_t root{};
    Envelope envelope;
    std::map<std::string, bool> valid_emitters;
    std::set<std::string> retired_emitters;
    // Captured while nodes are live; retirement never walks detached pointers.
    std::map<std::string, std::vector<std::uintptr_t>> source_ancestry;

    void bind_root(std::uintptr_t node) {
        if (node == root)
            return;
        root = node;
        valid_emitters.clear();
        source_ancestry.clear();
        // Root/LOD changes do not start a new actor lifetime or repair damage.
    }

    bool retire_node(std::uintptr_t node, std::uint64_t expected) {
        if (expected != generation || node == 0)
            return false;
        if (node == root) {
            bind_root(0);
            return true;
        }
        for (const auto &entry : source_ancestry) {
            if (std::find(entry.second.begin(), entry.second.end(), node) != entry.second.end()) {
                retired_emitters.insert(entry.first);
                valid_emitters[entry.first] = false;
            }
        }
        return true;
    }
};

struct PlayerState {
    Owner owner;
    Edge edge;

    void update(std::uint64_t generation, std::uintptr_t root, std::uint64_t tick,
                double seconds, bool shutdown, bool down, bool input_allowed) {
        if (!std::isfinite(seconds) || seconds < 0)
            throw std::runtime_error("headlights: invalid player tick delta");
        if (!generation) {
            *this = {};
            return;
        }
        if (generation != owner.generation) {
            *this = {};
            owner.generation = generation;
        }
        owner.bind_root(root);
        if (shutdown || !root) {
            edge = {};
        } else if (tick != owner.envelope.tick && edge.sample(down, input_allowed)) {
            owner.envelope.desired = !owner.envelope.desired;
        }
        owner.envelope.advance(seconds, tick, shutdown);
    }
};

} // namespace mw34::headlights
