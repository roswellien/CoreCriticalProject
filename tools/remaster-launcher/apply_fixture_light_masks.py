"""Reuse each prepared caster/light sphere result across its six shadow faces."""
import argparse
from pathlib import Path


def apply(host):
    replacements = {
        'vk_scene.hpp': [
            ('#include "draw_emissions.hpp"',
             '#include "draw_emissions.hpp"\n#include "fixture_light_masks.hpp"')],
        'fixture_shadow_stage.inc': [
            ('        std::function<bool()> valid;',
             '        std::function<bool()> valid;\n        std::uint64_t light_mask{};'),
            ('    mw34::effects::Uniform prepare_fixture_shadows(',
             '''    static bool fixture_light_masks_enabled() {
        static const bool enabled=[] {
            const char* value=std::getenv("MW34_FIXTURE_LIGHT_MASKS");
            if(!value||!*value||!std::strcmp(value,"0"))return false;
            if(!std::strcmp(value,"1"))return true;
            throw std::runtime_error("MW34_FIXTURE_LIGHT_MASKS must be 0 or 1");
        }();
        return enabled;
    }
    mw34::effects::Uniform prepare_fixture_shadows('''),
            ('        auto lights=scene.effect_lights;for(auto& meta:lights.shadow)meta={};fixtureFrameCasters.clear();',
             '        const bool reuse_masks=fixture_light_masks_enabled();\n        auto lights=scene.effect_lights;for(auto& meta:lights.shadow)meta={};fixtureFrameCasters.clear();'),
            ('''        for(auto& [key,caster]:fixtureCasters){bool relevant=false;
            for(unsigned i=weapons;i<count;++i)relevant|=caster.bounds.overlaps({lights.lights[i].start[0],lights.lights[i].start[1],lights.lights[i].start[2]},lights.lights[i].start[3]);''',
             '''        for(auto& [key,caster]:fixtureCasters){bool relevant=false;
            if(reuse_masks){caster.light_mask=mw34::submission::fixture_light_mask(caster.bounds,lights,weapons,count);relevant=caster.light_mask!=0;}
            else for(unsigned i=weapons;i<count;++i)relevant|=caster.bounds.overlaps({lights.lights[i].start[0],lights.lights[i].start[1],lights.lights[i].start[2]},lights.lights[i].start[3]);'''),
            ('        if(!fixtureTile||fixtureFrameCasters.empty())return;',
             '        const bool reuse_masks=fixture_light_masks_enabled();\n        if(!fixtureTile||fixtureFrameCasters.empty())return;'),
            ('for(const auto* caster:fixtureFrameCasters){if(!caster->bounds.overlaps({light.start[0],light.start[1],light.start[2]},light.start[3]))continue;',
             'for(const auto* caster:fixtureFrameCasters){if(reuse_masks?!(caster->light_mask&(std::uint64_t(1)<<i)):!caster->bounds.overlaps({light.start[0],light.start[1],light.start[2]},light.start[3]))continue;')]
    }
    pending = {}
    for name, edits in replacements.items():
        path = host / name
        source = path.read_text()
        for before, after in edits:
            if source.count(after) == 1:
                continue
            if source.count(before) != 1:
                raise ValueError(f'{name}: light mask anchor changed: {before[:70]}')
            source = source.replace(before, after, 1)
        pending[path] = source
    helper = Path(__file__).parent / 'native-overrides/fixture_light_masks.hpp'
    data = helper.read_bytes()
    for path, source in pending.items():
        if path.read_text() != source:
            path.write_text(source)
    destination = host / helper.name
    if not destination.exists() or destination.read_bytes() != data:
        destination.write_bytes(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
