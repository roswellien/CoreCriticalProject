#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <istream>
#include <fstream>
#include <filesystem>
#include <cstdlib>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include <cmath>
#include <cstring>

namespace mw34::chassis {
// Stock 0..18 and the retail Mech Lab's 19 (unselected) stay untouched.
// Runtime numbers are session-local. Persist the namespaced id, never this number.
inline constexpr unsigned first_runtime_id = 32;
inline constexpr std::array<const char*, 19> stock_names{
    "annihilator", "avatar", "blackhawk", "bushwacker", "cauldron", "champion",
    "daishi", "elemental", "firefly", "madcat", "orion", "owens", "puma",
    "shadowcat", "strider", "sunder", "supernova", "thor", "vulture"};
struct Socket {std::string node, bone;std::array<double,3> position;};
struct Registration {
    std::string id, name, resource;
    unsigned metadata_template{};
    std::string visual_template;
    std::string base_skin_name;
    std::array<std::string, 2> meshes, textures;
    std::vector<Socket> sockets;
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
    const bool sockets = std::string(magic, 8) == std::string("MWCHAS4\0", 8);
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
