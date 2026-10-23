"""Batch adjacent compatible fixture-shadow triangle ranges without reordering.

Retain all original caster selection, clipping and push arithmetic. Only
contiguous complete triangles with identical buffer/set/push bytes can merge.
"""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACT = 'f44627d44d1792b8a76eb2540103668570e84f725b756631cd238400d80aa087'


def apply(host):
    path = host / 'fixture_shadow_stage.inc'
    source = path.read_text(encoding='utf-8')
    if hashlib.sha256(path.read_bytes()).hexdigest() != CONTRACT:
        raise ValueError('Shadow batch source contract changed; review required')
    replacements = [
        ('    void record_fixture_shadows(const mw34::effects::Uniform& lights) {', '''    void record_fixture_shadows(const mw34::effects::Uniform& lights) {
        static const bool batch=[] {
            const char* value=std::getenv("MW34_SHADOW_BATCH");
            if(!value||!*value||!std::strcmp(value,"0"))return false;
            if(!std::strcmp(value,"1"))return true;
            throw std::runtime_error("MW34_SHADOW_BATCH must be 0 or 1");
        }();'''),
        ('                for(const auto* caster:fixtureFrameCasters)', '''                struct Push {mw34::fixture_shadow::Clip clip;std::array<float,4> alpha;};
                static_assert(sizeof(Push)==80);
                VkBuffer batchBuffer{};VkDescriptorSet batchSet{};Push batchPush{};
                unsigned batchFirst=0,batchCount=0;
                auto emit=[&]{if(!batchCount)return;
                    const VkDeviceSize zero=0;f.vkCmdBindVertexBuffers(cmd,0,1,&batchBuffer,&zero);
                    f.vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_GRAPHICS,fixtureShadowLayout,0,1,&batchSet,0,nullptr);
                    f.vkCmdPushConstants(cmd,fixtureShadowLayout,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,0,sizeof(batchPush),&batchPush);
                    f.vkCmdDraw(cmd,batchCount,1,batchFirst,0);batchCount=0;
                };
                for(const auto* caster:fixtureFrameCasters)'''),
        ('                    struct Push {mw34::fixture_shadow::Clip clip;std::array<float,4> alpha;};const Push push{mw34::fixture_shadow::compose(clip,caster->world),caster->alpha};static_assert(sizeof(Push)==80);',
         '''                    const Push push{mw34::fixture_shadow::compose(clip,caster->world),caster->alpha};
                    if(batch&&caster->count){
                        const std::uint64_t total=std::uint64_t(batchCount)+caster->count;
                        // Incomplete triangle tails cannot cross a draw boundary.
                        const bool same=batchBuffer==caster->buffer&&batchSet==caster->set&&
                            !std::memcmp(&batchPush,&push,sizeof(push))&&
                            std::uint64_t(batchFirst)+batchCount==caster->first&&
                            !(batchCount%3)&&!(caster->count%3)&&total<=0xffffffffULL;
                        if(batchCount&&!same)emit();
                        if(!batchCount){batchBuffer=caster->buffer;batchSet=caster->set;batchPush=push;batchFirst=caster->first;}
                        batchCount+=caster->count;continue;
                    }
                    if(batch)emit();'''),
        ('                }\n            }\n        }\n        f.vkCmdEndRenderPass(cmd);',
         '                }\n                if(batch)emit();\n            }\n        }\n        f.vkCmdEndRenderPass(cmd);'),
    ]
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError('Shadow batch anchor changed: ' + old)
        source = source.replace(old, new)
    path.write_text(source, encoding='utf-8')
    return dict(parent_shadow_source_sha256=CONTRACT,
                shadow_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    print(json.dumps(apply(parser.parse_args().host_source.resolve(strict=True)), indent=2))
