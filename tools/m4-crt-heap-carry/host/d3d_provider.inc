// Additional temporal sources retain their original TL color command. Only a
// byte-identical, unmodified polygon can provide diagnostic raw geometry.
void capture_world_inputs(D3DCmd &draw, unsigned target) {
    if (world_scope && world_scope->temporal_only) {
        auto candidate = draw;
        world_capture(candidate);
        if (candidate.model && candidate.vertices == draw.vertices) {
            camera_capture(candidate, target);
            temporal_source_capture(candidate);
            draw.temporal_model = std::move(candidate.model);
            draw.camera_view = std::move(candidate.camera_view);
            draw.temporal_source = std::move(candidate.temporal_source);
        }
        return;
    }
    world_capture(draw);
    camera_capture(draw, target);
    temporal_source_capture(draw);
}
// Direct3D3 provider (project-implemented, rendered through Vulkan; included inside mf::Stage).
// The real x64 DirectDraw has no Direct3D3, so QueryInterface(IID_IDirect3D3) on any DirectDraw object
// yields this provider's IDirect3D3. It reports one HAL device whose caps describe what the Vulkan
// renderer implements (pre-transformed vertices, Gouraud/flat shading, perspective-correct bilinear
// textures, alpha blending, vertex fog, 16-bit colour and depth). Draws are collected per scene and
// rendered at EndScene into the render-target surface. Methods without an implementation stop typed.

mw34::submission::DrawVertexScratch draw_vertex_scratch;

