"""Align the original status depth clears with their widescreen preview draws.

Only the two original HUD depth-fill producers are admitted. World clears,
preview geometry, camera framing, diagnostic colours and gameplay stay intact.
Pass a fresh private host-source directory; pinned builds are never edited.
"""
import argparse
from pathlib import Path
import shutil


def apply(host):
    pending = {}

    def edit(name, old, new):
        path = host / name
        source = pending.get(path, path.read_text(encoding='utf-8'))
        if source.count(new) == 1:
            return
        if source.count(old) != 1:
            raise ValueError(f'{name}: expected one status depth-clear anchor')
        pending[path] = source.replace(old, new, 1)

    edit('widescreen_stage.inc',
         '   case 0x444244:return WideZoom;',
         '   case 0x444244:return WideZoom;\n'
         '   // Original 43C6B0 clears depth before either status preview draws.\n'
         '   case 0x43c72a:return WideLeft;\n'
         '   case 0x43c748:return WideRight;')
    edit('vdd.inc', 'void*vdd_surface(',
         '#include "status_preview_clear_stage.inc"\nvoid*vdd_surface(')
    edit('vdd.inc', 'fill(*v,dst,load(fx+80)&0xffff);',
         'fill(*v,status_preview_depth_rect(dst,v->width,v->height),load(fx+80)&0xffff);')
    helper = Path(__file__).parent / 'native-overrides/status_preview_clear_stage.inc'
    for path, source in pending.items():
        path.write_text(source, encoding='utf-8', newline='\n')
    shutil.copyfile(helper, host / helper.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
