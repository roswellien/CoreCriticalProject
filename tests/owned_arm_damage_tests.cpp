// Authored hierarchy and stump fixture for the production damage matcher.
// Catalog decoding is covered separately by additional_chassis_checks.cpp.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

struct OverrideSourceMesh {
    const char *name;
    unsigned vertices;
    const char *owner;
};
struct OverrideModel {
    const char *id;
    const OverrideSourceMesh *roster;
    size_t count;
    unsigned lod;
    const char *resource;
    const char *source_chassis;
};
struct OverrideArmDamagePlan {
    const char *model;
    unsigned lod;
    const char *stub;
    unsigned vertices;
    std::uint64_t vertex_hash;
    const char *parent;
    std::array<const char *, 8> removed;
    unsigned count;
};
constexpr std::uint64_t authored_stump_hash() {
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    for (unsigned i = 0; i < 36; ++i)
        hash *= 0x100000001b3ULL;
    return hash;
}
const std::array<OverrideArmDamagePlan, 2> override_arm_damage_plans{{
    {"stock", 0, "larm_stub01", 3, authored_stump_hash(), "torso", {}, 0},
    {"stock", 0, "rarm_stub01", 3, authored_stump_hash(), "torso", {}, 0},
}};
namespace mw34::chassis {
struct ArmDamage {
    std::string arm, parent;
    std::vector<std::string> removed;
};
struct Registration {
    std::string resource;
    bool owned_visuals;
    std::array<std::vector<ArmDamage>, 2> arm_damage;
};
std::vector<Registration> records;
const auto &configured_catalog() { return records; }
} // namespace mw34::chassis

struct Fixture {
    std::map<unsigned, unsigned> words, parents;
    std::map<unsigned, std::string> names;
    bool readable(unsigned address, unsigned size) {
        return address >= 0x1000 && address + size < 0xa000;
    }
    unsigned load(unsigned address) { return words[address]; }
    unsigned override_parent(unsigned node) { return parents[node]; }
    std::string pose_name(unsigned node, unsigned) { return names[node]; }
    void stump(unsigned base, const char *arm, const char *stub) {
        names[base] = stub;
        names[base + 0x100] = arm;
        names[0x9000] = "torso";
        parents[base] = base + 0x100;
        parents[base + 0x100] = 0x9000;
        words[base + 0x100 + 0x5c] = 1;
        words[base + 0x100 + 0x60] = base + 0x200;
        words[base + 0x200] = base;
        words[base + 0x3c] = base + 0x300;
        words[base + 0x300 + 0x10] = 19;
        words[base + 0x300 + 0x38] = base + 0x400;
    }
#include "../tools/m4-crt-heap-carry/host/model_arm_damage.inc"
};

void require(bool value, const char *message) {
    if (!value)
        throw std::runtime_error(message);
}
int main() {
    try {
        const OverrideSourceMesh roster[]{{"hip", 3, "hip"},   {"torso", 3, "torso"},
                                          {"larm", 3, "larm"}, {"lhand", 3, "lhand"},
                                          {"rarm", 3, "rarm"}, {"rhand", 3, "rhand"}};
        const OverrideModel model{"community.example:mech", roster, 6, 0, "example", "example"};
        mw34::chassis::Registration registration{"example", true, {}};
        for (auto &lod : registration.arm_damage)
            lod = {{"larm", "torso", {"larm", "lhand"}}, {"rarm", "torso", {"rarm", "rhand"}}};
        mw34::chassis::records = {registration};
        Fixture fixture;
        fixture.stump(0x1000, "larm", "larm_stub01");
        fixture.stump(0x2000, "rarm", "rarm_stub01");
        std::map<std::string, unsigned> meshes;
        for (const auto &mesh : roster)
            meshes.emplace(mesh.name, mesh.vertices);
        std::map<std::string, unsigned> nodes{{"larm_stub01", 0x1000}, {"rarm_stub01", 0x2000}};
        unsigned mask{};
        require(!fixture.override_arm_damage_match(model, meshes, nodes, mask),
                "intact tree uses exact identity");
        meshes.erase("larm");
        meshes.erase("lhand");
        meshes.emplace("larm_stub01", 3);
        require(fixture.override_arm_damage_match(model, meshes, nodes, mask) && mask == 2,
                "owned left arm loss admitted");
        meshes.erase("rarm");
        meshes.erase("rhand");
        meshes.emplace("rarm_stub01", 3);
        require(fixture.override_arm_damage_match(model, meshes, nodes, mask) && mask == 3,
                "owned both arms admitted");
        auto bad = meshes;
        bad["foreign"] = 3;
        require(!fixture.override_arm_damage_match(model, bad, nodes, mask),
                "foreign surviving mesh rejected");
        bad = meshes;
        bad["lhand"] = 3;
        require(!fixture.override_arm_damage_match(model, bad, nodes, mask),
                "partial arm deletion rejected");
        fixture.words[0x1400] = 1;
        require(!fixture.override_arm_damage_match(model, meshes, nodes, mask),
                "changed stump bytes rejected");
        fixture.words[0x1400] = 0;
        fixture.names[0x9000] = "foreign";
        require(!fixture.override_arm_damage_match(model, meshes, nodes, mask),
                "foreign stump parent rejected");
        fixture.names[0x9000] = "torso";
        mw34::chassis::records[0].resource = "other";
        require(!fixture.override_arm_damage_match(model, meshes, nodes, mask),
                "other chassis plans cannot admit this actor");
        std::cout << "owned arm damage checks passed\n";
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
