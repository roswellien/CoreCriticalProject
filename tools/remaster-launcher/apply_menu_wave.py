"""Preserve original rollover warps in the enhanced menu draw list.

The original VA 0x558DD0 writes pixels directly rather than issuing an image
blit. Record its parameters in draw order, retain its real execution, and warp
the enhanced pre-effect canvas using the original displacement field.
"""
from pathlib import Path
import argparse
import re
import shutil


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Menu wave anchor changed: ' + old[:100])
    return text.replace(old, new)


RECORD = r'''
void menu_dl_wave_record(){
 if(menu_dl_frame!=host.frames||menu_dl_bad||menu_dl.empty())return;
 if(load(0x72c1e4)!=menu_dl_target||load(0x72c1e8)!=640||load(0x72c1ec)!=480||load(0x72c1f0)!=1280||load(0x72c1f4)!=640){menu_dl_bad=true;return;}
 if(menu_dl.size()>4096||std::count_if(menu_dl.begin(),menu_dl.end(),[](const MenuBlit&b){return b.wave;})>=8){menu_dl_bad=true;return;}
 const unsigned sp=state.gpr.rsp.dword;if(!readable(sp,28)){menu_dl_bad=true;return;}
 mw34::menu::Wave w;w.x=int(state.gpr.rcx.dword);w.y=int(state.gpr.rdx.dword);w.inner=int(load(sp+4));w.outer=int(load(sp+8));w.amplitude=int(load(sp+12));
 const unsigned period=load(sp+16),phase=load(sp+20),rect=load(sp+24);std::memcpy(&w.period,&period,4);std::memcpy(&w.phase,&phase,4);
 if(rect){if(!readable(rect,16)){menu_dl_bad=true;return;}w.left=int(load(rect));w.top=int(load(rect+4));w.right=int(load(rect+8));w.bottom=int(load(rect+12));}
 mw34::vkscene::HostFpEnvironment fp;if(!w.valid()){menu_dl_bad=true;return;}
 MenuBlit b;b.wave=true;b.iw=640;b.ih=480;b.x=b.sx0=std::clamp(w.x-w.outer-1,0,640);b.y=b.sy0=std::clamp(w.y-w.outer-1,0,480);b.sw=std::clamp(w.x+w.outer+1,0,640)-b.x;b.sh=std::clamp(w.y+w.outer+1,0,480)-b.y;b.offsets=mw34::menu::wave_map(w);if(std::none_of(b.offsets.begin(),b.offsets.end(),[](const auto d){return d.x||d.y||d.raster;}))return;menu_dl.push_back(std::move(b));
}
void menu_dl_wave_finish(size_t index){
 if(menu_dl_frame!=host.frames||menu_dl_bad||index>=menu_dl.size()||!menu_dl[index].wave)return;
 auto&b=menu_dl[index];if(std::none_of(b.offsets.begin(),b.offsets.end(),[](const auto d){return d.raster;}))return;
 b.raster.resize(640*480);b.px.resize(640*480);for(unsigned i=0;i<640*480;++i)if(b.offsets[i].raster){std::uint16_t pixel{};get_bytes(menu_dl_target+2*i,&pixel,2);b.px[i]=pixel;b.raster[i]=hud_rgba(pixel,255);}
}
'''


