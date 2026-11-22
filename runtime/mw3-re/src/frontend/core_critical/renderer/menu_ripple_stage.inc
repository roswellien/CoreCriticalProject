void destroy_menu_ripple_pipeline() {
    if (menuRipplePipeline)
        f.vkDestroyPipeline(device, menuRipplePipeline, nullptr);
    if (menuRippleLayout)
        f.vkDestroyPipelineLayout(device, menuRippleLayout, nullptr);
    if (menuRipplePool)
        f.vkDestroyDescriptorPool(device, menuRipplePool, nullptr);
    if (menuRippleVert)
        f.vkDestroyShaderModule(device, menuRippleVert, nullptr);
    if (menuRippleFrag)
        f.vkDestroyShaderModule(device, menuRippleFrag, nullptr);
    menuRipplePipeline = {};
    menuRippleLayout = {};
    menuRipplePool = {};
    menuRippleSet = {};
    menuRippleVert = menuRippleFrag = {};
}
void init_menu_ripple() {
    if (menuRippleSet)
        return;
    try {
        VkPushConstantRange push_constant_range{VK_SHADER_STAGE_FRAGMENT_BIT, 0,
                                                16 * sizeof(float)};
        VkPipelineLayoutCreateInfo layout{};
        layout.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        layout.setLayoutCount = 1;
        layout.pSetLayouts = &setLayout;
        layout.pushConstantRangeCount = 1;
        layout.pPushConstantRanges = &push_constant_range;
        check(f.vkCreatePipelineLayout(device, &layout, nullptr, &menuRippleLayout),
              "Menu ripple pipeline layout");
        auto module = [&](const std::uint32_t *code, size_t bytes) {
            VkShaderModuleCreateInfo module_info{};
            module_info.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
            module_info.codeSize = bytes;
            module_info.pCode = code;
            VkShaderModule shader_module{};
            check(f.vkCreateShaderModule(device, &module_info, nullptr, &shader_module),
                  "Menu ripple shader module");
            return shader_module;
        };
        menuRippleVert = module(fxaa_vert_spv, sizeof(fxaa_vert_spv));
        menuRippleFrag = module(menu_ripple_frag_spv, sizeof(menu_ripple_frag_spv));
        VkPipelineShaderStageCreateInfo stages[2]{};
        for (unsigned i = 0; i < 2; ++i) {
            stages[i].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
            stages[i].stage = i ? VK_SHADER_STAGE_FRAGMENT_BIT : VK_SHADER_STAGE_VERTEX_BIT;
            stages[i].module = i ? menuRippleFrag : menuRippleVert;
            stages[i].pName = "main";
        }
        VkPipelineVertexInputStateCreateInfo vertex_input{};
        vertex_input.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
        VkPipelineInputAssemblyStateCreateInfo input_assembly{};
        input_assembly.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
        input_assembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        VkPipelineViewportStateCreateInfo viewport{};
        viewport.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
        viewport.viewportCount = viewport.scissorCount = 1;
        VkPipelineRasterizationStateCreateInfo rasterizer{};
        rasterizer.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
        rasterizer.polygonMode = VK_POLYGON_MODE_FILL;
        rasterizer.cullMode = VK_CULL_MODE_NONE;
        rasterizer.lineWidth = 1;
        VkPipelineMultisampleStateCreateInfo multisampling{};
        multisampling.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
        multisampling.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
        VkPipelineDepthStencilStateCreateInfo depth_stencil{};
        depth_stencil.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
        depth_stencil.depthCompareOp = VK_COMPARE_OP_ALWAYS;
        VkPipelineColorBlendAttachmentState color_attachment{};
        color_attachment.colorWriteMask = 15;
        VkPipelineColorBlendStateCreateInfo blend{};
        blend.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
        blend.attachmentCount = 1;
        blend.pAttachments = &color_attachment;
        const VkDynamicState dynamic[2]{VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
        VkPipelineDynamicStateCreateInfo dynamic_state{};
        dynamic_state.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
        dynamic_state.dynamicStateCount = 2;
        dynamic_state.pDynamicStates = dynamic;
        VkGraphicsPipelineCreateInfo pipeline_info{};
        pipeline_info.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
        pipeline_info.stageCount = 2;
        pipeline_info.pStages = stages;
        pipeline_info.pVertexInputState = &vertex_input;
        pipeline_info.pInputAssemblyState = &input_assembly;
        pipeline_info.pViewportState = &viewport;
        pipeline_info.pRasterizationState = &rasterizer;
        pipeline_info.pMultisampleState = &multisampling;
        pipeline_info.pDepthStencilState = &depth_stencil;
        pipeline_info.pColorBlendState = &blend;
        pipeline_info.pDynamicState = &dynamic_state;
        pipeline_info.layout = menuRippleLayout;
        pipeline_info.renderPass = renderPass;
        check(f.vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &pipeline_info, nullptr,
                                          &menuRipplePipeline),
              "Menu ripple pipeline");
        VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
                                  scene_texture_bindings};
        VkDescriptorPoolCreateInfo poolInfo{};
        poolInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        poolInfo.maxSets = 1;
        poolInfo.poolSizeCount = 1;
        poolInfo.pPoolSizes = &size;
        check(f.vkCreateDescriptorPool(device, &poolInfo, nullptr, &menuRipplePool),
              "Menu ripple descriptor pool");
        VkDescriptorSetAllocateInfo descriptor_allocation{};
        descriptor_allocation.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        descriptor_allocation.descriptorPool = menuRipplePool;
        descriptor_allocation.descriptorSetCount = 1;
        descriptor_allocation.pSetLayouts = &setLayout;
        check(f.vkAllocateDescriptorSets(device, &descriptor_allocation, &menuRippleSet),
              "Menu ripple descriptor set");
    } catch (...) {
        destroy_menu_ripple_pipeline();
        throw;
    }
}

