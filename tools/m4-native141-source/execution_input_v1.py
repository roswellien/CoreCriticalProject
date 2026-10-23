"""Bind actual141 writer and closed strict gate without manufacturing admission."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
EXECUTION_SHA='536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6'
BUILD_SHA='ba1f699354fc2a14eb5dcc3bbfa4497e9ceb4ce01786e75cd95430f6c58de1bc'
PREP_SHA='98b3f726249ef233ccdc63855cd5c735aa2ff01cc8717494b686bec34dafb46e'
def load(execution,validation,validation_sha,pin):
 e=json.loads(pin(execution,EXECUTION_SHA).read_bytes());v=json.loads(pin(validation,validation_sha).read_bytes())
 assert e['passed'] and e['actual_workers_launched']==2 and e['all_workers_terminal']
 assert v['passed'] and v['reader_closed'] and v['execution_sha256']==EXECUTION_SHA
 assert e['build_sha256']==v['build_sha256']==BUILD_SHA and e['preparation_sha256']==v['preparation_sha256']==PREP_SHA
 assert len(v['cases'])==12 and v['current141_acceptance'] is False and v['initializer_credit']==0
 build=pin(R/'reports/m4-startup141-runway/build-r3/build.json',BUILD_SHA)
 b=json.loads(build.read_bytes());assert b['preparation_sha256']==PREP_SHA
 return dict(passed=True,all_workers_terminal=True,all_bounded_readers_closed=True,build_path=str(build),build_sha256=BUILD_SHA,levels=[dict(level=level,capture=e['runs'][level]['capture'])for level in ('O0','O2')],scope='Actual141 writer and closed strict observations bound only; full source is still pending',initializer_credit=0,current141_acceptance=False,writer_receipt=str(execution),writer_sha256=EXECUTION_SHA,strict_validation=str(validation),strict_validation_sha256=validation_sha)
