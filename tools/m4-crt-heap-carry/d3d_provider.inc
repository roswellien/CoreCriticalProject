// Direct3D3 provider (project-implemented, rendered through Vulkan; included inside mf::Stage).
// The real x64 DirectDraw has no Direct3D3, so QueryInterface(IID_IDirect3D3) on any DirectDraw object
// yields this provider's IDirect3D3. It reports one HAL device whose caps describe what the Vulkan
// renderer implements (pre-transformed vertices, Gouraud/flat shading, perspective-correct bilinear
// textures, alpha blending, vertex fog, 16-bit colour and depth). Draws are collected per scene and
// rendered at EndScene into the render-target surface. Methods without an implementation stop typed.

// D3DDEVICEDESC (DX6, 252 bytes): DWORD/float fields only, identical x86/x64 layout.
D3DDEVICEDESC hal_desc()const{D3DDEVICEDESC d{};d.dwSize=sizeof(d);static_assert(sizeof(D3DDEVICEDESC)==252);
 d.dwFlags=D3DDD_COLORMODEL|D3DDD_DEVCAPS|D3DDD_TRANSFORMCAPS|D3DDD_LIGHTINGCAPS|D3DDD_BCLIPPING|D3DDD_LINECAPS|D3DDD_TRICAPS|D3DDD_DEVICERENDERBITDEPTH|D3DDD_DEVICEZBUFFERBITDEPTH|D3DDD_MAXBUFFERSIZE|D3DDD_MAXVERTEXCOUNT;
 d.dcmColorModel=D3DCOLOR_RGB;d.dwDevCaps=D3DDEVCAPS_FLOATTLVERTEX|D3DDEVCAPS_EXECUTESYSTEMMEMORY|D3DDEVCAPS_TLVERTEXSYSTEMMEMORY|D3DDEVCAPS_TEXTUREVIDEOMEMORY|D3DDEVCAPS_DRAWPRIMTLVERTEX|D3DDEVCAPS_CANRENDERAFTERFLIP|D3DDEVCAPS_TEXTURENONLOCALVIDMEM|D3DDEVCAPS_DRAWPRIMITIVES2|D3DDEVCAPS_HWRASTERIZATION;
 d.dtcTransformCaps.dwSize=sizeof(D3DTRANSFORMCAPS);d.dlcLightingCaps.dwSize=sizeof(D3DLIGHTINGCAPS);d.bClipping=TRUE;
 for(auto*p:{&d.dpcLineCaps,&d.dpcTriCaps}){p->dwSize=sizeof(D3DPRIMCAPS);p->dwMiscCaps=D3DPMISCCAPS_CULLNONE|D3DPMISCCAPS_CULLCW|D3DPMISCCAPS_CULLCCW|D3DPMISCCAPS_MASKZ;
  p->dwRasterCaps=D3DPRASTERCAPS_DITHER|D3DPRASTERCAPS_ZTEST|D3DPRASTERCAPS_FOGVERTEX|D3DPRASTERCAPS_SUBPIXEL;p->dwZCmpCaps=0xff;p->dwSrcBlendCaps=D3DPBLENDCAPS_ZERO|D3DPBLENDCAPS_ONE|D3DPBLENDCAPS_SRCALPHA|D3DPBLENDCAPS_INVSRCALPHA;
  p->dwDestBlendCaps=p->dwSrcBlendCaps;p->dwAlphaCmpCaps=0xff;p->dwShadeCaps=D3DPSHADECAPS_COLORFLATRGB|D3DPSHADECAPS_COLORGOURAUDRGB|D3DPSHADECAPS_ALPHAFLATBLEND|D3DPSHADECAPS_ALPHAGOURAUDBLEND|D3DPSHADECAPS_FOGFLAT|D3DPSHADECAPS_FOGGOURAUD;
  p->dwTextureCaps=D3DPTEXTURECAPS_PERSPECTIVE|D3DPTEXTURECAPS_POW2|D3DPTEXTURECAPS_ALPHA|D3DPTEXTURECAPS_TRANSPARENCY;p->dwTextureFilterCaps=D3DPTFILTERCAPS_NEAREST|D3DPTFILTERCAPS_LINEAR;
  p->dwTextureBlendCaps=D3DPTBLENDCAPS_MODULATE|D3DPTBLENDCAPS_MODULATEALPHA|D3DPTBLENDCAPS_DECAL|D3DPTBLENDCAPS_COPY;p->dwTextureAddressCaps=D3DPTADDRESSCAPS_WRAP|D3DPTADDRESSCAPS_CLAMP;}
 d.dwDeviceRenderBitDepth=DDBD_16;d.dwDeviceZBufferBitDepth=DDBD_16;d.dwMaxBufferSize=0;d.dwMaxVertexCount=65535;d.dwMinTextureWidth=1;d.dwMinTextureHeight=1;d.dwMaxTextureWidth=256;d.dwMaxTextureHeight=256;
 d.dwMaxTextureRepeat=256;d.dwMaxTextureAspectRatio=8;d.dwFVFCaps=1;d.dwTextureOpCaps=D3DTEXOPCAPS_SELECTARG1|D3DTEXOPCAPS_MODULATE;d.wMaxTextureBlendStages=1;d.wMaxSimultaneousTextures=1;return d;}
void put_desc_d3d(unsigned at,const D3DDEVICEDESC&d){const auto*b=reinterpret_cast<const unsigned char*>(&d);for(unsigned i=0;i<sizeof(d);++i)runtime.memory().store<unsigned char>({at+i},b[i]);}

void*d3d_query(const com::Object&dd,unsigned out,const std::function<void*(unsigned,unsigned)>&done){if(!writable(out,4))deny("QueryInterface output outside the memory contract",out);
 const unsigned g=com_wrap(nullptr,*com::by_name("IDirect3D3"),0);host.com_object(g)->refs=1;host.d3d_owner[g]=root_of(dd);store(out,g);apis.back()+="(provider IDirect3D3)";return done(DD_OK,3);}

