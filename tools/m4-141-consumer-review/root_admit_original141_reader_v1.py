"""Admit one corrected strict reader of the already completed capture."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-original141';T=R/'tools/m4-141-consumer-review'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(p,v,h);assert files.setdefault(str(p),v)==v;return p
for rel,h in [('header-reader-preparation-r1','26ab05ae2933a4052c5d9ee55e58fefb1aee12343c1ea87e1974aaa0e687f49a'),('header-reader-controls-r1','6a8f2b7ace492e99a437f8ccedf5e2290cdee8e33f2d039380f32c82d09f7ecc'),('root-header-reader-controls-r1','d7d7c001badcc8262e325ab29c2b7c900562575cef3cd43d87c6e406091fa9a3')]:
 v=json.loads(pin(B/rel/'report.json',h).read_bytes());assert v['passed'] and not v['reader_opened'] and not v['worker_launched']
 for p,d in v['files'].items():pin(p,d)
tool=pin(T/'validate_original141_v7.py','e6fbfb2168ccfe2789ffb408681b61fca340d061f63b347b5e74eb9018c4b032');s=tool.read_text();ds=json.loads(pin(B/'header-reader-preparation-r1/validator-deltas.json').read_bytes());assert len(ds)==3
for d in reversed(ds):assert s.count(d['new'])==1;s=s.replace(d['new'],d['old'])
assert s==pin(T/'validate_original141_v6.py').read_text()
writer=pin(B/'root-capture-admission-r2/report.json','2317169a720a88b44b8c14de8f78ffea13974efaca78d4dc88a1a5331c244697');execution=pin(B/'root-capture-execution-r2/report.json','2897d2f5e3a6607e1609ea15a661a0cc76bffd12e2c9017a5b2993c7bb590820')
run=json.loads(execution.read_bytes());assert run['passed'] and run['preflight_sha256']==sha(writer) and Path(run['preflight_path'])==writer
stage=json.loads(pin(B/'root-capture-execution-r2/run/stage.json').read_bytes());assert stage['passed'] and stage['exit_code']==0 and stage['inputs_stable']
for k in ('stdout','stderr'):pin(B/'root-capture-execution-r2/run'/f'{k}.bin',stage[k+'_sha256'])
pin(__file__);assert all(sha(p)==d for p,d in files.items())
out=B/'root-strict-reader-admission-r1';out.mkdir();p=out/'report.json'
p.write_text(json.dumps(dict(passed=True,original141_validator_admitted=True,reader_only_admission=True,capture_preflight_path=str(writer),capture_preflight_sha256=sha(writer),actual_terminal_capture_sha256=sha(execution),whole_three_delta_inverse=True,production_AST_controls=23,all_numeric_header_checks_unchanged=True,worker_relaunch_admitted=False,worker_executed=False,reader_opened=False,accepted_function_credit=0,initializer_credit=0,files=files),indent=2)+'\n',encoding='utf-8');print(sha(p),len(files))
