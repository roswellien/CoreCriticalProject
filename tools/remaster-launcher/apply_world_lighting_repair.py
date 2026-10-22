"""Repair an R6 native host copy; validate all adapter anchors before writes."""
from pathlib import Path
import argparse
from apply_status_damage_colour import apply as apply_status_damage_colour
from apply_depth32 import apply as apply_depth32
from apply_detached_cockpit_visibility import apply as apply_detached_cockpit_visibility

ROOT=Path(__file__).resolve().parents[2]
SHARED=Path(__file__).parent/'native-overrides'

def apply(host):
    pending={}
    def edit(name,old,new):
        p=host/name;s=pending.get(p,p.read_text(encoding='utf-8'))
        # Several replacements retain their original anchor as a prefix.
        # Recognize an installed replacement before looking for that prefix.
        if s.count(new)==1:return
        if s.count(old)!=1:
            raise ValueError(f'{name}: expected one repair anchor: {old[:70]}')
        pending[p]=s.replace(old,new,1)
    edit('vk_scene.hpp','        apply_atmosphere(s);','        const auto environment=(s.hud||s.frontend_canvas)?mw34::sun::settings():mw34::sun::current_settings(s.detail_time);\n        apply_atmosphere(s,environment);')
    edit('vk_scene.hpp','const ShadowFrame shadowFrame=prepare_shadow(s);','const ShadowFrame shadowFrame=prepare_shadow(s,environment);')
    edit('vk_scene.hpp','ShadowFrame prepare_shadow(const Scene& s) {\n        ShadowFrame frame;const auto sun=mw34::sun::current_settings(s.detail_time);','ShadowFrame prepare_shadow(const Scene& s,const mw34::sun::Settings& sun) {\n        ShadowFrame frame;')
    edit('vk_scene.hpp','void apply_atmosphere(Scene& s) {\n        const auto sun=mw34::sun::current_settings(s.detail_time);skyEyeValid=false;','void apply_atmosphere(Scene& s,const mw34::sun::Settings& sun) {\n        skyEyeValid=false;')
    edit('vk_scene.hpp','u=mw34::sun::uniform(instance.sun_normal,mw34::sun::settings());u.world=instance.sun_world;if(instance.world)u.extra[1]=mw34::sun::settings().ground_normal_strength;','u=mw34::sun::uniform(instance.sun_normal,environment);u.world=instance.sun_world;if(instance.world)u.extra[1]=environment.ground_normal_strength;')
    edit('vk_scene.hpp','const auto& light=*draw.sun_tl;u=mw34::sun::uniform(light.camera_world,mw34::sun::settings());','const auto& light=*draw.sun_tl;u=mw34::sun::uniform(light.camera_world,environment);')
    edit('vk_scene.hpp','u.extra={light.projection[0],mw34::sun::settings().ground_normal_strength,mw34::sun::settings().shadow_debug?1.f:0.f,1};','u.extra={light.projection[0],environment.ground_normal_strength,environment.shadow_debug?1.f:0.f,1};')
    edit('vk_scene.hpp','if(shadowFrame.active){const auto& sun=mw34::sun::settings();','if(shadowFrame.active){const auto& sun=environment;')
    edit('vk_scene.hpp','u.detail_motion[3]=draw.key.blend?-1.f:mw34::effects::settings().night_gain;','u.detail_motion[3]=draw.key.blend?-1.f:environment.night_world_gain;')
    edit('vk_scene.hpp','const auto normal_settings=mw34::sun::current_settings(s.detail_time);','const auto& normal_settings=environment;')
    edit('vk_scene.hpp','std::uint64_t model_uploads{},model_uploaded_bytes{},model_draws{},world_gpu_draws{};','std::uint64_t model_uploads{},model_uploaded_bytes{},model_draws{},world_gpu_draws{},effect_light_peak{},fixture_light_peak{};')
    edit('vk_scene.hpp','std::memcpy(effectBuffer.mapped,&fx,sizeof(fx));','std::memcpy(effectBuffer.mapped,&fx,sizeof(fx));effect_light_peak=std::max(effect_light_peak,std::uint64_t(fx.params[0]));fixture_light_peak=std::max(fixture_light_peak,std::uint64_t(fx.params[2]));')
    # Use the presentation clock for campaign flashes even with water/cloud detail disabled.
    edit('d3d_provider.inc','if(mw34::detail::settings().water||mw34::detail::settings().clouds)sc.detail_time=','sc.detail_time=')
    edit('d3d_provider.inc','if(tex){if(auto*surface=vsurface(tex)){if(const auto*fixture=fixture_of(*surface)){pu.fog[3]=1.0f+fixture->intensity;}}}','if(tex&&effect_enabled()&&mw34::effects::settings().fixtures){if(auto*surface=vsurface(tex)){if(const auto*fixture=fixture_of(*surface)){pu.fog[3]=1.0f+fixture->intensity;}}}')
    edit('mfc_stage.hpp','if(n=="CreateFileA"){const std::string q=resolve(arg(0));mw34::campaign::CampaignManager::instance().observe_file(q);','if(n=="CreateFileA"){const std::string q=resolve(arg(0));')
    edit('mfc_stage.hpp','if(h==INVALID_HANDLE_VALUE)return done(0xffffffffU,7);const unsigned g2=ghandle(h);','if(h==INVALID_HANDLE_VALUE)return done(0xffffffffU,7);if(!writes&&(acc&GENERIC_READ)&&disp==OPEN_EXISTING)mw34::campaign::CampaignManager::instance().observe_file(q,true);const unsigned g2=ghandle(h);')
    edit('mfc_stage.hpp','unsigned texture{};int override_texture','unsigned texture{};unsigned fixture_node{},fixture_polygon{};int override_texture')
    edit('world_direct_stage.inc','sun_capture_world(*instance,scope.node);draw.model=','sun_capture_world(*instance,scope.node);draw.fixture_node=scope.node;draw.fixture_polygon=polygon.source;draw.model=')
    edit('world_geometry_stage.inc','<<",\\\"sun_models\\\":"<<(host.sren?host.sren->sun_model_draws:0)', '<<",\\\"sun_models\\\":"<<(host.sren?host.sren->sun_model_draws:0)<<",\\\"effect_light_peak\\\":"<<(host.sren?host.sren->effect_light_peak:0)<<",\\\"fixture_light_peak\\\":"<<(host.sren?host.sren->fixture_light_peak:0)')
    for name in ['sun_lighting.hpp','campaign_lighting.hpp','fixture_lighting.hpp','effect_lighting_settings.hpp','effect_scene_frag.h','sun_scene_frag.h']:
        pending[host/name]=(SHARED/name).read_text(encoding='utf-8')
    pending[host/'effect_lighting_stage.inc']=(SHARED/'world_effect_lighting_stage.inc').read_text(encoding='utf-8')
    pending[host/'effect_lighting.hpp']=(ROOT/'runtime/graphics/effect_lighting.hpp').read_text(encoding='utf-8')
    for p,text in pending.items():p.write_text(text,encoding='utf-8',newline='\n')
    apply_status_damage_colour(host)
    apply_depth32(host)
    adapter=host/'mesh_override_stage.inc'
    if 'detached_attached_cockpit_suppressed' not in adapter.read_text():
        apply_detached_cockpit_visibility(adapter)
    print('Applied native world-light repair to',host)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host-source',required=True,type=Path);apply(p.parse_args().host_source)
