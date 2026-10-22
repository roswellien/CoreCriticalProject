#pragma once
#include "effect_lighting.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace mw34::fixtures {

using Point = std::array<float, 3>;

struct FixtureDef {
    const char* name;
    std::uint32_t width;
    std::uint32_t height;
    std::uint32_t format;
    std::uint64_t hash;
    float radius;
    float intensity;
    std::array<float, 3> color;
    float normal_offset;
    bool is_spot;
};

// Registered light-bearing textures from game archives (both remastered and original banks)
inline const std::vector<FixtureDef>& fixture_catalog() {
    static const std::vector<FixtureDef> catalog = {
        // --- Remastered Texture Bank Entries ---
        // Streetlights (Facility street/flood lamps, t1/c3/c4)
        { "c5strt10", 512, 256, 0, 0xa7607277a3b5bc50ULL, 25.0f, 2.5f, {1.0f, 0.85f, 0.55f}, 0.25f, true },
        { "C5STRT10", 512, 256, 0, 0x35044880085af73aULL, 25.0f, 2.5f, {1.0f, 0.85f, 0.55f}, 0.25f, true },
        { "c5strt04", 256, 64,  0, 0xf76499b5b5e7f34aULL, 20.0f, 2.0f, {1.0f, 0.90f, 0.70f}, 0.20f, true },
        { "C5STRT04", 256, 64,  0, 0x78f15ee4fc1b7994ULL, 20.0f, 2.0f, {1.0f, 0.90f, 0.70f}, 0.20f, true },
        { "c5strt09", 512, 256, 0, 0x4001b11bd91c057eULL, 24.0f, 2.2f, {0.92f, 0.95f, 1.0f},  0.30f, true },
        { "C5STRT09", 256, 128, 0, 0x8f80244de21a8666ULL, 24.0f, 2.2f, {0.92f, 0.95f, 1.0f},  0.30f, true },
        { "c5strt12", 512, 512, 0, 0xf07cf43b2bb93754ULL, 22.0f, 2.0f, {1.0f, 0.88f, 0.60f}, 0.25f, true },
        { "C5STRT12", 512, 512, 0, 0xf7bd939403cff305ULL, 22.0f, 2.0f, {1.0f, 0.88f, 0.60f}, 0.25f, true },

        // Lighthouse Fixtures (Coastal/basin lighthouse optics, t1)
        { "lighthouse01", 1024, 1024, 0, 0x947209e376d92d19ULL, 45.0f, 3.5f, {1.0f, 0.96f, 0.85f}, 0.50f, true },
        { "lighthouse01", 256,  512,  0, 0x7c23915964643c9aULL, 45.0f, 3.5f, {1.0f, 0.96f, 0.85f}, 0.50f, true },
        { "lighthouse04", 1024, 1024, 0, 0xa2e3c0f4561543b2ULL, 45.0f, 3.5f, {1.0f, 0.96f, 0.85f}, 0.50f, true },
        { "lighthouse04", 512,  512,  0, 0xc1c06fd6f67f6dbeULL, 45.0f, 3.5f, {1.0f, 0.96f, 0.85f}, 0.50f, true },

        // Flares and Optical Beacons
        { "point_flare", 512, 512, 0, 0x5067582a24cf6701ULL, 20.0f, 2.5f, {1.0f, 0.40f, 0.20f}, 0.20f, false },
        { "point_flare", 256, 256, 0, 0x15109b94b8fa1749ULL, 20.0f, 2.5f, {1.0f, 0.40f, 0.20f}, 0.20f, false },
        { "lflare1",     512, 1024,0, 0x84ce6bbbb6e83af4ULL, 35.0f, 2.8f, {1.0f, 0.98f, 0.85f}, 0.35f, false },
        { "lflare1",     256, 512, 0, 0x2f6c446c2d0ddb6fULL, 35.0f, 2.8f, {1.0f, 0.98f, 0.85f}, 0.35f, false },
        { "LFLARE1",     256, 256, 0, 0xfe9b18aaef9f3758ULL, 35.0f, 2.8f, {1.0f, 0.98f, 0.85f}, 0.35f, false },
        { "lflare2",     1024,1024,0, 0x9ecdeff51395bd47ULL, 35.0f, 2.8f, {1.0f, 0.98f, 0.85f}, 0.35f, false },

        // Spotlights (Base perimeter floodlights, c2)
        { "spotlight1", 4096, 4096, 0, 0x5cc6301b581a978aULL, 30.0f, 2.8f, {1.0f, 0.92f, 0.75f}, 0.35f, true },
        { "spotlight1", 2048, 4096, 0, 0xd59989d3bc787f39ULL, 30.0f, 2.8f, {1.0f, 0.92f, 0.75f}, 0.35f, true },

        // Industrial Glow (Sodium furnace/reactor warning glow, c1)
        { "mfglow01", 2048, 1024, 0, 0x333428d448c3df50ULL, 25.0f, 3.0f, {1.0f, 0.62f, 0.12f}, 0.30f, false },
        { "MFGLOW01", 512,  512,  0, 0x1a7a35efc1eee6ccULL, 25.0f, 3.0f, {1.0f, 0.62f, 0.12f}, 0.30f, false },
        { "mfglow01", 1024, 512,  0, 0xfa23ad0c3220e4cdULL, 25.0f, 3.0f, {1.0f, 0.62f, 0.12f}, 0.30f, false },

        // Runway Guide Lights (Starport tarmac approach & edge markers, c4/c4b)
        { "runway01",   512,  1024, 0, 0xe54279b0f2a55871ULL, 18.0f, 2.0f, {0.65f, 0.85f, 1.0f}, 0.15f, false },
        { "runway01",   256,  512,  0, 0x3078a7f24745811eULL, 18.0f, 2.0f, {0.65f, 0.85f, 1.0f}, 0.15f, false },
        { "RUNWAY01",   1024, 2048, 0, 0x48d2736a66371dc9ULL, 18.0f, 2.0f, {0.65f, 0.85f, 1.0f}, 0.15f, false },
        { "m7runway01", 512,  512,  0, 0x4cfdb738f30449ccULL, 18.0f, 2.0f, {0.65f, 0.85f, 1.0f}, 0.15f, false },
        { "m7runway01", 256,  256,  0, 0x1df3258c3daa7e3fULL, 18.0f, 2.0f, {0.65f, 0.85f, 1.0f}, 0.15f, false },
        { "m7runway01", 2048, 2048, 0, 0xa42a5084eb878702ULL, 18.0f, 2.0f, {0.65f, 0.85f, 1.0f}, 0.15f, false },

        // --- Original 1999 Fallback Low-Res Entries ---
        { "spotlight1", 16, 16, 0, 0xbe78bcdbd952dd25ULL, 25.0f, 2.2f, {1.0f, 0.92f, 0.75f}, 0.35f, true },
        { "c5strt10", 128, 128, 0, 0x67a7fede3c04c2f6ULL, 22.0f, 2.0f, {1.0f, 0.85f, 0.55f}, 0.25f, true },
        { "c5strt04", 128, 128, 0, 0x3b0de89c32ab2aedULL, 18.0f, 1.8f, {1.0f, 0.90f, 0.70f}, 0.20f, true },
        { "c5strt09", 128, 64,  0, 0xdd908fa79466b504ULL, 24.0f, 2.2f, {0.92f, 0.95f, 1.0f}, 0.30f, true },
        { "c5strt12", 128, 128, 0, 0x8333d0d596f5bae8ULL, 20.0f, 1.9f, {1.0f, 0.88f, 0.60f}, 0.25f, true },
        { "mfglow01", 64, 64,   0, 0xa145008202a1d6c5ULL, 18.0f, 2.5f, {1.0f, 0.62f, 0.12f}, 0.30f, false },
        { "MFGLOW01", 32, 32,   0, 0x28a51783cae1a2b9ULL, 16.0f, 2.5f, {1.0f, 0.62f, 0.12f}, 0.30f, false },
        { "runway01", 32, 128,  0, 0xa569cf2341226320ULL, 14.0f, 1.6f, {0.65f, 0.85f, 1.0f}, 0.15f, false },
        { "m7runway01", 32, 128,0, 0xe0f262019d71eda1ULL, 14.0f, 1.6f, {0.65f, 0.85f, 1.0f}, 0.15f, false },
        { "lighthouse01", 128, 64, 0, 0x8ff49ed6765f32e1ULL, 35.0f, 3.0f, {1.0f, 0.95f, 0.85f}, 0.50f, true },
        { "lighthouse04", 64, 128, 0, 0x2fadd9136efae622ULL, 35.0f, 3.0f, {1.0f, 0.95f, 0.85f}, 0.50f, true },
        { "point_flare", 32, 32, 0, 0xf024277fb3c50b25ULL, 16.0f, 2.5f, {1.0f, 0.35f, 0.15f}, 0.20f, false },
        { "LFLARE1", 64, 64,    0, 0xb28f8fa0b3e5eff7ULL, 30.0f, 2.5f, {1.0f, 0.98f, 0.85f}, 0.35f, false },
        { "LFLARE2", 64, 64,    0, 0x8de51baf1a377c17ULL, 30.0f, 2.5f, {1.0f, 0.98f, 0.85f}, 0.35f, false },
    };
    return catalog;
}

