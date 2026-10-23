"""Reuse a submitted fixture atlas when every dependency is byte-identical.

Scope is one original world frame. No probabilistic hash, stale descriptors or
unchanged-caster-count assumptions qualify a cache hit.
"""
import argparse
import hashlib
import json
from pathlib import Path

VK_CONTRACTS = {
    '1e1dc603db7543c0e001434c9ca5906402ba8891a378b6c7d799ec865ba2c739',
    # Published 1.0.27 adds startup GPU/hardware diagnostics only.
    'f8bad2455da3a166af9f5a329fc1de3affa52fc9641c80fe9fce1b512b86b24b',
}
# The selected source plus the separately tested adjacent triangle batching.
FIXTURE_CONTRACT = '9ee11954fb0488b6a89fdd9c16742eb39003699187e77d3f9ee4fe17689178ae'


def apply(host):
    paths = [host / 'vk_scene.hpp', host / 'fixture_shadow_stage.inc']
    parent_vk = hashlib.sha256(paths[0].read_bytes()).hexdigest()
    for path, allowed in zip(paths, (VK_CONTRACTS, {FIXTURE_CONTRACT})):
        if hashlib.sha256(path.read_bytes()).hexdigest() not in allowed:
            raise ValueError(path.name + ': atlas reuse source contract changed')
    if (host / 'fixture_atlas_reuse.inc').exists():
        raise ValueError('Atlas reuse already applied')
    vk, fixture = [p.read_text(encoding='utf-8') for p in paths]
    def replace(text, old, new):
        if text.count(old) != 1:
            raise ValueError('Atlas reuse anchor changed: ' + old)
        return text.replace(old, new)
    vk = replace(vk, '        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit");\n        ++scenes;',
                 '        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit");\n        fixture_atlas_submitted();\n        ++scenes;')
    fixture = replace(fixture, '    void init_fixture_shadow() {',
                      '#include "fixture_atlas_reuse.inc"\n    void init_fixture_shadow() {')
    fixture = replace(fixture, 'auto lights=scene.effect_lights;for(auto& meta:lights.shadow)meta={};fixtureFrameCasters.clear();',
                      'auto lights=scene.effect_lights;for(auto& meta:lights.shadow)meta={};fixtureFrameCasters.clear();\n        fixtureAtlasFrame=scene.world_frame;fixtureAtlasRecorded=false;')
    fixture = replace(fixture, '{fixtureCasters.clear();fixtureGeneration=scene.world_generation;',
                      '{fixture_atlas_touch();fixtureCasters.clear();fixtureGeneration=scene.world_generation;')
    fixture = replace(fixture, 'if(invalid||(camera&&!caster.bounds.overlaps(eye,retention*2)))it=fixtureCasters.erase(it);else ++it;',
                      'if(invalid||(camera&&!caster.bounds.overlaps(eye,retention*2))){fixture_atlas_touch();it=fixtureCasters.erase(it);}else ++it;')
    fixture = replace(fixture, '            fixtureCasters[key]=std::move(caster);', '''            auto [stored,inserted]=fixtureCasters.try_emplace(key);
            if(fixture_atlas_capture_changed(inserted,stored->second,caster))fixture_atlas_touch();
            stored->second=std::move(caster);''')
    fixture = replace(fixture, '        if(!fixtureTile||fixtureFrameCasters.empty())return;',
                      '        if(!fixtureTile||fixtureFrameCasters.empty())return;\n        if(fixture_atlas_unchanged(lights))return;')
    fixture = replace(fixture, '        f.vkCmdEndRenderPass(cmd);',
                      '        f.vkCmdEndRenderPass(cmd);\n        if(fixture_atlas_reuse_enabled())fixtureAtlasRecorded=true;')
    fixture = replace(fixture, '    void drop_fixture_shadow() {', '''    void drop_fixture_shadow() {
        if(fixture_atlas_reuse_enabled())std::fprintf(stderr,"Fixture atlas reuse: %llu unchanged passes reused, %llu changed passes submitted, %llu tracked hits fully audited\\n",
            (unsigned long long)fixtureAtlasHits,(unsigned long long)fixtureAtlasBuilds,(unsigned long long)fixtureAtlasAudits);
        fixtureAtlasValid=false;fixtureAtlasRecorded=false;fixtureAtlasIdentity.clear();fixtureAtlasNext.clear();''')
    helper = (Path(__file__).parent / 'native-overrides/fixture_atlas_reuse.inc').read_bytes()
    paths[0].write_text(vk, encoding='utf-8');paths[1].write_text(fixture, encoding='utf-8')
    (host / 'fixture_atlas_reuse.inc').write_bytes(helper)
    return dict(parent_vk_sha256=parent_vk,parent_shadow_sha256=FIXTURE_CONTRACT,
                helper_sha256=hashlib.sha256(helper).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    print(json.dumps(apply(parser.parse_args().host_source.resolve(strict=True)), indent=2))
