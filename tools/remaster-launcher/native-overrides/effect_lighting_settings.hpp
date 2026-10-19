#pragma once
#include "effect_lighting.hpp"
#include "sun_lighting.hpp"
namespace mw34::effects {
struct Settings {bool enabled{};unsigned limit{16};float strength{1},night_gain{1};};
inline const Settings& settings(){
 static const Settings s=[] {
  Settings v;v.enabled=sun::flag("MW34_EFFECT_LIGHTS");
  const float limit=sun::parameter("MW34_EFFECT_LIGHT_LIMIT",16,1,capacity);
  if(limit!=std::floor(limit))throw std::runtime_error("Effect light limit must be an integer");
  v.limit=unsigned(limit);v.strength=sun::parameter("MW34_EFFECT_LIGHT_STRENGTH",1,0,8);
  v.night_gain=sun::parameter("MW34_NIGHT_WORLD_GAIN",1,0,1);
  if((v.enabled||v.night_gain!=1)&&!sun::settings().enabled)throw std::runtime_error("Effect/night lighting requires MW34_SUN=1");
  return v;
 }();return s;
}
}