void*d3d_call(const Import&imp,unsigned token,const std::function<unsigned(unsigned)>&arg,const std::function<void*(unsigned,unsigned)>&done){const std::string&n=imp.name;auto*o=host.com_object(arg(0));
 if(!o)deny("Call on an object that is not a live "+imp.dll,arg(0));const unsigned root=root_of(*o);auto*ro=host.com_object(root);auto&refs=ro?ro->refs:o->refs;
 if(n=="AddRef")return done(++refs,1);
 if(n=="Release"){const unsigned c=--refs;if(!c)for(auto&x:host.com_objects)if(x.alive&&root_of(x)==root)x.alive=false;return done(c,1);}
 if(imp.dll=="IDirect3D3"){
  if(n=="EnumDevices"){const unsigned cb=arg(1),ctx=arg(2);if(!find(cb))deny("EnumDevices callback has no lifted body",cb);auto&g=state.gpr;unsigned at=(g.rsp.dword-0x400)&~15U;
   at-=252;const unsigned hel=at;D3DDEVICEDESC hd{};hd.dwSize=sizeof(hd);put_desc_d3d(hel,hd);at-=252;const unsigned hal=at;put_desc_d3d(hal,hal_desc());at-=16;const unsigned guid=at;std::array<unsigned,4>w{};std::memcpy(w.data(),&IID_IDirect3DHALDevice,16);for(unsigned i=0;i<4;++i)store(guid+4*i,w[i]);
   const unsigned desc=scratch_string(at,"Vulkan HAL (MW34 RECOMP provider)"),name=scratch_string(at,"Direct3D HAL");
   const unsigned r=call_guest(cb,{guid,desc,name,hal,hel,ctx},true,"EnumDevices callback",at&~15U);apis.back()+="(1 HAL device, callback "+std::to_string(r)+")";return done(DD_OK,3);}
  if(n=="EnumZBufferFormats"){const GUID dev=guest_guid(arg(1));const unsigned cb=arg(2),ctx=arg(3);if(!IsEqualGUID(dev,IID_IDirect3DHALDevice))deny("EnumZBufferFormats for a device outside the provider",arg(1));if(!find(cb))deny("EnumZBufferFormats callback has no lifted body",cb);
   auto&g=state.gpr;const unsigned at=((g.rsp.dword-0x200)&~15U)-32;const std::array<unsigned,8>pf{32,DDPF_ZBUFFER,0,16,0,0xffff,0,0};for(unsigned i=0;i<8;++i)store(at+4*i,pf[i]);
   (void)call_guest(cb,{at,ctx},true,"EnumZBufferFormats callback",at&~15U);return done(DD_OK,4);}
  if(n=="CreateDevice"){const GUID dev=guest_guid(arg(1));const unsigned surf=arg(2),out=arg(3);if(arg(4))deny("CreateDevice aggregation is not modelled",arg(4));if(!IsEqualGUID(dev,IID_IDirect3DHALDevice))deny("CreateDevice for a device outside the provider",arg(1));
   auto*rt=vsurf_of(surf);if(!rt||!(rt->caps&DDSCAPS_3DDEVICE))deny("CreateDevice render target is not a 3D-capable virtual surface",surf);if(!writable(out,4))deny("CreateDevice output outside the memory contract",out);
   const unsigned g=com_wrap(nullptr,*com::by_name("IDirect3DDevice3"),0);host.com_object(g)->refs=1;D3DDev d{};d.guest=g;d.target=rt->guest;d.d3d=root;d3d_defaults(d,rt->zbuffer!=0);host.devices.push_back(d);store(out,g);apis.back()+="(HAL on "+std::to_string(rt->width)+"x"+std::to_string(rt->height)+")";return done(DD_OK,5);}
  // Managed textures live in guest memory and there is no separate video memory to evict from: the
  // eviction is complete with nothing to release.
  if(n=="EvictManagedTextures")return done(D3D_OK,1);
  if(n=="CreateMaterial"){const unsigned out=arg(1);if(arg(2))deny("CreateMaterial aggregation is not modelled",arg(2));if(!writable(out,4))deny("CreateMaterial output outside the memory contract",out);
   const unsigned g=com_wrap(nullptr,*com::by_name("IDirect3DMaterial3"),0);host.com_object(g)->refs=1;host.materials[g]={};store(out,g);return done(DD_OK,3);}
  if(n=="CreateViewport"){const unsigned out=arg(1);if(arg(2))deny("CreateViewport aggregation is not modelled",arg(2));if(!writable(out,4))deny("CreateViewport output outside the memory contract",out);
   const unsigned g=com_wrap(nullptr,*com::by_name("IDirect3DViewport3"),0);host.com_object(g)->refs=1;host.viewports.push_back({g});store(out,g);return done(DD_OK,3);}
 }
 if(imp.dll=="IDirect3DMaterial3"){auto it=host.materials.find(root);if(it==host.materials.end())deny("Material object without its state",root);
  if(n=="SetMaterial"||n=="GetMaterial"){const unsigned a=arg(1);if(!readable(a,4)||load(a)!=80)deny(n+" D3DMATERIAL with a wrong dwSize",a);if(n=="SetMaterial"){get_bytes(a,it->second.data(),80);return done(DD_OK,2);}
   if(!writable(a,80))deny("GetMaterial output outside the memory contract",a);for(unsigned i=0;i<80;++i)runtime.memory().store<unsigned char>({a+i},it->second[i]);return done(DD_OK,2);}
  if(n=="GetHandle"){if(!device(vsurf_root(arg(1)))||!writable(arg(2),4))deny("Material GetHandle arguments outside the model",arg(1));store(arg(2),root);return done(DD_OK,3);}}
 if(imp.dll=="IDirect3DViewport3"){auto*vp=viewport(root);if(!vp)deny("Viewport object without its state",root);
  if(n=="SetViewport2"||n=="GetViewport2"){const unsigned a=arg(1);if(!readable(a,44)||load(a)!=44)deny(n+" D3DVIEWPORT2 with a wrong dwSize",a);if(n=="SetViewport2"){get_bytes(a,vp->vp.data(),44);vp->set=true;for(auto&dd:host.devices)++dd.epoch;return done(DD_OK,2);}
   if(!vp->set)return done(unsigned(D3DERR_VIEWPORTDATANOTSET),2);if(!writable(a,44))deny("GetViewport2 output outside the memory contract",a);for(unsigned i=0;i<44;++i)runtime.memory().store<unsigned char>({a+i},vp->vp[i]);return done(DD_OK,2);}
  if(n=="SetBackground"){if(arg(1)&&!host.materials.count(arg(1)))deny("SetBackground with a handle that is not a provider material",arg(1));vp->background=arg(1);return done(DD_OK,2);}
  if(n=="GetBackground"){if(!writable(arg(1),4)||!writable(arg(2),4))deny("GetBackground outputs outside the memory contract",arg(1));store(arg(1),vp->background);store(arg(2),vp->background?1U:0U);return done(DD_OK,3);}
  if(n=="Clear"){const unsigned count=arg(1),rects=arg(2),flags=arg(3);if(count>64||!readable(rects,16*count))deny("Clear rectangles outside the memory contract",rects);auto*dev=device_with_viewport(root);if(!dev)deny("Clear on a viewport not attached to a device",root);
   unsigned color=0;if((flags&D3DCLEAR_TARGET)&&vp->background){const auto&m=host.materials[vp->background];float c[4];std::memcpy(c,m.data()+4,16);auto b=[](float x){return unsigned(std::clamp(x,0.f,1.f)*255.f+0.5f);};color=(b(c[3])<<24)|(b(c[0])<<16)|(b(c[1])<<8)|b(c[2]);}
   dev->commands.push_back({D3DCmd::Clear,flags,color,1.f,{},{},0});auto&c=dev->commands.back();for(unsigned i=0;i<count;++i)c.rects.push_back(RECT{LONG(load(rects+16*i)),LONG(load(rects+16*i+4)),LONG(load(rects+16*i+8)),LONG(load(rects+16*i+12))});
   if(!dev->in_scene)render_scene(*dev);return done(DD_OK,4);}
  if(n=="Clear2"){const unsigned count=arg(1),rects=arg(2),flags=arg(3),color=arg(4);float z;const unsigned zb=arg(5);std::memcpy(&z,&zb,4);if(count>64||!readable(rects,16*count))deny("Clear2 rectangles outside the memory contract",rects);
   auto*dev=device_with_viewport(root);if(!dev)deny("Clear2 on a viewport not attached to a device",root);dev->commands.push_back({D3DCmd::Clear,flags,color,z,{},{},0});auto&c=dev->commands.back();for(unsigned i=0;i<count;++i)c.rects.push_back(RECT{LONG(load(rects+16*i)),LONG(load(rects+16*i+4)),LONG(load(rects+16*i+8)),LONG(load(rects+16*i+12))});
   if(!dev->in_scene)render_scene(*dev);return done(DD_OK,7);}}
 if(imp.dll=="IDirect3DDevice3"){auto*dev=device(root);if(!dev)deny("Device object without its state",root);
  // The two methods issued per draw (about 1,800 pairs a frame) are selected first, by a selector resolved once per
  // import from the name; every other branch below is keyed on a different method name, so the order is equivalent.
  if(imp.op<0)imp.op=n=="SetTexture"?1:(n=="DrawPrimitive"||n=="DrawIndexedPrimitive")?2:0;
  if(imp.op==1){const unsigned stg=arg(1);if(stg>=8)deny("SetTexture stage outside the model",stg);const unsigned t=arg(2)?vsurf_root(arg(2)):0;if(t&&!vsurface(t))deny("SetTexture with an object that is not a provider texture",arg(2));dev->textures[stg]=t;return done(DD_OK,3);}
  if(imp.op==2){const unsigned type=arg(1),fvf=arg(2),verts=arg(3),vcount=arg(4);if(fvf!=D3DFVF_TLVERTEX)deny("Vertex format other than D3DFVF_TLVERTEX is not modelled",fvf);
   if(vcount>65535||!readable(verts,32*vcount))deny(n+" vertices outside the memory contract",verts);D3DCmd c{D3DCmd::Draw,type,0,0.f,{},{},0};c.vertices.resize(32*size_t(vcount));get_bytes(verts,c.vertices.data(),32*vcount);
   if(n=="DrawIndexedPrimitive"){const unsigned idx=arg(5),icount=arg(6);if(icount>196605||!readable(idx,2*icount))deny("Indices outside the memory contract",idx);c.indices.resize(icount);for(unsigned i=0;i<icount;++i)c.indices[i]=runtime.memory().load<unsigned short>({idx+2*i});}
   if(host.draw_log&&host.draw_detail_frame==host.frames+1){std::uint64_t h=0xcbf29ce484222325ULL;for(unsigned char b:c.vertices){h^=b;h*=0x100000001b3ULL;}float v0[8]{};if(c.vertices.size()>=32)std::memcpy(v0,c.vertices.data(),32);std::fprintf(host.draw_log,"  draw %u type %u n %u idx %zu v0 %.2f %.2f %.4f tex %08x %016llx\n",host.draw_calls,type,vcount,c.indices.size(),v0[0],v0[1],v0[2],dev->textures[0],(unsigned long long)h);}if(host.draw_log){++host.draw_calls;host.draw_fold(&type,4);host.draw_fold(&vcount,4);host.draw_fold(c.vertices.data(),c.vertices.size());if(!c.indices.empty())host.draw_fold(c.indices.data(),2*c.indices.size());}
   if(!dev->snap||dev->snap_epoch!=dev->epoch){dev->snap=std::make_shared<const std::vector<unsigned>>(snapshot(*dev));dev->snap_epoch=dev->epoch;}c.state_snapshot=dev->snap;c.texture=dev->textures[0];dev->commands.push_back(std::move(c));return done(DD_OK,n=="DrawPrimitive"?6:8);}
  if(n=="GetCaps"){for(auto[a,hal]:{std::pair<unsigned,bool>{arg(1),true},{arg(2),false}})if(a){if(!readable(a,4)||load(a)!=252)deny("GetCaps D3DDEVICEDESC with a wrong dwSize",a);D3DDEVICEDESC d{};d.dwSize=sizeof(d);if(hal)d=hal_desc();if(!writable(a,252))deny("GetCaps output outside the memory contract",a);put_desc_d3d(a,d);}return done(DD_OK,3);}
  if(n=="EnumTextureFormats"){const unsigned cb=arg(1),ctx=arg(2);if(!find(cb))deny("EnumTextureFormats callback has no lifted body",cb);
   for(const auto&f:texture_formats()){auto&g=state.gpr;const unsigned at=((g.rsp.dword-0x200)&~15U)-32;for(unsigned i=0;i<8;++i)store(at+4*i,f[i]);const unsigned r=call_guest(cb,{at,ctx},true,"EnumTextureFormats callback",at&~15U);if(!callback_fault.empty()||r==D3DENUMRET_CANCEL)break;}return done(DD_OK,3);}
  if(n=="AddViewport"){if(!viewport(vsurf_root(arg(1))))deny("AddViewport with an object that is not a provider viewport",arg(1));dev->viewports.push_back(vsurf_root(arg(1)));return done(DD_OK,2);}
  if(n=="DeleteViewport"){auto&v=dev->viewports;v.erase(std::remove(v.begin(),v.end(),vsurf_root(arg(1))),v.end());if(dev->current==vsurf_root(arg(1)))dev->current=0;return done(DD_OK,2);}
  if(n=="SetCurrentViewport"){const unsigned vp=vsurf_root(arg(1));if(std::find(dev->viewports.begin(),dev->viewports.end(),vp)==dev->viewports.end())deny("SetCurrentViewport with a viewport not added to the device",arg(1));dev->current=vp;++dev->epoch;return done(DD_OK,2);}
  if(n=="GetCurrentViewport"){if(!writable(arg(1),4))deny("GetCurrentViewport output outside the memory contract",arg(1));if(!dev->current)return done(unsigned(D3DERR_NOCURRENTVIEWPORT),2);++host.com_object(dev->current)->refs;store(arg(1),dev->current);return done(DD_OK,2);}
  if(n=="SetRenderState"){const unsigned st=arg(1),v=arg(2);if(st>=256)deny("Render state outside the modelled range",st);dev->rs[st]=v;++dev->epoch;
   // Legacy texture states are translated to stage 0 by the Direct3D 6 runtime for IDirect3DDevice3.
   auto&t0=dev->tss[0];
   if(st==D3DRENDERSTATE_TEXTUREMAG){if(v!=D3DFILTER_NEAREST&&v!=D3DFILTER_LINEAR)deny("TEXTUREMAG value not modelled",v);t0[D3DTSS_MAGFILTER]=v==D3DFILTER_LINEAR?D3DTFG_LINEAR:D3DTFG_POINT;}
   if(st==D3DRENDERSTATE_TEXTUREMIN){static const unsigned mn[7]={0,D3DTFN_POINT,D3DTFN_LINEAR,D3DTFN_POINT,D3DTFN_LINEAR,D3DTFN_POINT,D3DTFN_LINEAR},mp[7]={0,D3DTFP_NONE,D3DTFP_NONE,D3DTFP_POINT,D3DTFP_POINT,D3DTFP_LINEAR,D3DTFP_LINEAR};
    if(v<1||v>6)deny("TEXTUREMIN value not modelled",v);t0[D3DTSS_MINFILTER]=mn[v];t0[D3DTSS_MIPFILTER]=mp[v];}
   if(st==D3DRENDERSTATE_TEXTUREADDRESS){t0[D3DTSS_ADDRESSU]=t0[D3DTSS_ADDRESSV]=v;}
   if(st==D3DRENDERSTATE_TEXTUREADDRESSU)t0[D3DTSS_ADDRESSU]=v;
   if(st==D3DRENDERSTATE_TEXTUREADDRESSV)t0[D3DTSS_ADDRESSV]=v;
   if(st==D3DRENDERSTATE_TEXTUREMAPBLEND&&v!=D3DTBLEND_MODULATE)deny("Legacy TEXTUREMAPBLEND on IDirect3DDevice3 is not modelled",v);
   return done(DD_OK,3);}
  if(n=="GetRenderState"){const unsigned st=arg(1);if(st>=256||!writable(arg(2),4))deny("GetRenderState arguments outside the model",st);store(arg(2),dev->rs[st]);return done(DD_OK,3);}
  if(n=="SetTextureStageState"){const unsigned stg=arg(1),st=arg(2);if(stg>=8||st>=32)deny("Texture stage state outside the modelled range",st);dev->tss[stg][st]=arg(3);++dev->epoch;
   if(st==D3DTSS_ADDRESS)dev->tss[stg][D3DTSS_ADDRESSU]=dev->tss[stg][D3DTSS_ADDRESSV]=arg(3);return done(DD_OK,4);}
  if(n=="GetTextureStageState"){const unsigned stg=arg(1),st=arg(2);if(stg>=8||st>=32||!writable(arg(3),4))deny("GetTextureStageState arguments outside the model",st);store(arg(3),dev->tss[stg][st]);return done(DD_OK,4);}
  if(n=="GetTexture"){const unsigned stg=arg(1);if(stg>=8||!writable(arg(2),4))deny("GetTexture arguments outside the model",stg);store(arg(2),dev->textures[stg]);if(dev->textures[stg])++host.com_object(dev->textures[stg])->refs;return done(DD_OK,3);}
  if(n=="SetLightState"||n=="SetTransform"){if(!(n=="SetTransform"?readable(arg(2),64):true))deny("SetTransform matrix outside the memory contract",arg(2));return done(DD_OK,3);}
  if(n=="BeginScene"){if(dev->in_scene)return done(unsigned(D3DERR_SCENE_IN_SCENE),1);dev->in_scene=true;return done(DD_OK,1);}
  if(n=="EndScene"){if(!dev->in_scene)return done(unsigned(D3DERR_SCENE_NOT_IN_SCENE),1);dev->in_scene=false;render_scene(*dev);return done(DD_OK,1);}
  }
 if(imp.dll=="IDirect3DTexture2"){auto*t=vsurface(root);if(!t)deny("Texture object without its surface",root);
  if(n=="Load"){auto*s=vsurf_of(arg(1));if(!s||s->width!=t->width||s->height!=t->height||s->bpp!=t->bpp)deny("Texture Load between different surfaces is not modelled",arg(1));
   gpu_sync(s->guest);gpu_sync(t->guest);std::vector<unsigned char>b(s->bytes);get_bytes(s->mem,b.data(),s->bytes);if(t->bytes!=s->bytes)deny("Texture Load with different pitches",arg(1));write_bytes(t->mem,b.data(),unsigned(b.size()));t->tex_masks=s->tex_masks;t->version=++host.surface_versions;return done(DD_OK,2);}
  if(n=="GetHandle"){if(!writable(arg(2),4))deny("GetHandle output outside the memory contract",arg(2));store(arg(2),t->guest);return done(DD_OK,3);}}
 stop(m4_runtime::FaultReason::unresolved_import,"Direct3D provider method not implemented: "+imp.dll+"::"+n,token);}
