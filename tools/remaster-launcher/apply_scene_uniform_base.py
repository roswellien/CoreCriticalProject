"""Reuse the scene-wide portion of sun uniforms, preserving all draw overrides.

The pinned base function uses Settings for every field except its copied normal
matrix. Scene Settings are immutable here. Normal checks, effects, projections,
shadows, uploads, exact draw identities and ordering remain in the original loop.
"""
import argparse,hashlib,json
from pathlib import Path

CONTRACTS = {
    'vk_scene.hpp': 'cdcdb0a81cc4d0221a84aefdfecaf5d5c61fb9190b3eeac7f579f725e1101522',
    'sun_lighting.hpp': 'b1ac9f4eb3d267fabd038ded2a6be4b56d7cbbbb96b82cc4d8f10bd0b2b46c6e',
}

def apply(host):
    for name, expected in CONTRACTS.items():
        if hashlib.sha256((host/name).read_bytes()).hexdigest() != expected:
            raise ValueError(name + ': scene uniform dependencies changed; review required')
    path=host/'vk_scene.hpp';destination=host/'scene_uniform_base.hpp'
    if destination.exists():raise ValueError('Scene base reuse already applied')
    text=path.read_text(encoding='utf-8')
    def replace(old,new):
        nonlocal text
        if text.count(old)!=1:raise ValueError('Scene base anchor changed: '+old)
        text=text.replace(old,new)
    replace('#include "exact_uniform_runs.hpp"','#include "exact_uniform_runs.hpp"\n#include "scene_uniform_base.hpp"')
    replace('        bool sunScene = false;', '''        mw34::submission::SceneUniformBase<mw34::sun::Uniform> uniformBase(
            mw34::submission::scene_uniform_base_enabled());
        bool sunScene = false;''')
    replace('u = mw34::sun::uniform(instance.sun_normal, environment);',
            'u = uniformBase.capture(instance.sun_normal, [&] { return mw34::sun::uniform(instance.sun_normal, environment); });')
    replace('u = mw34::sun::uniform(light.camera_world, environment);',
            'u = uniformBase.capture(light.camera_world, [&] { return mw34::sun::uniform(light.camera_world, environment); });')
    replace('        // Descriptor sets: one per distinct (texture, sampler).', '''        uniform_base_builds += uniformBase.builds;
        uniform_base_hits += uniformBase.hits;
        // Descriptor sets: one per distinct (texture, sampler).''')
    replace('    std::uint64_t fxaa_passes{}, af_samplers{}, mip_levels_uploaded{};',
            '    std::uint64_t fxaa_passes{}, af_samplers{}, mip_levels_uploaded{};\n    std::uint64_t uniform_base_builds{}, uniform_base_hits{};')
    replace('        model_buffers.clear();', '''        model_buffers.clear();
        if (uniform_base_builds) std::fprintf(stderr,
            "Scene lighting base: %llu builds, %llu reused\\n",
            (unsigned long long)uniform_base_builds, (unsigned long long)uniform_base_hits);''')
    helper=(Path(__file__).parent/'native-overrides/scene_uniform_base.hpp').read_bytes()
    path.write_text(text,encoding='utf-8');destination.write_bytes(helper)
    return dict(parent_contracts=CONTRACTS,helper_sha256=hashlib.sha256(helper).hexdigest())

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host_source',type=Path)
    print(json.dumps(apply(parser.parse_args().host_source.resolve(strict=True)),indent=2))