// D3DDEVICEDESC (DX6, 252 bytes): DWORD/float fields only, identical x86/x64 layout.
D3DDEVICEDESC hal_desc(){D3DDEVICEDESC d{};d.dwSize=sizeof(d);static_assert(sizeof(D3DDEVICEDESC)==252);
 unsigned max_texture=256;if(std::getenv("MW34_REMASTER_BANKS")||override_enabled()){
  if(!host.presenter)host.presenter=std::make_unique<mw34::vkscene::Renderer>();
  try{HostInternal hi(*this);max_texture=render_idle("texture limit",[&]{return host.presenter->max_texture_dimension(host.display.window);});}catch(const std::exception&e){deny(std::string(e.what()),0);}}
 d.dwFlags=D3DDD_COLORMODEL|D3DDD_DEVCAPS|D3DDD_TRANSFORMCAPS|D3DDD_LIGHTINGCAPS|D3DDD_BCLIPPING|D3DDD_LINECAPS|D3DDD_TRICAPS|D3DDD_DEVICERENDERBITDEPTH|D3DDD_DEVICEZBUFFERBITDEPTH|D3DDD_MAXBUFFERSIZE|D3DDD_MAXVERTEXCOUNT;
 d.dcmColorModel=D3DCOLOR_RGB;d.dwDevCaps=D3DDEVCAPS_FLOATTLVERTEX|D3DDEVCAPS_EXECUTESYSTEMMEMORY|D3DDEVCAPS_TLVERTEXSYSTEMMEMORY|D3DDEVCAPS_TEXTUREVIDEOMEMORY|D3DDEVCAPS_DRAWPRIMTLVERTEX|D3DDEVCAPS_CANRENDERAFTERFLIP|D3DDEVCAPS_TEXTURENONLOCALVIDMEM|D3DDEVCAPS_DRAWPRIMITIVES2|D3DDEVCAPS_HWRASTERIZATION;
 d.dtcTransformCaps.dwSize=sizeof(D3DTRANSFORMCAPS);d.dlcLightingCaps.dwSize=sizeof(D3DLIGHTINGCAPS);d.bClipping=TRUE;
 for(auto*p:{&d.dpcLineCaps,&d.dpcTriCaps}){p->dwSize=sizeof(D3DPRIMCAPS);p->dwMiscCaps=D3DPMISCCAPS_CULLNONE|D3DPMISCCAPS_CULLCW|D3DPMISCCAPS_CULLCCW|D3DPMISCCAPS_MASKZ;
  p->dwRasterCaps=D3DPRASTERCAPS_DITHER|D3DPRASTERCAPS_ZTEST|D3DPRASTERCAPS_FOGVERTEX|D3DPRASTERCAPS_SUBPIXEL;p->dwZCmpCaps=0xff;p->dwSrcBlendCaps=D3DPBLENDCAPS_ZERO|D3DPBLENDCAPS_ONE|D3DPBLENDCAPS_SRCALPHA|D3DPBLENDCAPS_INVSRCALPHA;
  p->dwDestBlendCaps=p->dwSrcBlendCaps;p->dwAlphaCmpCaps=0xff;p->dwShadeCaps=D3DPSHADECAPS_COLORFLATRGB|D3DPSHADECAPS_COLORGOURAUDRGB|D3DPSHADECAPS_ALPHAFLATBLEND|D3DPSHADECAPS_ALPHAGOURAUDBLEND|D3DPSHADECAPS_FOGFLAT|D3DPSHADECAPS_FOGGOURAUD;
  p->dwTextureCaps=D3DPTEXTURECAPS_PERSPECTIVE|D3DPTEXTURECAPS_POW2|D3DPTEXTURECAPS_ALPHA|D3DPTEXTURECAPS_TRANSPARENCY;p->dwTextureFilterCaps=D3DPTFILTERCAPS_NEAREST|D3DPTFILTERCAPS_LINEAR;
  p->dwTextureBlendCaps=D3DPTBLENDCAPS_MODULATE|D3DPTBLENDCAPS_MODULATEALPHA|D3DPTBLENDCAPS_DECAL|D3DPTBLENDCAPS_COPY;p->dwTextureAddressCaps=D3DPTADDRESSCAPS_WRAP|D3DPTADDRESSCAPS_CLAMP;}
 d.dwDeviceRenderBitDepth=DDBD_16;d.dwDeviceZBufferBitDepth=DDBD_16;d.dwMaxBufferSize=0;d.dwMaxVertexCount=65535;d.dwMinTextureWidth=1;d.dwMinTextureHeight=1;d.dwMaxTextureWidth=max_texture;d.dwMaxTextureHeight=max_texture;
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
   const unsigned g=com_wrap(nullptr,*com::by_name("IDirect3DDevice3"),0);host.com_object(g)->refs=1;D3DDev d{};d.guest=g;d.target=rt->guest;d.d3d=root;d3d_defaults(d,rt->zbuffer!=0);host.devices.push_back(d);store(out,g);device_fog_created(out,d.rs[D3DRENDERSTATE_FOGENABLE]);apis.back()+="(HAL on "+std::to_string(rt->width)+"x"+std::to_string(rt->height)+")";return done(DD_OK,5);}
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
   dev->commands.push_back({D3DCmd::Clear,flags,color,1.f,{},{},0});auto&c=dev->commands.back();c.hud_role=wide_hud_role();for(unsigned i=0;i<count;++i)c.rects.push_back(RECT{LONG(load(rects+16*i)),LONG(load(rects+16*i+4)),LONG(load(rects+16*i+8)),LONG(load(rects+16*i+12))});
   if(!dev->in_scene)render_scene(*dev);return done(DD_OK,4);}
  if(n=="Clear2"){const unsigned count=arg(1),rects=arg(2),flags=arg(3),color=arg(4);float z;const unsigned zb=arg(5);std::memcpy(&z,&zb,4);if(count>64||!readable(rects,16*count))deny("Clear2 rectangles outside the memory contract",rects);
   auto*dev=device_with_viewport(root);if(!dev)deny("Clear2 on a viewport not attached to a device",root);dev->commands.push_back({D3DCmd::Clear,flags,color,z,{},{},0});auto&c=dev->commands.back();c.hud_role=wide_hud_role();for(unsigned i=0;i<count;++i)c.rects.push_back(RECT{LONG(load(rects+16*i)),LONG(load(rects+16*i+4)),LONG(load(rects+16*i+8)),LONG(load(rects+16*i+12))});
   if(!dev->in_scene)render_scene(*dev);return done(DD_OK,7);}}
 if(imp.dll=="IDirect3DDevice3"){auto*dev=device(root);if(!dev)deny("Device object without its state",root);
  // The two methods issued per draw (about 1,800 pairs a frame) are selected first, by a selector resolved once per
  // import from the name; every other branch below is keyed on a different method name, so the order is equivalent.
  if(imp.op<0)imp.op=n=="SetTexture"?1:(n=="DrawPrimitive"||n=="DrawIndexedPrimitive")?2:0;
  if(imp.op==1){const unsigned stg=arg(1);if(stg>=8)deny("SetTexture stage outside the model",stg);const unsigned t=arg(2)?vsurf_root(arg(2)):0;if(t&&!vsurface(t))deny("SetTexture with an object that is not a provider texture",arg(2));dev->textures[stg]=t;return done(DD_OK,3);}
  if(imp.op==2){const unsigned type=arg(1),fvf=arg(2),verts=arg(3),vcount=arg(4);if(fvf!=D3DFVF_TLVERTEX)deny("Vertex format other than D3DFVF_TLVERTEX is not modelled",fvf);
   if(vcount>65535||!readable(verts,32*vcount))deny(n+" vertices outside the memory contract",verts);D3DCmd c{D3DCmd::Draw,type,0,0.f,{},{},0};draw_vertex_scratch.prepare(c.vertices,32*size_t(vcount));get_bytes(verts,c.vertices.data(),32*vcount);
   if(n=="DrawIndexedPrimitive"){const unsigned idx=arg(5),icount=arg(6);if(icount>196605||!readable(idx,2*icount))deny("Indices outside the memory contract",idx);c.indices.resize(icount);for(unsigned i=0;i<icount;++i)c.indices[i]=runtime.memory().load<unsigned short>({idx+2*i});}
   if(host.draw_log&&host.draw_detail_frame==host.frames+1){std::uint64_t h=0xcbf29ce484222325ULL;for(unsigned char b:c.vertices){h^=b;h*=0x100000001b3ULL;}float v0[8]{};if(c.vertices.size()>=32)std::memcpy(v0,c.vertices.data(),32);std::fprintf(host.draw_log,"  draw %u type %u n %u idx %zu v0 %.2f %.2f %.4f tex %08x %016llx\n",host.draw_calls,type,vcount,c.indices.size(),v0[0],v0[1],v0[2],dev->textures[0],(unsigned long long)h);}if(host.draw_log){++host.draw_calls;host.draw_fold(&type,4);host.draw_fold(&vcount,4);host.draw_fold(c.vertices.data(),c.vertices.size());if(!c.indices.empty())host.draw_fold(c.indices.data(),2*c.indices.size());}
   if(!dev->snap||dev->snap_epoch!=dev->epoch){dev->snap=std::make_shared<const std::vector<unsigned>>(snapshot(*dev));dev->snap_epoch=dev->epoch;}c.state_snapshot=dev->snap;c.texture=dev->textures[0];c.hud_role=hud_deferred_role(type,verts,vcount,wide_hud_role());c.condition_schematic=override_status_preview();zoom_capture_command(c);divergence_trace(c);capture_world_inputs(c,dev->target);sun_capture_tl(c);sun_capture_sky(c);effect_observe(c);if(c.condition_schematic)override_emit(&c);if(!override_suppress_draw()&&!photo_replay_suppress_d3d_draw(c.hud_role)){
    static const bool early=[] {
     const char* value=std::getenv("MW34_EARLY_TRIANGLE_COMMANDS");
     if(!value||!*value||!std::strcmp(value,"0"))return false;
     if(!std::strcmp(value,"1"))return true;
     throw std::runtime_error("MW34_EARLY_TRIANGLE_COMMANDS must be 0 or 1");
    }();
    if(early)mw34::submission::append_triangle_command(dev->commands,std::move(c));
    else dev->commands.push_back(std::move(c));
   }draw_vertex_scratch.recycle(c.vertices);return done(DD_OK,n=="DrawPrimitive"?6:8);}
  if(n=="GetCaps"){for(auto[a,hal]:{std::pair<unsigned,bool>{arg(1),true},{arg(2),false}})if(a){if(!readable(a,4)||load(a)!=252)deny("GetCaps D3DDEVICEDESC with a wrong dwSize",a);D3DDEVICEDESC d{};d.dwSize=sizeof(d);if(hal)d=hal_desc();if(!writable(a,252))deny("GetCaps output outside the memory contract",a);put_desc_d3d(a,d);}return done(DD_OK,3);}
  if(n=="EnumTextureFormats"){const unsigned cb=arg(1),ctx=arg(2);if(!find(cb))deny("EnumTextureFormats callback has no lifted body",cb);
   for(const auto&f:texture_formats()){auto&g=state.gpr;const unsigned at=((g.rsp.dword-0x200)&~15U)-32;for(unsigned i=0;i<8;++i)store(at+4*i,f[i]);const unsigned r=call_guest(cb,{at,ctx},true,"EnumTextureFormats callback",at&~15U);if(!callback_fault.empty()||r==D3DENUMRET_CANCEL)break;}return done(DD_OK,3);}
  if(n=="AddViewport"){if(!viewport(vsurf_root(arg(1))))deny("AddViewport with an object that is not a provider viewport",arg(1));dev->viewports.push_back(vsurf_root(arg(1)));return done(DD_OK,2);}
  if(n=="DeleteViewport"){auto&v=dev->viewports;v.erase(std::remove(v.begin(),v.end(),vsurf_root(arg(1))),v.end());if(dev->current==vsurf_root(arg(1))){dev->current=0;++dev->epoch;}return done(DD_OK,2);}
  if(n=="SetCurrentViewport"){const unsigned vp=vsurf_root(arg(1));if(std::find(dev->viewports.begin(),dev->viewports.end(),vp)==dev->viewports.end())deny("SetCurrentViewport with a viewport not added to the device",arg(1));dev->current=vp;++dev->epoch;return done(DD_OK,2);}
  if(n=="GetCurrentViewport"){if(!writable(arg(1),4))deny("GetCurrentViewport output outside the memory contract",arg(1));if(!dev->current)return done(unsigned(D3DERR_NOCURRENTVIEWPORT),2);++host.com_object(dev->current)->refs;store(arg(1),dev->current);return done(DD_OK,2);}
  if(n=="SetRenderState"){const unsigned st=arg(1),v=arg(2);if(st>=256)deny("Render state outside the modelled range",st);const bool reuse=render_reuse_enabled();bool invalidated=false;
   // A repeated legacy state can still restore aliases changed through TSS.
   auto assign=[&](unsigned& cell,unsigned value){if(!reuse||cell!=value){cell=value;if(!invalidated){++dev->epoch;invalidated=true;}}};assign(dev->rs[st],v);
   // Legacy texture states are translated to stage 0 by the Direct3D 6 runtime for IDirect3DDevice3.
   auto&t0=dev->tss[0];
   if(st==D3DRENDERSTATE_TEXTUREMAG){if(v!=D3DFILTER_NEAREST&&v!=D3DFILTER_LINEAR)deny("TEXTUREMAG value not modelled",v);assign(t0[D3DTSS_MAGFILTER],v==D3DFILTER_LINEAR?D3DTFG_LINEAR:D3DTFG_POINT);}
   if(st==D3DRENDERSTATE_TEXTUREMIN){static const unsigned mn[7]={0,D3DTFN_POINT,D3DTFN_LINEAR,D3DTFN_POINT,D3DTFN_LINEAR,D3DTFN_POINT,D3DTFN_LINEAR},mp[7]={0,D3DTFP_NONE,D3DTFP_NONE,D3DTFP_POINT,D3DTFP_POINT,D3DTFP_LINEAR,D3DTFP_LINEAR};
    if(v<1||v>6)deny("TEXTUREMIN value not modelled",v);assign(t0[D3DTSS_MINFILTER],mn[v]);assign(t0[D3DTSS_MIPFILTER],mp[v]);}
   if(st==D3DRENDERSTATE_TEXTUREADDRESS){assign(t0[D3DTSS_ADDRESSV],v);assign(t0[D3DTSS_ADDRESSU],v);}
   if(st==D3DRENDERSTATE_TEXTUREADDRESSU)assign(t0[D3DTSS_ADDRESSU],v);
   if(st==D3DRENDERSTATE_TEXTUREADDRESSV)assign(t0[D3DTSS_ADDRESSV],v);
   if(st==D3DRENDERSTATE_TEXTUREMAPBLEND&&v!=D3DTBLEND_MODULATE)deny("Legacy TEXTUREMAPBLEND on IDirect3DDevice3 is not modelled",v);
   return done(DD_OK,3);}
  if(n=="GetRenderState"){const unsigned st=arg(1);if(st>=256||!writable(arg(2),4))deny("GetRenderState arguments outside the model",st);store(arg(2),dev->rs[st]);return done(DD_OK,3);}
  if(n=="SetTextureStageState"){const unsigned stg=arg(1),st=arg(2);if(stg>=8||st>=32)deny("Texture stage state outside the modelled range",st);const bool reuse=render_reuse_enabled();bool invalidated=false;
   // A repeated legacy state can still restore aliases changed through TSS.
   auto assign=[&](unsigned& cell,unsigned value){if(!reuse||cell!=value){cell=value;if(!invalidated){++dev->epoch;invalidated=true;}}};assign(dev->tss[stg][st],arg(3));
   if(st==D3DTSS_ADDRESS){assign(dev->tss[stg][D3DTSS_ADDRESSV],arg(3));assign(dev->tss[stg][D3DTSS_ADDRESSU],arg(3));}return done(DD_OK,4);}
  if(n=="GetTextureStageState"){const unsigned stg=arg(1),st=arg(2);if(stg>=8||st>=32||!writable(arg(3),4))deny("GetTextureStageState arguments outside the model",st);store(arg(3),dev->tss[stg][st]);return done(DD_OK,4);}
  if(n=="GetTexture"){const unsigned stg=arg(1);if(stg>=8||!writable(arg(2),4))deny("GetTexture arguments outside the model",stg);store(arg(2),dev->textures[stg]);if(dev->textures[stg])++host.com_object(dev->textures[stg])->refs;return done(DD_OK,3);}
  if(n=="SetLightState"||n=="SetTransform"){if(!(n=="SetTransform"?readable(arg(2),64):true))deny("SetTransform matrix outside the memory contract",arg(2));return done(DD_OK,3);}
  if(n=="BeginScene"){if(dev->in_scene)return done(unsigned(D3DERR_SCENE_IN_SCENE),1);dev->in_scene=true;override_scene_start();return done(DD_OK,1);}
  if(n=="EndScene"){if(!dev->in_scene)return done(unsigned(D3DERR_SCENE_NOT_IN_SCENE),1);dev->in_scene=false;render_scene(*dev);return done(DD_OK,1);}
  }
 if(imp.dll=="IDirect3DTexture2"){auto*t=vsurface(root);if(!t)deny("Texture object without its surface",root);
  if(n=="Load"){auto*s=vsurf_of(arg(1));if(!s||s->width!=t->width||s->height!=t->height||s->bpp!=t->bpp)deny("Texture Load between different surfaces is not modelled",arg(1));
   gpu_sync(s->guest);gpu_sync(t->guest);if(t->bytes!=s->bytes)deny("Texture Load with different pitches",arg(1));if(!s->mem&&!t->mem&&!s->pixels.empty()&&!t->pixels.empty())t->pixels=s->pixels;else{std::vector<unsigned char>b(s->bytes);surface_read(*s,0,b.data(),s->bytes);surface_write(*t,0,b.data(),unsigned(b.size()));}t->tex_masks=s->tex_masks;t->version=++host.surface_versions;return done(DD_OK,2);}
  if(n=="GetHandle"){if(!writable(arg(2),4))deny("GetHandle output outside the memory contract",arg(2));store(arg(2),t->guest);return done(DD_OK,3);}}
 stop(m4_runtime::FaultReason::unresolved_import,"Direct3D provider method not implemented: "+imp.dll+"::"+n,token);}