// Texture formats the renderer samples: RGB565, ARGB1555, ARGB4444 (DDPIXELFORMAT words).
static std::vector<std::array<unsigned,8>>texture_formats(){return {{32,DDPF_RGB,0,16,0xf800,0x07e0,0x001f,0},{32,DDPF_RGB|DDPF_ALPHAPIXELS,0,16,0x7c00,0x03e0,0x001f,0x8000},{32,DDPF_RGB|DDPF_ALPHAPIXELS,0,16,0x0f00,0x00f0,0x000f,0xf000}};}
D3DDev*device(unsigned g){for(auto&d:host.devices)if(d.guest==g)return &d;return nullptr;}
D3DViewport*viewport(unsigned g){for(auto&v:host.viewports)if(v.guest==g)return &v;return nullptr;}
D3DDev*device_with_viewport(unsigned vp){for(auto&d:host.devices)if(std::find(d.viewports.begin(),d.viewports.end(),vp)!=d.viewports.end())return &d;return nullptr;}
std::vector<unsigned>snapshot(const D3DDev&d){std::vector<unsigned>v(d.rs.begin(),d.rs.end());for(unsigned s=0;s<8;++s)v.insert(v.end(),d.tss[s].begin(),d.tss[s].end());v.insert(v.end(),8,0U);  /* textures travel per draw (D3DCmd::texture) */if(d.current&&viewport(d.current)){const auto&vp=viewport(d.current)->vp;for(unsigned i=0;i<11;++i){unsigned w;std::memcpy(&w,vp.data()+4*i,4);v.push_back(w);}}return v;}
// Direct3D 6 device defaults (render states and texture stage states) as a new IDirect3DDevice3 has them.
static unsigned fbits(float x){unsigned u;std::memcpy(&u,&x,4);return u;}
static const std::array<unsigned,256>&rs_defaults(){static const std::array<unsigned,256>d=[]{std::array<unsigned,256>r{};
  r[D3DRENDERSTATE_TEXTUREADDRESS]=D3DTADDRESS_WRAP;r[D3DRENDERSTATE_TEXTUREPERSPECTIVE]=TRUE;r[D3DRENDERSTATE_FILLMODE]=D3DFILL_SOLID;r[D3DRENDERSTATE_SHADEMODE]=D3DSHADE_GOURAUD;
  r[D3DRENDERSTATE_ROP2]=R2_COPYPEN;r[D3DRENDERSTATE_PLANEMASK]=0xffffffffU;r[D3DRENDERSTATE_ZWRITEENABLE]=TRUE;r[D3DRENDERSTATE_LASTPIXEL]=TRUE;
  r[D3DRENDERSTATE_TEXTUREMAG]=D3DFILTER_NEAREST;r[D3DRENDERSTATE_TEXTUREMIN]=D3DFILTER_NEAREST;r[D3DRENDERSTATE_SRCBLEND]=D3DBLEND_ONE;r[D3DRENDERSTATE_DESTBLEND]=D3DBLEND_ZERO;
  r[D3DRENDERSTATE_TEXTUREMAPBLEND]=D3DTBLEND_MODULATE;r[D3DRENDERSTATE_CULLMODE]=D3DCULL_CCW;r[D3DRENDERSTATE_ZFUNC]=D3DCMP_LESSEQUAL;r[D3DRENDERSTATE_ALPHAFUNC]=D3DCMP_ALWAYS;
  r[D3DRENDERSTATE_SPECULARENABLE]=TRUE;r[D3DRENDERSTATE_FOGTABLEEND]=fbits(1.f);r[D3DRENDERSTATE_FOGTABLEDENSITY]=fbits(1.f);r[D3DRENDERSTATE_TEXTUREADDRESSU]=D3DTADDRESS_WRAP;
  r[D3DRENDERSTATE_TEXTUREADDRESSV]=D3DTADDRESS_WRAP;r[D3DRENDERSTATE_ANISOTROPY]=1;r[D3DRENDERSTATE_STENCILFAIL]=D3DSTENCILOP_KEEP;r[D3DRENDERSTATE_STENCILZFAIL]=D3DSTENCILOP_KEEP;
  r[D3DRENDERSTATE_STENCILPASS]=D3DSTENCILOP_KEEP;r[D3DRENDERSTATE_STENCILFUNC]=D3DCMP_ALWAYS;r[D3DRENDERSTATE_STENCILMASK]=0xffffffffU;r[D3DRENDERSTATE_STENCILWRITEMASK]=0xffffffffU;
  r[D3DRENDERSTATE_TEXTUREFACTOR]=0xffffffffU;return r;}();return d;}
