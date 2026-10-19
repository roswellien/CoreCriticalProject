"""Diagnostic: log the front end's 2D primitive calls (MW34_MENU_DRAW_LOG=<file>, MW34_MENU_DRAW_LOG_FRAMES=<a-b>).

For frames without a 3D scene, each call to the original raster primitives
(image blit 0x55B3C0, lines 0x563B80/0x563DB0, pixel 0x5630A0/0x5641F0,
circle 0x5630C0, span 0x564080) and the text image builders (0x577BA0 clear,
0x577BD0 copy) is logged with the global 2D target (0x8007C8) and arguments.
Image blits also log the image size, flags, mask/alt planes, source rectangle and
the hi-res identity key. The original calls still run. Apply after apply_menu_hd.py.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one draw-log anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

HOOK = r'''  {static FILE*mdl=[]{const char*p=std::getenv("MW34_MENU_DRAW_LOG");return p&&*p?std::fopen(p,"w"):nullptr;}();
   static const std::pair<unsigned,unsigned> range=[]{const char*p=std::getenv("MW34_MENU_DRAW_LOG_FRAMES");unsigned a=0,b=0;if(p)std::sscanf(p,"%u-%u",&a,&b);return std::make_pair(a,b);}();
   if(mdl&&host.frames>=range.first&&host.frames<=range.second&&wide_world_frame!=host.frames&&
      (target==0x55b3c0||target==0x563b80||target==0x563db0||target==0x5630a0||target==0x5641f0||target==0x5630c0||target==0x564080||target==0x577ba0||target==0x577bd0)){
    const unsigned sp=state.gpr.rsp.dword,ecx=state.gpr.rcx.dword,edx=state.gpr.rdx.dword;
    std::fprintf(mdl,"%u %06x tgt %08x ret %06x ecx %08x edx %08x a %08x %08x %08x %08x",host.frames,target,load(0x8007c8),load(sp),ecx,edx,load(sp+4),load(sp+8),load(sp+12),load(sp+16));
    if(target==0x55b3c0&&readable(ecx,0x38)){const int w=std::int16_t(load(ecx+4)&0xffff),h=std::int16_t(load(ecx+6)&0xffff);const unsigned flags=(load(ecx+8)>>8)&0xff,pix=load(ecx+0x10),mask=load(ecx+0x14),alt=load(ecx+0x18),pitch=load(ecx+0x34),key=load(sp+8)&0xffff,src=load(sp+12);
     std::fprintf(mdl," img %dx%d flags %02x pix %08x mask %08x alt %08x pitch %u",w,h,flags,pix,mask,alt,pitch);
     if(src&&readable(src,16))std::fprintf(mdl," src [%d %d %d %d]",int(load(src)),int(load(src+4)),int(load(src+8)),int(load(src+12)));
     if(!alt&&w>0&&h>0&&std::int64_t(w)*h<=262144){const unsigned mode=mask?2U:(flags&2)?1U:0U;std::fprintf(mdl," id %016llx",(unsigned long long)hud_identity(pix,mask,mode,key,w,h,pitch));}
     if(text_images.count(ecx))std::fprintf(mdl," TEXT \"%s\"",text_images[ecx].recipes.empty()?"":text_images[ecx].recipes[0].text.c_str());}
    std::fprintf(mdl,"\n");std::fflush(mdl);}}
'''

def apply(host):
    m=host/'mfc_stage.hpp'
    edit(m,'  if(target==0x40a210){menu_bg_widget=state.gpr.rcx.dword;menu_bg_frame=host.frames;}',HOOK+'  if(target==0x40a210){menu_bg_widget=state.gpr.rcx.dword;menu_bg_frame=host.frames;}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
