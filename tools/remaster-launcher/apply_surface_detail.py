"""Compose optional sky/water relief into a private material-normal host copy."""
from pathlib import Path
import argparse

SOURCE=Path(__file__).parent/'native-overrides'

def apply(host):
    files={name:(host/name).read_text() for name in
           ['vk_scene.hpp','surface_normals_stage.inc','d3d_provider.inc','sun_tl_capture_stage.inc']}
    def replace(name,old,new):
        if files[name].count(old)!=1:raise ValueError('Unexpected surface detail anchor: '+name+' '+old[:80])
        files[name]=files[name].replace(old,new)
    replace('vk_scene.hpp','#include "sun_lighting.hpp"','#include "sun_lighting.hpp"\n#include "surface_detail.hpp"')
    replace('vk_scene.hpp','struct Draw { unsigned first, count;','struct Draw { unsigned detail_role{}; unsigned first, count;')
    # Keep positional aggregate initializers compatible: the new field must be last.
    files['vk_scene.hpp']=files['vk_scene.hpp'].replace('struct Draw { unsigned detail_role{}; unsigned first, count;', 'struct Draw { unsigned first, count;')
    replace('vk_scene.hpp','std::shared_ptr<const mw34::sun::Tl> sky_view{}; };','std::shared_ptr<const mw34::sun::Tl> sky_view{};unsigned detail_role{}; };')
    replace('vk_scene.hpp','struct Scene {','struct Scene {\n    double detail_time{};')
    anchor='                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)+at*sunStride,&u,sizeof(u));sunScene=true;'
    replace('vk_scene.hpp',anchor,
        '                if(mw34::materials::normal_maps_enabled()&&draw.normal_texture>=0&&((draw.detail_role==3&&draw.sky==1)||(draw.detail_role>0&&draw.detail_role<3&&!draw.sky&&(draw.sun_tl||(draw.model&&draw.model->world)))))mw34::detail::uniform(u,draw.detail_role,s.detail_time);\n'+anchor)
    replace('vk_scene.hpp','const bool normal_active=mw34::materials::normal_maps_enabled()&&normal_strength>0;',
            'const bool normal_active=mw34::materials::normal_maps_enabled()&&(normal_strength>0||mw34::detail::enabled(d.detail_role));')
    replace('vk_scene.hpp','                auto it = normalSets.find({t, d.sampler});',
            '                const unsigned normal_sampler=d.detail_role>0&&d.detail_role<3?0x10113U:d.sampler;\n                auto it = normalSets.find({t, normal_sampler});')
    replace('vk_scene.hpp','VkDescriptorImageInfo info{sampler(d.sampler), t->view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};\n                    VkWriteDescriptorSet',
            'VkDescriptorImageInfo info{sampler(normal_sampler), t->view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};\n                    VkWriteDescriptorSet')
    replace('vk_scene.hpp','it = normalSets.emplace(std::make_pair(t, d.sampler), set).first;',
            'it = normalSets.emplace(std::make_pair(t, normal_sampler), set).first;')
    replace('surface_normals_stage.inc',' std::set<mw34::materials::SurfaceKey> authored;',
            ' std::set<mw34::materials::SurfaceKey> authored;\n std::map<mw34::materials::SurfaceKey,unsigned> detail_roles;')
    replace('surface_normals_stage.inc','bool registered{},world{};','bool registered{},world{};unsigned detail{};')
    files['surface_normals_stage.inc']+='\n#include "surface_detail_stage.inc"\n'
    replace('surface_normals_stage.inc','return mw34::sun::settings().enabled&&((p&&*p)||(w&&*w));',
            'return mw34::sun::settings().enabled&&((p&&*p)||(w&&*w)||mw34::detail::settings().water||mw34::detail::settings().clouds);')
    replace('surface_normals_stage.inc',' surface_normals_load_world();',' surface_detail_load();\n surface_normals_load_world();')
    replace('surface_normals_stage.inc','format,index,registered,world};','format,index,registered,world,surface_normals.detail_roles.count(key)?surface_normals.detail_roles.at(key):0};')
    # A cloud registration must never admit the sky to the ordinary opaque
    # world-lighting path before sun_capture_sky gets to authenticate its view.
    replace('sun_tl_capture_stage.inc',
            '    !rs[D3DRENDERSTATE_ZENABLE]||!rs[D3DRENDERSTATE_ZWRITEENABLE]||!draw.texture)return;',
            '    !rs[D3DRENDERSTATE_ZENABLE]||!rs[D3DRENDERSTATE_ZWRITEENABLE]||!draw.texture)return;\n'
            ' if(mw34::detail::settings().clouds)if(auto*surface=vsurface(draw.texture))if(surface_detail_role(*surface)==3)return;')
    replace('d3d_provider.inc','sc.width=rt->width;', '{SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;if(mw34::detail::settings().water||mw34::detail::settings().clouds)sc.detail_time=mw34::detail::presentation_time(host.frames);}sc.width=rt->width;')
    replace('d3d_provider.inc','  if(bind_normal_idx<0&&(c.sun_tl||(c.model&&c.model->world))&&tex)if(auto*surface=vsurface(tex))bind_normal_idx=surface_normal_index(*surface);',
            '  if(tex&&(c.sun_tl||c.sky_view||(c.model&&c.model->world)))if(auto*surface=vsurface(tex)){SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;\n'
            '   dr.detail_role=surface_detail_role(*surface);if(bind_normal_idx<0||dr.detail_role)bind_normal_idx=surface_normal_index(*surface);\n  }')
    from lighting_header_dependencies import copy_lighting_dependencies
    copy_lighting_dependencies(host)
    for name,text in files.items():(host/name).write_text(text)
    for name in ['sun_lighting.hpp','surface_detail.hpp','surface_detail_stage.inc',
                 'sun_scene_frag.h','sun_world_vert.h','sun_model_vert.h','sun_tl_vert.h','sun_shadow_vert.h']:
        (host/name).write_bytes((SOURCE/name).read_bytes())

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