void d3d_defaults(D3DDev&d,bool zbuffer){d.rs=rs_defaults();d.rs[D3DRENDERSTATE_ZENABLE]=zbuffer?D3DZB_TRUE:D3DZB_FALSE;
 for(unsigned s=0;s<8;++s){auto&t=d.tss[s];t={};t[D3DTSS_COLOROP]=s?D3DTOP_DISABLE:D3DTOP_MODULATE;t[D3DTSS_COLORARG1]=D3DTA_TEXTURE;t[D3DTSS_COLORARG2]=D3DTA_CURRENT;
  t[D3DTSS_ALPHAOP]=s?D3DTOP_DISABLE:D3DTOP_SELECTARG1;t[D3DTSS_ALPHAARG1]=D3DTA_TEXTURE;t[D3DTSS_ALPHAARG2]=D3DTA_CURRENT;t[D3DTSS_TEXCOORDINDEX]=s;
  t[D3DTSS_ADDRESS]=t[D3DTSS_ADDRESSU]=t[D3DTSS_ADDRESSV]=D3DTADDRESS_WRAP;t[D3DTSS_MAGFILTER]=D3DTFG_POINT;t[D3DTSS_MINFILTER]=D3DTFN_POINT;t[D3DTSS_MIPFILTER]=D3DTFP_NONE;t[D3DTSS_MAXANISOTROPY]=1;}}
