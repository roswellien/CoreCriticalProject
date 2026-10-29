// Private Renderer implementation. The alternate pair owns the inactive target;
// swapping ownership lets the existing draw/scissor/guest-transfer paths use rw/rh.
Image worldColor, worldDepth;
VkFramebuffer worldFramebuffer{};
unsigned alternate_width{}, alternate_height{};
bool reduced_world_active{};

static unsigned world_scale_percent() {
    static const unsigned percent = [] {
        const char* value = std::getenv("MW34_WORLD_SCALE_PERCENT");
        if (!value || !*value) return 100U;
        unsigned result = 0;
        for (const char* c = value; *c; ++c) {
            if (*c < '0' || *c > '9' || result > 100)
                throw std::runtime_error("MW34_WORLD_SCALE_PERCENT requires an integer from 50 to 100");
            result = result * 10 + unsigned(*c - '0');
        }
        if (result < 50 || result > 100)
            throw std::runtime_error("MW34_WORLD_SCALE_PERCENT requires an integer from 50 to 100");
        return result;
    }();
    return percent;
}
// A depth-only clear starts a reduced frame only after presentation. Mid-frame
// depth resets (for example cockpit passes) must not resample an existing HUD.
bool world_frame_boundary{true};
static unsigned leading_full_clear(const Scene& scene) {
    unsigned cleared = 0;
    for (const auto& command : scene.order) {
        if (!command.clear) break;
        const auto& clear = scene.clears.at(command.index);
        for (const auto& rect : clear.rects) {
            if (rect.offset.x == 0 && rect.offset.y == 0 &&
                rect.extent.width == scene.width && rect.extent.height == scene.height)
                cleared |= clear.flags;
        }
    }
    return scene.has_depth ? cleared : 0;
}
void destroy_world_target() {
    if (worldFramebuffer) f.vkDestroyFramebuffer(device, worldFramebuffer, nullptr);
    worldFramebuffer = {};
    for (Image* image : {&worldColor, &worldDepth}) {
        if (image->view) f.vkDestroyImageView(device, image->view, nullptr);
        if (image->image) f.vkDestroyImage(device, image->image, nullptr);
        if (image->memory) f.vkFreeMemory(device, image->memory, nullptr);
        *image = {};
    }
    reduced_world_active = false;
    world_frame_boundary = true;
}
void create_world_target() {
    const auto percent = world_scale_percent();
    if (percent == 100 || target_frontend) return;
    const auto samples = mw34::display::samples(std::getenv("MW34_REMASTER_AA"));
    if (samples.x != 1 || samples.y != 1)
        throw std::runtime_error("Reduced world resolution requires AA off or FXAA, not SSAA");
    if (!remaster_width())
        throw std::runtime_error("Reduced world resolution requires an explicit output resolution");
    alternate_width = std::max(1U, unsigned(std::uint64_t(rw) * percent / 100));
    alternate_height = std::max(1U, unsigned(std::uint64_t(rh) * percent / 100));
    const auto color_format = rgba ? VK_FORMAT_R8G8B8A8_UNORM : VK_FORMAT_R5G6B5_UNORM_PACK16;
    for (auto format : {color_format, VK_FORMAT_D32_SFLOAT}) {
        VkFormatProperties properties{};
        f.vkGetPhysicalDeviceFormatProperties(gpu, format, &properties);
        auto required = VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT;
        if (format == color_format) required |= VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT;
        if ((properties.optimalTilingFeatures & required) != required)
            throw std::runtime_error("Reduced world resolution needs color/depth blits and linear color filtering");
    }
    image(worldColor.image, worldColor.memory, worldColor.view, alternate_width, alternate_height,
          color_format, VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT |
          VK_IMAGE_USAGE_TRANSFER_DST_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    image(worldDepth.image, worldDepth.memory, worldDepth.view, alternate_width, alternate_height,
          VK_FORMAT_D32_SFLOAT, VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT |
          VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
    const VkImageView views[]{worldColor.view, worldDepth.view};
    VkFramebufferCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    info.renderPass = renderPass;
    info.attachmentCount = 2;
    info.pAttachments = views;
    info.width = alternate_width;
    info.height = alternate_height;
    info.layers = 1;
    check(f.vkCreateFramebuffer(device, &info, nullptr, &worldFramebuffer), "world framebuffer");
    std::fprintf(stderr, "World resolution: internal %ux%u, output %ux%u, guest %ux%u\n",
                 alternate_width, alternate_height, rw, rh, width, height);
}
void select_world_target(bool reduced, bool discard) {
    if (!worldColor.image || reduced == reduced_world_active) return;
    settle();
    if (!discard) {
        check(f.vkResetCommandPool(device, commandPool, 0), "reset world transfer pool");
        VkCommandBufferBeginInfo begin{};
        begin.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd, &begin), "begin world transfer");
        const auto source_color_layout = in_attachment_layout ? VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
                                                             : VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
        const auto source_depth_layout = in_attachment_layout ? VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
                                                             : VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
        barrier(colorImage.image, source_color_layout, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                in_attachment_layout ? VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT : VK_ACCESS_TRANSFER_READ_BIT,
                VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        barrier(depthImage.image, source_depth_layout, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                in_attachment_layout ? VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT : VK_ACCESS_TRANSFER_READ_BIT,
                VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        for (auto [target, aspect] : {std::pair{worldColor.image, VkImageAspectFlags(VK_IMAGE_ASPECT_COLOR_BIT)},
                                     std::pair{worldDepth.image, VkImageAspectFlags(VK_IMAGE_ASPECT_DEPTH_BIT)}})
            barrier(target, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0,
                    VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                    VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
        blit_img(colorImage.image, rw, rh, worldColor.image, alternate_width, alternate_height,
                 VK_IMAGE_ASPECT_COLOR_BIT, VK_FILTER_LINEAR);
        blit_img(depthImage.image, rw, rh, worldDepth.image, alternate_width, alternate_height,
                 VK_IMAGE_ASPECT_DEPTH_BIT, VK_FILTER_NEAREST);
        for (auto [target, aspect] : {std::pair{worldColor.image, VkImageAspectFlags(VK_IMAGE_ASPECT_COLOR_BIT)},
                                     std::pair{worldDepth.image, VkImageAspectFlags(VK_IMAGE_ASPECT_DEPTH_BIT)}})
            barrier(target, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                    VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
        check(f.vkEndCommandBuffer(cmd), "end world transfer");
        check(f.vkResetFences(device, 1, &fence), "reset world transfer fence");
        VkSubmitInfo submit{};
        submit.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
        submit.commandBufferCount = 1;
        submit.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &submit, fence), "submit world transfer");
        scene_pending = true;
    }
    std::swap(colorImage, worldColor);
    std::swap(depthImage, worldDepth);
    std::swap(framebuffer, worldFramebuffer);
    std::swap(rw, alternate_width);
    std::swap(rh, alternate_height);
    scale_x = float(rw) / float(width);
    in_attachment_layout = false;
    reduced_world_active = reduced;
    if (!reduced) ++world_promotions;
}
