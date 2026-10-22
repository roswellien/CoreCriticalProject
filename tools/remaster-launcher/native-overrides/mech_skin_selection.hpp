#pragma once
#include <array>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>
#include <utility>

namespace mw34::skins {
// The original material reference carries the chassis texture name and B-H
// suffix. Shared mechanical textures carry no chassis/skin identity.
inline std::optional<unsigned> texture_skin(std::string_view chassis,
                                            std::string name) {
    for (auto &c : name) if (c >= 'A' && c <= 'Z') c = char(c - 'A' + 'a');
    unsigned skin = 0;
    if (name.size() >= 2 && name[name.size()-2] == '_' &&
        name.back() >= 'b' && name.back() <= 'h') {
        skin = unsigned(name.back() - 'a');
        name.resize(name.size()-2);
    }
    struct Aliases { std::string_view chassis, close, distance, extra; };
    constexpr Aliases aliases[] = {
        {"bushwacker","bushwacker","bushwa_d",""},
        {"madcat","mcat","mcat_d","madcat"},
        {"vulture","vulture","vultur_d","vult"},
        {"thor","thor","thor_d",""},
        {"orion","orion","orion_d",""},
        {"daishi","daishi","daishi_d",""},
        {"shadowcat","shadowcat","shadow_d",""},
        {"puma","puma","puma_d",""},
        {"annihilator","annihilator","annihi_d",""},
        {"cauldron","cauldron","cauldr_d",""},
        {"sunder","sunder","sunder_d",""},
        {"supernova","supernova","supern_d",""},
        {"blackhawk","blkhwk","blackh_d","blackhawk"},
        {"champion","champion","champi_d",""},
        {"strider","strider","stride_d",""},
        {"avatar","avatar","avatar_d",""},
        {"owens","owens","owens_d",""},
        {"firefly","firefly","firefl_d",""},
        {"elemental","elemental","",""}
    };
    for (const auto &row : aliases) {
        if (row.chassis != chassis) continue;
        for (const auto prefix : {row.close,row.distance,row.extra}) {
            if (prefix.empty() || !name.starts_with(prefix)) continue;
            const auto tail = std::string_view(name).substr(prefix.size());
            if (tail.empty()) continue;
            bool digit=false, valid=true;
            for (const auto c : tail) {
                digit |= c >= '0' && c <= '9';
                valid &= (c >= '0' && c <= '9') || c == '_';
            }
            if (valid && digit) return skin;
        }
    }
    return std::nullopt;
}

struct Selection {
    std::optional<unsigned> value;
    bool mixed{};
    void observe(std::optional<unsigned> skin) {
        if (!skin) return;
        if (value && value != skin) mixed=true;
        else value=skin;
    }
    std::optional<unsigned> result() const { return mixed ? std::nullopt : value; }
};

inline std::string binding(std::string id, bool distant, unsigned skin) {
    if (!skin || skin > 7) return {};
    for (auto &c : id) if (c >= 'a' && c <= 'z') c = char(c-'a'+'A');
    return "MW34_"+id+(distant ? "_LOD1" : "")+"_SKIN_"+
           char('A'+skin)+"_TEXTURES";
}

// Complete pixel equality, not a short signature alone, admits a shared image.
// Unchanged weapons/glazing and close/distance copies need one colour allocation.
template<class Texture>
unsigned intern_texture(std::vector<Texture>& textures, Texture image) {
    const auto found=std::find_if(textures.begin(),textures.end(),[&](const auto& existing){
        return existing.name==image.name && existing.width==image.width &&
               existing.height==image.height && existing.hash==image.hash &&
               existing.pixels==image.pixels;
    });
    if(found!=textures.end())return unsigned(found-textures.begin());
    const auto index=unsigned(textures.size());textures.push_back(std::move(image));return index;
}
} // namespace mw34::skins
