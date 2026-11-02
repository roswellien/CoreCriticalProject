#include "campaign_lighting.hpp"
#include <iostream>
using mw34::campaign::MissionEnvironment;
bool same(const std::vector<MissionEnvironment>& a,const std::vector<MissionEnvironment>& b){
 if(a.size()!=b.size())return false;
 for(std::size_t i=0;i<a.size();++i){
  if(a[i].azimuth!=b[i].azimuth)return false;
  if(a[i].elevation!=b[i].elevation)return false;
  if(a[i].sun_color!=b[i].sun_color)return false;
  if(a[i].sun_strength!=b[i].sun_strength)return false;
  if(a[i].ambient_color!=b[i].ambient_color)return false;
  if(a[i].ambient_strength!=b[i].ambient_strength)return false;
  if(a[i].night_world_gain!=b[i].night_world_gain)return false;
  if(a[i].sky_tint!=b[i].sky_tint)return false;
  if(a[i].sky_brightness!=b[i].sky_brightness)return false;
  if(a[i].sky_glow_color!=b[i].sky_glow_color)return false;
  if(a[i].sky_glow_strength!=b[i].sky_glow_strength)return false;
  if(a[i].sky_glow_focus!=b[i].sky_glow_focus)return false;
  if(a[i].sky_grade!=b[i].sky_grade)return false;
  if(a[i].horizon_low!=b[i].horizon_low)return false;
  if(a[i].horizon_high!=b[i].horizon_high)return false;
  if(a[i].haze_color!=b[i].haze_color)return false;
  if(a[i].haze_scale!=b[i].haze_scale)return false;
  if(a[i].fog_distance!=b[i].fog_distance)return false;
  if(a[i].shadows!=b[i].shadows)return false;
  if(a[i].shadow_range!=b[i].shadow_range)return false;
  if(a[i].shadow_bias!=b[i].shadow_bias)return false;
  if(a[i].shadow_darkness!=b[i].shadow_darkness)return false;
  if(a[i].rain_intensity!=b[i].rain_intensity)return false;
  if(a[i].wet_reflection!=b[i].wet_reflection)return false;
  if(a[i].has_lightning!=b[i].has_lightning)return false;
  if(a[i].valley_fog_altitude!=b[i].valley_fog_altitude)return false;
  if(a[i].valley_fog_density!=b[i].valley_fog_density)return false;
  if(a[i].dust_intensity!=b[i].dust_intensity)return false;
  if(a[i].smog_intensity!=b[i].smog_intensity)return false;
  if(a[i].heat_shimmer!=b[i].heat_shimmer)return false;
  if(a[i].volcanic_ash!=b[i].volcanic_ash)return false;
  if(a[i].lava_glow!=b[i].lava_glow)return false;
  if(a[i].is_interior!=b[i].is_interior)return false;
  if(a[i].env_lights.size()!=b[i].env_lights.size())return false;
  for(std::size_t j=0;j<a[i].env_lights.size();++j){
   if(a[i].env_lights[j].start!=b[i].env_lights[j].start || a[i].env_lights[j].end!=b[i].env_lights[j].end || a[i].env_lights[j].color!=b[i].env_lights[j].color)return false;
  }
 }
 return true;
}
int main(int argc,char** argv){
 if(argc!=3)return 2;
 const auto baseline=mw34::campaign::builtin_mission_database();auto values=baseline;
 const std::string mode=argv[1];
 if(mode=="reject"){
  try{mw34::packs::load_mission_environments(argv[2],values);return 3;}
  catch(const std::runtime_error&){if(!same(values,baseline))return 4;return 0;}
 }
 mw34::packs::load_mission_environments(argv[2],values);
 if(mode=="roundtrip")return same(values,baseline)?0:5;
 if(mode=="training"){
  if(values.size()!=24)return 12;
  _putenv_s("MW34_MISSION_ENVIRONMENTS",argv[2]);
  auto& campaign=mw34::campaign::CampaignManager::instance();
  for(unsigned mission=1;mission<=4;++mission){
   campaign.observe_file("zbd/t1/readerm"+std::to_string(mission)+".zbd");
   if(campaign.active_mission_id()!="t1m"+std::to_string(mission))return 13;
   if(!campaign.active_environment() || campaign.active_environment()->elevation<=0)return 14;
   if((campaign.evaluate_weather(0).rain_intensity>.5f)!=(mission==3))return 15;
  }
  return 0;
 }
 if(mode!="changed")return 6;
 _putenv_s("MW34_MISSION_ENVIRONMENTS",argv[2]);
 auto& campaign=mw34::campaign::CampaignManager::instance();
 campaign.observe_file("zbd/c1/readerm1.zbd",false);if(campaign.is_campaign_active())return 7;
 campaign.observe_file("zbd/c1/readerm1.zbd");
 if(!campaign.active_environment() || campaign.active_environment()->ambient_strength!=.31f)return 8;
 campaign.observe_file("zbd/c1/readerm3.zbd");
 const auto weather=campaign.evaluate_weather(.02);
 if(weather.wet_reflection!=.75f || weather.lightning_flash!=0)return 9;
 campaign.observe_file("zbd/c2/readerm4.zbd");
 if(campaign.active_environment()->ambient_strength!=.40f)return 10;
 campaign.observe_file("zbd/t1/readerm1.zbd");if(campaign.is_campaign_active())return 11;
 return 0;
}
