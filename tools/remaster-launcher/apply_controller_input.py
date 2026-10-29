"""Add opt-in SDL3 input to a reviewed native host without changing translated game bodies."""
from pathlib import Path
import argparse
import shutil


def apply(source: Path):
    path = source / 'mfc_stage.hpp'
    text = path.read_text(encoding='utf-8')
    if '#include "controller_input.hpp"' not in text:
        anchor = '#include "vk_scene.hpp"'
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one renderer include in native stage')
        text = text.replace(anchor, anchor + '\n#include "controller_input.hpp"')
    if ' #include "controller_stage.inc"' not in text:
        anchor = ' void*remaster_body(State*s,unsigned target,void*p,Body body){'
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one reviewed native dispatch wrapper')
        start = text.index(anchor)
        end = text.index('\n }', start) + len('\n }')
        original = text[start:end].replace('void*remaster_body(', 'void*controller_next_body(', 1)
        wrapper = ('\n #include "controller_stage.inc"\n'
                   ' void*remaster_body(State*s,unsigned target,void*p,Body body){\n'
                   '  return controller_body(s,target,p,[&]{return controller_next_body(s,target,p,body);});\n }')
        text = text[:start] + original + wrapper + text[end:]
    # SDL owns controllers while opted in. Never enumerate a second legacy joystick to the guest.
    old = 'auto&st=*c.st;if(!st.callback_fault.empty())return DIENUM_STOP;'
    new = old + '\n       if(st.controller_requested()&&(d->dwDevType&0xff)==DIDEVTYPE_JOYSTICK)return DIENUM_CONTINUE;'
    if new not in text:
        if text.count(old) != 2:
            raise RuntimeError('Expected reviewed input device/object enumeration callbacks')
        text = text.replace(old, new, 1)
    old_create = 'if(n=="CreateDevice"){const GUID g=guest_guid(arg(1));const unsigned out=arg(2);'
    new_create = old_create + 'if(controller_requested()&&!IsEqualGUID(g,GUID_SysKeyboard)&&!IsEqualGUID(g,GUID_SysMouse)){if(!writable(out,4))deny("Controller CreateDevice output outside memory contract",out);store(out,0);return done(unsigned(DIERR_DEVICENOTREG),4);}'
    if new_create not in text:
        if text.count(old_create) != 1:
            raise RuntimeError('Expected reviewed DirectInput device creation')
        text = text.replace(old_create,new_create,1)
    for name in ('controller_math.hpp', 'controller_input.hpp', 'controller_stage.inc',
                 'controller_virtual_test.hpp', 'joystick_selection.hpp'):
        shutil.copyfile(Path(__file__).parent / 'native-overrides' / name, source / name)
    path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source)
