"""Verify bounded original heat-display input observations, without field-unit claims."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct


def verify_heat(run,monitor):
    path=Path(__file__).parents[1]/'graphics-trace/verify.py'
    spec=importlib.util.spec_from_file_location('trace_verifier',path)
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    trace=verifier.verify(run,'draws',monitor)
    source=run/'hud-heat.jsonl';rows=[json.loads(line) for line in source.read_text().splitlines()]
    if not rows or len(rows)>256: raise ValueError('Heat observation budget/empty log')
    samples=[];previous=0;objects=set()
    for index,row in enumerate(rows,1):
        if row['seq']!=index or row['pid']!=trace['pid'] or row['valid'] is not True or row['caller']!=0x43c537:
            raise ValueError('Invalid heat observation identity/sequence')
        if row['phase'] not in ('before_original_update','after_original_update') or row['sampling']!='minimum_60_scenes':
            raise ValueError('Unknown heat sampling phase')
        prefix='prior' if row['phase']=='before_original_update' else 'result'
        if prefix+'_crop' not in row or prefix+'_arrow_y' not in row:
            raise ValueError('Heat geometry does not match observation phase')
        scene=row['completed_scenes']
        if scene<=0 or (previous and scene-previous<60): raise ValueError('Heat scene selection mismatch')
        previous=scene;objects.add(row['object'])
        bits=row['argument_float_bits']
        if len(bits)!=2 or any(type(b)!=int or not 0<=b<=0xffffffff for b in bits):
            raise ValueError('Invalid float bit payload')
        values=[struct.unpack('<f',struct.pack('<I',b))[0] for b in bits]
        if any(not math.isfinite(v) for v in values): raise ValueError('Nonfinite heat input')
        if row['viewport']!=[640,480] or row['target_stride']!=1280:
            raise ValueError('Unadmitted heat target profile')
        if any(not 0<v<=512 for v in row['bar_size']+row['meter_size']):
            raise ValueError('Unadmitted heat image dimensions')
        geometry={'prior_crop':row['prior_crop'],'prior_arrow_y':row['prior_arrow_y']} if row['phase']=='before_original_update' else {
            'result_crop':row['result_crop'],'result_arrow_y':row['result_arrow_y']}
        samples.append({'scene':scene,'phase':row['phase'],'argument_values':values,
            'arrow_display_fraction':max(0,min(1,sum(values))),
            **geometry})
    if len(objects)!=1: raise ValueError('Mixed HUD owners require separate recovery')
    if len({s['phase'] for s in samples})!=1: raise ValueError('Mixed heat observation phases')
    first=[s['argument_values'][0] for s in samples]
    return {'scope':'Recorded heat-display inputs and declared-phase geometry; field units and timing unproven',
        'run':str(run.resolve()),'monitor':str(monitor.resolve()),'object':next(iter(objects)),
        'sample_count':len(samples),'samples':samples,'first_argument_range':[min(first),max(first)],
        'rising_steps':sum(b>a for a,b in zip(first,first[1:])),
        'falling_steps':sum(b<a for a,b in zip(first,first[1:])),
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'trace_sha256':trace['trace_sha256']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('monitor',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();r=verify_heat(a.run,a.monitor);a.output.write_text(json.dumps(r,indent=2))
    print(json.dumps({k:v for k,v in r.items() if k!='samples'},indent=2))
