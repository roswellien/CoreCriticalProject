// Visible opaque world geometry still submitted as original TL vertices. The
// sun-only shader reconstructs positions from reciprocal depth and derives a
// geometric face normal. This supplies neither hidden geometry nor casters.
void sun_capture_tl(D3DCmd& draw) {
 if(!mw34::sun::settings().enabled||draw.model||override_suppress_draw()||frontend_on()||
    (draw.hud_role!=WideWorld&&draw.hud_role!=WideZoom)||draw.flags==D3DPT_POINTLIST)return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 if(!draw.state_snapshot||draw.state_snapshot->size()<256)return;
 const auto& rs=*draw.state_snapshot;
 if(rs[D3DRENDERSTATE_ALPHABLENDENABLE]||
    !rs[D3DRENDERSTATE_ZENABLE]||!rs[D3DRENDERSTATE_ZWRITEENABLE])return;
 // Sky identity is independent of the optional cloud animation setting.
 if(auto*surface=vsurface(draw.texture))if(surface_detail_role(*surface)==3)return;
 // The original lower horizon can write depth and have positive far depth.
 // Match its untextured identity before applying solid-surface lighting.
 if(!draw.texture && draw.override_texture<0 &&
    mw34::sky::backdrop(draw.vertices.data(),draw.vertices.size(),0,false,true))return;
 // Alpha-tested world objects retain their original cutout test in colour and shadow passes.
 // Authenticated world-role opaque objects receive light even without authored normal maps.
 OverrideMatrix camera_world;if(!sun_camera_world(camera_world))return;
 struct Vertex {float x,y,z,rhw;unsigned rgb,spec;float u,v;};
 for(size_t at=0;at<draw.vertices.size();at+=32){Vertex v;std::memcpy(&v,draw.vertices.data()+at,32);
  if(!std::isfinite(v.x)||!std::isfinite(v.y)||!std::isfinite(v.z)||!std::isfinite(v.rhw)||v.z<=0||v.rhw<=0)return;}
 const bool reuse=render_reuse_enabled();mw34::sun::Tl pending{};std::shared_ptr<mw34::sun::Tl> owned;
 auto* light=reuse?&pending:(owned=std::make_shared<mw34::sun::Tl>()).get();
 for(unsigned i=0;i<12;++i)light->camera_world[i]=float(camera_world[i]);
 light->projection={wide_float(0x73fb80),wide_float(0x73fc30),wide_float(0x73fb98),wide_float(0x73fb88),wide_float(0x73fb8c),wide_float(0x740304)};
 for(float v:light->projection)if(!std::isfinite(v))throw std::runtime_error("Sun TL projection nonfinite");
 if(light->projection[0]<=0||light->projection[1]==0||light->projection[2]==0)throw std::runtime_error("Sun TL projection invalid");
 if(reuse)draw.sun_tl=sun_tl_values.capture(pending);else draw.sun_tl=std::move(owned);
}

// Sky dome, horizon band and unlit fogged world draws: camera reference only
// (no lighting). Used by the sky shading for an exact per-pixel view ray.
void sun_capture_sky(D3DCmd& draw) {
 const auto& sun=mw34::sun::settings();
 if(!sun.enabled||!sun.sky_shading||draw.model||draw.sun_tl||override_suppress_draw()||frontend_on()||
    (draw.hud_role!=WideWorld&&draw.hud_role!=WideZoom)||!draw.state_snapshot||draw.state_snapshot->size()<256||!(*draw.state_snapshot)[D3DRENDERSTATE_FOGENABLE])return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 OverrideMatrix camera_world;if(!sun_camera_world(camera_world))return;
 const bool reuse=render_reuse_enabled();mw34::sun::Tl pending{};std::shared_ptr<mw34::sun::Tl> owned;
 auto* view=reuse?&pending:(owned=std::make_shared<mw34::sun::Tl>()).get();
 for(unsigned i=0;i<12;++i)view->camera_world[i]=float(camera_world[i]);
 view->projection={wide_float(0x73fb80),wide_float(0x73fc30),wide_float(0x73fb98),wide_float(0x73fb88),wide_float(0x73fb8c),wide_float(0x740304)};
 for(float v:view->projection)if(!std::isfinite(v))return;
 if(view->projection[0]<=0||view->projection[1]==0||view->projection[2]==0)return;
 if(reuse)draw.sky_view=sky_view_values.capture(pending);else draw.sky_view=std::move(owned);
}
