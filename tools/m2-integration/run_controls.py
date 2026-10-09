"""Run and publish authored negative controls plus the separate live API check."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
import ctypes
from build import ROOT, OUT, sha
from compare import validate_build

def run():
    build=validate_build()
    path=ROOT/'tests/m2-integration/test_controls.py'
    spec=importlib.util.spec_from_file_location('m2_controls',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    suite=unittest.defaultTestLoader.loadTestsFromModule(module)
    with (OUT/'controls-output.txt').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped:raise ValueError('Controls did not all execute and pass')
    contexts={}
    live={}
    preservation={}
    for level in ('O0','O2'):
        worker=build['workers'][level]
        child=subprocess.run([worker['path'],'--check-context'],capture_output=True,text=True,check=True)
        count=int(child.stdout.strip().rsplit(' ',1)[1]);contexts[level]={'passed':count,'worker_sha256':worker['sha256']}
        live_child=subprocess.run([worker['path'],'--live-timer'],capture_output=True,text=True,check=True)
        live[level]=json.loads(live_child.stdout)
        preserved=subprocess.run([worker['path'],'--check-state-preservation'],capture_output=True,text=True,check=True)
        preservation[level]={'checks':int(preserved.stdout.strip().rsplit(' ',1)[1]),'scope':'native logical guest FP/SIMD State unchanged across whole compiled integer/API call chain; no hardware FP comparison'}
    original_api=subprocess.run([build['workers']['reference']['path'],'--live-timer'],capture_output=True,text=True,check=True)
    live['reference']=json.loads(original_api.stdout)
    report={'schema_version':1,'status':'passed','test_groups':result.testsRun,'skipped':len(result.skipped),
            'build_sha256':sha(OUT/'build.json'),'test_source_sha256':sha(path),'context_controls':contexts,
            'adapter_ir_rejection_controls':9,'worker_rejections':12,
            'saved_record_corruption_controls':10,'provenance_corruption_controls':10,
            'positive_reviewed_adapter_blocks':8,'controls_output_sha256':sha(OUT/'controls-output.txt')}
    report['state_preservation_controls']=preservation
    (OUT/'controls.json').write_text(json.dumps(report,indent=2)+'\n')
    api={'schema_version':1,'scope':'separate live API availability check; excluded from deterministic comparisons',
         'build_sha256':sha(OUT/'build.json'),'result':live}
    provider=ctypes.WinDLL('winmm.dll');kernel=ctypes.WinDLL('kernel32.dll')
    getpath=kernel.GetModuleFileNameW;getpath.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint];getpath.restype=ctypes.c_uint
    path_buffer=ctypes.create_unicode_buffer(32768)
    length=getpath(provider._handle,path_buffer,len(path_buffer))
    if not length or length>=len(path_buffer):raise ValueError('Live API provider path unavailable')
    api['host_provider']={'path':path_buffer.value,'sha256':sha(Path(path_buffer.value)),
                          'scope':'provider resolved independently in x64 control host; no original-game API trace'}
    (OUT/'live-api.json').write_text(json.dumps(api,indent=2)+'\n')
    print(json.dumps(report,indent=2));print(json.dumps(api,indent=2));return report

if __name__=='__main__':run()