void ensure_menu_ripple_source() {
    if (menuRippleSource.view && menu_ripple_rw == rw && menu_ripple_rh == rh)
        return;
    settle();
    if (menuRippleSource.view)
        f.vkDestroyImageView(device, menuRippleSource.view, nullptr);
    if (menuRippleSource.image)
        f.vkDestroyImage(device, menuRippleSource.image, nullptr);
    if (menuRippleSource.memory)
        release_memory(device, menuRippleSource.memory, nullptr);
    menuRippleSource = {};
    menu_ripple_rw = menu_ripple_rh = 0;
    const auto source_sampler = sampler(3U | (3U << 4) | (3U << 8));
    image(menuRippleSource.image, menuRippleSource.memory, menuRippleSource.view, rw, rh,
          rgba ? VK_FORMAT_R8G8B8A8_UNORM : VK_FORMAT_R5G6B5_UNORM_PACK16,
          VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    menu_ripple_rw = rw;
    menu_ripple_rh = rh;
    VkDescriptorImageInfo info{source_sampler, menuRippleSource.view,
                               VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
    VkWriteDescriptorSet write{};
    write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write.dstSet = menuRippleSet;
    write.descriptorCount = 1;
    write.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    write.pImageInfo = &info;
    f.vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
}

public:
void prepare_menu_ripple() {
    if (!device)
        init();
    init_menu_ripple();
    if (rw && rh)
        ensure_menu_ripple_source();
}
void apply_menu_ripple(const MenuRipplePass &pass) {
    for (float value : {pass.center_u, pass.center_v, pass.scale_u, pass.scale_v, pass.inner,
                        pass.outer, pass.amplitude, pass.wavelength, pass.phase, pass.clip_u0,
                        pass.clip_v0, pass.clip_u1, pass.clip_v1})
        if (!std::isfinite(value))
            return;
    if (pass.scale_u <= 0.f || pass.scale_v <= 0.f || pass.outer <= 0.f ||
        pass.outer <= pass.inner || pass.wavelength <= 0.f)
        return;
    if (!device)
        init();
    select_world_target(false, false);
    prepare_menu_ripple();
    if (!colorImage.image || !rw || !rh)
        return;
    // Clamp in floating point before integer conversion, including extreme finite inputs.
    double left = (double(pass.center_u) - double(pass.outer) * pass.scale_u) * rw - 2;
    double top = (double(pass.center_v) - double(pass.outer) * pass.scale_v) * rh - 2;
    double right = (double(pass.center_u) + double(pass.outer) * pass.scale_u) * rw + 2;
    double bottom = (double(pass.center_v) + double(pass.outer) * pass.scale_v) * rh + 2;
    if (pass.has_clip) {
        left = std::max(left, double(pass.clip_u0) * rw);
        top = std::max(top, double(pass.clip_v0) * rh);
        right = std::min(right, double(pass.clip_u1) * rw);
        bottom = std::min(bottom, double(pass.clip_v1) * rh);
    }
    const auto x0 = int32_t(std::floor(std::clamp(left, 0.0, double(rw))));
    const auto y0 = int32_t(std::floor(std::clamp(top, 0.0, double(rh))));
    const auto x1 = int32_t(std::ceil(std::clamp(right, 0.0, double(rw))));
    const auto y1 = int32_t(std::ceil(std::clamp(bottom, 0.0, double(rh))));
    if (x1 <= x0 || y1 <= y0)
        return;
    VkRect2D scissor{{x0, y0}, {unsigned(x1 - x0), unsigned(y1 - y0)}};
    settle();
    check(f.vkResetCommandPool(device, commandPool, 0), "reset menu ripple pool");
    VkCommandBufferBeginInfo begin{};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    check(f.vkBeginCommandBuffer(cmd, &begin), "begin menu ripple");
    if (in_attachment_layout) {
        barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        barrier(depthImage.image, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
                VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
                VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
                    VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,
                VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT |
                    VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,
                VK_IMAGE_ASPECT_DEPTH_BIT);
    } else
        barrier(depthImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_ACCESS_TRANSFER_READ_BIT,
                VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
                    VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT,
                VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT |
                    VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,
                VK_IMAGE_ASPECT_DEPTH_BIT);
    // Discard the scratch image's previous contents before the complete copy.
    // Never sample the same color image that this pass is writing.
    barrier(menuRippleSource.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    blit_img(colorImage.image, rw, rh, menuRippleSource.image, rw, rh, VK_IMAGE_ASPECT_COLOR_BIT,
             VK_FILTER_NEAREST);
    barrier(menuRippleSource.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
            VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    barrier(colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
            VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_ACCESS_TRANSFER_READ_BIT,
            VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            VK_IMAGE_ASPECT_COLOR_BIT);
    VkRenderPassBeginInfo render_pass_begin{};
    render_pass_begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    render_pass_begin.renderPass = renderPass;
    render_pass_begin.framebuffer = framebuffer;
    render_pass_begin.renderArea = {{0, 0}, {rw, rh}};
    f.vkCmdBeginRenderPass(cmd, &render_pass_begin, VK_SUBPASS_CONTENTS_INLINE);
    VkViewport viewport{0, 0, float(rw), float(rh), 0, 1};

    f.vkCmdSetViewport(cmd, 0, 1, &viewport);
    f.vkCmdSetScissor(cmd, 0, 1, &scissor);
    f.vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, menuRipplePipeline);
    f.vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, menuRippleLayout, 0, 1,
                              &menuRippleSet, 0, nullptr);
    const float constants[16]{pass.center_u,    pass.center_v,
                              pass.scale_u,     pass.scale_v,
                              pass.inner,       pass.outer,
                              pass.amplitude,   pass.wavelength,
                              pass.phase,       pass.has_clip ? 1.f : 0.f,
                              0.5f / float(rw), 0.5f / float(rh),
                              pass.clip_u0,     pass.clip_v0,
                              pass.clip_u1,     pass.clip_v1};
    static_assert(sizeof(constants) == 64);
    f.vkCmdPushConstants(cmd, menuRippleLayout, VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(constants),
                         constants);
    f.vkCmdDraw(cmd, 3, 1, 0, 0);
    f.vkCmdEndRenderPass(cmd);
    // Color remains resident; the following normal render pass loads these
    // writes. Explicitly order the two passes, with depth preserved.
    barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
            VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
            VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_IMAGE_ASPECT_COLOR_BIT);

    check(f.vkEndCommandBuffer(cmd), "end menu ripple");
    check(f.vkResetFences(device, 1, &fence), "reset menu ripple fence");
    VkSubmitInfo submit{};
    submit.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submit.commandBufferCount = 1;
    submit.pCommandBuffers = &cmd;
    check(f.vkQueueSubmit(queue, 1, &submit, fence), "submit menu ripple");
    scene_pending = true;
    in_attachment_layout = true;
    ++menu_ripple_passes;
}

private:
