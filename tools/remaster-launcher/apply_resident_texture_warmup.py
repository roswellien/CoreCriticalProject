"""Add bounded size-prioritized resident texture preparation to the native host."""
from pathlib import Path
import argparse

def apply(host):
    helper=Path(__file__).parent/'native-overrides/surface_resident_texture_warmup.inc'
    provider=host/'d3d_provider.inc'
    source=provider.read_text()
    if '#include "surface_texture_warmup.inc"' not in source:
        raise RuntimeError('Install the existing world texture preparation first')
    replacements=[
        ('#include "surface_texture_warmup.inc"',
         '#include "surface_texture_warmup.inc"\n#include "surface_resident_texture_warmup.inc"'),
        ('effect_scene(sc);surface_texture_prewarm(sc);',
         'effect_scene(sc);surface_texture_prewarm(sc);surface_resident_texture_prewarm(sc);')]
    for before,after in replacements:
        if after in source:continue
        if source.count(before)!=1:raise RuntimeError(f'Unexpected resident texture preparation anchor: {before}')
        source=source.replace(before,after,1)
    # Resolve and validate all anchors before making any writes.
    data=helper.read_bytes()
    if provider.read_text()!=source:provider.write_text(source)
    destination=host/helper.name
    if not destination.exists() or destination.read_bytes()!=data:destination.write_bytes(data)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    apply(parser.parse_args().host)
