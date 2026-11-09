#ifdef _MSC_VER
#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS
#endif
#endif
#include "renderer/headlight_catalog.hpp"
#include "renderer/headlight_original_binding.hpp"
#include "renderer/headlight_spotlight.hpp"
#include "renderer/mech_headlights.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <sstream>

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
        try {
            full.advance(seconds, 3, false);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected && full.current == prior && full.tick == 2 && full.desired,
                "invalid delta mutated envelope or was accepted");
    }
    full.advance(0, 2, true);
    require(!full.desired && full.current == 0 && full.tick == 2,
            "paused shutdown did not retire immediately");
    Envelope invalid{true, 2, 7};
    bool rejected = false;
    try {
        invalid.advance(.1, 8, false);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected && invalid.current == 2 && invalid.tick == 7,
            "invalid current was accepted or changed");
}
void check_edge() {
    Edge edge;
    require(!edge.sample(true, true), "initial held input triggered");
    require(!edge.sample(false, true), "release triggered");
    require(edge.sample(true, true), "released edge did not arm");
    require(!edge.sample(true, true), "held input repeated");
    require(!edge.sample(true, false), "disabled input triggered");
    require(!edge.sample(true, true), "reenabling held input triggered");
    require(!edge.sample(false, true) && edge.sample(true, true),
            "release did not rearm after disable");
}
void check_retirement() {
    Owner owner;
    owner.generation = 9;
    owner.bind_root(10);
    owner.valid_emitters = {{"left", true}, {"right", true}};
    owner.source_ancestry = {{"left", {10, 42, 43}}, {"right", {10, 42, 44}}};
    owner.bind_root(10);
    require(owner.valid_emitters.size() == 2 && owner.generation == 9,
            "same root changed lifetime");
    require(!owner.retire_node(42, 8) && owner.retired_emitters.empty() &&
                owner.valid_emitters.at("left"),
            "stale generation retired a current lamp");
    require(!owner.retire_node(0, 9) && owner.retired_emitters.empty(),
            "zero node changed retirement");
    require(!owner.retire_node(999, 9) && owner.retired_emitters.empty(),
            "unrelated node reported retirement");
    require(owner.retire_node(42, 9), "current generation retirement rejected");
    require(!owner.valid_emitters.at("left") && !owner.valid_emitters.at("right") &&
                owner.retired_emitters.size() == 2,
            "saved ancestor did not retire every mounted lamp");
    owner.bind_root(20);
    require(owner.root == 20 && owner.generation == 9 && owner.retired_emitters.size() == 2 &&
                owner.valid_emitters.empty() && owner.source_ancestry.empty(),
            "root change repaired damage or changed generation");
    owner.valid_emitters["new"] = true;
    owner.source_ancestry["new"] = {20, 50};
    require(owner.retire_node(20, 9) && owner.root == 0 && owner.source_ancestry.empty() &&
                owner.valid_emitters.empty() && owner.generation == 9,
            "root retirement kept node identities");

    Owner limb_owner;
    limb_owner.generation = 1;
    limb_owner.bind_root(10);
    limb_owner.valid_emitters = {{"torso_lamp", true}, {"arm_lamp", true}};
    limb_owner.source_ancestry = {{"torso_lamp", {10, 100}}, {"arm_lamp", {10, 100, 200, 201}}};
    require(limb_owner.retire_node(200, 1), "retiring severed arm node should succeed");
    require(limb_owner.valid_emitters.at("torso_lamp"), "torso lamp should survive severed arm");
    require(!limb_owner.valid_emitters.at("arm_lamp"), "arm lamp should be marked invalid");
    require(limb_owner.retired_emitters.count("arm_lamp") == 1,
            "arm lamp should be in retired set");
    require(limb_owner.retired_emitters.count("torso_lamp") == 0,
            "torso lamp should not be retired");
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
void check_spotlight() {
    Lamp lamp;
    lamp.id = "test_lamp";
    lamp.space = "guest_node";
    lamp.attachment = "torso";
    lamp.position = {1.0f, 2.0f, 3.0f};
    lamp.direction = {0.0f, 0.0f, -1.0f};
    lamp.color = {1.0f, 0.9f, 0.8f};
    lamp.intensity = 4.0f;
    lamp.range = 100.0f;
    lamp.inner_angle = 10.0f;
    lamp.outer_angle = 30.0f;

    std::array<double, 16> identity_world{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    require(!spotlight(lamp, identity_world, 0.0, 1), "spotlight accepted zero envelope");
    require(!spotlight(lamp, identity_world, -0.5, 1), "spotlight accepted negative envelope");
    require(!spotlight(lamp, identity_world, 1.5, 1), "spotlight accepted >1 envelope");
    require(!spotlight(lamp, identity_world, 1.0, 0), "spotlight accepted zero source");

    Lamp donor_lamp = lamp;
    donor_lamp.space = "donor_bone";
    auto donor_cand = spotlight(donor_lamp, identity_world, 1.0, 1);
    require(donor_cand.has_value(), "valid donor_bone spotlight rejected");
    require(donor_cand->source == 1, "donor_bone spotlight source mismatch");

    Lamp invalid_space_lamp = lamp;
    invalid_space_lamp.space = "invalid_space";
    require(!spotlight(invalid_space_lamp, identity_world, 1.0, 1),
            "spotlight accepted invalid space");

    auto cand = spotlight(lamp, identity_world, 0.5, 42);
    require(cand.has_value(), "valid spotlight rejected");
    require(cand->source == 42, "spotlight source mismatch");
    require(cand->light.start[0] == 1.0f && cand->light.start[1] == 2.0f &&
                cand->light.start[2] == 3.0f,
            "spotlight position mismatch");
    require(cand->light.start[3] == 100.0f, "spotlight range mismatch");
    require(cand->light.end[0] == 0.0f && cand->light.end[1] == 0.0f && cand->light.end[2] == -1.0f,
            "spotlight direction mismatch");
    require(cand->light.end[3] == 2.0f, "spotlight type mismatch");
    require(cand->light.color[3] == 2.0f, "spotlight intensity not scaled by envelope");

    std::array<double, 16> rotated_world{0, 0, 1, 10, 0, 1, 0, 20, -1, 0, 0, 30, 0, 0, 0, 1};
    auto trans_cand = spotlight(lamp, rotated_world, 1.0, 1);
    require(trans_cand.has_value(), "transformed spotlight rejected");
    require(std::abs(trans_cand->light.start[0] - 13.0f) < 1e-4 &&
                std::abs(trans_cand->light.start[1] - 22.0f) < 1e-4 &&
                std::abs(trans_cand->light.start[2] - 29.0f) < 1e-4,
            "transformed position mismatch");
    require(std::abs(trans_cand->light.end[0] - (-1.0f)) < 1e-4 &&
                std::abs(trans_cand->light.end[1] - 0.0f) < 1e-4 &&
                std::abs(trans_cand->light.end[2] - 0.0f) < 1e-4,
            "transformed direction mismatch");
}

void check_catalog() {
    auto make_blob = [](uint32_t profiles, uint32_t start_id, uint32_t kind,
                        const std::string &hash, uint32_t lamps, float inner = 15.0f,
                        float outer = 25.0f, const char *magic_prefix = "MWHDLT1\0") {
        std::string s;
        s.append(magic_prefix, 8);
        auto put_u32 = [&](uint32_t v) { s.append(reinterpret_cast<const char *>(&v), 4); };
        put_u32(profiles);
        for (uint32_t p = 0; p < profiles; ++p) {
            put_u32(start_id + p);
            put_u32(kind);
            put_u32(static_cast<uint32_t>(hash.size()));
            s.append(hash);
            put_u32(0);
            put_u32(0);
            s.append(32, '\x01');
            put_u32(lamps);
            for (uint32_t l = 0; l < lamps; ++l) {
                std::string id = "l_" + std::to_string(l);
                put_u32(static_cast<uint32_t>(id.size()));
                s.append(id);
                std::string sp = "guest_node";
                put_u32(static_cast<uint32_t>(sp.size()));
                s.append(sp);
                std::string att = "hip";
                put_u32(static_cast<uint32_t>(att.size()));
                s.append(att);
                float pos[3] = {0, 0, 0};
                s.append(reinterpret_cast<const char *>(pos), 12);
                float dir[3] = {0, 0, -1.0f};
                s.append(reinterpret_cast<const char *>(dir), 12);
                float col[3] = {1, 1, 1};
                s.append(reinterpret_cast<const char *>(col), 12);
                float params[4] = {3.0f, 100.0f, inner, outer};
                s.append(reinterpret_cast<const char *>(params), 16);
            }
        }
        return s;
    };

    const std::string valid_hash(64, 'a');

    require(is_valid_stock_id(0), "stock_id 0 should be valid");
    require(is_valid_stock_id(18), "stock_id 18 should be valid");
    require(!is_valid_stock_id(7), "elemental stock_id 7 should be invalid");
    require(!is_valid_stock_id(19), "stock_id 19 should be invalid");

    {
        std::stringstream ss(make_blob(1, 0, 0, valid_hash, 1));
        auto profiles = read_stock_catalog(ss);
        require(profiles.size() == 1, "valid catalog single profile mismatch");
        require(profiles[0].stock_id == 0, "stock_id mismatch");
        require(profiles[0].lamps.size() == 1, "lamps count mismatch");
    }

    {
        std::stringstream ss(make_blob(1, 18, 0, valid_hash, 1));
        auto profiles = read_stock_catalog(ss);
        require(profiles.size() == 1 && profiles[0].stock_id == 18, "stock_id 18 catalog mismatch");
        require(match_original(profiles, "mech_vulture.flt", valid_hash) != nullptr,
                "match_original failed for stock_id 18 vulture");
    }

    {
        std::stringstream ss(make_blob(1, 19, 0, valid_hash, 1));
        bool rejected = false;
        try {
            read_stock_catalog(ss);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "catalog accepted stock_id 19");
    }

    {
        std::stringstream ss(make_blob(1, 0, 0, valid_hash, 1, 15, 25, "BADMAG1\0"));
        bool rejected = false;
        try {
            read_stock_catalog(ss);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "catalog accepted bad magic");
    }

    {
        std::stringstream ss(make_blob(19, 0, 0, valid_hash, 1));
        bool rejected = false;
        try {
            read_stock_catalog(ss);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "catalog accepted count > 18");
    }

    {
        std::stringstream ss(make_blob(1, 7, 0, valid_hash, 1));
        bool rejected = false;
        try {
            read_stock_catalog(ss);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "catalog accepted elemental stock_id 7");
    }

    {
        std::stringstream ss(make_blob(1, 0, 0, valid_hash, 9));
        bool rejected = false;
        try {
            read_stock_catalog(ss);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "catalog accepted lamps > 8");
    }

    {
        std::stringstream ss(make_blob(1, 0, 0, valid_hash, 1, 30.0f, 20.0f));
        bool rejected = false;
        try {
            read_stock_catalog(ss);
        } catch (const std::runtime_error &) {
            rejected = true;
        }
        require(rejected, "catalog accepted inner >= outer angle");
    }

    {
        std::stringstream ss(make_blob(1, 9, 0, valid_hash, 1));
        auto profiles = read_stock_catalog(ss);
        require(match_original(profiles, "mech_madcat.flt", valid_hash) != nullptr,
                "match_original failed");
        require(match_original(profiles, "mech_madcat.flt", std::string(64, 'b')) == nullptr,
                "match_original accepted wrong hash");
        require(match_original(profiles, "mech_bushwacker.flt", valid_hash) == nullptr,
                "match_original accepted wrong member");
    }

    const char *cat_path = std::getenv("MW34_STOCK_HEADLIGHTS");
    if (cat_path) {
        std::ifstream disk_file(cat_path, std::ios::binary);
        if (disk_file) {
            auto disk_profiles = read_stock_catalog(disk_file);
            require(disk_profiles.size() == 18, "real catalog should have 18 profiles");
            unsigned total = 0;
            for (const auto &p : disk_profiles)
                total += static_cast<unsigned>(p.lamps.size());
            require(total == 93, "real catalog should have exactly 93 lamps");
            require(match_original(
                        disk_profiles, "mech_madcat.flt",
                        "2a045eb890655ad5144a759e27a26880805d1d3ce96069613b688db5db6c3565") !=
                        nullptr,
                    "real madcat original match");
        }
    }
}
} // namespace
int main() {
    try {
        check_envelope();
        check_edge();
        check_retirement();
        check_player_state();
        check_spotlight();
        check_catalog();
        std::printf("Headlight state: %u checks passed\n", checks);
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "Headlight state: %s\n", error.what());
        return 1;
    }
}
