#include "fixture_lighting.hpp"
#include <iostream>
#include <map>

int main() {
    using namespace mw34;
    unsigned checks = 0;
    auto check = [&](bool value) { ++checks; if (!value) throw std::runtime_error("Vehicle lighting regression"); };
    std::map<unsigned, vehicle_lighting::Node> nodes {
        {1, {"body", 2, 4}}, {2, {"healthy", 3, 4}}, {3, {"veh_apc", 0, 4}},
        {4, {"dbase", 5, 4}}, {5, {"destroyed", 3, 4}}, {6, {"streetlamp", 0, 4}}
    };
    auto read = [&](unsigned id)->std::optional<vehicle_lighting::Node> {
        auto it=nodes.find(id);return it==nodes.end()?std::nullopt:std::optional(it->second);
    };
    auto state=vehicle_lighting::inspect(1,read);
    check(state.vehicle==3 && state.healthy==2 && state.alive);
    nodes[2].flags |= 0x100; // A different flag must not invalidate lifetime.
    check(vehicle_lighting::inspect(1,read).alive);
    nodes[2].flags &= ~4U;
    check(!vehicle_lighting::inspect(1,read).alive);
    nodes[2].flags |= 4;
    check(!vehicle_lighting::inspect(4,read).alive);
    check(!vehicle_lighting::inspect(6,read).vehicle);
    nodes[3].flags=0;
    check(!vehicle_lighting::inspect(1,read).alive);
    nodes[3].flags=4;
    check(!vehicle_lighting::inspect(99,read).vehicle);
    nodes[3].name="veh_harasser";
    check(vehicle_lighting::inspect(1,read).alive);
    check(vehicle_lighting::headlamp("tredtruck09") && !vehicle_lighting::headlamp("mfglow01"));
    auto& manager=fixtures::FixtureManager::instance();manager.clear();manager.begin_frame(1,1);
    fixtures::FixtureDef def{"tredtruck09",16,16,1,1,14,1,{1,1,1},.15f,false,{{{0,0,1,1}}}};
    const auto& directional=manager.directional(def);
    check(directional.is_spot && !def.is_spot && &manager.directional(def)==&directional);
    using V=fixtures::FixtureManager::UvPoint;
    std::vector<V> front{{{-1,-1,0},0,0},{{1,-1,0},1,0},{{0,1,0},.5f,1}};
    fixtures::Point forward{0,0,1};
    manager.observe_regions(directional,front,1,123,&forward);
    auto lights=manager.select_lights({0,0,0},8);
    check(lights.size()==1 && lights[0].end[3]==float(effects::LightKind::spot) && lights[0].end[2]==1);
    manager.clear();manager.begin_frame(2,2);
    std::reverse(front.begin(),front.end());
    manager.observe_regions(manager.directional(def),front,2,124,&forward);
    check(manager.active_count()==0); // Back-facing regions are not headlights.
    std::reverse(front.begin(),front.end());
    for(auto& v:front){v.p[2]=v.p[0];v.p[0]=0;}
    manager.observe_regions(manager.directional(def),front,2,125,&forward);
    check(manager.active_count()==0); // Side body panels cannot shine forward.
    // A scenery point fixture retains its existing type and off-camera policy.
    manager.observe_polygon(def,{{-1,-1,0},{1,-1,0},{0,1,0}},2,200);
    manager.begin_frame(3,3);
    lights=manager.select_lights({0,0,0},8);
    check(lights.size()==1 && lights[0].end[3]==float(effects::LightKind::point));
    manager.remove_source(200);check(manager.active_count()==0);
    manager.clear();
    std::cout<<"Vehicle activation, headlamp direction and scenery regression checks="<<checks<<" failures=0\n";
}
