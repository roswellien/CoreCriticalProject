"""Verify recorded same-scene counter updates through the isolated Vulkan pass."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from PIL import Image,ImageChops
from prepare import build,ROOT
from recover_counters import counters
from verify import oracle


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('monitor',type=Path)
    p.add_argument('components',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--canvas-package',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    state=counters(a.run,a.monitor);state_path=a.output/'counter-state.json'
    state_path.write_text(json.dumps(state,indent=2))
    common=set.intersection(*[set(s['completed_scenes'] for s in row['render_samples']) for row in state['rows']])
    scenes=sorted(common)
    if len(scenes)<2: raise ValueError('At least two same-scene snapshots required')
    executable=ROOT/'build/vulkan-replay/Release/mw34_vulkan_replay.exe'
    env=os.environ.copy();env['VK_LAYER_PATH']=str(ROOT/'local/tools/vulkan-sdk-portable/Bin')
    env['VK_IMPLICIT_LAYER_PATH']=str(ROOT/'local/tools/empty-implicit-layers')
    results=[]
    for scene,w,h,density in [(s,640,480,1) for s in scenes]+[(scenes[-1],3440,1440,3)]:
        out=a.output/f'scene-{scene}-{w}x{h}'
        receipt=build(a.components,out,w,h,1,density,a.canvas_package,counter_state=state_path,counter_scene=scene)
        process=subprocess.run([str(executable),str((out/'hud.replay').resolve()),str(ROOT/'build/vulkan-replay'),
            str((out/'vulkan.ppm').resolve()),'0.5','captured','1','d32','rgba8'],env=env,capture_output=True,text=True,timeout=30)
        (out/'run.txt').write_text(process.stdout+process.stderr)
        if process.returncode or 'zero validation warnings/errors' not in process.stdout: raise ValueError('Vulkan sequence execution failed')
        actual=Image.open(out/'vulkan.ppm').convert('RGB');expected=oracle(out,receipt)
        error=max(high for low,high in ImageChops.difference(actual,expected).getextrema())
        if error>2: raise ValueError('Sequence GPU/oracle mismatch')
        actual.save(out/'vulkan.png')
        values=[next(s['displayed_value'] for s in row['render_samples'] if s['completed_scenes']==scene) for row in state['rows']]
        results.append({'scene':scene,'viewport':[w,h],'values':values,'maximum_channel_error':error,
            'image_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),
            'package_sha256':hashlib.sha256((out/'hud.replay').read_bytes()).hexdigest()})
    hashes=[r['package_sha256'] for r in results if r['viewport']==[640,480]]
    if len(set(hashes))!=len(scenes): raise ValueError('Counter changes did not change rendered packages')
    if len({r['image_sha256'] for r in results if r['viewport']==[640,480]})!=len(scenes):
        raise ValueError('Counter changes did not change GPU images')
    try:build(a.components,a.output/'invalid-scene',640,480,1,1,a.canvas_package,counter_state=state_path,counter_scene=-1)
    except ValueError: pass
    else: raise ValueError('Unobserved scene admitted')
    report={'scope':'Recorded same-scene counter snapshots; no live updates, timing or full-HUD synchronization',
        'cases':results,'validation_messages':0,'unobserved_scene_rejected':True,
        'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (a.output/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':main()
