"""Save asset-free admission control diagnostics and source identities."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
TEST=ROOT/'tests/m2-slice-admission/test_admission.py'
spec=importlib.util.spec_from_file_location('m2_slice_controls',TEST)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
original=module.a.admit_context
counts=Counter();diagnostics=Counter()


def counted(*args,**kwargs):
    try:
        result=original(*args,**kwargs);counts['planning_contexts_admitted']+=1;return result
    except module.a.AdmissionError as error:
        counts['rejected_admissions']+=1;diagnostics[str(error)]+=1;raise


module.a.admit_context=counted
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
if not result.wasSuccessful():sys.exit(1)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'schema_version':1,'status':'passed_asset_free_slice_admission_controls','test_groups':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
        'counts':dict(counts),'rejection_diagnostics':dict(diagnostics),'actual_image_failure_controls':2,
        'semantic_contexts':'TOP8*physicalFTW256 plus CW12*DF2 and mixed full-tag/payload/vector storage',
        'execution_allowed':False,'source_sha256':{str(p):sha(p) for p in
            (TEST,ROOT/'tools/m2-slice-admission/admission.py',ROOT/'tools/m2-slice-admission/inspect_image.py',
             Path(__file__),ROOT/'docs/m2-next-slice-context.md')}}
out=ROOT/'reports/m2-slice-admission';out.mkdir(parents=True,exist_ok=True)
path=out/'controls.json';path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'controls_sha256':sha(path),**dict(counts),'test_groups':result.testsRun},indent=2))