def apply(host):
    vpath = host / 'vdd.inc'
    mpath = host / 'mfc_stage.hpp'
    v, m = vpath.read_text(), mpath.read_text()
    if 'void menu_dl_wave_record()' in v:
        raise ValueError('Menu wave already installed')
    start, end = v.index('struct MenuBlit{'), v.index('void present(const VSurface&v){')
    prefix, suffix, v = v[:start], v[end:], v[start:end]
    v = replace(v, 'bool bg{},text{},hires{};',
                'bool bg{},text{},hires{},wave{};std::vector<mw34::menu::Offset>offsets;std::vector<std::uint32_t>raster;')
    v = replace(v, 'bool menu_dl_present(const VSurface&v,const std::vector<unsigned char>&px){',
                RECORD + '\nbool menu_dl_present(const VSurface&v,const std::vector<unsigned char>&px){')
    v = replace(v, 'for(const auto&b:menu_dl)for(int r=0;r<b.sh;++r)',
                '''for(const auto&b:menu_dl){if(b.wave){const auto before=c;for(unsigned y=0;y<480;++y)for(unsigned x=0;x<640;++x){const auto d=b.offsets[y*640+x];const size_t to=(size_t(y)*640+x)*3,from=(size_t(int(y)+d.y)*640+unsigned(int(x)+d.x))*3;if(d.raster){const auto p=b.px[y*640+x];c[to]=float((p>>11)&31);c[to+1]=float((p>>5)&63);c[to+2]=float(p&31);}else for(int k=0;k<3;++k)c[to+k]=before[from+k];}continue;}for(int r=0;r<b.sh;++r)''')
    v = replace(v, 'd[k]=s[k]*t+d[k]*(1-t);}', 'd[k]=s[k]*t+d[k]*(1-t);}}')
    v = replace(v, 'std::vector<Src>srcs(menu_dl.size());',
                'std::vector<Src>srcs(menu_dl.size());std::vector<std::vector<std::uint32_t>>wave_pixels(menu_dl.size());')
    v = replace(v, 'auto rows=[&](unsigned y0,unsigned y1)',
                'size_t limit=menu_dl.size();unsigned clip_left=0,clip_right=ow;auto rows=[&](unsigned y0,unsigned y1)')
    v = replace(v, 'for(size_t n=0;n<menu_dl.size();++n){const auto&b=menu_dl[n];const double ly=',
                'for(size_t n=0;n<limit;++n){const auto&b=menu_dl[n];const double ly=')
    v = replace(v, 'const unsigned ox0=unsigned(std::max(0.0,std::ceil(b.x*fit-0.5))),ox1=std::min(ow,',
                'const unsigned ox0=std::max(clip_left,unsigned(std::max(0.0,std::ceil(b.x*fit-0.5)))),ox1=std::min(clip_right,')
    v = replace(v, 'for(unsigned ox=0;ox<ow;++ox){const float*d=',
                'for(unsigned ox=clip_left;ox<clip_right;++ox){const float*d=')
    v = replace(v,
                'const unsigned nt=std::max(1u,std::min(8u,std::thread::hardware_concurrency()));std::vector<std::thread>pool;\n for(unsigned t=0;t<nt;++t)pool.emplace_back(rows,oh*t/nt,oh*(t+1)/nt);for(auto&t:pool)t.join();',
                '''const unsigned nt=std::max(1u,std::min(8u,std::thread::hardware_concurrency()));
 auto render_prefix=[&](size_t count,unsigned left,unsigned top,unsigned right,unsigned bottom){limit=count;clip_left=left;clip_right=right;std::vector<std::thread>pool;for(unsigned t=0;t<nt;++t)pool.emplace_back(rows,top+(bottom-top)*t/nt,top+(bottom-top)*(t+1)/nt);for(auto&t:pool)t.join();};
 for(size_t n=0;n<menu_dl.size();++n)if(menu_dl[n].wave){const auto&b=menu_dl[n];int margin=2;for(const auto d:b.offsets)margin=std::max({margin,std::abs(d.x)+2,std::abs(d.y)+2});const unsigned left=unsigned(std::max(0.0,std::floor((b.x-margin)*fit))),top=unsigned(std::max(0.0,std::floor((b.y-margin)*fit))),right=std::min(ow,unsigned(std::max(0.0,std::ceil((b.x+b.sw+margin)*fit)))),bottom=std::min(oh,unsigned(std::max(0.0,std::ceil((b.y+b.sh+margin)*fit))));render_prefix(n,left,top,right,bottom);mw34::menu::warp_rgba(out,wave_pixels[n],ow,oh,b.offsets,&b.raster);srcs[n]={wave_pixels[n].data(),ow,oh,0.f,0.f,1.f,1.f};}
 render_prefix(menu_dl.size(),0,0,ow,oh);''')
    m = replace(m, '#include "vk_scene.hpp"', '#include "vk_scene.hpp"\n#include "menu_wave.hpp"')
    # Install into the outer chain for the Sun host, or main's lighting chain
    # when menu hooks have not yet been carried across the three-way merge.
    hook = '''  if(target==0x558dd0&&menu_hd_image().ok&&wide_world_frame!=host.frames){const size_t index=menu_dl.size();menu_dl_wave_record();try{void*r=remaster_body_inner(s,target,p,body);menu_dl_wave_finish(index);return r;}catch(...){menu_dl_bad=true;throw;}}\n'''
    anchor = '  if(target==0x55b3c0&&menu_hd_image().ok&&wide_world_frame!=host.frames)menu_dl_record();'
    if anchor in m:
        m = replace(m, anchor, hook + anchor)
    else:
        anchor = ' void*lighting_body(State*s,unsigned target,void*p,Body body){'
        m = replace(m, anchor, anchor + '\n' + hook +
                    '  if(target==0x55b3c0&&menu_hd_image().ok&&wide_world_frame!=host.frames)menu_dl_record();\n'
                    '  if(target==0x40a210){menu_bg_widget=state.gpr.rcx.dword;menu_bg_frame=host.frames;}')
        if 'MW34_MENU_SCROLL_HZ' not in m:
            from apply_menu_scroll_time import HOOK, TICKER
            m = replace(m, anchor, anchor + '\n' + HOOK + TICKER)
    # A previously generated dispatch bitmap must also admit the added hook.
    bitmap = re.compile(r'(for\(unsigned a:\{)([^}]+)(\}\)b\[\(a-0x400000\)>>6\])')
    matches = list(bitmap.finditer(m))
    if len(matches) > 1:
        raise ValueError('Multiple dispatch bitmaps')
    if matches:
        addresses = {int(a, 16) for a in matches[0][2].split(',')}
        addresses.add(0x558dd0)
        m = bitmap.sub(lambda match: match[1] + ','.join(hex(a) for a in sorted(addresses)) + match[3], m)
    # Main's conflict resolution preserves the photo/replay callback. Add menu
    # composition after it, without removing that service or its 3D path.
    v = prefix + v + suffix
    if 'shown=menu_dl_present(v,px)||' not in v:
        anchor = 'shown=host.presenter->present(host.display.window,px.data(),w,h,v.pitch,'
        v = replace(v, anchor, 'shown=menu_dl_present(v,px)||menu_hd_present(v,px)||host.presenter->present(host.display.window,px.data(),w,h,v.pitch,')
    shutil.copyfile(Path(__file__).resolve().parents[2] / 'runtime/graphics/menu_wave.hpp', host / 'menu_wave.hpp')
    vpath.write_text(v)
    mpath.write_text(m)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source)
