"""Extend an existing completed native host snapshot without replacing other work.

This private definition-loading boundary does not advertise a chassis capability:
selection, model identity, arbitrary metadata and save/load still need integration.
"""
import argparse
from pathlib import Path


def apply(source):
    source = Path(source)
    assets = Path(__file__).parent / 'native-overrides'
    edits = {
        'composition.cpp': [
            ('#include "additional_skins.hpp"', '#include "additional_skins.hpp"\n#include "additional_chassis.hpp"')],
        'mfc_stage.hpp': [
            ('if(const Body b=find(target)){state.gpr.rip.dword=target;++bodies;return b(s,target,p);}',
             'if(const Body b=find(target)){state.gpr.rip.dword=target;++bodies;'
             'if(chassis_target(target))return remaster_body(s,target,p,b);return b(s,target,p);}'),
            ('unsigned below=0){\n  const Body b=find(target);',
             'unsigned below=0,bool adapted=false){\n  const Body b=find(target);'),
            ('try{(void)b(&state,target,token_ptr);}catch(const GuestReturn&r)',
             'try{if(adapted)(void)remaster_body(&state,target,token_ptr,b);else (void)b(&state,target,token_ptr);}catch(const GuestReturn&r)'),
            ('#include "mechlab_skins_stage.inc"', '#include "mechlab_skins_stage.inc"\n #include "additional_chassis_stage.inc"\n #include "chassis_selection_stage.inc"'),
            ('void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};',
             'void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};\n'
             '  if(target==0x4eaea0)chassis_retire_root(state.gpr.rcx.dword);\n'
             '  if(target==0x408b40||target==0x48aac0||target==0x48a930||target==0x44ffc0||target==0x449220)return chassis_selection_body(s,target,p,body);\n'
             '  if(chassis_target(target))return chassis_body(s,target,p,body);')],
        'body_dispatch.hpp': [
            ('inline constexpr unsigned targets[]{',
             'inline constexpr unsigned targets[]{0x408b40U,0x41e9a0U,0x41df10U,0x449220U,0x48aac0U,0x48a930U,0x44ffc0U,0x4844b0U,0x4845f0U,0x484650U,0x484670U,0x4846a0U,0x4846e0U,0x484700U,0x484720U,')]
    }
    prepared = {}
    for name, replacements in edits.items():
        text = (source / name).read_text(encoding='utf-8')
        for old, new in replacements:
            if text.count(old) != 1 or new in text:
                raise ValueError('Additional chassis patch does not match source: ' + name)
            text = text.replace(old, new)
        prepared[name] = text
    for name, text in prepared.items():
        (source / name).write_text(text, encoding='utf-8')
    for name in ('additional_chassis.hpp', 'additional_chassis_stage.inc', 'chassis_selection_stage.inc'):
        (source / name).write_bytes((assets / name).read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)
