// A range backdrop contains only this producer's original opaque sky/horizon
// submissions. Its alpha is zero wherever neither a sky surface nor a valid
// guest color clear supplied a background. A separate zoom pass can instead use
// the resident color that is already under its scissor.
struct RangeBackdrop {
    Image color;
    VkFramebuffer framebuffer{};
    ::platform::ProducerView view{};
    bool resident{};
};
std::array<RangeBackdrop, 2> range_backdrops{};
RangeBackdrop *recording_backdrop{};
Image range_backdrop_depth{};
unsigned range_backdrop_width{}, range_backdrop_height{};

void destroy_range_backdrops() {
    for (auto &sky : range_backdrops) {
        if (sky.framebuffer)
            f.vkDestroyFramebuffer(device, sky.framebuffer, nullptr);
        destroy_range_image(sky.color);
        sky = {};
    }
    destroy_range_image(range_backdrop_depth);
    range_backdrop_width = range_backdrop_height = 0;
}

void destroy_range_image(Image &image) {
    if (image.view)
        f.vkDestroyImageView(device, image.view, nullptr);
    if (image.image)
        f.vkDestroyImage(device, image.image, nullptr);
    if (image.memory)
        release_memory(device, image.memory, nullptr);
    image = {};
}

void ensure_range_backdrop(unsigned index, bool depth = true) {
    if (range_backdrop_width != rw || range_backdrop_height != rh) {
        destroy_range_backdrops();
        range_backdrop_width = rw;
        range_backdrop_height = rh;
    }
    auto &sky = range_backdrops.at(index);
    if (!sky.color.image)
        image(sky.color.image, sky.color.memory, sky.color.view, rw, rh, VK_FORMAT_R8G8B8A8_UNORM,
              VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT |
                  VK_IMAGE_USAGE_SAMPLED_BIT,
              VK_IMAGE_ASPECT_COLOR_BIT);
    if (!depth || sky.framebuffer)
        return;
    if (!range_backdrop_depth.image)
        image(range_backdrop_depth.image, range_backdrop_depth.memory, range_backdrop_depth.view,
              rw, rh, VK_FORMAT_D32_SFLOAT, VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT,
              VK_IMAGE_ASPECT_DEPTH_BIT);
    const VkImageView views[]{sky.color.view, range_backdrop_depth.view};
    VkFramebufferCreateInfo info{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};
    info.renderPass = renderPass;
    info.attachmentCount = 2;
    info.pAttachments = views;
    info.width = rw;
    info.height = rh;
    info.layers = 1;
    check(f.vkCreateFramebuffer(device, &info, nullptr, &sky.framebuffer),
          "range backdrop framebuffer");
}

unsigned range_backdrop(const Scene &scene, const Draw &draw) const {
    if (recording_backdrop || draw.key.blend || !uses_world_range(scene, draw))
        return 0;
    // Only the two world view purposes (MainWorld = 1, WorldZoom = 2) own a backdrop, stored at
    // index purpose - 1. Original (0) or any other value must not index the array.
    const unsigned id = unsigned(draw.producer_view.purpose);
    if (id < 1 || id > range_backdrops.size())
        return 0;
    return range_backdrops[id - 1].view.present &&
                   ::platform::same_producer_view_bits(range_backdrops[id - 1].view,
                                                       draw.producer_view)
               ? id
               : 0;
}

