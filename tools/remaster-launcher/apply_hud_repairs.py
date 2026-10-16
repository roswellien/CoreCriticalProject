"""Apply the scoped HUD repairs to a private r8-compatible authored host tree.

No generated body or media is copied into this tool. Frozen builds are never
edited in place; pass the fresh candidate's host-source directory.
"""
from pathlib import Path
import argparse
import shutil


def replace_once(path, old, new):
    text = path.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise ValueError(f'{path.name}: expected one exact source contract')
    path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')


def apply(host):
    replace_once(host / 'mfc_stage.hpp', ' #include "widescreen_stage.inc"',
                 ' #include "widescreen_stage.inc"\n #include "hud_deferred_stage.inc"')
    replace_once(host / 'mfc_stage.hpp',
                 ' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};',
                 ''' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};
  if(wide_on()&&target==0x57bf80)return hud_panel_body(s,target,p,body);
  if(wide_on()&&target==0x57e110){
   try{result=body(s,target,p);}catch(...){hud_deferred_panels.clear();throw;}
   hud_deferred_panels.clear();return result;
  }''')
    replace_once(host / 'd3d_provider.inc',
                 'c.hud_role=wide_hud_role();if(!override_suppress_draw())',
                 'c.hud_role=hud_deferred_role(type,verts,vcount,wide_hud_role());if(!override_suppress_draw())')
    replace_once(host / 'mesh_override_stage.inc',
                 'OverrideScope override_begin(unsigned node){',
                 '''// These exact returns surround the original per-part condition schematic.
// Keep its original geometry/material state; replacements still draw in-world.
bool override_status_preview() const {
 for(unsigned i=depth;i>0;--i)if(returns[i-1]==0x441480||returns[i-1]==0x442a87)return true;
 return false;
}
OverrideScope override_begin(unsigned node){''')
    replace_once(host / 'mesh_override_stage.inc',
                 'o.scope={};if(!override_enabled())return previous;override_load();',
                 'o.scope={};if(!override_enabled()||override_status_preview())return previous;override_load();')
    shutil.copyfile(Path(__file__).parent / 'native-overrides/hud_deferred_stage.inc',
                    host / 'hud_deferred_stage.inc')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
