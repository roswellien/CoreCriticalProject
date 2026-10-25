"""Let Vulkan clip captured TL shadow triangles before evaluating batch savings.

The TL shadow vertices are already world-space triangle-list vertices, with an
identity world matrix. Original model casters keep their CPU cube-face test.
The unchanged depth pipeline clips against all six Vulkan clip planes. This
option omits only a conservative host box test, never source validation or the
original game geometry/lighting routines. Evaluate it with existing batching.
"""
import argparse
from pathlib import Path


def apply(host):
    path = host / 'fixture_shadow_stage.inc'
    source = path.read_text()
    anchor = '        if(!fixtureTile||fixtureFrameCasters.empty())return;'
    replacement = '''        static const bool gpu_clip_tl=[] {
            const char* value=std::getenv("MW34_SHADOW_GPU_CLIP");
            if(!value||!*value||!std::strcmp(value,"0"))return false;
            if(!std::strcmp(value,"1"))return true;
            throw std::runtime_error("MW34_SHADOW_GPU_CLIP must be 0 or 1");
        }();
        if(!fixtureTile||fixtureFrameCasters.empty())return;'''
    begin = '                    bool outside=false;for(unsigned plane=0;plane<6;++plane)'
    end = '                    if(outside)continue;'
    if replacement in source:
        if source.count('if(!gpu_clip_tl||caster->geometry_key){') != 1:
            raise ValueError('Partial GPU shadow clipping patch')
        return
    if source.count(anchor) != 1 or source.count(begin) != 1 or source.count(end) != 1:
        raise ValueError('Fixture cube-face clipping source changed')
    start = source.index(begin)
    stop = source.index(end, start) + len(end)
    original = source[start:stop]
    source = source[:start] + '                    if(!gpu_clip_tl||caster->geometry_key){\n' + original + '\n                    }' + source[stop:]
    source = source.replace(anchor, replacement, 1)
    path.write_text(source)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