// Render states the renderer interprets, and states with no effect on transformed-and-lit triangles
// (line/point-only, hint, transform/lighting, fog-table parameters without table fog, legacy states
// already translated to stage 0). Any other state that differs from its default is refused.
static bool rs_handled(unsigned k){switch(k){case D3DRENDERSTATE_TEXTUREADDRESS:case D3DRENDERSTATE_TEXTUREPERSPECTIVE:case D3DRENDERSTATE_ZENABLE:case D3DRENDERSTATE_FILLMODE:
  case D3DRENDERSTATE_SHADEMODE:case D3DRENDERSTATE_LINEPATTERN:case D3DRENDERSTATE_ZWRITEENABLE:case D3DRENDERSTATE_ALPHATESTENABLE:case D3DRENDERSTATE_LASTPIXEL:
  case D3DRENDERSTATE_TEXTUREMAG:case D3DRENDERSTATE_TEXTUREMIN:case D3DRENDERSTATE_SRCBLEND:case D3DRENDERSTATE_DESTBLEND:case D3DRENDERSTATE_TEXTUREMAPBLEND:
  case D3DRENDERSTATE_CULLMODE:case D3DRENDERSTATE_ZFUNC:case D3DRENDERSTATE_ALPHAREF:case D3DRENDERSTATE_ALPHAFUNC:case D3DRENDERSTATE_DITHERENABLE:
  case D3DRENDERSTATE_ALPHABLENDENABLE:case D3DRENDERSTATE_FOGENABLE:case D3DRENDERSTATE_SPECULARENABLE:case D3DRENDERSTATE_ZVISIBLE:case D3DRENDERSTATE_SUBPIXEL:
  case D3DRENDERSTATE_SUBPIXELX:case D3DRENDERSTATE_FOGCOLOR:case D3DRENDERSTATE_FOGTABLEMODE:case D3DRENDERSTATE_FOGTABLESTART:case D3DRENDERSTATE_FOGTABLEEND:
  case D3DRENDERSTATE_FOGTABLEDENSITY:case D3DRENDERSTATE_TEXTUREADDRESSU:case D3DRENDERSTATE_TEXTUREADDRESSV:case D3DRENDERSTATE_MIPMAPLODBIAS:
  case D3DRENDERSTATE_RANGEFOGENABLE:case D3DRENDERSTATE_ANISOTROPY:case D3DRENDERSTATE_FLUSHBATCH:case D3DRENDERSTATE_TRANSLUCENTSORTINDEPENDENT:
  case D3DRENDERSTATE_COLORKEYENABLE:case D3DRENDERSTATE_TEXTUREFACTOR:return true;default:return k>=136&&k<160;}}
