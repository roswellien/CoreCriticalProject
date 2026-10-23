"""Install exact 16-bit texture conversion through CPU-cached staging chunks.

Apply to the reviewed draw-submission renderer. This preserves image formats,
color expansion, alpha, mip generation, uploads and all game-facing producers.
"""
from pathlib import Path
import argparse


INSERT = """                static const bool staged=[] {
                    const char* value=std::getenv("MW34_TEXTURE_STAGING");
                    if(!value || !*value || !std::strcmp(value,"0"))return false;
                    if(!std::strcmp(value,"1"))return true;
                    throw std::runtime_error("MW34_TEXTURE_STAGING must be 0 or 1");
                }();
                if(staged){
                    const unsigned format=t->format==TexFormat::rgb565?0:t->format==TexFormat::argb1555?1:2;
                    mw34::texture_staging::copy(tp,t->pixels.data(),t->pixels.size(),format);
                    tp+=VkDeviceSize(t->width)*t->height*4;
                    continue;
                }
"""


def apply(host):
    helper=(Path(__file__).parent/'native-overrides'/'texture_staging.hpp').read_bytes()
    path=host/'vk_scene.hpp'
    source=path.read_text()
    for before,after in [
        ('#include "exact_uniform_runs.hpp"','#include "exact_uniform_runs.hpp"\n#include "texture_staging.hpp"'),
        ('                for (size_t i = 0; i < t->pixels.size(); ++i) {',INSERT+'                for (size_t i = 0; i < t->pixels.size(); ++i) {'),
    ]:
        if after in source:
            continue
        if source.count(before)!=1:
            raise RuntimeError('Unexpected texture staging anchor: '+before)
        source=source.replace(before,after,1)
    if path.read_text()!=source:path.write_text(source)
    destination=host/'texture_staging.hpp'
    if not destination.exists() or destination.read_bytes()!=helper:destination.write_bytes(helper)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    apply(parser.parse_args().host)
