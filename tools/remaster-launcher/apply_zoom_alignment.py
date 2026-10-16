"""Apply the display-only zoom scene anchor repair to a fresh r9 host tree."""
from pathlib import Path
import argparse
import shutil


def replace(path, old, new, count=1):
    text = path.read_text(encoding='utf-8')
    if text.count(old) != count:
        raise ValueError(f'{path.name}: expected {count} exact source matches')
    path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')


def apply(host):
    replace(host/'mfc_stage.hpp', 'unsigned hud_role{};};',
            'unsigned hud_role{};float zoom_anchor{};bool zoom_anchor_known{};};')
    replace(host/'mfc_stage.hpp', ' #include "hud_deferred_stage.inc"',
            ' #include "hud_deferred_stage.inc"\n #include "zoom_alignment_stage.inc"')
    replace(host/'mfc_stage.hpp',
            ' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};',
            ''' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};
  if(wide_on()&&target==0x442f50)return zoom_scene_body(s,target,p,body);''')
    replace(host/'d3d_provider.inc',
            'c.hud_role=hud_deferred_role(type,verts,vcount,wide_hud_role());',
            'c.hud_role=hud_deferred_role(type,verts,vcount,wide_hud_role());zoom_capture_command(c);')
    replace(host/'mesh_override_stage.inc',
            'draw.hud_role=wide_hud_role();',
            'draw.hud_role=wide_hud_role();zoom_capture_command(draw);')
    replace(host/'d3d_provider.inc', 'wide_adapt_tl(sc,dr,c.hud_role);',
            'wide_adapt_tl(sc,dr,c.hud_role,c.zoom_anchor_known?&c.zoom_anchor:nullptr);',2)
    replace(host/'gpu_hud.inc',
            ' wide_adapt_tl(hud_sc,dr,role,center_hint);',
            ''' const float zoom_anchor=wide_on()&&role==WideZoom?zoom_display_anchor():0.f;
 wide_adapt_tl(hud_sc,dr,role,role==WideZoom?&zoom_anchor:center_hint);''')
    replace(host/'widescreen_stage.inc',
            ' const float zoom_a=float(d.scissor.offset.x)+float(d.scissor.extent.width)*.5f;',
            ''' // The original D3D scissor is full-target even for zoom. Its midpoint
 // is a clipping bound, not the engine zoom camera's projection center.
 if(role==WideZoom&&!center_hint)deny("Widescreen zoom draw has no captured camera anchor",role);
 const float zoom_a=role==WideZoom?*center_hint:0.f;
 if(FILE*log=wide_log_file();log&&role==WideZoom&&host.frames%100==0){static unsigned last=~0U;if(last!=host.frames){last=host.frames;
  std::fprintf(log,"zoom-adapt frame %u target %ux%u scissor %d,%d %ux%u old-anchor %.9g camera-anchor %.9g\\n",host.frames,sc.width,sc.height,d.scissor.offset.x,d.scissor.offset.y,d.scissor.extent.width,d.scissor.extent.height,double(float(d.scissor.offset.x)+float(d.scissor.extent.width)*.5f),double(zoom_a));std::fflush(log);}}
''')
    shutil.copyfile(Path(__file__).parent/'native-overrides/zoom_alignment_stage.inc',
                    host/'zoom_alignment_stage.inc')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
