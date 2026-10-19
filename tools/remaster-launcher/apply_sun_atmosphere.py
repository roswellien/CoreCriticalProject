"""Add sky-dome tint and distance-haze colour to a sun/shadow test host.

Apply after apply_sun_shadows.py. Settings come from sun_lighting.hpp
(MW34_SKY_TINT, MW34_HAZE_COLOR, MW34_SKY_AUTO). With neutral sun/ambient
colours and no manual values the scene is not modified at all.

The MW3 sky is an opaque, textured original TL dome drawn at the far depth
limit (all vertices z <= 0.00025) with vertex fog; the horizon band is that
fog. The haze replaces the fog colour of every non-HUD draw; the sky tint
scales the dome's diffuse colour (or adds a texture-factor modulate when the
dome selects its texture alone). Unsupported colour operations stay untinted
and are counted.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one atmosphere anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    vk=host/'vk_scene.hpp'
    if 'prepare_shadow' not in vk.read_text():raise RuntimeError('Apply apply_sun_shadows.py first')
    if 'apply_atmosphere' in vk.read_text():raise RuntimeError('Use a fresh host copy; atmosphere already installed')
    edit(vk,'std::shared_ptr<const mw34::sun::Tl> sun_tl{}; };','std::shared_ptr<const mw34::sun::Tl> sun_tl{};unsigned char sky{};std::shared_ptr<const mw34::sun::Tl> sky_view{}; };')
    # Each sky/haze candidate captures its own camera with the draw, so the widescreen stage adapts it with that draw's vertices.
    edit(host/'mfc_stage.hpp','std::shared_ptr<const mw34::sun::Tl>sun_tl{};unsigned hud_role{};','std::shared_ptr<const mw34::sun::Tl>sun_tl{};std::shared_ptr<const mw34::sun::Tl>sky_view{};unsigned hud_role{};')
    edit(host/'d3d_provider.inc','world_capture(c);sun_capture_tl(c);','world_capture(c);sun_capture_tl(c);sun_capture_sky(c);')
    edit(host/'d3d_provider.inc','  dr.sun_tl=c.sun_tl;','  dr.sun_tl=c.sun_tl;dr.sky_view=c.sky_view;')
    anchor='  if(d.sun_tl){auto light=std::make_shared<mw34::sun::Tl>(*d.sun_tl);light->projection[1]/=k;light->projection[3]=a+(light->projection[3]+.5f-a)/k-.5f;d.sun_tl=std::move(light);}'
    edit(host/'widescreen_stage.inc',anchor,anchor+'\n  if(d.sky_view){auto view=std::make_shared<mw34::sun::Tl>(*d.sky_view);view->projection[1]/=k;view->projection[3]=a+(view->projection[3]+.5f-a)/k-.5f;d.sky_view=std::move(view);}')
    stage=host/'sun_tl_capture_stage.inc'
    stage.write_text(stage.read_text()+'''
// Sky dome, horizon band and unlit fogged world draws: camera reference only
// (no lighting). Used by the sky shading for an exact per-pixel view ray.
void sun_capture_sky(D3DCmd& draw) {
 const auto& sun=mw34::sun::settings();
 if(!sun.enabled||!sun.sky_shading||draw.model||draw.sun_tl||override_suppress_draw()||frontend_on()||
    (draw.hud_role!=WideWorld&&draw.hud_role!=WideZoom)||!draw.state_snapshot||draw.state_snapshot->size()<256||!(*draw.state_snapshot)[D3DRENDERSTATE_FOGENABLE])return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 OverrideMatrix camera_world;if(!sun_camera_world(camera_world))return;
 auto view=std::make_shared<mw34::sun::Tl>();
 for(unsigned i=0;i<12;++i)view->camera_world[i]=float(camera_world[i]);
 view->projection={wide_float(0x73fb80),wide_float(0x73fc30),wide_float(0x73fb98),wide_float(0x73fb88),wide_float(0x73fb8c),wide_float(0x740304)};
 for(float v:view->projection)if(!std::isfinite(v))return;
 if(view->projection[0]<=0||view->projection[1]==0||view->projection[2]==0)return;
 draw.sky_view=std::move(view);
}
''')
    edit(vk,'return mw34::sun::settings().enabled&&((d.sun_tl&&(d.push.mode[0]&4))','return mw34::sun::settings().enabled&&(d.sky||(d.sun_tl&&(d.push.mode[0]&4))')
    edit(vk,'                if(shadowFrame.active){const auto& sun=mw34::sun::settings();for(unsigned i=0;i<12;++i)u.shadow[i]',
         '''                if(skyEyeValid){const auto& e=draw.sun_tl&&!draw.sky?draw.sun_tl->camera_world:skyEye;u.sky_eye={e[3],e[7],e[11],1};}
                if(draw.sky)u.extra[3]=1.f+float(draw.sky);
                if(const char* dbg=std::getenv("MW34_SKY_DEBUG"))u.sky_blend[3]=*dbg=='3'?3.f+float(draw.sky?3:draw.model?(draw.model->world?1:2):0):*dbg=='2'?2.f:1.f+float(at%13)/13.f;
                if(shadowFrame.active){const auto& sun=mw34::sun::settings();for(unsigned i=0;i<12;++i)u.shadow[i]''')
    edit(vk,'sun_shadow_scenes{},sun_shadow_casters{},sun_shadow_reused{};',
         'sun_shadow_scenes{},sun_shadow_casters{},sun_shadow_reused{},sky_draws{},sky_tinted{},sky_untinted{},haze_draws{},horizon_draws{},haze_routed{},sky_own_view{};')
    edit(vk,'    void record_shadow(const ShadowFrame& frame) {','''    std::array<float,12> skyEye{};bool skyEyeValid{};
    void apply_atmosphere(Scene& s) {
        const auto& sun=mw34::sun::settings();skyEyeValid=false;
        if(!sun.enabled||s.hud||(!sun.sky_active&&!sun.haze_active&&!sun.sky_shading))return;
        // Sky shading: each far draw takes the camera of the nearest TL receiver
        // in submission order (the same view), else the next one after it.
        std::vector<std::shared_ptr<const mw34::sun::Tl>> view(s.draws.size());
        if(sun.sky_shading){
            std::shared_ptr<const mw34::sun::Tl> current;
            for(const auto& o:s.order)if(!o.clear){const auto& d=s.draws[o.index];if(d.sun_tl)current=d.sun_tl;view[o.index]=current;}
            current.reset();
            for(auto o=s.order.rbegin();o!=s.order.rend();++o)if(!o->clear){const auto& d=s.draws[o->index];if(d.sun_tl)current=d.sun_tl;if(!view[o->index])view[o->index]=current;}
            for(const auto& d:s.draws)if(d.sun_tl){skyEye=d.sun_tl->camera_world;skyEyeValid=true;break;}
        }
        for(size_t at=0;at<s.draws.size();++at){auto& d=s.draws[at];
            // Unlit fogged world draws (not sky) keep their colours but take the directional haze.
            if(d.sky_view)view[at]=d.sky_view;
            const bool routable=sun.sky_shading&&view[at]&&!d.model&&!d.sun_tl&&d.count&&(d.push.mode[0]&16);
            if(sun.haze_active&&(d.push.mode[0]&16)){
                for(unsigned i=0;i<3;++i)d.push.fog[i]=sun.haze_manual?sun.haze_color[i]:std::fmin(1.f,d.push.fog[i]*sun.haze_scale[i]);
                ++haze_draws;
            }
            if(routable&&d.key.blend){d.sky=3;d.sun_tl=view[at];++haze_routed;continue;}
            if(d.model||d.sun_tl||d.key.blend||!d.count||(d.texture>=0&&!sun.sky_active&&!sun.sky_shading)||(d.texture<0&&!sun.haze_active&&!sun.sky_shading))continue;
            bool distant=true;
            for(unsigned v=d.first;v<d.first+d.count&&distant;++v){float z;std::memcpy(&z,s.vertices.data()+size_t(v)*32+8,4);distant=std::isfinite(z)&&z>=0&&z<=.00025f;}
            if(!distant){if(routable){d.sky=3;d.sun_tl=view[at];++haze_routed;}continue;}
            if(sun.sky_shading&&view[at]){d.sky=d.texture<0?2:1;d.sun_tl=view[at];if(d.sky_view)++sky_own_view;if(d.texture<0)++horizon_draws;else{++sky_draws;++sky_tinted;}continue;}
            if(d.texture<0){
                // Untextured far backdrop below the dome: the horizon band takes the haze colour.
                for(unsigned v=d.first;v<d.first+d.count;++v){
                    std::uint32_t c;unsigned char* at=s.vertices.data()+size_t(v)*32+16;std::memcpy(&c,at,4);
                    std::uint32_t out=c&0xff000000u;
                    for(unsigned i=0;i<3;++i){const unsigned shift=16-8*i;const float x=sun.haze_manual?sun.haze_color[i]*255.f:float((c>>shift)&255)*sun.haze_scale[i];
                        out|=std::uint32_t(std::lround(std::fmin(255.f,std::fmax(0.f,x))))<<shift;}
                    std::memcpy(at,&out,4);
                }
                ++horizon_draws;continue;
            }
            ++sky_draws;
            const std::uint32_t w=d.push.mode[1],op=w&255,a1=(w>>8)&255,a2=(w>>16)&255;
            auto diffuse=[](std::uint32_t a){return (a&15)<=1&&!(a&48);};
            if(op==1||(op==2&&diffuse(a1))||(op==3&&diffuse(a2))||((op>=4&&op<=6)&&(diffuse(a1)||diffuse(a2)))){
                for(unsigned v=d.first;v<d.first+d.count;++v){
                    std::uint32_t c;unsigned char* at=s.vertices.data()+size_t(v)*32+16;std::memcpy(&c,at,4);
                    std::uint32_t out=c&0xff000000u;
                    for(unsigned i=0;i<3;++i){const unsigned shift=16-8*i;const float x=float((c>>shift)&255)*sun.sky_tint[i];
                        out|=std::uint32_t(std::lround(std::fmin(255.f,x)))<<shift;}
                    std::memcpy(at,&out,4);
                }
                ++sky_tinted;
            }else if(op==2&&(a1&63)==2){
                d.push.mode[1]=4u|(2u<<8)|(3u<<16);  // MODULATE(TEXTURE, TFACTOR)
                for(unsigned i=0;i<3;++i)d.push.factor[i]=sun.sky_tint[i];
                ++sky_tinted;
            }else ++sky_untinted;
        }
    }
    void record_shadow(const ShadowFrame& frame) {''')
    edit(vk,'        if (!s.vertices.empty()) std::memcpy(vertexBuffer.mapped, s.vertices.data(), s.vertices.size());',
         '        apply_atmosphere(s);\n        if (!s.vertices.empty()) std::memcpy(vertexBuffer.mapped, s.vertices.data(), s.vertices.size());')
    edit(vk,'        if(mw34::sun::settings().enabled)init_shadow();','''        if(mw34::sun::settings().enabled){init_shadow();const auto& sun=mw34::sun::settings();
            std::fprintf(stderr,"Sun colour %.3f %.3f %.3f, ambient tint %.3f %.3f %.3f; sky tint %.3f %.3f %.3f (%s), haze %s %.3f %.3f %.3f\\n",
                sun.color[0],sun.color[1],sun.color[2],sun.ambient_color[0],sun.ambient_color[1],sun.ambient_color[2],sun.sky_tint[0],sun.sky_tint[1],sun.sky_tint[2],
                sun.sky_manual?"manual":(sun.sky_active?"auto":"off"),sun.haze_manual?"colour":(sun.haze_active?"auto scale":"off"),
                sun.haze_manual?sun.haze_color[0]:sun.haze_scale[0],sun.haze_manual?sun.haze_color[1]:sun.haze_scale[1],sun.haze_manual?sun.haze_color[2]:sun.haze_scale[2]);}''')
    edit(host/'world_geometry_stage.inc','<<",\\\"sun_shadow_reused\\\":"<<(host.sren?host.sren->sun_shadow_reused:0)',
         '<<",\\\"sun_shadow_reused\\\":"<<(host.sren?host.sren->sun_shadow_reused:0)<<",\\\"sky_draws\\\":"<<(host.sren?host.sren->sky_draws:0)<<",\\\"sky_tinted\\\":"<<(host.sren?host.sren->sky_tinted:0)<<",\\\"sky_untinted\\\":"<<(host.sren?host.sren->sky_untinted:0)<<",\\\"haze_draws\\\":"<<(host.sren?host.sren->haze_draws:0)<<",\\\"horizon_draws\\\":"<<(host.sren?host.sren->horizon_draws:0)<<",\\\"haze_routed\\\":"<<(host.sren?host.sren->haze_routed:0)<<",\\\"sky_own_view\\\":"<<(host.sren?host.sren->sky_own_view:0)')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
