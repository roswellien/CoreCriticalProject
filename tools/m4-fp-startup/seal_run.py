"""Preserve exact identities and scope of the original-only research run."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    root=ROOT/'reports/m4-fp-startup'
    out=root/'run-r1/closure'
    if out.exists():raise ValueError('Fresh closure required')
    build=json.loads((root/'build-r1/build.json').read_text())
    if not build['passed']:raise ValueError('Actual compiled worker required')
    bindings={}
    for path,expected in build['bindings'].items():
        if sha(path)!=expected:raise ValueError('Build binding changed: '+path)
        bindings[path]=expected
    analysis=json.loads((root/'run-r1/analysis.json').read_text())
    observer=json.loads((root/'run-r1/observer-controls.json').read_text())
    causal=json.loads((root/'run-r1/worker-controls-normal/report.json').read_text())
    independent=json.loads((root/'independent-review/report.json').read_text())
    if not analysis['passed'] or analysis['records']!=480 or analysis['metadata_distinctions']!=480:
        raise ValueError('Actual FP analysis scope differs')
    if not observer['passed'] or len(observer['controls'])!=18 or not causal['passed'] or len(causal['controls'])!=6:
        raise ValueError('Actual causal/observer controls missing')
    out.mkdir()
    sources=[]
    for folder in ('tools/m4-fp-startup','tests/m4-fp-startup'):
        sources.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    sources += [ROOT/'docs/m4-fp-startup-research.md']
    for path in sources:
        destination=out/'sources'/path.relative_to(ROOT)
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
        if destination.read_bytes()!=path.read_bytes():raise ValueError('Source preservation differs')
        bindings[str(path.resolve())]=sha(path)
    inputs=[root/'research-r1/extraction.json',root/'build-r1/build.json',root/'run-r1/analysis.json',
            root/'run-r1/observer-controls.json',root/'run-r1/worker-controls-normal/report.json',
            root/'independent-review/report.json',root/'independent-review/pins.json']
    command=[str(Path(build['worker']).resolve()),'reports/m4-fp-startup/research-r1/pages.bin',
             'MW3/Mech3.exe','reports/m4-fp-startup/run-r1/original.bin']
    report={'passed':True,'scope':'Original-only startup FP output/metadata research; native equivalence remains open',
            'working_directory':str(ROOT),'actual_positive_command':command,'actual_positive_exit_code':0,
            'original_records':480,'roots':10,'repeat_comparisons':240,'FX_ENV_metadata_distinctions':480,
            'root_observer_controls':18,'actual_worker_causal_controls':6,
            'source_copies':len(sources),'inputs':[{'path':str(p),'sha256':sha(p)} for p in inputs],
            'worker_sha256':sha(build['worker']),
            'preserved_failures':['run-r1/observer-attempt1','run-r1/worker-controls','run-r1/worker-controls.log'],
            'hardware_provenance':'run-r1/host-observation.json; local environment observed after capture; CIM unavailable; no exact run timestamps claimed',
            'independent_review':'Independent raw PE/pack/opcode/480record reconstruction; primary analyzer/extractor not imported',
            'limits':['Fixed original-only ABI/constants/BSS and masked empty stack domain',
                'No native FP values/status/storage/metadata equivalence or full Remill State/events observations',
                'No complete CRT/order/services/SEH/MFC/menu or numerical oracle claim',
                'Sequential ordinary fresh directories only; concurrent/reparse/atomic publisher guarantees unproved',
                'Build/source/tools/artifacts bound; complete transitive SDK/system DLL/header identities unobserved'],
            'full_M4_complete':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for folder in ('research-r1','build-r1','run-r1','independent-review'):
        for path in (root/folder).rglob('*'):
            if path.is_file():bindings[str(path.resolve())]=sha(path)
    bindings[str(ROOT/'tools/analysis/pe.py')]=sha(ROOT/'tools/analysis/pe.py')
    (out/'pins.json').write_text(json.dumps({'files':bindings},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json'),'bindings':len(bindings),'M4_complete':False}))

if __name__=='__main__':main()