inline const FixtureDef* match_fixture(unsigned width, unsigned height, unsigned format, std::uint64_t hash) {
    for (const auto& f : fixture_catalog()) {
        if (f.width == width && f.height == height && (f.format == 0 || format == 0 || f.format == format) && f.hash == hash) {
            return &f;
        }
    }
    return nullptr;
}

// Bounded visual source cache. Proven static sources survive camera culling;
// anonymous billboards exist only in their submission frame.
struct ActiveFixture {
    Point position{},direction{};
    const FixtureDef* def{};
    unsigned last_frame{};
    std::uint64_t source{};
};
class FixtureManager {
    std::vector<ActiveFixture> fixtures_;
public:
    static FixtureManager& instance(){static FixtureManager value;return value;}
    void clear(){fixtures_.clear();}
    void remove_source(std::uint64_t id){std::erase_if(fixtures_,[&](const auto& f){return f.source==id;});}
    void begin_frame(unsigned frame){std::erase_if(fixtures_,[&](const auto& f){return !f.source&&f.last_frame!=frame;});}
    void observe_polygon(const FixtureDef& def,const std::vector<Point>& points,unsigned frame,std::uint64_t source=0){
        if(points.size()<3||points.size()>4096)return;
        Point c{},normal{};
        for(const auto& p:points)for(unsigned i=0;i<3;++i){if(!std::isfinite(p[i])||std::abs(p[i])>1000000)return;c[i]+=p[i]/float(points.size());}
        // Newell normal tolerates repeated or collinear first vertices.
        for(size_t i=0;i<points.size();++i){const auto&a=points[i];const auto&b=points[(i+1)%points.size()];
            normal[0]+=(a[1]-b[1])*(a[2]+b[2]);normal[1]+=(a[2]-b[2])*(a[0]+b[0]);normal[2]+=(a[0]-b[0])*(a[1]+b[1]);}
        const float length=std::sqrt(effects::distance2(normal,{0,0,0}));if(!(length>1e-6f))return;
        for(unsigned i=0;i<3;++i){normal[i]/=length;c[i]+=normal[i]*def.normal_offset;}
        for(auto& old:fixtures_)if((source&&old.source==source)||(!source&&!old.source&&old.def==&def&&effects::distance2(c,old.position)<.0625f)){
            old={c,normal,&def,frame,source};return;
        }
        if(fixtures_.size()>=512){auto oldest=std::min_element(fixtures_.begin(),fixtures_.end(),[](const auto&a,const auto&b){return a.last_frame<b.last_frame;});*oldest={c,normal,&def,frame,source};}
        else fixtures_.push_back({c,normal,&def,frame,source});
    }
    std::vector<effects::Light> select_lights(const Point& eye,unsigned limit,float strength=1,float range_scale=1)const{
        struct Candidate{float score;effects::Light light;std::uint64_t source;};std::vector<Candidate> picks;
        for(const auto& f:fixtures_){const auto& d=*f.def;const float power=d.intensity*strength;
            // Range affects local illumination and selection consistently; it does not alter lamp brightness.
            const float radius=d.radius*range_scale;
            const float radius2=radius*radius;const float distance2=effects::distance2(eye,f.position);
            if(power<=0)continue;effects::Light l;l.start={f.position[0],f.position[1],f.position[2],radius};
            l.end=d.is_spot?std::array<float,4>{f.direction[0],f.direction[1],f.direction[2],float(effects::LightKind::spot)}:std::array<float,4>{f.position[0],f.position[1],f.position[2],float(effects::LightKind::point)};
            l.color={d.color[0],d.color[1],d.color[2],power};picks.push_back({power*radius2/(radius2+distance2),l,f.source});
        }
        std::stable_sort(picks.begin(),picks.end(),[](const auto&a,const auto&b){return a.score>b.score;});
        std::vector<effects::Light> out;for(size_t i=0;i<std::min<size_t>(limit,picks.size());++i)out.push_back(picks[i].light);return out;
    }
    size_t active_count()const{return fixtures_.size();}
};

} // namespace mw34::fixtures
