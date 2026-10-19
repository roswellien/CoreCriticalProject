"""High-resolution front-end background: composite the menu at display resolution.

The original front end composes each menu screen in a 640x480 16-bit frame:
a scrolling background widget (0x40A210, vtable 0x5BC1B0) copies its 1280x960
image at the widget's scroll offset (+0xE8/+0xEC, wrapped) to the frame at
(0,0), then the menu draws text, buttons, glows and translucent overlays.

MW34_MENU_HD_BG=<file.mwhd> (raw RGB, here 5760x4320 = 4.5x the 1280x960
original) enables a host compositor for frames without a 3D scene:
  * expected background = the original image at the active widget's offset;
  * per guest pixel, tint gain = sum(frame)/sum(expected) over a 5x5 window of
    pixels whose colour is a consistent scaling of the background (untouched
    pixels give gain 1, translucent darkening/tinting overlays their factor);
  * output at the window's 4:3 fit (capped at 2880x2160): background-derived
    pixels = bilinear HD sample x bilinear gain; other pixels (opaque UI) keep
    the game's pixel (nearest).
The result is presented as 32-bit colour 1:1. Game code, timing and the 640x480
frame are unchanged; any mismatch (other image, no active widget) falls back to
the original 16-bit presentation. Apply after apply_menu_scroll_time.py.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one menu-HD anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

COMPOSITOR = r'''
struct MenuHdImage{std::vector<unsigned char>rgb;unsigned w{},h{},sw{},sh{};bool ok{};};
const MenuHdImage& menu_hd_image(){static const MenuHdImage image=[]{MenuHdImage m;const char*p=std::getenv("MW34_MENU_HD_BG");if(!p||!*p)return m;
  std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("Menu HD background unavailable");char magic[8];unsigned hdr[4];
  if(!f.read(magic,8)||std::memcmp(magic,"MWHDBG1\0",8)||!f.read(reinterpret_cast<char*>(hdr),16))throw std::runtime_error("Menu HD background format");
  m.w=hdr[0];m.h=hdr[1];m.sw=hdr[2];m.sh=hdr[3];if(!m.w||!m.h||!m.sw||!m.sh||m.w>16384||m.h>16384)throw std::runtime_error("Menu HD background size");
  m.rgb.resize(size_t(m.w)*m.h*3);if(!f.read(reinterpret_cast<char*>(m.rgb.data()),std::streamsize(m.rgb.size())))throw std::runtime_error("Menu HD background truncated");
  m.ok=true;std::fprintf(stderr,"Menu HD background: %ux%u for %ux%u source\n",m.w,m.h,m.sw,m.sh);return m;}();return image;}
unsigned menu_bg_widget{},menu_bg_frame{~0u};std::uint64_t menu_hd_frames{};
bool menu_hd_present(const VSurface&v,const std::vector<unsigned char>&px){
 const auto&hd=menu_hd_image();
 if(!hd.ok||v.bpp!=16||v.width!=640||v.height!=480||px.size()<size_t(v.pitch)*480||wide_world_frame==host.frames)return false;
 if(menu_bg_frame==~0u||host.frames-menu_bg_frame>2)return false;
 const unsigned wg=menu_bg_widget;if(!wg||!readable(wg,0x140))return false;
 const unsigned img=load(wg+0x3c);if(!img||!readable(img,0x14))return false;
 const unsigned dims=load(img+4),iw=dims&0xffff,ih=dims>>16;if(iw!=hd.sw||ih!=hd.sh)return false;
 const unsigned pix=load(img+0x10);if(!readable(pix,iw*ih*2))return false;
 static std::vector<std::uint16_t>bg;static unsigned bg_ptr{};static std::uint64_t bg_sum{};
 {std::uint64_t sum=0;for(unsigned i=0;i<256;++i){const unsigned at=pix+((i*2654435761u)%(iw*ih))*2;sum=sum*31+(load(at&~3u)>>((at&2)*8)&0xffff);}
  if(bg_ptr!=pix||bg_sum!=sum||bg.size()!=size_t(iw)*ih){bg.resize(size_t(iw)*ih);get_bytes(pix,reinterpret_cast<unsigned char*>(bg.data()),unsigned(bg.size()*2));bg_ptr=pix;bg_sum=sum;}}
 int rx=int(load(wg+0xe8)),ry=int(load(wg+0xec));
 {// The widget may already have stepped for the next frame: pick the offset (current or up to 4 steps back
  // along its velocity) that best explains this frame's pixels.
  const int vx=int(load(wg+0xbc)),vy=int(load(wg+0xc0));const std::uint16_t*fr=reinterpret_cast<const std::uint16_t*>(px.data());const unsigned pitch16=v.pitch/2;
  int best=-1,bx=rx,by=ry;
  for(int k=0;k<=4;++k){const int cx=rx-k*vx,cy=ry-k*vy;int hits=0;
   for(unsigned y=3;y<480;y+=8)for(unsigned x=3;x<640;x+=8)hits+=fr[y*pitch16+x]==bg[size_t(unsigned((cy+int(y))%int(ih)+int(ih))%ih)*iw+unsigned(((cx+int(x))%int(iw)+int(iw))%iw)];
   if(hits>best){best=hits;bx=cx;by=cy;}if(!vx&&!vy)break;}
  rx=((bx%int(iw))+int(iw))%int(iw);ry=((by%int(ih))+int(ih))%int(ih);}
 RECT rc{};::GetClientRect(host.display.window,&rc);if(rc.right<=0||rc.bottom<=0)return false;
 const double fit=std::min({double(rc.right)/640.0,double(rc.bottom)/480.0,2880.0/640.0});
 const unsigned ow=unsigned(std::lround(640*fit)),oh=unsigned(std::lround(480*fit));if(ow<640||oh<480)return false;
 mw34::vkscene::HostFpEnvironment fp;
 auto ch=[](std::uint16_t p,int c){return c==0?float((p>>11)&31)*(255.f/31):c==1?float((p>>5)&63)*(255.f/63):float(p&31)*(255.f/31);};
 const std::uint16_t*frame=reinterpret_cast<const std::uint16_t*>(px.data());const unsigned fp_=v.pitch/2;
 // Per guest pixel: candidate background (consistent tint of the expected pixel) and 5x5 windowed gains.
 static std::vector<float>g(640*480*3),e(640*480*3);static std::vector<unsigned char>cand(640*480);static std::vector<float>gain(640*480*3),add(640*480*3);
 for(unsigned y=0;y<480;++y)for(unsigned x=0;x<640;++x){const std::uint16_t f=frame[y*fp_+x];
  const std::uint16_t b=bg[size_t((unsigned(ry+int(y))%ih))*iw+(unsigned(rx+int(x))%iw)];const size_t i=size_t(y)*640+x;
  float r[3];bool ok=true;for(int c=0;c<3;++c){const float fv=ch(f,c),ev=ch(b,c);g[i*3+c]=fv;e[i*3+c]=ev;r[c]=(fv+8.f)/(ev+8.f);}
  if(f!=b){const float mn=std::min({r[0],r[1],r[2]}),mx=std::max({r[0],r[1],r[2]});ok=mn>0.12f&&mx<2.5f&&mx<=mn*1.45f;}
  // Additive green glow over the background: keep the glow as added light over the HD background.
  if(!ok){const float dr=g[i*3]-e[i*3],dg=g[i*3+1]-e[i*3+1],db=g[i*3+2]-e[i*3+2];
   if(dg>6.f&&dr>-10.f&&db>-10.f&&dr<dg*0.6f&&db<dg*0.6f){cand[i]=2;add[i*3]=dr;add[i*3+1]=dg;add[i*3+2]=db;continue;}}
  cand[i]=ok?1:0;}
 for(unsigned y=0;y<480;++y)for(unsigned x=0;x<640;++x){const size_t i=size_t(y)*640+x;if(cand[i]!=1)continue;
  float sg[3]{},se[3]{};for(int dy=-2;dy<=2;++dy){const int yy=int(y)+dy;if(yy<0||yy>=480)continue;for(int dx=-2;dx<=2;++dx){const int xx=int(x)+dx;if(xx<0||xx>=640)continue;
   const size_t j=size_t(yy)*640+xx;if(cand[j]!=1)continue;for(int c=0;c<3;++c){sg[c]+=g[j*3+c];se[c]+=e[j*3+c];}}}
  for(int c=0;c<3;++c)gain[i*3+c]=(sg[c]+4.f)/(se[c]+4.f);}
 static std::vector<std::uint32_t>out;out.assign(size_t(ow)*oh,0);
 const double S=double(hd.w)/double(hd.sw);const unsigned hw=hd.w,hh=hd.h;const unsigned char*H=hd.rgb.data();
 auto rows=[&](unsigned y0,unsigned y1){mw34::vkscene::HostFpEnvironment fpw;
  for(unsigned oy=y0;oy<y1;++oy){const double gy=(oy+0.5)/fit;const unsigned ny=std::min(479u,unsigned(gy));
   double hy=(double(ry)+gy)*S-0.5;hy-=std::floor(hy/hh)*hh;const unsigned y0h=unsigned(hy)%hh,y1h=(y0h+1)%hh;const float ty=float(hy-std::floor(hy));
   const double qy=gy-0.5;const int ay=std::clamp(int(std::floor(qy)),0,478);const float wy=float(std::clamp(qy-ay,0.0,1.0));
   for(unsigned ox=0;ox<ow;++ox){const double gx=(ox+0.5)/fit;const unsigned nx=std::min(639u,unsigned(gx));const size_t ni=size_t(ny)*640+nx;
    std::uint32_t o;
    if(!cand[ni]){const std::uint16_t f=frame[ny*fp_+nx];o=0xff000000u|unsigned(ch(f,0)+.5f)|unsigned(ch(f,1)+.5f)<<8|unsigned(ch(f,2)+.5f)<<16;}
    else{double hx=(double(rx)+gx)*S-0.5;hx-=std::floor(hx/hw)*hw;const unsigned x0h=unsigned(hx)%hw,x1h=(x0h+1)%hw;const float tx=float(hx-std::floor(hx));
     const double qx=gx-0.5;const int ax=std::clamp(int(std::floor(qx)),0,638);const float wx=float(std::clamp(qx-ax,0.0,1.0));
     float gn[3]{},ad[3]{},wsum=0,asum=0;const float wts[4]={(1-wx)*(1-wy),wx*(1-wy),(1-wx)*wy,wx*wy};const size_t idx[4]={size_t(ay)*640+ax,size_t(ay)*640+ax+1,size_t(ay+1)*640+ax,size_t(ay+1)*640+ax+1};
     for(int k=0;k<4;++k){if(cand[idx[k]]==1){wsum+=wts[k];for(int c=0;c<3;++c)gn[c]+=wts[k]*gain[idx[k]*3+c];}else if(cand[idx[k]]==2){asum+=wts[k];for(int c=0;c<3;++c)ad[c]+=wts[k]*add[idx[k]*3+c];}}
     if(wsum>0)for(float&q:gn)q/=wsum;else for(float&q:gn)q=1.f;
     if(asum>0)for(float&q:ad)q/=asum;
     const float af=cand[ni]==2?1.f:asum;
     o=0xff000000u;for(int c=0;c<3;++c){const float a=H[(size_t(y0h)*hw+x0h)*3+c],b=H[(size_t(y0h)*hw+x1h)*3+c],cc=H[(size_t(y1h)*hw+x0h)*3+c],d=H[(size_t(y1h)*hw+x1h)*3+c];
      const float val=((a*(1-tx)+b*tx)*(1-ty)+(cc*(1-tx)+d*tx)*ty)*gn[c]+ad[c]*af;o|=unsigned(std::clamp(val+.5f,0.f,255.f))<<(8*c);}}
    out[size_t(oy)*ow+ox]=o;}}};
 const unsigned nt=std::max(1u,std::min(8u,std::thread::hardware_concurrency()));std::vector<std::thread>pool;
 for(unsigned t=0;t<nt;++t)pool.emplace_back(rows,oh*t/nt,oh*(t+1)/nt);for(auto&t:pool)t.join();
 {static const std::string dump=[]{const char*p=std::getenv("MW34_MENU_HD_DUMP");return std::string(p?p:"");}();static const std::string at=[]{const char*p=std::getenv("MW34_MENU_HD_DUMP_FRAMES");return std::string(p?p:"");}();
  if(!dump.empty()&&(","+at+",").find(","+std::to_string(host.frames)+",")!=std::string::npos)if(FILE*f=std::fopen((dump+"."+std::to_string(host.frames)+".ppm").c_str(),"wb")){
   std::fprintf(f,"P6\n%u %u\n255\n",ow,oh);std::vector<unsigned char>row(size_t(ow)*3);for(unsigned y=0;y<oh;++y){for(unsigned x=0;x<ow;++x){const auto q=out[size_t(y)*ow+x];row[x*3]=q&255;row[x*3+1]=(q>>8)&255;row[x*3+2]=(q>>16)&255;}std::fwrite(row.data(),1,row.size(),f);}std::fclose(f);}}
 bool shown=false;
 try{HostInternal hi(*this);shown=host.presenter->present(host.display.window,reinterpret_cast<const std::uint8_t*>(out.data()),ow,oh,ow*4,false,true);}catch(const std::exception&ex){deny(std::string(ex.what()),v.guest);}
 if(shown)++menu_hd_frames;
 return shown;
}
'''

def apply(host):
    vk=host/'vk_scene.hpp'
    edit(vk,'#include <set>','#include <set>\n#include <thread>')
    edit(vk,'    bool present(HWND hwnd, const std::uint8_t *pixels, unsigned w, unsigned h, unsigned pitch,bool wide_world=false) {',
            '    bool present(HWND hwnd, const std::uint8_t *pixels, unsigned w, unsigned h, unsigned pitch,bool wide_world=false,bool rgba32=false) {')
    edit(vk,'        if (w != srcWidth || h != srcHeight) presentSource(w, h);\n        ensure(presentUpload, VkDeviceSize(w) * h * 2, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);',
            '        if (w != srcWidth || h != srcHeight || rgba32 != srcRgba) presentSource(w, h, rgba32);\n        const unsigned bpp = rgba32 ? 4 : 2;\n        ensure(presentUpload, VkDeviceSize(w) * h * bpp, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);')
    edit(vk,'        for (unsigned y = 0; y < h; ++y) std::memcpy(dst + size_t(y) * w * 2, pixels + size_t(y) * pitch, size_t(w) * 2);\n        if (overlay.on) overlay.draw(reinterpret_cast<std::uint16_t *>(dst), w, h);',
            '        for (unsigned y = 0; y < h; ++y) std::memcpy(dst + size_t(y) * w * bpp, pixels + size_t(y) * pitch, size_t(w) * bpp);\n        if (overlay.on && !rgba32) overlay.draw(reinterpret_cast<std::uint16_t *>(dst), w, h);')
    edit(vk,'    void presentSource(unsigned w, unsigned h) {','    bool srcRgba{};\n    void presentSource(unsigned w, unsigned h, bool rgba32 = false) {')
    edit(vk,'        image(srcImage.image, srcImage.memory, srcImage.view, w, h, VK_FORMAT_R5G6B5_UNORM_PACK16, VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT, VK_IMAGE_ASPECT_COLOR_BIT);\n        srcWidth = w; srcHeight = h;',
            '        image(srcImage.image, srcImage.memory, srcImage.view, w, h, rgba32 ? VK_FORMAT_R8G8B8A8_UNORM : VK_FORMAT_R5G6B5_UNORM_PACK16, VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT, VK_IMAGE_ASPECT_COLOR_BIT);\n        srcWidth = w; srcHeight = h; srcRgba = rgba32;')
    v=host/'vdd.inc'
    edit(v,'void present(const VSurface&v){',COMPOSITOR.strip()+'\nvoid present(const VSurface&v){')
    edit(v,'  if(!present_direct)shown=host.presenter->present(host.display.window,px.data(),w,h,v.pitch,wide_on()&&!frontend_on()&&wide_world_frame==host.frames);',
           '  if(!present_direct)shown=menu_hd_present(v,px)||host.presenter->present(host.display.window,px.data(),w,h,v.pitch,wide_on()&&!frontend_on()&&wide_world_frame==host.frames);')
    m=host/'mfc_stage.hpp'
    edit(m,'  if(target==0x40a210){static const double hz','  if(target==0x40a210){menu_bg_widget=state.gpr.rcx.dword;menu_bg_frame=host.frames;}\n  if(target==0x40a210){static const double hz')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
