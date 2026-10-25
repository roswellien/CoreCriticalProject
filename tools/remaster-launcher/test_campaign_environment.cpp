// Authored lifecycle and effective presentation checks; no original assets.
#include "sun_lighting.hpp"
#include <cstdio>
#include <stdexcept>
#include <string>
static unsigned checks;
static void require(bool value,const char* message){
    ++checks;if(!value)throw std::runtime_error(message);
}
int main(int argc,char**argv){try{
    const std::string mode=argc>1?argv[1]:"auto";
    _putenv_s("MW34_SUN","1");_putenv_s("MW34_SUN_SHADOWS","0");
    _putenv_s("MW34_CAMPAIGN_LIGHTING",mode=="off"?"0":"1");
    _putenv_s("MW34_MANUAL_LIGHTING",mode=="manual"?"1":"0");
    _putenv_s("MW34_WEATHER",mode=="weather-off"?"0":"1");
    // Expected schedule is independent of the selector implementation.
    const unsigned expected[]={3,1,1,1, 2,5,6,5, 2,2,3,3,5,4, 1,1,3,3,3,2};
    const bool automatic=mode!="off"&&mode!="manual";
    auto& manager=mw34::campaign::CampaignManager::instance();
    FILE* output=argc>2?std::fopen(argv[2],"wb"):nullptr;
    if(argc>2&&!output)throw std::runtime_error("Cannot write uniform evidence");
    unsigned index=0;
    for(unsigned op=1;op<=4;++op)for(unsigned mission=1;mission<=(op<3?4:6);++mission,++index){
        const auto id="c"+std::to_string(op)+"m"+std::to_string(mission);
        const auto region=op==4&&mission>3?"c4b":"c"+std::to_string(op);
        manager.observe_file("D:/authored/zbd/"+region+"/readerm"+std::to_string(mission)+".zbd");
        manager.frontend();manager.enter_world();
        const auto* env=manager.active_environment();require(env,"Missing mission");
        const auto settings=mw34::sun::current_settings(1);
        const auto uniform=mw34::sun::uniform({},settings);
        require(uniform.sky_tint[3]==float(automatic?expected[index]:1),"Wrong effective sky policy");
        require(!settings.shadows,"User-disabled shadows enabled by mission");
        if(automatic&&expected[index]==5){
            require(settings.strength==0&&settings.glow_strength==0&&settings.sky_brightness==0,"Outdoor light inside sealed mission");
            require(settings.color==std::array<float,3>{}&&settings.sky_tint==std::array<float,3>{},"Natural light colour inside sealed mission");
            require(settings.night_world_gain==0&&settings.heat_shimmer==0&&settings.dust_intensity==0,"Outdoor fill/weather inside sealed mission");
            const auto weather=manager.evaluate_weather(0); // Strike time exercises suppression.
            require(weather.is_interior&&weather.lightning_flash==0&&weather.rain_intensity==0,"Exterior rain/lightning inside sealed mission");
            require(weather.dust_intensity==0&&weather.smog_intensity==0&&weather.heat_shimmer==0&&weather.volcanic_ash==0&&weather.lava_glow==0,"Exterior particles inside sealed mission");
            // A later pack cannot turn the sealed map into an exterior.
            auto bad=*env;bad.is_interior=false;bad.sun_strength=4;bad.sky_brightness=4;
            bad.sky_glow_strength=4;bad.sun_color=bad.sky_tint={4,4,4};bad.shadows=true;
            auto guarded=mw34::sun::settings();mw34::sun::apply_campaign_environment(guarded,bad,0);
            require(guarded.strength==0&&guarded.glow_strength==0&&guarded.sky_brightness==0,"Old pack defeats sealed light policy");
            require(!guarded.shadows&&guarded.night_world_gain==0&&unsigned(guarded.sky_source)==5,"Old pack defeats sealed sky policy");
            if(mode!="weather-off"){
                require(settings.rain_wetness==env->wet_reflection,"Interior dampness lost");
                require(settings.valley_fog_density==env->valley_fog_density,"Local vent mist lost");
            }
        }
        if(mode=="weather-off")require(uniform.weather==std::array<float,4>{}&&uniform.weather_fog==std::array<float,4>{},"Disabled weather not neutral");
        if(output)require(std::fwrite(&uniform,sizeof uniform,1,output)==1,"Uniform write failed");
        manager.observe_file("D:/authored/zbd/c1/readerm1.zbd",false);
        require(manager.active_mission_id()==id,"Failed reader changed mission");
        manager.frontend();require(!manager.is_campaign_active(),"Menu did not reset mission");
        require(mw34::sun::uniform({},mw34::sun::current_settings()).sky_tint[3]==1,"Sky policy leaked into menu");
    }
    manager.observe_file("D:/authored/zbd/c3/readerm5.zbd");manager.enter_world();
    manager.observe_file("D:/authored/zbd/t1/readerm1.zbd");
    require(!manager.is_campaign_active()&&mw34::sun::uniform({},mw34::sun::current_settings()).sky_tint[3]==1,"Interior policy leaked into Training");
    manager.observe_file("D:/authored/zbd/c1/readerm1.zbd");manager.enter_world();
    const auto rain=manager.find_environment("c1m3");require(rain&&rain->has_lightning,"Storm preset lost");
    manager.observe_file("D:/authored/zbd/c1/readerm3.zbd");manager.enter_world();
    require(manager.evaluate_weather(0).lightning_flash>0,"Outdoor lightning suppressed");
    if(output)std::fclose(output);
    std::printf("%u all-20 campaign sky/interior/lifecycle checks passed (%s)\n",checks,mode.c_str());return 0;
}catch(const std::exception& error){std::fprintf(stderr,"%s\n",error.what());return 1;}}
