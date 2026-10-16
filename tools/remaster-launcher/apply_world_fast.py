"""Remove repeated bridge projection/triangulation on a fresh direct-r2 copy."""
from pathlib import Path
import argparse
import shutil
from apply_world_direct import replace


def apply(host):
    shutil.copyfile(Path(__file__).parent/'native-overrides/world_fast_binding.hpp',host/'world_fast_binding.hpp')
    replace(host/'vk_scene.hpp','#include "world_binding.hpp"','#include "world_binding.hpp"\n#include "world_fast_binding.hpp"')
    replace(host/'world_geometry_stage.inc',
            'unsigned material{},flags{},source{};',
            'unsigned material{},flags{},source{};std::shared_ptr<const mw34::vkscene::ModelGeometry> resident;')
    stage=host/'world_direct_stage.inc'
    replace(stage,'std::uint64_t world_mesh_hits{},',
            '#include "world_fast_binding.hpp"\nstd::uint64_t world_fast_corners{},world_audited_corners{},world_geometry_builds{};\nstatic bool world_fast_enabled(){static const bool value=[]{const char*p=std::getenv("MW34_WORLD_FAST_BINDING");if(p&&std::strcmp(p,"0")&&std::strcmp(p,"1"))throw std::runtime_error("MW34_WORLD_FAST_BINDING must be 0 or 1");return p&&*p==\'1\';}();return value;}\nstd::uint64_t world_mesh_hits{},')
    # Build resident triangle lists once per decoded source revision. The exact
    # snapshot cache continues to guard changed data and reused addresses.
    text=stage.read_text()
    begin=text.index(' auto geometry=std::make_shared<mw34::vkscene::ModelGeometry>();')
    end=text.index(' auto instance=std::make_shared<mw34::vkscene::ModelInstance>();',begin)
    old=text[begin:end]
    helper=old.replace('matched[i]','polygon.corners[count-1-i].vertex').replace('matched[i+1]','polygon.corners[count-2-i].vertex').replace('matched[0]','polygon.corners[count-1].vertex')
    helper=helper.replace('scope.name','name').replace('draw.texture','0')
    helper+=' ++world_geometry_builds;return found->second;\n}\n'
    helper='std::shared_ptr<const mw34::vkscene::ModelGeometry> world_resident(const WorldPolygon& polygon,const std::string& name){const unsigned count=unsigned(polygon.corners.size());\n'+helper
    replace(stage,old,'')
    replace(stage,'mw34::world::SnapshotCache<WorldScope> world_meshes',helper+'mw34::world::SnapshotCache<WorldScope> world_meshes')
    replace(stage,'decoded->polygon_base=polygons;',
            'for(auto& polygon:*decoded->polygons)polygon.resident=world_resident(polygon,name);\n  decoded->polygon_base=polygons;')
    replace(stage,'instance->geometry=found->second;', 'instance->geometry=polygon.resident;')
    replace(stage,' std::vector<mw34::vkscene::ModelVertex> matched;matched.reserve(count);',
            ' const bool fast=world_fast_enabled()&&load(frame-0x44)==polygon.material&&readable(polygon.material,4)&&(load(polygon.material)&0x100)&&mw34::world::unchanged_polygon(load(frame-0x74),polygon.flags,load(address+4),load(0x7489a8),load(frame-0x54));')
    replace(stage,'  const double z=matrix[8]*v.x',
            '  if(!std::isfinite(tl.u)||!std::isfinite(tl.v)||std::abs(v.u-tl.u)>1e-5||std::abs(v.v-tl.v)>1e-5){++world_misses;return;}\n  if(fast){++world_fast_corners;continue;}++world_audited_corners;\n  const double z=matrix[8]*v.x')
    replace(stage,'  matched.push_back(v);','')
    replace(host/'world_geometry_stage.inc','<<",\\\"mesh_hits\\\":"<<world_mesh_hits',
            '<<",\\\"fast_corners\\\":"<<world_fast_corners<<",\\\"audited_corners\\\":"<<world_audited_corners<<",\\\"geometry_builds\\\":"<<world_geometry_builds<<",\\\"mesh_hits\\\":"<<world_mesh_hits')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
