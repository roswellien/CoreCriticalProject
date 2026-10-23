"""Remove empty inline emission payloads from host-only Draw records.

Keep every source lookup, count limit, float bit, zero tail and shader upload.
Only nonempty payloads get scene-owned indexed storage; no asset alias is kept.
"""
import argparse,hashlib,json
from pathlib import Path

CONTRACTS={
 'vk_scene.hpp':'cdcdb0a81cc4d0221a84aefdfecaf5d5c61fb9190b3eeac7f579f725e1101522',
 'd3d_provider.inc':'6fff0284add87210268367a5fbff286ffc3004ea3de3b3bae7c61c4d15ebfb87',
}
def apply(host):
 for name,pin in CONTRACTS.items():
  if hashlib.sha256((host/name).read_bytes()).hexdigest()!=pin:raise ValueError(name+': emission contract changed; review required')
 destination=host/'draw_emissions.hpp'
 if destination.exists():raise ValueError('Sparse emission storage already applied')
 texts={name:(host/name).read_text(encoding='utf-8') for name in CONTRACTS}
 def replace(name,old,new):
  if texts[name].count(old)!=1:raise ValueError('Emission anchor changed: '+old)
  texts[name]=texts[name].replace(old,new)
 replace('vk_scene.hpp','#include "exact_uniform_runs.hpp"','#include "exact_uniform_runs.hpp"\n#include "draw_emissions.hpp"')
 replace('vk_scene.hpp','''    std::array<float, 4> emission_params{};
    std::array<std::array<float, 4>, 32> emission_regions{};''','''    std::uint32_t emission_index{mw34::submission::DrawEmissions::none};''')
 replace('vk_scene.hpp','    std::vector<Draw> draws;','    std::vector<Draw> draws;\n    mw34::submission::DrawEmissions emissions;')
 replace('vk_scene.hpp','''                    u.emission_params = draw.emission_params;
                    u.emission_regions = draw.emission_regions;''','''                    s.emissions.apply(draw.emission_index, u);''')
 replace('d3d_provider.inc','dr.emission_params={float(count),fixture->intensity,0,0};for(size_t i=0;i<count;++i)dr.emission_regions[i]=fixture->emission_regions[i];',
         'dr.emission_index=sc.emissions.capture({float(count),fixture->intensity,0,0},std::span<const mw34::submission::DrawEmissions::Float4>(fixture->emission_regions.data(),count));')
 replace('vk_scene.hpp','    std::uint64_t fxaa_passes{}, af_samplers{}, mip_levels_uploaded{};',
         '    std::uint64_t fxaa_passes{}, af_samplers{}, mip_levels_uploaded{};\n    std::uint64_t emission_draw_records{}, emission_payloads{};')
 replace('vk_scene.hpp','        // Descriptor sets: one per distinct (texture, sampler).',
         '        emission_draw_records += s.draws.size();emission_payloads += s.emissions.size();\n        // Descriptor sets: one per distinct (texture, sampler).')
 replace('vk_scene.hpp','        model_buffers.clear();','''        model_buffers.clear();
        if (emission_draw_records) std::fprintf(stderr,
            "Draw emission storage: %llu draw records, %llu payloads, Draw size %zu bytes\\n",
            (unsigned long long)emission_draw_records,(unsigned long long)emission_payloads,sizeof(Draw));''')
 helper=(Path(__file__).parent/'native-overrides/draw_emissions.hpp').read_bytes()
 for name,text in texts.items():(host/name).write_text(text,encoding='utf-8')
 destination.write_bytes(helper)
 return dict(parent_contracts=CONTRACTS,helper_sha256=hashlib.sha256(helper).hexdigest())

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host_source',type=Path)
 print(json.dumps(apply(parser.parse_args().host_source.resolve(strict=True)),indent=2))
