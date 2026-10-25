"""Keep retained-world validation callbacks out of ordinary host draw records."""
import argparse
from pathlib import Path


def apply(host):
    changes = {
        'vk_scene.hpp': [
            ('#include "draw_emissions.hpp"',
             '#include "draw_emissions.hpp"\n#include "shadow_validators.hpp"'),
            ('    std::function<bool()> shadow_valid;',
             '    std::uint32_t shadow_validation{mw34::submission::ShadowValidators::none};'),
            ('    mw34::submission::DrawEmissions emissions;',
             '    mw34::submission::DrawEmissions emissions;\n    mw34::submission::ShadowValidators shadow_validators;')],
        'd3d_provider.inc': [
            ('dr.shadow_valid=[this,proof]{SunCaptureFp preserve;return fixture_proof_valid(*proof);};',
             'dr.shadow_validation=sc.shadow_validators.capture([this,proof]{SunCaptureFp preserve;return fixture_proof_valid(*proof);});')],
        'fixture_shadow_stage.inc': [
            ('if(instance.world&&draw.shadow_source&&draw.shadow_valid){key={draw.shadow_source,0};caster.valid=draw.shadow_valid;}',
             'if(instance.world&&draw.shadow_source&&scene.shadow_validators.has(draw.shadow_validation)){key={draw.shadow_source,0};caster.valid=scene.shadow_validators.get(draw.shadow_validation);}')]
    }
    pending = {}
    for name, replacements in changes.items():
        path = host / name
        source = path.read_text()
        for before, after in replacements:
            if source.count(after) == 1:
                continue
            if source.count(before) != 1:
                raise ValueError(f'{name}: shadow validation anchor changed: {before[:70]}')
            source = source.replace(before, after, 1)
        pending[path] = source
    helper = Path(__file__).parent / 'native-overrides/shadow_validators.hpp'
    data = helper.read_bytes()
    for path, source in pending.items():
        if path.read_text() != source:
            path.write_text(source)
    destination = host / helper.name
    if not destination.exists() or destination.read_bytes() != data:
        destination.write_bytes(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