// Scene execution. Scenes holding only clears are applied to guest memory directly (target and 16-bit
// z-buffer); scenes with draws are rendered by the Vulkan scene renderer into the guest target and z-buffer.
void render_scene(D3DDev&d){auto*rt=vsurface(d.target);if(!rt)deny("Scene render target is gone",d.target);if(rt->bpp!=16)deny("Scene render target is not 16-bit",rt->bpp);
 VSurfaceRec*zb=rt->zbuffer?vsurface(rt->zbuffer):nullptr;if(zb&&(zb->bpp!=16||zb->width!=rt->width||zb->height!=rt->height))deny("Z-buffer surface outside the model",rt->zbuffer);
 const bool draws=std::any_of(d.commands.begin(),d.commands.end(),[](const D3DCmd&c){return c.kind==D3DCmd::Draw;});
 auto clip=[&](const RECT&r){RECT c{std::max<LONG>(r.left,0),std::max<LONG>(r.top,0),std::min<LONG>(r.right,LONG(rt->width)),std::min<LONG>(r.bottom,LONG(rt->height))};return c;};
 if(!draws){for(const auto&c:d.commands){const unsigned px=((c.a>>8)&0xf800)|((c.a>>5)&0x07e0)|((c.a>>3)&0x001f);
   for(const auto&r0:c.rects){const RECT r=clip(r0);if(r.right<=r.left||r.bottom<=r.top)continue;if(c.flags&D3DCLEAR_TARGET)fill(*rt,r,px);
    if((c.flags&D3DCLEAR_ZBUFFER)&&zb){const unsigned zv=unsigned(std::lround(std::clamp(c.z,0.f,1.f)*65535.f));fill(*zb,r,zv);}}}
  d.commands.clear();return;}
 if(!host.scene_t0)host.scene_t0=host.vclock()?std::max<std::uint64_t>(host.vclock_us/1000,1): ::GetTickCount64();
 namespace vs=mw34::vkscene;vs::Scene sc{};sc.width=rt->width;sc.height=rt->height;const size_t px=size_t(sc.width)*sc.height;sc.has_depth=zb!=nullptr;
 auto rows_in=[&](const VSurfaceRec&v,std::vector<std::uint16_t>&out){std::vector<unsigned char>row(size_t(v.width)*2);for(unsigned y=0;y<v.height;++y){get_bytes(v.mem+y*v.pitch,row.data(),unsigned(row.size()));std::memcpy(out.data()+size_t(y)*v.width,row.data(),row.size());}};
 const bool lazy=lazy_rt();if(lazy&&host.res_dirty&&(host.res_rt!=rt->guest||host.res_zb!=(zb?zb->guest:0U)))gpu_sync(0);
 bool rescale=false;if(lazy){auto*sr=scene_renderer();if(sr==host.presenter.get()){const float want=render_scale(rt->height);
  if(want!=sr->current_scale()){rescale=true;if(host.res_dirty)gpu_sync(0);}sr->request_scale(want);}}  /* a new scale recreates the target: its content moves through guest memory */
 const bool keep=lazy&&!rescale&&host.sren&&host.res_rt==rt->guest&&host.res_zb==(zb?zb->guest:0U)&&(host.res_dirty||(rt->version==host.res_ver_rt&&(!zb||zb->version==host.res_ver_zb)));
 if(!keep){sc.color.resize(px);sc.depth.assign(px,0);rows_in(*rt,sc.color);if(zb)rows_in(*zb,sc.depth);}  /* a resident scene (keep) uploads nothing and needs no host buffers */
 std::map<unsigned,int>tex_index;const auto&dflt=rs_defaults();const std::vector<unsigned>*validated=nullptr;
 for(const auto&c:d.commands){
  if(c.kind==D3DCmd::Clear){vs::Clear k{};k.flags=(c.flags&D3DCLEAR_TARGET?1U:0U)|(c.flags&D3DCLEAR_ZBUFFER?2U:0U);k.color[0]=float((c.a>>16)&255)/255.f;k.color[1]=float((c.a>>8)&255)/255.f;k.color[2]=float(c.a&255)/255.f;k.color[3]=float(c.a>>24)/255.f;k.z=std::clamp(c.z,0.f,1.f);
   for(const auto&r0:c.rects){const RECT r=clip(r0);if(r.right>r.left&&r.bottom>r.top)k.rects.push_back({{r.left,r.top},{unsigned(r.right-r.left),unsigned(r.bottom-r.top)}});}
   sc.order.push_back({true,unsigned(sc.clears.size())});sc.clears.push_back(std::move(k));continue;}
  const auto&v=*c.state_snapshot;if(v.size()<520+11)deny("Draw state snapshot without a viewport",unsigned(v.size()));const bool fresh=c.state_snapshot.get()!=validated;validated=c.state_snapshot.get();auto rs=[&](unsigned k){return v[k];};auto ts=[&](unsigned s,unsigned k){return v[256+32*s+k];};
  if(fresh)for(unsigned k=0;k<256;++k)if(v[k]!=dflt[k]&&!rs_handled(k)&&!(k==D3DRENDERSTATE_ZENABLE))deny("Render state "+std::to_string(k)+"="+std::to_string(v[k])+" is not modelled by the scene renderer",k);
  if(rs(D3DRENDERSTATE_FILLMODE)!=D3DFILL_SOLID)deny("Non-solid fill mode is not modelled",rs(D3DRENDERSTATE_FILLMODE));
  if(rs(D3DRENDERSTATE_ZENABLE)>D3DZB_TRUE)deny("W-buffering is not modelled",rs(D3DRENDERSTATE_ZENABLE));
  if(rs(D3DRENDERSTATE_FOGENABLE)&&rs(D3DRENDERSTATE_FOGTABLEMODE)!=D3DFOG_NONE)deny("Table fog is not modelled",rs(D3DRENDERSTATE_FOGTABLEMODE));
  if(ts(0,D3DTSS_COLOROP)<1||ts(0,D3DTSS_COLOROP)>14||ts(0,D3DTSS_ALPHAOP)<1||ts(0,D3DTSS_ALPHAOP)>14)deny("Texture stage 0 operation not modelled",ts(0,D3DTSS_COLOROP)|ts(0,D3DTSS_ALPHAOP)<<8);
  for(unsigned a:{ts(0,D3DTSS_COLORARG1),ts(0,D3DTSS_COLORARG2),ts(0,D3DTSS_ALPHAARG1),ts(0,D3DTSS_ALPHAARG2)})if((a&15)>4||(a&~0x3fU))deny("Texture stage 0 argument not modelled",a);
  if(ts(0,D3DTSS_TEXCOORDINDEX)!=0)deny("Texture coordinate index not modelled",ts(0,D3DTSS_TEXCOORDINDEX));
  if(ts(1,D3DTSS_COLOROP)!=D3DTOP_DISABLE)deny("Texture stage 1 is not modelled",ts(1,D3DTSS_COLOROP));
  for(unsigned a:{ts(0,D3DTSS_ADDRESSU),ts(0,D3DTSS_ADDRESSV)})if(a<1||a>3)deny("Texture address mode not modelled",a);
  if(ts(0,D3DTSS_MAGFILTER)>D3DTFG_LINEAR||ts(0,D3DTSS_MINFILTER)>D3DTFN_LINEAR)deny("Texture filter not modelled",ts(0,D3DTSS_MAGFILTER)|ts(0,D3DTSS_MINFILTER)<<8);
  vs::Draw dr{};dr.first=unsigned(sc.vertices.size()/32);dr.texture=-1;
  const unsigned tex=c.texture;if(tex){auto*t=vsurface(tex);if(!t)deny("Draw with a texture that is gone",tex);
   if(rs(D3DRENDERSTATE_COLORKEYENABLE)&&t->has_src_key)deny("Texture colour keying is not modelled",tex);
   auto it=tex_index.find(tex);if(it==tex_index.end()){vs::TextureRef r{};r.key=tex;r.width=t->width;r.height=t->height;
    r.format=t->tex_masks[0]==0xf800?vs::TexFormat::rgb565:t->tex_masks[0]==0x7c00?vs::TexFormat::argb1555:t->tex_masks[0]==0x0f00?vs::TexFormat::argb4444:(deny("Texture pixel format not modelled",t->tex_masks[0]),vs::TexFormat::rgb565);
    if(t->bpp!=16)deny("Texture depth not modelled",t->bpp);r.hash=t->version;if(!host.sren||!host.sren->current(tex,t->version,t->width,t->height)){gpu_sync(t->guest);r.pixels.resize(size_t(t->width)*t->height);rows_in(*t,r.pixels);}
    it=tex_index.emplace(tex,int(sc.textures.size())).first;sc.textures.push_back(std::move(r));}dr.texture=it->second;}
  dr.sampler=(ts(0,D3DTSS_MAGFILTER)==D3DTFG_LINEAR?1U:0U)|(ts(0,D3DTSS_MINFILTER)==D3DTFN_LINEAR?2U:0U)|(ts(0,D3DTSS_ADDRESSU)<<4)|(ts(0,D3DTSS_ADDRESSV)<<8);
  dr.key={std::uint8_t(rs(D3DRENDERSTATE_ALPHABLENDENABLE)!=0),std::uint8_t(rs(D3DRENDERSTATE_SRCBLEND)),std::uint8_t(rs(D3DRENDERSTATE_DESTBLEND)),std::uint8_t(zb&&rs(D3DRENDERSTATE_ZENABLE)),
          std::uint8_t(rs(D3DRENDERSTATE_ZFUNC)),std::uint8_t(rs(D3DRENDERSTATE_ZWRITEENABLE)!=0),std::uint8_t(rs(D3DRENDERSTATE_CULLMODE))};
  if(dr.key.src<1||dr.key.src>13||dr.key.dst<1||dr.key.dst>13||dr.key.zfunc<1||dr.key.zfunc>8||dr.key.cull<1||dr.key.cull>3)deny("Blend, depth or cull state outside the model",dr.key.src|dr.key.dst<<8);
  auto&pu=dr.push;pu.target[0]=float(sc.width);pu.target[1]=float(sc.height);pu.target[2]=0.5f;const unsigned fc=rs(D3DRENDERSTATE_FOGCOLOR),tf=rs(D3DRENDERSTATE_TEXTUREFACTOR);
  pu.fog[0]=float((fc>>16)&255)/255.f;pu.fog[1]=float((fc>>8)&255)/255.f;pu.fog[2]=float(fc&255)/255.f;pu.fog[3]=1;pu.factor[0]=float((tf>>16)&255)/255.f;pu.factor[1]=float((tf>>8)&255)/255.f;pu.factor[2]=float(tf&255)/255.f;pu.factor[3]=float(tf>>24)/255.f;
  pu.mode[0]=(rs(D3DRENDERSTATE_SHADEMODE)==D3DSHADE_FLAT?1U:0U)|(rs(D3DRENDERSTATE_TEXTUREPERSPECTIVE)?2U:0U)|(tex?4U:0U)|(rs(D3DRENDERSTATE_SPECULARENABLE)?8U:0U)|(rs(D3DRENDERSTATE_FOGENABLE)?16U:0U)|(rs(D3DRENDERSTATE_ALPHATESTENABLE)?32U:0U);
  pu.mode[1]=ts(0,D3DTSS_COLOROP)|ts(0,D3DTSS_COLORARG1)<<8|ts(0,D3DTSS_COLORARG2)<<16;pu.mode[2]=ts(0,D3DTSS_ALPHAOP)|ts(0,D3DTSS_ALPHAARG1)<<8|ts(0,D3DTSS_ALPHAARG2)<<16;
  pu.mode[3]=(rs(D3DRENDERSTATE_ALPHAFUNC)&255)|(rs(D3DRENDERSTATE_ALPHAREF)&255)<<8;
  {const LONG x=LONG(v[521]),y=LONG(v[522]);const RECT r=clip(RECT{x,y,x+LONG(v[523]),y+LONG(v[524])});dr.scissor={{r.left,r.top},{unsigned(std::max<LONG>(r.right-r.left,0)),unsigned(std::max<LONG>(r.bottom-r.top,0))}};}
  // Primitives become a triangle list in Direct3D order with the first vertex of each triangle first
  // (the flat-shading colour source), preserving each triangle's winding.
  const size_t nv=c.indices.empty()?c.vertices.size()/32:c.indices.size();auto vert=[&](size_t i){const size_t k=c.indices.empty()?i:c.indices[i];if(k*32+32>c.vertices.size())deny("Draw index outside its vertices",unsigned(k));sc.vertices.insert(sc.vertices.end(),c.vertices.begin()+std::ptrdiff_t(k*32),c.vertices.begin()+std::ptrdiff_t(k*32+32));};
  if(c.flags==D3DPT_TRIANGLELIST){for(size_t i=0;i+2<nv;i+=3){vert(i);vert(i+1);vert(i+2);}}
  else if(c.flags==D3DPT_TRIANGLESTRIP){for(size_t i=0;i+2<nv;++i){if(i&1){vert(i);vert(i+2);vert(i+1);}else{vert(i);vert(i+1);vert(i+2);}}}
  else if(c.flags==D3DPT_TRIANGLEFAN){for(size_t i=1;i+1<nv;++i){vert(i);vert(i+1);vert(0);}}
  else if(c.flags==D3DPT_POINTLIST){for(size_t i=0;i<nv;++i)vert(i);dr.key.points=1;}  // one-pixel points (shader point size 1)
  else deny("Primitive type not modelled by the scene renderer",c.flags);
  dr.count=unsigned(sc.vertices.size()/32)-dr.first;sc.order.push_back({false,unsigned(sc.draws.size())});sc.draws.push_back(dr);}
 scene_renderer();try{HostInternal hi(*this);host.sren->render(sc,!keep,!lazy);}catch(const std::exception&e){deny(std::string(e.what()),0);}
 if(lazy){rt->version=++host.surface_versions;if(zb)zb->version=++host.surface_versions;host.res_rt=rt->guest;host.res_zb=zb?zb->guest:0U;host.res_ver_rt=rt->version;host.res_ver_zb=zb?zb->version:0U;
  host.res_dirty=true;gpu_protect(true);if(host.sren->scenes==1)apis.back()+="(Vulkan scene renderer on "+host.sren->device_name+", lazy residency)";d.commands.clear();return;}
 auto rows_out=[&](VSurfaceRec&v,const std::vector<std::uint16_t>&in){for(unsigned y=0;y<v.height;++y)write_bytes(v.mem+y*v.pitch,in.data()+size_t(y)*v.width,v.width*2);};
 {static const bool poison=[]{const char*e=std::getenv("MW34_RT_POISON");return e&&*e=='1';}();if(poison)std::fill(sc.color.begin(),sc.color.end(),std::uint16_t(0xf81f));}  /* MW34_RT_POISON=1 (diagnostic): the copied-back 3D image is magenta, exposing software HUD reads */
 rows_out(*rt,sc.color);rt->version=++host.surface_versions;if(zb){static const bool zp=[]{const char*e=std::getenv("MW34_ZB_PERTURB");return e&&*e=='1';}();if(zp)for(auto&v:sc.depth)if(v)--v;  /* MW34_ZB_PERTURB=1 (diagnostic): depth written back one unit nearer */
 rows_out(*zb,sc.depth);zb->version=++host.surface_versions;}
 if(host.sren->scenes==1)apis.back()+="(Vulkan scene renderer on "+host.sren->device_name+")";
 d.commands.clear();}
