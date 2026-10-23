// The driver extracts the actual record method into record_off.inc and
// record_on.inc, renames it, and fixes its configuration to false/true. This
// fixture observes commands from those methods rather than reimplementing them.
#include <vulkan/vulkan.h>
#include "fixture_shadow.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace mw34::effects {
inline constexpr unsigned capacity = 64;
struct Light { std::array<float, 4> start{}; };
struct Uniform {
    std::array<float, 4> params{};
    std::array<Light, capacity> lights{};
    std::array<std::array<float, 4>, capacity> shadow{};
};
} // namespace mw34::effects

namespace {
void require(bool value, const char* message) {
    if (!value)
        throw std::runtime_error(message);
}
template <class Handle> Handle handle(std::uintptr_t value) {
    if constexpr (std::is_pointer_v<Handle>)
        return reinterpret_cast<Handle>(value);
    else
        return static_cast<Handle>(value);
}

struct DrawState {
    VkBuffer buffer{};
    VkDeviceSize buffer_offset{};
    VkDescriptorSet set{};
    VkPipeline pipeline{};
    VkPipelineLayout descriptor_layout{}, push_layout{};
    VkShaderStageFlags push_stages{};
    std::array<std::uint32_t, 6> viewport{};
    std::array<std::int64_t, 4> scissor{};
    std::array<unsigned char, 80> push{};
    unsigned count{}, instances{}, first{}, first_instance{};
    bool operator==(const DrawState&) const = default;
};

struct Commands {
    DrawState state;
    std::vector<DrawState> draws;
    std::array<std::uint32_t, 5> clear_and_area{};
    unsigned buffer_binds{}, set_binds{}, pushes{}, viewports{}, scissors{}, begins{}, ends{};
    bool open{}, have_buffer{}, have_set{}, have_pipeline{}, have_viewport{}, have_scissor{}, have_push{};

