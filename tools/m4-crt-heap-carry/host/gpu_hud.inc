// GPU HUD (MW34_GPU_HUD=1 with MW34_LAZY_RT=1; included inside mf::Stage). docs/hud-vulkan-integration-handoff.md.
// The game's own HUD code still runs and decides every element, value and position. While it holds the resident 3D
// target locked, its software raster primitives (image blit 0x55B3C0, line 0x563B80, clipped line 0x563DB0,
// circle 0x5630C0, pixel 0x5630A0/0x5641F0, span 0x564080)
// are not executed: each call is recorded as host draws (textured or coloured pre-transformed vertices) and returns to its
// caller with the callee's stack cleanup. At Unlock the recorded draws render onto the resident target through the scene
// renderer, so the HUD never touches guest pixels. Anything else (an image layout outside this model, or a draw into a
// different buffer) falls back: the draws so far are rendered, guest memory is synchronized and the rest of the lock runs
// on the CPU. A raw guest access to the stale target outside these primitives stops typed (page protection).
// HUD pixels are not bit-identical with the 16-bit software blends (straight alpha from the image mask); the HUD's logic
// and the 3D scene are. Lines and circles keep the software rasterization steps (one-pixel points).
static bool gpu_hud(){static const bool on=[]{const char*e=std::getenv("MW34_GPU_HUD");return e&&*e=='1';}();return on;}
bool hud_gpu_active{};unsigned hud_rt_mem{},hud_w{},hud_h{},hud_pitch{};
mw34::vkscene::Scene hud_sc{};std::map<std::uint64_t,int>hud_tex_index;
std::uint64_t hud_draws_total{},hud_fallbacks{},hud_noise_calls{},hud_jitter_calls{};unsigned hud_noise_slot{};bool hud_noise_reject_logged{},hud_jitter_reject_logged{},hud_jitter_line_reject_logged{};
void hud_begin(VSurface&rt){hud_gpu_active=true;hud_rt_mem=rt.mem;hud_w=rt.width;hud_h=rt.height;hud_pitch=rt.pitch;
 hud_sc=mw34::vkscene::Scene{};hud_sc.hud=true;hud_sc.frontend_canvas=host.sren&&host.sren->frontend_canvas();hud_sc.width=rt.width;hud_sc.height=rt.height;hud_sc.has_depth=host.res_zb!=0;hud_tex_index.clear();hud_noise_slot=0;}
static std::uint32_t hud_rgba(unsigned c,unsigned a){const std::uint32_t r=((c>>11)&31)*255/31,g=((c>>5)&63)*255/63,b=(c&31)*255/31;return r|g<<8|b<<16|std::uint32_t(a)<<24;}
static std::uint32_t hud_argb(unsigned c){const std::uint32_t r=((c>>11)&31)*255/31,g=((c>>5)&63)*255/63,b=(c&31)*255/31;return 0xff000000u|r<<16|g<<8|b;}
// One pre-transformed vertex (x, y, z, rhw, diffuse ARGB, specular, u, v), D3D pixel-centre convention.
void hud_vertex(float x,float y,std::uint32_t argb,float u,float v){float f[8]{x,y,0.f,1.f,0,0,u,v};std::memcpy(&f[4],&argb,4);const auto*b=reinterpret_cast<const unsigned char*>(f);hud_sc.vertices.insert(hud_sc.vertices.end(),b,b+32);}
void hud_draw(int tex,bool points,unsigned first,unsigned role_hint=~0U,const int*clip=nullptr,const float*center_hint=nullptr){namespace vs=mw34::vkscene;vs::Draw dr{};dr.first=first;dr.count=unsigned(hud_sc.vertices.size()/32)-first;if(!dr.count)return;dr.texture=tex;
 dr.sampler=(D3DTADDRESS_CLAMP<<4)|(D3DTADDRESS_CLAMP<<8);  // point sampling, clamped
 dr.key={1,D3DBLEND_SRCALPHA,D3DBLEND_INVSRCALPHA,0,D3DCMP_ALWAYS,0,D3DCULL_NONE,std::uint8_t(points?1:0)};
 auto&pu=dr.push;pu.target[0]=float(hud_w);pu.target[1]=float(hud_h);pu.target[2]=0.5f;pu.fog[3]=1;pu.factor[0]=pu.factor[1]=pu.factor[2]=pu.factor[3]=1;
 pu.mode[0]=tex>=0?4U:0U;const unsigned arg=tex>=0?D3DTA_TEXTURE:D3DTA_DIFFUSE;pu.mode[1]=D3DTOP_SELECTARG1|arg<<8|D3DTA_DIFFUSE<<16;pu.mode[2]=D3DTOP_SELECTARG1|arg<<8|D3DTA_DIFFUSE<<16;pu.mode[3]=0;
 dr.scissor={{0,0},{hud_w,hud_h}};
 if(clip)dr.scissor={{clip[0],clip[1]},{unsigned(clip[2]-clip[0]+1),unsigned(clip[3]-clip[1]+1)}};
 unsigned role=role_hint==~0U?wide_hud_role():role_hint;if(!role&&tex>=0)role=WideReticle;
 if(wide_on()&&host.frames==999){if(FILE*log=wide_log_file()){std::fprintf(log,"hud frame %u role %u texture %d count %u ret %06x bt",host.frames,role,tex,dr.count,load(state.gpr.rsp.dword));for(unsigned i=depth;i>0&&i+14>depth;--i)std::fprintf(log," %06x",returns[i-1]);std::fprintf(log,"\n");}}
 const float zoom_anchor=wide_on()&&role==WideZoom?(target_marker_draw_owner?target_marker_anchor():zoom_display_anchor()):0.f;
 wide_adapt_tl(hud_sc,dr,role,role==WideZoom?&zoom_anchor:center_hint);hud_sc.order.push_back({false,unsigned(hud_sc.draws.size())});hud_sc.draws.push_back(dr);++hud_draws_total;}
// A segment as a quad one game pixel wide (pixel-centre coordinates), extended half a pixel past both ends; it stays a
// continuous line at any render scale.
void hud_segment(float x0,float y0,float x1,float y1,std::uint32_t c){float dx=x1-x0,dy=y1-y0;const float len=std::sqrt(dx*dx+dy*dy);
 if(len<1e-3f){dx=1;dy=0;}else{dx/=len;dy/=len;}const float nx=-dy*0.5f,ny=dx*0.5f,ex=dx*0.5f,ey=dy*0.5f;
 const float ax=x0-ex+nx,ay=y0-ey+ny,bx=x1+ex+nx,by=y1+ey+ny,cx=x1+ex-nx,cy=y1+ey-ny,qx=x0-ex-nx,qy=y0-ey-ny;
 hud_vertex(ax,ay,c,0,0);hud_vertex(bx,by,c,0,0);hud_vertex(cx,cy,c,0,0);hud_vertex(ax,ay,c,0,0);hud_vertex(cx,cy,c,0,0);hud_vertex(qx,qy,c,0,0);}
void hud_point(int x,int y,std::uint32_t argb){if(x<0||y<0||unsigned(x)>=hud_w||unsigned(y)>=hud_h)return;hud_vertex(float(x),float(y),argb,0,0);}
// Hi-res HUD pack (tools/vulkan-hud/build_hires_pack.py; default <project>/local/hires-pack/hud, MW34_HIRES_HUD=<dir>,
// MW34_HIRES_HUD=0 disables): an in-game image whose identity key matches a pack file is drawn from that higher-density
// texture at the image's logical size (the game's position and crop are kept). Key: FNV-1a 64 over width and height
// (u32 LE), then per pixel the RGB565 word when opaque and 0 when transparent (mask value 0, or the colour key).
struct HiresTex{unsigned w{},h{};float u0{},v0{},u1{},v1{};std::vector<std::uint32_t>px;};
std::map<std::uint64_t,HiresTex>hires;bool hires_loaded{};std::uint64_t hires_hits{};
void hires_load(){hires_loaded=true;const char*e=std::getenv("MW34_HIRES_HUD");if(e&&std::string(e)=="0")return;std::filesystem::path dir;
 if(e&&*e)dir=e;else{const auto exe=host.paths.find(0x400000U);if(exe==host.paths.end())return;dir=std::filesystem::absolute(exe->second).parent_path().parent_path()/"local"/"hires-pack"/"hud";}
 std::error_code ec;if(!std::filesystem::is_directory(dir,ec))return;
 for(const auto&f:std::filesystem::directory_iterator(dir,ec)){if(f.path().extension()!=".rgba")continue;std::ifstream in(f.path(),std::ios::binary);char magic[4]{};HiresTex h{};
  in.read(magic,4);in.read(reinterpret_cast<char*>(&h.w),4);in.read(reinterpret_cast<char*>(&h.h),4);in.read(reinterpret_cast<char*>(&h.u0),16);
  if(!in||std::memcmp(magic,"MW3H",4)||!h.w||!h.h||h.w>8192||h.h>8192)continue;h.px.resize(size_t(h.w)*h.h);in.read(reinterpret_cast<char*>(h.px.data()),std::streamsize(h.px.size()*4));if(!in)continue;
  try{hires[std::stoull(f.path().stem().string(),nullptr,16)]=std::move(h);}catch(...){}}}
std::uint64_t hud_identity(unsigned pix,unsigned mask,unsigned mode,unsigned key,int w,int h,unsigned pitch){std::uint64_t v=0xcbf29ce484222325ULL;auto fold=[&](const void*p,size_t n){const auto*b=static_cast<const unsigned char*>(p);for(size_t i=0;i<n;++i){v^=b[i];v*=0x100000001b3ULL;}};
 const unsigned uw=unsigned(w),uh=unsigned(h);fold(&uw,4);fold(&uh,4);std::vector<std::uint16_t>row(uw);std::vector<std::uint8_t>m(mode==2?uw:0);
 for(unsigned y=0;y<uh;++y){get_bytes(pix+2*y*pitch,row.data(),uw*2);if(mode==2)get_bytes(mask+y*pitch,m.data(),uw);for(unsigned x=0;x<uw;++x){const bool transparent=mode==2?m[x]==0:mode==1&&row[x]==key;if(transparent)row[x]=0;}fold(row.data(),row.size()*2);}
 return v;}
// HUD text at output density. The game builds each HUD string image as: clear the shared DC over the image (0x577BA0),
// DrawTextA (shadow then main) through the host GDI service, copy the DC bitmap's nonzero words into the image (0x577BD0).
// Each DrawTextA between a clear and a copy is recorded (string, rectangle, flags, the DC's LOGFONT and text colour) and
// attached to that image. A blit of such an image at a render scale above 1 re-renders the recipes with the same fonts at
// the scale (antialiased host GDI, composited in order, straight alpha) and draws them at the image's logical size; the
// game's measurements, crops and positions are unchanged. MW34_HUD_TEXT=0 keeps the cached raster.
struct TextRecipe{std::string text;RECT rect{};unsigned flags{};LOGFONTA font{};COLORREF color{};};
struct TextImage{std::vector<TextRecipe>recipes;int w{},h{};std::uint64_t hash{};};
bool text_rec_active{};unsigned text_rec_image{};std::vector<TextRecipe>text_recs;std::map<unsigned,TextImage>text_images;
struct TextTex{unsigned w{},h{};float u0{},u1{};std::vector<std::uint32_t>px;};std::map<std::uint64_t,TextTex>text_cache;  // recipe hash x scale -> texture
std::uint64_t text_hits{};
static bool hud_text_on(){static const bool on=[]{const char*e=std::getenv("MW34_HUD_TEXT");return !(e&&*e=='0');}();return on;}
void text_record(HDC dc,const std::string&t,const RECT&r,unsigned flags){if(!text_rec_active||(flags&DT_CALCRECT))return;TextRecipe x{};x.text=t;x.rect=r;x.flags=flags;
 if(HGDIOBJ f=::GetCurrentObject(dc,OBJ_FONT))::GetObjectA(f,sizeof x.font,&x.font);x.color=::GetTextColor(dc);text_recs.push_back(std::move(x));}
void text_hooks(unsigned target){if(!gpu_hud()||!hud_text_on())return;const unsigned img=state.gpr.rcx.dword;
 if(target==0x577ba0){text_rec_active=true;text_rec_image=img;text_recs.clear();return;}
 if(target==0x577bd0&&text_rec_active&&img==text_rec_image){TextImage ti{};ti.recipes=std::move(text_recs);ti.w=std::int16_t(load(img+4)&0xffff);ti.h=std::int16_t(load(img+6)&0xffff);
  std::uint64_t v=0xcbf29ce484222325ULL;auto fold=[&](const void*p,size_t n){const auto*b=static_cast<const unsigned char*>(p);for(size_t i=0;i<n;++i){v^=b[i];v*=0x100000001b3ULL;}};
  for(const auto&r:ti.recipes){fold(r.text.data(),r.text.size());fold(&r.rect,sizeof r.rect);fold(&r.flags,4);fold(&r.font,sizeof r.font);fold(&r.color,4);}fold(&ti.w,4);fold(&ti.h,4);ti.hash=v;
  if(ti.recipes.empty())text_images.erase(img);else text_images[img]=std::move(ti);text_rec_active=false;text_recs.clear();}}
// RGBA (straight alpha) of the recipes at scale k into a (w*k) x (h*k) texture.
// Scaled fonts are not exactly proportional, so text is drawn unclipped with a margin of 40% of the width on each side (a
// left-aligned rectangle also extends into the right margin, so it neither clips nor wraps differently); the
// texture range [u0, u1] that maps onto the logical width covers the logical box and any ink beyond it (slight compression).
std::vector<std::uint32_t> text_render(const TextImage&ti,float k,unsigned&tw,unsigned&th,float&u0,float&u1){const float lw=float(ti.w)*k,m=std::ceil(lw*0.4f)+2.f;tw=unsigned(std::ceil(lw+2.f*m));th=unsigned(std::ceil(float(ti.h)*k));std::vector<std::uint32_t>out(size_t(tw)*th,0);
 HDC dc=::CreateCompatibleDC(nullptr);BITMAPINFO bi{};bi.bmiHeader={sizeof(BITMAPINFOHEADER),LONG(tw),-LONG(th),1,32,BI_RGB};void*bits{};HBITMAP bmp=::CreateDIBSection(dc,&bi,DIB_RGB_COLORS,&bits,nullptr,0);
 if(!dc||!bmp||!bits){if(bmp)::DeleteObject(bmp);if(dc)::DeleteDC(dc);return out;}HGDIOBJ oldb=::SelectObject(dc,bmp);::SetBkMode(dc,TRANSPARENT);::SetTextColor(dc,RGB(255,255,255));
 for(const auto&r:ti.recipes){std::memset(bits,0,size_t(tw)*th*4);LOGFONTA lf=r.font;lf.lfHeight=LONG(std::lround(double(lf.lfHeight)*k));lf.lfWidth=LONG(std::lround(double(lf.lfWidth)*k));lf.lfQuality=ANTIALIASED_QUALITY;
  HFONT f=::CreateFontIndirectA(&lf);HGDIOBJ oldf=::SelectObject(dc,f);
  { // the game measured and crops this text at its original width: narrow the scaled font when it runs wider
   std::string mt=r.text;RECT mr{0,0,LONG(std::lround((r.rect.right-r.rect.left)*k)),LONG(std::lround((r.rect.bottom-r.rect.top)*k))};const LONG target=mr.right;
   ::DrawTextA(dc,mt.data(),int(mt.size()),&mr,(r.flags|DT_CALCRECT)&~unsigned(DT_WORDBREAK));TEXTMETRICA tm{};
   if(mr.right>target&&target>0&&::GetTextMetricsA(dc,&tm)&&tm.tmAveCharWidth>0){lf.lfWidth=std::max<LONG>(1,LONG(double(tm.tmAveCharWidth)*double(target)/double(mr.right)));
    ::SelectObject(dc,oldf);::DeleteObject(f);f=::CreateFontIndirectA(&lf);oldf=::SelectObject(dc,f);}}RECT rr{LONG(std::lround(r.rect.left*k+m)),LONG(std::lround(r.rect.top*k)),LONG(std::lround(r.rect.right*k+m)),LONG(std::lround(r.rect.bottom*k))};if(!(r.flags&(DT_CENTER|DT_RIGHT)))rr.right+=LONG(m);
  std::string t=r.text;::DrawTextA(dc,t.data(),int(t.size()),&rr,(r.flags&~unsigned(DT_CALCRECT))|DT_NOCLIP);::GdiFlush();::SelectObject(dc,oldf);::DeleteObject(f);
  const auto*px=static_cast<const std::uint8_t*>(bits);const unsigned cr=GetRValue(r.color),cg=GetGValue(r.color),cb=GetBValue(r.color);
  for(size_t i=0;i<out.size();++i){const unsigned a=std::max({px[4*i],px[4*i+1],px[4*i+2]});if(!a)continue;const std::uint32_t d=out[i];const unsigned da=d>>24;
   const unsigned oa=a+da*(255-a)/255;auto mix=[&](unsigned s,unsigned dc2){return oa?(s*a+dc2*da*(255-a)/255)/oa:0;};
   out[i]=mix(cr,d&255)|mix(cg,(d>>8)&255)<<8|mix(cb,(d>>16)&255)<<16|oa<<24;}}
 ::SelectObject(dc,oldb);::DeleteObject(bmp);::DeleteDC(dc);
 unsigned ix0=tw,ix1=0;for(unsigned y=0;y<th;++y)for(unsigned x=0;x<tw;++x)if(out[size_t(y)*tw+x]>>24){ix0=std::min(ix0,x);ix1=std::max(ix1,x+1);}
 const float a=std::min(m,ix0<tw?float(ix0):m),b=std::max(m+lw,float(ix1));u0=a/float(tw);u1=b/float(tw);return out;}
// Draws a text image at output density; false when it is not a recorded text image or the scale is 1.
bool text_blit(unsigned img,int w,int h,int x,int y,int sx0,int sy0,int sx1,int sy1){auto it=text_images.find(img);if(it==text_images.end()||it->second.w!=w||it->second.h!=h)return false;
 const float k=host.sren?host.sren->current_scale():1.f;if(k<=1.01f)return false;const auto&ti=it->second;namespace vs=mw34::vkscene;
 const std::uint64_t key=ti.hash^std::uint64_t(std::lround(k*256));auto c=text_cache.find(key);if(c==text_cache.end()){if(text_cache.size()>512)text_cache.clear();TextTex tt{};tt.px=text_render(ti,k,tt.w,tt.h,tt.u0,tt.u1);{static FILE*dbg=[]{const char*e=std::getenv("MW34_HUD_TEXT_LOG");return e&&*e?std::fopen(e,"w"):nullptr;}();if(dbg){std::fprintf(dbg,"img %ux%u k %.2f tex %ux%u u %.3f-%.3f\n",unsigned(ti.w),unsigned(ti.h),k,tt.w,tt.h,tt.u0,tt.u1);for(const auto&r:ti.recipes)std::fprintf(dbg,"  [%s] rect %ld,%ld,%ld,%ld flags %x font %s h%ld w%ld wt%ld\n",r.text.c_str(),r.rect.left,r.rect.top,r.rect.right,r.rect.bottom,r.flags,r.font.lfFaceName,r.font.lfHeight,r.font.lfWidth,r.font.lfWeight);std::fflush(dbg);}}c=text_cache.emplace(key,std::move(tt)).first;}
 const unsigned tw=c->second.w,th=c->second.h;if(!tw||!th)return false;
 const std::uint64_t tkey=0x5445585400000000ULL^key;int ti2;auto hit=hud_tex_index.find(tkey);
 if(hit!=hud_tex_index.end())ti2=hit->second;else{vs::TextureRef r{};r.key=tkey;r.hash=key;r.width=tw;r.height=th;r.format=vs::TexFormat::rgba8888;if(!host.sren||!host.sren->current(tkey,key,tw,th))r.pixels32=c->second.px;
  ti2=int(hud_sc.textures.size());hud_tex_index[tkey]=ti2;hud_sc.textures.push_back(std::move(r));}
 const float du=c->second.u1-c->second.u0,fh=float(h)*k/float(th);const float a0=c->second.u0+du*float(sx0)/float(w),a1=c->second.u0+du*float(sx1)/float(w),b0=fh*float(sy0)/float(h),b1=fh*float(sy1)/float(h);
 const unsigned first=unsigned(hud_sc.vertices.size()/32);const float x0=float(x)-0.5f,y0=float(y)-0.5f,x1=x0+float(sx1-sx0),y1=y0+float(sy1-sy0);
 hud_vertex(x0,y0,0xffffffffu,a0,b0);hud_vertex(x1,y0,0xffffffffu,a1,b0);hud_vertex(x1,y1,0xffffffffu,a1,b1);hud_vertex(x0,y0,0xffffffffu,a0,b0);hud_vertex(x1,y1,0xffffffffu,a1,b1);hud_vertex(x0,y1,0xffffffffu,a0,b1);
 hud_draw(ti2,false,first);hud_sc.draws.back().sampler=1U|2U|(D3DTADDRESS_CLAMP<<4)|(D3DTADDRESS_CLAMP<<8);++text_hits;return true;}
// Image blit: ECX image, EDX x, [esp+4] y, [esp+8] colour key, [esp+12] optional source rectangle.
bool hud_blit(){const auto&g=state.gpr;const unsigned sp=g.rsp.dword,img=g.rcx.dword;const int x=int(g.rdx.dword),y=int(load(sp+4));const unsigned key=load(sp+8)&0xffff,src=load(sp+12);
 if(!readable(img,0x38))return false;const int w=std::int16_t(load(img+4)&0xffff),h=std::int16_t(load(img+6)&0xffff);const unsigned flags=(load(img+8)>>8)&0xff,pix=load(img+0x10),mask=load(img+0x14),alt=load(img+0x18),pitch=load(img+0x34);
 if(alt)return false;int sx0=0,sy0=0,sx1=w,sy1=h;if(src){if(!readable(src,16))return false;sx0=int(load(src));sy0=int(load(src+4));sx1=int(load(src+8));sy1=int(load(src+12));}
 const int sw=sx1-sx0,sh=sy1-sy0;if(sw<0||sw>0x800||sh<0||sh>0x800||sx0<0||sy0<0||sx1>int(pitch)||sy1>h)return false;if(!sw||!sh)return true;
 if(text_blit(img,w,h,x,y,sx0,sy0,sx1,sy1))return true;
 namespace vs=mw34::vkscene;const unsigned imode=mask?2U:(flags&2)?1U:0U;if(!hires_loaded)hires_load();
 if(!hires.empty()&&w>0&&h>0&&std::int64_t(w)*h<=65536){const std::uint64_t id=hud_identity(pix,mask,imode,key,w,h,pitch);auto hi=hires.find(id);
  if(hi!=hires.end()){const auto&ht=hi->second;const std::uint64_t tkey=0x4852455300000000ULL^id;int ti;auto it=hud_tex_index.find(tkey);
   if(it!=hud_tex_index.end())ti=it->second;else{vs::TextureRef r{};r.key=tkey;r.hash=id;r.width=ht.w;r.height=ht.h;r.format=vs::TexFormat::rgba8888;auto*ren=host.sren;
    if(!ren||!ren->current(tkey,id,r.width,r.height))r.pixels32=ht.px;ti=int(hud_sc.textures.size());hud_tex_index[tkey]=ti;hud_sc.textures.push_back(std::move(r));}
   const float du=ht.u1-ht.u0,dv=ht.v1-ht.v0,a0=ht.u0+du*float(sx0)/float(w),a1=ht.u0+du*float(sx1)/float(w),b0=ht.v0+dv*float(sy0)/float(h),b1=ht.v0+dv*float(sy1)/float(h);
   const unsigned first=unsigned(hud_sc.vertices.size()/32);const float x0=float(x)-0.5f,y0=float(y)-0.5f,x1=x0+float(sw),y1=y0+float(sh);
   hud_vertex(x0,y0,0xffffffffu,a0,b0);hud_vertex(x1,y0,0xffffffffu,a1,b0);hud_vertex(x1,y1,0xffffffffu,a1,b1);hud_vertex(x0,y0,0xffffffffu,a0,b0);hud_vertex(x1,y1,0xffffffffu,a1,b1);hud_vertex(x0,y1,0xffffffffu,a0,b1);
   hud_draw(ti,false,first);hud_sc.draws.back().sampler=1U|2U|(D3DTADDRESS_CLAMP<<4)|(D3DTADDRESS_CLAMP<<8);++hires_hits;return true;}}
 std::vector<std::uint16_t>px(size_t(sw)*sh);std::vector<std::uint8_t>al(mask?px.size():0);
 for(int r=0;r<sh;++r){get_bytes(pix+2*(unsigned(sy0+r)*pitch+unsigned(sx0)),px.data()+size_t(r)*sw,unsigned(sw)*2);if(mask)get_bytes(mask+unsigned(sy0+r)*pitch+unsigned(sx0),al.data()+size_t(r)*sw,unsigned(sw));}
 std::uint64_t hash=0xcbf29ce484222325ULL;auto fold=[&](const void*p,size_t n){const auto*b=static_cast<const unsigned char*>(p);for(size_t i=0;i<n;++i){hash^=b[i];hash*=0x100000001b3ULL;}};
 fold(px.data(),px.size()*2);fold(al.data(),al.size());const unsigned mode=mask?2U:(flags&2)?1U:0U;fold(&mode,4);fold(&key,4);
 const std::uint64_t tkey=0x4855440000000000ULL^(std::uint64_t(img)<<20)^std::uint64_t(unsigned(sx0)<<10^unsigned(sy0))^(std::uint64_t(mode)<<40);
 int ti;auto it=hud_tex_index.find(tkey);
 if(it!=hud_tex_index.end()&&hud_sc.textures[size_t(it->second)].hash==hash)ti=it->second;
 else{vs::TextureRef r{};r.key=tkey;r.hash=hash;r.width=unsigned(sw);r.height=unsigned(sh);r.format=vs::TexFormat::rgba8888;auto*ren=host.sren;
  if(!ren||!ren->current(tkey,hash,r.width,r.height)){r.pixels32.resize(px.size());for(size_t i=0;i<px.size();++i){const unsigned c=px[i];unsigned a=255;
    if(mode==2){const unsigned m=al[i];a=m<=3?0U:m>=0xfc?255U:m;}else if(mode==1&&c==key)a=0;r.pixels32[i]=hud_rgba(c,a);}}
  ti=int(hud_sc.textures.size());hud_tex_index[tkey]=ti;hud_sc.textures.push_back(std::move(r));}
 const unsigned first=unsigned(hud_sc.vertices.size()/32);const float x0=float(x)-0.5f,y0=float(y)-0.5f,x1=x0+float(sw),y1=y0+float(sh);
 hud_vertex(x0,y0,0xffffffffu,0,0);hud_vertex(x1,y0,0xffffffffu,1,0);hud_vertex(x1,y1,0xffffffffu,1,1);hud_vertex(x0,y0,0xffffffffu,0,0);hud_vertex(x1,y1,0xffffffffu,1,1);hud_vertex(x0,y1,0xffffffffu,0,1);
 hud_draw(ti,false,first);return true;}
// Line: ECX buffer base, EDX x0, [esp+4] y0, [esp+8] x1, [esp+12] y1, [esp+16] colour; a one-pixel-wide segment quad.
bool hud_line(){const auto&g=state.gpr;if(g.rcx.dword!=hud_rt_mem)return false;const unsigned sp=g.rsp.dword;const int x0=int(g.rdx.dword),y0=int(load(sp+4)),x1=int(load(sp+8)),y1=int(load(sp+12));const std::uint32_t c=hud_argb(load(sp+16)&0xffff);
 if(std::abs(x1-x0)>4096||std::abs(y1-y0)>4096)return false;const unsigned first=unsigned(hud_sc.vertices.size()/32);hud_segment(float(x0),float(y0),float(x1),float(y1),c);hud_draw(-1,false,first);return true;}
// Pixel5630A0: ECX x, EDX y, stackRGB565, RET4 (radar point5A6BB0).
// Pixel5641F0: ECX buffer, EDX y, stackx/RGB565, RET8. The original
// jittered-circle563440 keeps every rand/_ftol call and uses this leaf.
// Both original routines overwrite one cell without clipping.
bool hud_pixel(bool supplied_buffer=false){const auto&g=state.gpr;const unsigned sp=g.rsp.dword;
 if((supplied_buffer&&g.rcx.dword!=hud_rt_mem)||!readable(sp,supplied_buffer?12:8)||load(0x8007c8)!=hud_rt_mem||load(0x8007d4)!=hud_pitch||!hud_w||!hud_h||std::uint64_t(hud_pitch)<std::uint64_t(hud_w)*2||(hud_pitch&1))return false;
 const int x=int(supplied_buffer?load(sp+4):g.rcx.dword),y=int(g.rdx.dword);if(x<0||y<0||unsigned(x)>=hud_w||unsigned(y)>=hud_h)return false;
 const std::uint32_t c=hud_argb(load(sp+(supplied_buffer?8:4))&0xffff);const unsigned first=unsigned(hud_sc.vertices.size()/32);const float x0=float(x)-0.5f,y0=float(y)-0.5f,x1=x0+1.f,y1=y0+1.f;
 hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y1,c,0,0);hud_draw(-1,false,first);return true;}
