"""Install presentation-only local lights into a current sun/normal-map host.

All anchor checks precede writes. Use a private host copy; guest objects and
existing playable launch profiles are not changed by this adapter.
"""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).parent/'native-overrides'

def apply(host):
    pending={}
    def edit(name,old,new):
        path=host/name
        text=pending.get(path,path.read_text())
        if text.count(old)!=1:raise ValueError(f'{name}: expected one anchor {old[:65]!r}')
        pending[path]=text.replace(old,new)
    edit('vk_scene.hpp','#include "sun_lighting.hpp"','#include "sun_lighting.hpp"\n#include "effect_lighting_settings.hpp"')
    edit('vk_scene.hpp','#include "sun_scene_frag.h"','#include "effect_scene_frag.h"')
    edit('vk_scene.hpp','module(sun_scene_frag_spv,sizeof(sun_scene_frag_spv))','module(effect_scene_frag_spv,sizeof(effect_scene_frag_spv))')
    edit('vk_scene.hpp','    double detail_time{};','    double detail_time{};\n    mw34::effects::Uniform effect_lights{};')
    edit('vk_scene.hpp','Buffer upload, readback, vertexBuffer, texUpload, sunBuffer;','Buffer upload, readback, vertexBuffer, texUpload, sunBuffer, effectBuffer;')
    edit('vk_scene.hpp','            for(size_t at=0;at<s.draws.size();++at)if(!s.hud&&sun_lit(s.draws[at])){',
         '            ensure(effectBuffer,sizeof(mw34::effects::Uniform),VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT);\n'
         '            const mw34::effects::Uniform noEffects{};\n'
         '            const auto& fx=s.hud||s.frontend_canvas?noEffects:s.effect_lights;\n'
         '            std::memcpy(effectBuffer.mapped,&fx,sizeof(fx));\n'
         '            for(size_t at=0;at<s.draws.size();++at)if(!s.hud&&sun_lit(s.draws[at])){')
    edit('vk_scene.hpp','                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)',
         '                u.detail_motion[3]=draw.key.blend?-1.f:mw34::effects::settings().night_gain;\n'
         '                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)')
    edit('vk_scene.hpp','std::array<VkWriteDescriptorSet,2> w{};','VkDescriptorBufferInfo effectInfo{effectBuffer.buffer,0,sizeof(mw34::effects::Uniform)};\n            std::array<VkWriteDescriptorSet,3> w{};')
    edit('vk_scene.hpp','            f.vkUpdateDescriptorSets(device,2,w.data(),0,nullptr);',
         '            w[2].dstBinding=2;w[2].descriptorType=VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;w[2].pBufferInfo=&effectInfo;\n            f.vkUpdateDescriptorSets(device,3,w.data(),0,nullptr);')
    edit('vk_scene.hpp','maxUniformBufferRange<sizeof(mw34::sun::Uniform)','maxUniformBufferRange<std::max(sizeof(mw34::sun::Uniform),sizeof(mw34::effects::Uniform))')
    edit('vk_scene.hpp','const std::array<VkDescriptorSetLayoutBinding,2> sb','const std::array<VkDescriptorSetLayoutBinding,3> sb')
    edit('vk_scene.hpp','{1,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr}}};',
         '{1,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr},\n                    {2,VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr}}};')
    edit('vk_scene.hpp','si.bindingCount=2;si.pBindings=sb.data();','si.bindingCount=3;si.pBindings=sb.data();')
    edit('vk_scene.hpp','const std::array<VkDescriptorPoolSize,2> ps{{{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,n*2+1},{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC,1}}};',
         'const std::array<VkDescriptorPoolSize,3> ps{{{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,n*2+1},{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC,1},{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,1}}};')
    edit('vk_scene.hpp','pi.poolSizeCount = mw34::sun::settings().enabled?2:1;','pi.poolSizeCount = mw34::sun::settings().enabled?3:1;')
    edit('vk_scene.hpp','&presentUpload, &sunBuffer})','&presentUpload, &sunBuffer, &effectBuffer})')
    edit('vk_scene.hpp','const bool routable=sun.sky_shading&&view[at]',
         'const bool routable=(sun.sky_shading||mw34::effects::settings().enabled)&&view[at]')
    edit('mfc_stage.hpp','#include "sun_tl_capture_stage.inc"','#include "sun_tl_capture_stage.inc"\n#include "effect_lighting_stage.inc"')
    edit('d3d_provider.inc','sun_capture_tl(c);sun_capture_sky(c);','sun_capture_tl(c);sun_capture_sky(c);effect_observe(c);')
    edit('d3d_provider.inc','distance_scene_log(sc);','distance_scene_log(sc);effect_scene(sc);')
    for name,path in [('effect_lighting.hpp',ROOT/'runtime/graphics/effect_lighting.hpp'),
                      ('effect_lighting_settings.hpp',SOURCE/'effect_lighting_settings.hpp'),
                      ('effect_lighting_stage.inc',SOURCE/'effect_lighting_stage.inc'),
                      ('effect_scene_frag.h',SOURCE/'effect_scene_frag.h')]:
        pending[host/name]=path.read_text()
    for path,text in pending.items():path.write_text(text)
    print('Installed effect lights in',host)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host-source',type=Path,required=True);a=p.parse_args();apply(a.host_source)
