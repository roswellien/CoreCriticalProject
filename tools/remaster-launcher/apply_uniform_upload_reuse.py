"""Write each consecutive byte-identical lighting uniform run once per scene.

Preserve every shader-input calculation, guest validation, draw order, buffer
allocation guard and existing scene fence. Only upload slots/offsets change.
"""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACTS = {
    'vk_scene.hpp': 'cdcdb0a81cc4d0221a84aefdfecaf5d5c61fb9190b3eeac7f579f725e1101522',
    'exact_uniform_runs.hpp': 'be887d512df7601d9065b6b0e93a84dc6aac4c2a3b24a371dbcd02ac8cf578d8',
}

def apply(host):
    for name, expected in CONTRACTS.items():
        if hashlib.sha256((host/name).read_bytes()).hexdigest() != expected:
            raise ValueError(name + ': uniform upload contract changed; review required')
    destination = host/'exact_uniform_uploads.hpp'
    if destination.exists():
        raise ValueError('Uniform upload reuse already applied')
    path = host/'vk_scene.hpp'
    text = path.read_text(encoding='utf-8')
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('Uniform upload anchor changed: ' + old)
        text = text.replace(old, new)
    replace('#include "exact_uniform_runs.hpp"', '#include "exact_uniform_uploads.hpp"')
    replace('mw34::submission::ExactUniformRuns<mw34::sun::Uniform> uniformRuns;',
            'mw34::submission::ExactUniformUploads<mw34::sun::Uniform> uniformRuns(\n            mw34::submission::uniform_upload_reuse_enabled());')
    replace('''                    sunUniformIds[at] = uniformRuns.identify(u);
                    std::memcpy(static_cast<unsigned char *>(sunBuffer.mapped) + at * sunStride, &u,
                                sizeof(u));''',
            '''                    sunUniformIds[at] = uniformRuns.capture(u, at, sunStride, sunBuffer.mapped);''')
    replace('''        // Descriptor sets: one per distinct (texture, sampler).''',
            '''        uniform_upload_values += uniformRuns.values;
        uniform_upload_writes += uniformRuns.writes;
        // Descriptor sets: one per distinct (texture, sampler).''')
    replace('const std::uint32_t offset = std::uint32_t(o.index * sunStride);',
            'const std::uint32_t offset = uniformRuns.offset(sunUniformIds[o.index], o.index, sunStride);')
    replace('    std::uint64_t fxaa_passes{}, af_samplers{}, mip_levels_uploaded{};',
            '    std::uint64_t fxaa_passes{}, af_samplers{}, mip_levels_uploaded{};\n    std::uint64_t uniform_upload_values{}, uniform_upload_writes{};')
    replace('        model_buffers.clear();', '''        model_buffers.clear();
        if (uniform_upload_values) std::fprintf(stderr,
            "Lighting uniforms: %llu values, %llu mapped writes, %llu bytes written\\n",
            (unsigned long long)uniform_upload_values, (unsigned long long)uniform_upload_writes,
            (unsigned long long)(uniform_upload_writes * sizeof(mw34::sun::Uniform)));''')
    helper = (Path(__file__).parent/'native-overrides/exact_uniform_uploads.hpp').read_bytes()
    path.write_text(text, encoding='utf-8')
    destination.write_bytes(helper)
    return dict(parent_contracts=CONTRACTS, helper_sha256=hashlib.sha256(helper).hexdigest())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    print(json.dumps(apply(parser.parse_args().host_source.resolve(strict=True)), indent=2))
