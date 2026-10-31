#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::packs {
// MW34ENV1 is a bounded little-endian data contract, never native struct bytes.
// Parse transactionally so malformed data cannot leave half-updated mission state.
template<class Environment>
unsigned load_mission_environments(const std::string& path, std::vector<Environment>& database) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("Cannot open required mission lighting catalog");
    stream.seekg(0, std::ios::end);
    const auto size = stream.tellg();
    if (size < 12 || size > 262144) throw std::runtime_error("Invalid mission lighting catalog size");
    stream.seekg(0);
    std::vector<unsigned char> data(static_cast<std::size_t>(size));
    if (!stream.read(reinterpret_cast<char*>(data.data()), size)) throw std::runtime_error("Truncated mission lighting catalog");
    if (std::memcmp(data.data(), "MW34ENV1", 8)) throw std::runtime_error("Unsupported mission lighting catalog");
    std::size_t cursor = 8;
    auto u32 = [&]() {
        if (cursor + 4 > data.size()) throw std::runtime_error("Truncated mission lighting value");
        std::uint32_t value{};
        for (unsigned i=0;i<4;++i) value |= std::uint32_t(data[cursor++]) << (8*i);
        return value;
    };
    auto number = [&](float low, float high) {
        const auto bits = u32(); float value{}; static_assert(sizeof(value)==sizeof(bits));
        std::memcpy(&value, &bits, 4);
        if (!std::isfinite(value) || value < low || value > high) throw std::runtime_error("Invalid mission lighting number");
        return value;
    };
    auto flag = [&]() { const auto value=u32(); if(value>1) throw std::runtime_error("Invalid mission lighting flag"); return value!=0; };
    const auto count=u32();
    if(count>24) throw std::runtime_error("Too many mission environments");
    auto updated=database; std::set<std::string> seen;
    for(unsigned item=0;item<count;++item) {
        const auto length=u32();
        if(length<1 || length>16 || cursor+length>data.size()) throw std::runtime_error("Invalid mission lighting identity");
        const std::string id(reinterpret_cast<const char*>(data.data()+cursor),length);cursor+=length;
        if(!seen.insert(id).second) throw std::runtime_error("Duplicate mission lighting identity");
        auto found=std::find_if(updated.begin(),updated.end(),[&](const auto& value){return id==value.id;});
        if(found==updated.end()) {
            static constexpr const char* training_ids[] = {"t1m1", "t1m2", "t1m3", "t1m4"};
            const auto training = std::find_if(std::begin(training_ids), std::end(training_ids),
                [&](const char* value) { return id == value; });
            if(training==std::end(training_ids) || updated.empty())
                throw std::runtime_error("Unknown mission lighting identity");
            auto environment=updated.front();
            environment.id=*training;
            updated.push_back(environment);
            found=std::prev(updated.end());
        }
        auto& env=*found;
        env.azimuth=number(-360.0f, 360.0f);
        env.elevation=number(0.0f, 90.0f);
        for(auto& component:env.sun_color) component=number(0.0f, 4.0f);
        env.sun_strength=number(0.0f, 4.0f);
        for(auto& component:env.ambient_color) component=number(0.0f, 4.0f);
        env.ambient_strength=number(0.0f, 2.0f);
        env.night_world_gain=number(0.0f, 1.0f);
        for(auto& component:env.sky_tint) component=number(0.0f, 4.0f);
        env.sky_brightness=number(0.0f, 4.0f);
        for(auto& component:env.sky_glow_color) component=number(0.0f, 4.0f);
        env.sky_glow_strength=number(0.0f, 4.0f);
        env.sky_glow_focus=number(0.0f, 20.0f);
        for(auto& component:env.sky_grade) component=number(0.0f, 1.0f);
        env.horizon_low=number(0.0f, 0.9f);
        env.horizon_high=number(0.0f, 1.0f);
        for(auto& component:env.haze_color) component=number(0.0f, 1.0f);
        for(auto& component:env.haze_scale) component=number(0.0f, 4.0f);
        env.fog_distance=number(0.0f, 10000.0f);
        env.shadows=flag();
        env.shadow_range=number(0.0f, 10000.0f);
        env.shadow_bias=number(0.0f, 10.0f);
        env.shadow_darkness=number(0.0f, 1.0f);
        env.rain_intensity=number(0.0f, 1.0f);
        env.wet_reflection=number(0.0f, 1.0f);
        env.has_lightning=flag();
        env.valley_fog_altitude=number(-10000.0f, 10000.0f);
        env.valley_fog_density=number(0.0f, 4.0f);
        env.dust_intensity=number(0.0f, 1.0f);
        env.smog_intensity=number(0.0f, 1.0f);
        env.heat_shimmer=number(0.0f, 1.0f);
        env.volcanic_ash=number(0.0f, 1.0f);
        env.lava_glow=number(0.0f, 1.0f);
        env.is_interior=flag();
        if(env.horizon_low>=env.horizon_high && !(env.is_interior && env.horizon_low==0 && env.horizon_high==0))
            throw std::runtime_error("Invalid mission lighting horizon");
        const auto lights=u32();
        if(lights>64) throw std::runtime_error("Too many mission light emitters");
        env.env_lights.clear();env.env_lights.resize(lights);
        for(auto& light:env.env_lights) {
            for(auto& value:light.start)value=number(-1000000.f,1000000.f);
            if(light.start[3]<0 || light.start[3]>10000)throw std::runtime_error("Invalid emitter radius");
            for(auto& value:light.end)value=number(-1000000.f,1000000.f);
            for(auto& value:light.color)value=number(0.f,64.f);
        }
    }
    if(cursor!=data.size())throw std::runtime_error("Trailing mission lighting bytes");
    database.swap(updated);
    return count;
}
} // namespace mw34::packs
