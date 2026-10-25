"""Prepare already loaded immutable replacement geometry before first-use draws."""
from pathlib import Path
import argparse


def apply(host):
    path=host/'vk_scene.hpp';source=path.read_text(encoding='utf-8')
    member='    std::vector<std::shared_ptr<const ModelGeometry>> model_warmup;'
    if member not in source:
        anchor='    std::vector<Draw> draws;'
        if source.count(anchor)!=1: raise ValueError('Scene draw ownership changed')
        source=source.replace(anchor,anchor+'\n'+member,1)
        anchor='        // Textures: content-hashed cache keyed by guest surface; changed or new ones are uploaded.'
        if source.count(anchor)!=1: raise ValueError('Original model upload collection changed')
        addition='''        // Warmup shares the original immutable upload and completion path.
        // It adds no draw and retains exact geometry identity checks.
        for (const auto &geometry : s.model_warmup) {
            if (!gpu_models() || !geometry)
                throw std::runtime_error("Invalid immutable model warmup");
            auto &b = model_buffer(*geometry);
            if (!b.uploaded && std::find(model_pending.begin(), model_pending.end(), &b) == model_pending.end())
                model_pending.push_back(&b);
        }
'''
        source=source.replace(anchor,addition+anchor,1)
    elif 'for (const auto &geometry : s.model_warmup)' not in source:
        raise ValueError('Partial immutable model warmup')
    path.write_text(source,encoding='utf-8',newline='\n')
    path=host/'d3d_provider.inc';source=path.read_text(encoding='utf-8')
    anchor='surface_texture_prewarm(sc);surface_resident_texture_prewarm(sc);'
    replacement=anchor+'model_geometry_prewarm(sc);'
    if replacement not in source:
        if source.count(anchor)!=1: raise ValueError('Original world warmup route changed')
        source=source.replace(anchor,replacement,1)
    path.write_text(source,encoding='utf-8',newline='\n')
    path=host/'mesh_override_stage.inc';source=path.read_text(encoding='utf-8')
    include='#include "model_geometry_warmup.inc"'
    if include not in source: source=source.rstrip()+'\n\n'+include+'\n'
    path.write_text(source,encoding='utf-8',newline='\n')
    helper=Path(__file__).parent/'native-overrides/model_geometry_warmup.inc'
    (host/helper.name).write_bytes(helper.read_bytes())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