// Zoom can be a separate no-clear packet composited over the resident main
// picture. Only copy the authenticated scissor; preserve the incoming image
// layout and leave both guest color and depth untouched.
bool copy_zoom_backdrop(const Scene &scene, bool upload) {
    using Purpose = ::platform::ProducerPurpose;
    if (upload || scene.draws.empty() ||
        std::any_of(scene.clears.begin(), scene.clears.end(),
                    [](const auto &clear) { return (clear.flags & 1) != 0; }))
        return false;
    const auto &first = scene.draws.front();
    const auto &view = first.producer_view;
    if (!view.present || view.purpose != Purpose::WorldZoom || !view.camera_rect_available ||
        !view.canvas_available || view.camera_rect.width <= 0 || view.camera_rect.height <= 0 ||
        view.canvas.width <= 0 || view.canvas.height <= 0)
        return false;
    const auto &r = first.scissor;
    if (r.offset.x < 0 || r.offset.y < 0 || !r.extent.width || !r.extent.height ||
        unsigned(r.offset.x) + std::uint64_t(r.extent.width) > scene.width ||
        unsigned(r.offset.y) + std::uint64_t(r.extent.height) > scene.height)
        return false;
    bool opaque = false;
    for (const auto &draw : scene.draws) {
        opaque |= !draw.key.blend;
        if (!uses_world_range(scene, draw) ||
            !::platform::same_producer_view_bits(view, draw.producer_view) ||
            draw.scissor.offset.x != r.offset.x || draw.scissor.offset.y != r.offset.y ||
            draw.scissor.extent.width != r.extent.width ||
            draw.scissor.extent.height != r.extent.height)
            return false;
    }
    if (!opaque)
        return false;
    select_world_target(false, false);
    settle();
    ensure_range_backdrop(1, false);
    auto &sky = range_backdrops[1];
    const auto rect = scaled(r);
    check(f.vkResetCommandPool(device, commandPool, 0), "reset zoom backdrop pool");
    VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    check(f.vkBeginCommandBuffer(cmd, &begin), "begin zoom backdrop copy");
    if (in_attachment_layout)
        barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    barrier(sky.color.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0,
            VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    VkImageCopy region{};
    region.srcSubresource = region.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    region.srcOffset = region.dstOffset = {rect.offset.x, rect.offset.y, 0};
    region.extent = {rect.extent.width, rect.extent.height, 1};
    f.vkCmdCopyImage(cmd, colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, sky.color.image,
                     VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
    barrier(sky.color.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
            VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    if (in_attachment_layout)
        barrier(colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_ACCESS_TRANSFER_READ_BIT,
                VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                VK_IMAGE_ASPECT_COLOR_BIT);
    check(f.vkEndCommandBuffer(cmd), "end zoom backdrop copy");
    check(f.vkResetFences(device, 1, &fence), "reset zoom backdrop fence");
    VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    submit.commandBufferCount = 1;
    submit.pCommandBuffers = &cmd;
    check(f.vkQueueSubmit(queue, 1, &submit, fence), "submit zoom backdrop copy");
    scene_pending = true;
    sky.view = view;
    sky.resident = true;
    return true;
}

void capture_range_backdrops(Scene &original, bool upload) {
    for (auto &sky : range_backdrops)
        sky.view = {};
    if (!rgba || original.hud || original.frontend_canvas || original.guest_surface_write ||
        original.pom_diagnostic_mode)
        return;
    if (copy_zoom_backdrop(original, upload))
        return;
    // Multiple clears after terrain or incompatible sky emissions have no single
    // unambiguous backdrop for the packet. Keep coverage in that case.
    bool emitted = false;
    std::array<float, 4> clear_color{};
    std::array<const ::platform::ProducerView *, 2> views{};
    std::array<bool, 2> ambiguous{};
    for (const auto &o : original.order) {
        if (o.clear) {
            const auto &clear = original.clears[o.index];
            if (!(clear.flags & 1))
                continue;
            if (emitted || clear.rects.size() != 1 || clear.rects.front().offset.x != 0 ||
                clear.rects.front().offset.y != 0 ||
                clear.rects.front().extent.width != original.width ||
                clear.rects.front().extent.height != original.height)
                return;
            std::copy_n(clear.color, 4, clear_color.begin());
            clear_color[3] = 1.f;
            continue;
        }
        const auto &d = original.draws[o.index];
        emitted = true;
        if (!d.native_sky && d.sky != 1 && d.sky != 2)
            continue;
        const auto &v = d.producer_view;
        const unsigned id = unsigned(v.purpose);
        if (!v.present || !id || id > views.size())
            return;
        if (d.model || d.key.blend ||
            (views[id - 1] && !::platform::same_producer_view_bits(*views[id - 1], v)))
            ambiguous[id - 1] = true;
        views[id - 1] = &v;
    }
    for (unsigned id = 0; id < views.size(); ++id) {
        if (!views[id] || ambiguous[id])
            continue;
        if (std::none_of(original.draws.begin(), original.draws.end(), [&](const auto &draw) {
                return uses_world_range(original, draw) && !draw.key.blend &&
                       ::platform::same_producer_view_bits(*views[id], draw.producer_view);
            }))
            continue;
        Scene capture{};
        capture.width = original.width;
        capture.height = original.height;
        capture.has_depth = true;
        capture.detail_settings = original.detail_settings;
        capture.detail_time = original.detail_time;
        Clear clear{};
        clear.flags = 3;
        std::copy(clear_color.begin(), clear_color.end(), clear.color);
        clear.rects.push_back({{0, 0}, {capture.width, capture.height}});
        capture.clears.push_back(std::move(clear));
        capture.order.push_back({true, 0});
        for (const auto &o : original.order) {
            if (o.clear)
                continue;
            const auto &source = original.draws[o.index];
            if ((!source.native_sky && source.sky != 1 && source.sky != 2) ||
                !::platform::same_producer_view_bits(*views[id], source.producer_view))
                continue;
            auto draw = source;
            const auto offset = size_t(draw.first) * 32, size = size_t(draw.count) * 32;
            if (offset > original.vertices.size() || size > original.vertices.size() - offset)
                throw std::runtime_error("Range backdrop TL vertex range is invalid");
            draw.first = unsigned(capture.vertices.size() / 32);
            draw.emission_index = mw34::submission::DrawEmissions::none;
            capture.vertices.insert(capture.vertices.end(), original.vertices.begin() + offset,
                                    original.vertices.begin() + offset + size);
            capture.order.push_back({false, unsigned(capture.draws.size())});
            capture.draws.push_back(std::move(draw));
        }
        ensure_range_backdrop(id);
        range_backdrops[id].resident = false;
        struct Scope {
            Renderer &r;
            Scene &original, &capture;
            bool attachment, dirty;
            Scope(Renderer &r, Scene &original, Scene &capture, RangeBackdrop &destination)
                : r(r), original(original), capture(capture), attachment(r.in_attachment_layout),
                  dirty(r.quality_world_dirty) {
                original.textures.swap(capture.textures);
                r.recording_backdrop = &destination;
            }
            ~Scope() {
                r.recording_backdrop = nullptr;
                r.in_attachment_layout = attachment;
                r.quality_world_dirty = dirty;
                original.textures.swap(capture.textures);
            }
        } scope(*this, original, capture, range_backdrops[id]);
        render_scene(capture, false, false);
        range_backdrops[id].view = *views[id];
    }
}
