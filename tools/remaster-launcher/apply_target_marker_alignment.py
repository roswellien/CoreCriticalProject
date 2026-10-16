"""Apply scoped zoom target-marker display corrections to a fresh r12 host."""
from pathlib import Path
import argparse
import shutil

def replace(path,old,new,count=1):
    s=path.read_text(encoding='utf-8')
    if s.count(old)!=count:
        raise ValueError(f'{path.name}: expected {count} exact source matches')
    path.write_text(s.replace(old,new),encoding='utf-8',newline='\n')

def apply(host):
    replace(host/'mfc_stage.hpp',' #include "zoom_alignment_stage.inc"',
            ' #include "zoom_alignment_stage.inc"\n #include "target_marker_stage.inc"')
    replace(host/'mfc_stage.hpp',' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};',
            ''' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};
  if(wide_on()&&(target==0x440b00||target==0x441490||target==0x440510||
     (target_marker_update_owner&&(target==0x53cf10||target==0x40da30))))return target_marker_body(s,target,p,body);''')
    replace(host/'widescreen_stage.inc',
            'case 0x4414b8:case 0x4414c8:case 0x4414d8:case 0x44154b:case 0x44155b:return WideWorld;',
            '''case 0x4414b8:case 0x4414c8:case 0x4414d8:return target_marker_zoom()?WideZoom:WideWorld;
   case 0x44154b:case 0x44155b:return WideWorld;''')
    replace(host/'zoom_alignment_stage.inc',
            ' if(!wide_on()||command.hud_role!=WideZoom)return;',
            ''' if(!wide_on()||command.hud_role!=WideZoom)return;
 if(target_marker_draw_owner){command.zoom_anchor=target_marker_anchor();command.zoom_anchor_known=true;return;}''')
    replace(host/'gpu_hud.inc',
            ' const float zoom_anchor=wide_on()&&role==WideZoom?zoom_display_anchor():0.f;',
            ' const float zoom_anchor=wide_on()&&role==WideZoom?(target_marker_draw_owner?target_marker_anchor():zoom_display_anchor()):0.f;')
    shutil.copyfile(Path(__file__).parent/'native-overrides/target_marker_stage.inc',host/'target_marker_stage.inc')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
