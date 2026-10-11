"""Recover displayed speed text from identity-verified original text-cache calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


def recover(run, monitor):
    path=Path(__file__).parents[1]/'graphics-trace/verify.py'
    spec=importlib.util.spec_from_file_location('trace_verifier',path)
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    trace=verifier.verify(run,'draws',monitor)
    source=run/'hud-text.jsonl'
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    if not rows or len(rows)>256: raise ValueError('Text observer budget exceeded or empty')
    speed=[]
    for index,row in enumerate(rows,1):
        if row['seq']!=index or row['pid']!=trace['pid'] or row['valid'] is not True:
            raise ValueError('Invalid or discontinuous text observation')
        if row['caller'] not in (0x5a0895,0x5a0b48,0x5a0bb8) or row['codepage']!=1252:
            raise ValueError('Unsupported text source or encoding')
        text=bytes.fromhex(row['text_hex']).decode('cp1252')
        face=bytes.fromhex(row['font_face_hex']).decode('cp1252')
        if row['caller']==0x5a0bb8 and re.fullmatch(r'-?\d+\.\d\nKPH',text):
            if face!='Arial' or row['font_height']!=-8 or row['flags']!=0 or row['result']<=0:
                raise ValueError('Unsupported observed speed font/drawing contract')
            left,top,right,bottom=row['rect_after']
            if (left,top)!=(0,0) or not (0<right<=512 and 0<bottom<=128):
                raise ValueError('Unsupported local text-cache bounds')
            speed.append({'text':text,'displayed_speed_kph':float(text.split('\n')[0]),
                          'logicalWidth':right,'logicalHeight':bottom,'fontFace':face,
                          'fontHeight':row['font_height'],'fontWeight':row['font_weight'],
                          'textColor':row['text_color'],'logicalLineHeight':row['result']/2,
                          'source_event':row['seq'],'completed_scenes':row['completed_scenes']})
    if not speed: raise ValueError('No admitted displayed speed observation')
    placement=None
    draw_source=run/'hud-draw.jsonl'
    draw_sha=None
    if draw_source.exists():
        draws=[json.loads(line) for line in draw_source.read_text().splitlines()]
        if not draws or len(draws)>512: raise ValueError('HUD draw observer budget')
        candidates=[]
        for index,row in enumerate(draws,1):
            if row['seq']!=index or row['pid']!=trace['pid'] or row['valid'] is not True:
                raise ValueError('Invalid or discontinuous HUD draw')
            if row['caller'] not in (0x5a116e,0x5a1197) or row['dispatch']!=0x55b3c0 or row['viewport']!=[640,480] or row['target_stride']!=1280:
                raise ValueError('Unrecovered HUD draw/target profile')
            text=bytes.fromhex(row['text_hex']).decode('cp1252')
            if re.fullmatch(r'-?\d+\.\d\nKPH',text):
                matches=[s for s in speed if s['text']==text and s['completed_scenes']<=row['completed_scenes']]
                if not matches: continue
                matched=matches[-1]
                size=[matched['logicalWidth'],matched['logicalHeight']]
                if row['flags']!=0 or row['font_height']!=-8 or row['image_size']!=size or row['rectangle_argument']!=[0,0,*size]:
                    raise ValueError('Unrecovered speed crop/size contract')
                if not (0<=row['x'] and 0<=row['y'] and row['x']+size[0]<=640 and row['y']+size[1]<=480):
                    raise ValueError('Speed draw outside admitted source viewport')
                candidates.append((matched,row))
        if not candidates: raise ValueError('No text/placement correlation in same run')
        selected,draw=candidates[-1]
        placement={'source_viewport':[640,480],'x':draw['x'],'y':draw['y'],'source_rectangle':draw['rectangle_argument'],
                   'draw_event':draw['seq'],'object':draw['object'],'image':draw['image'],
                   'scope':'Observed final speed destination; ordering covers text draws only',
                   'widescreen_anchor':'right-top is a host policy for the speed gauge; only 640x480 destination is observed'}
        draw_sha=hashlib.sha256(draw_source.read_bytes()).hexdigest()
    else:
        selected=speed[-1]
    return {'scope':'Recorded original displayed speed; internal telemetry and full-frame ordering unproven',
            'speed_samples':speed,'selected_speed':selected,'placement':placement,'draw_source_sha256':draw_sha,
            'run':str(run.resolve()),'monitor':str(monitor.resolve()),
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'trace_sha256':trace['trace_sha256'],'snapshot_kind':'recorded_display_text'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    p.add_argument('monitor',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();state=recover(a.run,a.monitor);a.output.write_text(json.dumps(state,indent=2))
    print(json.dumps({'speed_samples':len(state['speed_samples']),'selected_speed':state['selected_speed']},indent=2))
