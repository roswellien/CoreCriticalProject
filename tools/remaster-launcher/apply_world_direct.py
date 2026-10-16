"""Add direct original-polygon binding to a fresh copy of the world r2 host."""
from pathlib import Path
import argparse
import shutil


def replace(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:
        raise RuntimeError(f'{path.name}: expected one contract: {old[:70]}')
    path.write_text(text.replace(old,new))


def apply(host):
    shutil.copyfile(Path(__file__).parent/'native-overrides/world_direct_stage.inc',host/'world_direct_stage.inc')
    shutil.copyfile(Path(__file__).parent/'native-overrides/world_binding.hpp',host/'world_binding.hpp')
    replace(host/'vk_scene.hpp','#include "geometry_profile.hpp"','#include "world_binding.hpp"\n#include "geometry_profile.hpp"')
    old=host/'world_geometry_stage.inc'
    replace(old,'unsigned material{},flags{};','unsigned material{},flags{},source{};')
    replace(old,'unsigned node{},mesh{};std::string name;std::vector<WorldPolygon> polygons;',
            'unsigned node{},mesh{},frame_base{},polygon_base{};std::string name;std::shared_ptr<std::vector<WorldPolygon>> polygons=std::make_shared<std::vector<WorldPolygon>>();std::shared_ptr<std::vector<int>> polygon_lookup;')
    replace(old,'world_begin(unsigned node)','world_decode_begin(unsigned node)')
    replace(old,'void world_capture(D3DCmd&draw)','void world_search_capture(D3DCmd&draw)')
    replace(old,'WorldPolygon polygon;polygon.material=', 'WorldPolygon polygon;polygon.source=poly;polygon.material=')
    replace(old,'result->polygons.push_back','result->polygons->push_back')
    replace(old,':world_scope->polygons)', ':*world_scope->polygons)')
    replace(old,'<<",\\\"cached\\\":"<<world_geometry.size()',
            '<<",\\\"mesh_hits\\\":"<<world_mesh_hits<<",\\\"mesh_misses\\\":"<<world_mesh_misses<<",\\\"scope_ticks\\\":"<<world_scope_ticks<<",\\\"binding_ticks\\\":"<<world_binding_ticks<<",\\\"cached\\\":"<<world_geometry.size()')
    stage=host/'mfc_stage.hpp'
    replace(stage,'#include "world_geometry_stage.inc"','#include "world_direct_stage.inc"')
    replace(stage,'world_begin(state.gpr.rcx.dword)', 'world_begin(state.gpr.rcx.dword,state.gpr.rsp.dword-4)')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
