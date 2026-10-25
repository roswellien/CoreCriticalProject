"""Reuse temporary captured vertex storage after ownership leaves the input draw."""
from pathlib import Path
import argparse
import hashlib


def apply(host):
    stage=host/'d3d_provider.inc'
    source=stage.read_text(encoding='utf-8')
    helper=Path(__file__).parent/'native-overrides/early_triangle_commands.hpp'
    old_helper=(host/helper.name).read_text(encoding='utf-8')
    if old_helper!=helper.read_text(encoding='utf-8') and hashlib.sha256(old_helper.encode()).hexdigest()!='b6fec62c983b25f794497f01d0e341115e0fa33e107190caf6e7d22352172065':
        raise ValueError('Unknown early-triangle helper; merge before applying')
    if 'mw34::submission::DrawVertexScratch draw_vertex_scratch;' in source:
        if ('draw_vertex_scratch.recycle(c.vertices)' not in source or
                'draw_vertex_scratch.prepare(c.vertices,32*size_t(vcount))' not in source or
                'draw_vertex_reuse_enabled' in source or old_helper != helper.read_text(encoding='utf-8')):
            raise ValueError('Partial draw vertex scratch adapter')
        return
    if '#include "early_triangle_commands.hpp"' not in (host/'mfc_stage.hpp').read_text(encoding='utf-8'):
        raise ValueError('Early triangle command header required')
    old='// D3DDEVICEDESC (DX6, 252 bytes): DWORD/float fields only, identical x86/x64 layout.'
    if source.count(old)!=1: raise ValueError('Native stage ownership anchor changed')
    source=source.replace(old,'mw34::submission::DrawVertexScratch draw_vertex_scratch;\n\n'+old,1)
    old='c.vertices.resize(32*size_t(vcount));get_bytes(verts,c.vertices.data(),32*vcount);'
    if source.count(old)!=1: raise ValueError('Original complete vertex copy changed')
    source=source.replace(old,'draw_vertex_scratch.prepare(c.vertices,32*size_t(vcount));get_bytes(verts,c.vertices.data(),32*vcount);',1)
    old='   }return done(DD_OK,n=="DrawPrimitive"?6:8);}'
    if source.count(old)!=1: raise ValueError('Original capture return route changed')
    source=source.replace(old,'   }draw_vertex_scratch.recycle(c.vertices);return done(DD_OK,n=="DrawPrimitive"?6:8);}',1)
    stage.write_text(source,encoding='utf-8',newline='\n')
    (host/helper.name).write_bytes(helper.read_bytes())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
