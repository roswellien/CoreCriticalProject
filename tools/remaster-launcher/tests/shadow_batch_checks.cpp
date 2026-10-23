// The driver extracts the actual batching record method into record_off.inc and
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
        Renderer off,on;
        std::vector<FixtureCaster> casters(16);
        for(unsigned i=0;i<casters.size();++i){
            auto& c=casters[i];c.buffer=handle<VkBuffer>(100);c.set=handle<VkDescriptorSet>(200);
            c.first=i*3;c.count=3;c.alpha={8,128,0,0};
            c.bounds.low={-2,-2,-2};c.bounds.high={2,2,2};
            off.fixtureFrameCasters.push_back(&c);on.fixtureFrameCasters.push_back(&c);
        }
        mw34::effects::Uniform lights;
        lights.params[0]=3;
        for(unsigned i=0;i<3;++i){lights.lights[i].start={float(i*4),0,0,32};lights.shadow[i]={1,.1f,32,.025f};}
        std::uint64_t beforeDraws=0,afterDraws=0,primitives=0;unsigned passes=0;
        auto expanded=[](const std::vector<DrawState>& draws){
            std::vector<DrawState> triangles;
            for(auto draw:draws)for(unsigned i=0;i+2<draw.count;i+=3){
                auto triangle=draw;triangle.first+=i;triangle.count=3;triangles.push_back(triangle);
            }
            return triangles;
        };
        auto compare=[&](const char* label){
            off.f.reset();on.f.reset();
            CountedBounds::overlaps_count=0;off.record_off(lights);const auto before=CountedBounds::overlaps_count;
            CountedBounds::overlaps_count=0;on.record_on(lights);const auto after=CountedBounds::overlaps_count;
            const auto a=expanded(off.f.draws),b=expanded(on.f.draws);
            if(a!=b)throw std::runtime_error(std::string(label)+": ordered triangle inputs differ");
            require(before==after,"Batching changed original light membership tests");
            require(!off.f.open&&!on.f.open&&off.f.begins==on.f.begins&&off.f.ends==on.f.ends&&
                off.f.clear_and_area==on.f.clear_and_area&&off.f.viewports==on.f.viewports&&
                off.f.scissors==on.f.scissors,"Atlas/face behavior changed");
            require(on.f.draws.size()<=off.f.draws.size(),"Batching increased draw count");
            beforeDraws+=off.f.draws.size();afterDraws+=on.f.draws.size();primitives+=a.size();++passes;
        };
        compare("contiguous identical triangles");
        require(on.f.draws.size()<off.f.draws.size(),"Contiguous compatible ranges did not merge");
        casters[3].set=handle<VkDescriptorSet>(201);
        casters[5].buffer=handle<VkBuffer>(101);
        casters[7].alpha={7,127,1,0};
        casters[9].alpha[3]=std::bit_cast<float>(0x80000000U);
        casters[11].world[3]=.25f;
        compare("descriptor buffer alpha signed-zero and transform boundaries");
        casters[4].bounds.low={1000,1000,1000};casters[4].bounds.high={1001,1001,1001};
        casters[6].bounds.low={8,-.1f,-.1f};casters[6].bounds.high={9,.1f,.1f};
        compare("light and cube-face exclusions retain physical range gaps");
        for(unsigned i=0;i<casters.size();++i){casters[i].count=i%6;casters[i].first=i*8;}
        // If 1/2-vertex tails cross a boundary they create extra triangles.
        casters[0].first=0;casters[0].count=4;casters[1].first=4;casters[1].count=5;
        compare("zero and incomplete triangle tails");
        std::reverse(off.fixtureFrameCasters.begin(),off.fixtureFrameCasters.end());
        on.fixtureFrameCasters=off.fixtureFrameCasters;
        compare("reverse traversal");
        // Resource and matrix changes across calls must never retain old batch state.
        for(auto& c:casters){c.buffer=handle<VkBuffer>(400);c.set=handle<VkDescriptorSet>(500);c.world[7]+=.5f;}
        compare("new resource identities");compare("fresh command buffer unchanged resources");
        off.fixtureFrameCasters={&casters[12]};on.fixtureFrameCasters=off.fixtureFrameCasters;
        casters[12].first=0xfffffffdU;casters[12].count=3;
        compare("high first vertex");
        lights.shadow[0]={};lights.shadow[1]={};lights.shadow[2]={};compare("no enabled lights");
        off.fixtureFrameCasters.clear();on.fixtureFrameCasters.clear();compare("empty casters");
        off.fixtureTile=on.fixtureTile=0;compare("disabled atlas");
        require(primitives&&afterDraws<beforeDraws,"Fixture did not exercise batching");
        std::cout<<"shadow batch passes="<<passes<<" identical_triangles="<<primitives
            <<" GPU_draws="<<beforeDraws<<"->"<<afterDraws<<" failures=0\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
