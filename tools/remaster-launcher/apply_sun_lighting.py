"""Install the isolated directional-sun prototype in a copied alpha host."""
from pathlib import Path
import argparse
import shutil

HERE=Path(__file__).parent

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one sun anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    vk=host/'vk_scene.hpp'
    if '#include "sun_lighting.hpp"' in vk.read_text():raise RuntimeError('Use a fresh host copy; sun already installed')
    for name in ['sun_lighting.hpp','sun_lighting_stage.inc','sun_world_vert.h','sun_model_vert.h','sun_scene_frag.h','sun_tl_vert.h','sun_tl_capture_stage.inc']:
        shutil.copyfile(HERE/'native-overrides'/name,host/name)
    edit(vk,'#include "world_binding.hpp"','#include "world_binding.hpp"\n#include "sun_lighting.hpp"\n#include "sun_world_vert.h"\n#include "sun_model_vert.h"\n#include "sun_scene_frag.h"\n#include "sun_tl_vert.h"')
    edit(vk,'std::uint32_t color{};bool world{};','std::uint32_t color{};bool world{};std::array<float,12> sun_normal{};bool sun_eligible{};')
    edit(vk,'    Buffer upload, readback, vertexBuffer, texUpload;','''    Buffer upload, readback, vertexBuffer, texUpload, sunBuffer;
    VkDeviceSize sunStride{};
    VkDescriptorSetLayout sunSetLayout{};
    VkShaderModule sunWorldVert{},sunModelVert{},sunFrag{};
    std::map<std::uint64_t,std::uint64_t> sunChecked;
    bool sun_lit(const Draw& d)const {
        return mw34::sun::settings().enabled&&d.model&&d.model->sun_eligible&&(!d.model->world||(d.push.mode[0]&4));
    }
public:
    std::uint64_t sun_world_draws{},sun_model_draws{};
private:''')
    edit(vk,'        // Descriptor sets: one per distinct (texture, sampler).','''        bool sunScene=false;
        if(mw34::sun::settings().enabled){
            if(s.draws.size()>0xffffffffULL/sunStride)throw std::runtime_error("Sun uniform offsets exceed the Vulkan dynamic-offset range");
            ensure(sunBuffer,std::max<VkDeviceSize>(sunStride,sunStride*s.draws.size()),VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT);
            for(size_t at=0;at<s.draws.size();++at)if(!s.hud&&sun_lit(s.draws[at])){
                const auto& instance=*s.draws[at].model;const auto& geometry=*instance.geometry;
                auto previous=sunChecked.find(geometry.key);
                if(previous==sunChecked.end()||previous->second!=geometry.hash){
                    for(const auto& v:geometry.vertices){const double n=double(v.nx)*v.nx+double(v.ny)*v.ny+double(v.nz)*v.nz;
                        if(!std::isfinite(n)||n<1e-12)throw std::runtime_error("Sun prototype has an invalid source normal");}
                    sunChecked[geometry.key]=geometry.hash;
                }
                const auto u=mw34::sun::uniform(instance.sun_normal,mw34::sun::settings());
                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)+at*sunStride,&u,sizeof(u));sunScene=true;
            }
        }
        // Descriptor sets: one per distinct (texture, sampler).''')
    edit(vk,'            drawSets[i] = it->second;\n        }\n        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");','''            drawSets[i] = it->second;
        }
        VkDescriptorSet sunSet{};
        if(sunScene){
            VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};ai.descriptorPool=descriptorPool;ai.descriptorSetCount=1;ai.pSetLayouts=&sunSetLayout;
            check(f.vkAllocateDescriptorSets(device,&ai,&sunSet),"sun descriptor set");
            VkDescriptorBufferInfo info{sunBuffer.buffer,0,sizeof(mw34::sun::Uniform)};
            VkWriteDescriptorSet w{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};w.dstSet=sunSet;w.descriptorCount=1;w.descriptorType=VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC;w.pBufferInfo=&info;
            f.vkUpdateDescriptorSets(device,1,&w,0,nullptr);
        }
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");''')
    edit(vk,'            const bool model=bool(d.model);const VkPipelineLayout layout=model?modelLayout:pipelineLayout;',
         '            const bool model=bool(d.model),lit=!s.hud&&sun_lit(d);const VkPipelineLayout layout=model?modelLayout:pipelineLayout;')
    edit(vk,'pipeline(d.key,model,d.model&&d.model->world)','pipeline(d.key,model,d.model&&d.model->world,lit)')
    edit(vk,'            { const VkRect2D sc = scaled(d.scissor);', '''            if(lit){const std::uint32_t offset=std::uint32_t(o.index*sunStride);f.vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,layout,1,1,&sunSet,1,&offset);
                if(d.model->world)++sun_world_draws;else ++sun_model_draws;}
            { const VkRect2D sc = scaled(d.scissor);''')
    edit(vk,'            check(f.vkCreatePipelineLayout(device,&pli,nullptr,&modelLayout),"model pipeline layout");}', '''            std::array<VkDescriptorSetLayout,2> sets{setLayout,VK_NULL_HANDLE};
            if(mw34::sun::settings().enabled){
                sunStride=(sizeof(mw34::sun::Uniform)+p.limits.minUniformBufferOffsetAlignment-1)/p.limits.minUniformBufferOffsetAlignment*p.limits.minUniformBufferOffsetAlignment;
                if(p.limits.maxUniformBufferRange<sizeof(mw34::sun::Uniform))throw std::runtime_error("Sun uniform range unavailable");
                VkDescriptorSetLayoutBinding sb{0,VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC,1,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,nullptr};
                VkDescriptorSetLayoutCreateInfo si{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};si.bindingCount=1;si.pBindings=&sb;
                check(f.vkCreateDescriptorSetLayout(device,&si,nullptr,&sunSetLayout),"sun descriptor layout");
                sets[1]=sunSetLayout;pli.setLayoutCount=2;pli.pSetLayouts=sets.data();
                const auto& sun=mw34::sun::settings();std::fprintf(stderr,"Sun prototype: world +Y up, azimuth %.3f elevation %.3f strength %.3f ambient %.3f; textured original world and GPU replacement models\\n",double(sun.azimuth),double(sun.elevation),double(sun.strength),double(sun.ambient));
            }
            check(f.vkCreatePipelineLayout(device,&pli,nullptr,&modelLayout),"model pipeline layout");}''')
    edit(vk,'        std::array<VkAttachmentDescription, 2> at{};','''        if(mw34::sun::settings().enabled){
            if(!gpu_models())throw std::runtime_error("Sun prototype requires GPU geometry");
            sunWorldVert=module(sun_world_vert_spv,sizeof(sun_world_vert_spv));sunModelVert=module(sun_model_vert_spv,sizeof(sun_model_vert_spv));sunFrag=module(sun_scene_frag_spv,sizeof(sun_scene_frag_spv));
        }
        std::array<VkAttachmentDescription, 2> at{};''')
    edit(vk,'        VkDescriptorPoolSize ps{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, n};','''        const std::array<VkDescriptorPoolSize,2> ps{{{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,n},{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC,1}}};''')
    edit(vk,'pi.maxSets = n; pi.poolSizeCount = 1; pi.pPoolSizes = &ps;',
         'pi.maxSets = n+1; pi.poolSizeCount = mw34::sun::settings().enabled?2:1; pi.pPoolSizes = ps.data();')
    edit(vk,'VkPipeline pipeline(const PipelineKey &k,bool model=false,bool world=false)',
         'VkPipeline pipeline(const PipelineKey &k,bool model=false,bool world=false,bool lit=false)')
    edit(vk,'|(world?(1ULL<<58):0ULL);','|(world?(1ULL<<58):0ULL)|(lit?(1ULL<<59):0ULL);')
    edit(vk,'st[i].module = i ? frag : (world?worldVert:(model?modelVert:vert));',
         'st[i].module = lit?(i?sunFrag:(world?sunWorldVert:sunModelVert)):(i ? frag : (world?worldVert:(model?modelVert:vert)));')
    edit(vk,'const std::array<VkVertexInputAttributeDescription,4> wa{{{0,0,VK_FORMAT_R32G32B32_SFLOAT,0},{1,1,VK_FORMAT_R32_UINT,16},{2,1,VK_FORMAT_R32_UINT,20},{3,1,VK_FORMAT_R32G32_SFLOAT,24}}};',
         'const std::array<VkVertexInputAttributeDescription,5> wa{{{0,0,VK_FORMAT_R32G32B32_SFLOAT,0},{1,1,VK_FORMAT_R32_UINT,16},{2,1,VK_FORMAT_R32_UINT,20},{3,1,VK_FORMAT_R32G32_SFLOAT,24},{4,0,VK_FORMAT_R32G32B32_SFLOAT,12}}};')
    edit(vk,'vi.vertexAttributeDescriptionCount=world?4:(model?3:4);',
         'vi.vertexAttributeDescriptionCount=world?(lit?5:4):(model?3:4);')
    edit(vk,'&vertexBuffer, &texUpload, &presentUpload','&vertexBuffer, &texUpload, &presentUpload, &sunBuffer')
    edit(vk,'        if(modelVert)f.vkDestroyShaderModule(device,modelVert,nullptr);','''        if(sunSetLayout)f.vkDestroyDescriptorSetLayout(device,sunSetLayout,nullptr);
        if(sunWorldVert)f.vkDestroyShaderModule(device,sunWorldVert,nullptr);
        if(sunModelVert)f.vkDestroyShaderModule(device,sunModelVert,nullptr);
        if(sunFrag)f.vkDestroyShaderModule(device,sunFrag,nullptr);
        if(modelVert)f.vkDestroyShaderModule(device,modelVert,nullptr);''')
    edit(host/'mfc_stage.hpp','#include "world_direct_stage.inc"','#include "world_direct_stage.inc"\n#include "sun_lighting_stage.inc"\n#include "sun_tl_capture_stage.inc"')
    edit(host/'world_direct_stage.inc','float(near_clip)};draw.model=std::move(instance);','float(near_clip)};sun_capture_world(*instance,scope.node);draw.model=std::move(instance);')
    edit(host/'mesh_override_stage.inc','instance->color=batch.color;draw.model=std::move(instance);',
         'instance->color=batch.color;sun_capture_model(*instance,o.scope.node,node_to_camera,batch_to_camera);draw.model=std::move(instance);')
    edit(host/'world_geometry_stage.inc','<<",\\\"unmatched\\\":"<<world_misses',
         '<<",\\\"sun_world\\\":"<<(host.sren?host.sren->sun_world_draws:0)<<",\\\"sun_models\\\":"<<(host.sren?host.sren->sun_model_draws:0)<<",\\\"unmatched\\\":"<<world_misses')

    apply_tl(host)

