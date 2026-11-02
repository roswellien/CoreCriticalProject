// Optional diagnostic attachments. Guest images, descriptor pools and projection
// constants remain authoritative and are never replaced with these resources.
struct alignas(16) TemporalUniform {
    std::array<float, 12> camera{}, world{}, previous_view{};
    std::array<float, 4> projection{}, previous_projection{}, dimensions{}, depth{}, previous{},
        jitter{};
    std::array<unsigned, 4> flags{};
};
static_assert(sizeof(TemporalUniform) == 256);
struct TemporalSlot {
    std::array<Image, 4> images{};
    VkFramebuffer framebuffer{};
    unsigned width{}, height{}, target{}, phase{};
    std::uint64_t frame{}, published_frame{}, bytes{};
    bool initialized{}, poisoned{}, published{}, history_valid{};
    std::array<float, 2> jitter{}, previous_jitter{};
    std::shared_ptr<const mw34::temporal::Snapshot> camera;
    using SourceKey =
        std::tuple<unsigned, unsigned, unsigned, unsigned, unsigned, std::array<unsigned, 3>>;
    std::map<SourceKey, std::shared_ptr<const mw34::temporal::StaticSource>> sources;
};
std::map<mw34::temporal::View, TemporalSlot> temporal_slots;
VkRenderPass temporal_pass{};
VkDescriptorSetLayout temporal_uniform_layout{};
VkPipelineLayout temporal_layout{};
VkDescriptorPool temporal_pool{};
VkShaderModule temporal_vertex{}, temporal_fragment{};
std::map<std::uint64_t, VkPipeline> temporal_pipelines;
Buffer temporal_uniforms, temporal_vertices, temporal_readback;
VkDeviceSize temporal_stride{};
std::uint64_t temporal_allocated_bytes{}, temporal_submissions{};
static constexpr std::uint64_t temporal_byte_limit = 512ULL * 1024 * 1024;