// Clipped line 0x563DB0 (radar selected-target triangle): ECX buffer, EDX inclusive
// rectangle, stack x0/y0/x1/y1/RGB565. The separate original body ends in RET 0x14.
// Preserve its X-then-Y endpoint clipping, extended slope, float32 reciprocal and
// _ftol truncation. The existing segment emitter supplies the output-density line.
bool hud_clipped_line(){const auto&g=state.gpr;const unsigned sp=g.rsp.dword,rect=g.rdx.dword;
 if(g.rcx.dword!=hud_rt_mem||!readable(sp,24)||!rect||!readable(rect,16))return false;
 const int clip[4]{int(load(rect)),int(load(rect+4)),int(load(rect+8)),int(load(rect+12))};
 const int left=clip[0],top=clip[1],right=clip[2],bottom=clip[3];
 // Original579880 returns0,0,W,H. Keep that rectangle for the original
 // endpoint arithmetic; only the GPU scissor intersects the physical surface.
 if(!hud_w||!hud_h||left<0||top<0||right<left||bottom<top||unsigned(right)>hud_w||unsigned(bottom)>hud_h)return false;
 const int gpu_clip[4]{left,top,std::min(right,int(hud_w)-1),std::min(bottom,int(hud_h)-1)};
 int x0=int(load(sp+4)),y0=int(load(sp+8)),x1=int(load(sp+12)),y1=int(load(sp+16));
 // Bound arithmetic before any guest-equivalent floating point work. Unknown
 // targets, malformed rectangles and overflow cases use synchronized fallback.
 auto bounded=[](int v){return v>=-1048576&&v<=1048576;};
 if(!bounded(x0)||!bounded(y0)||!bounded(x1)||!bounded(y1)||!bounded(right)||!bounded(bottom))return false;
 auto code=[&](int x,int y){return (x<left?1:x>right?2:0)|(y<top?4:y>bottom?8:0);};
 const int out0=code(x0,y0),out1=code(x1,y1);if(out0&out1)return true;
 const unsigned short cw=state.x87.fxsave32.cwd.flat;
 if((cw&0x3f)!=0x3f||(cw&0x300)==0x100)return false;
 // Guest CW is emulated state; the physical host CW can differ after a driver
 // call. Use it only inside a host-FP scope, then restore the physical state.
 mw34::vkscene::HostFpEnvironment host_fp;__asm__ volatile("fldcw %0"::"m"(cw));
 if(out0|out1){const int dx=x1-x0,dy=y1-y0;unsigned char slope[10]{};float inverse{};
  if(dx)__asm__ volatile("fildl %1\n\tfidivl %2\n\tfstpt %0":"=m"(slope):"m"(dy),"m"(dx):"st");
  if(dy)__asm__ volatile("fildl %1\n\tfidivl %2\n\tfstps %0":"=m"(inverse):"m"(dx),"m"(dy):"st");
  const unsigned short trunc_cw=cw|0xc00;
  auto adjust=[&](int&value,int delta,bool reciprocal){long long step{};
   if(reciprocal)__asm__ volatile("fildl %2\n\tfmuls %3\n\tfldcw %4\n\tfistpll %0\n\tfldcw %1":"=m"(step):"m"(cw),"m"(delta),"m"(inverse),"m"(trunc_cw):"st");
   else __asm__ volatile("fildl %2\n\tfldt %3\n\tfmulp\n\tfldcw %4\n\tfistpll %0\n\tfldcw %1":"=m"(step):"m"(cw),"m"(delta),"m"(slope),"m"(trunc_cw):"st");
   const std::int64_t result=std::int64_t(value)+step;if(result<-2147483648LL||result>2147483647LL)return false;value=int(result);return true;};
  if(x0<left){if(!adjust(y0,left-x0,false))return false;x0=left;}
  else if(x0>right){if(!adjust(y0,right-x0,false))return false;x0=right;}
  if(x1<left){if(!adjust(y1,left-x1,false))return false;x1=left;}
  else if(x1>right){if(!adjust(y1,right-x1,false))return false;x1=right;}
  if(y0<top){if(y1<top)return true;if(!adjust(x0,top-y0,true))return false;y0=top;}
  else if(y0>bottom){if(y1>bottom)return true;if(!adjust(x0,bottom-y0,true))return false;y0=bottom;}
  if(y1<top){if(!adjust(x1,top-y1,true))return false;y1=top;}
  else if(y1>bottom){if(!adjust(x1,bottom-y1,true))return false;y1=bottom;}
 }
 if(code(x0,y0)||code(x1,y1)||unsigned(x0)>=hud_w||unsigned(x1)>=hud_w||unsigned(y0)>=hud_h||unsigned(y1)>=hud_h||std::abs(x1-x0)>4096||std::abs(y1-y0)>4096)return false;
 const unsigned first=unsigned(hud_sc.vertices.size()/32);hud_segment(float(x0),float(y0),float(x1),float(y1),hud_argb(load(sp+20)&0xffff));hud_draw(-1,false,first,~0U,gpu_clip);return true;}
// Circle 0x5630C0: ECX/EDX centre, [esp+4] radius, [esp+8] RGB565 colour,
// [esp+12] optional inclusive clip rectangle. This entry always draws an outline.
// Original 0x5630E2..EE publishes its scratch words; 0x563416..42B advances the midpoint circle.
bool hud_circle(){const auto&g=state.gpr;const unsigned sp=g.rsp.dword;const int cx=int(g.rcx.dword),cy=int(g.rdx.dword),r=int(load(sp+4));const std::uint32_t c=hud_argb(load(sp+8)&0xffff);const unsigned clip=load(sp+12);
 if(r<=0)return true;if(r>2048)return false;
 int left=0,top=0,right=int(hud_w)-1,bottom=int(hud_h)-1;
 if(clip){if(!readable(clip,16))return false;left=std::max(left,int(load(clip)));top=std::max(top,int(load(clip+4)));right=std::min(right,int(load(clip+8)));bottom=std::min(bottom,int(load(clip+12)));}
 // A coordinate overflow is outside this GPU adapter's bounded case; run the original body instead.
 if(std::int64_t(cx)-r<-0x80000000LL||std::int64_t(cx)+r>0x7fffffffLL||std::int64_t(cy)-r<-0x80000000LL||std::int64_t(cy)+r>0x7fffffffLL)return false;
 store(0x72c244,clip);store(0x72c248,unsigned(cx));store(0x72c24c,unsigned(cy));
 const unsigned role=wide_hud_role();const bool projected=wide_on()&&(role==WideWorld||role==WideReticle);
 const int scissor[4]{left,top,right,bottom};const float center=float(cx);
 if(right<left||bottom<top)return true;
 const unsigned first=unsigned(hud_sc.vertices.size()/32);
 auto point=[&](int x,int y){if(!projected&&(x<left||x>right||y<top||y>bottom))return;const float x0=float(x)-0.5f,y0=float(y)-0.5f,x1=x0+1.f,y1=y0+1.f;
  hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y1,c,0,0);};
 int x=r,y=0,error=1-r;
 do{point(cx+x,cy+y);point(cx-x,cy+y);point(cx+x,cy-y);point(cx-x,cy-y);point(cx+y,cy+x);point(cx-y,cy+x);point(cx-y,cy-x);point(cx+y,cy-x);
  if(error>=0){--x;error-=2*x;}error+=2*y+3;++y;
 }while(y<=x);
 // Target lead circle44155B->5A3B00: projected centre, screen-sized radius.
 // Clip after narrowing the extent around that centre, including partial circles.
 if(projected)hud_draw(-1,false,first,WideReticle,scissor,&center);else hud_draw(-1,false,first);return true;}
// Span: ECX colour, EDX pixel count, destination address [0x72C278] (the routine fills [dest, dest + 2*count)).
bool hud_span(){const auto&g=state.gpr;const unsigned dest=load(0x72c278),count=g.rdx.dword;const std::uint32_t c=hud_argb(g.rcx.dword&0xffff);
 if(dest<hud_rt_mem||count>hud_w)return false;const unsigned off=(dest-hud_rt_mem)/2,stride=hud_pitch/2;const int y=int(off/stride),x=int(off%stride);if(unsigned(y)>=hud_h)return false;if(!count)return true;
 const unsigned first=unsigned(hud_sc.vertices.size()/32);const float x0=float(x)-0.5f,y0=float(y)-0.5f,x1=x0+float(count),y1=y0+1.f;
 hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y1,c,0,0);hud_draw(-1,false,first);return true;}
// Panel interference558C10: run the actual translated body once, including its
// _ftol/format-getter/rand calls and all guest register/FP effects. Its sole
// destination access558D13 is a 16-bit overwrite; skipped pixels are unread.
// Stage those writes in the stale CPU target while the GPU stays authoritative.
bool hud_stack_input_alias(unsigned a,unsigned bytes,unsigned sp,unsigned frame_bytes=20)const{
 std::uint64_t stack_low=low,stack_high=kind==Kind::initterm?game_stack_top:std::uint64_t(entry_esp)+16;
 if(host.thread_tid){bool found{};for(const auto&t:host.threads)if(!t.exited&&t.tid==host.thread_tid){stack_low=t.stack_lo;stack_high=t.stack_hi;found=true;break;}if(!found)return true;}
 if(sp<stack_low||std::uint64_t(sp)+frame_bytes>stack_high)return true;
 // These bodies reuse input arguments as locals as well as pushing below SP.
 // Caller-stack rectangles above all20 input bytes remain stable and allowed.
 return std::uint64_t(a)<std::uint64_t(sp)+frame_bytes&&stack_low<std::uint64_t(a)+bytes;}
