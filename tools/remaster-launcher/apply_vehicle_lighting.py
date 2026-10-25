"""Bind vehicle fixture lifetime to original activation and aim headlamps forward."""
from pathlib import Path
import argparse
import shutil


def apply(host):
    helper = Path(__file__).with_name('native-overrides') / 'vehicle_lighting.hpp'
    shutil.copy2(helper, host / helper.name)
    p = host / 'fixture_lighting.hpp'
    s = p.read_text()
    if '#include "vehicle_lighting.hpp"' in s:
        raise RuntimeError('Vehicle lighting already applied; use a fresh source snapshot')
    s = s.replace('#include "effect_lighting.hpp"', '#include "effect_lighting.hpp"\n#include "vehicle_lighting.hpp"', 1)
    marker = '    unsigned frame_{};double time_{};'
    if s.count(marker) != 1:
        raise RuntimeError('Unexpected fixture manager layout')
    s = s.replace(marker, '    std::map<const FixtureDef*,FixtureDef> directional_definitions_;\n' + marker)
    s = s.replace('void clear(){fixtures_.clear();region_definitions_.clear();}',
                  'void clear(){fixtures_.clear();region_definitions_.clear();directional_definitions_.clear();}')
    marker = '    void remove_source('
    at = s.index(marker)
    s = s[:at] + '''    const FixtureDef& directional(const FixtureDef& def){
        auto [it,added]=directional_definitions_.try_emplace(&def,def);
        it->second.is_spot=true;return it->second;
    }
''' + s[at:]
    old = 'unsigned frame,std::uint64_t owner){'
    if s.count(old) != 1:
        raise RuntimeError('Unexpected fixture UV observer')
    s = s.replace(old, 'unsigned frame,std::uint64_t owner,const Point* forward=nullptr){')
    old = 'for(unsigned j=0;j<3;++j){normal[j]/=length;position[j]+=normal[j]*def.normal_offset;}'
    if s.count(old) != 1:
        raise RuntimeError('Unexpected fixture region normal')
    s = s.replace(old, old + '''
            if(forward){float facing=0;for(unsigned j=0;j<3;++j)facing+=normal[j]*(*forward)[j];
                if(facing<.5f)continue;normal=*forward;}
''')
    p.write_text(s)
    p = host / 'effect_lighting_stage.inc'
    s = p.read_text()
    s = s.replace('unsigned surface{};std::uint64_t version{};',
                  'unsigned surface{};std::uint64_t version{};unsigned vehicle{},healthy{};', 1)
    marker = 'bool fixture_proof_valid(const FixtureSourceProof& proof){'
    s = s.replace(marker, '''mw34::vehicle_lighting::State fixture_vehicle(unsigned node){
 return mw34::vehicle_lighting::inspect(node,[&](unsigned at)->std::optional<mw34::vehicle_lighting::Node>{
  if(!readable(at,100))return std::nullopt;
  return mw34::vehicle_lighting::Node{pose_name(at,36),override_parent(at),load(at+0x24)};
 });
}
''' + marker + '''
 if(proof.vehicle){if(!readable(proof.vehicle+0x24,4)||!readable(proof.healthy+0x24,4)||
   !(load(proof.vehicle+0x24)&4)||!(load(proof.healthy+0x24)&4))return false;}
''', 1)
    old = 'FixtureSourceProof proof;if(!fixture_capture_proof(draw,surface,proof))return 0;'
    if s.count(old) != 1:
        raise RuntimeError('Unexpected light source proof')
    s = s.replace(old, old + '''
 const auto vehicle=fixture_vehicle(draw.fixture_node);
 if(vehicle.vehicle){if(!vehicle.alive)return 0;proof.vehicle=vehicle.vehicle;proof.healthy=vehicle.healthy;}
''')
    # This observer uses the original model-space polygon and winding, so its
    # front-facing normal and the vehicle's -Z axis share a proven world basis.
    old = 'if(fixture_original_polygon(draw,identity,original)){\n   const auto source=fixture_source(identity,*surface);'
    new = '''if(fixture_original_polygon(draw,identity,original)){
   const auto vehicle=fixture_vehicle(identity.fixture_node);
   if(vehicle.vehicle&&!vehicle.alive)return;
   mw34::fixtures::Point forward{};const mw34::fixtures::Point* direction=nullptr;
   if(vehicle.vehicle&&mw34::vehicle_lighting::headlamp(fixture->name)){
    OverrideMatrix view;if(!sun_camera_world(view))return;
    const auto world=override_product(view,override_matrix(load(load(0x5eda90))));
    forward={float(-world[2]),float(-world[6]),float(-world[10])};
    const float length=std::sqrt(mw34::effects::distance2(forward,{0,0,0}));
    if(!(length>1e-6f))return;for(float&v:forward)v/=length;
    fixture=&manager.directional(*fixture);direction=&forward;
   }
   const auto source=fixture_source(identity,*surface);'''
    if s.count(old) != 1:
        raise RuntimeError('Unexpected original fixture polygon observer')
    s = s.replace(old, new)
    s = s.replace('manager.observe_regions(*fixture,triangles,host.frames,source);',
                  'manager.observe_regions(*fixture,triangles,host.frames,source,direction);', 1)
    old = '  const auto source=fixture_source(draw,*surface);'
    if s.count(old) != 1:
        raise RuntimeError('Unexpected fixture fallback observer')
    s = s.replace(old, '''  // Vehicle sources require proven original geometry/lifetime, never retained anonymous observations.
  if(fixture_vehicle(draw.fixture_node?draw.fixture_node:fixture_mesh_node).vehicle)return;
''' + old)
    p.write_text(s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
