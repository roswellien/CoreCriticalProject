"""Negative controls for recorded text/image destination admission."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
from observe_state import recover


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    p.add_argument('monitor',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    state=recover(a.run,a.monitor)
    rows=[json.loads(line) for line in (a.run/'hud-draw.jsonl').read_text().splitlines()]
    controls={}
    changed=copy.deepcopy(rows);changed[0]['pid']+=1;controls['mixed_pid']=changed
    changed=copy.deepcopy(rows);changed[0]['seq']=2;controls['reordered_draw']=changed
    changed=copy.deepcopy(rows);changed[0]['dispatch']=0x55b250;controls['unrecovered_dispatch']=changed
    changed=copy.deepcopy(rows)
    next(r for r in changed if bytes.fromhex(r['text_hex']).decode('cp1252').endswith('\nKPH'))['rectangle_argument'][0]=1
    controls['unrecovered_source_crop']=changed
    rejected=[]
    with tempfile.TemporaryDirectory() as temporary:
        directory=Path(temporary)/'run';shutil.copytree(a.run,directory)
        for name,candidate in controls.items():
            (directory/'hud-draw.jsonl').write_text('\n'.join(json.dumps(r) for r in candidate))
            try: recover(directory,a.monitor)
            except ValueError as error: rejected.append({'control':name,'reason':str(error)})
            else: raise ValueError(f'{name} admitted')
    report={'scope':'Recorded placement admission only; no live replacement or full-frame order',
            'placement':state['placement'],'rejected_controls':rejected}
    a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':main()