struct HudNoise{unsigned sp{},rect{},target{},w{},h{},pitch{},stride{},table{},table_size{},colors[3]{},role{};int left{},top{},right{},bottom{},center_x{};bool center_known{};std::uint64_t probability{};std::uint16_t sentinel{};};
const char*hud_noise_guard(HudNoise&n){const auto&g=state.gpr;n.sp=g.rsp.dword;n.rect=g.rcx.dword;
 auto aliases=[&](unsigned a,unsigned bytes){for(const unsigned guest:{host.res_rt,host.res_zb})if(guest)if(const auto*v=vsurface(guest))if(std::uint64_t(a)<std::uint64_t(v->mem)+v->bytes&&std::uint64_t(v->mem)<std::uint64_t(a)+bytes)return true;return false;};
 if(aliases(n.sp,20)||(n.rect&&aliases(n.rect,16)))return "noise-input-aliases-resident-surface";
 if(!readable(n.sp,20))return "stack-unreadable";
 n.probability=std::uint64_t(load(n.sp+4))|std::uint64_t(load(n.sp+8))<<32;n.colors[0]=g.rdx.dword&0xffff;n.colors[1]=load(n.sp+12)&0xffff;n.colors[2]=load(n.sp+16)&0xffff;
 if(!readable(0x72c1d8,32))return "context-unreadable";
 n.table_size=load(0x72c1d8);n.table=load(0x72c1dc);n.target=load(0x72c1e4);n.w=load(0x72c1e8);n.h=load(0x72c1ec);n.pitch=load(0x72c1f0);n.stride=load(0x72c1f4);
 if(n.rect){if(hud_stack_input_alias(n.rect,16,n.sp))return "rectangle-aliases-active-stack";if(!readable(n.rect,16))return "rectangle-unreadable";n.left=int(load(n.rect));n.top=int(load(n.rect+4));n.right=int(load(n.rect+8));n.bottom=int(load(n.rect+12));}
 else{if(!n.w||!n.h)return "empty-default-context";n.right=int(n.w-1);n.bottom=int(n.h-1);}
 if(!host.res_dirty||!host.sren)return "no-authoritative-gpu-target";
 const auto*rt=vsurface(host.res_rt);if(!rt||rt->mem!=hud_rt_mem||rt->bpp!=16||rt->width!=hud_w||rt->height!=hud_h||rt->pitch!=hud_pitch)return "resident-target-mismatch";
 if(n.target!=hud_rt_mem||n.w!=hud_w||n.h!=hud_h||n.pitch!=hud_pitch||n.stride!=hud_pitch/2)return "noise-context-mismatch";
 if(!hud_w||!hud_h||hud_w>4096||hud_h>4096||(hud_pitch&1)||std::uint64_t(hud_pitch)<std::uint64_t(hud_w)*2||std::uint64_t(hud_pitch)*hud_h>rt->bytes)return "surface-layout-unsupported";
 if(n.left<0||n.top<0||n.right<n.left||n.bottom<n.top||unsigned(n.right)>hud_w||unsigned(n.bottom)>hud_h)return "exclusive-rectangle-outside-target";
 // Accept finite probabilities[0,1], including negative zero, using bits so
 // host floating-point validation cannot change the guest's actual FP effects.
 const auto magnitude=n.probability&0x7fffffffffffffffULL;if(magnitude>0x3ff0000000000000ULL||((n.probability>>63)&&magnitude))return "probability-unsupported";
 //5581C0 requested exactly0x6400 bytes. At rand()==32767 the original
 // sliding pair reads table[size]; this proves mapped readability, not
 // ownership by that allocation. Preserve that actual byte; invent no padding.
 if(n.table_size!=0x6400||!n.table||!readable(n.table,n.table_size+1))return "noise-table-or-adjacent-byte-unreadable";
 if(aliases(n.table,n.table_size+1))return "noise-input-aliases-resident-surface";
 const unsigned width=unsigned(n.right-n.left),height=unsigned(n.bottom-n.top);
 for(unsigned y=0;y<height&&width;++y){const auto address=std::uint64_t(hud_rt_mem)+std::uint64_t(unsigned(n.top)+y)*hud_pitch+unsigned(n.left)*2;
  if(address>0xffffffffULL||!writable(unsigned(address),width*2))return "noise-row-unwritable";}
 if(hud_noise_slot>=4096)return "noise-draw-slot-bound";
 n.role=wide_hud_role();while(n.sentinel==n.colors[0]||n.sentinel==n.colors[1]||n.sentinel==n.colors[2])++n.sentinel;return nullptr;}
void*hud_overwrite_body(State*s,unsigned target,void*p,Body body,const HudNoise&n,std::uint64_t keyspace){
 const unsigned width=unsigned(n.right-n.left),height=unsigned(n.bottom-n.top);namespace vs=mw34::vkscene;
 vs::TextureRef texture{};texture.width=width;texture.height=height;texture.format=vs::TexFormat::rgba8888;texture.pixels32.resize(size_t(width)*height);
 std::vector<std::uint16_t>row(width,n.sentinel);void*result{};
 {struct Staging{Stage&stage;bool active,protected_pages;explicit Staging(Stage&x):stage(x),active(x.hud_gpu_active),protected_pages(x.host.res_protected){
    try{stage.gpu_protect(false);}catch(...){stage.hud_gpu_active=active;stage.gpu_protect(protected_pages);throw;}stage.hud_gpu_active=false;}
   ~Staging()noexcept(false){stage.hud_gpu_active=active;stage.gpu_protect(protected_pages);}}staging(*this);
  for(unsigned y=0;y<height&&width;++y)write_bytes(hud_rt_mem+(unsigned(n.top)+y)*hud_pitch+unsigned(n.left)*2,row.data(),width*2);
  result=body(s,target,p); // The caller's real frame is already bound by enter().
  for(unsigned y=0;y<height&&width;++y){get_bytes(hud_rt_mem+(unsigned(n.top)+y)*hud_pitch+unsigned(n.left)*2,row.data(),width*2);
   for(unsigned x=0;x<width;++x){const unsigned c=row[x];if(c!=n.sentinel&&c!=n.colors[0]&&c!=n.colors[1]&&c!=n.colors[2])deny("Translated HUD overwrite wrote an unexpected colour",target);texture.pixels32[size_t(y)*width+x]=c==n.sentinel?0U:hud_rgba(c,255);}}}
 if(!width||!height)return result;
 // Everything below is display work after the guest returned. A failure must
 // propagate visibly: never rerun the body and consume its random calls twice.
 std::uint64_t hash=0xcbf29ce484222325ULL;for(const auto pixel:texture.pixels32)for(unsigned shift=0;shift<32;shift+=8){hash^=(pixel>>shift)&0xff;hash*=0x100000001b3ULL;}
 texture.key=keyspace|hud_noise_slot++;texture.hash=hash;if(host.sren->current(texture.key,hash,width,height))texture.pixels32.clear();
 const int ti=int(hud_sc.textures.size());hud_sc.textures.push_back(std::move(texture));mw34::vkscene::HostFpEnvironment host_fp;
 const unsigned first=unsigned(hud_sc.vertices.size()/32);const float x0=float(n.left)-0.5f,y0=float(n.top)-0.5f,x1=float(n.right)-0.5f,y1=float(n.bottom)-0.5f;
 hud_vertex(x0,y0,0xffffffffu,0,0);hud_vertex(x1,y0,0xffffffffu,1,0);hud_vertex(x1,y1,0xffffffffu,1,1);hud_vertex(x0,y0,0xffffffffu,0,0);hud_vertex(x1,y1,0xffffffffu,1,1);hud_vertex(x0,y1,0xffffffffu,0,1);const float center=float(n.center_x);hud_draw(ti,false,first,n.role,nullptr,n.center_known?&center:nullptr);return result;}
void*hud_noise_body(State*s,unsigned target,void*p,Body body){HudNoise n{};
 if(const char*why=hud_noise_guard(n)){if(!hud_noise_reject_logged)if(FILE*log=wide_log_file()){hud_noise_reject_logged=true;
   std::fprintf(log,"noise rejection frame %u why %s rt %08x expected %ux%u/%u context %08x %ux%u/%u stride %u rect %08x [%d,%d,%d,%d) table %08x size %u probability %016llx colors %04x,%04x,%04x bt",host.frames,why,hud_rt_mem,hud_w,hud_h,hud_pitch,n.target,n.w,n.h,n.pitch,n.stride,n.rect,n.left,n.top,n.right,n.bottom,n.table,n.table_size,(unsigned long long)n.probability,n.colors[0],n.colors[1],n.colors[2]);for(unsigned i=depth;i>0&&i+12>depth;--i)std::fprintf(log," %06x",returns[i-1]);std::fprintf(log,"\n");std::fflush(log);}
  hud_fallback();return body(s,target,p);}
 void*result=hud_overwrite_body(s,target,p,body,n,0x4e4f495300000000ULL);++hud_noise_calls;return result;}
