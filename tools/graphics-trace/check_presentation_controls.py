"""Causal denial controls for the presentation-candidate verifier."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
from verify_presentation import inspect


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    positive=inspect(args.run)
    original=[json.loads(line) for line in (args.run/'presentation.jsonl').read_text().splitlines()]
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='presentation-controls-',dir=args.run.parent) as temporary:
        candidate=Path(temporary)/'run'
        shutil.copytree(args.run,candidate)
        for control in ('missing_event','mixed_pid','failed_flips','open_scene','backward_counter','no_primary','mixed_thread'):
            rows=copy.deepcopy(original)
            if control=='missing_event':rows.pop(0)
            elif control=='mixed_pid':rows[-1]['pid']+=1
            elif control=='failed_flips':
                for row in rows:
                    if row['method']=='Flip':row['hresult']=-1
            elif control=='open_scene':
                for row in rows:
                    if row['method']=='Flip' and row['completed_scenes']>0:row['scene_open']=True
            elif control=='backward_counter':rows[-1]['completed_scenes']=0
            elif control=='no_primary':
                for row in rows:row['caps']&=~512
            elif control=='mixed_thread':rows[-1]['tid']+=1
            (candidate/'presentation.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
            try:inspect(candidate)
            except ValueError:rejected.append(control)
            else:raise AssertionError(f'Control accepted: {control}')
    print(json.dumps({'positive':positive,'rejected_controls':rejected},indent=2))
