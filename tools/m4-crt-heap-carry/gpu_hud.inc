// GPU HUD (MW34_GPU_HUD=1 with MW34_LAZY_RT=1; included inside mf::Stage). docs/hud-vulkan-integration-handoff.md.
// The game's own HUD code still runs and decides every element, value and position. While it holds the resident 3D
// target locked, its four software raster primitives (image blit 0x55B3C0, line 0x563B80, circle 0x5630C0, span 0x564080)
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
std::uint64_t hud_draws_total{},hud_fallbacks{};
void hud_begin(VSurface&rt){hud_gpu_active=true;hud_rt_mem=rt.mem;hud_w=rt.width;hud_h=rt.height;hud_pitch=rt.pitch;
 hud_sc=mw34::vkscene::Scene{};hud_sc.width=rt.width;hud_sc.height=rt.height;hud_sc.has_depth=host.res_zb!=0;hud_tex_index.clear();}
static std::uint32_t hud_rgba(unsigned c,unsigned a){const std::uint32_t r=((c>>11)&31)*255/31,g=((c>>5)&63)*255/63,b=(c&31)*255/31;return r|g<<8|b<<16|std::uint32_t(a)<<24;}
static std::uint32_t hud_argb(unsigned c){const std::uint32_t r=((c>>11)&31)*255/31,g=((c>>5)&63)*255/63,b=(c&31)*255/31;return 0xff000000u|r<<16|g<<8|b;}
// One pre-transformed vertex (x, y, z, rhw, diffuse ARGB, specular, u, v), D3D pixel-centre convention.
void hud_vertex(float x,float y,std::uint32_t argb,float u,float v){float f[8]{x,y,0.f,1.f,0,0,u,v};std::memcpy(&f[4],&argb,4);const auto*b=reinterpret_cast<const unsigned char*>(f);hud_sc.vertices.insert(hud_sc.vertices.end(),b,b+32);}
void hud_draw(int tex,bool points,unsigned first){namespace vs=mw34::vkscene;vs::Draw dr{};dr.first=first;dr.count=unsigned(hud_sc.vertices.size()/32)-first;if(!dr.count)return;dr.texture=tex;
 dr.sampler=(D3DTADDRESS_CLAMP<<4)|(D3DTADDRESS_CLAMP<<8);  // point sampling, clamped
 dr.key={1,D3DBLEND_SRCALPHA,D3DBLEND_INVSRCALPHA,0,D3DCMP_ALWAYS,0,D3DCULL_NONE,std::uint8_t(points?1:0)};
 auto&pu=dr.push;pu.target[0]=float(hud_w);pu.target[1]=float(hud_h);pu.target[2]=0.5f;pu.fog[3]=1;pu.factor[0]=pu.factor[1]=pu.factor[2]=pu.factor[3]=1;
 pu.mode[0]=tex>=0?4U:0U;const unsigned arg=tex>=0?D3DTA_TEXTURE:D3DTA_DIFFUSE;pu.mode[1]=D3DTOP_SELECTARG1|arg<<8|D3DTA_DIFFUSE<<16;pu.mode[2]=D3DTOP_SELECTARG1|arg<<8|D3DTA_DIFFUSE<<16;pu.mode[3]=0;
 dr.scissor={{0,0},{hud_w,hud_h}};hud_sc.order.push_back({false,unsigned(hud_sc.draws.size())});hud_sc.draws.push_back(dr);++hud_draws_total;}
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
bool hud_line(){const auto&g=state.gpr;const unsigned sp=g.rsp.dword;const int x0=int(g.rdx.dword),y0=int(load(sp+4)),x1=int(load(sp+8)),y1=int(load(sp+12));const std::uint32_t c=hud_argb(load(sp+16)&0xffff);
 if(std::abs(x1-x0)>4096||std::abs(y1-y0)>4096)return false;const unsigned first=unsigned(hud_sc.vertices.size()/32);hud_segment(float(x0),float(y0),float(x1),float(y1),c);hud_draw(-1,false,first);return true;}
// Circle: ECX centre x, EDX centre y, [esp+4] radius, [esp+8] colour, [esp+12] fill; midpoint circle (outline points or spans).
bool hud_circle(){const auto&g=state.gpr;const unsigned sp=g.rsp.dword;const int cx=int(g.rcx.dword),cy=int(g.rdx.dword),r=int(load(sp+4));const std::uint32_t c=hud_argb(load(sp+8)&0xffff);const bool fill=load(sp+12)!=0;
 if(r<0||r>2048)return false;if(!r)return true;const unsigned first=unsigned(hud_sc.vertices.size()/32);
 const int n=std::clamp(int(6.2831853f*float(r)/3.f),16,256);const float pi2=6.2831853f;  // polyline / fan around the circle
 for(int i=0;i<n;++i){const float a0=pi2*float(i)/float(n),a1=pi2*float(i+1)/float(n);const float x0=float(cx)+float(r)*std::cos(a0),y0=float(cy)+float(r)*std::sin(a0),x1=float(cx)+float(r)*std::cos(a1),y1=float(cy)+float(r)*std::sin(a1);
  if(fill){const float rr=float(r)+0.5f;hud_vertex(float(cx),float(cy),c,0,0);hud_vertex(float(cx)+rr*std::cos(a0),float(cy)+rr*std::sin(a0),c,0,0);hud_vertex(float(cx)+rr*std::cos(a1),float(cy)+rr*std::sin(a1),c,0,0);}
  else hud_segment(x0,y0,x1,y1,c);}
 hud_draw(-1,false,first);return true;}