// Texture formats the renderer samples: RGB565, ARGB1555, ARGB4444 (DDPIXELFORMAT words).
static std::vector<std::array<unsigned,8>>texture_formats(){return {{32,DDPF_RGB,0,16,0xf800,0x07e0,0x001f,0},{32,DDPF_RGB|DDPF_ALPHAPIXELS,0,16,0x7c00,0x03e0,0x001f,0x8000},{32,DDPF_RGB|DDPF_ALPHAPIXELS,0,16,0x0f00,0x00f0,0x000f,0xf000}};}
D3DDev*device(unsigned g){for(auto&d:host.devices)if(d.guest==g)return &d;return nullptr;}
D3DViewport*viewport(unsigned g){for(auto&v:host.viewports)if(v.guest==g)return &v;return nullptr;}
D3DDev*device_with_viewport(unsigned vp){for(auto&d:host.devices)if(std::find(d.viewports.begin(),d.viewports.end(),vp)!=d.viewports.end())return &d;return nullptr;}
std::vector<unsigned>snapshot(const D3DDev&d){std::vector<unsigned>v;if(render_reuse_enabled()){v.reserve(531);v.insert(v.end(),d.rs.begin(),d.rs.end());}else v.assign(d.rs.begin(),d.rs.end());for(unsigned s=0;s<8;++s)v.insert(v.end(),d.tss[s].begin(),d.tss[s].end());v.insert(v.end(),8,0U);  /* textures travel per draw (D3DCmd::texture) */if(d.current&&viewport(d.current)){const auto&vp=viewport(d.current)->vp;for(unsigned i=0;i<11;++i){unsigned w;std::memcpy(&w,vp.data()+4*i,4);v.push_back(w);}}return v;}
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
#include "surface_texture_warmup.inc"
#include "surface_resident_texture_warmup.inc"
void render_scene(D3DDev&d){if(override_state().preview_active)override_preview_finish(&d);auto*rt=vsurface(d.target);if(!rt)deny("Scene render target is gone",d.target);if(rt->bpp!=16)deny("Scene render target is not 16-bit",rt->bpp);
 VSurfaceRec*zb=rt->zbuffer?vsurface(rt->zbuffer):nullptr;if(zb&&(zb->bpp!=16||zb->width!=rt->width||zb->height!=rt->height))deny("Z-buffer surface outside the model",rt->zbuffer);
 const bool draws=std::any_of(d.commands.begin(),d.commands.end(),[](const D3DCmd&c){return c.kind==D3DCmd::Draw;});
 auto clip=[&](const RECT&r){RECT c{std::max<LONG>(r.left,0),std::max<LONG>(r.top,0),std::min<LONG>(r.right,LONG(rt->width)),std::min<LONG>(r.bottom,LONG(rt->height))};return c;};
 if(!draws){for(const auto&c:d.commands){const unsigned px=((c.a>>8)&0xf800)|((c.a>>5)&0x07e0)|((c.a>>3)&0x001f);
   for(const auto&r0:c.rects){const RECT r=clip(wide_rect(r0,c.hud_role,rt->width,rt->height));if(r.right<=r.left||r.bottom<=r.top)continue;if(c.flags&D3DCLEAR_TARGET)fill(*rt,r,px);
    if((c.flags&D3DCLEAR_ZBUFFER)&&zb){const unsigned zv=unsigned(std::lround(std::clamp(c.z,0.f,1.f)*65535.f));fill(*zb,r,zv);}}}
  d.commands.clear();return;}
 if(!host.scene_t0)host.scene_t0=host.vclock()?std::max<std::uint64_t>(host.vclock_us/1000,1): ::GetTickCount64();
 if(override_enabled())override_load();
 namespace vs=mw34::vkscene;vs::Scene sc{};sc.shadow_sequence=++host.shadow_sequence;sc.temporal_frame=camera_flip_serial+1;sc.temporal_target=d.target;sc.frontend_canvas=frontend_on();{SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;sc.detail_time=mw34::detail::presentation_time(host.frames);}sc.width=rt->width;sc.height=rt->height;const size_t px=size_t(sc.width)*sc.height;sc.has_depth=zb!=nullptr;
 auto rows_in=[&](const VSurfaceRec&v,std::vector<std::uint16_t>&out){std::vector<unsigned char>row(size_t(v.width)*2);for(unsigned y=0;y<v.height;++y){surface_read(v,y*v.pitch,row.data(),unsigned(row.size()));std::memcpy(out.data()+size_t(y)*v.width,row.data(),row.size());}};
 const bool lazy=lazy_rt();if(lazy&&host.res_dirty&&(host.res_rt!=rt->guest||host.res_zb!=(zb?zb->guest:0U)))gpu_sync(0);
 bool rescale=false;if(lazy){auto*sr=scene_renderer();if(sr==host.presenter.get()){const float want=render_scale(rt->height);
  if(want!=sr->sent.scale||sr->sent.frontend_canvas!=frontend_on()){rescale=true;if(host.res_dirty)gpu_sync(0);}sr->sent.scale_req=want;}}  /* a new scale recreates the target: its content moves through guest memory */
 const bool keep=lazy&&!rescale&&host.sren&&host.res_rt==rt->guest&&host.res_zb==(zb?zb->guest:0U)&&(host.res_dirty||(rt->version==host.res_ver_rt&&(!zb||zb->version==host.res_ver_zb)));
 if(!keep){sc.color.resize(px);sc.depth.assign(px,0);rows_in(*rt,sc.color);if(zb)rows_in(*zb,sc.depth);}  /* a resident scene (keep) uploads nothing and needs no host buffers */
 // One output draw/order record per captured command; avoid copying large
 // lighting/material records repeatedly as the vectors grow.
 sc.draws.reserve(d.commands.size());sc.order.reserve(d.commands.size());
 size_t vertexBytes=0;
 for(const auto& command:d.commands)if(command.kind==D3DCmd::Draw&&!(command.model&&!command.model->world)){
  const size_t n=command.indices.empty()?command.vertices.size()/32:command.indices.size();
  const size_t count=command.flags==D3DPT_POINTLIST?n:command.flags==D3DPT_TRIANGLELIST?(n/3)*3:n>=3?(n-2)*3:0;
  if(count>(sc.vertices.max_size()-vertexBytes)/32)deny("Scene vertex reservation exceeds host bounds",0);
  vertexBytes+=count*32;
 }
 sc.vertices.reserve(vertexBytes);
 std::map<unsigned,int>tex_index;const auto&dflt=rs_defaults();const std::vector<unsigned>*validated=nullptr;
 for(const auto&c:d.commands){
  if(c.kind==D3DCmd::Clear){vs::Clear k{};k.flags=(c.flags&D3DCLEAR_TARGET?1U:0U)|(c.flags&D3DCLEAR_ZBUFFER?2U:0U);k.color[0]=float((c.a>>16)&255)/255.f;k.color[1]=float((c.a>>8)&255)/255.f;k.color[2]=float(c.a&255)/255.f;k.color[3]=float(c.a>>24)/255.f;k.z=std::clamp(c.z,0.f,1.f);
   for(const auto&r0:c.rects){const RECT r=clip(wide_rect(r0,c.hud_role,rt->width,rt->height));if(r.right>r.left&&r.bottom>r.top)k.rects.push_back({{r.left,r.top},{unsigned(r.right-r.left),unsigned(r.bottom-r.top)}});}
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
  vs::Draw dr{};dr.condition_schematic=c.condition_schematic;dr.first=unsigned(sc.vertices.size()/32);dr.texture=-1;dr.normal_texture=-1;
  const unsigned tex=c.texture;  if(c.missile_exhaust){missile_texture(sc,dr);}else if(c.override_texture>=0){const auto&o=override_state();if(!override_enabled()||size_t(c.override_texture)>=o.textures.size())deny("Invalid host replacement texture",unsigned(c.override_texture));const auto&t=o.textures[c.override_texture];
   const std::uint64_t key=0x4257000000000000ULL+unsigned(c.override_texture);auto it=std::find_if(sc.textures.begin(),sc.textures.end(),[&](const vs::TextureRef&r){return r.key==key;});
   if(it==sc.textures.end()){vs::TextureRef r{};r.key=key;r.hash=t.hash;r.width=t.width;r.height=t.height;r.format=vs::TexFormat::rgb565;if(!host.sren||!host.sren->sent_current(key,t.hash,t.width,t.height))r.pixels=t.pixels;sc.textures.push_back(std::move(r));dr.texture=int(sc.textures.size()-1);}else dr.texture=int(it-sc.textures.begin());}
  else if(tex){auto*t=vsurface(tex);if(!t)deny("Draw with a texture that is gone",tex);
   if(rs(D3DRENDERSTATE_COLORKEYENABLE)&&t->has_src_key)deny("Texture colour keying is not modelled",tex);
   auto it=tex_index.find(tex);if(it==tex_index.end()){vs::TextureRef r{};r.key=tex;r.width=t->width;r.height=t->height;
    r.format=t->tex_masks[0]==0xf800?vs::TexFormat::rgb565:t->tex_masks[0]==0x7c00?vs::TexFormat::argb1555:t->tex_masks[0]==0x0f00?vs::TexFormat::argb4444:(deny("Texture pixel format not modelled",t->tex_masks[0]),vs::TexFormat::rgb565);
    if(t->bpp!=16)deny("Texture depth not modelled",t->bpp);r.hash=t->version;if(!host.sren||!host.sren->sent_current(tex,t->version,t->width,t->height)){gpu_sync(t->guest);r.pixels.resize(size_t(t->width)*t->height);rows_in(*t,r.pixels);
     if(const char* mark=std::getenv("MW34_TL_TEXTURE_MARK");mark&&*mark&&t->bytes>=8){char sig[20];std::snprintf(sig,sizeof sig,"%08x%08x",surface_word(*t,0),surface_word(*t,4));
      // Comma-separated signatures; the n-th gets the n-th solid colour.
      static const unsigned short colours[]={0xF81F,0x07E0,0x001F,0xFFE0,0x07FF,0xF800,0xFFFF,0x8010,0x0410,0xFC00,0x841F,0x0000};
      std::string list(mark);size_t at=0;unsigned n=0;
      while(at<=list.size()){size_t end=list.find(',',at);if(end==std::string::npos)end=list.size();
       if(list.compare(at,end-at,sig)==0){for(auto& px:r.pixels)px=colours[n%12];std::fprintf(stderr,"[TL_TEXTURE_MARK] %s colour %u\n",sig,n);break;}
       at=end+1;++n;}}}
    it=tex_index.emplace(tex,int(sc.textures.size())).first;sc.textures.push_back(std::move(r));}dr.texture=it->second;}
  int bind_normal_idx=-1;
  if(c.override_normal_texture>=0&&override_enabled()){
   bind_normal_idx=c.override_normal_texture;
  }else if((c.sun_tl||(c.model&&c.model->world))&&tex&&override_enabled()){
   const auto&o=override_state();
   if(o.ground_normal_texture>=0){
    auto*t=vsurface(tex);
    static std::set<unsigned> seen_tl_tex;
    if(t && seen_tl_tex.insert(tex).second){
     unsigned d0 = t->bytes>=4 ? surface_word(*t,0) : 0;
     unsigned d1 = t->bytes>=8 ? surface_word(*t,4) : 0;
     if(const char* dump_dir=std::getenv("MW34_TL_TEXTURE_DUMP");dump_dir&&*dump_dir&&t->width&&t->height&&t->width<=4096&&t->height<=4096){
      char name[96];std::snprintf(name,sizeof name,"\\%u_%ux%u_%08x%08x.ppm",tex,t->width,t->height,d0,d1);
      std::ofstream ppm(std::string(dump_dir)+name,std::ios::binary);
      if(ppm){ppm<<"P6\n"<<t->width<<" "<<t->height<<"\n255\n";std::vector<unsigned char> row(size_t(t->width)*2),rgb(size_t(t->width)*3);
       for(unsigned y=0;y<t->height;++y){surface_read(*t,y*t->pitch,row.data(),unsigned(row.size()));
        for(unsigned x=0;x<t->width;++x){const unsigned short p=*reinterpret_cast<const unsigned short*>(row.data()+x*2);
         rgb[x*3]=((p>>11)&0x1f)*255/31;rgb[x*3+1]=((p>>5)&0x3f)*255/63;rgb[x*3+2]=(p&0x1f)*255/31;}
        ppm.write(reinterpret_cast<const char*>(rgb.data()),std::streamsize(rgb.size()));}}
     }
     fprintf(stderr, "[UNIQUE_TL_TEX] tex=%u w=%u h=%u pitch=%u mem=0x%x d0=0x%08x d1=0x%08x ground_n=%d\n",
             tex, t->width, t->height, t->pitch, t->mem, d0, d1, o.ground_normal_texture);
     fflush(stderr);
     if(t->width == 1024 && t->height == 1024 && seen_tl_tex.size() == 1){
      std::ofstream ppm("C:\\Users\\jcbla\\MW34SunTests\\big-lake-r1\\dump_ground_1024.ppm", std::ios::binary);
      if(ppm){
       ppm << "P6\n1024 1024\n255\n";
       std::vector<unsigned char> row(1024*2);
       std::vector<unsigned char> rgb(1024*3);
       for(unsigned y=0; y<1024; ++y){
        surface_read(*t,y*t->pitch, row.data(), unsigned(row.size()));
        for(unsigned x=0; x<1024; ++x){
         unsigned short p = *reinterpret_cast<const unsigned short*>(row.data() + x*2);
         rgb[x*3+0] = ((p>>11)&0x1f)*255/31;
         rgb[x*3+1] = ((p>>5)&0x3f)*255/63;
         rgb[x*3+2] = (p&0x1f)*255/31;
        }
        ppm.write(reinterpret_cast<const char*>(rgb.data()), rgb.size());
       }
       fprintf(stderr, "[DUMP_GROUND_1024] written\n"); fflush(stderr);
      }
     }
    }
    const bool is_ground = t && (
     (t->width == 1024 && t->height == 1024 && t->bytes>=8 && surface_word(*t,0) == 0x7a457a65 && surface_word(*t,4) == 0x7a457a45) ||
     (t->width == 2048 && t->height == 2048 && t->bytes>=8 && surface_word(*t,0) == 0x59c459e5 && surface_word(*t,4) == 0x59c459c4) ||
     (t->width == 2048 && t->height == 2048 && t->bytes>=8 && surface_word(*t,0) == 0x20c120c1 && surface_word(*t,4) == 0x20c120c1)
    );
    if(!is_ground&&t&&t->bytes>=8){const unsigned s0=surface_word(*t,0),s1=surface_word(*t,4);
     for(const auto& g:o.ground_normal_bindings)if(g[0]==t->width&&g[1]==t->height&&g[2]==s0&&g[3]==s1){bind_normal_idx=int(g[4]);break;}}
    if(is_ground){
     bind_normal_idx=o.ground_normal_texture;
     static int ground_draw_logs = 0;
     if(ground_draw_logs < 5 && c.vertices.size() >= 32){
      const float* vf = reinterpret_cast<const float*>(c.vertices.data());
      fprintf(stderr, "[GROUND_BOUND] draw vertices=%zu u0=%.4f v0=%.4f normal_idx=%d\n",
              c.vertices.size()/32, vf[6], vf[7], bind_normal_idx);
      fflush(stderr);
      ground_draw_logs++;
     }
    }
   }
  }
  if(tex&&(c.sun_tl||c.sky_view||(c.model&&c.model->world)))if(auto*surface=vsurface(tex)){SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
   dr.detail_role=surface_detail_role(*surface);if(bind_normal_idx<0||dr.detail_role)bind_normal_idx=surface_normal_index(*surface);
  }
  if(bind_normal_idx>=0){const auto&o=override_state();if(size_t(bind_normal_idx)<o.normal_textures.size()){const auto&t=o.normal_textures[bind_normal_idx];
   const std::uint64_t key=0x42574e524d000000ULL+unsigned(bind_normal_idx);auto it=std::find_if(sc.textures.begin(),sc.textures.end(),[&](const vs::TextureRef&r){return r.key==key;});
   if(it==sc.textures.end()){vs::TextureRef r{};r.key=key;r.hash=t.hash;r.width=t.width;r.height=t.height;r.format=vs::TexFormat::rgba8888;if(!host.sren||!host.sren->sent_current(key,t.hash,t.width,t.height)){surface_normals_require_image(bind_normal_idx);r.pixels32=t.pixels32;}sc.textures.push_back(std::move(r));dr.normal_texture=int(sc.textures.size()-1);}else dr.normal_texture=int(it-sc.textures.begin());}}
  dr.sampler=0x10000U|(ts(0,D3DTSS_MAGFILTER)==D3DTFG_LINEAR?1U:0U)|(ts(0,D3DTSS_MINFILTER)==D3DTFN_LINEAR?2U:0U)|(ts(0,D3DTSS_ADDRESSU)<<4)|(ts(0,D3DTSS_ADDRESSV)<<8);
  dr.key={std::uint8_t(rs(D3DRENDERSTATE_ALPHABLENDENABLE)!=0),std::uint8_t(rs(D3DRENDERSTATE_SRCBLEND)),std::uint8_t(rs(D3DRENDERSTATE_DESTBLEND)),std::uint8_t(zb&&rs(D3DRENDERSTATE_ZENABLE)),
          std::uint8_t(rs(D3DRENDERSTATE_ZFUNC)),std::uint8_t(rs(D3DRENDERSTATE_ZWRITEENABLE)!=0),std::uint8_t(rs(D3DRENDERSTATE_CULLMODE))};
  if(dr.key.src<1||dr.key.src>13||dr.key.dst<1||dr.key.dst>13||dr.key.zfunc<1||dr.key.zfunc>8||dr.key.cull<1||dr.key.cull>3)deny("Blend, depth or cull state outside the model",dr.key.src|dr.key.dst<<8);
  auto&pu=dr.push;pu.target[0]=float(sc.width);pu.target[1]=float(sc.height);pu.target[2]=0.5f;const unsigned fc=rs(D3DRENDERSTATE_FOGCOLOR),tf=rs(D3DRENDERSTATE_TEXTUREFACTOR);
  pu.fog[0]=float((fc>>16)&255)/255.f;pu.fog[1]=float((fc>>8)&255)/255.f;pu.fog[2]=float(fc&255)/255.f;pu.fog[3]=1;pu.factor[0]=float((tf>>16)&255)/255.f;pu.factor[1]=float((tf>>8)&255)/255.f;pu.factor[2]=float(tf&255)/255.f;pu.factor[3]=float(tf>>24)/255.f;
  if(tex&&effect_enabled()&&mw34::effects::settings().fixtures){if(auto*surface=vsurface(tex)){if(const auto*fixture=fixture_of(*surface)){pu.fog[3]=1.0f+fixture->intensity;
    if(!fixture->emission_regions.empty()){const auto count=std::min(size_t(32),fixture->emission_regions.size());dr.emission_index=sc.emissions.capture({float(count),fixture->intensity,0,0},std::span<const mw34::submission::DrawEmissions::Float4>(fixture->emission_regions.data(),count));}}}}
  pu.mode[0]=(rs(D3DRENDERSTATE_SHADEMODE)==D3DSHADE_FLAT?1U:0U)|(rs(D3DRENDERSTATE_TEXTUREPERSPECTIVE)?2U:0U)|((tex||c.override_texture>=0||c.missile_exhaust)?4U:0U)|(rs(D3DRENDERSTATE_SPECULARENABLE)?8U:0U)|(rs(D3DRENDERSTATE_FOGENABLE)?16U:0U)|(rs(D3DRENDERSTATE_ALPHATESTENABLE)?32U:0U);
  pu.mode[1]=ts(0,D3DTSS_COLOROP)|ts(0,D3DTSS_COLORARG1)<<8|ts(0,D3DTSS_COLORARG2)<<16;pu.mode[2]=ts(0,D3DTSS_ALPHAOP)|ts(0,D3DTSS_ALPHAARG1)<<8|ts(0,D3DTSS_ALPHAARG2)<<16;
  pu.mode[3]=(rs(D3DRENDERSTATE_ALPHAFUNC)&255)|(rs(D3DRENDERSTATE_ALPHAREF)&255)<<8;
  {const LONG x=LONG(v[521]),y=LONG(v[522]);const RECT r=clip(RECT{x,y,x+LONG(v[523]),y+LONG(v[524])});dr.scissor={{r.left,r.top},{unsigned(std::max<LONG>(r.right-r.left,0)),unsigned(std::max<LONG>(r.bottom-r.top,0))}};}
  /* Only opaque depth-writing draws can become fixture shadow casters (fixture_shadow_stage.inc). */
  if(mw34::effects::settings().fixture_shadows&&!dr.key.blend&&dr.key.zenable&&dr.key.zwrite&&c.model&&c.model->world&&c.fixture_node&&c.fixture_polygon&&tex){
   SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
   if(auto*surface=vsurface(tex))if(auto proof=fixture_caster_proof(c,*surface)){
    dr.shadow_source=(std::uint64_t(c.fixture_node)<<32)|c.fixture_polygon;
    dr.shadow_proof=true;effect_lighting.shadow_proofs[dr.shadow_source]={proof,sc.shadow_sequence};
   }
  }
  dr.sun_tl=c.sun_tl;dr.sky_view=c.sky_view;dr.surface_material=c.surface_material;dr.camera_view=c.camera_view;dr.temporal_output_only=c.hud_role!=WideWorld&&c.hud_role!=WideZoom;dr.temporal_source=c.temporal_source;dr.temporal_model=c.temporal_model;
  if(c.model&&c.model->world)dr.model=c.model;
  if(c.model&&!c.model->world){if(!mw34::vkscene::Renderer::gpu_models()||!c.model->geometry)deny("Optional GPU model draw is not enabled",0);
   dr.model=c.model;dr.first=0;dr.count=unsigned(c.model->geometry->vertices.size());wide_adapt_tl(sc,dr,c.hud_role,c.zoom_anchor_known?&c.zoom_anchor:nullptr);sc.order.push_back({false,unsigned(sc.draws.size())});sc.draws.push_back(std::move(dr));continue;}
  // Primitives become a triangle list in Direct3D order with the first vertex of each triangle first
  // (the flat-shading colour source), preserving each triangle's winding.
  const size_t nv=c.indices.empty()?c.vertices.size()/32:c.indices.size();auto vert=[&](size_t i){const size_t k=c.indices.empty()?i:c.indices[i];if(k*32+32>c.vertices.size())deny("Draw index outside its vertices",unsigned(k));sc.vertices.insert(sc.vertices.end(),c.vertices.begin()+std::ptrdiff_t(k*32),c.vertices.begin()+std::ptrdiff_t(k*32+32));};
  if(c.flags==D3DPT_TRIANGLELIST){for(size_t i=0;i+2<nv;i+=3){vert(i);vert(i+1);vert(i+2);}}
  else if(c.flags==D3DPT_TRIANGLESTRIP){for(size_t i=0;i+2<nv;++i){if(i&1){vert(i);vert(i+2);vert(i+1);}else{vert(i);vert(i+1);vert(i+2);}}}
  else if(c.flags==D3DPT_TRIANGLEFAN){for(size_t i=1;i+1<nv;++i){vert(i);vert(i+1);vert(0);}}
  else if(c.flags==D3DPT_POINTLIST){for(size_t i=0;i<nv;++i)vert(i);dr.key.points=1;}  // one-pixel points (shader point size 1)
  else deny("Primitive type not modelled by the scene renderer",c.flags);
  dr.count=unsigned(sc.vertices.size()/32)-dr.first;wide_adapt_tl(sc,dr,c.hud_role,c.zoom_anchor_known?&c.zoom_anchor:nullptr);sc.order.push_back({false,unsigned(sc.draws.size())});sc.draws.push_back(std::move(dr));}
 distance_scene_log(sc);camera_scene(sc);effect_scene(sc);
 if(mw34::effects::settings().fixture_shadows)sc.valid_shadow_sources=fixture_shadow_sources_valid(fixture_scene_needs_shadow_sources(sc));  /* after effect_scene sets the fixture lights */
 surface_texture_prewarm(sc);surface_resident_texture_prewarm(sc);model_geometry_prewarm(sc);
 submit_scene(sc,!keep,!lazy);
 if(lazy){rt->version=++host.surface_versions;if(zb)zb->version=++host.surface_versions;host.res_rt=rt->guest;host.res_zb=zb?zb->guest:0U;host.res_ver_rt=rt->version;host.res_ver_zb=zb?zb->version:0U;
  host.res_dirty=true;gpu_protect(true);if(host.sren->sent.scenes==1)apis.back()+="(Vulkan scene renderer on "+host.scene_counts.device_name+", lazy residency)";d.commands.clear();return;}
 auto rows_out=[&](VSurfaceRec&v,const std::vector<std::uint16_t>&in){for(unsigned y=0;y<v.height;++y)write_bytes(v.mem+y*v.pitch,in.data()+size_t(y)*v.width,v.width*2);};
 {static const bool poison=[]{const char*e=std::getenv("MW34_RT_POISON");return e&&*e=='1';}();if(poison)std::fill(sc.color.begin(),sc.color.end(),std::uint16_t(0xf81f));}  /* MW34_RT_POISON=1 (diagnostic): the copied-back 3D image is magenta, exposing software HUD reads */
 rows_out(*rt,sc.color);rt->version=++host.surface_versions;if(zb){static const bool zp=[]{const char*e=std::getenv("MW34_ZB_PERTURB");return e&&*e=='1';}();if(zp)for(auto&v:sc.depth)if(v)--v;  /* MW34_ZB_PERTURB=1 (diagnostic): depth written back one unit nearer */
 rows_out(*zb,sc.depth);zb->version=++host.surface_versions;}
 if(host.sren->sent.scenes==1)apis.back()+="(Vulkan scene renderer on "+host.scene_counts.device_name+")";
 d.commands.clear();}


