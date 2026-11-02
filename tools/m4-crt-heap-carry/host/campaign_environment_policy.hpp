#pragma once
#include <string_view>

namespace mw34::campaign {
// Presentation policy follows the approved 20-mission schedule. It is separate
// from pack colour/intensity values so an older pack cannot reopen sealed maps.
enum class SkySource : unsigned {
    OriginalClouds = 1, ClearDay = 2, Twilight = 3,
    ClearNight = 4, Interior = 5, DustHaze = 6
};
inline bool sealed_mission(const char* id) {
    const std::string_view key = id ? id : "";
    return key == "c2m2" || key == "c2m4" || key == "c3m5";
}
inline SkySource mission_sky_source(const char* id, bool interior) {
    const std::string_view key = id ? id : "";
    if (interior || sealed_mission(id)) return SkySource::Interior;
    if (key == "t1m2" || key == "c2m1" || key == "c3m1" || key == "c3m2" || key == "c4m6")
        return SkySource::ClearDay;
    if (key == "t1m1" || key == "t1m4" || key == "c1m1" || key == "c3m3" || key == "c3m4" ||
        key == "c4m3" || key == "c4m4" || key == "c4m5")
        return SkySource::Twilight;
    if (key == "c3m6") return SkySource::ClearNight;
    if (key == "c2m3") return SkySource::DustHaze;
    return SkySource::OriginalClouds;
}
} // namespace mw34::campaign
