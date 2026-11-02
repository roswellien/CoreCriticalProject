// Virtual display surfaces (project presentation provider; included inside mf::Stage).
// Surfaces are guest COM objects whose pixel memory lives in guest pages, so Lock hands the game a
// guest pointer and the game's own (recompiled) renderer writes the pixels. Flip swaps the surface
// memory of the front buffer and its attached back buffer (DirectDraw flip semantics) and presents the
// front buffer to the game window. Blt/BltFast implement colour fill, copy, source colour key and
// nearest stretch for same-format surfaces. Anything outside this model stops typed.

using VSurface=VSurfaceRec;using VPalette=VPaletteRec;
VSurface*vsurface(unsigned g){auto&h=host;for(;h.vsurf_indexed<h.vsurfaces.size();++h.vsurf_indexed)h.vsurf_index.emplace(h.vsurfaces[h.vsurf_indexed].guest,h.vsurf_indexed);const auto it=h.vsurf_index.find(g);return it==h.vsurf_index.end()||!h.vsurfaces[it->second].bytes?nullptr:&h.vsurfaces[it->second];}
unsigned vsurf_root(unsigned g){const auto*o=host.com_object(g);return o?root_of(*o):g;}
VSurface*vsurf_of(unsigned g){return vsurface(vsurf_root(g));}
void surface_collect_retired(){
 // Recycle only released identities, retaining provider-side references too.
 std::set<unsigned> pinned{host.res_rt,host.res_zb};
 for(const auto&o:host.com_objects)if(o.alive||o.refs)pinned.insert(root_of(o));
 for(const auto&d:host.devices){
  if(host.com_object(d.guest)){pinned.insert(d.target);pinned.insert(d.zbuffer);for(unsigned t:d.textures)pinned.insert(t);}
  for(const auto&c:d.commands)if(c.kind==D3DCmd::Draw)pinned.insert(c.texture);
 }
 for(size_t before=~size_t{};before!=pinned.size();){before=pinned.size();for(const auto&v:host.vsurfaces)if(pinned.count(v.guest)){pinned.insert(v.attached);pinned.insert(v.zbuffer);}}
 unsigned count=0;std::uint64_t bytes=0;
 for(auto&v:host.vsurfaces)if(v.bytes&&!v.locks&&!pinned.count(v.guest)){
  const auto n=(std::uint64_t(v.bytes)+4095)&~std::uint64_t(4095);
  if(!n||n>0xffffffffULL)deny("Invalid retired surface extent",v.mem);
  if(v.mem){runtime.memory().unmap({v.mem});host.surface_free_pages.put(v.mem,unsigned(n));}v.pixels.clear();
  bytes+=n;++count;v.mem=0;v.bytes=0;
 }
 std::fprintf(stderr,"Surface page reclamation: %u retired surfaces, %llu bytes\n",count,(unsigned long long)bytes);
}
unsigned surface_pages(unsigned bytes){
 const auto aligned=(std::uint64_t(std::max(bytes,1U))+4095)&~std::uint64_t(4095);
 if(aligned>0xffffffffULL)deny("Surface page size overflow",bytes);const unsigned n=unsigned(aligned);
 unsigned g=host.surface_free_pages.take(n);
 if(!g){
  if(!host.vsurface_next)host.vsurface_next=vsurface_arena;
  if(host.vsurface_next<0x80000000U&&std::uint64_t(host.vsurface_next)+n>vsurface_arena_end&&std::getenv("MW34_REMASTER_BANKS"))host.vsurface_next=0x80000000U;
  const std::uint64_t limit=host.vsurface_next>=0x80000000U?0xf0000000ULL:vsurface_arena_end;
  if(std::uint64_t(host.vsurface_next)+n>limit){surface_collect_retired();g=host.surface_free_pages.take(n);if(!g)deny("Virtual surface arena exhausted (no safe retired range fits)",host.vsurface_next);}
  else{g=host.vsurface_next;host.vsurface_next+=n;}
 }
 bool bad{};try{runtime.memory().map({g},n,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked surface memory mapping",g);return g;
}
unsigned make_surface(unsigned w,unsigned h,unsigned bpp,unsigned caps,const com::Iface&iface){const auto row=(std::uint64_t(w)*bpp/8+3)&~std::uint64_t(3);const auto extent=row*h;
 if(!w||!h||!bpp||row>0xffffffffULL||extent>0xffffffffULL)deny("Surface dimensions overflow",w);const unsigned pitch=unsigned(row),bytes=unsigned(extent);
 const unsigned g=com_wrap(nullptr,iface);host.com_object(g)->refs=1;host.vsurfaces.push_back({g,w,h,pitch,bpp,caps,(caps&DDSCAPS_TEXTURE)?0:surface_pages(bytes),bytes,0,0,0});if(caps&DDSCAPS_TEXTURE)host.vsurfaces.back().pixels.resize(bytes);if(host.vsurfaces.size()%128==0)surface_collect_retired();host.vsurfaces.back().version=++host.surface_versions;return g;}
// Service reads/writes see the live guest Lock view when present, otherwise host storage.
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
DDPIXELFORMAT surface_format(const VSurface&v){if(v.caps&(DDSCAPS_TEXTURE|DDSCAPS_ZBUFFER)){DDPIXELFORMAT f{};f.dwSize=sizeof(f);f.dwRGBBitCount=16;
  if(v.caps&DDSCAPS_ZBUFFER){f.dwFlags=DDPF_ZBUFFER;f.dwRBitMask=0;f.dwGBitMask=0xffff;return f;}f.dwFlags=DDPF_RGB|(v.tex_masks[3]?DDPF_ALPHAPIXELS:0);f.dwRBitMask=v.tex_masks[0];f.dwGBitMask=v.tex_masks[1];f.dwBBitMask=v.tex_masks[2];f.dwRGBAlphaBitMask=v.tex_masks[3];return f;}
 return virtual_format(v.bpp);}
void fill_desc(const VSurface&v,DDSURFACEDESC2&d){d={};d.dwSize=sizeof(d);d.dwFlags=DDSD_CAPS|DDSD_WIDTH|DDSD_HEIGHT|DDSD_PITCH|DDSD_PIXELFORMAT;d.dwWidth=v.width;d.dwHeight=v.height;d.lPitch=LONG(v.pitch);
 d.ddpfPixelFormat=surface_format(v);d.ddsCaps.dwCaps=v.caps;if(v.attached){d.dwFlags|=DDSD_BACKBUFFERCOUNT;d.dwBackBufferCount=1;}if(v.has_src_key){d.dwFlags|=DDSD_CKSRCBLT;d.ddckCKSrcBlt=v.src_key;}}
// Presentation of the front buffer (RGB565 / palettized) into the game window's client area.
// Lazy residency of the 3D target (MW34_LAZY_RT=1). After a scene the GPU images hold the newest render-target and
// z-buffer content; guest memory is refreshed (gpu_sync) only before a service reads or writes one of those surfaces:
// Lock, Blt/BltFast, fills, Flip/presentation, texture Load and texture uploads. While the guest copy is stale its pages are
// inaccessible, so guest code touching them outside a service stops typed instead of using old pixels.
mw34::vkscene::Renderer*scene_renderer(){if(!host.sren){if(lazy_rt()&&host.presenter)host.sren=host.presenter.get();else{if(!host.renderer)host.renderer=std::make_unique<mw34::vkscene::Renderer>();host.sren=host.renderer.get();}}return host.sren;}
// Render scale of the resident target on the presenter device: the window's client height over the game height
// (1..4), or MW34_RENDER_SCALE. The 3D scenes and the GPU HUD render at that resolution; guest copies stay at the
// game resolution (blits through staging images).
float render_scale(unsigned gh){const unsigned output=mw34::vkscene::Renderer::remaster_height();
 if(output){if(!gh)throw std::runtime_error("Remaster render target has zero height");return std::clamp(float(output)/float(gh),1.f,4.f);}
 static const char*e=std::getenv("MW34_RENDER_SCALE");if(e&&*e)return std::clamp(std::stof(e),1.f,4.f);
 RECT rc{};if(!host.display.window||!::GetClientRect(host.display.window,&rc)||rc.bottom<=0||!gh)return 1.f;return std::clamp(float(rc.bottom)/float(gh),1.f,4.f);}
static bool lazy_rt(){static const bool on=[]{const char*e=std::getenv("MW34_LAZY_RT");return e&&*e=='1';}();return on;}
void gpu_protect(bool stale){if(stale==host.res_protected)return;host.res_protected=stale;auto*b=reinterpret_cast<std::byte*>(runtime.memory().flat_base());if(!b)return;for(const unsigned g:{host.res_rt,host.res_zb})if(g)if(auto*v=vsurface(g)){DWORD old{};
 if(!::VirtualProtect(b+v->mem,v->bytes,stale?PAGE_NOACCESS:PAGE_READWRITE,&old))deny("Resident surface page protection",v->guest);}}
void gpu_sync(unsigned guest){if(!host.res_dirty||(guest&&guest!=host.res_rt&&guest!=host.res_zb))return;auto*rt=vsurface(host.res_rt);if(!rt||!host.sren)deny("Resident render target is gone",host.res_rt);
 auto*zb=host.res_zb?vsurface(host.res_zb):nullptr;gpu_protect(false);namespace vs=mw34::vkscene;vs::Scene sc{};sc.width=rt->width;sc.height=rt->height;sc.color.resize(size_t(sc.width)*sc.height);sc.depth.resize(sc.color.size());
 try{HostInternal hi(*this);host.sren->fetch_resident(sc);}catch(const std::exception&e){deny(std::string(e.what()),0);}
 for(unsigned y=0;y<rt->height;++y)write_bytes(rt->mem+y*rt->pitch,sc.color.data()+size_t(y)*rt->width,rt->width*2);
 if(zb)for(unsigned y=0;y<zb->height;++y)write_bytes(zb->mem+y*zb->pitch,sc.depth.data()+size_t(y)*zb->width,zb->width*2);host.res_dirty=false;}
// Direct presentation (lazy residency on the presenter's device): set by Flip when the back buffer is the resident
// target and no frame dump is due; the presenter shows the resident image and the bookkeeping below is unchanged.
bool present_direct{};
// Copies the resident image into another surface's memory (direct presentation fallback); the GPU stays authoritative.
void resident_into(const VSurface&v){auto*rt=vsurface(host.res_rt);if(!rt||rt->width!=v.width||rt->height!=v.height)deny("Resident image does not fit the presented surface",v.guest);
 namespace vs=mw34::vkscene;vs::Scene sc{};sc.width=rt->width;sc.height=rt->height;sc.color.resize(size_t(sc.width)*sc.height);sc.depth.resize(sc.color.size());
 try{HostInternal hi(*this);host.sren->fetch_resident(sc);}catch(const std::exception&e){deny(std::string(e.what()),0);}
 for(unsigned y=0;y<v.height;++y)write_bytes(v.mem+y*v.pitch,sc.color.data()+size_t(y)*v.width,v.width*2);}
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
struct MenuBlit{int x{},y{},sx0{},sy0{},sw{},sh{},iw{},ih{};unsigned mode{},key{};bool bg{},text{},hires{},wave{};std::vector<mw34::menu::Offset>offsets;std::vector<std::uint32_t>raster;std::uint64_t id{};unsigned text_img{};std::uint64_t text_hash{};std::vector<std::uint16_t>px;std::vector<std::uint8_t>al;};
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

bool menu_dl_present(const VSurface&v,const std::vector<unsigned char>&px){
 const auto&hd=menu_hd_image();
 if(!hd.ok||v.bpp!=16||v.width!=640||v.height!=480||px.size()<size_t(v.pitch)*480||wide_world_frame==host.frames)return false;
 if(menu_dl_frame!=host.frames||menu_dl_bad||menu_dl.empty())return false;
 const std::uint16_t*frame=reinterpret_cast<const std::uint16_t*>(px.data());const unsigned fp_=v.pitch/2;
 mw34::vkscene::HostFpEnvironment fp;
 auto alpha=[](const MenuBlit&b,size_t i)->unsigned{if(b.mode==2){const unsigned m=b.al[i];return m<=3?0u:m>=0xfc?255u:m;}if(b.mode==1&&b.px[i]==b.key)return 0u;return 255u;};
 // 1. Replay at 640x480 and compare with the game's frame.
 {static std::vector<float>c(640*480*3);std::fill(c.begin(),c.end(),0.f);
  for(const auto&b:menu_dl){if(b.wave){const auto before=c;for(unsigned y=0;y<480;++y)for(unsigned x=0;x<640;++x){const auto d=b.offsets[y*640+x];const size_t to=(size_t(y)*640+x)*3,from=(size_t(int(y)+d.y)*640+unsigned(int(x)+d.x))*3;if(d.raster){const auto p=b.px[y*640+x];c[to]=float((p>>11)&31);c[to+1]=float((p>>5)&63);c[to+2]=float(p&31);}else for(int k=0;k<3;++k)c[to+k]=before[from+k];}continue;}for(int r=0;r<b.sh;++r)for(int q=0;q<b.sw;++q){const size_t i=size_t(r)*b.sw+q;const unsigned a=alpha(b,i);if(!a)continue;const std::uint16_t p=b.px[i];
   float*d=&c[(size_t(b.y+r)*640+unsigned(b.x+q))*3];const float s[3]={float((p>>11)&31),float((p>>5)&63),float(p&31)},t=a/255.f;for(int k=0;k<3;++k)d[k]=s[k]*t+d[k]*(1-t);}}
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
 std::vector<Src>srcs(menu_dl.size());std::vector<std::vector<std::uint32_t>>wave_pixels(menu_dl.size());
 for(size_t n=0;n<menu_dl.size();++n){const auto&b=menu_dl[n];
  auto tit=b.text?text_images.find(b.text_img):text_images.end();
  if(b.text&&hud_text_on()&&tit!=text_images.end()&&tit->second.hash==b.text_hash){const auto&ti=tit->second;const std::uint64_t key=ti.hash^std::uint64_t(std::lround(fit*256));auto it=text_cache.find(key);
   if(it==text_cache.end()){if(text_cache.size()>512)text_cache.clear();TextTex tt{};tt.px=text_render(ti,float(fit),tt.w,tt.h,tt.u0,tt.u1);it=text_cache.emplace(key,std::move(tt)).first;}
   if(it->second.w&&it->second.h){const float fh=float(b.ih)*float(fit)/float(it->second.h);srcs[n]={it->second.px.data(),it->second.w,it->second.h,it->second.u0,0.f,it->second.u1,fh};}}
  else if(b.hires){const auto&ht=hires.at(b.id);srcs[n]={ht.px.data(),ht.w,ht.h,ht.u0,ht.v0,ht.u1,ht.v1};}}
 static std::vector<std::uint32_t>out;out.assign(size_t(ow)*oh,0xff000000u);
 const double S=double(hd.w)/double(hd.sw);const unsigned hw=hd.w,hh=hd.h;const unsigned char*H=hd.rgb.data();
 size_t limit=menu_dl.size();unsigned clip_left=0,clip_right=ow;auto rows=[&](unsigned y0,unsigned y1){mw34::vkscene::HostFpEnvironment fpw;std::vector<float>acc(size_t(ow)*3);
  for(unsigned oy=y0;oy<y1;++oy){const double gy=(oy+0.5)/fit;std::fill(acc.begin(),acc.end(),0.f);
   for(size_t n=0;n<limit;++n){const auto&b=menu_dl[n];const double ly=gy-b.y;if(ly<0||ly>=b.sh)continue;
    const unsigned ox0=std::max(clip_left,unsigned(std::max(0.0,std::ceil(b.x*fit-0.5)))),ox1=std::min(clip_right,unsigned(std::max(0.0,std::ceil((b.x+b.sw)*fit-0.5))));
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
   for(unsigned ox=clip_left;ox<clip_right;++ox){const float*d=&acc[size_t(ox)*3];out[size_t(oy)*ow+ox]=0xff000000u|unsigned(std::clamp(d[0]+.5f,0.f,255.f))|unsigned(std::clamp(d[1]+.5f,0.f,255.f))<<8|unsigned(std::clamp(d[2]+.5f,0.f,255.f))<<16;}}};
 const unsigned nt=std::max(1u,std::min(8u,std::thread::hardware_concurrency()));
 auto render_prefix=[&](size_t count,unsigned left,unsigned top,unsigned right,unsigned bottom){limit=count;clip_left=left;clip_right=right;std::vector<std::thread>pool;for(unsigned t=0;t<nt;++t)pool.emplace_back(rows,top+(bottom-top)*t/nt,top+(bottom-top)*(t+1)/nt);for(auto&t:pool)t.join();};
 for(size_t n=0;n<menu_dl.size();++n)if(menu_dl[n].wave){const auto&b=menu_dl[n];int margin=2;for(const auto d:b.offsets)margin=std::max({margin,std::abs(d.x)+2,std::abs(d.y)+2});const unsigned left=unsigned(std::max(0.0,std::floor((b.x-margin)*fit))),top=unsigned(std::max(0.0,std::floor((b.y-margin)*fit))),right=std::min(ow,unsigned(std::max(0.0,std::ceil((b.x+b.sw+margin)*fit)))),bottom=std::min(oh,unsigned(std::max(0.0,std::ceil((b.y+b.sh+margin)*fit))));render_prefix(n,left,top,right,bottom);mw34::menu::warp_rgba(out,wave_pixels[n],ow,oh,b.offsets,&b.raster);srcs[n]={wave_pixels[n].data(),ow,oh,0.f,0.f,1.f,1.f};}
 render_prefix(menu_dl.size(),0,0,ow,oh);
 {static const std::string dump=[]{const char*p=std::getenv("MW34_MENU_HD_DUMP");return std::string(p?p:"");}();static const std::string at=[]{const char*p=std::getenv("MW34_MENU_HD_DUMP_FRAMES");return std::string(p?p:"");}();
  if(!dump.empty()&&(","+at+",").find(","+std::to_string(host.frames)+",")!=std::string::npos)if(FILE*f=std::fopen((dump+".dl."+std::to_string(host.frames)+".ppm").c_str(),"wb")){
   std::fprintf(f,"P6\n%u %u\n255\n",ow,oh);std::vector<unsigned char>row(size_t(ow)*3);for(unsigned y=0;y<oh;++y){for(unsigned x=0;x<ow;++x){const auto q=out[size_t(y)*ow+x];row[x*3]=q&255;row[x*3+1]=(q>>8)&255;row[x*3+2]=(q>>16)&255;}std::fwrite(row.data(),1,row.size(),f);}std::fclose(f);}}
 bool shown=false;
 try{HostInternal hi(*this);shown=host.presenter->present(host.display.window,reinterpret_cast<const std::uint8_t*>(out.data()),ow,oh,ow*4,false,true);}catch(const std::exception&ex){deny(std::string(ex.what()),v.guest);}
 if(shown)++menu_dl_frames;
 return shown;
}
void present(const VSurface&v,unsigned flipped_target=0){if(!present_direct)gpu_sync(v.guest);if(!host.display.window)deny("Presentation without a cooperative window",v.guest);const unsigned w=v.width,h=v.height;
 std::vector<unsigned char>px;if(!present_direct){px.resize(size_t(v.pitch)*h);get_bytes(v.mem,px.data(),unsigned(px.size()));if(v.bpp==16){mw34::vkscene::HostFpEnvironment fp;menu_version::paint_footer(px.data(),w,h,v.pitch);}}
 struct{BITMAPINFOHEADER h;DWORD masks[256];}bi{};bi.h.biSize=sizeof(BITMAPINFOHEADER);bi.h.biWidth=LONG(v.pitch/(v.bpp/8));bi.h.biHeight=-LONG(h);bi.h.biPlanes=1;bi.h.biBitCount=WORD(v.bpp);
 if(v.bpp==16){bi.h.biCompression=BI_BITFIELDS;bi.masks[0]=0xf800;bi.masks[1]=0x07e0;bi.masks[2]=0x001f;}else if(v.bpp==8){const auto*pal=vpalette(v.palette);if(!pal)deny("8-bit presentation without a palette",v.guest);
  for(unsigned i=0;i<256;++i)bi.masks[i]=RGB(pal->entries[i].peBlue,pal->entries[i].peGreen,pal->entries[i].peRed);bi.h.biClrUsed=256;}else deny("Presentation depth not modelled",v.bpp);
 // 16-bit frames are presented by the Vulkan swapchain presenter unless MW34_PRESENT=gdi; the GDI presenter
 // serves 8-bit frames and devices without window presentation.
 static const bool gdi_only=[]{const char*p=std::getenv("MW34_PRESENT");return p&&std::string(p)=="gdi";}();bool shown=false;
 if(v.bpp==16&&!gdi_only){if(!host.presenter)host.presenter=std::make_unique<mw34::vkscene::Renderer>();try{HostInternal hi(*this);if(present_direct){host.presenter->finish_world();photo_replay_on_present(w,h,true,px,v.pitch);if(host.presenter->overlay.on)overlay_gpu(w,h);{static const char*hp=std::getenv("MW34_HIRES_DUMP_FILE");static const unsigned hf=[]{const char*e=std::getenv("MW34_HIRES_DUMP");return e&&*e?unsigned(std::stoul(e)):0U;}();if(hf&&hp&&host.frames+1==hf)host.presenter->dump_fullres(hp);}{static const char*list=std::getenv("MW34_HIRES_DUMP_FRAMES");static const char*dir=std::getenv("MW34_HIRES_DUMP_DIR");if(list&&dir){std::istringstream frames(list);std::string item;while(std::getline(frames,item,','))if(std::stoul(item)==host.frames+1){const auto file=(std::filesystem::path(dir)/("target-"+std::to_string(host.frames+1)+".ppm")).string();host.presenter->dump_fullres(file.c_str());break;}}}shown=host.presenter->present_resident(host.display.window,w,h);if(!shown){resident_into(v);present_direct=false;px.resize(size_t(v.pitch)*h);get_bytes(v.mem,px.data(),unsigned(px.size()));}}
  if(!present_direct){photo_replay_on_present(w,h,false,px,v.pitch);shown=menu_dl_present(v,px)||menu_hd_present(v,px)||host.presenter->present(host.display.window,px.data(),w,h,v.pitch,wide_on()&&!frontend_on()&&wide_world_frame==host.frames);}}catch(const std::exception&e){deny(std::string(e.what()),v.guest);}
  if(shown&&host.presenter->presents==1)apis.back()+="(Vulkan presenter on "+host.presenter->device_name+")";}
 if(!shown){RECT rc{};::GetClientRect(host.display.window,&rc);HDC dc=::GetDC(host.display.window);::SetStretchBltMode(dc,COLORONCOLOR);
 int dx=0,dy=0,dw=rc.right,dh=rc.bottom;
 if(wide_on()&&(frontend_on()||wide_world_frame!=host.frames)){const double fit=std::min(double(dw)/w,double(dh)/h);dw=int(std::lround(w*fit));dh=int(std::lround(h*fit));dx=(rc.right-dw)/2;dy=(rc.bottom-dh)/2;::FillRect(dc,&rc,static_cast<HBRUSH>(::GetStockObject(BLACK_BRUSH)));}
 ::StretchDIBits(dc,dx,dy,dw,dh,0,0,LONG(w),LONG(h),px.data(),reinterpret_cast<BITMAPINFO*>(&bi),DIB_RGB_COLORS,SRCCOPY);::ReleaseDC(host.display.window,dc);}
 {static const double menu_period=[]{const char*p=std::getenv("MW34_MENU_FPS");if(!p||!*p)return 0.0;const double v=std::atof(p);return v>=1&&v<=1000?1.0/v:0.0;}();
  if(menu_period>0&&wide_world_frame!=host.frames){
   static LARGE_INTEGER freq{},last{};static HANDLE timer=::CreateWaitableTimerExW(nullptr,nullptr,CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,TIMER_ALL_ACCESS);
   if(!freq.QuadPart)::QueryPerformanceFrequency(&freq);
   LARGE_INTEGER now{};::QueryPerformanceCounter(&now);
   const LONGLONG due=last.QuadPart+LONGLONG(menu_period*double(freq.QuadPart));
   if(last.QuadPart&&now.QuadPart<due){
    const double wait=double(due-now.QuadPart)/double(freq.QuadPart);
    if(wait>0.002&&timer){LARGE_INTEGER d{};d.QuadPart=-LONGLONG((wait-0.0015)*1e7);::SetWaitableTimer(timer,&d,0,nullptr,nullptr,FALSE);::WaitForSingleObject(timer,INFINITE);}
    do ::QueryPerformanceCounter(&now);while(now.QuadPart<due);
    last.QuadPart=due;
   }else last=now;
  }}
 camera_present(flipped_target);
 ++host.frames;mw34_frames_presented.store(host.frames,std::memory_order_relaxed);hud_present();{static const unsigned df=[]{const char*e=std::getenv("MW34_MEM_DUMP_FRAME");return e&&*e?unsigned(std::stoul(e)):0U;}();static const char*dp=std::getenv("MW34_MEM_DUMP");  /* diagnostic: game .data/.bss image at that frame */
 {static const std::string frames_list=[]{const char*e=std::getenv("MW34_MEM_DUMP_FRAMES");return std::string(e?e:"");}();
  if(dp&&!frames_list.empty()&&(","+frames_list+",").find(","+std::to_string(host.frames)+",")!=std::string::npos){
   std::vector<std::byte>b(0x9a2000-0x5e0000);runtime.memory().read({0x5e0000},b);
   if(FILE*f=std::fopen((std::string(dp)+"."+std::to_string(host.frames)+".bin").c_str(),"wb")){std::fwrite(b.data(),1,b.size(),f);std::fclose(f);}
   if(!px.empty())if(FILE*f=std::fopen((std::string(dp)+"."+std::to_string(host.frames)+".frame").c_str(),"wb")){const unsigned hdr[3]={w,h,v.pitch};std::fwrite(hdr,4,3,f);std::fwrite(px.data(),1,px.size(),f);std::fclose(f);}
   // Guest heap (0x50000000..mapped) as a second file.
   const unsigned hb=GuestHeap::lo,he=host.gheap.mapped;if(he>hb){std::vector<std::byte>h(he-hb);
    for(unsigned at=hb;at<he;at+=0x10000){const unsigned n=std::min(0x10000u,he-at);if(readable(at,n)){std::vector<std::byte>c(n);runtime.memory().read({at},c);std::memcpy(h.data()+(at-hb),c.data(),n);}}
    if(FILE*f=std::fopen((std::string(dp)+"."+std::to_string(host.frames)+".heap").c_str(),"wb")){std::fwrite(h.data(),1,h.size(),f);std::fclose(f);}}}}
 if(df&&dp&&host.frames==df){std::vector<std::byte>b(0x9a2000-0x5e0000);runtime.memory().read({0x5e0000},b);if(FILE*f=std::fopen(dp,"wb")){std::fwrite(b.data(),1,b.size(),f);std::fclose(f);}}}if(host.draw_log){{std::fprintf(host.draw_log,"%u %u %016llx up %llu rb %llu hud %llu fb %llu touch %llu hires %llu text %llu log2 %llu exp2 %llu model_up %llu model_bytes %llu model_draw %llu fxaa %llu af_samplers %llu mip_levels %llu\n",host.frames,host.draw_calls,(unsigned long long)host.draw_hash,host.sren?(unsigned long long)host.sren->target_uploads:0ULL,host.sren?(unsigned long long)host.sren->readbacks:0ULL,(unsigned long long)hud_draws_total,(unsigned long long)hud_fallbacks,(unsigned long long)touch_count,(unsigned long long)hires_hits,(unsigned long long)text_hits,mw34_x87_counts[0],mw34_x87_counts[1],host.sren?(unsigned long long)host.sren->model_uploads:0ULL,host.sren?(unsigned long long)host.sren->model_uploaded_bytes:0ULL,host.sren?(unsigned long long)host.sren->model_draws:0ULL,host.sren?(unsigned long long)host.sren->fxaa_passes:0ULL,host.sren?(unsigned long long)host.sren->af_samplers:0ULL,host.sren?(unsigned long long)host.sren->mip_levels_uploaded:0ULL);}host.draw_hash=0xcbf29ce484222325ULL;host.draw_calls=0;}if(host.vclock())host.vclock_us+=host.vclock_step_us;
 platform_present();
 // Opt-in frame timing (MW34_FRAME_TIMES=<file>): one line per presented frame, "frame host_ms 3d_scenes virtual_clock_us".
 static FILE*const frame_times=[]{const char*p=std::getenv("MW34_FRAME_TIMES");return p&&*p?std::fopen(p,"w"):nullptr;}();
 if(frame_times){static const auto t0=std::chrono::steady_clock::now();std::fprintf(frame_times,"%u %.3f %llu %llu\n",host.frames,std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t0).count(),
   static_cast<unsigned long long>(host.sren?host.sren->scenes:0),static_cast<unsigned long long>(host.vclock_us));std::fflush(frame_times);}
 // Keep loading/menu intervals out of the new gameplay measurement window.
 if(host.presenter&&host.presenter->overlay.on){static bool measured_gameplay=false;
  const bool gameplay=host.sren&&host.sren->scenes&&!frontend_on();
  if(gameplay!=measured_gameplay)host.presenter->overlay.reset();measured_gameplay=gameplay;}
 world_present();geometry_profile.present(host.frames);
 if(host.frame_dump&&(host.frames==1||host.frames%host.frame_dump==0))dump_frame(v,px);
 if(host.frame_budget&&host.frames>=host.frame_budget)stop(m4_runtime::FaultReason::unresolved_translation,"Presentation frame budget reached: "+std::to_string(host.frames)+" frames presented ("+std::to_string(host.presenter?host.presenter->presents:0)+(host.presenter&&host.presenter->dxgi_presenting()?" through the Vulkan/DXGI bridge":" through the Vulkan swapchain")+(host.presenter&&host.presenter->presents?" on "+host.presenter->device_name:std::string())+")",host.frames);}
// Evidence: the presented frame as a binary PPM (converted from RGB565) under the run's frame directory.
void dump_frame(const VSurface&v,const std::vector<unsigned char>&px){if(host.frame_dir.empty()||v.bpp!=16)return;std::ofstream f(host.frame_dir+"/frame-"+std::to_string(host.frames)+".ppm",std::ios::binary);
 f<<"P6\n"<<v.width<<" "<<v.height<<"\n255\n";for(unsigned y=0;y<v.height;++y)for(unsigned x=0;x<v.width;++x){const unsigned p=unsigned(px[size_t(y)*v.pitch+2*x])|unsigned(px[size_t(y)*v.pitch+2*x+1])<<8;
  const unsigned char rgb[3]{static_cast<unsigned char>(((p>>11)&31)*255/31),static_cast<unsigned char>(((p>>5)&63)*255/63),static_cast<unsigned char>((p&31)*255/31)};f.write(reinterpret_cast<const char*>(rgb),3);}}
VPalette*vpalette(unsigned g){for(auto&p:host.vpalettes)if(p.guest==g)return &p;return nullptr;}
// Rectangle helpers on guest RECT words (null = whole surface), clipped to the surface.
RECT surf_rect(unsigned a,const VSurface&v){if(!a)return RECT{0,0,LONG(v.width),LONG(v.height)};if(!readable(a,16))deny("Surface rectangle outside the memory contract",a);
 RECT r{LONG(load(a)),LONG(load(a+4)),LONG(load(a+8)),LONG(load(a+12))};if(r.left<0||r.top<0||r.right>LONG(v.width)||r.bottom>LONG(v.height)||r.left>r.right||r.top>r.bottom)deny("Surface rectangle outside the surface",a);return r;}
// Same-format copy with optional source colour key and nearest-neighbour stretch.
// Blt/BltFast/colour fills, row by row: source rows are read once, destination rows are composed and written
// whole (colour-keyed pixels keep the destination pixel); nearest stretching as before. Rectangles must lie
// inside their surfaces.
bool inside(const VSurface&v,const RECT&r){return r.left>=0&&r.top>=0&&r.right<=LONG(v.width)&&r.bottom<=LONG(v.height);}
void blit(const VSurface&d,RECT dr,const VSurface&s,RECT sr,bool key,unsigned klo,unsigned khi){d.version=++host.surface_versions;if(d.bpp!=s.bpp)deny("Blt between surfaces of different depths is not modelled",d.bpp);
 const LONG dw=dr.right-dr.left,dh=dr.bottom-dr.top,sw=sr.right-sr.left,sh=sr.bottom-sr.top;if(dw<=0||dh<=0||sw<=0||sh<=0)return;
 gpu_sync(d.guest);gpu_sync(s.guest);if(!inside(d,dr)||!inside(s,sr))deny("Blt rectangle outside its surface",unsigned(dr.left));const unsigned b=d.bpp/8;if(b!=1&&b!=2&&b!=4)deny("Blt depth not modelled",d.bpp);camera_surface_written(d.guest);
 std::vector<unsigned char>src(size_t(sw)*sh*b),row(size_t(dw)*b);for(LONG y=0;y<sh;++y)surface_read(s,unsigned(sr.top+y)*s.pitch+unsigned(sr.left)*b,src.data()+size_t(y)*sw*b,unsigned(sw)*b);
 for(LONG y=0;y<dh;++y){const LONG sy=y*sh/dh;const unsigned da=unsigned(dr.top+y)*d.pitch+unsigned(dr.left)*b;if(key)surface_read(d,da,row.data(),unsigned(dw)*b);
  for(LONG x=0;x<dw;++x){const unsigned char*p=src.data()+(size_t(sy)*sw+size_t(x*sw/dw))*b;unsigned c=0;std::memcpy(&c,p,b);if(key&&c>=klo&&c<=khi)continue;std::memcpy(row.data()+size_t(x)*b,p,b);}
  surface_write(d,da,row.data(),unsigned(dw)*b);}}
bool resident_current(){auto*rt=vsurface(host.res_rt);auto*zb=host.res_zb?vsurface(host.res_zb):nullptr;return rt&&rt->version==host.res_ver_rt&&(!host.res_zb||(zb&&zb->version==host.res_ver_zb));}
void gpu_fill(const VSurface&d,RECT r,unsigned c){auto*rt=vsurface(host.res_rt);namespace vs=mw34::vkscene;vs::Scene sc{};sc.frontend_canvas=host.sren->frontend_canvas();sc.width=rt->width;sc.height=rt->height;
 // DirectDraw fills use guest surface coordinates, not a preceding world raster scale.
 sc.guest_surface_write=true;
 sc.has_depth=host.res_zb!=0;vs::Clear k{};const bool depth=d.guest==host.res_zb;
 if(depth&&mw34::temporal::enabled()){sc.temporal_frame=camera_flip_serial+1;sc.temporal_target=host.res_rt;}k.flags=depth?2U:1U;k.color[0]=float((c>>11)&31)/31.f;k.color[1]=float((c>>5)&63)/63.f;k.color[2]=float(c&31)/31.f;k.color[3]=1.f;k.z=float(c&0xffff)/65535.f;
 k.rects.push_back({{r.left,r.top},{unsigned(r.right-r.left),unsigned(r.bottom-r.top)}});sc.order.push_back({true,0});sc.clears.push_back(std::move(k));
 try{HostInternal hi(*this);host.sren->render(sc,false,false);}catch(const std::exception&e){deny(std::string(e.what()),0);}
 d.version=++host.surface_versions;if(depth)host.res_ver_zb=d.version;else host.res_ver_rt=d.version;host.res_dirty=true;gpu_protect(true);}
void fill(const VSurface&d,RECT r,unsigned c){if(lazy_rt()&&host.sren&&d.bpp==16&&r.right>r.left&&r.bottom>r.top&&inside(d,r)&&(d.guest==host.res_rt||(host.res_zb&&d.guest==host.res_zb))&&(host.res_dirty||resident_current())){gpu_fill(d,r,c);return;}gpu_sync(d.guest);d.version=++host.surface_versions;if(r.right<=r.left||r.bottom<=r.top)return;if(!inside(d,r))deny("Fill rectangle outside its surface",unsigned(r.left));camera_surface_written(d.guest);
 const unsigned b=d.bpp/8;if(b!=1&&b!=2&&b!=4)deny("Fill depth not modelled",d.bpp);std::vector<unsigned char>row(size_t(r.right-r.left)*b);for(size_t x=0;x<row.size()/b;++x)std::memcpy(row.data()+x*b,&c,b);
 for(LONG y=r.top;y<r.bottom;++y)surface_write(d,unsigned(y)*d.pitch+unsigned(r.left)*b,row.data(),unsigned(row.size()));}

void*vdd_create_surface(unsigned out,unsigned a,unsigned dsize,const std::function<void*(unsigned,unsigned)>&done){const DDSURFACEDESC2 d=get_desc(a,dsize);const unsigned caps=d.ddsCaps.dwCaps;
 if(!writable(out,4))deny("CreateSurface output outside the memory contract",out);if(!host.display.width)deny("CreateSurface before the virtual display mode is set",a);
 const auto&iface=*com::by_name(dsize==124?"IDirectDrawSurface4":"IDirectDrawSurface");std::string what;
 if(caps&DDSCAPS_PRIMARYSURFACE){if(d.dwFlags&(DDSD_WIDTH|DDSD_HEIGHT))deny("Primary surface with explicit size",a);
  const unsigned front=make_surface(host.display.width,host.display.height,host.display.bpp,(caps&~DDSCAPS_BACKBUFFER)|DDSCAPS_FRONTBUFFER|DDSCAPS_VISIBLE|DDSCAPS_VIDEOMEMORY,iface);vsurface(front)->primary=true;
  if(caps&DDSCAPS_FLIP){if(!(d.dwFlags&DDSD_BACKBUFFERCOUNT)||d.dwBackBufferCount!=1)deny("Flip chains other than one back buffer are not modelled",d.dwBackBufferCount);
   const unsigned back=make_surface(host.display.width,host.display.height,host.display.bpp,(caps&~(DDSCAPS_PRIMARYSURFACE|DDSCAPS_FRONTBUFFER|DDSCAPS_VISIBLE))|DDSCAPS_BACKBUFFER|DDSCAPS_VIDEOMEMORY,iface);
   vsurface(front)->attached=back;what="primary+back";}else what="primary";store(out,front);}
 else if(caps&DDSCAPS_ZBUFFER){if(!(d.dwFlags&DDSD_WIDTH)||!(d.dwFlags&DDSD_HEIGHT)||!(d.dwFlags&DDSD_PIXELFORMAT)||d.ddpfPixelFormat.dwRGBBitCount!=16)deny("Z-buffer other than 16-bit is not modelled",a);
  const unsigned g=make_surface(d.dwWidth,d.dwHeight,16,caps|DDSCAPS_VIDEOMEMORY,iface);vsurface(g)->tex_masks={0,0,0,0xffff};what="z-buffer";store(out,g);}
 else if(caps&DDSCAPS_TEXTURE){if(!(d.dwFlags&DDSD_WIDTH)||!(d.dwFlags&DDSD_HEIGHT)||!(d.dwFlags&DDSD_PIXELFORMAT)||d.ddpfPixelFormat.dwRGBBitCount!=16)deny("Texture format other than 16-bit is not modelled",a);
  const auto&pf=d.ddpfPixelFormat;bool ok=false;for(const auto&f:texture_formats())if(pf.dwRBitMask==f[4]&&pf.dwGBitMask==f[5]&&pf.dwBBitMask==f[6]&&((pf.dwFlags&DDPF_ALPHAPIXELS)?pf.dwRGBAlphaBitMask:0)==f[7])ok=true;if(!ok)deny("Texture pixel format outside the provider formats",pf.dwGBitMask);
  const unsigned g=make_surface(d.dwWidth,d.dwHeight,16,caps,iface);vsurface(g)->tex_masks={pf.dwRBitMask,pf.dwGBitMask,pf.dwBBitMask,(pf.dwFlags&DDPF_ALPHAPIXELS)?pf.dwRGBAlphaBitMask:0};
  if(d.dwFlags&DDSD_CKSRCBLT){auto*vv=vsurface(g);vv->has_src_key=true;vv->src_key=d.ddckCKSrcBlt;}what="texture "+std::to_string(d.dwWidth)+"x"+std::to_string(d.dwHeight);store(out,g);}
 else if(caps&(DDSCAPS_OFFSCREENPLAIN|DDSCAPS_SYSTEMMEMORY|DDSCAPS_VIDEOMEMORY|DDSCAPS_3DDEVICE)){if(!(d.dwFlags&DDSD_WIDTH)||!(d.dwFlags&DDSD_HEIGHT))deny("Offscreen surface without a size",a);
  unsigned bpp=host.display.bpp;if(d.dwFlags&DDSD_PIXELFORMAT){bpp=d.ddpfPixelFormat.dwRGBBitCount;if(bpp==16&&(d.ddpfPixelFormat.dwGBitMask!=0x07e0))deny("Offscreen pixel format other than RGB565 is not modelled",d.ddpfPixelFormat.dwGBitMask);}
  const unsigned g=make_surface(d.dwWidth,d.dwHeight,bpp,caps|((caps&DDSCAPS_SYSTEMMEMORY)?0:DDSCAPS_VIDEOMEMORY),iface);if(d.dwFlags&DDSD_CKSRCBLT){auto*v=vsurface(g);v->has_src_key=true;v->src_key=d.ddckCKSrcBlt;}
  what="offscreen "+std::to_string(d.dwWidth)+"x"+std::to_string(d.dwHeight);store(out,g);}
 else deny("CreateSurface caps outside the virtual display model (texture/z-buffer/3D device need the Direct3D provider): "+std::to_string(caps),caps);
 apis.back()+="(virtual "+what+")";return done(DD_OK,4);}

#include "status_preview_clear_stage.inc"
void*vdd_surface(const Import&imp,unsigned token,const std::function<unsigned(unsigned)>&arg,const std::function<void*(unsigned,unsigned)>&done){const std::string&n=imp.name;
 auto*v=vsurf_of(arg(0));if(!v)deny("Surface call on an object that is not a live virtual surface",arg(0));const unsigned dsize=imp.dll=="IDirectDrawSurface4"?124U:108U;
 if(n=="AddRef")return done(++host.com_object(v->guest)->refs,1);
 if(n=="Release"){auto&r=host.com_object(v->guest)->refs;const unsigned c=--r;if(!c){for(auto&x:host.com_objects)if(x.alive&&root_of(x)==v->guest)x.alive=false;if(v->attached)if(auto*b=vsurface(v->attached)){for(auto&x:host.com_objects)if(x.alive&&root_of(x)==b->guest)x.alive=false;}}return done(c,1);}
 if(n=="QueryInterface"&&IsEqualGUID(guest_guid(arg(1)),IID_IDirect3DTexture2)){if(!(v->caps&DDSCAPS_TEXTURE))deny("Texture interface on a non-texture surface",v->guest);if(!writable(arg(2),4))deny("QueryInterface output outside the memory contract",arg(2));
  ++host.com_object(v->guest)->refs;store(arg(2),com_wrap(nullptr,*com::by_name("IDirect3DTexture2"),v->guest));return done(DD_OK,3);}
 if(n=="AddAttachedSurface"){auto*z=vsurf_of(arg(1));if(!z||!(z->caps&DDSCAPS_ZBUFFER))deny("AddAttachedSurface of a non-z-buffer surface is not modelled",arg(1));v->zbuffer=z->guest;++host.com_object(z->guest)->refs;return done(DD_OK,2);}
 if(n=="DeleteAttachedSurface"){if(arg(1))deny("DeleteAttachedSurface flags are not modelled",arg(1));if(v->zbuffer&&vsurf_root(arg(2))==v->zbuffer){--host.com_object(v->zbuffer)->refs;v->zbuffer=0;return done(DD_OK,3);}return done(unsigned(DDERR_SURFACENOTATTACHED),3);}
 if(n=="QueryInterface"){const GUID g=guest_guid(arg(1));const auto*wi=com::by_iid(g);if(!wi||std::string(wi->name).find("Surface")==std::string::npos)deny("Surface QueryInterface for an interface outside the virtual display model",arg(1));
  if(!writable(arg(2),4))deny("QueryInterface output outside the memory contract",arg(2));++host.com_object(v->guest)->refs;store(arg(2),com_wrap(nullptr,*wi,v->guest));return done(DD_OK,3);}
 if(n=="GetAttachedSurface"){const unsigned c=arg(1),out=arg(2);if(!readable(c,4)||!writable(out,4))deny("GetAttachedSurface arguments outside the memory contract",c);const unsigned want=load(c);
  if(!(want&DDSCAPS_BACKBUFFER)||!v->attached){store(out,0);return done(unsigned(DDERR_NOTFOUND),3);}++host.com_object(v->attached)->refs;store(out,v->attached);return done(DD_OK,3);}
 if(n=="Lock"){const unsigned rect=arg(1),desc=arg(2),flags=arg(3);if(arg(4))deny("Lock event handle is not modelled",arg(4));if(!readable(desc,4)||load(desc)!=dsize)deny("Lock descriptor with a wrong dwSize",desc);
  if(gpu_hud()&&lazy_rt()&&host.sren&&host.res_dirty&&v->guest==host.res_rt&&!hud_gpu_active)hud_begin(*v);else gpu_sync(v->guest);
  const bool gpu_hud_lock=hud_gpu_active&&v->guest==host.res_rt;if(!(flags&DDLOCK_READONLY)&&!gpu_hud_lock)camera_surface_written(v->guest);
  const RECT r=surf_rect(rect,*v);texture_lock_pages(*v);DDSURFACEDESC2 d{};fill_desc(*v,d);put_desc(desc,d,dsize);store(desc+36,v->mem+unsigned(r.top)*v->pitch+unsigned(r.left)*(v->bpp/8));store(desc+4,load(desc+4)|DDSD_LPSURFACE);v->lock_access.acquire((flags&DDLOCK_READONLY)!=0,gpu_hud_lock);++v->locks;(void)flags;
  {static const bool watch=[]{const char*e=std::getenv("MW34_HUD_WATCH");return e&&*e;}();if(watch&&v->width>=640&&v->height>=480&&v->bpp==16&&!hud_watch_hi){auto*b=reinterpret_cast<std::byte*>(runtime.memory().flat_base());if(b){hud_watch_lo=reinterpret_cast<std::uintptr_t>(b+v->mem);hud_watch_hi=hud_watch_lo+std::uintptr_t(v->pitch)*v->height;DWORD old{};::VirtualProtect(reinterpret_cast<void*>(hud_watch_lo&~std::uintptr_t(4095)),(hud_watch_hi-(hud_watch_lo&~std::uintptr_t(4095))+4095)&~std::uintptr_t(4095),PAGE_READONLY,&old);}}}
  return done(DD_OK,5);}
 if(n=="Unlock"){if(!v->locks)return done(unsigned(DDERR_NOTLOCKED),2);if(hud_gpu_active&&v->guest==host.res_rt){hud_flush();hud_gpu_active=false;--v->locks;if(v->lock_access.release(!v->locks))v->version=++host.surface_versions;return done(DD_OK,2);}if(hud_watch_hi){DWORD old{};::VirtualProtect(reinterpret_cast<void*>(hud_watch_lo&~std::uintptr_t(4095)),(hud_watch_hi-(hud_watch_lo&~std::uintptr_t(4095))+4095)&~std::uintptr_t(4095),PAGE_READWRITE,&old);hud_watch_lo=hud_watch_hi=0;if(host.frames%25==0)hud_watch_save();}--v->locks;if(!v->locks)texture_unlock_pages(*v);if(v->lock_access.release(!v->locks))v->version=++host.surface_versions;return done(DD_OK,2);}
 if(n=="Flip"){if(!v->primary||!v->attached)deny("Flip on a surface without a flip chain",v->guest);if(arg(1))deny("Flip with an explicit target is not modelled",arg(1));auto*b=vsurface(v->attached);{const unsigned next=host.frames+1;const bool dump_due=host.frame_dump&&(next==1||next%host.frame_dump==0);
  present_direct=lazy_rt()&&host.res_dirty&&b->guest==host.res_rt&&host.sren&&host.presenter&&host.sren==host.presenter.get()&&!dump_due;}
  /* the guest memories swap: the protection follows the resident surface (b keeps the GPU image as its content) */
  if(!present_direct){gpu_sync(b->guest);gpu_sync(v->guest);}else gpu_protect(false);std::swap(v->mem,b->mem);if(present_direct)gpu_protect(true);v->version=++host.surface_versions;b->version=++host.surface_versions;present(*v,b->guest);present_direct=false;return done(DD_OK,3);}
 if(n=="Blt"){const unsigned dr=arg(1),src=arg(2),sr=arg(3),flags=arg(4),fx=arg(5);const RECT dst=surf_rect(dr,*v);
  if(flags&DDBLT_DEPTHFILL){if(!(v->caps&DDSCAPS_ZBUFFER))deny("Depth fill on a non-z-buffer surface",v->guest);if(!readable(fx,100))deny("Blt depth fill without its DDBLTFX",fx);fill(*v,status_preview_depth_rect(dst,v->width,v->height),load(fx+80)&0xffff);return done(DD_OK,6);}
  if(flags&DDBLT_COLORFILL){if(!readable(fx,100))deny("Blt colour fill without its DDBLTFX",fx);fill(*v,dst,load(fx+80));if(v->primary&&!v->attached)present(*v);return done(DD_OK,6);}
  if(flags&~(DDBLT_WAIT|DDBLT_KEYSRC|DDBLT_ASYNC|DDBLT_DONOTWAIT))deny("Blt flags outside the virtual display model: "+std::to_string(flags),flags);auto*s=vsurf_of(src);if(!s)deny("Blt source is not a virtual surface",src);
  const bool key=(flags&DDBLT_KEYSRC)&&s->has_src_key;blit(*v,dst,*s,surf_rect(sr,*s),key,s->src_key.dwColorSpaceLowValue,s->src_key.dwColorSpaceHighValue);if(v->primary&&!v->attached)present(*v);return done(DD_OK,6);}
 if(n=="BltFast"){const unsigned x=arg(1),y=arg(2),src=arg(3),sr=arg(4),trans=arg(5);auto*s=vsurf_of(src);if(!s)deny("BltFast source is not a virtual surface",src);const RECT srect=surf_rect(sr,*s);
  if(trans&~(DDBLTFAST_SRCCOLORKEY|DDBLTFAST_WAIT|DDBLTFAST_NOCOLORKEY))deny("BltFast flags outside the virtual display model",trans);const RECT d{LONG(x),LONG(y),LONG(x)+(srect.right-srect.left),LONG(y)+(srect.bottom-srect.top)};
  if(d.right>LONG(v->width)||d.bottom>LONG(v->height))deny("BltFast outside the destination",x);const bool key=(trans&DDBLTFAST_SRCCOLORKEY)&&s->has_src_key;blit(*v,d,*s,srect,key,s->src_key.dwColorSpaceLowValue,s->src_key.dwColorSpaceHighValue);
  if(v->primary&&!v->attached)present(*v);return done(DD_OK,6);}
 if(n=="GetPixelFormat"){const unsigned a=arg(1);if(!writable(a,32))deny("GetPixelFormat output outside the memory contract",a);const DDPIXELFORMAT f=surface_format(*v);std::array<unsigned,8>w{};std::memcpy(w.data(),&f,32);for(unsigned i=0;i<8;++i)store(a+4*i,w[i]);return done(DD_OK,2);}
 if(n=="GetSurfaceDesc"){const unsigned a=arg(1);if(!readable(a,4)||load(a)!=dsize)deny("GetSurfaceDesc descriptor with a wrong dwSize",a);DDSURFACEDESC2 d{};fill_desc(*v,d);put_desc(a,d,dsize);return done(DD_OK,2);}
 if(n=="GetCaps"){const unsigned a=arg(1);if(!writable(a,dsize==124?16:4))deny("GetCaps output outside the memory contract",a);store(a,v->caps);if(dsize==124){store(a+4,0);store(a+8,0);store(a+12,0);}return done(DD_OK,2);}
 if(n=="IsLost"||n=="Restore"||n=="PageLock"||n=="PageUnlock"||n=="GetFlipStatus"||n=="GetBltStatus")return done(DD_OK,n=="IsLost"||n=="Restore"?1:2);
 if(n=="SetColorKey"||n=="GetColorKey"){const unsigned fl=arg(1),a=arg(2);if(!(fl&(DDCKEY_SRCBLT|DDCKEY_DESTBLT))||(fl&~(DDCKEY_SRCBLT|DDCKEY_DESTBLT|DDCKEY_COLORSPACE)))deny("Colour key kind not modelled",fl);auto&k=(fl&DDCKEY_SRCBLT)?v->src_key:v->dst_key;auto&has=(fl&DDCKEY_SRCBLT)?v->has_src_key:v->has_dst_key;
  if(n=="SetColorKey"){if(!a){has=false;return done(DD_OK,3);}if(!readable(a,8))deny("Colour key outside the memory contract",a);k.dwColorSpaceLowValue=load(a);k.dwColorSpaceHighValue=(fl&DDCKEY_COLORSPACE)?load(a+4):load(a);has=true;return done(DD_OK,3);}
  if(!has)return done(unsigned(DDERR_NOCOLORKEY),3);if(!writable(a,8))deny("Colour key outside the memory contract",a);store(a,k.dwColorSpaceLowValue);store(a+4,k.dwColorSpaceHighValue);return done(DD_OK,3);}
 if(n=="SetClipper"){v->clipper=arg(1);return done(DD_OK,2);}
 if(n=="GetClipper"){if(!writable(arg(1),4))deny("GetClipper output outside the memory contract",arg(1));if(!v->clipper)return done(unsigned(DDERR_NOCLIPPERATTACHED),2);store(arg(1),v->clipper);return done(DD_OK,2);}
 if(n=="SetPalette"){if(arg(1)&&!vpalette(vsurf_root(arg(1))))deny("SetPalette with an object that is not a virtual palette",arg(1));v->palette=arg(1)?vsurf_root(arg(1)):0;return done(DD_OK,2);}
 if(n=="GetDDInterface")deny("Surface GetDDInterface is not modelled",0);
 stop(m4_runtime::FaultReason::unresolved_import,"Virtual surface method not implemented: "+imp.dll+"::"+n,token);}

void*vdd_aux(const Import&imp,unsigned token,const std::function<unsigned(unsigned)>&arg,const std::function<void*(unsigned,unsigned)>&done){const std::string&n=imp.name;auto*o=host.com_object(arg(0));
 if(!o)deny("Call on an object that is not a live virtual "+imp.dll,arg(0));
 if(n=="AddRef")return done(++o->refs,1);
 if(n=="Release"){const unsigned c=--o->refs;if(!c){o->alive=false;host.clippers.erase(o->guest);}return done(c,1);}
 if(imp.dll=="IDirectDrawClipper"){if(n=="SetHWnd"){if(arg(1))deny("Clipper flags are not modelled",arg(1));host.clippers[o->guest]=arg(2);return done(DD_OK,3);}
  if(n=="GetHWnd"){if(!writable(arg(1),4))deny("GetHWnd output outside the memory contract",arg(1));store(arg(1),host.clippers[o->guest]);return done(DD_OK,2);}}
 if(imp.dll=="IDirectDrawPalette"){auto*p=vpalette(o->guest);if(!p)deny("Palette object without its entries",o->guest);
  if(n=="SetEntries"||n=="GetEntries"){const unsigned first=arg(2),count=arg(3),a=arg(4);if(arg(1)||first+count>256||!(n=="SetEntries"?readable(a,4*count):writable(a,4*count)))deny(n+" arguments outside the model",a);
   if(n=="SetEntries")get_bytes(a,p->entries+first,4*count);else for(unsigned i=0;i<4*count;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(p->entries+first)[i]);return done(DD_OK,5);}
  if(n=="GetCaps"){if(!writable(arg(1),4))deny("Palette GetCaps output outside the memory contract",arg(1));store(arg(1),p->flags);return done(DD_OK,2);}}
 stop(m4_runtime::FaultReason::unresolved_import,"Virtual "+imp.dll+" method not implemented: "+n,token);}

