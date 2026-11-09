#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <istream>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace mw34::headlights {
struct Lamp {
    std::string id, space, attachment;
    std::array<float, 3> position{}, direction{}, color{};
    float intensity{}, range{}, inner_angle{}, outer_angle{};
};

struct StockProfile {
    unsigned stock_id{};
    bool replacement{};
    std::string original_hash;
    std::array<std::string, 2> meshes;
    std::array<unsigned char, 32> identity{};
    std::vector<Lamp> lamps;
};

template <typename Number, typename Text, typename Fail>
inline std::vector<Lamp> read_lamps(Number number, Text text, Fail fail, bool donor) {
    std::vector<Lamp> result;
    const unsigned count = number();
    if (count > 8) fail();
    std::set<std::string> light_ids;
    auto scalar = [&](float low, float high) {
        const std::uint32_t bits = number();
        float value;
        static_assert(sizeof(value) == sizeof(bits) && std::numeric_limits<float>::is_iec559);
        std::memcpy(&value, &bits, sizeof(value));
        if (!std::isfinite(value) || value < low || value > high) fail();
        return value;
    };
    for (unsigned index = 0; index < count; ++index) {
        Lamp light{text(31), text(10), text(31)};
        for (unsigned char c : light.id)
            if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-')) fail();
        if (!light_ids.insert(light.id).second ||
            (light.space != "guest_node" && light.space != "donor_bone") ||
            (light.space == "donor_bone" && !donor)) fail();
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
        result.push_back(std::move(light));
    }
    return result;
}

inline std::vector<StockProfile> read_stock_catalog(std::istream &file) {
    auto fail = [] { throw std::runtime_error("Stock headlights: invalid catalog"); };
    auto bytes = [&](void *out, unsigned size) {
        if (!file.read(static_cast<char *>(out), size)) fail();
    };
    auto number = [&] {
        std::array<unsigned char, 4> value{};
        bytes(value.data(), 4);
        return unsigned(value[0]) | (unsigned(value[1]) << 8) |
               (unsigned(value[2]) << 16) | (unsigned(value[3]) << 24);
    };
    auto text = [&](unsigned maximum) {
        const auto size = number();
        if (size > maximum) fail();
        std::string value(size, '\0');
        bytes(value.data(), size);
        if (value.find('\0') != std::string::npos) fail();
        return value;
    };
    auto required_text = [&](unsigned maximum) {
        auto value = text(maximum);
        if (value.empty()) fail();
        return value;
    };
    char magic[8];
    bytes(magic, 8);
    if (std::memcmp(magic, "MWHDLT1\0", 8)) fail();
    const auto count = number();
    if (count > 18) fail();
    std::vector<StockProfile> result;
    for (unsigned i = 0; i < count; ++i) {
        StockProfile profile;
        profile.stock_id = number();
        const unsigned kind = number();
        if (profile.stock_id > 18 || profile.stock_id == 7 || kind > 1 ||
            (!result.empty() && profile.stock_id <= result.back().stock_id)) fail();
        profile.replacement = kind != 0;
        profile.original_hash = required_text(64);
        if (profile.original_hash.size() != 64 || profile.original_hash.find_first_not_of("0123456789abcdef") != std::string::npos) fail();
        for (auto &mesh : profile.meshes) {
            mesh = text(4096);
            if (mesh.empty() == profile.replacement) fail();
        }
        bytes(profile.identity.data(), unsigned(profile.identity.size()));
        if (std::all_of(profile.identity.begin(), profile.identity.end(), [](auto v) { return v == 0; })) fail();
        profile.lamps = read_lamps(number, required_text, fail, profile.replacement);
        result.push_back(std::move(profile));
    }
    if (file.peek() != std::char_traits<char>::eof() || file.bad()) fail();
    return result;
}

} // namespace mw34::headlights
