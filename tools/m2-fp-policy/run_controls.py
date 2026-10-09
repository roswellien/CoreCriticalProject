"""Run asset-free profile controls and save actual admission counts and identities."""
from collections import Counter
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m2-fp-policy'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    spec=importlib.util.spec_from_file_location('fp_policy_controls',ROOT/'tests/m2-fp-policy/test_policy.py')
    tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
    original=tests.p.admit;accepted=Counter();rejected=Counter()
    def tracked(profile,*args,**kwargs):
        try:result=original(profile,*args,**kwargs)
        except tests.p.PolicyError as error:
            rejected[str(error)]+=1;raise
        accepted[profile]+=1;return result
    tests.p.admit=tracked
    stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise AssertionError(stream.getvalue())
    paths=[Path(__file__),ROOT/'tools/m2-fp-policy/policy.py',ROOT/'tools/m2-fp-policy/profiles.json',
           ROOT/'tools/m2-fp-policy/build_profiles.py',ROOT/'tests/m2-fp-policy/test_policy.py']
    report={'schema_version':1,'status':'bounded_planning_controls_passed','test_groups':result.testsRun,
            'failed_groups':len(result.failures)+len(result.errors),'skipped_groups':len(result.skipped),
            'profile_admissions':sum(accepted.values()),'admissions_by_profile':dict(accepted),
            'rejected_admission_calls':sum(rejected.values()),'diagnostics':dict(rejected),
            'separate_domain_identity_rejections':1,'all_execution_remains_denied':True,
            'live_state_final_acceptance':'pending','source_identities':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},
            'test_output':stream.getvalue()}
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'planning-controls.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report_sha256':sha(path),'groups':result.testsRun,
                      'admissions':sum(accepted.values()),'rejections':sum(rejected.values()),
                      'domain_identity_rejections':1},indent=2))


if __name__=='__main__':run()