    void reset() {
        require(!open, "Previous shadow pass was left open");
        *this = Commands{};
        // Simulate a fresh command buffer or unrelated preceding pass. A
        // renderer cache carried between calls cannot supply a valid first bind.
        state.buffer = handle<VkBuffer>(0xf001);
        state.set = handle<VkDescriptorSet>(0xf002);
    }
    void vkCmdBeginRenderPass(VkCommandBuffer, const VkRenderPassBeginInfo* pass,
                              VkSubpassContents contents) {
        require(!open && contents == VK_SUBPASS_CONTENTS_INLINE, "Invalid pass begin");
        require(pass->clearValueCount == 1, "Missing atlas clear");
        clear_and_area = {std::bit_cast<std::uint32_t>(pass->pClearValues[0].depthStencil.depth),
                          std::uint32_t(pass->renderArea.offset.x),
                          std::uint32_t(pass->renderArea.offset.y),
                          pass->renderArea.extent.width, pass->renderArea.extent.height};
        open = true;
        ++begins;
    }
    void vkCmdBindPipeline(VkCommandBuffer, VkPipelineBindPoint point, VkPipeline pipeline) {
        require(open && point == VK_PIPELINE_BIND_POINT_GRAPHICS, "Invalid pipeline bind");
        state.pipeline = pipeline;
        have_pipeline = true;
    }
    void vkCmdSetViewport(VkCommandBuffer, unsigned first, unsigned count, const VkViewport* value) {
        require(open && first == 0 && count == 1, "Unexpected viewport range");
        state.viewport = {std::bit_cast<std::uint32_t>(value->x), std::bit_cast<std::uint32_t>(value->y),
                          std::bit_cast<std::uint32_t>(value->width), std::bit_cast<std::uint32_t>(value->height),
                          std::bit_cast<std::uint32_t>(value->minDepth), std::bit_cast<std::uint32_t>(value->maxDepth)};
        have_viewport = true;
        ++viewports;
    }
    void vkCmdSetScissor(VkCommandBuffer, unsigned first, unsigned count, const VkRect2D* value) {
        require(open && first == 0 && count == 1, "Unexpected scissor range");
        state.scissor = {value->offset.x, value->offset.y, value->extent.width, value->extent.height};
        have_scissor = true;
        ++scissors;
    }
    void vkCmdBindVertexBuffers(VkCommandBuffer, unsigned first, unsigned count,
                                const VkBuffer* buffer, const VkDeviceSize* offset) {
        require(open && first == 0 && count == 1, "Unexpected vertex binding range");
        state.buffer = *buffer;
        state.buffer_offset = *offset;
        have_buffer = true;
        ++buffer_binds;
    }
    void vkCmdBindDescriptorSets(VkCommandBuffer, VkPipelineBindPoint point, VkPipelineLayout layout,
                                 unsigned first, unsigned count, const VkDescriptorSet* set,
                                 unsigned dynamic_count, const unsigned*) {
        require(open && point == VK_PIPELINE_BIND_POINT_GRAPHICS && first == 0 && count == 1 &&
                    dynamic_count == 0, "Unexpected descriptor binding range");
        state.set = *set;
        state.descriptor_layout = layout;
        have_set = true;
        ++set_binds;
    }
    void vkCmdPushConstants(VkCommandBuffer, VkPipelineLayout layout, VkShaderStageFlags stages,
                            unsigned offset, unsigned bytes, const void* data) {
        require(open && offset == 0 && bytes == state.push.size(), "Unexpected shadow push range");
        std::memcpy(state.push.data(), data, state.push.size());
        state.push_layout = layout;
        state.push_stages = stages;
        have_push = true;
        ++pushes;
    }
    void vkCmdDraw(VkCommandBuffer, unsigned count, unsigned instances, unsigned first, unsigned first_instance) {
        require(open && have_buffer && have_set && have_pipeline && have_viewport && have_scissor && have_push,
                "Draw lacks complete command state, including first binds");
        state.count = count;
        state.instances = instances;
        state.first = first;
        state.first_instance = first_instance;
        draws.push_back(state);
        have_push = false;
    }
    void vkCmdEndRenderPass(VkCommandBuffer) {
        require(open, "Shadow pass ended without begin");
        open = false;
        ++ends;
    }
};

struct CountedBounds : mw34::fixture_shadow::Bounds {
    static inline std::uint64_t overlaps_count{};
    bool overlaps(const mw34::fixture_shadow::Point& point, float radius) const {
        ++overlaps_count;
        return Bounds::overlaps(point, radius);
    }
};
struct FixtureCaster {
    VkBuffer buffer{};
    unsigned first{}, count{};
    mw34::fixture_shadow::Matrix world = mw34::fixture_shadow::identity;
    CountedBounds bounds;
    std::array<float, 4> alpha{};
    VkDescriptorSet set{};
};
struct Renderer {
    Commands f;
    VkCommandBuffer cmd = handle<VkCommandBuffer>(1);
    VkRenderPass fixtureShadowPass = handle<VkRenderPass>(2);
    VkFramebuffer fixtureShadowFramebuffer = handle<VkFramebuffer>(3);
    VkPipeline fixtureShadowPipeline = handle<VkPipeline>(4);
    VkPipelineLayout fixtureShadowLayout = handle<VkPipelineLayout>(5);
    unsigned fixtureTile = 256, fixtureAtlasWidth = 4096, fixtureAtlasHeight = 6144;
    std::vector<FixtureCaster*> fixtureFrameCasters;
#include "record_off.inc"
#include "record_on.inc"
};
} // namespace

