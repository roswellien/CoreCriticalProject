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
    old_hooks = '''
  if(target==0x4f3a70)distance_restore(state.gpr.rcx.dword);
  if(target==0x4f4170||target==0x4f41b0)distance_prepare(state.gpr.rcx.dword);
  if((target==0x4b52c0||target==0x4f6dc0||target==0x4f7030)&&(distance_requested()>800||distance_log()))return distance_camera_body(s,target,p,body);
  if(target==0x49bfd0&&distance_requested()>800){const unsigned sp=state.gpr.rsp.dword;
   if(readable(sp,20)&&load(sp+4)==0x200&&(load(sp+16)==0x5ea600||load(sp+16)==0x5ea628))deny("Extended draw distance exceeds original terrain tiler capacity",target);}
  if((target==0x4f5c80||target==0x4f61b0)&&distance_log()){
   const unsigned camera=load(state.gpr.rsp.dword+4);result=body(s,target,p);distance_tiles(camera);return result;}
'''
    previous_hooks = old_hooks.replace('(distance_requested()>800||distance_log())',
                              '(distance_requested()>800||distance_fog_requested()||distance_log())')
    previous_hooks += '''  if(target==0x440b00&&(distance_requested()>800||distance_fog_requested()))return distance_marker_body(s,target,p,body);
'''
    hooks = previous_hooks.replace('target==0x4f7030)', 'target==0x4f7030||target==0x4f73f0)')
    hooks += '''  if(target==0x526e10&&(distance_requested()>800||distance_fog_requested()||distance_log()))distance_fog_bound(state.gpr.rcx.dword);
  if(target==0x555a70&&distance_log())distance_fog_consumed();
'''
    for prior in (previous_hooks, old_hooks):
        if prior in text and hooks not in text:
            text = text.replace(prior, hooks)
    if 'distance_restore(state.gpr.rcx.dword)' not in text:
        if text.count(anchor) != 1:
            raise RuntimeError('Expected one remaster body in native snapshot')
        text = text.replace(anchor, anchor + hooks)
    elif hooks not in text:
        raise RuntimeError('Existing draw-distance hooks differ; inspect before updating')
    old_zoom = 'if(wide_on()&&target==0x442f50)return zoom_scene_body(s,target,p,body);'
    new_zoom = 'if(target==0x442f50&&(wide_on()||distance_requested()>800||distance_fog_requested()))return zoom_scene_body(s,target,p,body);'
    if old_zoom in text:
        text = text.replace(old_zoom, new_zoom)
    elif new_zoom not in text:
        raise RuntimeError('Expected authenticated zoom scope in native snapshot')
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
