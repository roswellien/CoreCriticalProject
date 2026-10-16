"""Add bounded opt-in original TL/camera capture to a fresh fast-r2 snapshot."""
from pathlib import Path
import argparse
import shutil
from apply_world_direct import replace


def apply(host):
    shutil.copyfile(Path(__file__).parent/'native-overrides/divergence_trace_stage.inc',host/'divergence_trace_stage.inc')
    replace(host/'mfc_stage.hpp','#include "world_direct_stage.inc"',
            '#include "world_direct_stage.inc"\n#include "divergence_trace_stage.inc"')
    replace(host/'d3d_provider.inc','zoom_capture_command(c);world_capture(c);',
            'zoom_capture_command(c);divergence_trace(c);world_capture(c);')
    replace(host/'mfc_stage.hpp','h.live[at]=bytes;++h.allocs;if(zero)',
            'h.live[at]=bytes;++h.allocs;divergence_heap(1,at,bytes,zero);if(zero)')
    replace(host/'mfc_stage.hpp','h.live.erase(it);++h.frees;',
            'divergence_heap(2,at,it->second,0);h.live.erase(it);++h.frees;')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
