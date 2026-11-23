#pragma once
#include "additional_chassis.hpp"
#include "effect_lighting.hpp"
#include <map>
#include <set>
#include <string>

namespace mw34::headlights {
// Host presentation state. Original campaign save records are never extended.
struct Envelope {
    bool desired{};
    double current{};
    std::uint64_t tick{};
    void advance(double seconds, std::uint64_t next_tick, bool shutdown) {
        if (shutdown)
            desired = false;
        if (next_tick == tick)
            return;
        tick = next_tick;
        if (!std::isfinite(seconds) || seconds < 0)
            throw std::runtime_error("Headlights: invalid simulation delta");
        if (!seconds)
            return;
        const double target = desired ? 1 : 0;
        current = target + (current - target) * std::exp(-3.7446653419424887 * seconds);
        if (std::abs(current - target) <= .05 + 1e-12)
            current = target;
    }
};
struct Edge {
    bool armed{}, held{};
    bool sample(bool down, bool allowed) {
        if (!allowed) {
            armed = false;
            held = false;
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
struct Emitter {
    effects::Point position{}, direction{};
    bool valid{};
};
// What happened to a lamp whose mount failed mid-mission; the caller logs the first two.
enum class MountLoss { retired, went_dark, still_dark };
struct Owner {
    std::uint64_t generation{};
    unsigned root{}, chassis{};
    bool ready{};
    Envelope envelope;
    std::map<std::string, Emitter> emitters;
    std::set<std::string> retired_emitters;
    // Capture the authenticated mount ancestry while nodes are live. A parent
    // can be unlinked before its destruction callback, so walking it then is unsafe.
    std::map<std::string, std::vector<unsigned>> source_ancestry;
    // Lamps whose mount never resolved on the current model (a distance model can lack
    // it). They stay dark and are retried each refresh; the set makes "dark" and "back"
    // log once each instead of every tick.
    std::set<std::string> dark_mounts;
    void bind_root(unsigned next_root) {
        if (root == next_root)
            return;
        root = next_root;
        emitters.clear();
        source_ancestry.clear();
        // A root/LOD change is not a new actor lifetime: damaged mounts stay retired, and
        // dark mounts stay dark so a lamp missing from the far model logs only once.
    }
    bool retire_missing_mount(const std::string &id) {
        if (!source_ancestry.count(id))
            return false;
        retired_emitters.insert(id);
        emitters[id].valid = false;
        return true;
    }
    // A lamp that worked on this model loses its mount only to damage, so it is retired
    // for the mission. One that never resolved here waits for its mount to come back.
    MountLoss lose_mount(const std::string &id) {
        if (retire_missing_mount(id))
            return MountLoss::retired;
        emitters[id].valid = false;
        const bool first_dark_tick = dark_mounts.insert(id).second;
        return first_dark_tick ? MountLoss::went_dark : MountLoss::still_dark;
    }
    // True when the lamp was dark, so the caller logs that it came back.
    bool found_mount(const std::string &id) { return dark_mounts.erase(id) != 0; }
    bool retire_node(unsigned node, std::uint64_t expected_generation) {
        if (generation != expected_generation)
            return false;
        if (node == root) {
            bind_root(0);
            return true;
        }
        for (const auto &[id, ancestry] : source_ancestry)
            if (std::find(ancestry.begin(), ancestry.end(), node) != ancestry.end()) {
                retired_emitters.insert(id);
                emitters[id].valid = false;
            }
        return true;
    }
};
// Lamps that are off and fully faded emit nothing, so their mount search can wait until
// they are switched on again. That also covers shut-down and dead mechs once faded.
inline bool refresh_needed(const Owner &owner) {
    const bool lamps_lit_or_fading = owner.envelope.desired || owner.envelope.current > 0;
    return lamps_lit_or_fading;
}
inline std::set<std::string> emitter_ids(const chassis::Registration &record) {
    std::set<std::string> result;
    for (const auto &lamp : record.headlights)
        result.insert(lamp.id);
    return result;
}
inline unsigned retirement_mask(const Owner &owner, const chassis::Registration &record) {
    unsigned result = 0, bit = 0;
    for (const auto &id : emitter_ids(record)) {
        if (owner.retired_emitters.count(id))
            result |= 1U << bit;
        ++bit;
    }
    return result;
}
inline void restore_retirement(Owner &owner, const chassis::Registration &record, unsigned mask) {
    const auto ids = emitter_ids(record);
    if (mask >= (1U << ids.size()))
        throw std::runtime_error("Headlights: invalid replay retirement mask");
    owner.retired_emitters.clear();
    unsigned bit = 0;
    for (const auto &id : ids) {
        if (mask & (1U << bit))
            owner.retired_emitters.insert(id);
        ++bit;
    }
};
using Owners = std::map<unsigned, Owner>;
inline bool erase_generation(Owners &owners, unsigned actor, std::uint64_t generation) {
    const auto owner = owners.find(actor);
    if (owner == owners.end() || owner->second.generation != generation)
        return false;
    owners.erase(owner);
    return true;
}
using Matrix = std::array<double, 16>;
inline Emitter transform(const chassis::Headlight &lamp, const Matrix &world) {
    Emitter result;
    for (unsigned axis = 0; axis < 3; ++axis) {
        double p = world[axis * 4 + 3], d = 0;
        for (unsigned i = 0; i < 3; ++i) {
            p += world[axis * 4 + i] * lamp.position[i];
            d += world[axis * 4 + i] * lamp.direction[i];
        }
        if (!std::isfinite(p) || !std::isfinite(d) || std::abs(p) > 1e6)
            throw std::runtime_error("Headlights: invalid mount transform");
        result.position[axis] = float(p);
        result.direction[axis] = float(d);
    }
    const double length = std::hypot(double(result.direction[0]), double(result.direction[1]),
                                     double(result.direction[2]));
    if (!std::isfinite(length) || !(length > 1e-12))
        throw std::runtime_error("Headlights: singular mount direction");
    for (auto &value : result.direction)
        value = float(value / length);
    result.valid = true;
    return result;
}
} // namespace mw34::headlights
