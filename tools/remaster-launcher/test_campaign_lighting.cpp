// Authored renderer/lifecycle controls; no original game assets or saves.
#include "sun_lighting.hpp"
#include "effect_lighting_settings.hpp"
#include <iostream>
void require(bool v,const char* text){if(!v)throw std::runtime_error(text);}
int main(int argc,char**){try{
 _putenv_s("MW34_SUN","1");_putenv_s("MW34_SUN_SHADOWS","0");_putenv_s("MW34_CAMPAIGN_LIGHTING","1");
 _putenv_s("MW34_MANUAL_LIGHTING",argc>1?"1":"0");
 auto& manager=mw34::campaign::CampaignManager::instance();
 auto& fixtures=mw34::fixtures::FixtureManager::instance();
 for(unsigned op=1;op<=4;++op)for(unsigned mission=1;mission<=(op<3?4:6);++mission){
  const auto id="c"+std::to_string(op)+"m"+std::to_string(mission);
  const auto region=op==4&&mission>3?"c4b":"c"+std::to_string(op);
  manager.observe_file("D:/isolated/zbd/"+region+"/readerm"+std::to_string(mission)+".zbd",true);
  require(manager.active_mission_id()==id,"Exact reader identity");
  manager.frontend();require(manager.active_mission_id()==id,"Loading frontend preserves pending mission");
  manager.enter_world();const auto s=mw34::sun::current_settings(1);
  const auto* env=manager.find_environment(id);require(env,"Mission exists");
  require(s.azimuth==(argc>1?mw34::sun::settings().azimuth:env->azimuth),"Mission environment or explicit manual override");
  require(!s.shadows,"Mission cannot enable user-disabled shadows");
  manager.observe_file("D:/isolated/zbd/c1/readerm1.zbd",false);require(manager.active_mission_id()==id,"Failed opens preserve mission");
  manager.observe_file("D:/isolated/games/pilot0101.mw3",true);require(manager.active_mission_id()==id,"Save filename is not mission identity");
  manager.observe_file("D:/isolated/zbd/c1/readerm1.zbd.bak",true);require(manager.active_mission_id()==id,"Reader suffix match is exact");
  manager.frontend();require(!manager.is_campaign_active(),"Return to menu resets campaign");
 }
 auto s=mw34::sun::settings();s.rain_wetness=.8f;s.dust_intensity=.3f;s.valley_fog_density=.4f;s.valley_fog_altitude=37;
 const auto u=mw34::sun::uniform({},s);
 require(u.weather[0]==.8f&&u.weather[2]==.3f&&u.weather_fog[0]==.4f&&u.weather_fog[1]==37,"Dedicated weather upload");
 require(u.color[3]==0&&u.sky_tint[3]==1&&u.detail==std::array<float,4>{},"Weather does not alias sky/water channels");
 const auto neutral=mw34::sun::uniform({},mw34::sun::settings());require(neutral.weather==std::array<float,4>{}&&neutral.weather_fog==std::array<float,4>{},"Weather off is neutral");
 for(unsigned limit=1;limit<=mw34::effects::capacity;++limit)for(unsigned weapons=0;weapons<=limit;++weapons)for(unsigned reserve=0;reserve<=32;++reserve){
  const auto slots=mw34::effects::fixture_slots(weapons,limit,reserve);require(weapons+slots<=limit,"Combined budget never exceeds requested limit");
  require(slots<=limit-std::min(reserve,limit),"Weapon reservation preserved");}
 const mw34::fixtures::FixtureDef def{"authored spotlight",1,1,0,1,30,2,{1,1,1},.35f,true};
 const std::vector<mw34::fixtures::Point> a{{0,0,0},{0,0,1},{1,0,0}},b{{10,0,0},{10,0,1},{11,0,0}};
 fixtures.observe_polygon(def,a,1,17);fixtures.observe_polygon(def,b,2,17);require(fixtures.active_count()==1,"Stable source updates rather than leaving old position");
 fixtures.begin_frame(100);require(fixtures.active_count()==1,"Verified off-camera sources do not expire by frame age");
 auto lights=fixtures.select_lights({10,0,0},1);require(lights.size()==1&&lights[0].start[0]>10&&lights[0].end[3]==2,"Updated location and distinct spotlight type");
 fixtures.observe_polygon(def,a,100);require(fixtures.active_count()==2,"Separate anonymous fixture");fixtures.begin_frame(101);fixtures.select_lights({100000,0,0},1);require(fixtures.active_count()==1,"Anonymous source expires outside retention distance");
 fixtures.remove_source(17);require(!fixtures.active_count(),"Invalidated/destroyed source removed");
 fixtures.observe_polygon(def,a,102,18);manager.observe_file("D:/isolated/zbd/t1/readerm1.zbd");require(!manager.is_campaign_active()&&!fixtures.active_count(),"Training clears campaign and fixture state");
 fixtures.observe_polygon(def,a,103,19);manager.observe_file("D:/isolated/zbd/c1/readeria1.zbd");require(!fixtures.active_count(),"Instant Action transition clears fixtures");
 fixtures.observe_polygon(def,a,104,20);manager.observe_file("D:/isolated/zbd/c1/readermp1.zbd");require(!fixtures.active_count(),"Multiplayer transition clears fixtures");
 std::cout<<"20 mission states, manual mode, failed opens, save-name isolation, menu/mode resets, weather fields and fixture lifecycle passed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
