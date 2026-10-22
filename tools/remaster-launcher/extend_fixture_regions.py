"""Allow one texture's UV islands to use distinct light radii/colours.

Zero radius means masked glow without a physical light. Existing definitions
retain their original behaviour. Applies only to a private UV-capable host.
"""
from pathlib import Path
import argparse

def apply(path):
    source=path.read_text()
    if 'region_definitions_' in source:
        return
    def replace(old,new):
        nonlocal source
        if source.count(old)!=1:
            raise ValueError(f'Expected one extension marker in {path}: {old[:70]}')
        source=source.replace(old,new)
    replace('#include <vector>','#include <map>\n#include <vector>')
    replace('    bool emission_only{false};','    bool emission_only{false};\n    std::vector<float> emission_radii{};\n    std::vector<Point> emission_colors{};')
    replace('    std::vector<ActiveFixture> fixtures_;','    std::vector<ActiveFixture> fixtures_;\n    // std::map keeps active light-definition pointers stable as islands arrive.\n    std::map<std::pair<const FixtureDef*,size_t>,FixtureDef> region_definitions_;')
    replace('void clear(){fixtures_.clear();}','void clear(){fixtures_.clear();region_definitions_.clear();}')
    start=source.index('    void observe_regions(');end=source.index('    size_t active_count()',start)
    method=source[start:end]
    old='            const auto& rect=def.emission_regions[island];'
    assert method.count(old)==1
    new='''            const float radius=island<def.emission_radii.size()?def.emission_radii[island]:def.radius;
            if(radius<=0)continue; // Glow-only island: included in shader mask, no point light.
            const FixtureDef* light_def=&def;
            if(!def.emission_radii.empty()||!def.emission_colors.empty()){
                auto [it,inserted]=region_definitions_.try_emplace(std::make_pair(&def,island),def);
                if(inserted){it->second.radius=radius;if(island<def.emission_colors.size())it->second.color=def.emission_colors[island];}
                light_def=&it->second;
            }
            const auto& rect=def.emission_regions[island];'''
    method=method.replace(old,new).replace('old.def==&def','old.def==light_def').replace('&def,frame','light_def,frame')
    source=source[:start]+method+source[end:]
    path.write_text(source)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    args=parser.parse_args();apply(args.host/'fixture_lighting.hpp')
