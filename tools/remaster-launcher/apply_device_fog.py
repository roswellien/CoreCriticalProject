"""Add an opt-in original main-device fog-cache lifetime repair."""
from pathlib import Path
import argparse
import shutil
from apply_world_direct import replace


def apply(host: Path):
    source = Path(__file__).parent / 'native-overrides/device_fog_stage.inc'
    shutil.copyfile(source, host / source.name)
    replace(host / 'mfc_stage.hpp', '#include "d3d_provider.inc"',
            '#include "device_fog_stage.inc"\n#include "d3d_provider.inc"')
    replace(host / 'd3d_provider.inc', 'host.devices.push_back(d);store(out,g);',
            'host.devices.push_back(d);store(out,g);device_fog_created(out,d.rs[D3DRENDERSTATE_FOGENABLE]);')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
