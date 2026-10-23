"""Add opt-in GPU/pass, existing-wait, atlas-caster and memory-budget attribution.

This changes diagnostics only. It does not select a runtime or optimize output.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

CONTRACTS = {
    'vk_scene.hpp': '1e1dc603db7543c0e001434c9ca5906402ba8891a378b6c7d799ec865ba2c739',
    'fixture_shadow_stage.inc': 'f44627d44d1792b8a76eb2540103668570e84f725b756631cd238400d80aa087',
    'quality_stage.inc': '3db87acaefe9c3ec044a94d3d66c9ba8fdfdabbf070aa4d79de5c800ae23781d',
}


def apply(host):
    sources = {name: (host / name).read_text(encoding='utf-8') for name in CONTRACTS}
    for name, pin in CONTRACTS.items():
        if pin and hashlib.sha256((host / name).read_bytes()).hexdigest() != pin:
            raise ValueError(name + ': GPU attribution source contract changed')
    helper = host / 'gpu_work_profile.hpp'
    if helper.exists():
        raise ValueError('GPU attribution already applied')

    def replace(name, old, new):
        if sources[name].count(old) != 1:
            raise ValueError(name + ': GPU attribution anchor changed: ' + old)
        sources[name] = sources[name].replace(old, new)

    vk = 'vk_scene.hpp'
    replace(vk, '#include "texture_staging.hpp"', '#include "texture_staging.hpp"\n#include "gpu_work_profile.hpp"')
    replace(vk, '    struct Fns {', '''    mw34::diagnostic::GpuWorkProfile work;
    VkResult profile_wait(VkDevice d, unsigned count, const VkFence* waits, VkBool32 all, std::uint64_t timeout) {
        const char* label=count==1&&waits[0]==fence?"scene_fence_wait":"present_fence_wait";
        const auto result=work.call(label,[&]{return f.vkWaitForFences(d,count,waits,all,timeout);});
        if(result==VK_SUCCESS&&work.enabled())for(unsigned i=0;i<count;++i){
            if(waits[i]==fence)work.collect(0);if(waits[i]==presentFence)work.collect(1);}
        return result;
    }
    VkResult profile_idle(VkDevice d) {
        const auto result=work.call("device_idle",[&]{return f.vkDeviceWaitIdle(d);});
        if(result==VK_SUCCESS){work.collect(0);work.collect(1);}return result;
    }
    VkResult profile_acquire(VkDevice d,VkSwapchainKHR swap,std::uint64_t timeout,VkSemaphore semaphore,VkFence wait,unsigned* index) {
        return work.call("acquire",[&]{return f.vkAcquireNextImageKHR(d,swap,timeout,semaphore,wait,index);});
    }
    VkResult profile_present(VkQueue q,const VkPresentInfoKHR* info) {
        return work.call("queue_present",[&]{return f.vkQueuePresentKHR(q,info);});
    }
    struct Fns {''')
    # Redirect original waits only; wrapper bodies retain the actual entry points.
    wrapper_start = sources[vk].index('    mw34::diagnostic::GpuWorkProfile work;')
    original, wrappers = sources[vk][:wrapper_start], sources[vk][wrapper_start:]
    for old, new in [('f.vkWaitForFences(', 'profile_wait('), ('f.vkDeviceWaitIdle(', 'profile_idle('),
                     ('f.vkAcquireNextImageKHR(', 'profile_acquire('), ('f.vkQueuePresentKHR(', 'profile_present(')]:
        original = original.replace(old, new)
    # Private target/swapchain/shutdown waits also need collection before reuse.
    marker = wrappers.index('    struct Fns {')
    body = wrappers[marker:]
    for old, new in [('f.vkWaitForFences(', 'profile_wait('), ('f.vkDeviceWaitIdle(', 'profile_idle(')]:
        body = body.replace(old, new)
    sources[vk] = original + wrappers[:marker] + body

    replace(vk, '        settle();\n        if (!device)\n            init();',
            '        work.context(s.world_frame,presents+1,scenes+1);\n        const auto profileRenderStart=work.clock();\n        settle();\n        if (!device)\n            init();')
    replace(vk, '        const auto fixtureLights = prepare_fixture_shadows(s, bound);',
            '        const auto profilePrepareStart=work.clock();\n        const auto fixtureLights = prepare_fixture_shadows(s, bound);\n        work.elapsed("shadow_prepare",profilePrepareStart);')
    replace(vk, '        } else\n            scene_pending = true;\n    }',
            '        } else\n            scene_pending = true;\n        work.elapsed("render_total",profileRenderStart);\n        work.event("scene","draws_mips_models_uploads",s.draws.size(),mip_levels_uploaded,model_uploads,uploads);\n    }')
    # Request only the optional memory query extension in the diagnostic mode.
    replace(vk, '            if (exclusiveRequested()) {\n                if (!has(', '''            if(work.enabled() && has(VK_KHR_GET_PHYSICAL_DEVICE_PROPERTIES_2_EXTENSION_NAME) && !exclusiveRequested())
                instanceExtensions.push_back(VK_KHR_GET_PHYSICAL_DEVICE_PROPERTIES_2_EXTENSION_NAME);
            if (exclusiveRequested()) {
                if (!has(''')
    replace(vk, '        std::vector<const char *> deviceExtensions;',
            '        std::vector<const char *> deviceExtensions;\n        bool profileBudget=false;')
    replace(vk, '            for (const auto &p : props) {\n                if (!std::strcmp(p.extensionName, swapExt))', '''            for (const auto &p : props) {
                if(work.enabled() && !std::strcmp(p.extensionName,VK_EXT_MEMORY_BUDGET_EXTENSION_NAME))profileBudget=true;
                if (!std::strcmp(p.extensionName, swapExt))''')
    replace(vk, '        check(f.vkCreateDevice(gpu, &dci, nullptr, &device), "create device");', '''        const bool profileProperties2=work.enabled()&&std::any_of(instanceExtensions.begin(),instanceExtensions.end(),
            [](const char* name){return !std::strcmp(name,VK_KHR_GET_PHYSICAL_DEVICE_PROPERTIES_2_EXTENSION_NAME);});
        auto profileMemory=profileProperties2?reinterpret_cast<PFN_vkGetPhysicalDeviceMemoryProperties2KHR>(get(instance,"vkGetPhysicalDeviceMemoryProperties2KHR")):nullptr;
        if(work.enabled() && profileBudget && profileMemory)deviceExtensions.push_back(VK_EXT_MEMORY_BUDGET_EXTENSION_NAME);
        dci.enabledExtensionCount=unsigned(deviceExtensions.size());dci.ppEnabledExtensionNames=deviceExtensions.data();
        check(f.vkCreateDevice(gpu, &dci, nullptr, &device), "create device");''')
    replace(vk, '        MW34_VK_DEV_FNS(MW34_VK_DLOAD)', '''        MW34_VK_DEV_FNS(MW34_VK_DLOAD)
        if(work.enabled()){
            unsigned n=0;f.vkGetPhysicalDeviceQueueFamilyProperties(gpu,&n,nullptr);
            std::vector<VkQueueFamilyProperties> properties(n);f.vkGetPhysicalDeviceQueueFamilyProperties(gpu,&n,properties.data());
            VkPhysicalDeviceProperties limits{};f.vkGetPhysicalDeviceProperties(gpu,&limits);
            work.initialize(device,gpu,f.vkGetDeviceProcAddr,properties.at(family).timestampValidBits,
                limits.limits.timestampPeriod,profileBudget?profileMemory:nullptr);
        }''')
    # A query bank is reset only after the normal fence/device wait collected it.
    pattern = r'(check\(f\.vkBeginCommandBuffer\((cmd|presentCmd), &bi\), "([^"]+)"\);)'
    sources[vk], count = re.subn(pattern, lambda m: m[1] + '\n        work.begin(' +
        ('1' if m[2] == 'presentCmd' else '0') + ',' + m[2] + ',"' + m[3] + '");', sources[vk])
    if count != 9:
        raise ValueError('Reviewed command begin inventory changed: ' + str(count))
    pattern = r'(check\(f\.vkEndCommandBuffer\((cmd|presentCmd)\), "[^"]+"\);)'
    sources[vk], ended = re.subn(pattern, lambda m: 'work.finish(' +
        ('1' if m[2] == 'presentCmd' else '0') + ',' + m[2] + ');\n        ' + m[1], sources[vk])
    if ended != count:
        raise ValueError('Command begin/end inventory differs')
    # Spans use the original command stream and add no resource barriers.
    replace(vk, '        record_fixture_shadows(fixtureLights);', '''        const auto fixtureSpan=work.start(0,cmd,"fixture_shadows");
        const auto profileRecordStart=work.clock();
        record_fixture_shadows(fixtureLights);
        work.elapsed("shadow_record",profileRecordStart);
        work.end(0,cmd,fixtureSpan);''')
    replace(vk, '        VkRenderPassBeginInfo rb{};\n        rb.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;\n        rb.renderPass = renderPass;',
            '        const auto worldSpan=work.start(0,cmd,"main_pass");\n        VkRenderPassBeginInfo rb{};\n        rb.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;\n        rb.renderPass = renderPass;')
    # Unique end of the main scene pass (other render passes live in includes).
    replace(vk, '        f.vkCmdEndRenderPass(cmd);\n        if (!s.hud && !s.draws.empty())',
            '        f.vkCmdEndRenderPass(cmd);\n        work.end(0,cmd,worldSpan);\n        if (!s.hud && !s.draws.empty())')
    sources[vk] = sources[vk].replace('        ++presents;', '        ++presents;\n        work.sampleMemory(presents);')
    replace(vk, '        f.vkDestroyDevice(device, nullptr);',
            '        work.shutdown();\n        f.vkDestroyDevice(device, nullptr);')

    quality = 'quality_stage.inc'
    replace(quality, '    // The temporary is a color copy, not a second rasterization.',
            '    const auto fxaaSpan=work.start(0,cmd,"fxaa");\n    // The temporary is a color copy, not a second rasterization.')
    # End must follow every command in this pass; closing brace is reviewed below.
    start = sources[quality].index('void record_fxaa() {')
    depth = 0
    for pos in range(sources[quality].index('{', start), len(sources[quality])):
        char = sources[quality][pos]
        if char == '{': depth += 1
        if char == '}':
            depth -= 1
            if depth == 0:
                sources[quality] = sources[quality][:pos] + '    work.end(0,cmd,fxaaSpan);\n' + sources[quality][pos:]
                break
    if 'return;' in sources[quality][sources[quality].index('const auto fxaaSpan'):pos]:
        raise ValueError('FXAA early return needs paired timestamp review')

    fixture = 'fixture_shadow_stage.inc'
    replace(fixture, '        std::vector<ModelVertex> tl;\n        for(auto& [key,caster]:fixtureCasters)',
            '        std::vector<ModelVertex> tl;\n        std::uint64_t profileCurrent=0,profileOld=0,profileTl=0,profileModel=0;\n        for(auto& [key,caster]:fixtureCasters)')
    replace(fixture, '            fixtureFrameCasters.push_back(&caster);', '''            fixtureFrameCasters.push_back(&caster);
            if(work.enabled()){profileCurrent+=caster.frame==scene.world_frame;profileOld+=caster.frame!=scene.world_frame;
                profileTl+=!caster.tl.empty();profileModel+=caster.tl.empty();}''')
    replace(fixture, '        return lights;\n    }', '''        work.event("casters","current_previous_tl_model",profileCurrent,profileOld,profileTl,profileModel);
        work.event("atlas","lights_vertices_hud_frontend",count-weapons,tl.size(),scene.hud,scene.frontend_canvas);
        return lights;
    }''')
    replace(fixture, '        VkClearValue clear{};clear.depthStencil.depth=1;',
            '        std::uint64_t profileDraws=0,profileVertices=0,profileFaces=0;\n        VkClearValue clear{};clear.depthStencil.depth=1;')
    replace(fixture, '                const auto clip=mw34::fixture_shadow::face(',
            '                ++profileFaces;\n                const auto clip=mw34::fixture_shadow::face(')
    replace(fixture, 'f.vkCmdDraw(cmd,caster->count,1,caster->first,0);',
            'f.vkCmdDraw(cmd,caster->count,1,caster->first,0);if(work.enabled()){++profileDraws;profileVertices+=caster->count;}')
    replace(fixture, '        f.vkCmdEndRenderPass(cmd);',
            '        f.vkCmdEndRenderPass(cmd);\n        work.event("atlas","draws_vertices_faces_casters",profileDraws,profileVertices,profileFaces,fixtureFrameCasters.size());')
    payload = (Path(__file__).parent / 'native-overrides/gpu_work_profile.hpp').read_bytes()
    for name, text in sources.items():
        (host / name).write_text(text, encoding='utf-8')
    helper.write_bytes(payload)
    return dict(parent_contracts=CONTRACTS,command_streams=count,
                helper_sha256=hashlib.sha256(payload).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    print(json.dumps(apply(parser.parse_args().host_source.resolve(strict=True)), indent=2))
