"""Bind the independent original/source observer to the fresh boundary repair."""
from pathlib import Path
import argparse, importlib.util, json, traceback
import sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('repaired_joint27_raw',Path(__file__).with_name('observe.py'))
J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
original_receipts=J.source_receipts

def source_receipts(original_path,native_run,pe,game,raw_iat):
    # All frozen-source and literal original associations still undergo the
    # existing separately independent review. Fresh execution bindings follow.
    initial=original_receipts(original_path,J.ROOT/'reports/m4-joint27-startup/capture-r1',pe,game,raw_iat)
    for p,h in json.loads(J.pin(native_run/'pins.json').read_text())['files'].items():J.pin(p,h)
    build=json.loads(J.pin(J.BASE/'native-boundary-build-r1/build.json').read_text());J.need(build['passed'],'Fresh boundary native compile')
    for group in ('sources','tools','artifacts'):
        for p,h in build[group].items():J.pin(p,h)
    old=json.loads((J.ROOT/'reports/m4-joint27-startup/build-only-r1/build.json').read_text())
    recipe=json.loads(J.pin(native_run/'report.json').read_text());J.need(recipe['passed'] and recipe['actual_native_phases']==2592 and not recipe['per_phase_reseed'],'Fresh complete actual persistent calls')
    for level in ('O0','O2'):
        entry=build['workers'][level];J.need(entry['objects']==old['objects'][level],'Exact frozen translated object association unchanged')
        for p,h in entry['objects'].items():J.pin(p,h)
        worker=J.pin(entry['path'],entry['sha256']);b=worker.read_bytes();J.need(J.u16(b,J.words(b,60)[0]+4)==0x8664,'Fresh exact AMD64 linked worker')
        command=next(q for q in recipe['commands'] if q['arguments'][0]==str(worker));J.need(command['exit_code']==0,'Actual successful fresh worker recipe')
    controls=J.BASE/'independent-controls-r3';receipt=json.loads(J.pin(controls/'report.json').read_text());J.need(receipt['passed'] and receipt['actual_records']==204 and receipt['corruption_rejections']==3468,'Independent compiled boundary/source fault closure')
    for p,h in json.loads(J.pin(controls/'pins.json').read_text())['files'].items():J.pin(p,h)
    J.pin(__file__)
    return initial

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('original',type=Path);p.add_argument('native_run',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    J.source_receipts=source_receipts
    J.main(a.original.resolve(),a.native_run.resolve(),a.output.resolve(),117684)
    report=a.output/'report.json';r=json.loads(report.read_text());r.update(scope='Independent actual original versus repaired O0/O2 connected27 source/State/pages/FP/events/routes; source fault closure separately independently passed',source_fault_controls_accepted=True,repaired_native_build='reports/m4-joint-startup27/native-boundary-build-r1',source_fault_receipt='reports/m4-joint-startup27/independent-controls-r3/report.json',provider_checkpoint_required_separately=True,connected_roots=27,full_CRT=False,ordinary_game_launched=False)
    report.write_text(json.dumps(r,indent=2)+'\n')
    # This is the fresh independent receipt itself, not a frozen input. Replace
    # its pre-annotation hash in the final source/observation pin inventory.
    J.PINS[str(report.resolve())]=J.sha(report);J.pin(__file__)
    (a.output/'repaired-review-source.py').write_bytes(Path(__file__).read_bytes());J.pin(a.output/'repaired-review-source.py')
    (a.output/'pins.json').write_text(json.dumps(dict(files=J.PINS),indent=2)+'\n')
