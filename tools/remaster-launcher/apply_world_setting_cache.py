"""Cache the process-fixed GPU-terrain flag used by world mesh admission.

Apply to the current native host. World scope, name matching, geometry,
original callbacks and legacy first-character flag semantics stay unchanged.
"""
from pathlib import Path
import argparse

BEFORE = ' const char*pt=std::getenv("MW34_GPU_TERRAIN");\n if(pt&&*pt==\'1\'){'
AFTER = ' static const bool gpu_terrain=[] {const char* value=std::getenv("MW34_GPU_TERRAIN");return value&&*value==\'1\';}();\n if(gpu_terrain){'


def apply(host):
    path = host / 'world_geometry_stage.inc'
    source = path.read_text()
    if source.count(AFTER) == 1:
        return
    if source.count(BEFORE) != 1:
        raise RuntimeError('Unexpected GPU-terrain admission setting anchor')
    path.write_text(source.replace(BEFORE, AFTER, 1))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
