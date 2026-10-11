"""Recover recorded weapon-area display counters; internal ammunition is unproven."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from observe_state import recover


def counters(run, monitor):
    evidence=recover(run,monitor)  # Identity, provider, shutdown and all draw rows.
    source=run/'hud-draw.jsonl'
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    text_source=run/'hud-text.jsonl'
    cache=[json.loads(line) for line in text_source.read_text().splitlines()]
    groups={}
    for row in rows:
        if row['x']!=610 or row['y'] not in (70,80,90,100): continue
        text=bytes.fromhex(row['text_hex']).decode('cp1252')
        if not re.fullmatch(r' \d{2}',text):
            raise ValueError('Unsupported recorded counter text')
        if row['font_height']!=-10 or row['flags']!=0 or row['image_size']!=[15,13] or row['rectangle_argument']!=[0,0,15,13]:
            raise ValueError('Unsupported recorded counter drawing contract')
        key=(row['object'],row['y'])
        groups.setdefault(key,[]).append({'text':text,'displayed_value':int(text),
            'draw_event':row['seq'],'completed_scenes':row['completed_scenes'],
            'image':row['image'],'destination':[610,row['y'],15,13]})
    if len(groups)!=4 or sorted(y for obj,y in groups)!=[70,80,90,100]:
        raise ValueError('Four independent observed rows required')
    result=[]
    for (obj,y),samples in sorted(groups.items(),key=lambda pair:pair[0][1]):
        values=[sample['displayed_value'] for sample in samples]
        if len(values)<2 or any(b!=a-1 for a,b in zip(values,values[1:])):
            raise ValueError('No admitted unit-decrement sequence')
        correlated=[]
        for sample in samples:
            matches=[r for r in cache if r['caller']==0x5a0bb8 and r['flags']==0 and
                     bytes.fromhex(r['text_hex']).decode('cp1252')==sample['text'] and
                     r['completed_scenes']<=sample['completed_scenes'] and
                     r['font_height']==-10 and r['font_face_hex']=='417269616c' and
                     r['rect_after']==[0,0,15,13] and r['result']==13]
            if matches:
                main=matches[-1]
                correlated.append(dict(sample,logicalWidth=15,logicalHeight=13,fontHeight=-10,
                    fontWeight=main['font_weight'],textColor=main['text_color'],logicalLineHeight=13,
                    text_event=main['seq']))
        if not correlated: raise ValueError('No admitted counter font/cache correlation')
        result.append({'object':obj,'source_y':y,'samples':samples,'render_samples':correlated,'selected_render_sample':correlated[-1],
                       'observed_decrements':len(samples)-1})
    return {'scope':'Recorded displayed counter transitions; ammunition fields, weapon mapping and heat remain unproven',
            'run':evidence['run'],'monitor':evidence['monitor'],
            'draw_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'text_source_sha256':hashlib.sha256(text_source.read_bytes()).hexdigest(),
            'rows':result,'snapshot_kind':'recorded_display_counters',
            'placement_policy':'Only original 640x480 observed; future widescreen anchoring is host policy'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path);parser.add_argument('monitor',type=Path)
    parser.add_argument('output',type=Path);args=parser.parse_args()
    result=counters(args.run,args.monitor)
    args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps({'rows':len(result['rows']),
                     'observed_decrements':[r['observed_decrements'] for r in result['rows']]}))
