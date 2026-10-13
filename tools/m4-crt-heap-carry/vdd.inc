// Virtual display surfaces (project presentation provider; included inside mf::Stage).
// Surfaces are guest COM objects whose pixel memory lives in guest pages, so Lock hands the game a
// guest pointer and the game's own (recompiled) renderer writes the pixels. Flip swaps the surface
// memory of the front buffer and its attached back buffer (DirectDraw flip semantics) and presents the
// front buffer to the game window. Blt/BltFast implement colour fill, copy, source colour key and
// nearest stretch for same-format surfaces. Anything outside this model stops typed.

using VSurface=VSurfaceRec;using VPalette=VPaletteRec;
VSurface*vsurface(unsigned g){for(auto&v:host.vsurfaces)if(v.guest==g)return &v;return nullptr;}
unsigned vsurf_root(unsigned g){const auto*o=host.com_object(g);return o?root_of(*o):g;}
VSurface*vsurf_of(unsigned g){return vsurface(vsurf_root(g));}
unsigned surface_pages(unsigned bytes){const unsigned n=(std::max(bytes,1U)+4095U)&~4095U;if(host.vsurface_next==0)host.vsurface_next=vsurface_arena;const unsigned g=host.vsurface_next;
 if(std::uint64_t(g)+n>vsurface_arena_end)deny("Virtual surface arena exhausted",g);host.vsurface_next+=n;bool bad{};try{runtime.memory().map({g},n,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked surface memory mapping",g);return g;}
unsigned make_surface(unsigned w,unsigned h,unsigned bpp,unsigned caps,const com::Iface&iface){const unsigned pitch=((w*bpp/8)+3U)&~3U,bytes=pitch*h;
 const unsigned g=com_wrap(nullptr,iface);host.com_object(g)->refs=1;host.vsurfaces.push_back({g,w,h,pitch,bpp,caps,surface_pages(bytes),bytes,0,0,0});host.vsurfaces.back().version=++host.surface_versions;return g;}
DDPIXELFORMAT surface_format(const VSurface&v){if(v.caps&(DDSCAPS_TEXTURE|DDSCAPS_ZBUFFER)){DDPIXELFORMAT f{};f.dwSize=sizeof(f);f.dwRGBBitCount=16;
  if(v.caps&DDSCAPS_ZBUFFER){f.dwFlags=DDPF_ZBUFFER;f.dwRBitMask=0;f.dwGBitMask=0xffff;return f;}f.dwFlags=DDPF_RGB|(v.tex_masks[3]?DDPF_ALPHAPIXELS:0);f.dwRBitMask=v.tex_masks[0];f.dwGBitMask=v.tex_masks[1];f.dwBBitMask=v.tex_masks[2];f.dwRGBAlphaBitMask=v.tex_masks[3];return f;}
 return virtual_format(v.bpp);}
void fill_desc(const VSurface&v,DDSURFACEDESC2&d){d={};d.dwSize=sizeof(d);d.dwFlags=DDSD_CAPS|DDSD_WIDTH|DDSD_HEIGHT|DDSD_PITCH|DDSD_PIXELFORMAT;d.dwWidth=v.width;d.dwHeight=v.height;d.lPitch=LONG(v.pitch);
 d.ddpfPixelFormat=surface_format(v);d.ddsCaps.dwCaps=v.caps;if(v.attached){d.dwFlags|=DDSD_BACKBUFFERCOUNT;d.dwBackBufferCount=1;}if(v.has_src_key){d.dwFlags|=DDSD_CKSRCBLT;d.ddckCKSrcBlt=v.src_key;}}
// Presentation of the front buffer (RGB565 / palettized) into the game window's client area.
void present(const VSurface&v){if(!host.display.window)deny("Presentation without a cooperative window",v.guest);const unsigned w=v.width,h=v.height;
 std::vector<unsigned char>px(size_t(v.pitch)*h);get_bytes(v.mem,px.data(),unsigned(px.size()));
 struct{BITMAPINFOHEADER h;DWORD masks[256];}bi{};bi.h.biSize=sizeof(BITMAPINFOHEADER);bi.h.biWidth=LONG(v.pitch/(v.bpp/8));bi.h.biHeight=-LONG(h);bi.h.biPlanes=1;bi.h.biBitCount=WORD(v.bpp);
 if(v.bpp==16){bi.h.biCompression=BI_BITFIELDS;bi.masks[0]=0xf800;bi.masks[1]=0x07e0;bi.masks[2]=0x001f;}else if(v.bpp==8){const auto*pal=vpalette(v.palette);if(!pal)deny("8-bit presentation without a palette",v.guest);
  for(unsigned i=0;i<256;++i)bi.masks[i]=RGB(pal->entries[i].peBlue,pal->entries[i].peGreen,pal->entries[i].peRed);bi.h.biClrUsed=256;}else deny("Presentation depth not modelled",v.bpp);
 // 16-bit frames are presented by the Vulkan swapchain presenter unless MW34_PRESENT=gdi; the GDI presenter
 // serves 8-bit frames and devices without window presentation.
 static const bool gdi_only=[]{const char*p=std::getenv("MW34_PRESENT");return p&&std::string(p)=="gdi";}();bool shown=false;
 if(v.bpp==16&&!gdi_only){if(!host.presenter)host.presenter=std::make_unique<mw34::vkscene::Renderer>();try{HostInternal hi(*this);shown=host.presenter->present(host.display.window,px.data(),w,h,v.pitch);}catch(const std::exception&e){deny(std::string(e.what()),v.guest);}
  if(shown&&host.presenter->presents==1)apis.back()+="(Vulkan presenter on "+host.presenter->device_name+")";}
 if(!shown){RECT rc{};::GetClientRect(host.display.window,&rc);HDC dc=::GetDC(host.display.window);::SetStretchBltMode(dc,COLORONCOLOR);
 ::StretchDIBits(dc,0,0,rc.right,rc.bottom,0,0,LONG(w),LONG(h),px.data(),reinterpret_cast<BITMAPINFO*>(&bi),DIB_RGB_COLORS,SRCCOPY);::ReleaseDC(host.display.window,dc);}
 ++host.frames;mw34_frames_presented.store(host.frames,std::memory_order_relaxed);if(host.frame_dump&&(host.frames==1||host.frames%host.frame_dump==0))dump_frame(v,px);
 if(host.frame_budget&&host.frames>=host.frame_budget)stop(m4_runtime::FaultReason::unresolved_translation,"Presentation frame budget reached: "+std::to_string(host.frames)+" frames presented ("+std::to_string(host.presenter?host.presenter->presents:0)+" through the Vulkan swapchain"+(host.presenter&&host.presenter->presents?" on "+host.presenter->device_name:std::string())+")",host.frames);}
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
 if(!inside(d,dr)||!inside(s,sr))deny("Blt rectangle outside its surface",unsigned(dr.left));const unsigned b=d.bpp/8;if(b!=1&&b!=2&&b!=4)deny("Blt depth not modelled",d.bpp);
 std::vector<unsigned char>src(size_t(sw)*sh*b),row(size_t(dw)*b);for(LONG y=0;y<sh;++y)get_bytes(s.mem+unsigned(sr.top+y)*s.pitch+unsigned(sr.left)*b,src.data()+size_t(y)*sw*b,unsigned(sw)*b);
 for(LONG y=0;y<dh;++y){const LONG sy=y*sh/dh;const unsigned da=d.mem+unsigned(dr.top+y)*d.pitch+unsigned(dr.left)*b;if(key)get_bytes(da,row.data(),unsigned(dw)*b);
  for(LONG x=0;x<dw;++x){const unsigned char*p=src.data()+(size_t(sy)*sw+size_t(x*sw/dw))*b;unsigned c=0;std::memcpy(&c,p,b);if(key&&c>=klo&&c<=khi)continue;std::memcpy(row.data()+size_t(x)*b,p,b);}
  write_bytes(da,row.data(),unsigned(dw)*b);}}
void fill(const VSurface&d,RECT r,unsigned c){d.version=++host.surface_versions;if(r.right<=r.left||r.bottom<=r.top)return;if(!inside(d,r))deny("Fill rectangle outside its surface",unsigned(r.left));
 const unsigned b=d.bpp/8;if(b!=1&&b!=2&&b!=4)deny("Fill depth not modelled",d.bpp);std::vector<unsigned char>row(size_t(r.right-r.left)*b);for(size_t x=0;x<row.size()/b;++x)std::memcpy(row.data()+x*b,&c,b);
 for(LONG y=r.top;y<r.bottom;++y)write_bytes(d.mem+unsigned(y)*d.pitch+unsigned(r.left)*b,row.data(),unsigned(row.size()));}

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
  const RECT r=surf_rect(rect,*v);DDSURFACEDESC2 d{};fill_desc(*v,d);put_desc(desc,d,dsize);store(desc+36,v->mem+unsigned(r.top)*v->pitch+unsigned(r.left)*(v->bpp/8));store(desc+4,load(desc+4)|DDSD_LPSURFACE);++v->locks;(void)flags;return done(DD_OK,5);}
 if(n=="Unlock"){if(!v->locks)return done(unsigned(DDERR_NOTLOCKED),2);--v->locks;v->version=++host.surface_versions;return done(DD_OK,2);}
 if(n=="Flip"){if(!v->primary||!v->attached)deny("Flip on a surface without a flip chain",v->guest);if(arg(1))deny("Flip with an explicit target is not modelled",arg(1));auto*b=vsurface(v->attached);std::swap(v->mem,b->mem);v->version=++host.surface_versions;b->version=++host.surface_versions;present(*v);return done(DD_OK,3);}
 if(n=="Blt"){const unsigned dr=arg(1),src=arg(2),sr=arg(3),flags=arg(4),fx=arg(5);const RECT dst=surf_rect(dr,*v);
  if(flags&DDBLT_DEPTHFILL){if(!(v->caps&DDSCAPS_ZBUFFER))deny("Depth fill on a non-z-buffer surface",v->guest);if(!readable(fx,100))deny("Blt depth fill without its DDBLTFX",fx);fill(*v,dst,load(fx+80)&0xffff);return done(DD_OK,6);}
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
