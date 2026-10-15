// Private Renderer members: mip uploads and the world-only FXAA pass.
// No CPU frame transfer, guest framebuffer mutation or supersampling.
void generate_mips(Tex&t){
    unsigned w=t.width,h=t.height;
    for(unsigned level=1;level<t.levels;++level){
        barrier(t.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_IMAGE_ASPECT_COLOR_BIT,level-1);
        const unsigned nw=std::max(1U,w/2),nh=std::max(1U,h/2);
        VkImageBlit b{};b.srcSubresource={VK_IMAGE_ASPECT_COLOR_BIT,level-1,0,1};b.dstSubresource={VK_IMAGE_ASPECT_COLOR_BIT,level,0,1};
        b.srcOffsets[1]={int(w),int(h),1};b.dstOffsets[1]={int(nw),int(nh),1};
        f.vkCmdBlitImage(cmd,t.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,t.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&b,VK_FILTER_LINEAR);
        barrier(t.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_ACCESS_TRANSFER_READ_BIT,VK_ACCESS_SHADER_READ_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_IMAGE_ASPECT_COLOR_BIT,level-1);
        w=nw;h=nh;
    }
    barrier(t.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_IMAGE_ASPECT_COLOR_BIT,t.levels-1);
    mip_levels_uploaded+=t.levels-1;
}
void init_quality(){
    VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT,0,2*sizeof(float)};
    VkPipelineLayoutCreateInfo layout{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};layout.setLayoutCount=1;layout.pSetLayouts=&setLayout;layout.pushConstantRangeCount=1;layout.pPushConstantRanges=&range;
    check(f.vkCreatePipelineLayout(device,&layout,nullptr,&qualityLayout),"FXAA pipeline layout");
    auto module=[&](const std::uint32_t*code,size_t bytes){VkShaderModuleCreateInfo mi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};mi.codeSize=bytes;mi.pCode=code;VkShaderModule out{};check(f.vkCreateShaderModule(device,&mi,nullptr,&out),"FXAA shader module");return out;};
    qualityVert=module(fxaa_vert_spv,sizeof(fxaa_vert_spv));qualityFrag=module(fxaa_frag_spv,sizeof(fxaa_frag_spv));
    VkPipelineShaderStageCreateInfo stages[2]{};for(unsigned i=0;i<2;++i){stages[i].sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;stages[i].stage=i?VK_SHADER_STAGE_FRAGMENT_BIT:VK_SHADER_STAGE_VERTEX_BIT;stages[i].module=i?qualityFrag:qualityVert;stages[i].pName="main";}
    VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};ia.topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkPipelineViewportStateCreateInfo vp{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};vp.viewportCount=vp.scissorCount=1;
    VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};rs.polygonMode=VK_POLYGON_MODE_FILL;rs.cullMode=VK_CULL_MODE_NONE;rs.lineWidth=1;
    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};ms.rasterizationSamples=VK_SAMPLE_COUNT_1_BIT;
    VkPipelineDepthStencilStateCreateInfo ds{VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};ds.depthCompareOp=VK_COMPARE_OP_ALWAYS;
    VkPipelineColorBlendAttachmentState cb{};cb.colorWriteMask=15;
    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};blend.attachmentCount=1;blend.pAttachments=&cb;
    const VkDynamicState dynamic[2]{VK_DYNAMIC_STATE_VIEWPORT,VK_DYNAMIC_STATE_SCISSOR};VkPipelineDynamicStateCreateInfo dy{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};dy.dynamicStateCount=2;dy.pDynamicStates=dynamic;
    VkGraphicsPipelineCreateInfo pi{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};pi.stageCount=2;pi.pStages=stages;pi.pVertexInputState=&vi;pi.pInputAssemblyState=&ia;pi.pViewportState=&vp;pi.pRasterizationState=&rs;pi.pMultisampleState=&ms;pi.pDepthStencilState=&ds;pi.pColorBlendState=&blend;pi.pDynamicState=&dy;pi.layout=qualityLayout;pi.renderPass=renderPass;
    check(f.vkCreateGraphicsPipelines(device,VK_NULL_HANDLE,1,&pi,nullptr,&qualityPipeline),"FXAA pipeline");
    VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1};VkDescriptorPoolCreateInfo poolInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};poolInfo.maxSets=1;poolInfo.poolSizeCount=1;poolInfo.pPoolSizes=&size;
    check(f.vkCreateDescriptorPool(device,&poolInfo,nullptr,&qualityPool),"FXAA descriptor pool");VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};ai.descriptorPool=qualityPool;ai.descriptorSetCount=1;ai.pSetLayouts=&setLayout;check(f.vkAllocateDescriptorSets(device,&ai,&qualitySet),"FXAA descriptor set");
}
void record_fxaa(){
    if(!quality_world_dirty)return;
    if(!qualitySource.image||!qualityPipeline)throw std::runtime_error("FXAA target or pipeline unavailable");
    // The temporary is a color copy, not a second rasterization. Original D16
    // stays intact; later HUD draws use the original depth-disabled pipeline.
    if(in_attachment_layout){barrier(colorImage.image,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
        barrier(depthImage.image,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT|VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_IMAGE_ASPECT_DEPTH_BIT);}
    else barrier(depthImage.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_ACCESS_TRANSFER_READ_BIT,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT|VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_IMAGE_ASPECT_DEPTH_BIT);
    barrier(qualitySource.image,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,0,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
    blit_img(colorImage.image,rw,rh,qualitySource.image,rw,rh,VK_IMAGE_ASPECT_COLOR_BIT,VK_FILTER_NEAREST);
    barrier(qualitySource.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
    barrier(colorImage.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_ACCESS_TRANSFER_READ_BIT,VK_ACCESS_COLOR_ATTACHMENT_READ_BIT|VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
    VkRenderPassBeginInfo rb{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};rb.renderPass=renderPass;rb.framebuffer=framebuffer;rb.renderArea={{0,0},{rw,rh}};
    f.vkCmdBeginRenderPass(cmd,&rb,VK_SUBPASS_CONTENTS_INLINE);
    VkViewport vp{0,0,float(rw),float(rh),0,1};VkRect2D scissor{{0,0},{rw,rh}};f.vkCmdSetViewport(cmd,0,1,&vp);f.vkCmdSetScissor(cmd,0,1,&scissor);
    f.vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,qualityPipeline);f.vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,qualityLayout,0,1,&qualitySet,0,nullptr);
    const float pixel[2]{1.f/float(rw),1.f/float(rh)};f.vkCmdPushConstants(cmd,qualityLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,sizeof pixel,pixel);f.vkCmdDraw(cmd,3,1,0,0);
    f.vkCmdEndRenderPass(cmd);
    // Color remains resident; the following normal render pass loads these
    // writes. Explicitly order the two passes, with depth preserved.
    barrier(colorImage.image,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,VK_ACCESS_COLOR_ATTACHMENT_READ_BIT|VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
    quality_world_dirty=false;in_attachment_layout=true;++fxaa_passes;
}
