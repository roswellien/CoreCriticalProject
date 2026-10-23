#include "../native-overrides/scene_uniform_base.hpp"
// Include the source snapshot's pinned shader-input builder, as selected with -I.
#include "sun_lighting.hpp"
#include <bit>
#include <iostream>

namespace {
unsigned checks{};
void require(bool value) { ++checks; if (!value) throw std::runtime_error("Scene uniform fixture failed"); }
}
int main(int argc,char** argv) {
    try {
        if (argc>1) {
            _putenv_s("MW34_UNIFORM_BASE_REUSE",argv[1]);
            if (std::strcmp(argv[1],"0")&&std::strcmp(argv[1],"1")) {
                bool rejected=false;
                try { mw34::submission::scene_uniform_base_enabled(); }
                catch (const std::runtime_error&) { rejected=true; }
                require(rejected);
            } else require(mw34::submission::scene_uniform_base_enabled()==(argv[1][0]=='1'));
        } else {
            using Uniform=mw34::sun::Uniform;
            for (bool enabled : {false,true}) for (unsigned scene=0;scene<12;++scene) {
                mw34::submission::SceneUniformBase<Uniform> cache(enabled);
                mw34::sun::Settings settings;
                settings.azimuth=float(scene)*30-90;settings.elevation=float(scene)*5-20;
                settings.color={.6f,.8f,1.f};settings.ambient=.15f+float(scene)*.02f;
                settings.rain_wetness=.12f;settings.heat_shimmer=.23f;settings.dust_intensity=.34f;
                settings.valley_fog_density=.45f;settings.valley_fog_altitude=17;
                std::array<float,12> normal{};
                unsigned calls=0;
                auto capture=[&] { return cache.capture(normal,[&] { ++calls;return mw34::sun::uniform(normal,settings); }); };
                require(cache.builds==0&&calls==0); // No eager initialization for empty scenes.
                auto initial=capture();auto reference=mw34::sun::uniform(normal,settings);
                require(!std::memcmp(&initial,&reference,sizeof(Uniform)));
                // Mutating one draw's effects must never contaminate the cached base.
                initial.emission_regions[31][3]=123.f;initial.world[0]=456.f;initial.shadow[0]=789.f;
                for (unsigned word=0;word<12;++word) for (unsigned bit=0;bit<32;++bit) {
                    normal.fill(0);normal[word]=std::bit_cast<float>(std::uint32_t(1)<<bit);
                    auto actual=capture();auto expected=mw34::sun::uniform(normal,settings);
                    require(!std::memcmp(&actual,&expected,sizeof(Uniform)));
                }
                require(calls==(enabled?1:385));
                require(cache.builds==calls&&cache.hits==(enabled?384:0));
            }
        }
        std::cout<<"Scene lighting base checks="<<checks<<" failures=0\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
