#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <istream>
#include <fstream>
#include <filesystem>
#include <cstdlib>
#include <set>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <cmath>
#include <cstring>
#include <bit>

namespace mw34::chassis {
// Stock 0..18 and the retail Mech Lab's 19 (unselected) stay untouched.
// Runtime numbers are session-local. Persist the namespaced id, never this number.
inline constexpr unsigned first_runtime_id = 32;
inline constexpr std::array<const char*, 19> stock_names{
    "annihilator", "avatar", "blackhawk", "bushwacker", "cauldron", "champion",
    "daishi", "elemental", "firefly", "madcat", "orion", "owens", "puma",
    "shadowcat", "strider", "sunder", "supernova", "thor", "vulture"};
struct Socket {std::string node, bone;std::array<double,3> position;};
struct Headlight {
    std::string id, space, attachment;
    std::array<float, 3> position{}, direction{}, color{};
    float intensity{}, range{}, inner_angle{}, outer_angle{};
};
struct SourceMesh { std::string name, owner; unsigned vertices{}; };
struct Registration {
    std::string id, name, resource;
    unsigned metadata_template{};
    std::string visual_template;
    std::string base_skin_name;
    std::array<std::string, 2> meshes, textures;
    std::vector<Socket> sockets;
    std::vector<Headlight> headlights;
    bool owned_visuals{};
    std::array<std::vector<SourceMesh>, 2> owned_rosters;
    std::vector<SourceMesh> cockpit_roster;
    std::map<std::string,unsigned> skin_textures;
};
inline bool identifier(const std::string& value, unsigned maximum) {
    if (value.empty() || value.size() > maximum) return false;
    for (unsigned char c : value)
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
              c == '.' || c == '_' || c == '-')) return false;
    return value.front() != '.' && value.front() != '_' && value.front() != '-';
}
inline std::vector<Registration> read_catalog(std::istream& file) {
    auto fail = [] { throw std::runtime_error("Additional chassis: invalid catalog"); };
    auto bytes = [&](char* p, unsigned n) { if (!file.read(p, n)) fail(); };
    auto number = [&] {
        unsigned char p[4]; bytes(reinterpret_cast<char*>(p), 4);
        return unsigned(p[0]) | (unsigned(p[1]) << 8) |
               (unsigned(p[2]) << 16) | (unsigned(p[3]) << 24);
    };
    auto text = [&](unsigned max) {
        const unsigned n = number(); if (!n || n > max) fail();
        std::string value(n, '\0'); bytes(value.data(), n);
        if (value.find('\0') != std::string::npos) fail();
        return value;
    };
    char magic[8]; bytes(magic, 8);
    const bool owned = std::string(magic, 8) == std::string("MWCHAS6\0", 8);
    const bool headlights = owned || std::string(magic, 8) == std::string("MWCHAS5\0", 8);
    const bool sockets = headlights || std::string(magic, 8) == std::string("MWCHAS4\0", 8);
    const bool names = sockets || std::string(magic, 8) == std::string("MWCHAS3\0", 8);
    const bool visuals = names || std::string(magic, 8) == std::string("MWCHAS2\0", 8);
    if (!visuals && std::string(magic, 8) != std::string("MWCHAS1\0", 8)) fail();
    const unsigned count = number(); if (!count || count > 128) fail();
    std::set<std::string> ids, resources;
    std::vector<Registration> result;
    for (unsigned i = 0; i < count; ++i) {
        Registration r{text(193), text(64), text(24), number()};
        const auto colon = r.id.find(':');
        if (colon == std::string::npos || !identifier(r.id.substr(0, colon), 128) ||
            !identifier(r.id.substr(colon + 1), 64) || !identifier(r.resource, 24) ||
            r.metadata_template >= stock_names.size() || r.metadata_template == 7 ||
            !ids.insert(r.id).second || !resources.insert(r.resource).second ||
            (!result.empty() && result.back().id >= r.id)) fail();
        if (r.resource == "notmech" ||
            std::find(stock_names.begin(), stock_names.end(), r.resource) != stock_names.end()) fail();
        for (unsigned char c : r.name) if (c < 32 || c > 126) fail();
        if (visuals) {
            const unsigned enabled = number(); if (enabled > 1) fail();
            if (enabled) {
                r.visual_template = text(24);
                if (r.visual_template == "elemental" ||
                    std::find(stock_names.begin(), stock_names.end(), r.visual_template) == stock_names.end()) fail();
                for (unsigned lod = 0; lod < 2; ++lod) {
                    r.meshes[lod] = text(4096); r.textures[lod] = text(4096);
                }
            }
        }
        if (names) {
            const unsigned n = number(); if (n > 64) fail();
            r.base_skin_name.resize(n); bytes(r.base_skin_name.data(), n);
            for (unsigned char c : r.base_skin_name) if (c < 32 || c > 126) fail();
        }
        if(sockets) {
            const unsigned count=number();if(count>64||(count&&r.visual_template.empty()))fail();
            std::set<std::string> nodes;
            for(unsigned i=0;i<count;++i) {
                Socket socket{text(11),text(31),{}};
                if(socket.node.size()!=11||socket.node.compare(0,9,"firepoint")||
                   socket.node[9]<'0'||socket.node[9]>'9'||socket.node[10]<'0'||socket.node[10]>'9'||
                   !nodes.insert(socket.node).second)fail();
                for(unsigned char c:socket.bone)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='.'||c=='-'))fail();
                for(auto& value:socket.position){bytes(reinterpret_cast<char*>(&value),8);if(!std::isfinite(value)||std::abs(value)>100)fail();}
                r.sockets.push_back(std::move(socket));
            }
        }
        if (headlights) {
            const unsigned count = number();
            if (count > 8) fail();
            std::set<std::string> light_ids;
            auto scalar = [&](float low, float high) {
                const float value = std::bit_cast<float>(std::uint32_t(number()));
                if (!std::isfinite(value) || value < low || value > high) fail();
                return value;
            };
            for (unsigned index = 0; index < count; ++index) {
                Headlight light{text(31), text(10), text(31)};
                for (unsigned char c : light.id)
                    if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-')) fail();
                if (!light_ids.insert(light.id).second ||
                    (light.space != "guest_node" && light.space != "donor_bone") ||
                    (light.space == "donor_bone" && r.visual_template.empty())) fail();
                for (unsigned char c : light.attachment)
                    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                          (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-')) fail();
                for (auto& v : light.position) v = scalar(-100, 100);
                for (auto& v : light.direction) v = scalar(-1, 1);
                const double length = std::hypot(double(light.direction[0]), double(light.direction[1]), double(light.direction[2]));
                if (std::abs(length - 1) > 0.00001) fail();
                for (auto& v : light.direction) v = float(v / length);
                for (auto& v : light.color) v = scalar(0, 1);
                light.intensity = scalar(0, 8);
                light.range = scalar(1, 256);
                light.inner_angle = scalar(0, 89);
                light.outer_angle = scalar(0, 89);
                if (light.inner_angle >= light.outer_angle) fail();
                r.headlights.push_back(std::move(light));
            }
        }
        if (owned) {
            const unsigned enabled = number(); if (enabled > 1) fail();
            r.owned_visuals = enabled != 0;
            if (r.owned_visuals) {
                if (!r.visual_template.empty() || !r.sockets.empty()) fail();
                auto roster = [&](bool required) {
                    const unsigned size = number(); if (size > 256 || (required && !size)) fail();
                    std::vector<SourceMesh> rows;
                    std::set<std::string> names;
                    for (unsigned at = 0; at < size; ++at) {
                        SourceMesh mesh{text(31), text(31), number()};
                        auto valid_name = [](const std::string& value) {
                            for (unsigned char c : value)
                                if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
                                      (c >= '0' && c <= '9') || c == '_' || c == '.' || c == '-')) return false;
                            return !value.empty();
                        };
                        if (!valid_name(mesh.name) || !valid_name(mesh.owner) ||
                            !names.insert(mesh.name).second || !mesh.vertices || mesh.vertices > 100000) fail();
                        rows.push_back(std::move(mesh));
                    }
                    return rows;
                };
                for (unsigned lod = 0; lod < 2; ++lod) {
                    r.meshes[lod] = text(4096); r.textures[lod] = text(4096);
                    r.owned_rosters[lod] = roster(true);
                }
                r.cockpit_roster = roster(false);
                const unsigned skins = number(); if (skins > 4096) fail();
                for (unsigned at = 0; at < skins; ++at) {
                    auto name = text(31); const unsigned skin = number();
                    if (skin > 7 || !identifier(name,31) || !r.skin_textures.emplace(name,skin).second) fail();
                }
            }
        }
        result.push_back(std::move(r));
    }
    if (file.peek() != std::char_traits<char>::eof()) fail();
    return result;
}
inline const std::vector<Registration>& configured_catalog() {
    static const auto records = [] {
        const char* path = std::getenv("MW34_ADDITIONAL_CHASSIS");
        if (!path || !*path) return std::vector<Registration>{};
        std::ifstream file(std::filesystem::u8path(path), std::ios::binary);
        return read_catalog(file);
    }();
    return records;
}
} // namespace mw34::chassis
