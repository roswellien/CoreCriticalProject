"""Apply the bounded original-mesh GPU bridge to a fresh private host snapshot."""
from pathlib import Path
import argparse
import shutil


def replace(path, old, new):
    value=path.read_text()
    if value.count(old)!=1:
        raise RuntimeError(f'{path.name}: expected one source contract: {old[:70]}')
    path.write_text(value.replace(old,new))


def apply(host):
    source=Path(__file__).parent/'native-overrides'
    for name in ('world_geometry_stage.inc','world_scene.vert','world_scene_vert.h'):
        shutil.copyfile(source/name,host/name)
    stage=host/'mfc_stage.hpp'
    replace(stage,' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};',
        ''' #include "world_geometry_stage.inc"
 void*remaster_body(State*s,unsigned target,void*p,Body body){
  if(world_enabled()&&target==0x4f6720){++world_cell_depth;try{void*r=remaster_body_inner(s,target,p,body);--world_cell_depth;return r;}catch(...){--world_cell_depth;throw;}}
  if(world_enabled()&&target==0x53f2e0){auto previous=world_scope;world_scope=world_begin(state.gpr.rcx.dword);try{void*r=remaster_body_inner(s,target,p,body);world_scope=std::move(previous);return r;}catch(...){world_scope=std::move(previous);throw;}}
  return remaster_body_inner(s,target,p,body);
 }
 void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};''')
    provider=host/'d3d_provider.inc'
    replace(provider,'zoom_capture_command(c);if(!override_suppress_draw())',
            'zoom_capture_command(c);world_capture(c);if(!override_suppress_draw())')
    replace(provider,'  if(c.model){if(!mw34::vkscene::Renderer::gpu_models()',
            '  if(c.model&&c.model->world)dr.model=c.model;\n  if(c.model&&!c.model->world){if(!mw34::vkscene::Renderer::gpu_models()')
    replace(host/'vdd.inc',' geometry_profile.present(host.frames);',
            ' world_present();\n geometry_profile.present(host.frames);')
    vk=host/'vk_scene.hpp'
    replace(vk,'std::uint64_t model_uploads{},model_uploaded_bytes{},model_draws{};',
            'std::uint64_t model_uploads{},model_uploaded_bytes{},model_draws{},world_gpu_draws{};')
    replace(vk,'#include "model_scene_vert.h"','#include "world_scene_vert.h"\n#include "model_scene_vert.h"')
    replace(vk,'std::uint32_t color{}; };','std::uint32_t color{};bool world{}; };')
    replace(vk,'VkShaderModule vert{}, frag{},modelVert{};','VkShaderModule vert{}, frag{},modelVert{},worldVert{};')
    replace(vk,'if(gpu_models())modelVert=module(model_scene_vert_spv,sizeof(model_scene_vert_spv));',
            'if(gpu_models()){modelVert=module(model_scene_vert_spv,sizeof(model_scene_vert_spv));worldVert=module(world_scene_vert_spv,sizeof(world_scene_vert_spv));}')
    replace(vk,'if(modelVert)f.vkDestroyShaderModule(device,modelVert,nullptr);',
            'if(modelVert)f.vkDestroyShaderModule(device,modelVert,nullptr);\n        if(worldVert)f.vkDestroyShaderModule(device,worldVert,nullptr);')
    replace(vk,'pipeline(d.key,model)', 'pipeline(d.key,model,d.model&&d.model->world)')
    replace(vk,'&mp);++model_draws;', '&mp);++model_draws;if(i.world)++world_gpu_draws;')
    replace(vk,'if(!b.uploaded||d.first||d.count!=b.count)', 'if(!b.uploaded||(!i.world&&d.first)||d.count!=b.count)')
    replace(vk,'if(boundVertices!=b.local.buffer){f.vkCmdBindVertexBuffers(cmd,0,1,&b.local.buffer,&zero);boundVertices=b.local.buffer;}ModelPush mp{};',
            'if(i.world){const VkBuffer buffers[2]{b.local.buffer,vertexBuffer.buffer};const VkDeviceSize offsets[2]{0,VkDeviceSize(d.first)*32};f.vkCmdBindVertexBuffers(cmd,0,2,buffers,offsets);boundVertices=b.local.buffer;}\n'
            '                else if(boundVertices!=b.local.buffer){f.vkCmdBindVertexBuffers(cmd,0,1,&b.local.buffer,&zero);boundVertices=b.local.buffer;}ModelPush mp{};')
    replace(vk,'mp.base.factor[0]=float((i.color>>16)&255)/255.f;mp.base.factor[1]=float((i.color>>8)&255)/255.f;mp.base.factor[2]=float(i.color&255)/255.f;mp.base.factor[3]=1.f;',
            'if(!i.world){mp.base.factor[0]=float((i.color>>16)&255)/255.f;mp.base.factor[1]=float((i.color>>8)&255)/255.f;mp.base.factor[2]=float(i.color&255)/255.f;mp.base.factor[3]=1.f;}')
    replace(vk,'f.vkCmdDraw(cmd, d.count, 1, d.first, 0);','f.vkCmdDraw(cmd, d.count, 1, d.model&&d.model->world?0:d.first, 0);')
    replace(vk,'VkPipeline pipeline(const PipelineKey &k,bool model=false)',
            'VkPipeline pipeline(const PipelineKey &k,bool model=false,bool world=false)')
    replace(vk,'k.packed()|(model?(1ULL<<57):0ULL)', 'k.packed()|(model?(1ULL<<57):0ULL)|(world?(1ULL<<58):0ULL)')
    replace(vk,'(model?modelVert:vert)', '(world?worldVert:(model?modelVert:vert))')
    old='vi.vertexBindingDescriptionCount = 1; vi.pVertexBindingDescriptions = &vb; vi.vertexAttributeDescriptionCount = model?3:4; vi.pVertexAttributeDescriptions = model?ma.data():va.data();'
    replace(vk,old,'''const std::array<VkVertexInputBindingDescription,2> wb{{{0,32,VK_VERTEX_INPUT_RATE_VERTEX},{1,32,VK_VERTEX_INPUT_RATE_VERTEX}}};
        const std::array<VkVertexInputAttributeDescription,4> wa{{{0,0,VK_FORMAT_R32G32B32_SFLOAT,0},{1,1,VK_FORMAT_R32_UINT,16},{2,1,VK_FORMAT_R32_UINT,20},{3,1,VK_FORMAT_R32G32_SFLOAT,24}}};
        vi.vertexBindingDescriptionCount=world?2:1;vi.pVertexBindingDescriptions=world?wb.data():&vb;vi.vertexAttributeDescriptionCount=world?4:(model?3:4);vi.pVertexAttributeDescriptions=world?wa.data():(model?ma.data():va.data());''')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
