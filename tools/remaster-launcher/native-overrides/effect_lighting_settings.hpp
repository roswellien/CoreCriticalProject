#pragma once
#include "effect_lighting.hpp"
#include "sun_lighting.hpp"
namespace mw34::effects {
struct Settings {bool enabled{},fixtures{true};unsigned limit{64},weapon_reserve{0};float strength{1},night_gain{1},fixture_range_scale{1};};
inline const Settings& settings(){
 static const Settings s=[] {
  Settings v;v.enabled=sun::flag("MW34_EFFECT_LIGHTS");
  const float limit=sun::parameter("MW34_EFFECT_LIGHT_LIMIT",64,1,capacity);
  if(limit!=std::floor(limit))throw std::runtime_error("Effect light limit must be an integer");
  v.limit=unsigned(limit);v.strength=sun::parameter("MW34_EFFECT_LIGHT_STRENGTH",1,0,8);
  v.fixtures=!std::getenv("MW34_FIXTURE_LIGHTS")||sun::flag("MW34_FIXTURE_LIGHTS");
  const float reserve=sun::parameter("MW34_WEAPON_LIGHT_RESERVE",0,0,capacity);
  if(reserve!=std::floor(reserve))throw std::runtime_error("Weapon reserve must be an integer");
  v.weapon_reserve=std::min(unsigned(reserve),v.limit);
  v.fixture_range_scale=sun::parameter("MW34_FIXTURE_LIGHT_RANGE_SCALE",1,.25f,4);
  v.night_gain=sun::parameter("MW34_NIGHT_WORLD_GAIN",1,0,1);
  if((v.enabled||v.night_gain!=1)&&!sun::settings().enabled)throw std::runtime_error("Effect/night lighting requires MW34_SUN=1");
  return v;
 }();return s;
}
}
