#include "../../m4-crt-heap-carry/host/additional_chassis.hpp"
#include <fstream>
#include <limits>
#include <sstream>

namespace {
void check(bool value) {
    if (!value)
        throw std::runtime_error("Chassis catalog check failed");
}
void number(std::string &out, unsigned n) {
    for (unsigned i = 0; i < 4; ++i)
        out += char((n >> (8 * i)) & 255);
}
void text(std::string &out, const std::string &value) {
    number(out, unsigned(value.size()));
    out += value;
}
std::string record(const std::string &id, const std::string &resource) {
    std::string out;
    text(out, id);
    text(out, "Example mech");
    text(out, resource);
    number(out, 10);
    return out;
}
void rejected(const std::string &bytes) {
    std::istringstream stream(bytes);
    bool failed{};
    try {
        mw34::chassis::read_catalog(stream);
    } catch (const std::runtime_error &) {
        failed = true;
    }
    check(failed);
}
} // namespace
int main(int argc, char **argv) {
    std::string header("MWCHAS1\0", 8);
    number(header, 1);
    const std::string valid = header + record("community.example:mech", "example");
    std::istringstream stream(valid);
    const auto records = mw34::chassis::read_catalog(stream);
    check(records.size() == 1 && records[0].metadata_template == 10);
    check(mw34::chassis::first_runtime_id > 19);
    for (std::size_t n = 0; n < valid.size(); ++n)
        rejected(valid.substr(0, n));
    rejected(valid + "x");
    rejected(header + record("community.example:mech", "madcat"));
    rejected(header + record("community.example:mech", "notmech"));
    rejected(header + record("unnamespaced", "example"));
    rejected(header + record("community.example:mech", "../bad"));
    std::string two("MWCHAS1\0", 8);
    number(two, 2);
    rejected(two + record("a:one", "one") + record("a:one", "two"));
    rejected(two + record("a:one", "same") + record("a:two", "same"));
    rejected(two + record("z:one", "one") + record("a:two", "two"));
    std::string visual("MWCHAS2\0", 8);
    number(visual, 1);
    visual += record("community.example:mech", "example");
    number(visual, 1);
    for (const char *value : {"madcat", "close.bin", "close.tex", "far.bin", "far.tex"})
        text(visual, value);
    std::istringstream visual_stream(visual);
    const auto models = mw34::chassis::read_catalog(visual_stream);
    check(models[0].metadata_template == 10 && models[0].visual_template == "madcat");
    check(models[0].meshes[1] == "far.bin" && models[0].textures[0] == "close.tex");
    for (std::size_t n = 0; n < visual.size(); ++n)
        rejected(visual.substr(0, n));
    rejected(visual + "x");
    std::string named("MWCHAS3\0", 8);
    number(named, 1);
    named += record("community.example:mech", "example");
    number(named, 0);
    text(named, "Olive Drab");
    std::istringstream named_stream(named);
    const auto labels = mw34::chassis::read_catalog(named_stream);
    check(labels[0].base_skin_name == "Olive Drab" && labels[0].visual_template.empty());
    for (std::size_t n = 0; n < named.size(); ++n)
        rejected(named.substr(0, n));
    rejected(named + "x");
    std::string empty("MWCHAS3\0", 8);
    number(empty, 1);
    empty += record("a:b", "other");
    number(empty, 0);
    auto with_label = [&](const std::string &label) {
        auto out = empty;
        text(out, label);
        return out;
    };
    for (const auto &label :
         {std::string("bad\n"), std::string(65, 'x'), std::string("bad\0name", 8)})
        rejected(with_label(label));
    for (const auto &label : {std::string{}, std::string(64, 'x')}) {
        std::istringstream accepted(with_label(label));
        check(mw34::chassis::read_catalog(accepted)[0].base_skin_name == label);
    }
    auto visual_named = visual;
    visual_named[6] = '3';
    text(visual_named, "Base");
    std::istringstream visual_named_stream(visual_named);
    const auto both = mw34::chassis::read_catalog(visual_named_stream);
    check(both[0].base_skin_name == "Base" && both[0].meshes[1] == "far.bin");
    auto socket_catalog = visual_named;
    socket_catalog[6] = '4';
    number(socket_catalog, 1);
    text(socket_catalog, "firepoint01");
    text(socket_catalog, "Forearm_Right");
    const double position[3]{4.0, -0.01, -1.13};
    socket_catalog.append(reinterpret_cast<const char *>(position), sizeof(position));
    std::istringstream socket_stream(socket_catalog);
    const auto socket_records = mw34::chassis::read_catalog(socket_stream);
    check(socket_records[0].sockets[0].node == "firepoint01" &&
          socket_records[0].sockets[0].position[2] == position[2]);
    for (std::size_t n = 0; n < socket_catalog.size(); ++n)
        rejected(socket_catalog.substr(0, n));
    rejected(socket_catalog + "x");
    auto bad_position = socket_catalog;
    const double bad = std::numeric_limits<double>::quiet_NaN();
    std::memcpy(bad_position.data() + bad_position.size() - 8, &bad, 8);
    rejected(bad_position);
    auto lamps = socket_catalog;
    lamps[6] = '5';
    number(lamps, 1);
    text(lamps, "left");
    text(lamps, "donor_bone");
    text(lamps, "Forearm_Right");
    for (float value : {1.f, 2.f, 3.f, 0.f, 0.f, -1.f, 1.f, .9f, .8f, 2.f, 50.f, 15.f, 30.f})
        number(lamps, std::bit_cast<unsigned>(value));
    std::istringstream lamp_stream(lamps);
    const auto lamp_records = mw34::chassis::read_catalog(lamp_stream);
    check(lamp_records[0].headlights.size() == 1 && lamp_records[0].headlights[0].range == 50);
    for (size_t n = 0; n < lamps.size(); ++n)
        rejected(lamps.substr(0, n));
    rejected(lamps + "x");
    auto invalid_cone = lamps;
    const unsigned angle = std::bit_cast<unsigned>(15.f);
    for (unsigned i = 0; i < 4; ++i)
        invalid_cone[invalid_cone.size() - 4 + i] = char(angle >> (8 * i));
    rejected(invalid_cone);
    std::string owned("MWCHAS6\0", 8);
    number(owned, 1);
    owned += record("community.example:mech", "example");
    number(owned, 0);
    number(owned, 0);
    number(owned, 0);
    number(owned, 0);
    number(owned, 1);
    for (unsigned lod = 0; lod < 2; ++lod) {
        text(owned, "mesh.bin");
        text(owned, "texture.bin");
        number(owned, 1);
        text(owned, "torso_polys");
        text(owned, "torso");
        number(owned, 3);
    }
    number(owned, 1);
    text(owned, "g25");
    text(owned, "g25");
    number(owned, 4);
    number(owned, 2);
    text(owned, "example_t0");
    number(owned, 0);
    text(owned, "example_t0_b");
    number(owned, 1);
    std::istringstream owned_stream(owned);
    const auto owned_records = mw34::chassis::read_catalog(owned_stream);
    check(owned_records[0].owned_visuals && owned_records[0].visual_template.empty());
    check(owned_records[0].owned_rosters[1][0].owner == "torso");
    check(owned_records[0].cockpit_roster[0].name == "g25");
    check(owned_records[0].skin_textures.at("example_t0_b") == 1);
    for (size_t n = 0; n < owned.size(); ++n)
        rejected(owned.substr(0, n));
    rejected(owned + "x");
    auto invalid_owned_skin = owned;
    invalid_owned_skin.back() = char(8);
    rejected(invalid_owned_skin);
    auto damaged = owned;
    damaged[6] = '7';
    for (unsigned lod = 0; lod < 2; ++lod) {
        number(damaged, 1);
        text(damaged, "larm");
        text(damaged, "torso");
        number(damaged, 1);
        text(damaged, "torso_polys");
    }
    std::istringstream damaged_stream(damaged);
    const auto damage_records = mw34::chassis::read_catalog(damaged_stream);
    check(damage_records[0].arm_damage[1][0].arm == "larm");
    check(damage_records[0].arm_damage[0][0].removed[0] == "torso_polys");
    for (size_t n = owned.size(); n < damaged.size(); ++n)
        rejected(damaged.substr(0, n));
    rejected(damaged + "x");
    auto foreign_damage = damaged;
    foreign_damage.back() = 'x';
    rejected(foreign_damage);
    auto weapon_visuals = damaged;
    weapon_visuals[6] = '8';
    for (unsigned lod = 0; lod < 2; ++lod) {
        number(weapon_visuals, 17); number(weapon_visuals, 0); // u64 mesh identity
        number(weapon_visuals, 1);
        text(weapon_visuals, "lhand"); text(weapon_visuals, "ERLargeLaser");
        text(weapon_visuals, "Forearm_Left");
        weapon_visuals.append(24, char(0));
    }
    std::istringstream weapon_stream(weapon_visuals);
    auto weapon_records = mw34::chassis::read_catalog(weapon_stream);
    check(weapon_records[0].weapon_visual_identity[1] == 17);
    check(weapon_records[0].weapon_visuals[0][0].source_control == "lhand");
    for (size_t n = damaged.size(); n < weapon_visuals.size(); ++n)
        rejected(weapon_visuals.substr(0, n));
    rejected(weapon_visuals + "x");
    auto wrong_weapon = weapon_visuals;
    wrong_weapon[wrong_weapon.size() - 24 - 1] = 'x'; rejected(wrong_weapon);
    auto invalid_position = weapon_visuals;
    const double nonfinite = std::numeric_limits<double>::quiet_NaN();
    std::memcpy(invalid_position.data() + invalid_position.size() - 24, &nonfinite, 8);
    rejected(invalid_position);
    if (argc == 2) {
        std::ifstream file(argv[1], std::ios::binary);
        check(mw34::chassis::read_catalog(file).size() == 2);
    }
}