int main() {
    try {
        Renderer off, on;
        std::vector<FixtureCaster> casters(14);
        for (unsigned i = 0; i < casters.size(); ++i) {
            auto& caster = casters[i];
            // Consecutive identical bindings, then alternating buffers and
            // descriptor-only/buffer-only changes. Every caster has its own ID.
            caster.buffer = handle<VkBuffer>(100 + (i < 4 ? 0 : i % 3));
            caster.set = handle<VkDescriptorSet>(200 + (i < 4 ? 0 : (i / 2) % 3));
            caster.first = 1000 + i * 9;
            caster.count = 3 + (i % 3) * 3;
            caster.alpha = {float(i), float(i * 2), float(i & 1), 0};
            caster.bounds.low = {-2, -2, -2};
            caster.bounds.high = {2, 2, 2};
            if (i & 1) {
                caster.world = {0, 0, 1, float(i), 0, 1, 0, -float(i), -1, 0, 0, 0.25f};
            }
        }
        // A caster intersecting only one face and one outside every light.
        casters[12].bounds.low = {8, -0.1f, -0.1f};
        casters[12].bounds.high = {9, 0.1f, 0.1f};
        casters[13].bounds.low = {1000, 1000, 1000};
        casters[13].bounds.high = {1001, 1001, 1001};
        for (auto& caster : casters) {
            off.fixtureFrameCasters.push_back(&caster);
            on.fixtureFrameCasters.push_back(&caster);
        }
        mw34::effects::Uniform lights;
        lights.params[0] = 4;
        for (unsigned i : {0U, 1U, 3U}) {
            lights.lights[i].start = {0, 0, 0, 32};
            lights.shadow[i] = {1, 0.1f, 32, 0.025f};
        }
        lights.lights[1].start = {500, 500, 500, 2}; // Active light with no members.
        lights.lights[3].start = {8, 0, 0, 16};

        std::uint64_t off_overlaps = 0, on_overlaps = 0, draws = 0;
        unsigned off_buffers = 0, on_buffers = 0, off_sets = 0, on_sets = 0, passes = 0;
        auto compare = [&](const char* label) {
            off.f.reset();
            on.f.reset();
            CountedBounds::overlaps_count = 0;
            off.record_off(lights);
            const auto before = CountedBounds::overlaps_count;
            CountedBounds::overlaps_count = 0;
            on.record_on(lights);
            const auto after = CountedBounds::overlaps_count;
            require(!off.f.open && !on.f.open, "Pass remained open");
            if (off.f.draws != on.f.draws)
                throw std::runtime_error(std::string(label) + ": ordered GPU draw state differs");
            require(off.f.begins == on.f.begins && off.f.ends == on.f.ends &&
                        off.f.clear_and_area == on.f.clear_and_area &&
                        off.f.viewports == on.f.viewports && off.f.scissors == on.f.scissors &&
                        off.f.pushes == on.f.pushes, "Nonbinding command behavior changed");
            require(before == after * 6, "Membership tests were not reduced to once per light");
            require(on.f.buffer_binds <= off.f.buffer_binds && on.f.set_binds <= off.f.set_binds,
                    "Optimized submission increased binding commands");
            off_overlaps += before;
            on_overlaps += after;
            draws += off.f.draws.size();
            off_buffers += off.f.buffer_binds;
            on_buffers += on.f.buffer_binds;
            off_sets += off.f.set_binds;
            on_sets += on.f.set_binds;
            ++passes;
        };
        compare("mixed casters and empty light");

        // Change resources/transforms between calls, as with regenerated model
        // buffers and descriptor-pool resets, then submit an unchanged call too.
        for (auto& caster : casters) {
            caster.buffer = handle<VkBuffer>(300);
            caster.set = handle<VkDescriptorSet>(400);
            caster.world[3] += 0.5f;
        }
        compare("new resources");
        compare("unchanged resources in a fresh command buffer");
        std::reverse(off.fixtureFrameCasters.begin(), off.fixtureFrameCasters.end());
        on.fixtureFrameCasters = off.fixtureFrameCasters;
        compare("changed source traversal order");

        off.fixtureFrameCasters = {&casters[12]};
        on.fixtureFrameCasters = off.fixtureFrameCasters;
        lights.params[0] = 1;
        compare("one face occupied, five empty");
        lights.shadow[0] = {};
        compare("no active shadow lights");
        off.fixtureFrameCasters.clear();
        on.fixtureFrameCasters.clear();
        compare("empty caster list");
        off.fixtureFrameCasters = {&casters[0]};
        on.fixtureFrameCasters = off.fixtureFrameCasters;
        off.fixtureTile = on.fixtureTile = 0;
        compare("disabled atlas");

        require(draws && on_buffers < off_buffers && on_sets < off_sets && on_overlaps < off_overlaps,
                "Fixture did not demonstrate all targeted reductions");
        std::cout << "shadow submission passes=" << passes << " identical_draws=" << draws
                  << " overlaps=" << off_overlaps << "->" << on_overlaps
                  << " buffer_binds=" << off_buffers << "->" << on_buffers
                  << " descriptor_binds=" << off_sets << "->" << on_sets << " failures=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
