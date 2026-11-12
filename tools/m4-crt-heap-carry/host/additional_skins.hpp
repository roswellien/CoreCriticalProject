#pragma once
#include <cstdint>
#include <fstream>
#include <set>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::skins {
struct Addition { std::string id, name, chassis, close, distance; };
inline std::vector<Addition> read_additions(std::istream& file) {
    auto fail=[] { throw std::runtime_error("Additional skins: invalid catalog"); };
    auto bytes=[&](char* p, std::size_t n) { if(!file.read(p,std::streamsize(n)))fail(); };
    auto number=[&] { unsigned char p[4];bytes(reinterpret_cast<char*>(p),4);
        return std::uint32_t(p[0])|(std::uint32_t(p[1])<<8)|(std::uint32_t(p[2])<<16)|(std::uint32_t(p[3])<<24); };
    auto text=[&](unsigned max) { const auto n=number();if(!n||n>max)fail();std::string value(n,'\0');bytes(value.data(),n);
        if(value.find('\0')!=std::string::npos)fail();return value; };
    char magic[8];bytes(magic,8);if(std::string(magic,8)!=std::string("BWSKIN1\0",8))fail();
    const auto count=number();if(!count||count>128)fail();
    std::vector<Addition> result;std::set<std::string> ids;
    for(unsigned i=0;i<count;++i){Addition a{text(193),text(256),text(193),text(4096),text(4096)};
        if(a.id.find(':')==std::string::npos||!ids.insert(a.id).second)fail();
        for(const auto c:a.name)if(static_cast<unsigned char>(c)<32||static_cast<unsigned char>(c)>126)fail();
        result.push_back(std::move(a));}
    if(file.peek()!=std::char_traits<char>::eof())fail();
    return result;
}
// An owned base livery cannot stand in for an unprovided original alternate skin.
inline const char* replacement_texture_path(const char* explicit_path, const char* base_path,
                                            unsigned skin, const char* configured_path) {
    return explicit_path ? explicit_path : skin == 0 && base_path ? base_path : configured_path;
}
// Original per-instance skin identity is never mutated by an added appearance.
inline unsigned appearance(unsigned original, unsigned additional, bool player, bool player_preview) {
    return additional>=8 && (player||player_preview) ? additional : original;
}
inline unsigned selection(unsigned original, std::optional<unsigned> chosen, bool player, bool player_preview) {
    return chosen && (player||player_preview) ? *chosen : original;
}
} // namespace mw34::skins
