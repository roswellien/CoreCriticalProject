"""Apply optional main-world draw distance to a completed native source snapshot."""
from pathlib import Path
import argparse
import shutil


def apply(source: Path):
    header = source / 'mfc_stage.hpp'
    text = header.read_text()
    anchor = ' #include "widescreen_stage.inc"'
    include = ' #include "draw_distance_stage.inc"'
    if include not in text:
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one widescreen include in native snapshot')
        text = text.replace(anchor, anchor + '\n' + include)
    anchor = ' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};'
    hooks = '''
  if(target==0x4f3a70)distance_restore(state.gpr.rcx.dword);
  if(target==0x4f4170||target==0x4f41b0)distance_prepare(state.gpr.rcx.dword);
  if((target==0x4b52c0||target==0x4f6dc0||target==0x4f7030)&&(distance_requested()>800||distance_log()))return distance_camera_body(s,target,p,body);
  if(target==0x49bfd0&&distance_requested()>800){const unsigned sp=state.gpr.rsp.dword;
   if(readable(sp,20)&&load(sp+4)==0x200&&(load(sp+16)==0x5ea600||load(sp+16)==0x5ea628))deny("Extended draw distance exceeds original terrain tiler capacity",target);}
  if((target==0x4f5c80||target==0x4f61b0)&&distance_log()){
   const unsigned camera=load(state.gpr.rsp.dword+4);result=body(s,target,p);distance_tiles(camera);return result;}
'''
    if 'distance_restore(state.gpr.rcx.dword)' not in text:
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one remaster body in native snapshot')
        text = text.replace(anchor, anchor + hooks)
    elif hooks not in text:
        raise RuntimeError('Existing draw-distance hooks differ; inspect before updating')
    provider = source / 'd3d_provider.inc'
    draws = provider.read_text()
    anchor = ' scene_renderer();try{HostInternal hi(*this);host.sren->render(sc,!keep,!lazy);}'
    if ' distance_scene_log(sc);' not in draws:
        if draws.count(anchor) != 1:
            raise RuntimeError('Expected one scene renderer in native snapshot')
        draws = draws.replace(anchor, ' distance_scene_log(sc);\n' + anchor)
    shutil.copyfile(Path(__file__).parent / 'native-overrides/draw_distance_stage.inc', source / 'draw_distance_stage.inc')
    header.write_text(text)
    provider.write_text(draws)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source)
