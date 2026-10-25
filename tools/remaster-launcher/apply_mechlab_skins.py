"""Move additive skin selection into the retail Mech Lab SKIN_LIST.

Apply to a fresh completed additional-skins host snapshot. The old shortcut
window/input hook is removed; content registration and texture readers remain.
"""
import argparse
from pathlib import Path


def apply(host):
    host=Path(host)
    pending={}
    def edit(name,old,new):
        path=host/name;text=pending.get(path,path.read_text(encoding='utf-8'))
        if new and new in text:return
        if text.count(old)!=1:raise ValueError(f'{name}: missing/ambiguous Mech Lab anchor: {old[:65]}')
        pending[path]=text.replace(old,new,1)
    edit('composition.cpp','#include "additional_skin_picker.hpp"\n','')
    path=host/'photo_replay_stage.inc';text=path.read_text(encoding='utf-8')
    if text.count('    additional_skin_controls();\n')!=2:raise ValueError('Expected old shortcut polling in both presentation paths')
    text=text.replace('    additional_skin_controls();\n','')
    for old in ('        if(std::getenv("MW34_ADDITIONAL_SKINS")&&additional_skin_chord_down())b[0x42]=0;\n',
                '            if(ofs==0x42&&std::getenv("MW34_ADDITIONAL_SKINS")&&additional_skin_chord_down())continue;\n'):
        if text.count(old)!=1:raise ValueError('Expected old shortcut input filter')
        text=text.replace(old,'')
    pending[path]=text
    edit('mfc_stage.hpp','#include "additional_skins_stage.inc"',
         '#include "additional_skins_stage.inc"\n #include "mechlab_skins_stage.inc"')
    edit('mfc_stage.hpp','void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};',
         'void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};\n'
         '  if(target==0x44cf70||target==0x44b1c0)return mechlab_skin_body(s,target,p,body);\n'
         '  if(target==0x448a20)mechlab_skin_closed();')
    edit('body_dispatch.hpp','0x448960U,0x448a20U,','0x448960U,0x448a20U,0x44b1c0U,0x44cf70U,')
    for name in ('additional_skins_stage.inc','mechlab_skins_stage.inc'):
        pending[host/name]=(Path(__file__).parent/'native-overrides'/name).read_text(encoding='utf-8')
    for path,text in pending.items():path.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host',type=Path);apply(p.parse_args().host)