void temporal_destroy_image(Image &resource) {
    if (resource.view)
        f.vkDestroyImageView(device, resource.view, nullptr);
    if (resource.image)
        f.vkDestroyImage(device, resource.image, nullptr);
    if (resource.memory)
        f.vkFreeMemory(device, resource.memory, nullptr);
    resource = {};
}
void temporal_destroy_slot(TemporalSlot &slot) {
    if (slot.framebuffer)
        f.vkDestroyFramebuffer(device, slot.framebuffer, nullptr);
    for (auto &image : slot.images)
        temporal_destroy_image(image);
    temporal_allocated_bytes -= slot.bytes;
    slot = {};
}
void temporal_drop_slots() {
    for (auto &[view, slot] : temporal_slots)
        temporal_destroy_slot(slot);
    temporal_slots.clear();
    temporal_allocated_bytes = 0;
}
void temporal_shutdown() {
    temporal_drop_slots();
    for (auto &[key, pipeline] : temporal_pipelines)
        f.vkDestroyPipeline(device, pipeline, nullptr);
    temporal_pipelines.clear();
    if (temporal_pool)
        f.vkDestroyDescriptorPool(device, temporal_pool, nullptr);
    if (temporal_layout)
        f.vkDestroyPipelineLayout(device, temporal_layout, nullptr);
    if (temporal_uniform_layout)
        f.vkDestroyDescriptorSetLayout(device, temporal_uniform_layout, nullptr);
    if (temporal_pass)
        f.vkDestroyRenderPass(device, temporal_pass, nullptr);
    for (auto shader : {temporal_vertex, temporal_fragment})
        if (shader)
            f.vkDestroyShaderModule(device, shader, nullptr);
    for (auto *buffer : {&temporal_uniforms, &temporal_vertices, &temporal_readback}) {
        if (buffer->buffer)
            f.vkDestroyBuffer(device, buffer->buffer, nullptr);
        if (buffer->memory)
            f.vkFreeMemory(device, buffer->memory, nullptr);
        *buffer = {};
    }
    temporal_pool = {};
    temporal_layout = {};
    temporal_uniform_layout = {};
    temporal_pass = {};
    temporal_vertex = {};
    temporal_fragment = {};
}
void temporal_init() {
    if (temporal_pass)
        return;
    VkPhysicalDeviceProperties properties{};
    f.vkGetPhysicalDeviceProperties(gpu, &properties);
    temporal_stride =
        (sizeof(TemporalUniform) + properties.limits.minUniformBufferOffsetAlignment - 1) /
        properties.limits.minUniformBufferOffsetAlignment *
        properties.limits.minUniformBufferOffsetAlignment;
    if (sizeof(TemporalUniform) > properties.limits.maxUniformBufferRange)
        throw std::runtime_error("Temporal uniform exceeds device limits");
    const VkFormat formats[]{VK_FORMAT_R32_SFLOAT, VK_FORMAT_R32G32_SFLOAT, VK_FORMAT_R8_UNORM,
                             VK_FORMAT_D32_SFLOAT};
    std::array<VkAttachmentDescription, 4> attachments{};
    for (unsigned i = 0; i < 4; ++i) {
        VkFormatProperties format{};
        f.vkGetPhysicalDeviceFormatProperties(gpu, formats[i], &format);
        const auto required =
            i == 3 ? VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT |
                         VK_FORMAT_FEATURE_TRANSFER_DST_BIT
                   : VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT | VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT |
                         VK_FORMAT_FEATURE_TRANSFER_SRC_BIT | VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
        if ((format.optimalTilingFeatures & required) != required)
            throw std::runtime_error(
                "GPU lacks required temporal attachment/sample/transfer format");
        auto &attachment = attachments[i];
        attachment.format = formats[i];
        attachment.samples = VK_SAMPLE_COUNT_1_BIT;
        attachment.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        attachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        attachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        attachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        attachment.initialLayout = attachment.finalLayout =
            i == 3 ? VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
                   : VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    }
    const VkAttachmentReference colors[]{{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},
                                         {1, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},
                                         {2, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL}};
    const VkAttachmentReference depth{3, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL};
    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 3;
    subpass.pColorAttachments = colors;
    subpass.pDepthStencilAttachment = &depth;
    VkRenderPassCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    info.attachmentCount = 4;
    info.pAttachments = attachments.data();
    info.subpassCount = 1;
    info.pSubpasses = &subpass;
    check(f.vkCreateRenderPass(device, &info, nullptr, &temporal_pass), "temporal render pass");
    VkDescriptorSetLayoutBinding uniform{0, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC, 1,
                                         VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
                                         nullptr};
    VkDescriptorSetLayoutCreateInfo layout{};
    layout.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    layout.bindingCount = 1;
    layout.pBindings = &uniform;
    check(f.vkCreateDescriptorSetLayout(device, &layout, nullptr, &temporal_uniform_layout),
          "temporal uniform layout");
    const VkDescriptorSetLayout sets[]{setLayout, temporal_uniform_layout};
    VkPushConstantRange push{VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0,
                             sizeof(Push)};
    VkPipelineLayoutCreateInfo pipeline_layout{};
    pipeline_layout.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pipeline_layout.setLayoutCount = 2;
    pipeline_layout.pSetLayouts = sets;
    pipeline_layout.pushConstantRangeCount = 1;
    pipeline_layout.pPushConstantRanges = &push;
    check(f.vkCreatePipelineLayout(device, &pipeline_layout, nullptr, &temporal_layout),
          "temporal pipeline layout");
    auto shader = [&](auto &words, VkShaderModule &result) {
        VkShaderModuleCreateInfo module{};
        module.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        module.codeSize = sizeof(words);
        module.pCode = words;
        check(f.vkCreateShaderModule(device, &module, nullptr, &result), "temporal shader");
    };
    shader(temporal_inputs_vert_spv, temporal_vertex);
    shader(temporal_inputs_frag_spv, temporal_fragment);
}
TemporalSlot &temporal_slot(const mw34::temporal::Snapshot &camera) {
    auto found = temporal_slots.find(camera.view);
    if (found == temporal_slots.end()) {
        if (temporal_slots.size() == mw34::temporal::History::capacity)
            throw std::runtime_error("Temporal view capacity exceeded");
        found = temporal_slots.try_emplace(camera.view).first;
    }
    auto &slot = found->second;
    const unsigned w = camera.sizes[4], h = camera.sizes[5];
    if (!slot.framebuffer) {
        VkPhysicalDeviceProperties properties{};
        f.vkGetPhysicalDeviceProperties(gpu, &properties);
        const auto bytes = std::uint64_t(w) * h * 17;
        if (!w || !h || w > properties.limits.maxImageDimension2D ||
            h > properties.limits.maxImageDimension2D ||
            bytes > temporal_byte_limit - temporal_allocated_bytes)
            throw std::runtime_error("Temporal target capacity exceeded");
        slot.width = w;
        slot.height = h;
        const VkFormat formats[]{VK_FORMAT_R32_SFLOAT, VK_FORMAT_R32G32_SFLOAT, VK_FORMAT_R8_UNORM,
                                 VK_FORMAT_D32_SFLOAT};
        for (unsigned i = 0; i < 4; ++i) {
            auto &target = slot.images[i];
            image(target.image, target.memory, target.view, w, h, formats[i],
                  i == 3 ? VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT |
                               VK_IMAGE_USAGE_TRANSFER_DST_BIT
                         : VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT |
                               VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                  i == 3 ? VK_IMAGE_ASPECT_DEPTH_BIT : VK_IMAGE_ASPECT_COLOR_BIT);
        }
        VkImageView views[]{slot.images[0].view, slot.images[1].view, slot.images[2].view,
                            slot.images[3].view};
        VkFramebufferCreateInfo framebuffer{};
        framebuffer.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        framebuffer.renderPass = temporal_pass;
        framebuffer.attachmentCount = 4;
        framebuffer.pAttachments = views;
        framebuffer.width = w;
        framebuffer.height = h;
        framebuffer.layers = 1;
        check(f.vkCreateFramebuffer(device, &framebuffer, nullptr, &slot.framebuffer),
              "temporal framebuffer");
        slot.bytes = bytes;
        temporal_allocated_bytes += bytes;
    }
    if (slot.width != w || slot.height != h)
        throw std::runtime_error("Temporal target survived incompatible dimensions");
    return slot;
}
VkPipeline temporal_pipeline(const PipelineKey &key, bool model, bool world) {
    const auto identity = key.packed() | (model ? 1ULL << 57 : 0) | (world ? 1ULL << 58 : 0);
    if (auto found = temporal_pipelines.find(identity); found != temporal_pipelines.end())
        return found->second;
    std::array<VkPipelineShaderStageCreateInfo, 2> shaders{};
    for (unsigned i = 0; i < 2; ++i) {
        shaders[i].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        shaders[i].stage = i ? VK_SHADER_STAGE_FRAGMENT_BIT : VK_SHADER_STAGE_VERTEX_BIT;
        shaders[i].module = i ? temporal_fragment : temporal_vertex;
        shaders[i].pName = "main";
    }
    const VkVertexInputBindingDescription bindings[]{{0, 32, VK_VERTEX_INPUT_RATE_VERTEX},
                                                     {1, 32, VK_VERTEX_INPUT_RATE_VERTEX}};
    const VkVertexInputAttributeDescription attributes[]{
        {0, 0, VK_FORMAT_R32G32B32A32_SFLOAT, 0},
        {1, world ? 1U : 0U, VK_FORMAT_R32_UINT, 16},
        {2, world ? 1U : 0U, VK_FORMAT_R32_UINT, 20},
        {3, world ? 1U : 0U, VK_FORMAT_R32G32_SFLOAT, 24}};
    VkPipelineVertexInputStateCreateInfo vertex{};
    vertex.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vertex.vertexBindingDescriptionCount = world ? 2 : 1;
    vertex.pVertexBindingDescriptions = bindings;
    vertex.vertexAttributeDescriptionCount = 4;
    vertex.pVertexAttributeDescriptions = attributes;
    VkPipelineInputAssemblyStateCreateInfo assembly{};
    assembly.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    assembly.topology =
        key.points ? VK_PRIMITIVE_TOPOLOGY_POINT_LIST : VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkPipelineViewportStateCreateInfo viewport{};
    viewport.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    viewport.viewportCount = viewport.scissorCount = 1;
    VkPipelineRasterizationStateCreateInfo raster{};
    raster.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    raster.polygonMode = VK_POLYGON_MODE_FILL;
    raster.lineWidth = 1;
    raster.cullMode = key.cull == 1 ? VK_CULL_MODE_NONE : VK_CULL_MODE_BACK_BIT;
    raster.frontFace = key.cull == 3 ? VK_FRONT_FACE_CLOCKWISE : VK_FRONT_FACE_COUNTER_CLOCKWISE;
    VkPipelineMultisampleStateCreateInfo samples{};
    samples.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    samples.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    VkPipelineDepthStencilStateCreateInfo depth{};
    depth.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    depth.depthTestEnable = key.zenable;
    depth.depthWriteEnable = key.zenable && key.zwrite;
    depth.depthCompareOp = VkCompareOp(key.zfunc - 1);
    std::array<VkPipelineColorBlendAttachmentState, 3> colors{};
    for (auto &color : colors)
        color.colorWriteMask = 15;
    VkPipelineColorBlendStateCreateInfo blend{};
    blend.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    blend.attachmentCount = 3;
    blend.pAttachments = colors.data();
    const VkDynamicState states[]{VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dynamic{};
    dynamic.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dynamic.dynamicStateCount = 2;
    dynamic.pDynamicStates = states;
    VkGraphicsPipelineCreateInfo pipeline{};
    pipeline.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    pipeline.stageCount = 2;
    pipeline.pStages = shaders.data();
    pipeline.pVertexInputState = &vertex;
    pipeline.pInputAssemblyState = &assembly;
    pipeline.pViewportState = &viewport;
    pipeline.pRasterizationState = &raster;
    pipeline.pMultisampleState = &samples;
    pipeline.pDepthStencilState = &depth;
    pipeline.pColorBlendState = &blend;
    pipeline.pDynamicState = &dynamic;
    pipeline.layout = temporal_layout;
    pipeline.renderPass = temporal_pass;
    VkPipeline result{};
    check(f.vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &pipeline, nullptr, &result),
          "temporal graphics pipeline");
    temporal_pipelines.emplace(identity, result);
    return result;
}
void temporal_begin_commands() {
    settle();
    check(f.vkResetCommandPool(device, commandPool, 0), "reset temporal command pool");
    VkCommandBufferBeginInfo begin{};
    begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    check(f.vkBeginCommandBuffer(cmd, &begin), "begin temporal commands");
}
void temporal_submit() {
    check(f.vkEndCommandBuffer(cmd), "end temporal commands");
    check(f.vkResetFences(device, 1, &fence), "reset temporal fence");
    VkSubmitInfo submit{};
    submit.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submit.commandBufferCount = 1;
    submit.pCommandBuffers = &cmd;
    check(f.vkQueueSubmit(queue, 1, &submit, fence), "submit temporal commands");
    scene_pending = true;
    ++temporal_submissions;
}
// DirectDraw depth fills carry their exact target, real frame and ordered
// rectangle. They replace visibility, not the retained color surface metadata.
bool temporal_ordered_depth_clear(const Scene &scene) const {
    if (!scene.guest_surface_write || !scene.has_depth || scene.hud || scene.frontend_canvas ||
        !scene.temporal_frame || !scene.temporal_target || !scene.draws.empty() ||
        scene.clears.empty() || scene.order.size() != scene.clears.size())
        return false;
    for (std::size_t i = 0; i < scene.clears.size(); ++i) {
        const auto &clear = scene.clears[i];
        if (!scene.order[i].clear || scene.order[i].index != i || clear.flags != 2 ||
            !std::isfinite(clear.z) || clear.z < 0 || clear.z > 1 || clear.rects.empty())
            return false;
        for (const auto &r : clear.rects)
            if (r.offset.x < 0 || r.offset.y < 0 ||
                std::uint64_t(r.offset.x) + r.extent.width > scene.width ||
                std::uint64_t(r.offset.y) + r.extent.height > scene.height)
                return false;
    }
    for (const auto &[view, slot] : temporal_slots) {
        const auto pending = camera_history.pending_view(view);
        if (slot.frame == scene.temporal_frame && slot.target == scene.temporal_target &&
            pending && pending->frame == scene.temporal_frame &&
            pending->target == scene.temporal_target && pending->sizes[0] == scene.width &&
            pending->sizes[1] == scene.height)
            return true;
    }
    return false;
}
const std::shared_ptr<const ModelInstance> &temporal_geometry(const Draw &draw) const {
    return draw.temporal_model ? draw.temporal_model : draw.model;
}
void temporal_append(const Scene &scene) {
    if (!mw34::temporal::enabled() || !scene.temporal_frame || scene.hud || scene.frontend_canvas)
        return;
    std::map<mw34::temporal::View, std::shared_ptr<const mw34::temporal::Snapshot>> views;
    for (const auto &draw : scene.draws) {
        const auto &model = temporal_geometry(draw);
        if (draw.camera_view && model && model->world) {
            auto pending = camera_history.pending_view(draw.camera_view->view);
            if (pending && pending->frame == scene.temporal_frame &&
                pending->target == scene.temporal_target)
                views.emplace(pending->view, pending);
        }
    }
    for (auto &[view, slot] : temporal_slots)
        if (slot.frame == scene.temporal_frame && slot.target == scene.temporal_target &&
            slot.camera)
            views.try_emplace(view, slot.camera);
    if (views.empty())
        return;
    settle();
    temporal_init();
    const auto count = scene.draws.size();
    if (count > 0xffffffffULL / temporal_stride)
        throw std::runtime_error("Temporal submission uniform capacity exceeded");
    ensure(temporal_uniforms, std::max<VkDeviceSize>(count * temporal_stride, temporal_stride),
           VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT);
    ensure(temporal_vertices, std::max<VkDeviceSize>(scene.vertices.size(), 32),
           VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
    if (!scene.vertices.empty())
        std::memcpy(temporal_vertices.mapped, scene.vertices.data(), scene.vertices.size());
    if (temporal_pool)
        f.vkDestroyDescriptorPool(device, temporal_pool, nullptr);
    const VkDescriptorPoolSize pool_sizes[]{
        {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, unsigned(count * 2 + 2)},
        {VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC, 1}};
    VkDescriptorPoolCreateInfo pool{};
    pool.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    pool.maxSets = unsigned(count + 1);
    pool.poolSizeCount = 2;
    pool.pPoolSizes = pool_sizes;
    check(f.vkCreateDescriptorPool(device, &pool, nullptr, &temporal_pool),
          "temporal descriptor pool");
    VkDescriptorSetAllocateInfo allocation{};
    allocation.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    allocation.descriptorPool = temporal_pool;
    allocation.descriptorSetCount = 1;
    allocation.pSetLayouts = &temporal_uniform_layout;
    VkDescriptorSet uniform_set{};
    check(f.vkAllocateDescriptorSets(device, &allocation, &uniform_set), "temporal uniform set");
    VkDescriptorBufferInfo buffer{temporal_uniforms.buffer, 0, sizeof(TemporalUniform)};
    VkWriteDescriptorSet write{};
    write.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    write.dstSet = uniform_set;
    write.dstBinding = 0;
    write.descriptorCount = 1;
    write.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC;
    write.pBufferInfo = &buffer;
    f.vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
    std::vector<VkDescriptorSet> texture_sets(count);
    for (std::size_t i = 0; i < count; ++i) {
        const auto &draw = scene.draws[i];
        const Tex *texture =
            draw.texture < 0 ? &white : &textures.at(scene.textures.at(draw.texture).key);
        allocation.pSetLayouts = &setLayout;
        check(f.vkAllocateDescriptorSets(device, &allocation, &texture_sets[i]),
              "temporal texture set");
        VkDescriptorImageInfo image{sampler(draw.sampler), texture->view,
                                    VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
        write.dstSet = texture_sets[i];
        write.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        write.pBufferInfo = nullptr;
        write.pImageInfo = &image;
        f.vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
    }
    for (const auto &[view, camera] : views) {
        auto &slot = temporal_slot(*camera);
        const bool fresh = slot.frame != scene.temporal_frame;
        const auto previous = camera_history.previous_for(*camera);
        if (fresh) {
            slot.history_valid = previous && slot.published_frame + 1 == scene.temporal_frame;
            slot.phase = slot.history_valid ? slot.phase + 1 : 0;
            slot.previous_jitter = slot.jitter;
            slot.jitter = mw34::temporal::jitter_enabled()
                              ? mw34::temporal::jitter(slot.phase, camera->sizes[2], slot.width)
                              : std::array<float, 2>{};
            slot.frame = scene.temporal_frame;
            slot.target = scene.temporal_target;
            slot.sources.clear();
            slot.poisoned = false;
            slot.published = false;
        }
        slot.camera = camera;
        if (scene.guest_surface_write && !temporal_ordered_depth_clear(scene) &&
            (camera_history.pending() || !(leading_full_clear(scene) & 1)))
            slot.poisoned = true;
        // Each view has distinct uniforms. Finish earlier view use before rewriting them.
        settle();
        for (std::size_t i = 0; i < count; ++i) {
            const auto &draw = scene.draws[i];
            const auto &model = temporal_geometry(draw);
            TemporalUniform uniform{};
            uniform.projection = {camera->projection[1], camera->projection[2],
                                  camera->projection[3], camera->projection[4]};
            uniform.dimensions = {float(scene.width), float(scene.height), float(slot.width),
                                  float(slot.height)};
            uniform.depth = {camera->projection[0], camera->projection[5], camera->far_clip, 0};
            uniform.jitter = {slot.jitter[0], slot.jitter[1], 0, 0};
            uniform.flags[2] = draw.key.blend && draw.key.src == 5 &&
                               draw.key.dst == 6 && !draw.key.zwrite;
            if (model) {
                uniform.camera = model->camera;
                uniform.flags[0] = model->world ? 1 : 2;
                const auto &projection = model->projection;
                uniform.projection = {projection[1], projection[2], projection[3], projection[4]};
                uniform.depth[0] = projection[0];
                uniform.depth[1] = projection[5];
            }
            if (previous) {
                uniform.previous_view =
                    mw34::temporal::inverse_affine(mw34::temporal::camera_world(*previous));
                uniform.previous_projection = {previous->projection[1], previous->projection[2],
                                               previous->projection[3], previous->projection[4]};
                uniform.previous = {previous->projection[0], float(previous->sizes[0]),
                                    float(previous->sizes[1]), previous->far_clip};
                uniform.depth[3] = previous->projection[5];
            }
            if (draw.temporal_source && draw.camera_view && draw.camera_view->view == view &&
                model && model->world) {
                const auto &source = *draw.temporal_source;
                const TemporalSlot::SourceKey key{source.cell_owner, source.cell,    source.record,
                                                  source.node,       source.polygon, source.offset};
                const auto found = slot.sources.find(key);
                if (found != slot.sources.end() && !source.unchanged(*found->second))
                    slot.poisoned = true;
                slot.sources.insert_or_assign(key, draw.temporal_source);
                uniform.world = source.world;
                uniform.flags[1] = previous && slot.history_valid && source.previous_static &&
                                   source.frame == slot.frame &&
                                   source.load_epoch == camera->load_epoch && !draw.key.blend &&
                                   draw.key.zenable && draw.key.zwrite;

            }
            if (model && !model->world && (draw.push.mode[0] & 32))
                slot.poisoned = true;
            std::memcpy(static_cast<unsigned char *>(temporal_uniforms.mapped) +
                            i * temporal_stride,
                        &uniform, sizeof(uniform));
        }
        temporal_begin_commands();
        for (unsigned i = 0; i < 4; ++i) {
            const VkImageAspectFlags aspect = i == 3 ? VK_IMAGE_ASPECT_DEPTH_BIT : VK_IMAGE_ASPECT_COLOR_BIT;
            const auto attachment = i == 3 ? VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
                                           : VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
            const auto from = slot.initialized
                                  ? (i == 3 ? attachment : VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL)
                                  : VK_IMAGE_LAYOUT_UNDEFINED;
            if (fresh) {
                barrier(slot.images[i].image, from, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                        slot.initialized ? VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT
                                         : 0,
                        VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                        VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
                const VkImageSubresourceRange range{aspect, 0, 1, 0, 1};
                if (i == 3) {
                    const VkClearDepthStencilValue clear{0, 0};
                    f.vkCmdClearDepthStencilImage(cmd, slot.images[i].image,
                                                  VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &clear, 1,
                                                  &range);
                } else {
                    const VkClearColorValue clear{};
                    f.vkCmdClearColorImage(cmd, slot.images[i].image,
                                           VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &clear, 1, &range);
                }
                barrier(slot.images[i].image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, attachment,
                        VK_ACCESS_TRANSFER_WRITE_BIT,
                        i == 3 ? VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
                                     VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT
                               : VK_ACCESS_COLOR_ATTACHMENT_READ_BIT |
                                     VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                        VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, aspect);
            } else {
                barrier(slot.images[i].image, from, attachment,
                        VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT,
                        i == 3 ? VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
                                     VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT
                               : VK_ACCESS_COLOR_ATTACHMENT_READ_BIT |
                                     VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                        VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                        aspect);
            }
        }
        slot.initialized = true;
        VkRenderPassBeginInfo begin{};
        begin.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
        begin.renderPass = temporal_pass;
        begin.framebuffer = slot.framebuffer;
        begin.renderArea.extent = {slot.width, slot.height};
        f.vkCmdBeginRenderPass(cmd, &begin, VK_SUBPASS_CONTENTS_INLINE);
        VkViewport viewport{0, 0, float(slot.width), float(slot.height), 0, 1};
        f.vkCmdSetViewport(cmd, 0, 1, &viewport);
        for (const auto &command : scene.order) {
            if (command.clear) {
                const auto &clear = scene.clears.at(command.index);
                if (!(clear.flags & 3))
                    continue;
                std::vector<VkClearRect> rectangles;
                for (const auto &r : clear.rects) {
                    const int x0 = int(std::lround(r.offset.x * double(slot.width) / scene.width)),
                              y0 =
                                  int(std::lround(r.offset.y * double(slot.height) / scene.height));
                    const int x1 = int(std::lround((r.offset.x + int(r.extent.width)) *
                                                   double(slot.width) / scene.width)),
                              y1 = int(std::lround((r.offset.y + int(r.extent.height)) *
                                                   double(slot.height) / scene.height));
                    if (x0 < 0 || y0 < 0 || x1 > int(slot.width) || y1 > int(slot.height) ||
                        x1 < x0 || y1 < y0)
                        throw std::runtime_error("Temporal clear outside target");
                    if (x1 > x0 && y1 > y0)
                        rectangles.push_back(
                            {{{x0, y0}, {unsigned(x1 - x0), unsigned(y1 - y0)}}, 0, 1});
                }
                std::array<VkClearAttachment, 4> attachments{};
                unsigned n = 0;
                if (clear.flags & 1)
                    for (unsigned i = 0; i < 3; ++i) {
                        attachments[n].aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                        attachments[n].colorAttachment = i;
                        ++n;
                    }
                // A depth-only clear does not replace the retained color surface.
                // Preserve its source metadata until an ordered draw covers it.
                if (clear.flags & 2) {
                    attachments[n].aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
                    attachments[n].clearValue.depthStencil = {clear.z, 0};
                    ++n;
                }
                if (!rectangles.empty())
                    f.vkCmdClearAttachments(cmd, n, attachments.data(), unsigned(rectangles.size()),
                                            rectangles.data());
                continue;
            }
            const auto index = command.index;
            const auto &draw = scene.draws.at(index);
            const auto &model = temporal_geometry(draw);
            if (!draw.count || !draw.scissor.extent.width || !draw.scissor.extent.height ||
                draw.temporal_output_only)
                continue;
            f.vkCmdBindPipeline(
                cmd, VK_PIPELINE_BIND_POINT_GRAPHICS,
                temporal_pipeline(draw.key, bool(model), model && model->world));
            const std::uint32_t offset = std::uint32_t(index * temporal_stride);
            const VkDescriptorSet sets[]{texture_sets[index], uniform_set};
            f.vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, temporal_layout, 0, 2,
                                      sets, 1, &offset);
            const int x0 = std::clamp(
                int(std::lround(draw.scissor.offset.x * double(slot.width) / scene.width)), 0,
                int(slot.width));
            const int y0 = std::clamp(
                int(std::lround(draw.scissor.offset.y * double(slot.height) / scene.height)), 0,
                int(slot.height));
            const int x1 = std::clamp(
                int(std::lround((draw.scissor.offset.x + int(draw.scissor.extent.width)) *
                                double(slot.width) / scene.width)),
                x0, int(slot.width));
            const int y1 = std::clamp(
                int(std::lround((draw.scissor.offset.y + int(draw.scissor.extent.height)) *
                                double(slot.height) / scene.height)),
                y0, int(slot.height));
            const VkRect2D scissor{{x0, y0}, {unsigned(x1 - x0), unsigned(y1 - y0)}};
            f.vkCmdSetScissor(cmd, 0, 1, &scissor);
            Push push = draw.push;
            if (model) {
                const auto &geometry = model_buffers.at(model->geometry->key);
                const VkBuffer buffers[]{geometry.local.buffer, model->world
                                                                    ? temporal_vertices.buffer
                                                                    : geometry.local.buffer};
                const VkDeviceSize offsets[]{0,
                                             model->world ? VkDeviceSize(draw.first) * 32 : 0};
                f.vkCmdBindVertexBuffers(cmd, 0, model->world ? 2 : 1, buffers, offsets);
            } else {
                const VkDeviceSize offset = 0;
                f.vkCmdBindVertexBuffers(cmd, 0, 1, &temporal_vertices.buffer, &offset);
            }
            f.vkCmdPushConstants(cmd, temporal_layout,
                                 VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0,
                                 sizeof(push), &push);
            f.vkCmdDraw(cmd, draw.count, 1, model ? 0 : draw.first, 0);
        }
        f.vkCmdEndRenderPass(cmd);
        for (unsigned i = 0; i < 3; ++i)
            barrier(slot.images[i].image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                    VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                    VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                    VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT | VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                    VK_IMAGE_ASPECT_COLOR_BIT);
        temporal_submit();
    }
}
void temporal_complete(std::uint64_t frame) {
    for (auto it = temporal_slots.begin(); it != temporal_slots.end();) {
        if (it->second.frame != frame) {
            settle();
            temporal_destroy_slot(it->second);
            it = temporal_slots.erase(it);
        } else
            ++it;
    }
    for (auto &[view, slot] : temporal_slots) {
        const auto pair = camera_history.pairs().find(view);
        slot.published = slot.frame == frame && !slot.poisoned &&
                         pair != camera_history.pairs().end() && pair->second.current;
        slot.history_valid = slot.published && slot.history_valid && pair->second.valid();
        if (slot.published)
            slot.published_frame = frame;
    }
}

public:
std::uint64_t temporal_bytes() const { return temporal_allocated_bytes; }
struct TemporalPixels {
    unsigned width{}, height{};
    std::uint64_t frame{};
    bool history_valid{};
    std::array<float, 2> jitter{}, previous_jitter{};
    std::vector<float> depth, motion;
    std::vector<unsigned char> validity;
};
TemporalPixels capture_temporal(const mw34::temporal::View &view) {
    HostFpEnvironment fp;
    TemporalPixels result{};
    const auto found = temporal_slots.find(view);
    if (found == temporal_slots.end() || !found->second.published ||
        !camera_history.pairs().contains(view))
        return result;
    auto &slot = found->second;
    settle();
    const VkDeviceSize pixels = VkDeviceSize(slot.width) * slot.height;
    const VkDeviceSize offsets[]{0, pixels * 4, pixels * 12};
    ensure(temporal_readback, offsets[2] + pixels, VK_BUFFER_USAGE_TRANSFER_DST_BIT);
    temporal_begin_commands();
    for (unsigned i = 0; i < 3; ++i) {
        barrier(slot.images[i].image, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        copyOut(slot.images[i].image, temporal_readback.buffer, offsets[i],
                VK_IMAGE_ASPECT_COLOR_BIT, slot.width, slot.height);
        barrier(slot.images[i].image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_READ_BIT,
                VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT | VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                VK_IMAGE_ASPECT_COLOR_BIT);
    }
    VkBufferMemoryBarrier host_read{};host_read.sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER;
    host_read.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;host_read.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
    host_read.srcQueueFamilyIndex=host_read.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
    host_read.buffer=temporal_readback.buffer;host_read.offset=0;host_read.size=VK_WHOLE_SIZE;
    f.vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,0,nullptr,1,&host_read,0,nullptr);
    temporal_submit();
    settle();
    result.width = slot.width;
    result.height = slot.height;
    result.frame = slot.frame;
    result.history_valid = slot.history_valid;
    result.jitter = slot.jitter;
    result.previous_jitter = slot.previous_jitter;
    result.depth.resize(std::size_t(pixels));
    result.motion.resize(std::size_t(pixels) * 2);
    result.validity.resize(std::size_t(pixels));
    const auto *bytes = static_cast<const unsigned char *>(temporal_readback.mapped);
    std::memcpy(result.depth.data(), bytes, std::size_t(pixels) * 4);
    std::memcpy(result.motion.data(), bytes + offsets[1], std::size_t(pixels) * 8);
    std::memcpy(result.validity.data(), bytes + offsets[2], std::size_t(pixels));
    return result;
}

private:
