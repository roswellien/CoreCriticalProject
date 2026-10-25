// Authored mission/ABI checks. The optional output compares full uniform bytes
// against the preceding host without requiring any original game inputs.
#include "sun_lighting.hpp"
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
unsigned checks;
void require(bool value){++checks;if(!value)throw std::runtime_error("C3M1 sky lifecycle check failed at "+std::to_string(checks));}
int main(int argc,char**argv){try{
    const std::string mode=argc>1?argv[1]:"auto";
    _putenv_s("MW34_SUN","1");_putenv_s("MW34_SUN_SHADOWS","0");
    _putenv_s("MW34_MISSION_ENVIRONMENTS","");
    _putenv_s("MW34_MANUAL_LIGHTING",mode=="manual"?"1":"0");
    _putenv_s("MW34_CAMPAIGN_LIGHTING",mode=="off"?"0":"1");
    _putenv_s("MW34_WEATHER",mode=="weather-off"?"0":"1");
    auto& manager=mw34::campaign::CampaignManager::instance();
    FILE* output=argc>2?std::fopen(argv[2],"wb"):nullptr;
    if(argc>2&&!output)throw std::runtime_error("Uniform output unavailable");
    for(unsigned operation=1;operation<=4;++operation)
        for(unsigned mission=1;mission<=(operation<3?4:6);++mission){
            const auto id="c"+std::to_string(operation)+"m"+std::to_string(mission);
            const auto region=operation==4&&mission>3?"c4b":"c"+std::to_string(operation);
            manager.observe_file("D:/authored/zbd/"+region+"/readerm"+std::to_string(mission)+".zbd");
            manager.frontend();manager.enter_world();
            const auto settings=mw34::sun::current_settings(1.0);
            const auto uniform=mw34::sun::uniform({},settings);
            bool clear=false;
#ifdef MW34_EXPECT_CLEAR_SKY
            clear=id=="c3m1"&&mode!="manual"&&mode!="off";
            require(settings.clear_day_sky==clear);
#endif
            require(uniform.sky_tint[3]==(clear?2.f:1.f));
            require(sizeof(uniform)==912); // Current composed host includes emission regions.
            require(!settings.shadows);
            if(mode=="weather-off")require(uniform.weather==std::array<float,4>{});
            if(output)require(std::fwrite(&uniform,sizeof(uniform),1,output)==1);
            manager.frontend();
            require(mw34::sun::uniform({},mw34::sun::current_settings(1.0)).sky_tint[3]==1.f);
        }
    manager.observe_file("D:/authored/zbd/c3/readerm1.zbd");manager.enter_world();
    manager.observe_file("D:/authored/zbd/t1/readerm1.zbd");
    require(mw34::sun::uniform({},mw34::sun::current_settings()).sky_tint[3]==1.f);
    if(output)std::fclose(output);
    std::printf("%u C3M1-only sky, 20-mission, menu/Training/manual and uniform checks passed (%s)\n",checks,mode.c_str());
    return 0;
}catch(const std::exception&error){std::fprintf(stderr,"%s\n",error.what());return 1;}}
