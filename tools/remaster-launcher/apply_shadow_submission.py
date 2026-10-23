"""Remove repeated light membership checks and identical Vulkan shadow binds.

All caches are local to one shadow pass. Caster order, clipping, push constants,
draws, shaders, atlas dimensions and light selection are unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACT = "f44627d44d1792b8a76eb2540103668570e84f725b756631cd238400d80aa087"


def apply(host):
    path = host / "fixture_shadow_stage.inc"
    source = path.read_text(encoding="utf-8")
    if hashlib.sha256(path.read_bytes()).hexdigest() != CONTRACT:
        raise ValueError("Shadow recording source changed; review required")
    method = "    void record_fixture_shadows(const mw34::effects::Uniform& lights) {"
    start = source.index(method)
    before, section = source[:start], source[start:]
    replacements = [
        (method, method + '''
        static const bool reuse=[] {
            const char* value=std::getenv("MW34_SHADOW_SUBMISSION_REUSE");
            if(!value||!*value||!std::strcmp(value,"0"))return false;
            if(!std::strcmp(value,"1"))return true;
            throw std::runtime_error("MW34_SHADOW_SUBMISSION_REUSE must be 0 or 1");
        }();'''),
        ("        VkClearValue clear{};clear.depthStencil.depth=1;",
         '''        // Neither membership nor bindings change between cube faces.
        // Start fresh each pass so destruction/recreation cannot leave stale handles.
        std::vector<FixtureCaster*> light_casters;
        if(reuse)light_casters.reserve(fixtureFrameCasters.size());
        VkBuffer last_buffer{};VkDescriptorSet last_set{};
        bool buffer_bound=false,set_bound=false;
        VkClearValue clear{};clear.depthStencil.depth=1;'''),
        ("            for(unsigned side=0;side<6;++side)",
         '''            if(reuse){light_casters.clear();
                for(auto* caster:fixtureFrameCasters)
                    if(caster->bounds.overlaps({light.start[0],light.start[1],light.start[2]},light.start[3]))light_casters.push_back(caster);
            }
            const auto& casters=reuse?light_casters:fixtureFrameCasters;
            for(unsigned side=0;side<6;++side)'''),
        ("for(const auto* caster:fixtureFrameCasters){if(!caster->bounds.overlaps(",
         "for(const auto* caster:casters){if(!reuse&&!caster->bounds.overlaps("),
        ("const VkDeviceSize zero=0;f.vkCmdBindVertexBuffers(cmd,0,1,&caster->buffer,&zero);f.vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,fixtureShadowLayout,0,1,&caster->set,0,nullptr);",
         '''const VkDeviceSize zero=0;
                    if(!reuse||!buffer_bound||last_buffer!=caster->buffer){f.vkCmdBindVertexBuffers(cmd,0,1,&caster->buffer,&zero);last_buffer=caster->buffer;buffer_bound=true;}
                    if(!reuse||!set_bound||last_set!=caster->set){f.vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,fixtureShadowLayout,0,1,&caster->set,0,nullptr);last_set=caster->set;set_bound=true;}'''),
    ]
    for old, new in replacements:
        if section.count(old) != 1:
            raise ValueError("Shadow submission anchor changed: " + old)
        section = section.replace(old, new)
    path.write_text(before + section, encoding="utf-8")
    return {"parent_shadow_source_sha256": CONTRACT,
            "shadow_source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_source", type=Path)
    args = parser.parse_args()
    print(json.dumps(apply(args.host_source.resolve(strict=True)), indent=2))
