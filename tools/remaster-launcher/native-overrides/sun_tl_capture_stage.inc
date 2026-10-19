// Visible opaque world geometry still submitted as original TL vertices. The
// sun-only shader reconstructs positions from reciprocal depth and derives a
// geometric face normal. This supplies neither hidden geometry nor casters.
void sun_capture_tl(D3DCmd& draw) {
 if(!mw34::sun::settings().enabled||!world_cell_depth||draw.model||override_suppress_draw()||frontend_on()||
    (draw.hud_role!=WideWorld&&draw.hud_role!=WideZoom)||draw.flags==D3DPT_POINTLIST)return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 if(!draw.state_snapshot||draw.state_snapshot->size()<256)return;
 const auto& rs=*draw.state_snapshot;
 if(rs[D3DRENDERSTATE_ALPHABLENDENABLE]||rs[D3DRENDERSTATE_ALPHATESTENABLE]||
    !rs[D3DRENDERSTATE_ZENABLE]||!rs[D3DRENDERSTATE_ZWRITEENABLE]||!draw.texture)return;
 OverrideMatrix camera_world;if(!sun_camera_world(camera_world))return;
 struct Vertex {float x,y,z,rhw;unsigned rgb,spec;float u,v;};
 for(size_t at=0;at<draw.vertices.size();at+=32){Vertex v;std::memcpy(&v,draw.vertices.data()+at,32);
  if(!std::isfinite(v.x)||!std::isfinite(v.y)||!std::isfinite(v.z)||!std::isfinite(v.rhw)||v.z<=0||v.rhw<=0)return;}
 auto light=std::make_shared<mw34::sun::Tl>();
 for(unsigned i=0;i<12;++i)light->camera_world[i]=float(camera_world[i]);
 light->projection={wide_float(0x73fb80),wide_float(0x73fc30),wide_float(0x73fb98),wide_float(0x73fb88),wide_float(0x73fb8c),wide_float(0x740304)};
 for(float v:light->projection)if(!std::isfinite(v))throw std::runtime_error("Sun TL projection nonfinite");
 if(light->projection[0]<=0||light->projection[1]==0||light->projection[2]==0)throw std::runtime_error("Sun TL projection invalid");
 draw.sun_tl=std::move(light);
}
