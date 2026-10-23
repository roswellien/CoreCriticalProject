"""Apply exact-state adjacent TL batching and bounded scene reservations.

Targets the modern native renderer after resource warmup. Shader programs must
retain the reviewed attribute-based TL input contract (no primitive/draw IDs).
All anchors are checked before writing; generated game translations stay local.
"""
from pathlib import Path
import argparse
import hashlib

SHADER_PINS = {'d3d_scene_frag.h': '7b416e54999db332efb6cb98760862a44bed724fc7d3e96ec221dca25fb15776',
 'd3d_scene_vert.h': '14724d337712489bebaf9535aa89457d510da8b600c8bdd03de556397a394d14',
 'effect_scene_frag.h': '1e01ed2fc13d18f3bf4d852025ae8746c404a07d9a1110fb1bf09800eb0cf3e6',
 'sun_tl_vert.h': 'bba6d2e023b6c7a0633b32554ae237e78961765ca613dbb4c80f644ca46813eb'}

PATCHES = {
    'd3d_provider.inc': [
        (r''' const bool keep=lazy&&!rescale&&host.sren&&host.res_rt==rt->guest&&host.res_zb==(zb?zb->guest:0U)&&(host.res_dirty||(rt->version==host.res_ver_rt&&(!zb||zb->version==host.res_ver_zb)));
 if(!keep){sc.color.resize(px);sc.depth.assign(px,0);rows_in(*rt,sc.color);if(zb)rows_in(*zb,sc.depth);}  /* a resident scene (keep) uploads nothing and needs no host buffers */
 std::map<unsigned,int>tex_index;const auto&dflt=rs_defaults();const std::vector<unsigned>*validated=nullptr;
 for(const auto&c:d.commands){
''', r''' const bool keep=lazy&&!rescale&&host.sren&&host.res_rt==rt->guest&&host.res_zb==(zb?zb->guest:0U)&&(host.res_dirty||(rt->version==host.res_ver_rt&&(!zb||zb->version==host.res_ver_zb)));
 if(!keep){sc.color.resize(px);sc.depth.assign(px,0);rows_in(*rt,sc.color);if(zb)rows_in(*zb,sc.depth);}  /* a resident scene (keep) uploads nothing and needs no host buffers */
 // One output draw/order record per captured command; avoid copying large
 // lighting/material records repeatedly as the vectors grow.
 sc.draws.reserve(d.commands.size());sc.order.reserve(d.commands.size());
 size_t vertexBytes=0;
 for(const auto& command:d.commands)if(command.kind==D3DCmd::Draw&&!(command.model&&!command.model->world)){
  const size_t n=command.indices.empty()?command.vertices.size()/32:command.indices.size();
  const size_t count=command.flags==D3DPT_POINTLIST?n:command.flags==D3DPT_TRIANGLELIST?(n/3)*3:n>=3?(n-2)*3:0;
  if(count>(sc.vertices.max_size()-vertexBytes)/32)deny("Scene vertex reservation exceeds host bounds",0);
  vertexBytes+=count*32;
 }
 sc.vertices.reserve(vertexBytes);
 std::map<unsigned,int>tex_index;const auto&dflt=rs_defaults();const std::vector<unsigned>*validated=nullptr;
 for(const auto&c:d.commands){
'''),
        (r'''  else if(c.flags==D3DPT_POINTLIST){for(size_t i=0;i<nv;++i)vert(i);dr.key.points=1;}  // one-pixel points (shader point size 1)
  else deny("Primitive type not modelled by the scene renderer",c.flags);
  dr.count=unsigned(sc.vertices.size()/32)-dr.first;wide_adapt_tl(sc,dr,c.hud_role,c.zoom_anchor_known?&c.zoom_anchor:nullptr);sc.order.push_back({false,unsigned(sc.draws.size())});sc.draws.push_back(dr);}
 distance_scene_log(sc);effect_scene(sc);
 scene_renderer();try{HostInternal hi(*this);host.sren->render(sc,!keep,!lazy);}catch(const std::exception&e){deny(std::string(e.what()),0);}
''', r'''  else if(c.flags==D3DPT_POINTLIST){for(size_t i=0;i<nv;++i)vert(i);dr.key.points=1;}  // one-pixel points (shader point size 1)
  else deny("Primitive type not modelled by the scene renderer",c.flags);
  dr.count=unsigned(sc.vertices.size()/32)-dr.first;wide_adapt_tl(sc,dr,c.hud_role,c.zoom_anchor_known?&c.zoom_anchor:nullptr);sc.order.push_back({false,unsigned(sc.draws.size())});sc.draws.push_back(std::move(dr));}
 distance_scene_log(sc);effect_scene(sc);
 scene_renderer();try{HostInternal hi(*this);host.sren->render(sc,!keep,!lazy);}catch(const std::exception&e){deny(std::string(e.what()),0);}
'''),
    ],
    'vk_scene.hpp': [
        (r'''#include <windows.h>
#include "pipeline_warmup.hpp"
#include <vulkan/vulkan_win32.h>
#include <algorithm>
''', r'''#include <windows.h>
#include "pipeline_warmup.hpp"
#include "exact_uniform_runs.hpp"
#include <vulkan/vulkan_win32.h>
#include <algorithm>
'''),
        (r'''  public:
    std::string device_name;
    std::uint64_t scenes{}, draws{}, uploads{};
    using PerfOverlay = mw34::performance::Overlay;
    PerfOverlay overlay;
''', r'''  public:
    std::string device_name;
    std::uint64_t scenes{}, draws{}, uploads{}, submitted_draws{}, combined_draws{};
    using PerfOverlay = mw34::performance::Overlay;
    PerfOverlay overlay;
'''),
        (r'''        const ShadowFrame shadowFrame = prepare_shadow(s, environment);
        const auto fixtureLights = prepare_fixture_shadows(s, bound);
        bool sunScene = false;
        if (mw34::sun::settings().enabled) {
''', r'''        const ShadowFrame shadowFrame = prepare_shadow(s, environment);
        const auto fixtureLights = prepare_fixture_shadows(s, bound);
        // Upload memory can be write-combined: never read it for CPU comparisons.
        mw34::submission::ExactUniformRuns<mw34::sun::Uniform> uniformRuns;
        std::vector<unsigned> sunUniformIds(s.draws.size());
        bool sunScene = false;
        if (mw34::sun::settings().enabled) {
'''),
        (r'''                    u.emission_params = draw.emission_params;
                    u.emission_regions = draw.emission_regions;
                    std::memcpy(static_cast<unsigned char *>(sunBuffer.mapped) + at * sunStride, &u,
                                sizeof(u));
''', r'''                    u.emission_params = draw.emission_params;
                    u.emission_regions = draw.emission_regions;
                    sunUniformIds[at] = uniformRuns.identify(u);
                    std::memcpy(static_cast<unsigned char *>(sunBuffer.mapped) + at * sunStride, &u,
                                sizeof(u));
'''),
        (r'''        f.vkCmdBindVertexBuffers(cmd, 0, 1, &vertexBuffer.buffer, &zero);
        VkBuffer boundVertices = vertexBuffer.buffer;
        // Draw and clear indices refer to separate arrays, but their ordering is shared.
        for (const auto &o : s.order) {
            if (o.clear) {
                const auto &c = s.clears[o.index];
''', r'''        f.vkCmdBindVertexBuffers(cmd, 0, 1, &vertexBuffer.buffer, &zero);
        VkBuffer boundVertices = vertexBuffer.buffer;
        // Coalesce only adjacent complete TL triangle lists. All effective
        // GPU inputs must match bit-for-bit; never cross clears or model draws.
        // The shaders use vertex attributes, not primitive/draw IDs.
        static const bool combine = [] {
            const char* value = std::getenv("MW34_TL_COMBINE");
            if (!value || !*value || std::strcmp(value, "1") == 0) return true;
            if (std::strcmp(value, "0") == 0) return false;
            throw std::runtime_error("MW34_TL_COMBINE must be 0 or 1");
        }();
        auto same_tl = [&](unsigned a, unsigned b) {
            const auto& left = s.draws[a]; const auto& right = s.draws[b];
            if (left.model || right.model || left.key.points || right.key.points ||
                !left.count || !right.count || left.count % 3 || right.count % 3 ||
                left.key.packed() != right.key.packed() || drawSets[a] != drawSets[b] ||
                std::memcmp(&left.push, &right.push, sizeof(Push)) != 0 ||
                std::memcmp(&left.scissor, &right.scissor, sizeof(VkRect2D)) != 0)
                return false;
            const bool lit = !s.hud && sun_lit(left);
            if (lit != (!s.hud && sun_lit(right))) return false;
            if (lit && (drawNormalSets[a] != drawNormalSets[b] ||
                sunUniformIds[a] != sunUniformIds[b])) return false;
            return true;
        };
        // Draw and clear indices refer to separate arrays, but their ordering is shared.
        for (size_t orderAt = 0; orderAt < s.order.size(); ++orderAt) {
            const auto &o = s.order[orderAt];
            if (o.clear) {
                const auto &c = s.clears[o.index];
'''),
        (r'''            if (!d.count || !d.scissor.extent.width || !d.scissor.extent.height)
                continue;
            const bool model = bool(d.model), lit = !s.hud && sun_lit(d);
            const VkPipelineLayout layout = (model || lit) ? modelLayout : pipelineLayout;
''', r'''            if (!d.count || !d.scissor.extent.width || !d.scissor.extent.height)
                continue;
            unsigned vertexCount = d.count, logicalDraws = 1;
            if (combine && !d.model && !d.key.points && d.count % 3 == 0) {
                while (orderAt + 1 < s.order.size()) {
                    const auto& next = s.order[orderAt + 1];
                    if (next.clear) break;
                    const auto& candidate = s.draws[next.index];
                    if (std::uint64_t(d.first) + vertexCount != candidate.first ||
                        std::uint64_t(vertexCount) + candidate.count > 0xffffffffULL ||
                        !same_tl(o.index, next.index)) break;
                    vertexCount += candidate.count;
                    ++logicalDraws; ++orderAt;
                }
            }
            const bool model = bool(d.model), lit = !s.hud && sun_lit(d);
            const VkPipelineLayout layout = (model || lit) ? modelLayout : pipelineLayout;
'''),
        (r'''                                          &drawNormalSets[o.index], 0, nullptr);
                if (!d.model)
                    ++sun_tl_draws;
                else if (d.model->world)
                    ++sun_world_draws;
''', r'''                                          &drawNormalSets[o.index], 0, nullptr);
                if (!d.model)
                    sun_tl_draws += logicalDraws;
                else if (d.model->world)
                    ++sun_world_draws;
'''),
        (r'''                                     sizeof(Push), &d.push);
            }
            f.vkCmdDraw(cmd, d.count, 1, d.model && d.model->world ? 0 : d.first, 0);
            ++draws;
        }
        f.vkCmdEndRenderPass(cmd);
''', r'''                                     sizeof(Push), &d.push);
            }
            f.vkCmdDraw(cmd, vertexCount, 1, d.model && d.model->world ? 0 : d.first, 0);
            draws += logicalDraws;
            ++submitted_draws;
            combined_draws += logicalDraws - 1;
        }
        f.vkCmdEndRenderPass(cmd);
'''),
        (r'''        f.vkDeviceWaitIdle(device);
        pipelineWarmup.save();
        if (qualityPipeline)
            f.vkDestroyPipeline(device, qualityPipeline, nullptr);
''', r'''        f.vkDeviceWaitIdle(device);
        pipelineWarmup.save();
        std::fprintf(stderr, "Submission: %llu logical draws, %llu GPU draws, %llu adjacent TL draws combined\n",
            (unsigned long long)draws, (unsigned long long)submitted_draws,
            (unsigned long long)combined_draws);
        if (qualityPipeline)
            f.vkDestroyPipeline(device, qualityPipeline, nullptr);
'''),
    ],
}

def apply(host):
    for name, expected in SHADER_PINS.items():
        if hashlib.sha256((host / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Recheck TL batching inputs before using changed shader: {name}")
    header = (Path(__file__).parent / 'native-overrides' / 'exact_uniform_runs.hpp').read_bytes()
    planned = {}
    for name, patches in PATCHES.items():
        path = host / name
        source = path.read_text()
        for before, after in patches:
            if after in source:
                continue
            if source.count(before) != 1:
                raise RuntimeError(f"Unexpected submission adapter anchor in {name}: {before[:70]}")
            source = source.replace(before, after, 1)
        planned[path] = source
    for path, source in planned.items():
        if path.read_text() != source:
            path.write_text(source)
    destination = host / 'exact_uniform_runs.hpp'
    if not destination.exists() or destination.read_bytes() != header:
        destination.write_bytes(header)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    args = parser.parse_args()
    apply(args.host)
