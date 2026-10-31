#pragma once
#include "effect_lighting.hpp"
#include "vehicle_lighting.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <map>
#include <vector>

namespace mw34::fixtures {

using Point = std::array<float, 3>;
// Moving sources participate in the same final selection without entering the
// scenery retention cache. Caller order is its stable identity tie breaker.
struct MovingLight { effects::Light light; std::array<float, 4> cone{}; };
struct SelectedLight { effects::Light light; std::array<float, 4> cone{}; };

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
    std::vector<std::array<float,4>> emission_regions{};
    bool emission_only{false};
    std::vector<float> emission_radii{};
    std::vector<Point> emission_colors{};
};

// Registered light-bearing textures from game archives (both remastered and original banks)
inline const std::vector<FixtureDef>& fixture_catalog() {
    static const std::vector<FixtureDef> catalog = {
        #include "c2_material_fixtures.inc"
        #include "c1_material_fixtures.inc"
        #include "c3_material_fixtures.inc"
        #include "t1_material_fixtures.inc"
        #include "c4_material_fixtures.inc"
        // --- Remastered Texture Bank Entries ---
        // Streetlights (Facility street/flood lamps, t1/c3/c4)

        // Lighthouse Fixtures (Coastal/basin lighthouse optics, t1)

        // Flares and Optical Beacons

        // Spotlights (Base perimeter floodlights, c2)
        { "spotlight1", 4096, 4096, 0, 0x5cc6301b581a978aULL, 30.0f, 2.8f, {1.0f, 0.92f, 0.75f}, 0.35f, true },
        { "spotlight1", 2048, 4096, 0, 0xd59989d3bc787f39ULL, 30.0f, 2.8f, {1.0f, 0.92f, 0.75f}, 0.35f, true },

        // Industrial Glow (Sodium furnace/reactor warning glow, c1)
        { "mfglow01", 2048, 1024, 0, 0x333428d448c3df50ULL, 25.0f, 3.0f, {1.0f, 0.62f, 0.12f}, 0.30f, false },
        { "MFGLOW01", 512,  512,  0, 0x1a7a35efc1eee6ccULL, 25.0f, 3.0f, {1.0f, 0.62f, 0.12f}, 0.30f, false },
        { "mfglow01", 1024, 512,  0, 0xfa23ad0c3220e4cdULL, 25.0f, 3.0f, {1.0f, 0.62f, 0.12f}, 0.30f, false },

        // Runway Guide Lights (Starport tarmac approach & edge markers, c4/c4b)

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
// anonymous observations are retained within the configured player distance.
struct ActiveFixture {
    Point position{},direction{};
    const FixtureDef* def{};
    unsigned last_frame{};
    std::uint64_t source{};
    std::uint64_t owner{};
    double first_seen{};bool selected{};
};
class FixtureManager {
    std::vector<ActiveFixture> fixtures_;
    // std::map keeps active light-definition pointers stable as islands arrive.
    std::map<std::pair<const FixtureDef*,size_t>,FixtureDef> region_definitions_;
    std::map<const FixtureDef*,FixtureDef> directional_definitions_;
    unsigned frame_{};double time_{};
public:
    static FixtureManager& instance(){static FixtureManager value;return value;}
    void clear(){fixtures_.clear();region_definitions_.clear();directional_definitions_.clear();}
    const FixtureDef& directional(const FixtureDef& def){
        auto [it,added]=directional_definitions_.try_emplace(&def,def);
        it->second.is_spot=true;return it->second;
    }
    void remove_source(std::uint64_t id){std::erase_if(fixtures_,[&](const auto& f){return f.source==id||f.owner==id;});}
    void begin_frame(unsigned frame,double time=0){frame_=frame;time_=time;}
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
            const double first=old.first_seen;const bool selected=old.selected;old={c,normal,&def,frame,source,0,first,selected};return;
        }
        if(fixtures_.size()>=4096){auto oldest=std::min_element(fixtures_.begin(),fixtures_.end(),[](const auto&a,const auto&b){return a.last_frame<b.last_frame;});*oldest={c,normal,&def,frame,source,0,time_};}
        else fixtures_.push_back({c,normal,&def,frame,source,0,time_});
    }
    std::vector<SelectedLight> select_combined(const Point& eye,unsigned limit,float strength=1,float range_scale=1,float retain_distance=160,float fade_distance=32,const std::vector<MovingLight>& moving={},bool scenery=true){
        // View-frustum visibility never deletes a fixture. Invalidated original
        // sources still remove it immediately. Keep proven identities until their
        // owner invalidates, so returning toward a cached source needs no redraw.
        // Only anonymous observations expire by distance.
        std::erase_if(fixtures_,[&](const auto& f){const float keep=std::max(retain_distance,f.def->radius*range_scale*4);return !f.source&&f.last_frame!=frame_&&effects::distance2(eye,f.position)>keep*keep;});
        struct Candidate{float score;effects::Light light;size_t index;std::array<float,4> cone{};};std::vector<Candidate> picks;
        for(size_t index=0;scenery&&index<fixtures_.size();++index){auto& f=fixtures_[index];const auto& d=*f.def;
            const float radius=d.radius*range_scale,radius2=radius*radius,distance2=effects::distance2(eye,f.position);
            const float distance=std::sqrt(distance2);
            const float keep=std::max(retain_distance,radius*4),band=std::max(fade_distance,radius);
            // Retention fades only sources no longer submitted by the game.
            // A visible lamp must illuminate its surroundings immediately, even
            // when the camera is outside the offscreen retention distance.
            float fade=f.last_frame==frame_?1.f:std::clamp((keep-distance)/band,0.f,1.f);
            fade=fade*fade*(3-2*fade);
            const float power=d.intensity*strength*fade;
            if(power<=0||radius<=0)continue;effects::Light l;l.start={f.position[0],f.position[1],f.position[2],radius};
            l.end=d.is_spot?std::array<float,4>{f.direction[0],f.direction[1],f.direction[2],float(effects::LightKind::spot)}:std::array<float,4>{f.position[0],f.position[1],f.position[2],float(effects::LightKind::point)};
            l.color={d.color[0],d.color[1],d.color[2],power};
            // Keep incumbents unless a new candidate is materially stronger.
            picks.push_back({power*radius2/(radius2+distance2)*(f.selected?1.25f:1.f),l,index});
        }
        for(const auto& source:moving){
            const auto& light=source.light;
            const float radius2=light.start[3]*light.start[3];
            const float distance2=effects::distance2(eye,{light.start[0],light.start[1],light.start[2]});
            if(light.color[3]>0&&radius2>0)
                picks.push_back({light.color[3]*radius2/(radius2+distance2),light,fixtures_.size(),source.cone});
        }
        std::stable_sort(picks.begin(),picks.end(),[](const auto&a,const auto&b){return a.score>b.score;});
        for(auto& f:fixtures_)f.selected=false;
        std::vector<SelectedLight> out;
        for(size_t i=0;i<std::min<size_t>(limit,picks.size());++i){
            if(picks[i].index<fixtures_.size())fixtures_[picks[i].index].selected=true;
            out.push_back({picks[i].light,picks[i].cone});
        }
        return out;
    }

    std::vector<effects::Light> select_lights(const Point& eye,unsigned limit,float strength=1,float range_scale=1,float retain_distance=160,float fade_distance=32){
        std::vector<effects::Light> result;
        for(const auto& selected:select_combined(eye,limit,strength,range_scale,retain_distance,fade_distance))result.push_back(selected.light);
        return result;
    }

    struct UvPoint { Point p; float u,v; };
    void observe_regions(const FixtureDef& def,const std::vector<UvPoint>& triangles,unsigned frame,std::uint64_t owner,const Point* forward=nullptr){
        if(def.emission_only||def.radius<=0)return;
        for(size_t island=0;island<def.emission_regions.size();++island){
            const float radius=island<def.emission_radii.size()?def.emission_radii[island]:def.radius;
            if(radius<=0)continue; // Glow-only island: included in shader mask, no point light.
            const FixtureDef* light_def=&def;
            if(!def.emission_radii.empty()||!def.emission_colors.empty()){
                auto [it,inserted]=region_definitions_.try_emplace(std::make_pair(&def,island),def);
                if(inserted){it->second.radius=radius;if(island<def.emission_colors.size())it->second.color=def.emission_colors[island];}
                light_def=&it->second;
            }
            const auto& rect=def.emission_regions[island];float best=0;Point position{},normal{};
            for(size_t at=0;at+2<triangles.size();at+=3){
                const auto&a=triangles[at];const auto&b=triangles[at+1];const auto&c=triangles[at+2];
                std::vector<UvPoint> poly{a,b,c};
                for(unsigned edge=0;edge<4&&!poly.empty();++edge){std::vector<UvPoint> clipped;
                    auto distance=[&](const UvPoint& p){return edge==0?p.u-rect[0]:edge==1?rect[2]-p.u:edge==2?p.v-rect[1]:rect[3]-p.v;};
                    auto previous=poly.back();float dp=distance(previous);
                    for(const auto& current:poly){const float dc=distance(current);
                        if((dp>=0)!=(dc>=0)){const float t=dp/(dp-dc);UvPoint cross{};for(unsigned j=0;j<3;++j)cross.p[j]=previous.p[j]+t*(current.p[j]-previous.p[j]);cross.u=previous.u+t*(current.u-previous.u);cross.v=previous.v+t*(current.v-previous.v);clipped.push_back(cross);}
                        if(dc>=0)clipped.push_back(current);previous=current;dp=dc;
                    }poly=std::move(clipped);
                }
                if(poly.size()<3)continue;float area=0;for(size_t i=0;i<poly.size();++i){const auto&p=poly[i];const auto&q=poly[(i+1)%poly.size()];area+=p.u*q.v-q.u*p.v;}area=std::abs(area);
                // The visible fragment centroid changes at the screen edge. Recover
                // the authored island center through the triangle's affine UV mapping
                // instead, including when that center is just outside the clipped
                // triangle. Otherwise one physical lamp drifts/duplicates in retention.
                if(area<=best||area<1e-10f)continue;
                const double bu=double(b.u)-a.u,bv=double(b.v)-a.v,cu=double(c.u)-a.u,cv=double(c.v)-a.v;
                const double determinant=bu*cv-bv*cu;
                if(!std::isfinite(determinant)||std::abs(determinant)<1e-12)continue;
                const double du=(double(rect[0])+rect[2])*.5-a.u,dv=(double(rect[1])+rect[3])*.5-a.v;
                const double wb=(du*cv-dv*cu)/determinant,wc=(bu*dv-bv*du)/determinant;
                Point anchor{};bool valid=true;
                for(unsigned j=0;j<3;++j){const double value=a.p[j]+wb*(double(b.p[j])-a.p[j])+wc*(double(c.p[j])-a.p[j]);
                    if(!std::isfinite(value)||std::abs(value)>1000000)valid=false;anchor[j]=float(value);}
                if(!valid)continue;best=area;position=anchor;
                Point e{},f{};for(unsigned j=0;j<3;++j){e[j]=b.p[j]-a.p[j];f[j]=c.p[j]-a.p[j];}normal={e[1]*f[2]-e[2]*f[1],e[2]*f[0]-e[0]*f[2],e[0]*f[1]-e[1]*f[0]};
            }
            const float length=std::sqrt(effects::distance2(normal,{0,0,0}));if(best<=0||length<=1e-6f)continue;
            for(unsigned j=0;j<3;++j){normal[j]/=length;position[j]+=normal[j]*def.normal_offset;}
            if(forward){float facing=0;for(unsigned j=0;j<3;++j)facing+=normal[j]*(*forward)[j];
                if(facing<.5f)continue;normal=*forward;}

            const std::uint64_t id=owner?(owner^(0x9e3779b97f4a7c15ULL*(island+1))):0;
            bool updated=false;for(auto&old:fixtures_)if((id&&old.source==id)||(!id&&!old.source&&old.def==light_def&&effects::distance2(old.position,position)<.0625f)){const double first=old.first_seen;const bool selected=old.selected;old={position,normal,light_def,frame,id,owner,first,selected};updated=true;break;}
            if(!updated&&fixtures_.size()<4096)fixtures_.push_back({position,normal,light_def,frame,id,owner,time_});
        }
    }

    size_t active_count()const{return fixtures_.size();}
};

} // namespace mw34::fixtures
