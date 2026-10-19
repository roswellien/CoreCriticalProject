"""Install the optional scoped turret aiming correction in a native snapshot."""
from pathlib import Path
import argparse
import shutil


def apply(source: Path):
    path = source / 'mfc_stage.hpp'
    text = path.read_text()
    math_include = '#include "turret_aim_math.hpp"'
    if math_include not in text:
        anchor = '#include "vk_scene.hpp"'
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one global scene include')
        text = text.replace(anchor, anchor + '\n' + math_include)
    include = ' #include "turret_aim_stage.inc"'
    if include not in text:
        anchor = ' #include "draw_distance_stage.inc"'
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one draw-distance include')
        text = text.replace(anchor, anchor + '\n' + include)
    wrapper = ''' void*remaster_body(State*s,unsigned target,void*p,Body body){
  return turret_aim_body(s,target,p,[&]{return remaster_body_inner(s,target,p,body);});
 }
'''
    if wrapper not in text:
        old = ' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};'
        new = ' void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};'
        anchor = ' void*enter(State*s,unsigned target,void*p,Body body)'
        if text.count(old) != 1 or text.count(anchor) != 1:
            raise RuntimeError('Expected known normal native dispatch layout')
        text = text.replace(old, new).replace(anchor, wrapper + anchor)
    for name in ('turret_aim_math.hpp', 'turret_aim_stage.inc'):
        shutil.copyfile(Path(__file__).parent / 'native-overrides' / name, source / name)
    path.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source)