// Exact monotone bounds for the jittered outline563440 and line562970.
// Every calculation here preserves the complete physical FP environment,
// including x87 status/tag/stack and MXCSR; emulated guest state is untouched.
unsigned hud_effect_amplitude(unsigned short cw,bool line,int radius,int dx,int dy,unsigned fuzz){alignas(16) std::array<unsigned char,512>fp;unsigned amplitude{},sum{},approx{};const unsigned tenth=0x3dcccccdU;
 if(line){__asm__ volatile("fxsave64 %[fp]\n\tfninit\n\tfldcw %[cw]\n\tfildl %[dx]\n\tfildl %[dy]\n\tfld %%st(1)\n\tfmul %%st(2),%%st\n\tfld %%st(1)\n\tfmul %%st(2),%%st\n\tfaddp\n\tfstps %[sum]\n\tfstp %%st(0)\n\tfstp %%st(0)\n\tmovl %[sum],%%eax\n\tsarl $1,%%eax\n\taddl $0x1fc00000,%%eax\n\tmovl %%eax,%[approx]\n\tflds %[approx]\n\tfmuls %[fuzz]\n\tfmuls %[tenth]\n\tfstps %[amplitude]\n\tfxrstor64 %[fp]"
  :[fp]"=m"(fp),[amplitude]"=m"(amplitude),[sum]"=m"(sum),[approx]"=m"(approx):[cw]"m"(cw),[dx]"m"(dx),[dy]"m"(dy),[fuzz]"m"(fuzz),[tenth]"m"(tenth):"eax","cc","memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");}
 else{__asm__ volatile("fxsave64 %[fp]\n\tfninit\n\tfldcw %[cw]\n\tfildl %[radius]\n\tfmuls %[fuzz]\n\tfmuls %[tenth]\n\tfstps %[amplitude]\n\tfxrstor64 %[fp]"
  :[fp]"=m"(fp),[amplitude]"=m"(amplitude):[cw]"m"(cw),[radius]"m"(radius),[fuzz]"m"(fuzz),[tenth]"m"(tenth):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");}return amplitude;}
int hud_effect_limit(unsigned short cw,int nominal,int random,unsigned amplitude){alignas(16) std::array<unsigned char,512>fp;int result{};const unsigned inverse=0x38000100U,one=0x3f800000U;const unsigned short truncate=static_cast<unsigned short>((cw&~0xc00U)|0xc00U);
 __asm__ volatile("fxsave64 %[fp]\n\tfninit\n\tfldcw %[cw]\n\tfildl %[random]\n\tfmuls %[inverse]\n\tfadd %%st(0),%%st\n\tfsubs %[one]\n\tfmuls %[amplitude]\n\tfiaddl %[nominal]\n\tfldcw %[truncate]\n\tfistpl %[result]\n\tfxrstor64 %[fp]"
  :[fp]"=m"(fp),[result]"=m"(result):[cw]"m"(cw),[random]"m"(random),[inverse]"m"(inverse),[one]"m"(one),[amplitude]"m"(amplitude),[nominal]"m"(nominal),[truncate]"m"(truncate):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");return result;}
void hud_effect_axis(unsigned short cw,int first,int last,unsigned amplitude,int&low,int&high){const int values[4]{hud_effect_limit(cw,first,0,amplitude),hud_effect_limit(cw,first,32767,amplitude),hud_effect_limit(cw,last,0,amplitude),hud_effect_limit(cw,last,32767,amplitude)};low=*std::min_element(values,values+4);high=*std::max_element(values,values+4);}
// Both original bodies are overwrite-only, preserve one supplied colour and
// retain every real rand/_ftol call, scratch store and argument-slot reuse.
struct HudJitter{HudNoise output{};int cx{},cy{},x1{},y1{},radius{},clip[4]{},bound[4]{};unsigned fuzz{},cw{},amplitude{};};
const char*hud_jitter_guard(HudJitter&j,bool line=false){auto&n=j.output;const auto&g=state.gpr;n.sp=g.rsp.dword;j.cx=int(g.rcx.dword);j.cy=int(g.rdx.dword);const unsigned frame_bytes=line?24:20;
 auto aliases=[&](unsigned a,unsigned bytes){for(const unsigned guest:{host.res_rt,host.res_zb})if(guest)if(const auto*v=vsurface(guest))if(std::uint64_t(a)<std::uint64_t(v->mem)+v->bytes&&std::uint64_t(v->mem)<std::uint64_t(a)+bytes)return true;return false;};
 if(aliases(n.sp,frame_bytes))return "jitter-stack-aliases-resident-surface";if(!readable(n.sp,frame_bytes))return "jitter-stack-unreadable";
 if(line){j.x1=int(load(n.sp+4));j.y1=int(load(n.sp+8));n.colors[0]=load(n.sp+12)&0xffff;j.fuzz=load(n.sp+16);n.rect=load(n.sp+20);}
 else{j.radius=int(load(n.sp+4));n.colors[0]=load(n.sp+8)&0xffff;j.fuzz=load(n.sp+12);n.rect=load(n.sp+16);}n.colors[1]=n.colors[2]=n.colors[0];
 n.target=load(0x8007c8);n.pitch=load(0x8007d4);n.w=hud_w;n.h=hud_h;n.stride=n.pitch/2;
 if(!host.res_dirty||!host.sren)return "jitter-no-authoritative-gpu-target";
 const auto*rt=vsurface(host.res_rt);if(!rt||rt->mem!=hud_rt_mem||rt->bpp!=16||rt->width!=hud_w||rt->height!=hud_h||rt->pitch!=hud_pitch)return "jitter-resident-target-mismatch";
 if(n.target!=hud_rt_mem||n.pitch!=hud_pitch)return "jitter-global-target-or-pitch-mismatch";
 if(!hud_w||!hud_h||hud_w>4096||hud_h>4096||(hud_pitch&1)||std::uint64_t(hud_pitch)<std::uint64_t(hud_w)*2||std::uint64_t(hud_pitch)*hud_h>rt->bytes)return "jitter-surface-layout-unsupported";
 n.role=wide_hud_role();if(!line&&n.role==WideWorld){n.role=WideReticle;n.center_known=true;n.center_x=j.cx;}
 while(n.sentinel==n.colors[0])++n.sentinel;if(!line&&j.radius<=0)return nullptr; // actual early return still executes
 j.cw=state.x87.fxsave32.cwd.flat;if((j.cw&0x3f)!=0x3f||(j.cw&0x300)==0x100)return "jitter-guest-cw-unsupported";
 if((!line&&j.radius>4096)||j.cx<-8192||j.cx>8192||j.cy<-8192||j.cy>8192||(line&&(j.x1<-8192||j.x1>8192||j.y1<-8192||j.y1>8192))||(j.fuzz&0x7fffffffU)>0x3f800000U)return "jitter-radius-center-or-fuzz-unsupported";
 j.amplitude=hud_effect_amplitude(static_cast<unsigned short>(j.cw),line,j.radius,line?std::abs(j.x1-j.cx):0,line?std::abs(j.y1-j.cy):0,j.fuzz);
 // Supported rounding and truncation are monotone on these finite ranges.
 // Four nominal/rand corners include both amplitude signs and every emitted
 // circle/line point, including negative fractions that _ftol converts to0.
 hud_effect_axis(static_cast<unsigned short>(j.cw),line?std::min(j.cx,j.x1):j.cx-j.radius,line?std::max(j.cx,j.x1):j.cx+j.radius,j.amplitude,j.bound[0],j.bound[2]);
 hud_effect_axis(static_cast<unsigned short>(j.cw),line?std::min(j.cy,j.y1):j.cy-j.radius,line?std::max(j.cy,j.y1):j.cy+j.radius,j.amplitude,j.bound[1],j.bound[3]);
 int left=j.bound[0],top=j.bound[1],right=j.bound[2],bottom=j.bound[3];
 if(n.rect){if(aliases(n.rect,16))return "jitter-clip-aliases-resident-surface";if(hud_stack_input_alias(n.rect,16,n.sp,frame_bytes))return "jitter-clip-aliases-active-stack";if(!readable(n.rect,16))return "jitter-clip-unreadable";
  for(unsigned i=0;i<4;++i)j.clip[i]=int(load(n.rect+4*i));if(j.clip[0]>j.clip[2]||j.clip[1]>j.clip[3])return "jitter-clip-inverted";
  left=std::max(left,j.clip[0]);top=std::max(top,j.clip[1]);right=std::min(right,j.clip[2]);bottom=std::min(bottom,j.clip[3]);}
 if(left<=right&&top<=bottom){
  // Never intersect with the physical target to hide an original write. In
  // particular an inclusive original clip endingW/H can still allow aliases.
  if(left<0||top<0||unsigned(right)>=hud_w||unsigned(bottom)>=hud_h)return "jitter-write-bound-outside-physical-target";
  n.left=left;n.top=top;n.right=right+1;n.bottom=bottom+1;}
 const unsigned width=unsigned(n.right-n.left),height=unsigned(n.bottom-n.top);for(unsigned y=0;y<height&&width;++y){const auto address=std::uint64_t(hud_rt_mem)+std::uint64_t(unsigned(n.top)+y)*hud_pitch+unsigned(n.left)*2;
  if(address>0xffffffffULL||!writable(unsigned(address),width*2))return "jitter-row-unwritable";}
 if(hud_noise_slot>=4096)return "jitter-draw-slot-bound";return nullptr;}
void*hud_jitter_body(State*s,unsigned target,void*p,Body body,bool line=false){HudJitter j{};
 if(const char*why=hud_jitter_guard(j,line)){const auto&n=j.output;bool&logged=line?hud_jitter_line_reject_logged:hud_jitter_reject_logged;if(!logged)if(FILE*log=wide_log_file()){logged=true;
   std::fprintf(log,"jitter rejection frame %u primitive %06x why %s rt %08x expected %ux%u/%u global %08x/%u start %d,%d end %d,%d radius %d fuzz %08x amplitude %08x cw %04x clip %08x [%d,%d,%d,%d] inclusive-bound [%d,%d,%d,%d] staged [%d,%d,%d,%d) bt",host.frames,target,why,hud_rt_mem,hud_w,hud_h,hud_pitch,n.target,n.pitch,j.cx,j.cy,j.x1,j.y1,j.radius,j.fuzz,j.amplitude,j.cw,n.rect,j.clip[0],j.clip[1],j.clip[2],j.clip[3],j.bound[0],j.bound[1],j.bound[2],j.bound[3],n.left,n.top,n.right,n.bottom);for(unsigned i=depth;i>0&&i+12>depth;--i)std::fprintf(log," %06x",returns[i-1]);std::fprintf(log,"\n");std::fflush(log);}
  hud_fallback();return body(s,target,p);}
 void*result=hud_overwrite_body(s,target,p,body,j.output,line?0x4a4c494e00000000ULL:0x4a49545400000000ULL);++hud_jitter_calls;return result;}
void hud_flush(){if(hud_sc.draws.empty())return;if(photo_replay_hide_hud()){hud_begin(*vsurface(host.res_rt));return;}
 try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);}catch(const std::exception&e){deny(std::string(e.what()),0);}hud_begin(*vsurface(host.res_rt));}
// The lock reverts to the CPU: draws so far reach the target, guest memory is synchronized and unprotected.
void hud_fallback(){hud_flush();hud_gpu_active=false;++hud_fallbacks;gpu_sync(host.res_rt);}
// Entry interception (enter()): true when the primitive was recorded and the call returned to its caller.
bool hud_intercept(unsigned target,void*p,void*&result){if(target==0x577ba0||target==0x577bd0){text_hooks(target);return false;}if(!hud_gpu_active)return false;unsigned args;
 if(target==0x55b3c0)args=12;else if(target==0x563b80)args=16;else if(target==0x563db0)args=20;else if(target==0x5630a0)args=4;else if(target==0x5641f0)args=8;else if(target==0x5630c0)args=12;else if(target==0x564080)args=0;else return false;
 auto reject=[&](const char*why){if(wide_on()&&hud_fallbacks<8){if(FILE*log=wide_log_file()){const unsigned sp=state.gpr.rsp.dword;std::fprintf(log,"fallback frame %u primitive %06x why %s rt %08x global %08x ecx %08x edx %08x args %08x %08x %08x %08x bt",host.frames,target,why,hud_rt_mem,load(0x8007c8),state.gpr.rcx.dword,state.gpr.rdx.dword,load(sp+4),load(sp+8),load(sp+12),load(sp+16));for(unsigned i=depth;i>0&&i+10>depth;--i)std::fprintf(log," %06x",returns[i-1]);std::fprintf(log,"\n");std::fflush(log);}}hud_fallback();};
 if(load(0x8007c8)!=hud_rt_mem){reject("other-global-target");return false;}
 const bool ok=target==0x55b3c0?hud_blit():target==0x563b80?hud_line():target==0x563db0?hud_clipped_line():(target==0x5630a0||target==0x5641f0)?hud_pixel(target==0x5641f0):target==0x5630c0?hud_circle():hud_span();if(!ok){reject("primitive-guard");return false;}
 auto&g=state.gpr;const unsigned sp=g.rsp.dword;g.rip.dword=load(sp);g.rsp.dword=sp+4+args;result=p;return true;}
// FPS/frame-time overlay on the direct presentation path: the presenter's overlay text is drawn into a small buffer and
// rendered as an alpha-blended text tile beside the radar (diagnostic; not guest state).
void overlay_gpu(unsigned w,unsigned h){auto&ov=host.presenter->overlay;ov.prepare(w,h);const unsigned bw=ov.box_w,bh=ov.box_h;if(!bw||!bh)return;std::vector<std::uint16_t>buf(size_t(bw)*bh,0);ov.paint(buf.data(),bw);
 namespace vs=mw34::vkscene;hud_sc=vs::Scene{};hud_sc.hud=true;hud_sc.width=w;hud_sc.height=h;hud_sc.has_depth=host.res_zb!=0;hud_w=w;hud_h=h;vs::TextureRef r{};r.key=0x4f564c0000000000ULL;r.width=bw;r.height=bh;r.format=vs::TexFormat::rgba8888;
 r.pixels32.resize(size_t(bw)*bh);for(unsigned y=0;y<bh;++y)for(unsigned x=0;x<bw;++x)r.pixels32[size_t(y)*bw+x]=hud_rgba(buf[size_t(y)*bw+x],buf[size_t(y)*bw+x]?255:0);
 std::uint64_t hash=0xcbf29ce484222325ULL;for(auto v:r.pixels32){hash^=v;hash*=0x100000001b3ULL;}r.hash=hash;hud_sc.textures.push_back(std::move(r));
 const float x=float(ov.box_x)-0.5f,y=float(ov.box_y)-0.5f;const unsigned first=0;hud_vertex(x,y,0xffffffffu,0,0);hud_vertex(x+bw,y,0xffffffffu,1,0);hud_vertex(x+bw,y+bh,0xffffffffu,1,1);
 hud_vertex(x,y,0xffffffffu,0,0);hud_vertex(x+bw,y+bh,0xffffffffu,1,1);hud_vertex(x,y+bh,0xffffffffu,0,1);hud_draw(0,false,first,WideLeft);
 /* GPU-resident overlay: no CPU color/depth upload or readback. */try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);}catch(const std::exception&e){deny(std::string(e.what()),0);}hud_sc=vs::Scene{};}
