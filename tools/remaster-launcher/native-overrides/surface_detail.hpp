#pragma once
#include "sun_lighting.hpp"
#include <chrono>
#include <cstdint>

namespace mw34::detail {
// Presentation-only state. No guest clock queries or simulation writes.
struct Settings {
    bool water{}, clouds{};
    float water_strength{.45f}, cloud_strength{.35f}, scale{.06f}, speed{.025f};
};
inline const Settings& settings() {
    static const Settings value=[] {
        Settings s;
        s.water=sun::flag("MW34_WATER_DETAIL");s.clouds=sun::flag("MW34_CLOUD_DETAIL");
        s.water_strength=sun::parameter("MW34_WATER_DETAIL_STRENGTH",.45f,0,2);
        s.cloud_strength=sun::parameter("MW34_CLOUD_DETAIL_STRENGTH",.35f,0,2);
        s.scale=sun::parameter("MW34_WATER_DETAIL_SCALE",.06f,.001f,2);
        s.speed=sun::parameter("MW34_WATER_DETAIL_SPEED",.025f,0,.2f);
        return s;
    }();return value;
}
inline bool enabled(unsigned role) {
    const auto&s=settings();return (role==1||role==2)?s.water&&s.water_strength>0:role==3?s.clouds&&s.cloud_strength>0:false;
}
inline double presentation_time(std::uint64_t frame) {
    using Clock=std::chrono::steady_clock;
    static const auto start=Clock::now();
    static const bool fixed=std::getenv("MW34_DETAIL_FIXED_TIME")!=nullptr;
    static const float fixed_time=sun::parameter("MW34_DETAIL_FIXED_TIME",0,0,86400);
    static std::uint64_t previous=~std::uint64_t{};static double seconds{};
    if(fixed)return fixed_time;
    if(previous!=frame){seconds=std::chrono::duration<double>(Clock::now()-start).count();previous=frame;}
    return seconds;
}
inline void uniform(sun::Uniform&u,unsigned role,double seconds) {
    if(!enabled(role))return;
    const auto&s=settings();
    // Integer periodic frequencies in the water tile share this 2000-second
    // phase cycle. Wrapping cannot cause a visible jump, even after long play.
    u.detail={float(role),role==3?s.cloud_strength:s.water_strength,s.scale,0};
    // Speed is relative to the default; the shader's offsets wrap in full tiles.
    const double travel=seconds*s.speed;
    u.detail_motion={float(travel-std::floor(travel/50)*50),0,0,0};
}
}
