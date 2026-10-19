"""Front end at display resolution from the game's own 2D draw list.

Every element of the menu frame is drawn by the original image blit 0x55B3C0
(ECX image, EDX x, [esp+4] y, [esp+8] colour key, [esp+12] optional source
rectangle) into the 640x480 frame; text images are DrawTextA recipes recorded
by the GPU HUD text hooks (0x577BA0/0x577BD0). The game still draws the frame
as before; each blit is also recorded with a snapshot of the pixels it uses.

At presentation (frames without a 3D scene, MW34_MENU_HD_BG set):
  1. the list is replayed at 640x480 and compared with the game's frame; if
     fewer than 97% of pixels agree (within 2 RGB565 steps), nothing changes;
  2. the list is replayed at the window's 4:3 fit (max 2880x2160) in order:
     the 1280x960 background from the HD image, text images re-rendered with
     their recorded fonts at the output scale, images with a hi-res pack entry
     (MW34_HIRES_HUD identity keys) from that texture, other images bilinear
     (premultiplied alpha). Mask planes give alpha (<=3 clear, >=252 opaque),
     colour-key images are transparent at the key, the rest are opaque;
  3. the result is presented as 32-bit colour.
Apply after apply_menu_hd.py (falls back to its compositor).
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one menu-DL anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

RECORD = r'''  if(target==0x55b3c0&&menu_hd_image().ok&&wide_world_frame!=host.frames)menu_dl_record();
'''

RENDER = r'''
struct MenuBlit{int x{},y{},sx0{},sy0{},sw{},sh{},iw{},ih{};unsigned mode{},key{};bool bg{},text{},hires{};std::uint64_t id{};unsigned text_img{};std::uint64_t text_hash{};std::vector<std::uint16_t>px;std::vector<std::uint8_t>al;};
std::vector<MenuBlit>menu_dl;bool menu_hires_loaded{};
// Additional hi-res sprites for the front end (MW34_HIRES_MENU=<dir>, same MW3H .rgba format and identity keys as the HUD pack).
void menu_hires_load(){if(menu_hires_loaded)return;menu_hires_loaded=true;const char*e=std::getenv("MW34_HIRES_MENU");if(!e||!*e)return;std::error_code ec;
 for(const auto&f:std::filesystem::directory_iterator(e,ec)){if(f.path().extension()!=".rgba")continue;std::ifstream in(f.path(),std::ios::binary);char magic[4]{};HiresTex h{};
  in.read(magic,4);in.read(reinterpret_cast<char*>(&h.w),4);in.read(reinterpret_cast<char*>(&h.h),4);in.read(reinterpret_cast<char*>(&h.u0),16);
  if(!in||std::memcmp(magic,"MW3H",4)||!h.w||!h.h||h.w>8192||h.h>8192)continue;h.px.resize(size_t(h.w)*h.h);in.read(reinterpret_cast<char*>(h.px.data()),std::streamsize(h.px.size()*4));if(!in)continue;
  try{hires[std::stoull(f.path().stem().string(),nullptr,16)]=std::move(h);}catch(...){}}
 std::fprintf(stderr,"Menu hi-res sprites: %zu entries total\n",hires.size());}unsigned menu_dl_frame{~0u},menu_dl_target{};bool menu_dl_bad{};std::uint64_t menu_dl_frames{},menu_dl_rejects{};
void menu_dl_record(){
 if(menu_dl_frame!=host.frames){menu_dl.clear();menu_dl_frame=host.frames;menu_dl_target=load(0x8007c8);menu_dl_bad=false;}
 if(menu_dl_bad)return;if(load(0x8007c8)!=menu_dl_target||menu_dl.size()>4096){menu_dl_bad=true;return;}
 const auto&g=state.gpr;const unsigned sp=g.rsp.dword,img=g.rcx.dword;MenuBlit b;b.x=int(g.rdx.dword);b.y=int(load(sp+4));b.key=load(sp+8)&0xffff;const unsigned src=load(sp+12);
 if(!readable(img,0x38)){menu_dl_bad=true;return;}
 b.iw=std::int16_t(load(img+4)&0xffff);b.ih=std::int16_t(load(img+6)&0xffff);const unsigned flags=(load(img+8)>>8)&0xff,pix=load(img+0x10),mask=load(img+0x14),alt=load(img+0x18),pitch=load(img+0x34);
 if(alt||b.iw<=0||b.ih<=0){menu_dl_bad=true;return;}
 int sx0=0,sy0=0,sx1=b.iw,sy1=b.ih;if(src){if(!readable(src,16)){menu_dl_bad=true;return;}sx0=int(load(src));sy0=int(load(src+4));sx1=int(load(src+8));sy1=int(load(src+12));}
 if(sx0<0||sy0<0||sx1>int(pitch)||sy1>b.ih||sx1<sx0||sy1<sy0){menu_dl_bad=true;return;}
 // Clip the destination to the 640x480 frame.
 int x=b.x,y=b.y;if(x<0){sx0-=x;x=0;}if(y<0){sy0-=y;y=0;}sx1=std::min(sx1,sx0+(640-x));sy1=std::min(sy1,sy0+(480-y));
 if(sx1<=sx0||sy1<=sy0)return;
 b.x=x;b.y=y;b.sx0=sx0;b.sy0=sy0;b.sw=sx1-sx0;b.sh=sy1-sy0;b.mode=mask?2U:(flags&2)?1U:0U;
 b.px.resize(size_t(b.sw)*b.sh);if(mask)b.al.resize(b.px.size());
 for(int r=0;r<b.sh;++r){get_bytes(pix+2*(unsigned(sy0+r)*pitch+unsigned(sx0)),b.px.data()+size_t(r)*b.sw,unsigned(b.sw)*2);if(mask)get_bytes(mask+unsigned(sy0+r)*pitch+unsigned(sx0),b.al.data()+size_t(r)*b.sw,unsigned(b.sw));}
 const auto&hd=menu_hd_image();b.bg=hd.ok&&unsigned(b.iw)==hd.sw&&unsigned(b.ih)==hd.sh&&b.mode==0;
 if(auto t=text_images.find(img);t!=text_images.end()&&t->second.w==b.iw&&t->second.h==b.ih){b.text=true;b.text_img=img;b.text_hash=t->second.hash;}
 static const std::string sprite_dump=[]{const char*p=std::getenv("MW34_MENU_SPRITE_DUMP");return std::string(p?p:"");}();
 if(!b.bg&&!b.text){if(!hires_loaded)hires_load();menu_hires_load();const bool want=!hires.empty()||!sprite_dump.empty();
  if(want&&std::int64_t(b.iw)*b.ih<=1<<20){b.id=hud_identity(pix,mask,b.mode,b.key,b.iw,b.ih,pitch);b.hires=hires.count(b.id)!=0;
   static std::set<std::uint64_t>dumped;if(!sprite_dump.empty()&&b.iw*b.ih>=16&&dumped.insert(b.id).second){char name[64];std::snprintf(name,sizeof name,"/%016llx.mwsp",(unsigned long long)b.id);
    if(FILE*f=std::fopen((sprite_dump+name).c_str(),"wb")){const unsigned hdr[3]={unsigned(b.iw),unsigned(b.ih),b.mode};std::fwrite("MWSP",1,4,f);std::fwrite(hdr,4,3,f);std::vector<std::uint16_t>row(b.iw);std::vector<std::uint8_t>mr(b.iw);std::vector<std::uint32_t>o(b.iw);
     for(int r=0;r<b.ih;++r){get_bytes(pix+2*unsigned(r)*pitch,row.data(),unsigned(b.iw)*2);if(mask)get_bytes(mask+unsigned(r)*pitch,mr.data(),unsigned(b.iw));
      for(int q=0;q<b.iw;++q){unsigned a=255;if(b.mode==2){const unsigned m=mr[q];a=m<=3?0u:m>=0xfc?255u:m;}else if(b.mode==1&&row[q]==b.key)a=0;o[q]=hud_rgba(row[q],a);}std::fwrite(o.data(),4,o.size(),f);}std::fclose(f);}}}}
 menu_dl.push_back(std::move(b));
}
bool menu_dl_present(const VSurface&v,const std::vector<unsigned char>&px){
 const auto&hd=menu_hd_image();
 if(!hd.ok||v.bpp!=16||v.width!=640||v.height!=480||px.size()<size_t(v.pitch)*480||wide_world_frame==host.frames)return false;
 if(menu_dl_frame!=host.frames||menu_dl_bad||menu_dl.empty())return false;
 const std::uint16_t*frame=reinterpret_cast<const std::uint16_t*>(px.data());const unsigned fp_=v.pitch/2;
 mw34::vkscene::HostFpEnvironment fp;
 auto alpha=[](const MenuBlit&b,size_t i)->unsigned{if(b.mode==2){const unsigned m=b.al[i];return m<=3?0u:m>=0xfc?255u:m;}if(b.mode==1&&b.px[i]==b.key)return 0u;return 255u;};
 // 1. Replay at 640x480 and compare with the game's frame.
 {static std::vector<float>c(640*480*3);std::fill(c.begin(),c.end(),0.f);
  for(const auto&b:menu_dl)for(int r=0;r<b.sh;++r)for(int q=0;q<b.sw;++q){const size_t i=size_t(r)*b.sw+q;const unsigned a=alpha(b,i);if(!a)continue;const std::uint16_t p=b.px[i];
   float*d=&c[(size_t(b.y+r)*640+unsigned(b.x+q))*3];const float s[3]={float((p>>11)&31),float((p>>5)&63),float(p&31)},t=a/255.f;for(int k=0;k<3;++k)d[k]=s[k]*t+d[k]*(1-t);}
  size_t good=0;for(unsigned y=0;y<480;++y)for(unsigned x=0;x<640;++x){const std::uint16_t f=frame[y*fp_+x];const float*d=&c[(size_t(y)*640+x)*3];
   good+=std::abs(float((f>>11)&31)-d[0])<=2.5f&&std::abs(float((f>>5)&63)-d[1])<=4.5f&&std::abs(float(f&31)-d[2])<=2.5f;}
  const double ratio=double(good)/(640.0*480.0);
  static bool told=false;if(!told||ratio<0.97){if(!told||menu_dl_rejects<5)std::fprintf(stderr,"Menu draw list: %zu blits, replay match %.4f%s\n",menu_dl.size(),ratio,ratio<0.97?" (rejected)":"");told=true;}
  if(ratio<0.97){++menu_dl_rejects;return false;}}
 // 2. Replay at output resolution.
 RECT rc{};::GetClientRect(host.display.window,&rc);if(rc.right<=0||rc.bottom<=0)return false;
 const double fit=std::min({double(rc.right)/640.0,double(rc.bottom)/480.0,2880.0/640.0});
 const unsigned ow=unsigned(std::lround(640*fit)),oh=unsigned(std::lround(480*fit));if(ow<640||oh<480)return false;
 struct Src{const std::uint32_t*px{};unsigned w{},h{};float u0{},v0{},u1{},v1{};};  // straight-alpha RGBA texture and the [u0,u1]x[v0,v1] range for the full image
 std::vector<Src>srcs(menu_dl.size());
 for(size_t n=0;n<menu_dl.size();++n){const auto&b=menu_dl[n];
  auto tit=b.text?text_images.find(b.text_img):text_images.end();
  if(b.text&&hud_text_on()&&tit!=text_images.end()&&tit->second.hash==b.text_hash){const auto&ti=tit->second;const std::uint64_t key=ti.hash^std::uint64_t(std::lround(fit*256));auto it=text_cache.find(key);
   if(it==text_cache.end()){if(text_cache.size()>512)text_cache.clear();TextTex tt{};tt.px=text_render(ti,float(fit),tt.w,tt.h,tt.u0,tt.u1);it=text_cache.emplace(key,std::move(tt)).first;}
   if(it->second.w&&it->second.h){const float fh=float(b.ih)*float(fit)/float(it->second.h);srcs[n]={it->second.px.data(),it->second.w,it->second.h,it->second.u0,0.f,it->second.u1,fh};}}
  else if(b.hires){const auto&ht=hires.at(b.id);srcs[n]={ht.px.data(),ht.w,ht.h,ht.u0,ht.v0,ht.u1,ht.v1};}}
 static std::vector<std::uint32_t>out;out.assign(size_t(ow)*oh,0xff000000u);
 const double S=double(hd.w)/double(hd.sw);const unsigned hw=hd.w,hh=hd.h;const unsigned char*H=hd.rgb.data();
 auto rows=[&](unsigned y0,unsigned y1){mw34::vkscene::HostFpEnvironment fpw;std::vector<float>acc(size_t(ow)*3);
  for(unsigned oy=y0;oy<y1;++oy){const double gy=(oy+0.5)/fit;std::fill(acc.begin(),acc.end(),0.f);
   for(size_t n=0;n<menu_dl.size();++n){const auto&b=menu_dl[n];const double ly=gy-b.y;if(ly<0||ly>=b.sh)continue;
    const unsigned ox0=unsigned(std::max(0.0,std::ceil(b.x*fit-0.5))),ox1=std::min(ow,unsigned(std::max(0.0,std::ceil((b.x+b.sw)*fit-0.5))));
    const auto&s=srcs[n];
    for(unsigned ox=ox0;ox<ox1;++ox){const double lx=(ox+0.5)/fit-b.x;float c[3],a;
     if(b.bg){double hx=(b.sx0+lx)*S-0.5,hy=(b.sy0+ly)*S-0.5;hx=std::clamp(hx,0.0,double(hw-1));hy=std::clamp(hy,0.0,double(hh-1));
      const unsigned x0=unsigned(hx),y0_=unsigned(hy),x1=std::min(x0+1,hw-1),y1_=std::min(y0_+1,hh-1);const float tx=float(hx-x0),ty=float(hy-y0_);
      for(int k=0;k<3;++k){const float p00=H[(size_t(y0_)*hw+x0)*3+k],p10=H[(size_t(y0_)*hw+x1)*3+k],p01=H[(size_t(y1_)*hw+x0)*3+k],p11=H[(size_t(y1_)*hw+x1)*3+k];
       c[k]=(p00*(1-tx)+p10*tx)*(1-ty)+(p01*(1-tx)+p11*tx)*ty;}a=1.f;}
     else if(s.px){// hi-res or text texture: map the image coordinate into the texture's range
      const double fu=(b.sx0+lx)/b.iw,fv=(b.sy0+ly)/b.ih;double tu=(s.u0+(s.u1-s.u0)*fu)*s.w-0.5,tv=(s.v0+(s.v1-s.v0)*fv)*s.h-0.5;
      tu=std::clamp(tu,0.0,double(s.w-1));tv=std::clamp(tv,0.0,double(s.h-1));const unsigned x0=unsigned(tu),y0_=unsigned(tv),x1=std::min(x0+1,s.w-1),y1_=std::min(y0_+1,s.h-1);
      const float tx=float(tu-x0),ty=float(tv-y0_);const float w4[4]={(1-tx)*(1-ty),tx*(1-ty),(1-tx)*ty,tx*ty};const std::uint32_t q[4]={s.px[size_t(y0_)*s.w+x0],s.px[size_t(y0_)*s.w+x1],s.px[size_t(y1_)*s.w+x0],s.px[size_t(y1_)*s.w+x1]};
      float pm[3]{};a=0;for(int j=0;j<4;++j){const float qa=float(q[j]>>24)/255.f*w4[j];a+=qa;for(int k=0;k<3;++k)pm[k]+=float((q[j]>>(8*k))&255)*qa;}
      if(a<=1e-4f)continue;for(int k=0;k<3;++k)c[k]=pm[k]/a;}
     else{// low-resolution image: bilinear with premultiplied alpha over the snapshot
      double qx=lx-0.5,qy=ly-0.5;qx=std::clamp(qx,0.0,double(b.sw-1));qy=std::clamp(qy,0.0,double(b.sh-1));const unsigned x0=unsigned(qx),y0_=unsigned(qy),x1=std::min(x0+1,unsigned(b.sw-1)),y1_=std::min(y0_+1,unsigned(b.sh-1));
      const float tx=float(qx-x0),ty=float(qy-y0_);const float w4[4]={(1-tx)*(1-ty),tx*(1-ty),(1-tx)*ty,tx*ty};const size_t id4[4]={size_t(y0_)*b.sw+x0,size_t(y0_)*b.sw+x1,size_t(y1_)*b.sw+x0,size_t(y1_)*b.sw+x1};
      float pm[3]{};a=0;for(int j=0;j<4;++j){const float qa=float(alpha(b,id4[j]))/255.f*w4[j];if(qa<=0)continue;a+=qa;const std::uint16_t p=b.px[id4[j]];
       pm[0]+=float((p>>11)&31)*(255.f/31)*qa;pm[1]+=float((p>>5)&63)*(255.f/63)*qa;pm[2]+=float(p&31)*(255.f/31)*qa;}
      if(a<=1e-4f)continue;for(int k=0;k<3;++k)c[k]=pm[k]/a;}
     float*d=&acc[size_t(ox)*3];for(int k=0;k<3;++k)d[k]=c[k]*a+d[k]*(1-a);}}
   for(unsigned ox=0;ox<ow;++ox){const float*d=&acc[size_t(ox)*3];out[size_t(oy)*ow+ox]=0xff000000u|unsigned(std::clamp(d[0]+.5f,0.f,255.f))|unsigned(std::clamp(d[1]+.5f,0.f,255.f))<<8|unsigned(std::clamp(d[2]+.5f,0.f,255.f))<<16;}}};
 const unsigned nt=std::max(1u,std::min(8u,std::thread::hardware_concurrency()));std::vector<std::thread>pool;
 for(unsigned t=0;t<nt;++t)pool.emplace_back(rows,oh*t/nt,oh*(t+1)/nt);for(auto&t:pool)t.join();
 {static const std::string dump=[]{const char*p=std::getenv("MW34_MENU_HD_DUMP");return std::string(p?p:"");}();static const std::string at=[]{const char*p=std::getenv("MW34_MENU_HD_DUMP_FRAMES");return std::string(p?p:"");}();
  if(!dump.empty()&&(","+at+",").find(","+std::to_string(host.frames)+",")!=std::string::npos)if(FILE*f=std::fopen((dump+".dl."+std::to_string(host.frames)+".ppm").c_str(),"wb")){
   std::fprintf(f,"P6\n%u %u\n255\n",ow,oh);std::vector<unsigned char>row(size_t(ow)*3);for(unsigned y=0;y<oh;++y){for(unsigned x=0;x<ow;++x){const auto q=out[size_t(y)*ow+x];row[x*3]=q&255;row[x*3+1]=(q>>8)&255;row[x*3+2]=(q>>16)&255;}std::fwrite(row.data(),1,row.size(),f);}std::fclose(f);}}
 bool shown=false;
 try{HostInternal hi(*this);shown=host.presenter->present(host.display.window,reinterpret_cast<const std::uint8_t*>(out.data()),ow,oh,ow*4,false,true);}catch(const std::exception&ex){deny(std::string(ex.what()),v.guest);}
 if(shown)++menu_dl_frames;
 return shown;
}
'''

def apply(host):
    v=host/'vdd.inc'
    if 'menu_hd_present' not in v.read_text():raise RuntimeError('Apply apply_menu_hd.py first')
    edit(v,'void present(const VSurface&v){',RENDER.strip()+'\nvoid present(const VSurface&v){')
    edit(v,'shown=menu_hd_present(v,px)||','shown=menu_dl_present(v,px)||menu_hd_present(v,px)||')
    m=host/'mfc_stage.hpp'
    edit(m,'  if(target==0x40a210){menu_bg_widget=state.gpr.rcx.dword;menu_bg_frame=host.frames;}',RECORD+'  if(target==0x40a210){menu_bg_widget=state.gpr.rcx.dword;menu_bg_frame=host.frames;}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