def apply_tl(host):
    vk=host/'vk_scene.hpp'
    edit(vk,'std::shared_ptr<const ModelInstance> model{}; };','std::shared_ptr<const ModelInstance> model{};std::shared_ptr<const mw34::sun::Tl> sun_tl{}; };')
    edit(vk,'sun_world_draws{},sun_model_draws{};','sun_world_draws{},sun_model_draws{},sun_tl_draws{};')
    edit(vk,'return mw34::sun::settings().enabled&&d.model&&d.model->sun_eligible&&(!d.model->world||(d.push.mode[0]&4));',
         'return mw34::sun::settings().enabled&&((d.sun_tl&&(d.push.mode[0]&4))||(d.model&&d.model->sun_eligible&&(!d.model->world||(d.push.mode[0]&4))));')
    text=vk.read_text();a=text.index('                const auto& instance=*s.draws[at].model;');b=text.index('                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)',a)
    text=text[:a]+'''                const auto& draw=s.draws[at];mw34::sun::Uniform u;
                if(draw.model){
                    const auto& instance=*draw.model;const auto& geometry=*instance.geometry;
                    auto previous=sunChecked.find(geometry.key);
                    if(previous==sunChecked.end()||previous->second!=geometry.hash){
                        for(const auto& v:geometry.vertices){const double n=double(v.nx)*v.nx+double(v.ny)*v.ny+double(v.nz)*v.nz;
                            if(!std::isfinite(n)||n<1e-12)throw std::runtime_error("Sun prototype has an invalid source normal");}
                        sunChecked[geometry.key]=geometry.hash;
                    }
                    u=mw34::sun::uniform(instance.sun_normal,mw34::sun::settings());
                }else{
                    const auto& light=*draw.sun_tl;u=mw34::sun::uniform(light.camera_world,mw34::sun::settings());
                    u.projection={light.projection[1],light.projection[2],light.projection[3],light.projection[4]};u.extra={light.projection[0],0,0,1};
                }
'''+text[b:];vk.write_text(text)
    edit(vk,'layout=model?modelLayout:pipelineLayout;','layout=(model||lit)?modelLayout:pipelineLayout;')
    edit(vk,'if(d.model->world)++sun_world_draws;else ++sun_model_draws;',
         'if(!d.model)++sun_tl_draws;else if(d.model->world)++sun_world_draws;else ++sun_model_draws;')
    edit(vk,'VkShaderModule sunWorldVert{},sunModelVert{},sunFrag{};','VkShaderModule sunWorldVert{},sunModelVert{},sunTlVert{},sunFrag{};')
    edit(vk,'sunFrag=module(sun_scene_frag_spv,sizeof(sun_scene_frag_spv));','sunTlVert=module(sun_tl_vert_spv,sizeof(sun_tl_vert_spv));sunFrag=module(sun_scene_frag_spv,sizeof(sun_scene_frag_spv));')
    edit(vk,'(world?sunWorldVert:sunModelVert)','(world?sunWorldVert:(model?sunModelVert:sunTlVert))')
    edit(vk,'pi.layout = model?modelLayout:pipelineLayout;','pi.layout = (model||lit)?modelLayout:pipelineLayout;')
    edit(vk,'        if(sunFrag)f.vkDestroyShaderModule(device,sunFrag,nullptr);',
         '        if(sunTlVert)f.vkDestroyShaderModule(device,sunTlVert,nullptr);\n        if(sunFrag)f.vkDestroyShaderModule(device,sunFrag,nullptr);')
    edit(host/'mfc_stage.hpp','model{};unsigned hud_role{};','model{};std::shared_ptr<const mw34::sun::Tl>sun_tl{};unsigned hud_role{};')
    edit(host/'d3d_provider.inc','world_capture(c);if(!override_suppress_draw())','world_capture(c);sun_capture_tl(c);if(!override_suppress_draw())')
    edit(host/'d3d_provider.inc','  if(c.model&&c.model->world)dr.model=c.model;','  dr.sun_tl=c.sun_tl;\n  if(c.model&&c.model->world)dr.model=c.model;')
    wide=host/'widescreen_stage.inc'
    anchor='  for(unsigned i=d.first;i<d.first+d.count;++i){float x;auto*p=sc.vertices.data()'
    edit(wide,anchor,'''  if(d.sun_tl){auto light=std::make_shared<mw34::sun::Tl>(*d.sun_tl);light->projection[1]/=k;light->projection[3]=a+(light->projection[3]+.5f-a)/k-.5f;d.sun_tl=std::move(light);}
'''+anchor)
    edit(host/'world_geometry_stage.inc','<<",\\\"sun_models\\\":"<<(host.sren?host.sren->sun_model_draws:0)',
         '<<",\\\"sun_tl\\\":"<<(host.sren?host.sren->sun_tl_draws:0)<<",\\\"sun_models\\\":"<<(host.sren?host.sren->sun_model_draws:0)')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
