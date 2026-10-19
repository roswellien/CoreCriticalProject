"""Add the optional sun shadow map to a copied sun/normal-map test host.

Apply after apply_sun_lighting.py and the Mad Cat normal-map host edits. The
replacement GPU mechs are rendered into one orthographic sun depth map around
the active camera; the existing sun shader samples it on lit receivers.
Disabled (MW34_SUN_SHADOWS unset/0) every draw keeps its existing inputs.
"""
from pathlib import Path
import argparse
import shutil

HERE=Path(__file__).parent

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one shadow anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    vk=host/'vk_scene.hpp'
    if 'sun_shadow_vert.h' in vk.read_text():raise RuntimeError('Use a fresh host copy; sun shadows already installed')
    if 'normalSetLayout' not in vk.read_text():raise RuntimeError('Sun shadows expect the normal-map sun host')
    for name in ['sun_lighting.hpp','sun_world_vert.h','sun_model_vert.h','sun_scene_frag.h','sun_tl_vert.h','sun_shadow_vert.h']:
        shutil.copyfile(HERE/'native-overrides'/name,host/name)
    edit(vk,'#include "sun_tl_vert.h"','#include "sun_tl_vert.h"\n#include "sun_shadow_vert.h"\n#include <set>')
    edit(vk,'std::array<float,12> sun_normal{};bool sun_eligible{}; };','std::array<float,12> sun_normal{},sun_world{};bool sun_eligible{}; };')
    edit(vk,'    VkShaderModule sunWorldVert{},sunModelVert{},sunTlVert{},sunFrag{};','''    VkShaderModule sunWorldVert{},sunModelVert{},sunTlVert{},sunFrag{};
    // Optional sun shadow map. Casters are GPU replacement models only.
    struct ShadowCaster { VkBuffer buffer{};unsigned count{};std::array<float,12> rows{}; };
    struct ShadowFrame { bool active{},reused{};mw34::sun::ShadowView view;std::vector<ShadowCaster> casters; };
    mw34::sun::ShadowView lastShadowView;unsigned scenesSinceShadow{~0u};
    VkImage shadowImage{};VkDeviceMemory shadowMemory{};VkImageView shadowView{};VkSampler shadowSampler{};
    VkRenderPass shadowPass{};VkFramebuffer shadowFramebuffer{};VkPipelineLayout shadowLayout{};VkPipeline shadowPipeline{};VkShaderModule shadowVert{};
    void init_shadow() {
        const auto& sun=mw34::sun::settings();const unsigned size=sun.shadows?sun.shadow_size:1;
        VkFormat format=VK_FORMAT_D32_SFLOAT;VkFormatProperties fp{};f.vkGetPhysicalDeviceFormatProperties(gpu,format,&fp);
        const VkFormatFeatureFlags need=VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT|VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT;
        if((fp.optimalTilingFeatures&need)!=need){format=VK_FORMAT_D16_UNORM;f.vkGetPhysicalDeviceFormatProperties(gpu,format,&fp);
            if((fp.optimalTilingFeatures&need)!=need)throw std::runtime_error("GPU cannot render and sample a sun shadow depth map");}
        const bool linear=(fp.optimalTilingFeatures&VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT)!=0;
        VkPhysicalDeviceProperties p{};f.vkGetPhysicalDeviceProperties(gpu,&p);
        if(size>p.limits.maxImageDimension2D||size>p.limits.maxFramebufferWidth||size>p.limits.maxFramebufferHeight)throw std::runtime_error("Sun shadow map size exceeds the GPU limit");
        image(shadowImage,shadowMemory,shadowView,size,size,format,VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_DEPTH_BIT);
        VkSamplerCreateInfo si{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};si.magFilter=si.minFilter=linear?VK_FILTER_LINEAR:VK_FILTER_NEAREST;si.mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST;
        si.addressModeU=si.addressModeV=si.addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;si.compareEnable=VK_TRUE;si.compareOp=VK_COMPARE_OP_LESS_OR_EQUAL;
        check(f.vkCreateSampler(device,&si,nullptr,&shadowSampler),"sun shadow sampler");
        if(!sun.shadows)return;  // 1x1 placeholder keeps the sun descriptor set valid.
        VkAttachmentDescription at{};at.format=format;at.samples=VK_SAMPLE_COUNT_1_BIT;at.loadOp=VK_ATTACHMENT_LOAD_OP_CLEAR;at.storeOp=VK_ATTACHMENT_STORE_OP_STORE;
        at.stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE;at.stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE;
        at.initialLayout=VK_IMAGE_LAYOUT_UNDEFINED;at.finalLayout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
        VkAttachmentReference dr{0,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL};
        VkSubpassDescription sp{};sp.pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS;sp.pDepthStencilAttachment=&dr;
        // Previous scene's receiver reads -> depth writes -> this scene's receiver reads.
        std::array<VkSubpassDependency,2> dep{};
        dep[0]={VK_SUBPASS_EXTERNAL,0,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,
                0,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT|VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,0};
        dep[1]={0,VK_SUBPASS_EXTERNAL,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
                VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT,0};
        VkRenderPassCreateInfo rpi{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};rpi.attachmentCount=1;rpi.pAttachments=&at;rpi.subpassCount=1;rpi.pSubpasses=&sp;rpi.dependencyCount=2;rpi.pDependencies=dep.data();
        check(f.vkCreateRenderPass(device,&rpi,nullptr,&shadowPass),"sun shadow render pass");
        VkFramebufferCreateInfo fi{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};fi.renderPass=shadowPass;fi.attachmentCount=1;fi.pAttachments=&shadowView;fi.width=fi.height=size;fi.layers=1;
        check(f.vkCreateFramebuffer(device,&fi,nullptr,&shadowFramebuffer),"sun shadow framebuffer");
        VkPushConstantRange pr{VK_SHADER_STAGE_VERTEX_BIT,0,48};
        VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};pli.pushConstantRangeCount=1;pli.pPushConstantRanges=&pr;
        check(f.vkCreatePipelineLayout(device,&pli,nullptr,&shadowLayout),"sun shadow pipeline layout");
        VkPipelineShaderStageCreateInfo st{VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};st.stage=VK_SHADER_STAGE_VERTEX_BIT;st.module=shadowVert;st.pName="main";
        VkVertexInputBindingDescription vb{0,sizeof(ModelVertex),VK_VERTEX_INPUT_RATE_VERTEX};VkVertexInputAttributeDescription va{0,0,VK_FORMAT_R32G32B32_SFLOAT,0};
        VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};vi.vertexBindingDescriptionCount=1;vi.pVertexBindingDescriptions=&vb;vi.vertexAttributeDescriptionCount=1;vi.pVertexAttributeDescriptions=&va;
        VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};ia.topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        VkViewport vp{0,0,float(size),float(size),0,1};VkRect2D sc{{0,0},{size,size}};
        VkPipelineViewportStateCreateInfo vps{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};vps.viewportCount=1;vps.pViewports=&vp;vps.scissorCount=1;vps.pScissors=&sc;
        // Two-sided: replacement meshes are not guaranteed closed. Slope bias
        // plus the receiver's normal offset/bias avoid self-shadow acne.
        VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};rs.polygonMode=VK_POLYGON_MODE_FILL;rs.cullMode=VK_CULL_MODE_NONE;rs.lineWidth=1;
        rs.depthBiasEnable=VK_TRUE;rs.depthBiasSlopeFactor=1.5f;
        VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};ms.rasterizationSamples=VK_SAMPLE_COUNT_1_BIT;
        VkPipelineDepthStencilStateCreateInfo ds{VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};ds.depthTestEnable=ds.depthWriteEnable=VK_TRUE;ds.depthCompareOp=VK_COMPARE_OP_LESS;
        VkPipelineColorBlendStateCreateInfo bs{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
        VkGraphicsPipelineCreateInfo gi{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};gi.stageCount=1;gi.pStages=&st;gi.pVertexInputState=&vi;gi.pInputAssemblyState=&ia;gi.pViewportState=&vps;
        gi.pRasterizationState=&rs;gi.pMultisampleState=&ms;gi.pDepthStencilState=&ds;gi.pColorBlendState=&bs;gi.layout=shadowLayout;gi.renderPass=shadowPass;
        check(f.vkCreateGraphicsPipelines(device,VK_NULL_HANDLE,1,&gi,nullptr,&shadowPipeline),"sun shadow pipeline");
        std::fprintf(stderr,"Sun shadows: %ux%u %s map, range +-%.1f, receiver bias %.3f, darkness %.2f, %s PCF; GPU replacement models cast\\n",
            size,size,format==VK_FORMAT_D32_SFLOAT?"D32":"D16",double(sun.shadow_range),double(sun.shadow_bias),double(sun.shadow_darkness),linear?"bilinear":"point");
    }
    // Centre on the active world camera (from its visible TL receivers),
    // pushed half a range ahead horizontally, then gather each visible GPU
    // replacement draw once with its sun-clip transform.
    ShadowFrame prepare_shadow(const Scene& s) {
        ShadowFrame frame;const auto& sun=mw34::sun::settings();
        if(!sun.shadows||s.hud)return frame;
        // MW3 may draw terrain and mechs in separate BeginScene/EndScene
        // batches. A batch without casters (or without a camera reference)
        // samples the latest map with that map's exact sun transform.
        if(scenesSinceShadow!=~0u)++scenesSinceShadow;
        auto reuse=[&]{if(scenesSinceShadow<=8){frame.active=frame.reused=true;frame.view=lastShadowView;++sun_shadow_reused;}return frame;};
        const mw34::sun::Tl* camera=nullptr;
        for(const auto& d:s.draws)if(d.sun_tl&&sun_lit(d)){camera=d.sun_tl.get();break;}
        if(!camera)return reuse();
        const auto& m=camera->camera_world;
        std::array<double,3> centre{m[3],m[7],m[11]};
        const double fx=m[2],fz=m[10],fl=std::sqrt(fx*fx+fz*fz);
        if(fl>1e-6){centre[0]+=fx/fl*sun.shadow_range*.5;centre[2]+=fz/fl*sun.shadow_range*.5;}
        frame.view=mw34::sun::shadow_view(centre,sun);
        std::set<std::pair<VkBuffer,std::array<float,12>>> seen;
        const double margin=1+64.0/sun.shadow_range;
        unsigned ahead=0,outside=0;
        for(const auto& d:s.draws){
            if(!d.model||d.model->world||!d.count||!sun_lit(d))continue;
            const auto& i=*d.model;const auto& b=model_buffers.at(i.geometry->key);
            const auto rows=mw34::sun::shadow_caster(frame.view,i.sun_world);
            if(std::abs(rows[3])>margin||std::abs(rows[7])>margin){++outside;continue;}
            if(!seen.insert({b.local.buffer,rows}).second)continue;
            frame.casters.push_back({b.local.buffer,b.count,rows});
            if((i.sun_world[3]-m[3])*fx+(i.sun_world[11]-m[11])*fz>0)++ahead;
        }
        frame.active=!frame.casters.empty();
        if(!frame.active)return reuse();
        if(const char* audit=std::getenv("MW34_SUN_SHADOW_AUDIT");audit&&std::strtoull(audit,nullptr,10)==sun_shadow_scenes){
            std::fprintf(stderr,"Sun shadow audit scene %llu camera %.2f %.2f %.2f\\n",(unsigned long long)sun_shadow_scenes,m[3],m[7],m[11]);
            for(const auto& d:s.draws){if(!d.model||d.model->world||!d.count||!sun_lit(d))continue;const auto& w=d.model->sun_world;
                std::array<double,3> lo{1e30,1e30,1e30},hi{-1e30,-1e30,-1e30};
                for(const auto& v:d.model->geometry->vertices)for(unsigned r=0;r<3;++r){const double x=w[r*4]*v.x+w[r*4+1]*v.y+w[r*4+2]*v.z+w[r*4+3];lo[r]=std::min(lo[r],x);hi[r]=std::max(hi[r],x);}
                std::fprintf(stderr,"  caster key %016llx verts %zu world x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f\\n",(unsigned long long)d.model->geometry->key,d.model->geometry->vertices.size(),lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]);}
        }
        if(frame.active){lastShadowView=frame.view;scenesSinceShadow=0;}
        if(frame.active&&(sun_shadow_scenes<3||sun_shadow_scenes%600==0)){
            std::fprintf(stderr,"Sun shadow scene %llu: camera %.2f %.2f %.2f forward %.3f %.3f, casters %zu (%u ahead, %u outside region), texel %.4f\\n",
                (unsigned long long)sun_shadow_scenes,m[3],m[7],m[11],fx,fz,frame.casters.size(),ahead,outside,frame.view.texel);
            // Projection contract: screen = centre + scale * camera.xy / camera.z for both receiver kinds.
            const auto& tp=camera->projection;
            std::fprintf(stderr,"  TL receivers: scale %.3f %.3f centre %.2f %.2f\\n",double(tp[1])*tp[0],double(tp[2])*tp[0],tp[3],tp[4]);
            for(const auto& d:s.draws)if(d.model&&!d.model->world&&sun_lit(d)){const auto& p=d.model->projection;const auto& w=d.model->sun_world;
                std::fprintf(stderr,"  GPU model: scale %.3f %.3f centre %.2f %.2f, camera origin %.2f %.2f %.2f, world origin %.2f %.2f %.2f\\n",
                    double(p[1])*p[0],double(p[2])*p[0],p[3],p[4],d.model->camera[3],d.model->camera[7],d.model->camera[11],w[3],w[7],w[11]);break;}
        }
        return frame;
    }
    void record_shadow(const ShadowFrame& frame) {
        const unsigned size=mw34::sun::settings().shadow_size;
        VkClearValue clear{};clear.depthStencil.depth=1.f;
        VkRenderPassBeginInfo rb{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};rb.renderPass=shadowPass;rb.framebuffer=shadowFramebuffer;rb.renderArea={{0,0},{size,size}};rb.clearValueCount=1;rb.pClearValues=&clear;
        f.vkCmdBeginRenderPass(cmd,&rb,VK_SUBPASS_CONTENTS_INLINE);
        f.vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,shadowPipeline);
        VkBuffer bound{};const VkDeviceSize zero=0;
        for(const auto& c:frame.casters){
            if(c.buffer!=bound){f.vkCmdBindVertexBuffers(cmd,0,1,&c.buffer,&zero);bound=c.buffer;}
            f.vkCmdPushConstants(cmd,shadowLayout,VK_SHADER_STAGE_VERTEX_BIT,0,48,c.rows.data());f.vkCmdDraw(cmd,c.count,1,0,0);
        }
        f.vkCmdEndRenderPass(cmd);
        ++sun_shadow_scenes;sun_shadow_casters+=frame.casters.size();
    }''')
    edit(vk,'sun_world_draws{},sun_model_draws{},sun_tl_draws{};','sun_world_draws{},sun_model_draws{},sun_tl_draws{},sun_shadow_scenes{},sun_shadow_casters{},sun_shadow_reused{};')
    edit(vk,'''                VkDescriptorSetLayoutBinding sb{0,VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC,1,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,nullptr};
                VkDescriptorSetLayoutCreateInfo si{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};si.bindingCount=1;si.pBindings=&sb;''',
'''                const std::array<VkDescriptorSetLayoutBinding,2> sb{{{0,VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC,1,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,nullptr},
                    {1,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr}}};
                VkDescriptorSetLayoutCreateInfo si{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};si.bindingCount=2;si.pBindings=sb.data();''')
    edit(vk,'sunFrag=module(sun_scene_frag_spv,sizeof(sun_scene_frag_spv));\n        }',
         'sunFrag=module(sun_scene_frag_spv,sizeof(sun_scene_frag_spv));\n            if(mw34::sun::settings().shadows)shadowVert=module(sun_shadow_vert_spv,sizeof(sun_shadow_vert_spv));\n        }')
    edit(vk,'check(f.vkCreateRenderPass(device, &rpi, nullptr, &renderPass), "render pass");',
         'check(f.vkCreateRenderPass(device, &rpi, nullptr, &renderPass), "render pass");\n        if(mw34::sun::settings().enabled)init_shadow();')
    edit(vk,'''        barrier(flatNormal.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);''',
'''        barrier(flatNormal.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        if(shadowImage)barrier(shadowImage, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, 0, VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);''')
    edit(vk,'{{{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,n*2},','{{{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,n*2+1},')
    edit(vk,'        bool sunScene=false;','        const ShadowFrame shadowFrame=prepare_shadow(s);\n        bool sunScene=false;')
    edit(vk,'                    u=mw34::sun::uniform(instance.sun_normal,mw34::sun::settings());',
         '                    u=mw34::sun::uniform(instance.sun_normal,mw34::sun::settings());u.world=instance.sun_world;')
    edit(vk,'u.extra={light.projection[0],mw34::sun::settings().normal_strength,0,1};',
         'u.extra={light.projection[0],mw34::sun::settings().normal_strength,mw34::sun::settings().shadow_debug?1.f:0.f,1};')
    edit(vk,'                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)+at*sunStride,&u,sizeof(u));sunScene=true;',
'''                if(shadowFrame.active){const auto& sun=mw34::sun::settings();for(unsigned i=0;i<12;++i)u.shadow[i]=float(shadowFrame.view.rows[i]);
                    u.shadow_params={1.f,float(shadowFrame.view.texel),float(sun.shadow_bias*shadowFrame.view.depth_scale),sun.shadow_darkness};}
                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)+at*sunStride,&u,sizeof(u));sunScene=true;''')
    edit(vk,'''            VkWriteDescriptorSet w{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};w.dstSet=sunSet;w.descriptorCount=1;w.descriptorType=VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC;w.pBufferInfo=&info;
            f.vkUpdateDescriptorSets(device,1,&w,0,nullptr);''',
'''            VkDescriptorImageInfo shadowInfo{shadowSampler,shadowView,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
            std::array<VkWriteDescriptorSet,2> w{};for(auto& x:w){x.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;x.dstSet=sunSet;x.descriptorCount=1;}
            w[0].descriptorType=VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC;w[0].pBufferInfo=&info;
            w[1].dstBinding=1;w[1].descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;w[1].pImageInfo=&shadowInfo;
            f.vkUpdateDescriptorSets(device,2,w.data(),0,nullptr);''')
    edit(vk,'        if(s.hud&&quality_world_dirty&&fxaa_enabled())record_fxaa();',
         '        if(s.hud&&quality_world_dirty&&fxaa_enabled())record_fxaa();\n        if(shadowFrame.active&&!shadowFrame.reused)record_shadow(shadowFrame);')
    edit(vk,'        if(sunSetLayout)f.vkDestroyDescriptorSetLayout(device,sunSetLayout,nullptr);','''        if(shadowPipeline)f.vkDestroyPipeline(device,shadowPipeline,nullptr);
        if(shadowLayout)f.vkDestroyPipelineLayout(device,shadowLayout,nullptr);
        if(shadowFramebuffer)f.vkDestroyFramebuffer(device,shadowFramebuffer,nullptr);
        if(shadowPass)f.vkDestroyRenderPass(device,shadowPass,nullptr);
        if(shadowSampler)f.vkDestroySampler(device,shadowSampler,nullptr);
        if(shadowView)f.vkDestroyImageView(device,shadowView,nullptr);
        if(shadowImage)f.vkDestroyImage(device,shadowImage,nullptr);
        if(shadowMemory)f.vkFreeMemory(device,shadowMemory,nullptr);
        if(shadowVert)f.vkDestroyShaderModule(device,shadowVert,nullptr);
        if(sunSetLayout)f.vkDestroyDescriptorSetLayout(device,sunSetLayout,nullptr);''')
    stage=host/'sun_lighting_stage.inc'
    edit(stage,' instance.sun_normal=mw34::sun::normal_matrix(override_product(camera_world,local_camera));instance.sun_eligible=true;',
         ' const auto local_world=override_product(camera_world,local_camera);\n instance.sun_normal=mw34::sun::normal_matrix(local_world);instance.sun_world=mw34::sun::world_matrix(local_world);instance.sun_eligible=true;')
    edit(stage,' instance.sun_normal=mw34::sun::normal_matrix(override_product(camera_world,batch_camera));instance.sun_eligible=true;',
         ' const auto local_world=override_product(camera_world,batch_camera);\n instance.sun_normal=mw34::sun::normal_matrix(local_world);instance.sun_world=mw34::sun::world_matrix(local_world);instance.sun_eligible=true;')
    edit(host/'world_geometry_stage.inc','<<",\\\"sun_models\\\":"<<(host.sren?host.sren->sun_model_draws:0)',
         '<<",\\\"sun_models\\\":"<<(host.sren?host.sren->sun_model_draws:0)<<",\\\"sun_shadow_scenes\\\":"<<(host.sren?host.sren->sun_shadow_scenes:0)<<",\\\"sun_shadow_casters\\\":"<<(host.sren?host.sren->sun_shadow_casters:0)<<",\\\"sun_shadow_reused\\\":"<<(host.sren?host.sren->sun_shadow_reused:0)')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
