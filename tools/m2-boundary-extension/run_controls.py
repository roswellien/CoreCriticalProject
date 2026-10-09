"""Execute all authored negative controls and record actual native control counts."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from build import ROOT, OUT, sha
from compare import validate_build

def run():
    build=validate_build();path=ROOT/'tests/m2-boundary-extension/test_controls.py'
    spec=importlib.util.spec_from_file_location('boundary_controls',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    suite=unittest.defaultTestLoader.loadTestsFromModule(module)
    with (OUT/'controls-output.txt').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped:raise ValueError('Controls did not all execute and pass')
    contexts={};preservation={}
    for level in ('O0','O2'):
        worker=build['workers'][level]
        for option,destination in (('--check-context',contexts),('--check-state-preservation',preservation)):
            child=subprocess.run([worker['path'],option],capture_output=True,text=True,check=True)
            destination[level]={'checks':int(child.stdout.strip().rsplit(' ',1)[1]),'worker_sha256':worker['sha256']}
    report={'schema_version':1,'status':'passed','test_groups':result.testsRun,'skipped':len(result.skipped),
            'build_sha256':sha(OUT/'build.json'),'test_source_sha256':sha(path),'directed_controls':module.COUNTS,
            'context_controls':contexts,'logical_guest_fp_simd_preservation_controls':preservation,
            'controls_output_sha256':sha(OUT/'controls-output.txt')}
    (OUT/'controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report

if __name__=='__main__':run()
