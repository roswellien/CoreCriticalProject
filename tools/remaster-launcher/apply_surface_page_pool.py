"""Install pressure-driven reclamation of released virtual surface pixel pages."""
from pathlib import Path
import argparse
import shutil

OVERRIDES = Path(__file__).parent / 'native-overrides'


def apply(source: Path):
    path = source / 'mfc_stage.hpp'
    text = path.read_text()
    include = '#include "surface_page_pool.hpp"'
    if include not in text:
        anchor = '#include "vk_scene.hpp"'
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one renderer include')
        text = text.replace(anchor, anchor + '\n' + include, 1)
    field = 'mw34::surface_pages::FreeList surface_free_pages;'
    if field not in text:
        anchor = 'unsigned vsurface_next{};'
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one surface allocator cursor')
        text = text.replace(anchor, anchor + field, 1)
    path.write_text(text)
    path = source / 'vdd.inc'
    text = path.read_text()
    template = (OVERRIDES / 'vdd.inc').read_text()
    start, end = 'VSurface*vsurface(', 'unsigned make_surface('
    if any(x.count(start) != 1 or x.count(end) != 1 for x in (text, template)):
        raise RuntimeError('Expected one virtual surface allocation block')
    a, b = text.index(start), text.index(end)
    c, d = template.index(start), template.index(end)
    block = template[c:d]
    # This prerequisite also supports older frozen hosts. Install the host
    # texture storage change separately, after this guest-page pool migration.
    if 'texture_backing.hpp' not in (source / 'mfc_stage.hpp').read_text():
        block = block.replace('!h.vsurfaces[it->second].bytes?nullptr:', '!h.vsurfaces[it->second].mem?nullptr:')
        block = block.replace('if(v.bytes&&!v.locks&&!pinned.count(v.guest)){', 'if(v.mem&&!v.locks&&!pinned.count(v.guest)){')
        block = block.replace('if(v.mem){runtime.memory().unmap({v.mem});host.surface_free_pages.put(v.mem,unsigned(n));}v.pixels.clear();',
                              'runtime.memory().unmap({v.mem});host.surface_free_pages.put(v.mem,unsigned(n));')
    path.write_text(text[:a] + block + text[b:])
    shutil.copyfile(OVERRIDES / 'surface_page_pool.hpp', source / 'surface_page_pool.hpp')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source.resolve(strict=True))