// Span: ECX colour, EDX pixel count, destination address [0x72C278] (the routine fills [dest, dest + 2*count)).
bool hud_span(){const auto&g=state.gpr;const unsigned dest=load(0x72c278),count=g.rdx.dword;const std::uint32_t c=hud_argb(g.rcx.dword&0xffff);
 if(dest<hud_rt_mem||count>hud_w)return false;const unsigned off=(dest-hud_rt_mem)/2,stride=hud_pitch/2;const int y=int(off/stride),x=int(off%stride);if(unsigned(y)>=hud_h)return false;if(!count)return true;
 const unsigned first=unsigned(hud_sc.vertices.size()/32);const float x0=float(x)-0.5f,y0=float(y)-0.5f,x1=x0+float(count),y1=y0+1.f;
 hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y0,c,0,0);hud_vertex(x1,y1,c,0,0);hud_vertex(x0,y1,c,0,0);hud_draw(-1,false,first);return true;}
void hud_flush(){if(hud_sc.draws.empty())return;hud_sc.color.resize(size_t(hud_w)*hud_h);hud_sc.depth.resize(hud_sc.color.size());
 try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);}catch(const std::exception&e){deny(std::string(e.what()),0);}hud_begin(*vsurface(host.res_rt));}
// The lock reverts to the CPU: draws so far reach the target, guest memory is synchronized and unprotected.
void hud_fallback(){hud_flush();hud_gpu_active=false;++hud_fallbacks;gpu_sync(host.res_rt);}
// Entry interception (enter()): true when the primitive was recorded and the call returned to its caller.
bool hud_intercept(unsigned target,void*p,void*&result){if(target==0x577ba0||target==0x577bd0){text_hooks(target);return false;}if(!hud_gpu_active)return false;unsigned args;
 if(target==0x55b3c0)args=12;else if(target==0x563b80)args=16;else if(target==0x5630c0)args=12;else if(target==0x564080)args=0;else return false;
 if(load(0x8007c8)!=hud_rt_mem){hud_fallback();return false;}
 const bool ok=target==0x55b3c0?hud_blit():target==0x563b80?hud_line():target==0x5630c0?hud_circle():hud_span();if(!ok){hud_fallback();return false;}
 auto&g=state.gpr;const unsigned sp=g.rsp.dword;g.rip.dword=load(sp);g.rsp.dword=sp+4+args;result=p;return true;}
// FPS/frame-time overlay on the direct presentation path: the presenter's overlay text is drawn into a small buffer and
// rendered as an opaque textured quad onto the resident image just before it is presented (diagnostic; not guest state).
void overlay_gpu(unsigned w,unsigned h){auto&ov=host.presenter->overlay;std::vector<std::uint16_t>buf(size_t(w)*24,0);ov.draw(buf.data(),w,24);const unsigned bw=ov.box_w,bh=ov.box_h;if(!bw||!bh)return;
 namespace vs=mw34::vkscene;hud_sc=vs::Scene{};hud_sc.width=w;hud_sc.height=h;hud_sc.has_depth=host.res_zb!=0;hud_w=w;hud_h=h;vs::TextureRef r{};r.key=0x4f564c0000000000ULL;r.width=bw;r.height=bh;r.format=vs::TexFormat::rgba8888;
 r.pixels32.resize(size_t(bw)*bh);for(unsigned y=0;y<bh;++y)for(unsigned x=0;x<bw;++x)r.pixels32[size_t(y)*bw+x]=hud_rgba(buf[size_t(y)*w+x],255);
 std::uint64_t hash=0xcbf29ce484222325ULL;for(auto v:r.pixels32){hash^=v;hash*=0x100000001b3ULL;}r.hash=hash;hud_sc.textures.push_back(std::move(r));
 const unsigned first=0;hud_vertex(-0.5f,-0.5f,0xffffffffu,0,0);hud_vertex(float(bw)-0.5f,-0.5f,0xffffffffu,1,0);hud_vertex(float(bw)-0.5f,float(bh)-0.5f,0xffffffffu,1,1);
 hud_vertex(-0.5f,-0.5f,0xffffffffu,0,0);hud_vertex(float(bw)-0.5f,float(bh)-0.5f,0xffffffffu,1,1);hud_vertex(-0.5f,float(bh)-0.5f,0xffffffffu,0,1);hud_draw(0,false,first);
 hud_sc.color.resize(size_t(w)*h);hud_sc.depth.resize(hud_sc.color.size());try{HostInternal hi(*this);host.sren->render(hud_sc,false,false);}catch(const std::exception&e){deny(std::string(e.what()),0);}hud_sc=vs::Scene{};}
