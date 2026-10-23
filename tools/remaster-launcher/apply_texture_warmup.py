"""Prepare bounded resident world textures during the first native mission load.

Apply after the reviewed normal-page warmup adapter. Generated game translations
remain local; this installs only the authored renderer/provider adapter.
"""
from pathlib import Path
import argparse


def apply(host):
    helper = (Path(__file__).parent / 'native-overrides' / 'surface_texture_warmup.inc').read_bytes()
    normals = host / 'surface_normals_stage.inc'
    provider = host / 'd3d_provider.inc'
    text = normals.read_text()
    if 'std::getenv("MW34_NORMAL_PREWARM")' not in text or 'bool registered{}, world{};' not in text:
        raise RuntimeError('Install the reviewed normal-page warmup adapter first')
    planned = {}
    patches = {
        normals: [('struct SurfaceNormalState {\n    bool loaded{};',
                   'struct SurfaceNormalState {\n    bool loaded{}, gpu_prewarmed{};')],
        provider: [('void render_scene(D3DDev&d){',
                    '#include "surface_texture_warmup.inc"\nvoid render_scene(D3DDev&d){'),
                   (' distance_scene_log(sc);effect_scene(sc);',
                    ' distance_scene_log(sc);effect_scene(sc);surface_texture_prewarm(sc);')],
    }
    for path, replacements in patches.items():
        source = path.read_text()
        for before, after in replacements:
            if after in source:
                continue
            if source.count(before) != 1:
                raise RuntimeError(f'Unexpected texture preparation anchor in {path.name}: {before}')
            source = source.replace(before, after, 1)
        planned[path] = source
    for path, source in planned.items():
        if path.read_text() != source:
            path.write_text(source)
    destination = host / 'surface_texture_warmup.inc'
    if not destination.exists() or destination.read_bytes() != helper:
        destination.write_bytes(helper)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
