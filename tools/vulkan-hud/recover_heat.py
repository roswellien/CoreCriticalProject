"""Admit recorded post-update heat geometry, without physical-unit claims."""
import argparse
import json
import math
from pathlib import Path
from verify_heat import verify_heat


def recover_heat(run,monitor):
    evidence=verify_heat(run,monitor)
    for sample in evidence['samples']:
        if sample['phase']!='after_original_update': raise ValueError('Post-update geometry required')
        first,second=sample['argument_values']
        if not 0<=first<=1: raise ValueError('Heat fill outside admitted range')
        top=120-math.ceil(120*first)
        arrow=280-math.ceil(122*max(0,min(1,first+second)))
        if sample['result_crop']!=[0,top,15,120] or sample['result_arrow_y']!=arrow:
            raise ValueError('Heat geometry differs from recovered profile')
    selected=max(evidence['samples'],key=lambda s:s['argument_values'][0])
    return {'scope':'Recorded original heat crop/arrow profile; physical units and live integration unproven',
        'run':evidence['run'],'monitor':evidence['monitor'],'source_sha256':evidence['source_sha256'],
        'trace_sha256':evidence['trace_sha256'],'samples':evidence['samples'],'selected':selected,
        'bar_size':[15,120],'meter_size':[17,122],'snapshot_kind':'recorded_heat_geometry'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('monitor',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();r=recover_heat(a.run,a.monitor);a.output.write_text(json.dumps(r,indent=2))
    print(json.dumps({'samples':len(r['samples']),'selected':r['selected']},indent=2))
