"""Move unlocked DirectDraw texture pixels out of the 32-bit guest arena.

Apply narrowly to a frozen native source tree, preserving newer rendering work.
"""
from pathlib import Path
import argparse
import shutil

OVERRIDES = Path(__file__).parent / 'native-overrides'


def apply(source):
    if '#include "texture_backing.hpp"' in (source / 'mfc_stage.hpp').read_text():
        raise RuntimeError('Host texture storage is already integrated; use an unmodified frozen source tree')
    def edit(name, replacements):
        path = source / name
        text = path.read_text()
        for old, new in replacements:
            if old not in text:
                raise RuntimeError(f'{name}: missing storage integration anchor: {old[:90]}')
            text = text.replace(old, new)
        path.write_text(text)

    edit('mfc_stage.hpp', [
        ('#include "surface_page_pool.hpp"', '#include "surface_page_pool.hpp"\n#include "texture_backing.hpp"'),
        ('mutable std::uint64_t version{};};', 'mutable std::uint64_t version{};mutable mw34::textures::Backing pixels;};'),
        ('if(a>=v.mem&&e<=std::uint64_t(v.mem)+v.bytes)', 'if(v.mem&&a>=v.mem&&e<=std::uint64_t(v.mem)+v.bytes)'),
    ])
    edit('vdd.inc', [
        ('!h.vsurfaces[it->second].mem?nullptr:', '!h.vsurfaces[it->second].bytes?nullptr:'),
        ('if(v.mem&&!v.locks&&!pinned.count(v.guest)){', 'if(v.bytes&&!v.locks&&!pinned.count(v.guest)){'),
        ('runtime.memory().unmap({v.mem});host.surface_free_pages.put(v.mem,unsigned(n));',
         'if(v.mem){runtime.memory().unmap({v.mem});host.surface_free_pages.put(v.mem,unsigned(n));}v.pixels.clear();'),
        ('const unsigned pitch=((w*bpp/8)+3U)&~3U,bytes=pitch*h;',
         'const auto row=(std::uint64_t(w)*bpp/8+3)&~std::uint64_t(3);const auto extent=row*h;\n if(!w||!h||!bpp||row>0xffffffffULL||extent>0xffffffffULL)deny("Surface dimensions overflow",w);const unsigned pitch=unsigned(row),bytes=unsigned(extent);'),
        ('caps,surface_pages(bytes),bytes,0,0,0});host.vsurfaces.back().version=',
         'caps,(caps&DDSCAPS_TEXTURE)?0:surface_pages(bytes),bytes,0,0,0});if(caps&DDSCAPS_TEXTURE)host.vsurfaces.back().pixels.resize(bytes);if(host.vsurfaces.size()%128==0)surface_collect_retired();host.vsurfaces.back().version='),
        ('const RECT r=surf_rect(rect,*v);DDSURFACEDESC2 d{};',
         'const RECT r=surf_rect(rect,*v);texture_lock_pages(*v);DDSURFACEDESC2 d{};'),
        ('--v->locks;v->version=++host.surface_versions;', '--v->locks;if(!v->locks)texture_unlock_pages(*v);v->version=++host.surface_versions;'),
        ('get_bytes(s.mem+unsigned(sr.top+y)*s.pitch+unsigned(sr.left)*b,', 'surface_read(s,unsigned(sr.top+y)*s.pitch+unsigned(sr.left)*b,'),
        ('const unsigned da=d.mem+unsigned(dr.top+y)*d.pitch+unsigned(dr.left)*b;if(key)get_bytes(da,', 'const unsigned da=unsigned(dr.top+y)*d.pitch+unsigned(dr.left)*b;if(key)surface_read(d,da,'),
        ('write_bytes(da,row.data(),unsigned(dw)*b);', 'surface_write(d,da,row.data(),unsigned(dw)*b);'),
        ('write_bytes(d.mem+unsigned(y)*d.pitch+unsigned(r.left)*b,', 'surface_write(d,unsigned(y)*d.pitch+unsigned(r.left)*b,'),
    ])
    path = source / 'vdd.inc'
    text = path.read_text()
    anchor = 'DDPIXELFORMAT surface_format('
    assert text.count(anchor) == 1
    helpers = '''// Service reads/writes see the live guest Lock view when present, otherwise host storage.
void surface_read(const VSurface& v,unsigned offset,void* out,unsigned bytes){
 if(std::uint64_t(offset)+bytes>v.bytes)deny("Surface read outside pixels",v.guest);
 if(v.mem)get_bytes(v.mem+offset,out,bytes);else v.pixels.read(offset,out,bytes);
}
void surface_write(const VSurface& v,unsigned offset,const void* in,unsigned bytes){
 if(std::uint64_t(offset)+bytes>v.bytes)deny("Surface write outside pixels",v.guest);
 if(v.mem)write_bytes(v.mem+offset,in,bytes);else v.pixels.write(offset,in,bytes);
}
unsigned surface_word(const VSurface& v,unsigned offset){unsigned word{};surface_read(v,offset,&word,4);return word;}
void texture_lock_pages(VSurface& v){
 if(v.pixels.empty()||v.mem)return;
 v.mem=surface_pages(v.bytes);
 std::vector<unsigned char> row(v.pitch);
 for(unsigned y=0;y<v.height;++y){v.pixels.read(size_t(y)*v.pitch,row.data(),v.pitch);write_bytes(v.mem+y*v.pitch,row.data(),v.pitch);}
}
void texture_unlock_pages(VSurface& v){
 if(v.pixels.empty()||!v.mem)return;
 std::vector<unsigned char> row(v.pitch);
 for(unsigned y=0;y<v.height;++y){get_bytes(v.mem+y*v.pitch,row.data(),v.pitch);v.pixels.write(size_t(y)*v.pitch,row.data(),v.pitch);}
 runtime.memory().unmap({v.mem});host.surface_free_pages.put(v.mem,unsigned((std::uint64_t(v.bytes)+4095)&~std::uint64_t(4095)));v.mem=0;
}
'''
    path.write_text(text.replace(anchor, helpers + anchor))
    # All provider consumers of texture pixels must use the same backing, including
    # normal/effect hashing, texture warmup, and renderer-specific material probes.
    for name in ['d3d_provider.inc','surface_normals_stage.inc','effect_lighting_stage.inc',
                 'world_effect_lighting_stage.inc','surface_texture_warmup.inc',
                 'surface_resident_texture_warmup.inc']:
        path = source / name
        if not path.exists():
            continue
        text = path.read_text()
        for obj in ['s','t','surface','v']:
            for access in ['.', '->']:
                prefix = obj + access + 'mem'
                text = text.replace('get_bytes('+prefix+'+', 'surface_read('+('*'+obj if access=='->' else obj)+',')
                text = text.replace('get_bytes('+prefix+',', 'surface_read('+('*'+obj if access=='->' else obj)+',0,')
                text = text.replace('get_bytes('+prefix+' + ', 'surface_read('+('*'+obj if access=='->' else obj)+',')
        text = text.replace('write_bytes(t->mem,', 'surface_write(*t,0,')
        if name == 'd3d_provider.inc':
            old = 'std::vector<unsigned char>b(s->bytes);surface_read(*s,0,b.data(),s->bytes);if(t->bytes!=s->bytes)deny("Texture Load with different pitches",arg(1));surface_write(*t,0,b.data(),unsigned(b.size()));'
            new = 'if(t->bytes!=s->bytes)deny("Texture Load with different pitches",arg(1));if(!s->mem&&!t->mem&&!s->pixels.empty()&&!t->pixels.empty())t->pixels=s->pixels;else{std::vector<unsigned char>b(s->bytes);surface_read(*s,0,b.data(),s->bytes);surface_write(*t,0,b.data(),unsigned(b.size()));}'
            if old not in text:
                raise RuntimeError('Texture Load copy anchor missing')
            text = text.replace(old,new)
        text = text.replace('!surface.mem', '!surface.bytes')
        for offset in [0,4]:
            for space in ['', ' ']:
                address = 't->mem' + (('+'+space+str(offset)) if offset else '')
                text = text.replace('load('+address+')', f'surface_word(*t,{offset})')
        for count in [4,8]:
            text = text.replace(f'readable(t->mem,{count})', f't->bytes>={count}')
            text = text.replace(f'readable(t->mem, {count})', f't->bytes>={count}')
        text = text.replace('readable(t->mem+4, 4)', 't->bytes>=8')
        # One multiline read has spaces around its address addition.
        text = text.replace('get_bytes(surface.mem + ', 'surface_read(surface,')
        path.write_text(text)
    if source.resolve() != OVERRIDES.resolve():
        shutil.copyfile(OVERRIDES / 'texture_backing.hpp', source / 'texture_backing.hpp')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source.resolve(strict=True))
